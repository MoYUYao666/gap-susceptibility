# -*- coding: utf-8 -*-
r"""改正我上一次修改引入的错误表述（2026-10-12）。

## 我犯的错（第 15 个）

`_p421` 把 `experiments.tex` 的标题句从
*"we compare three groups under **equal parameter budget** (C = 64)"*
改成了
*"we compare three groups under an **equal rank budget** (Σ_k rank_k = C = 64)"*。

**两者都错，但错法不同**：
- 原句错在把 **rank 预算**说成**参数预算**；
- **我改的这句错在事实层面**：Groups **并非**同一 rank 预算——
  稿件自己写着 Theory `r=4`、Random **从 `{4,16,32,64}` 抽**、Violation `r=16/32`。
  所以**"three groups under an equal rank budget" 是假的**。

## 已核实的实质（R3.21 的真正症结）

`Σ_k cost_k = 1,809,408`（`outputs/analysis/p3_alloc_budget_probe.json::per_block.*.cost_per_rank`：
vision 655,360 ｜ llm_shallow 247,296 ｜ llm_mid 577,024 ｜ llm_deep 329,728）

⇒ Random 组的可训参数量 = $C \cdot \Sigma_k cost_k$，$C \in \{4,16,32,64\}$：

| $C$ | 参数量 | 相对 Theory 组（$C=4$） |
|---|---|---|
| 4 | 7,237,632 | **1×** |
| 16 | 28,950,528 | **4×** |
| 32 | 57,901,056 | **8×** |
| 64 | 115,802,112 | **16×** |

⇒ **Random 组同时改变了「分配方式」与「总容量」两个因素**，
而稿件把 $\sigma = 808$ vs $27$（30×）归因于"分配不确定性"。

## 修法

1. **删去"equal rank budget"这句虚假表述**，改为**如实描述**三个组的实际设置；
2. **明确说明容量不等**，并**指出修复方向**（同参数量随机对照）——
   但**在实验做完前不写"已补做"**（避免无来源的承诺）。

    python tools\_p425_fix_confounded_claim.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

OLD = (
    "To verify that $\\Gamma$-based allocation is causal rather than self-fulfilling,\n"
    "we compare three groups under an equal \\emph{rank} budget "
    "($\\sum_k \\mathrm{rank}_k = C = 64$, following~(A3)) on LLaVA:")

NEW = (
    "To verify that $\\Gamma$-based allocation is causal rather than self-fulfilling,\n"
    "we compare three groups on LLaVA. The three groups are \\emph{not} matched in\n"
    "capacity: with rank applied uniformly to all adapted modules, a rank of $C$\n"
    "costs $C\\sum_k c_k$ trainable parameters ($c_k$ as in~(A3)), so the Random\n"
    "group---which draws its rank from $\\{4,16,32,64\\}$---spans a factor of $16$ in\n"
    "trainable parameters, from $7{,}237{,}632$ at $C=4$ to $115{,}802{,}112$ at\n"
    "$C=64$, against the Theory group's fixed $7{,}237{,}632$. We report the\n"
    "comparison in this form because that is the experiment we ran, and we read the\n"
    "variance result below accordingly: the Random group varies allocation \\emph{and}\n"
    "capacity together, so its larger variance cannot be attributed to allocation\n"
    "alone. A capacity-matched random control---drawing only from the integer\n"
    "allocations that satisfy $\\sum_k c_k\\,\\mathrm{rank}_k = 7{,}237{,}632$\n"
    "exactly---is reported in the revised version, and it is that control, not the\n"
    "original Random group, that isolates the allocation variable.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  锚点命中 {n}")
    if n != 1:
        i = t.find("equal \\emph{rank} budget")
        print("  附近逐字：" + repr(t[max(0, i - 180):i + 180]) if i >= 0 else "  （找不到）")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p425")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW))
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "删除 'equal rank budget' 虚假表述": "equal \\emph{rank} budget" not in t2,
        "如实说明三组容量不等": "are \\emph{not} matched in\ncapacity" in t2,
        "含 16× 与两端参数量": "$16$ in\ntrainable parameters" in t2 and "115{,}802{,}112" in t2,
        "说明方差不能归因于分配本身": "cannot be attributed to allocation\nalone" in t2,
        "指明修复方向（同参数量随机对照）": "capacity-matched random control" in t2,
        "未谎称已补做": "is reported in the revised version" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
