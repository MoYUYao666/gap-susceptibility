# -*- coding: utf-8 -*-
r"""修 P3 的记账口径与 β 表述（用逐字锚点；2026-10-12）。

## 与 `_p421` 的差别

`_p421` 的两处锚点**没命中**（我按"一行写完"猜的文本，实际是**跨行**的）：

- `experiments.tex` 逐字：`The CLIP-derived allocation ($\beta=0.137$)\nthen predicts …`
- `theory.tex` 逐字：`(A2) Separable objective. (A3)\nBudget $\sum_k \mathrm{rank}_k = C$, …`

**本脚本用逐字锚点**，并断言命中数 == 1 才改。

    python tools\_p422_fix_p3_budget_beta2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"
TH = REPO / "paper3" / "paper_ieee" / "sections" / "theory.tex"

E_BETA_OLD = (
    "The CLIP-derived allocation ($\\beta=0.137$)\n"
    "then predicts a hard-protection configuration (all budget to the\n"
    "least-coupled shallow block), consistent with the scale-invariance\n"
    "analysis (Section~III).")
E_BETA_NEW = (
    "The allocation predicted from the ordering alone then gives a\n"
    "hard-protection configuration (all budget to the least-coupled\n"
    "shallow block), consistent with the scale-invariance analysis\n"
    "(Section~III). This prediction uses only the \\emph{ordering} of\n"
    "$\\Gamma_k$ and requires no numerical value of $\\beta$. The symbol\n"
    "$\\beta$ is overloaded in the literature and we keep the two uses\n"
    "apart: the $\\beta$ in the allocation rule of Eq.~5 is a free\n"
    "temperature, whereas the $\\beta$ fitted to the trajectory dynamics\n"
    "of Paper~2 (median $0.072$ over $96$ fits; the value $0.137$ quoted\n"
    "in an earlier draft is a single fit,\n"
    "\\texttt{ode\\_ledger.json::runs[90]}, $R^2=0.951$) is a different\n"
    "quantity and does not enter Eq.~5.")

TH_A3_OLD = (
    "(A2) Separable objective. (A3)\n"
    "Budget $\\sum_k \\mathrm{rank}_k = C$, $\\mathrm{rank}_k \\geq 1$. (A4)\n")
TH_A3_NEW = (
    "(A2) Separable objective. (A3)\n"
    "Budget $\\sum_k \\mathrm{rank}_k = C$, $\\mathrm{rank}_k \\geq 1$.\n"
    "This is a budget on \\emph{rank}, not on trainable parameters: the\n"
    "parameter cost of one unit of rank depends on the block,\n"
    "$c_k = \\sum_{W \\in M_k}(\\mathrm{in}_W + \\mathrm{out}_W)$, and $c_k$\n"
    "varies by a factor of $2.65$ across blocks in Qwen2-VL ($655{,}360$\n"
    "for the vision block against $247{,}296$ for the shallow LLM block;\n"
    "\\texttt{outputs/analysis/p3\\_alloc\\_budget\\_probe.json}). A uniform\n"
    "rank is therefore \\emph{not} a uniform parameter allocation, and the\n"
    "two conventions give different solutions: under a parameter budget\n"
    "$\\sum_k c_k\\,\\mathrm{rank}_k = B$ the KKT system of Eq.~5 acquires an\n"
    "extra factor and the solution becomes\n"
    "$\\mathrm{rank}^*_k \\propto \\exp(-\\beta|\\Gamma_k|)/c_k$. Eq.~5 below\n"
    "is stated in the rank convention. (A4)\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for p, old, new, label in ((EX, E_BETA_OLD, E_BETA_NEW, "β 来源（CLIP-derived）"),
                               (TH, TH_A3_OLD, TH_A3_NEW, "(A3) 记账口径说明")):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠️ '} {p.name}: {label} 命中 {n}")
        if n == 1 and a.apply:
            bak = p.with_suffix(".tex.bak_p422")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            total += 1
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    ex = io.open(EX, encoding="utf-8", errors="replace").read()
    th = io.open(TH, encoding="utf-8", errors="replace").read()
    checks = {
        "experiments 不再说 CLIP-derived": "CLIP-derived allocation" not in ex,
        "experiments 指明 β 出处": "ode\\_ledger.json::runs[90]" in ex,
        "experiments 声明两者不同量": "is a different\nquantity" in ex or "different" in ex,
        "experiments 声明只用排序": "requires no numerical value of $\\beta$" in ex,
        "theory 含 c_k 定义": "$c_k = \\sum_{W \\in M_k}" in th,
        "theory 含 2.65×": "$2.65$" in th,
        "theory 含参数记账变体解": "/c_k$" in th,
        "theory 声明 Eq.5 是 rank 口径": "is stated in the rank convention" in th,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
