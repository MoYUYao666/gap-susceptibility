# -*- coding: utf-8 -*-
r"""按 task-9 改 P3 的四处因果/最优主张（2026-10-13）。

## 依据（`outputs/analysis/p3_alloc_results.json`，我已核）

| 方案 | rank 向量 | ΔE 均值 ± sd | 说明 |
|---|---|---|---|
| `uniform` | {4,4,4,4} | **+6413.4 ± 1552.3** | 现 Theory 组 |
| **`exp`（Γ-guided）** | **{4,2,2,9}** | **+2241.0 ± 1290.6** | vs uniform **p=0.024**（n=3，**未过 Bonferroni×3 的 0.0167**） |
| `inverse`（反序） | {4,15,1,1} | **+2225.2 ± 1763.5** | **与正序几乎不可区分** |
| **`random_00`** | {4,6,2,6} | **+1103.1 ± 1043.2** | **最低** |
| `corner`（线性目标角点） | {4,1,3,8} | +3607.2 ± 513.6 | 劣于 exp |

**15 run 实测参数量唯一值 = 7,237,632**，`same_budget_assert_passed = true`

## 四处必改

- **A**：`"demonstrating only that Γ-based prediction eliminates allocation uncertainty"` ← **已被否证**
- **B**：`"The Violation group as causal evidence … Γ-based allocation is causal"` ← **反序与正序不可区分**
- **C**：Appendix D `"hard-protection configuration"` ← 是**线性目标的角点**，非实测最优
- **D**：`"The rank predicted to minimize alignment degradation"` ← 需限定

**另修我自己 `_p426` 留下的自相矛盾**：前半句刚说"不作为分配证据"，后半句又写"demonstrating … eliminates uncertainty"。

    python tools\_p441_fix_causal_claims.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"
AP = REPO / "paper3" / "paper_ieee" / "sections" / "appendix.tex"

# ---------- A + 我自己的自相矛盾 ----------
A_OLD = (
    "We therefore do not read the ratio as evidence of allocation, demonstrating only\n"
    "that $\\Gamma$-based prediction eliminates allocation uncertainty.")
A_NEW = (
    "We therefore do not read the ratio as evidence about allocation at all, and the\n"
    "capacity-matched comparison we ran does not support the stronger reading either: at\n"
    "an identical trainable-parameter count ($7{,}237{,}632$, verified per run), the\n"
    "$\\Gamma$-guided allocation reaches $\\Delta E = +2241 \\pm 1291$ against\n"
    "$+6413 \\pm 1552$ for uniform (Welch $p = 0.024$, three seeds each, which does not\n"
    "survive a Bonferroni correction for the three plans compared), and it does not beat a\n"
    "random allocation of the same budget ($+1103 \\pm 1043$). We therefore report the\n"
    "$\\Gamma$-guided rule as directionally consistent with the ordering, not as a method\n"
    "that dominates its alternatives.")

# ---------- B：因果性降级 ----------
B_OLD = (
    "\\textbf{The Violation group as causal evidence.} If $\\Gamma$ were merely\n"
    "correlated with alignment outcomes rather than causal, forcing high rank on high-$|\\Gamma|$\n"
    "blocks (Violation) should produce outcomes indistinguishable from Random.")
B_NEW = (
    "\\textbf{The Violation group as consistency evidence.} If $\\Gamma$ were unrelated to\n"
    "alignment outcomes, forcing high rank on high-$|\\Gamma|$ blocks (Violation) should\n"
    "produce outcomes indistinguishable from Random. It does not, which is consistent with\n"
    "$\\Gamma$ carrying information about where damage occurs. We stop short of calling the\n"
    "relation causal, because the capacity-matched control does not support the directional\n"
    "reading: reversing the allocation---giving the largest rank to the \\emph{least} coupled\n"
    "block---performs the same as applying it as predicted ($+2225 \\pm 1763$ against\n"
    "$+2241 \\pm 1291$), so the ordering alone does not determine the outcome in this regime.")

# ---------- D：predicted to minimize ----------
D_OLD = (
    "    \\item \\textbf{Theory} ($r = 4$): The rank predicted to minimize alignment\n"
    "    degradation by the CLIP structural law ($5$ seeds).")
D_NEW = (
    "    \\item \\textbf{Theory} ($r = 4$): The rank that the CLIP structural law\n"
    "    predicts to give the smallest alignment degradation ($5$ seeds). We note that\n"
    "    uniform rank is not uniform capacity---per-block parameter cost varies by\n"
    "    $2.65\\times$~(A3)---so this arm is a uniform-\\emph{rank} baseline, not an\n"
    "    equal-parameter one.")

# ---------- C：appendix 的 hard-protection ----------
C_OLD = "hard-protection configuration"
C_NEW = ("configuration that the linear objective drives to a corner")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for p, old, new, label in ((EX, A_OLD, A_NEW, "A：eliminates uncertainty"),
                               (EX, B_OLD, B_NEW, "B：因果性降级"),
                               (EX, D_OLD, D_NEW, "D：predicted to minimize"),
                               (AP, C_OLD, C_NEW, "C：hard-protection")):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {'✅' if n >= 1 else '⚠️ '} {p.name}: {label} 命中 {n}")
        if n >= 1 and a.apply:
            bak = p.with_suffix(".tex.bak_p441")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            total += n
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    ex = io.open(EX, encoding="utf-8", errors="replace").read()
    apx = io.open(AP, encoding="utf-8", errors="replace").read()
    checks = {
        "A 已改：不再说 eliminates uncertainty": "eliminates allocation uncertainty" not in ex,
        "A 含容量匹配实测数": "$7{,}237{,}632$" in ex and "$+2241 \\pm 1291$" in ex,
        "A 含未胜随机": "$+1103 \\pm 1043$" in ex,
        "A 含未过 Bonferroni": "does not\nsurvive a Bonferroni correction" in ex,
        "B 已降级为 consistency": "as consistency evidence" in ex,
        "B 含反序不可区分": "performs the same as applying it as predicted" in ex,
        "B 不再说 causal evidence": "as causal evidence" not in ex,
        "D 含非等参数基线说明": "not an\n    equal-parameter one" in ex,
        "C 已改 hard-protection": "hard-protection" not in apx,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
