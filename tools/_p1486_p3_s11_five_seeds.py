# -*- coding: utf-8 -*-
r"""P3 soundness hardening 1: make the supplement's crossing text consistent with the five-seed statistics.

    python tools/_p1486_p3_s11_five_seeds.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(SUPP, encoding="utf-8").read()
    old = ("lists the seed-42 trajectories; the second-seed differences are $-10.5$ at $r=5$ and $+115.0$ at $r=6$), so "
           "the sign is consistent across the two seeds. An exact two-sided permutation test on the $r=5$ vs $r=6$ "
           "difference gives $p=0.33$; with two seeds per rank the smallest attainable $p$ is $0.17$, so the test is "
           "under-powered by construction and we report the sign consistency rather than a significance claim.")
    new = ("lists the seed-42 trajectories and Table~\\ref{tab:seed5} the full five-seed set). With five seeds per rank the "
           "difference is resolvable: $r=5$ gives $-23.0\\pm22.3$ (one of five positive) and $r=6$ gives $+65.5\\pm38.5$ "
           "(all five positive), and an exact two-sided permutation test over the ten runs gives $p=0.008$---the smallest "
           "attainable value with five seeds per group, i.e.\\ complete separation of the two rank groups.")
    assert t.count(old) == 1, t.count(old)
    t = t.replace(old, new, 1)
    print("  S11 text updated to the five-seed statistics")
    if a.apply:
        io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
