# -*- coding: utf-8 -*-
r"""P3: write the five-seed crossing statistics into the manuscript and the supplementary per-seed table (S14).

Requires outputs/analysis/p3_seeds_combined.json from tools/_p1448_p3_seeds_analysis.py.

    python tools/_p1449_p3_insert_seeds.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMBINED = os.path.join(REPO, "outputs", "analysis", "p3_seeds_combined.json")
EXP = os.path.join(REPO, "paper3", "paper_ieee", "sections", "experiments.tex")
CONC = os.path.join(REPO, "paper3", "paper_ieee", "sections", "conclusion.tex")
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
AUDIT = os.path.join(REPO, "paper3", "paper_ieee", "audit_check.py")

OLD_EXP2 = ("at $r=5$ the sign is seed-dependent ($-10.5$ and $+8.0$ for two seeds, i.e.\\ zero lies inside the "
            "interval), at $r=6$ it is positive for both seeds ($+115.0$ and $+25.5$)")
OLD_CONC = ("with three seeds the smallest effect we could detect exceeds the one we observe, and an exact permutation "
            "test between $r=5$ and $r=6$ gives $p=0.100$.")


def fmt(vals, signed=True):
    return ", ".join(("%+.1f" % v) if signed else ("%.1f" % v) for v in vals)


def section_tex(c):
    rows = []
    for rank, key in (("$r=5$", "r5"), ("$r=6$", "r6")):
        for seed, val in sorted(c["values"][key].items(), key=lambda kv: int(kv[0])):
            rows.append("%s & %s & %+.1f \\\\" % (rank, seed, val))
    return ("""\\section{Per-seed crossing values}
\\label{app:seed5}

The five seeds per rank at the crossing, same protocol (three epochs, $E_0=3921.0$). $\\Delta E$ is the change of the
alignment energy from epoch 0 to epoch 3; positive values mean degradation. Data: \\texttt{outputs/\\allowbreak analysis/\\allowbreak p3\\_rerun\\_seeds.json} and the seed-42/123 archives named in Section~S7.

\\begin{table}[h]
\\centering
\\small
\\caption{Per-seed $\\Delta E$ at the crossing. The exact two-sided permutation test on the difference of means gives
$p=%.3f$ (smallest attainable $%.3f$ with five seeds per rank).}
\\label{tab:seed5}
\\begin{tabular}{@{}llr@{}}
\\toprule
rank & seed & $\\Delta E$ \\\\
\\midrule
%s
\\bottomrule
\\end{tabular}
\\end{table}

""" % (c["permutation"]["p_two_sided"], c["permutation"]["p_min_attainable"], "\n".join(rows)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(COMBINED):
        print("  combined statistics not ready")
        return 0
    c = json.load(io.open(COMBINED, encoding="utf-8"))
    v5 = [c["values"]["r5"][s] for s in sorted(c["values"]["r5"], key=int)]
    v6 = [c["values"]["r6"][s] for s in sorted(c["values"]["r6"], key=int)]
    p = c["permutation"]["p_two_sided"]
    pmin = c["permutation"]["p_min_attainable"]
    new_exp2 = ("at $r=5$ the sign is seed-dependent ($%s$ for five seeds; mean $%+.1f \\pm %.1f$, %d of $5$ positive), "
                "at $r=6$ it is positive on all five seeds ($%s$; mean $%+.1f \\pm %.1f$), and the exact two-sided "
                "permutation test between the two rank groups gives $p=%.3f$ (smallest attainable $%.3f$ with five "
                "seeds per rank)" % (fmt(v5), c["r5"]["mean"], c["r5"]["sd"], c["r5"]["n_positive"],
                                     fmt(v6), c["r6"]["mean"], c["r6"]["sd"], p, pmin))
    new_conc = ("with five seeds per rank the difference of means is $%+.1f$ points and an exact two-sided permutation "
                "test gives $p=%.3f$ (smallest attainable $%.3f$); the crossing is bracketed, and its location belongs "
                "to the measurement protocol rather than to the model." % (c["difference_of_means"], p, pmin))
    te = io.open(EXP, encoding="utf-8").read()
    tc = io.open(CONC, encoding="utf-8").read()
    ts = io.open(SUPP, encoding="utf-8").read()
    changed = False
    if OLD_EXP2 in te:
        assert te.count(OLD_EXP2) == 1
        te = te.replace(OLD_EXP2, new_exp2, 1)
        changed = True
        print("  experiments sentence replaced")
    else:
        print("  experiments sentence already replaced")
    if OLD_CONC in tc:
        assert tc.count(OLD_CONC) == 1
        tc = tc.replace(OLD_CONC, new_conc, 1)
        changed = True
        print("  conclusion sentence replaced")
    else:
        print("  conclusion sentence already replaced")
    if "app:seed5" not in ts:
        anchor = "\\bibliographystyle{IEEEtran}"
        ts = ts.replace(anchor, section_tex(c) + "\n" + anchor, 1)
        changed = True
        print("  supplementary S14 added")
    ta = io.open(AUDIT, encoding="utf-8").read()
    old = 'check("supplement: thirteen S-sections", n_sections == 13, f"{n_sections} sections")'
    new = 'check("supplement: fourteen S-sections", n_sections == 14, f"{n_sections} sections")'
    if old in ta:
        ta = ta.replace(old, new, 1)
        changed = True
        print("  audit supplement count 13->14")
    if a.apply and changed:
        io.open(EXP, "w", encoding="utf-8", newline="").write(te)
        io.open(CONC, "w", encoding="utf-8", newline="").write(tc)
        io.open(SUPP, "w", encoding="utf-8", newline="").write(ts)
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(ta)
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
