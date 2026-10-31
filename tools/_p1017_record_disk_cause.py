# -*- coding: utf-8 -*-
r"""Record the real cause of the silent death (a full disk) and the checkpoint fix.

    python tools/_p1017_record_disk_cause.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "静默死亡真因=磁盘满"

ENT = """> **💾 2026-10-16 12:40 —— 11:44「静默死亡」的**真因是根分区写满**；checkpoint 从 **14.4 GB 降到 160 MB**（已验证）**
>
> ### 一、🔍 真因：**根分区 100% 满**（不是显存、不是我的释放逻辑）
>
> ```
> overlay 30G  30G  200K  100%  /          <- 11:55 实测
> text_only_s456_ckpt.pt  64 字节          <- 写了一半就被 ENOSPC 打断的残骸
> ```
>
> **ENOSPC 发生在写 epoch checkpoint 时，而 sweep 的日志也在这个满盘上** ⇒ **traceback 写不进日志**
> ⇒ 表现为"进程消失、日志停在 step 2225、没有任何错误信息"。**这就是三次"静默死亡"的解释。**
>
> ### 二、🔍 为什么会满：**checkpoint 存了整个模型**
>
> | 代码 | 问题 |
> |---|---|
> | `torch.save({"model": mm.state_dict()})` | **存了全部 7B 参数** ⇒ **14,367,576,761 字节/epoch** |
> | 而可训练参数只有 | text arm **20 M** / vision arm **3.6 M** ⇒ 本就该只存这些 |
>
> 3 个 epoch × 14.4 GB × 每个 arm ⇒ **30 GB 盘必然写满**。（此功能是我加的 `--resume`，属**我的设计缺陷**。）
>
> ### 三、✅ 修法与验证
>
> | 修法 | 验证（实测） |
> |---|---|
> | checkpoint **只存可训练张量**（`p.requires_grad` 的 state_dict 子集；加载端本就 `strict=False`）| **14,367,576,761 B → 160,298,591 B**（**约 90×**）|
> | 清理：删掉遗留 ckpt + pip 缓存（**记录不受影响**，每个 arm 完成即单独落 JSON）| 根分区 **30 G → 5.5 G（释放 24 G）** |
> | 新增 **每个 arm 的异常守卫**：traceback 写 `ARM_FAILURES.txt` 并**继续下一个 arm** | 单 arm 失败不再带走整个 sweep |
> | 释放加固：`synchronize` + `ipc_collect` + 两次 `empty_cache` + 打印 allocated/reserved | 日志可见 |
> | 去掉管道里的 `grep`（**它会缓冲吞掉尾部**）| 现在能实时看到 "Loading weights" 与完整 epoch 行 |
>
> ### 四、⚠️ 这一轮我犯的错（逐条记录）
>
> | # | 错判 | 实际 |
> |---|---|---|
> | ① | 以为 OOM 是 warmup 预留 | 第一个真因是**旧模型未释放**（已修，19.4 GB 释放可见）|
> | ② | 以为"释放够彻底了" | **第三个真因是磁盘满**，与显存无关 |
> | ③ | 诊断脚本读 `final_sweep.log`（旧日志）| 把已修复的失败又报了一遍 ⇒ 新增 `_p1005` 读当前日志 |
> | ④ | 用 `sftp.put` 改远端文件 | 磁盘满时**上传本身失败**（`OSError: Failure`）⇒ 改用远端就地命令清理 |
>
> ### 五、⏱️ 当前进度
>
> | 项 | 值 |
> |---|---|
> | 记录 | **5 条**（frozen ×3 + `text_only_s42` + `text_only_s123`）|
> | 当前 | `text_only_s456` step 900/2250（epoch 2/3），loss 0.795，1.0 s/步 |
> | 磁盘 | 根 **25 G 可用**（checkpoint 已无害）；数据盘 37 G |
> | 剩余 | **6 个 run** ⇒ **约 15:30 完成** |
>
> **工具**：`_p1014`（清理脚本，因盘满未能上传）｜`_p1015`（就地清理）｜`_p1016`（小 checkpoint）｜`_p1017`（本条）。
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
    row = ("40. 💾 **静默死亡真因=根分区写满（2026-10-16 12:40）** —— `overlay 30G 用满、只剩 200K` ⇒ 写 epoch checkpoint 时 "
           "**ENOSPC**，而日志在同一满盘 ⇒ **traceback 写不进日志**（这就是三次「进程消失、无报错」的解释；残骸 ckpt 仅 **64 字节**）。"
           "**为何满**：`torch.save({\"model\": mm.state_dict()})` **存了整个 7B 模型 = 14.4 GB/epoch**（我的 `--resume` 设计缺陷）。"
           "**修法**：只存可训练张量 ⇒ **14,367,576,761 B → 160,298,591 B（约 90×）**（已实测）；清理遗留 ckpt+pip 缓存 ⇒ **释放 24 G**；"
           "另加 **per-arm 异常守卫**（失败写 `ARM_FAILURES.txt` 并继续）、释放加固、**去掉管道 `grep`**（缓冲吞日志尾部）。"
           "进度 **5 条记录**，当前 `text_only_s456` step 900/2250，剩余 6 run ⇒ 约 15:30 完成。详见 `HANDOFF.md` 顶部 12:40 条目。\n")
    anchor = "39. 🔧 **两次 OOM 的真根因已修并验证（2026-10-16 11:30）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
