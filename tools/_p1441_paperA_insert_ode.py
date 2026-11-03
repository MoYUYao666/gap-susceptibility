# -*- coding: utf-8 -*-
r"""Paper A: add the family-specific ODE fit-scope sentence.

    python tools/_p1441_paperA_insert_ode.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(REPO, "paper合", "sections", "empirical.tex")
ANCHOR = "(Table~\\ref{tab:family})."
ADD = (" The residual structure is concentrated in the adapter family: $95\\%$ of the LoRA runs and $64\\%$ of the full\n"
       "fine-tuning runs exceed $R^2=0.9$, against $7\\%$ of the adapter runs (minimum $0.001$\n"
       "\\texttt{outputs/\\allowbreak analysis/\\allowbreak paperA\\_ode\\_residuals.json}). The quantitative ODE claims are\n"
       "therefore restricted to the two families that satisfy the first-order reduction; the adapter family enters only\n"
       "through the qualitative position ordering.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(TEX, encoding="utf-8").read()
    assert "The residual structure is concentrated" not in t
    assert t.count(ANCHOR) == 1, t.count(ANCHOR)
    t = t.replace(ANCHOR, ANCHOR + ADD, 1)
    print("  sentence inserted")
    if a.apply:
        io.open(TEX, "w", encoding="utf-8", newline="").write(t)
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
