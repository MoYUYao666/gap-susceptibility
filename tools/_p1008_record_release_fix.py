# -*- coding: utf-8 -*-
r"""Record the real cause of the repeated OOMs and its fix.

    python tools/_p1008_record_release_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "OOM 真根因：旧模型未释放"

ENT = """> **🔧 2026-10-16 11:30 —— 两次 OOM 的**真根因**找到并修好：**每个 arm 的旧模型从未释放**；已在真实运行中验证**
>
> ### 一、🔍 真根因（读 traceback + 失败时刻的显存快照，不是猜）
>
> 失败时的实测状态：
>
> ```
> GPU 0 has a total capacity of 31.48 GiB of which 4.17 GiB is free
> this process has 27.29 GiB memory in use ... 26.74 GiB is allocated by PyTorch
> caching_allocator_warmup -> _ = torch.empty(int(byte_count // 2), dtype=torch.float16, ...)
> torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 12.91 GiB.
> ```
>
> **那 26.74 GiB 就是上一个 arm 的模型（+优化器+激活）**：每个 arm 都 `build()` 一个全新的 14 GB 模型，
> **旧模型从未 `del`、缓存从未清**，于是**第二个 arm 加载时只剩 4 GB**。
>
> ### 二、⚠️ 我先前的**三个错误判断**（逐个被实测否掉，如实记录）
>
> | # | 我的判断 | 实际 | 证据 |
> |---|---|---|---|
> | ① | 加 `--alloc-warmup-gb 1.5` 收紧 warmup 预留即可 | **无效** | 崩溃栈显示失败发生在 `_capped_warmup` **内部**，`_orig_warmup` 仍申请 12.91 GiB |
> | ② | 在 `build` 附近插入释放块 | **插错两处**：插到 `build` **之后**（把刚建好的模型删了 ⇒ `UnboundLocalError`），且落在 `if arm != "frozen":` **块内**（frozen arm 到不了） | 运行日志逐字可见 |
> | ③ | 仅靠日志判断状态 | 诊断脚本读的是**旧日志** `final_sweep.log`，于是把**已修复**的失败又报了一遍 | 新增 `_p1005` 读**当前**日志 |
>
> ### 三、✅ 修法与验证
>
> **修法**：在每个 arm 的 `build(arm)` **之前**（同一缩进、`frozen` 分支之外）执行
> `del mm` / `del opt`（`NameError` 容错）→ `gc.collect()` → `torch.cuda.empty_cache()` →
> 打印可用显存 → **断言 ≥16 GB，不够就干净退出而不是半途炸**。
>
> **验证（真实运行，不是推断）**：重启后日志打印
> `device free before this arm: 19.3 GB of 33.8 GB`，并**成功越过前两次崩溃的确切位置**
> （`text_only_s456` 的 `build` 之后进入训练）：**step 1025/2250、loss 0.676、0.97 s/步、ETA 11:45**。
>
> ### 四、⏱️ 当前进度
>
> | 项 | 值 |
> |---|---|
> | 已完成记录 | **5**：frozen ×3 + `text_only_s42` + `text_only_s123` |
> | 进行中 | `text_only_s456`（第 3 个被训练的 arm）|
> | 剩余 | **7 个 run** ⇒ **约 15:50 全部完成** |
> | GPU / 磁盘 | 30.8 GiB、58°C；数据盘 **35 G 可用** |
>
> ### 五、🧠 可复用的教训
>
> 1. **长跑脚本的循环里必须显式释放上一轮的大对象**——`del` + `empty_cache()` 不是可选项；
> 2. **崩溃栈要看"失败发生在哪一层"**：我修的是 warmup 的"上限"，而失败发生在 warmup **内部**的真实申请；
> 3. **诊断工具必须指向当前运行**（旧日志会把已修复的问题反复报出来）；
> 4. **插入代码要断言位置**（`_p1007` 现在断言"释放块必须在 build 之前"），不要靠"看起来插对了"。
>
> **工具**：`_p1006`（首次释放块，位置错）｜`_p1007`（按行号搬正+断言）｜`_p1005`（读当前日志）｜`_p1008`（本条）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    mp = io.open(REPO / "文件地图.md", encoding="utf-8").read()
    row = ("39. 🔧 **两次 OOM 的真根因已修并验证（2026-10-16 11:30）** —— **每个 arm 的旧模型从未释放**："
           "失败时实测 `31.48 GiB 仅剩 4.17 GiB 可用、26.74 GiB 仍被占用`，即上一个 arm 的模型+优化器还挂着；"
           "`--alloc-warmup-gb` 无效（失败发生在 warmup **内部**）。**修法**：`build(arm)` **之前**"
           "`del mm/del opt` + `gc.collect()` + `empty_cache()` + **断言 ≥16 GB 否则干净退出**。"
           "**真实运行验证**：日志打印 `device free before this arm: 19.3 GB` 并越过前两次崩溃点，"
           "`text_only_s456` 正常训练（step 1025/2250）。⚠️ 另有三个我自己的错判（warmup 上限无效、释放块插错两处、"
           "诊断脚本读旧日志）已如实记录。进度 **5 条记录**，剩余 7 run ⇒ 约 15:50 完成。"
           "详见 `HANDOFF.md` 顶部 2026-10-16 11:30 条目。\n")
    anchor = "38. 🐌 **加速调查：只保留 `--eval-batch`（2026-10-16 09:55）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
