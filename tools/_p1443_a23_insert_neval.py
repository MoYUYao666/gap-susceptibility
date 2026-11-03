# -*- coding: utf-8 -*-
r"""A23: add the evaluation-sample-size floor of the tripwire calibration.

    python tools/_p1443_a23_insert_neval.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(REPO, "paper_a2", "main_ieee.tex")
ANCHOR = ("rather than at $\\lambda{=}1$, and its calibration is reported with the model runs "
          "(Section~\\ref{sec:replica}).")
ADD = (" Calibration also has a sample-size floor: subsampling the 67-class marine evaluation set, the "
       "$\\tau$--accuracy correlation is unstable at 32--64 images (Pearson $r$ between $-0.64$ and $0.48$ across the two "
       "encoders) and only stabilises with the full split ($0.61$--$0.83$; "
       "\\texttt{outputs/\\allowbreak analysis/\\allowbreak a23\\_neval\\_sensitivity.json}), so tripwire levels fitted on "
       "fewer than a hundred evaluation images are indicative only.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(TEX, encoding="utf-8").read()
    assert "Calibration also has a sample-size floor" not in t
    assert t.count(ANCHOR) == 1, t.count(ANCHOR)
    t = t.replace(ANCHOR, ANCHOR + ADD, 1)
    print("  sentence inserted")
    if a.apply:
        io.open(TEX, "w", encoding="utf-8", newline="").write(t)
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
