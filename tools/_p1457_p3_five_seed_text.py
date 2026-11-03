# -*- coding: utf-8 -*-
r"""P3: replace the two-seed/three-seed crossing statements with the five-seed statistics.

    python tools/_p1457_p3_five_seed_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(REPO, "paper3", "paper_ieee", "sections", "experiments.tex")
CONC = os.path.join(REPO, "paper3", "paper_ieee", "sections", "conclusion.tex")

OLD_EXP = ("What we cannot do is put $r_c$ on a rank:\nwith three seeds the smallest effect we could detect exceeds "
           "the one we observe, and an\nexact permutation test between $r=5$ and $r=6$ gives $p=0.100$. The crossing "
           "is\nbracketed, and its location belongs to the measurement protocol rather than to the model.")
NEW_EXP = ("With five seeds per rank the same comparison is resolvable: $r=5$ gives $-23.0\\pm22.3$ points (one of "
           "five\nseeds positive) and $r=6$ gives $+65.5\\pm38.5$ (all five positive), a difference of means of $+88.5$ "
           "points\n(exact two-sided permutation test over the ten runs, $p=0.008$, the smallest attainable with five "
           "seeds per\ngroup). What we still cannot do is put $r_c$ on a single rank: the crossing is bracketed between "
           "$r=5$ and\n$r=6$, and its location belongs to the measurement protocol rather than to the model.")

OLD_CONC1 = ("the interval at $r=5$ spans\nzero and an exact permutation test between neighbouring ranks is not "
             "significant---and we")
NEW_CONC1 = ("the interval at $r=5$ still contains zero for individual seeds, while the five-seed group comparison\n"
             "between the two neighbouring ranks is significant (exact two-sided $p=0.008$)---and we")

OLD_CONC2 = ("at $r=5$ the sign is seed-dependent ($-10.5$ and $+8.0$ for two seeds, i.e.\\ zero lies inside the "
             "interval), at $r=6$ it is positive for both seeds ($+115.0$ and $+25.5$)")
NEW_CONC2 = ("at $r=5$ the sign remains seed-dependent ($-10.5$, $+8.0$, $-36.5$, $-27.0$ and $-49.0$ for five "
             "seeds;\nmean $-23.0\\pm22.3$, one of five positive), at $r=6$ it is positive on all five seeds ($+115.0$, "
             "$+25.5$,\n$+32.0$, $+62.0$ and $+93.0$; mean $+65.5\\pm38.5$)")

OLD_COUNT = "Experimental validation covers 126 runs on the present protocol"
NEW_COUNT = "Experimental validation covers 132 runs on the present protocol"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    te = io.open(EXP, encoding="utf-8").read()
    tc = io.open(CONC, encoding="utf-8").read()
    changed = False
    for old, new, name in ((OLD_EXP, NEW_EXP, "experiments crossing statement"),
                           (OLD_CONC1, NEW_CONC1, "conclusion bracketing statement"),
                           (OLD_CONC2, NEW_CONC2, "conclusion per-seed values"),
                           (OLD_COUNT, NEW_COUNT, "conclusion run count")):
        target, other = (te, tc) if name.startswith("experiments") else (tc, te)
        if old in target:
            target = target.replace(old, new, 1)
            if name.startswith("experiments"):
                te = target
            else:
                tc = target
            changed = True
            print("  replaced:", name)
        else:
            print("  NOT FOUND:", name)
    if a.apply and changed:
        io.open(EXP, "w", encoding="utf-8", newline="").write(te)
        io.open(CONC, "w", encoding="utf-8", newline="").write(tc)
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
