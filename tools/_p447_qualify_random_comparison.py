# -*- coding: utf-8 -*-
r"""把"未胜随机"标注为待重算 + 说明 random_00 的性质（2026-10-13）。

## 依据（`tools/_p445` / `_p446`，我已核）

30 个方案 → **只有 15 个不同 rank 向量、5 组重复**；**14 个"随机"里只有 10 个是独立的**：

| 随机方案 | 与哪个**规则**方案同一分配 |
|---|---|
| `random_00` | **`exp_ca_beta_1e-4`**（Γ 的 cost-aware 变体） |
| `random_04` | `corner` / `exact_opt` |
| `random_12` | `inverse_beta_paper_0.137` |
| `random_13` | **`exp_beta_paper_0.137`**（**正是论文 Eq.5 的解**） |

**10 个独立随机样本的 obj 分布**：`26,527 … 64,825`，**中位数 44,505**——
而 **`random_00` 的 obj 恰好 = 44,505 = 该中位数** ⇒ **它不是特殊样本**，
且**没有独立随机样本的 obj 低于 Γ-guided（25,356）**。

⇒ 我先前稿中 *"it does not beat a random allocation of the same budget ($+1103$)"*
**建立在被污染的对照上**（`+1103` 来自一条 Γ 规则，不是随机抽样）
⇒ **必须标注为"待独立样本重算"，不得作为结论，也不得反向翻案**。

    python tools\_p447_qualify_random_comparison.py [--apply]
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
    "and it does not beat\n"
    "a random allocation of the same budget ($+1103 \\pm 1043$). Reversing the rule---\n"
    "largest rank on the least-coupled block---performs the same as applying it as\n"
    "predicted ($+2225 \\pm 1763$).")

NEW = (
    "and it does not beat\n"
    "a random allocation of the same budget in the comparison we ran ($+1103 \\pm 1043$).\n"
    "We flag that comparison as provisional rather than as a result: the budget-feasible\n"
    "set contains only fifteen distinct allocations, and four of the fourteen draws we had\n"
    "labelled `random' coincide exactly with rule-based solutions---the lowest of them,\n"
    "which is the one that beats the $\\Gamma$-guided rule, coincides with the cost-aware\n"
    "variant of the rule itself at $\\beta = 10^{-4}$, and another coincides with Eq.~5 at\n"
    "the paper's own $\\beta = 0.137$. The ten remaining draws are the ones that constitute\n"
    "an actual random sample, their linear-objective values span $26{,}527$ to $64{,}825$,\n"
    "and the excluded draw sits exactly at the median ($44{,}505$) of that sample. We\n"
    "report the matched-budget comparison against those ten draws in the revised version\n"
    "and do not draw a conclusion from the contaminated one. Reversing the rule---largest\n"
    "rank on the least-coupled block---performs the same as applying it as predicted\n"
    "($+2225 \\pm 1763$).")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  锚点命中 {n}")
    if n != 1:
        i = t.find("does not beat")
        print("  附近：" + repr(t[max(0, i - 120):i + 260]) if i >= 0 else "  （找不到）")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p447")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW))
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "标注为 provisional": "provisional rather than as a result" in t2,
        "含 15 个不同分配": "only fifteen distinct allocations" in t2,
        "含 4 个与规则重合": "coincide exactly with rule-based solutions" in t2,
        "含 random_00 = cost-aware 1e-4": "cost-aware\nvariant of the rule itself" in t2,
        "含另一个 = Eq.5 β=0.137": "Eq.~5 at\nthe paper's own $\\beta = 0.137$" in t2,
        "含 10 个独立样本与 obj 范围": "ten remaining draws" in t2 and "$26{,}527$" in t2,
        "含被排在样本中位数": "exactly at the median ($44{,}505$)" in t2,
        "声明不从被污染对照下结论": "do not draw a conclusion from the contaminated one" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
