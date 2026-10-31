# -*- coding: utf-8 -*-
r"""把**实验 A** 插到队列中 **COCO 之前**（2026-10-08 07:55）。

## 为什么 A 要排在 COCO 前

| 实验 | 回答什么 | 优先级 |
|---|---|---|
| **A**（`_p21_alpha_trainer_based.py`） | **论文中心论断**：ODE 系数 α 能否由梯度预测 | **高** |
| COCO 补跑（36 h） | **附表**的跨数据集稳健性 | 中 |

**中心论断 > 附表。** 且 A 只需 **1 seed × 10 epoch ≈ 1.5 h**，COCO 要 36 h。

## 插入位置

同秩对照（CLIP B/32 r4 三臂）之后、COCO 之前。

    python tools\_p22_add_alpha_task.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p20_serial_executor.py"

OLD = "    for site in (\"both\", \"text_only\"):\n        for rk in (4, 16, 64, 1, 2, 32):"

NEW = '''    # **实验 A**（trainer 基座，测 α 能否由梯度预测）—— 论文中心论断，**排在 COCO 前**。
    # 只跑 1 seed：判据需要的是"同一 run 内 α̂ 与 α_fit 的可比性"，
    # 且动力学对齐自检（DG* 跨度 ≈ 0.1641）先于任何预测结论。
    a_out = REPO / "outputs/theory/alpha_trainer_based/alpha_trainer_based.json"
    q.append(("A: α 由梯度预测(trainer基座)",
              [PY, "tools/_p21_alpha_trainer_based.py", "--apply",
               "--seeds", "42", "--epochs", "10", "--rank", "8", "--maxsamples", "5000"],
              a_out, 4 * 3600))

    for site in ("both", "text_only"):
        for rk in (4, 16, 64, 1, 2, 32):'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "A: α 由梯度预测(trainer基座)" in t:
        print("  已插入，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(OLD)}）")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    t = t.replace(OLD, NEW, 1)
    ast.parse(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "A: α 由梯度预测(trainer基座)" in t2
    print("  ✅ 已插入实验 A（位于同秩对照之后、COCO 之前）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
