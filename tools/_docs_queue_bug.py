# -*- coding: utf-8 -*-
r"""落账：批次修正队列的"静默跳过"bug + 已修（2026-10-10 晚）。

    python tools\_docs_queue_bug.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🐛 2026-10-10 晚 —— 修掉批次修正队列的一个"静默跳过"bug（差点白跑一夜）**
>
> ### 一、症状
>
> 批次修正队列启动后，OCLIP 的"重跑"任务 **8 秒就 rc=0 返回**，但**文件没变**
> （`batch_size` 仍是 64、mtime 是旧的）。
>
> ### 二、根因（**两层**）
>
> **① `experiments/strict_freeze_control.py` 有跳过逻辑，只看文件存在性、不看配置**：
>
> ```
> [skip] text_only seed=123 already done
> total 0.0 min
> ```
>
> → 只要 `OUT_DIR/tag/seed{seed}/results.json` 存在，**脚本直接退出（8 s，rc=0）**。
> **我的队列以为"跑过了就覆盖"，实际什么都没做。**
>
> （脚本自己的防御检查也印证了这个设计：
> `[拒绝运行] --rank 4 但 --out-dir=... 未包含 rank 标识` ——
> "原因：跳过逻辑按 OUT_DIR/tag/seed 判断，不同 rank 共用目录会导致后跑的 rank 直接复用前一个的结果"。）
>
> **② 我误判为"参数错误"**：先怀疑 `--out-dir` 缺 rank 标识，但实际路径
> `outputs/strict_freeze_oclip/r4` **是含 `r4` 的**，检查能通过。**真正的失败是"静默跳过"。**
>
> ### 三、排查过程（可复核）
>
> | 步骤 | 结果 |
> |---|---|
> | 手动跑同参数（`_probe_oclip`，无 rank 目录） | ❌ `[拒绝运行] --out-dir 未包含 rank 标识` → **误导了我** |
> | 改跑含 rank 的路径（`_probe_oclip/r4`，10 样本） | ❌ `topk k out of range`（**样本太少，与队列无关**） |
> | **真实规模**（5000 样本，`_probe2/r4`） | ✅ **成功，298 s**，写出 `results.json` |
> | **队列的确切命令**（含 `--name oclip_r4_r4_`） | 🔴 **`[skip] already done`** ← **真因** |
>
> ### 四、修法
>
> 在重跑前**把旧文件改名**（`results.json` → `results.batch64.bak`），脚本才会真跑。
> **保留旧文件而非删除**——它是"批次污染"的证据。
>
> 已加入 `tools/_p169_batchfix_queue.py` 的 `stash_old()`（`tools/_p170` 施加）。
>
> ### 五、修后验证
>
> ```
> [19:54:57] ▶ [rerun] oclip_r4/r4/text_only/seed123
> [19:54:57]    旧文件(batch=64)→results.batch64.bak
> [20:00:33]    ✅ oclip_r4/r4/text_only/seed123（335s）   ← 真的跑了
> ```
>
> ### 六、教训（写给未来的自己）
>
> **"rc=0"不等于"做了事"。** 幂等驱动必须**以产物元数据为准**判断是否完成，
> 而**不能把 rc=0 当作成功信号**——本次脚本的设计是"存在即跳过"，
> 于是 rc=0 与"什么都没做"不可区分。**验证要落到文件内容/时间戳上。**
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if '"静默跳过"bug' in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ('"静默跳过"bug', "[skip] text_only seed=123 already done",
              "results.batch64.bak", "335s", "rc=0\"不等于\"做了事"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
