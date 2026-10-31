# -*- coding: utf-8 -*-
r"""给协议脚本加 `GapConfig(compute_every_n_epochs=1)`（2026-10-08）。

## 为什么（**这是一个测量缺陷，会毁掉 ODE 拟合**）

实测对比：

| run | epoch 记录点 | DG\\* 跨度 |
|---|---|---|
| 归档 Flickr30k `v1_both_r8` | **1–10（10 点）** | **0.1641** |
| 归档 COCO `coco_both_r8` | **1–10（10 点）** | **0.1011** |
| **我的新跑** | **1,2,4,6,8,10（仅 6 点）** | **0.0054** ❌ |

**根因**：协议脚本**没设 `GapConfig`** → 用默认 `compute_every_n_epochs=2`
→ **只在偶数 epoch 记 DG\\***（10 epoch 只得 6 个点）。

而 `experiments/theory/v1_rank_sweep.py:128` **显式设了 `compute_every_n_epochs=1`**
——归档的 96 个 `dg_star_history.json` 就是逐 epoch 的。

**→ 不修的话，新跑的 `DG*` 轨迹既稀疏又几乎平（跨度小 30 倍），ODE 拟合不可比。**

## 改法

在 `ExperimentConfig(...)` 里加 `gap=GapConfig(compute_every_n_epochs=1)`。

## 代价

已跑的 2 个 run 作废（稀疏记录），已清理；修后重跑。

    python tools\_p37_fix_gap_config.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "experiments" / "strict_freeze_control.py"

OLD = """    cfg = ExperimentConfig(
        name="%s%s" % (NAME_PREFIX, tag),
        lora=LoRAConfig(rank=RANK, alpha=RANK * ALPHA_MULT, **CONFIGS[tag]),"""
NEW = """    cfg = ExperimentConfig(
        name="%s%s" % (NAME_PREFIX, tag),
        lora=LoRAConfig(rank=RANK, alpha=RANK * ALPHA_MULT, **CONFIGS[tag]),
        # **必须逐 epoch 记录**：ODE 拟合的状态变量 DG* 需要每 epoch 一个点。
        # 默认 compute_every_n_epochs=2 会只记偶数 epoch（10 epoch 只得 6 点），
        # 实测跨度因此小 30 倍（0.0054 vs 归档 0.1641），**拟合不可比**。
        # 归档的 dg_star_history.json 全部是逐 epoch 的（见 v1_rank_sweep.py:128）。
        gap=GapConfig(compute_every_n_epochs=1),"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "必须逐 epoch 记录" in t:
        print("  已加，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(OLD)}）")
        return 1
    # 确认 GapConfig 已导入
    if "GapConfig" not in t.split("def run_one")[0]:
        print("  ⚠ 需先导入 GapConfig → 在 src.config 导入行补上")
        import re
        m = re.search(r"from src\.config import ([^\n]+)", t)
        if m and "GapConfig" not in m.group(1):
            t = t.replace(m.group(0), m.group(0).rstrip() + ", GapConfig", 1)
            print("    已补导入")
    if not apply:
        print("  （预演）")
        return 0
    t = t.replace(OLD, NEW, 1)
    ast.parse(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "gap=GapConfig(compute_every_n_epochs=1)" in t2
    print("  ✅ 已加 GapConfig(compute_every_n_epochs=1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
