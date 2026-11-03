# -*- coding: utf-8 -*-
r"""修 A / B / C 三处（用逐字锚点；`_p441` 只命中了 D）（2026-10-13）。

## 逐字位置（实测）

- **A** `experiments.tex`：
  `We\ntherefore do not read the ratio as evidence of allocation, demonstrating only\nthat $\Gamma$-based prediction eliminates allocation uncertainty.`
- **B** `experiments.tex`：`\textbf{The Violation group as causal evidence.} If $\Gamma$ were merely\ncorrelated with alignment outcomes rather than causal, forcing high rank on\nhigh-$|\Gamma|$ blocks (Violation) ...`
- **C** `hard-protection` 出现在**两处**：`experiments.tex`（*"gives a hard-protection configuration"*）
  与 `theory.tex`（*"the same hard-protection limit"*）——**不在 appendix**（我先前的任务书给错了位置）

    python tools\_p442_fix_causal_claims2.py [--apply]
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

A_OLD = (
    "We\ntherefore do not read the ratio as evidence of allocation, demonstrating only\n"
    "that $\\Gamma$-based prediction eliminates allocation uncertainty.")
A_NEW = (
    "We therefore do not read the ratio as evidence about allocation at all.\n"
    "The capacity-matched comparison we ran does not support the stronger reading\n"
    "either: at an identical trainable-parameter count ($7{,}237{,}632$, verified per\n"
    "run), the $\\Gamma$-guided allocation reaches $\\Delta E = +2241 \\pm 1291$ against\n"
    "$+6413 \\pm 1552$ for uniform (Welch $p = 0.024$ over three seeds, which does not\n"
    "survive a Bonferroni correction for the three plans compared), and it does not beat\n"
    "a random allocation of the same budget ($+1103 \\pm 1043$). Reversing the rule---\n"
    "largest rank on the least-coupled block---performs the same as applying it as\n"
    "predicted ($+2225 \\pm 1763$). We therefore report the $\\Gamma$-guided rule as\n"
    "directionally consistent with the ordering, not as a method that dominates its\n"
    "alternatives.")

B_OLD = (
    "\\textbf{The Violation group as causal evidence.} If $\\Gamma$ were merely\n"
    "correlated with alignment outcomes rather than causal, forcing high rank on\n"
    "high-$|\\Gamma|$ blocks (Violation) should produce outcomes indistinguishable\n"
    "from Random.")
B_NEW = (
    "\\textbf{The Violation group as consistency evidence.} If $\\Gamma$ carried no\n"
    "information about where damage occurs, forcing high rank on high-$|\\Gamma|$ blocks\n"
    "(Violation) should produce outcomes indistinguishable from Random. It does not, which\n"
    "is consistent with $\\Gamma$ being informative about the location of damage. We stop\n"
    "short of calling the relation causal, because the capacity-matched control does not\n"
    "support the directional reading---the reversed allocation performs the same as the\n"
    "predicted one---so in this regime the ordering alone does not determine the outcome.")

C1_OLD = ("The allocation predicted from the ordering alone then gives a\n"
          "hard-protection configuration (all budget to the least-coupled\n"
          "shallow block), consistent with the scale-invariance analysis\n"
          "(Section~III).")
C1_NEW = ("The allocation predicted from the ordering alone then drives the linear\n"
          "objective to a corner (all budget to the least-coupled shallow block), consistent\n"
          "with the scale-invariance analysis (Section~III). We note that this corner is a\n"
          "property of the linear surrogate and not of the measured energy: the\n"
          "capacity-matched\n"
          "corner configuration scores $\\Delta E = +3607 \\pm 514$, worse than the\n"
          "$\\Gamma$-guided interior solution ($+2241 \\pm 1291$).")

C2_OLD = ("for well-separated magnitudes any temperature below\nthe separation scale yields the same hard-protection limit---negligible\ncapacity on the alignment-sensitive blocks, as validated by the\ncounterfactual experiments (Section~IV-E).")
C2_NEW = ("for well-separated magnitudes any temperature below\nthe separation scale drives the linear surrogate to the same corner---negligible\ncapacity on the alignment-sensitive blocks. We note that this corner is not the\nbest configuration under the measured energy: in the capacity-matched comparison\nof Section~IV-E the corner scores $\\Delta E = +3607 \\pm 514$ while the\n$\\Gamma$-guided interior solution scores $+2241 \\pm 1291$.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for p, old, new, label in ((EX, A_OLD, A_NEW, "A：eliminates uncertainty"),
                               (EX, B_OLD, B_NEW, "B：causal → consistency"),
                               (EX, C1_OLD, C1_NEW, "C1：experiments 的 hard-protection"),
                               (TH, C2_OLD, C2_NEW, "C2：theory 的 hard-protection limit")):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        print(f"  {'✅' if n == 1 else '⚠️ '} {p.name}: {label} 命中 {n}")
        if n == 1 and a.apply:
            bak = p.with_suffix(".tex.bak_p442")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            total += 1
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 共改 {total} 处")
    ex = io.open(EX, encoding="utf-8", errors="replace").read()
    th = io.open(TH, encoding="utf-8", errors="replace").read()
    checks = {
        "A 不再说 eliminates uncertainty": "eliminates allocation uncertainty" not in ex,
        "A 含容量匹配实测数": "$7{,}237{,}632$" in ex and "$+2241 \\pm 1291$" in ex,
        "A 含未胜随机": "$+1103 \\pm 1043$" in ex,
        "A 含反序同样": "$+2225 \\pm 1763$" in ex,
        "B 已降级为 consistency": "as consistency evidence" in ex,
        "B 不再说 causal evidence": "as causal evidence" not in ex,
        "B 含反序不可区分": "the reversed allocation performs the same" in ex,
        "C1 已改并含 corner 劣于 interior": "worse than the" in ex and "$+3607 \\pm 514$" in ex,
        "C2 已改 theory": "drives the linear surrogate to the same corner" in th,
        "全稿不再有 hard-protection": ("hard-protection" not in ex) and ("hard-protection" not in th),
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
