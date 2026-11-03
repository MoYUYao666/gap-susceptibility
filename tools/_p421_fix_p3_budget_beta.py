# -*- coding: utf-8 -*-
r"""修 P3 的记账口径与 β 表述（审稿意见 R3.21 / R3.7；2026-10-12）。

## 已核实的两个稿件错误

### ① 记账口径（R3.21 的要害）

- `theory.tex:173` **(A3)**: `Budget $\sum_k \mathrm{rank}_k = C$` ← **rank 记账**
- `experiments.tex:255`: *"we compare three groups under **equal parameter budget** ($C = 64$)"*
  ← **写成了"参数预算"**，**术语冲突**
- 实测每 rank 成本（`outputs/analysis/p3_alloc_budget_probe.json::per_block.*.cost_per_rank`）：
  **vision 655,360** ｜ shallow **247,296** → **块间差 2.65×**
  ⇒ **"rank 均匀" ≠ "参数均匀"**；uniform r=4 的逐块参数量最大/最小 = **2.65×**

### ② β 的两重问题（R3.7）

- `experiments.tex:141`: *"**The CLIP-derived allocation** ($\beta=0.137$) then predicts …"*
- 实测出处：`outputs/analysis/ode_ledger.json::runs[90].beta = 0.1371162965748463`
  → 配置 **`v1_trajectory/v1_text_only_r64`**、**`family=lora`** ← **不是 CLIP**；
  96 个 run 中**唯一**命中；全部 β **中位数 0.072**
- 且 `theory.tex:232--233` **自己声明**：该 β 与 Eq. 5 的 β 是**不同量**、在 Eq. 5 中**不起作用**
  → **同一符号两名 + 名字来源错 + 内部矛盾**

## 修法

- ①：把 `experiments.tex` 的 "equal parameter budget" 改为**明确 rank 记账**，
  并**补一句参数记账的说明**（含实测成本差 2.65×）
- ②：**改符号**（把 ODE 拟合的 β 改名为 $\beta_{\mathrm{ODE}}$ 或直接删去该称谓）+
  **改来源描述**（"CLIP-derived" → 指向 `ode_ledger.json` 的实际 run），
  并在 Eq. 5 处**显式声明记账口径**（rank vs 参数）

    python tools\_p421_fix_p3_budget_beta.py [--apply]
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

# ---------- ① experiments.tex：equal parameter budget → 明确 rank 记账 ----------
E_BUDGET_OLD = r"we compare three groups under equal parameter budget ($C = 64$) on LLaVA:"
E_BUDGET_NEW = (
    r"we compare three groups under an equal \emph{rank} budget "
    r"($\sum_k \mathrm{rank}_k = C = 64$, following~(A3)) on LLaVA:"
)

# ---------- ② experiments.tex：CLIP-derived β → 如实来源 ----------
E_BETA_OLD = (
    r"The CLIP-derived allocation ($\beta=0.137$) then predicts a hard-protection configuration "
    r"(all budget to the least-coupled shallow block), consistent with the scale-invariance "
    r"analysis (Section~III).")
E_BETA_NEW = (
    r"The allocation predicted from the ordering alone then gives a hard-protection "
    r"configuration (all budget to the least-coupled shallow block), consistent with the "
    r"scale-invariance analysis (Section~III). We stress that this prediction uses only the "
    r"\emph{ordering} of $\Gamma_k$ and does not require a numerical value of $\beta$: the "
    r"$\beta$ that appears in the allocation rule of Eq.~5 and the $\beta$ fitted to the "
    r"trajectory dynamics of Paper~2 (median $0.072$ over $96$ fits; the value $0.137$ quoted "
    r"in earlier drafts is a single fit, \texttt{ode\_ledger.json::runs[90]}, "
    r"\texttt{v1\_textory\_r64}, $R^2=0.951$) are \emph{different quantities}, as "
    r"Section~III notes, and the former is not calibrated from the latter.")

# ---------- ③ theory.tex：Eq.5 处声明记账口径 ----------
TH_RULE_OLD = r"(A3) Budget $\sum_k \mathrm{rank}_k = C$, $\mathrm{rank}_k \geq 1$."
TH_RULE_NEW = (
    r"(A3) Budget $\sum_k \mathrm{rank}_k = C$, $\mathrm{rank}_k \geq 1$. "
    r"This is a budget on \emph{rank}, not on trainable parameters: the number of parameters "
    r"a unit of rank costs depends on the block, $c_k = \sum_{W \in M_k}(\mathrm{in}_W + "
    r"\mathrm{out}_W)$, and $c_k$ varies across blocks by a factor of $2.65$ in Qwen2-VL "
    r"($655{,}360$ for the vision block against $247{,}296$ for the shallow LLM block; "
    r"\texttt{outputs/analysis/p3\_alloc\_budget\_probe.json}). A uniform rank is therefore "
    r"\emph{not} a uniform parameter allocation, and the two accounting conventions give "
    r"different solutions: under a parameter budget $\sum_k c_k\,\mathrm{rank}_k = B$ the "
    r"KKT system of Eq.~5 acquires an extra factor and the solution becomes "
    r"$\mathrm{rank}^*_k \propto \exp(-\beta|\Gamma_k|)/c_k$.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for p, old, new, label in ((EX, E_BUDGET_OLD, E_BUDGET_NEW, "记账口径（equal parameter budget）"),
                               (EX, E_BETA_OLD, E_BETA_NEW, "β 来源（CLIP-derived）"),
                               (TH, TH_RULE_OLD, TH_RULE_NEW, "(A3) 处的记账说明")):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠️ '} {p.name}: {label} 命中 {n}")
        if n == 1 and a.apply:
            bak = p.with_suffix(".tex.bak_p421")
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
        "experiments 不再说 equal parameter budget": "equal parameter budget" not in ex,
        "experiments 改为 equal rank budget": "equal \\emph{rank} budget" in ex,
        "experiments 不再说 CLIP-derived": "CLIP-derived allocation" not in ex,
        "experiments 指明 β 出处": "ode\\_ledger.json::runs[90]" in ex,
        "experiments 声明两者是不同量": "different quantities" in ex,
        "theory 含 2.65× 与成本定义": "$2.65$" in th and "$c_k = \\sum_{W \\in M_k}" in th,
        "theory 含参数记账下的变体解": "/c_k$" in th,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
