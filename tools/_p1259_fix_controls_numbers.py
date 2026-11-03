# -*- coding: utf-8 -*-
r"""Correct the controls table: the matched-gap row must mirror the numbers already in Section 5.2.

Section 5.2 reports a 32.7-point spread at |dCG| <= 0.03 on CLIP, and 27.1 points on OpenCLIP (dCG = 0.066) and on
SigLIP (dCG = 0.197). The controls table I inserted said 33.1 points and quoted 27.1 for both other models at the 0.03
tolerance, which the archives do not support (a1_matched_gap_families.json: 32.68; a1_matched_gap_crossmodel.json: 8.08
at 0.021 for OpenCLIP and 5.94 at 0.023 for SigLIP). This patch aligns the table with the text.

    python tools/_p1259_fix_controls_numbers.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

OLD = r"""Matched gap across perturbation families & ``at a given gap, accuracy is determined'' & $33.1$ points at
$|\Delta\mathrm{CG}|\le0.03$ (CLIP); $27.1$ and $27.1$ on OpenCLIP and SigLIP \\"""
NEW = r"""Matched gap across perturbation families & ``at a given gap, accuracy is determined'' & $32.7$ points at
$|\Delta\mathrm{CG}|\le0.03$ (CLIP); $27.1$ points on OpenCLIP at $\Delta\mathrm{CG}=0.066$ and on SigLIP at $0.197$ \\"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    n = t.count(OLD)
    print(f"  matched-gap row: {n}")
    assert n == 1
    t = t.replace(OLD, NEW, 1)
    print(f"  '33.1' remaining: {t.count('33.1')} | '32.7' present: {t.count('32.7')}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
