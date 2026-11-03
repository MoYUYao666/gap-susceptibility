# -*- coding: utf-8 -*-
r"""Close the audit warnings introduced by the new theory/protocol blocks.

  C-05 / C-07  `tab:protocol` and `prop:nobound` were never referenced from the text
  J-01         the claim ledgers are older than the (just edited) manuscript sources

    python tools/_p1258_fix_new_refs.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

OLD1 = r"""The CUSUM threshold is calibrated
leave-one-trajectory-out, choosing the smallest $h$ that fires on none of the other nine trajectories; the median is
$h=6.0$ (range $5.25$--$6.0$)."""
NEW1 = r"""The CUSUM threshold is calibrated
leave-one-trajectory-out, choosing the smallest $h$ that fires on none of the other nine trajectories; the median is
$h=6.0$ (range $5.25$--$6.0$). Table~\ref{tab:protocol} reports the outcome for each rule."""

OLD2 = r"""Proposition~\ref{prop:nonsuff} is an existence statement; it says nothing about how far apart two same-gap
representations can be in accuracy."""
NEW2 = r"""Proposition~\ref{prop:nobound} states the resulting asymmetry in the form the experiments measure: an accuracy
difference is bounded by the mass of rows whose decision changes, a quantity the gap does not see, so no bound in terms
of $\Delta\mathrm{CG}$ exists. Proposition~\ref{prop:nonsuff} is an existence statement; it says nothing about how far
apart two same-gap representations can be in accuracy."""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    for old, new, label in ((OLD1, NEW1, "protocol table ref"), (OLD2, NEW2, "nobound ref")):
        n = t.count(old)
        print(f"  {label}: {n}")
        assert n == 1, label
        t = t.replace(old, new, 1)
    for lab in ("ref{tab:protocol}", "ref{prop:nobound}"):
        print(f"  now referenced {lab}: {('\\' + lab) in t}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
