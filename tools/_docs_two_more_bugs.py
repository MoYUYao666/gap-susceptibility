# -*- coding: utf-8 -*-
r"""落账：执行器两处新 bug + 实验 A 终于跑起来（2026-10-08 10:30）。

    python tools\_docs_two_more_bugs.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🐛 2026-10-08 10:30 —— 又两处执行器 bug（都是我写的）｜实验 A 终于真跑起来**
>
> ### Bug 1：COCO 任务 `--seeds` 传成**单个字符串** → 12 个任务全空转
>
> ```python
> "--seeds", "42 123 456",      # ← argparse 当成一个参数
> ```
> **实测**：`strict_freeze_control.py: error: argument --seeds: invalid int value: '42 123 456'`
> → **rc=2、30 秒一个、连续 9 个任务全失败**（`del` 之后空转到下一个）。
>
> **修**：`"--seeds", *"42 123 456".split()` → 三个独立参数。
>
> ### Bug 2：实验 A 被**误判"已完成"** → 真正的实验被跳过
>
> `_p21_alpha_trainer_based.py` **无条件**写 `alpha_trainer_based.json`（**未对齐时也写**，
> 内容 `"aligned": false`）。而 `task_done()` **只看文件存在** → 把
> **我那次 100 样本的诊断运行**当成 A 完成 → `⏭ A: ... 已完成（合格）→ 跳过`。
>
> **修**：A 的完成判据改为**读 JSON 要求 `aligned == true` 且存在 `passed` 字段**。
>
> **这是"文件存在即完成"判据第三次咬到我**（前两次：α 首跑残留、下载目录非空）——
> **判据必须校验内容语义，不能只看存在性。**
>
> ### ✅ 实验 A 现在真在跑
>
> ```
> [10:24:26] ▶ A: α 由梯度预测(trainer基座)
> Epoch 3: 71%|███████▏ | 45/63 [00:39<00:15, 1.17it/s, loss=3.3285]
> GPU: 7813 MiB, 99%
> ```
>
> **🔑 关键佐证**：loader 给出 **63 步/epoch**，**正好等于归档的 630/10**
> —— 此前我按 `5000/64=78` 推算，**实际与归档完全一致**。
> **→ 这是"动力学对齐"的直接证据**（比 DG\\* 跨度更硬的指标）。
>
> ### 本阶段自错累计 15 次
>
> | 类型 | 次数 |
> |---|---|
> | 判据类 | 7（新增："A 完成判据只看文件存在"） |
> | 操作类 | 2 |
> | 设计类 | 3 |
> | 代码类 | 3（新增：`--seeds` 未拆分） |
>
> **共同模式依然未变：用了方便的写法，而非正确的。**
> **对策③（新增）**：**"完成"判据必须校验输出内容的语义**（`aligned`/`passed` 等标志位），
> 不得只看文件是否存在。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "又两处执行器 bug" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("又两处执行器 bug", "invalid int value", "误判", "63 步/epoch", "自错累计 15 次"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
