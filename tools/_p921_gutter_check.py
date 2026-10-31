# -*- coding: utf-8 -*-
r"""Locate the true gutter between the supplement's two columns and check nothing crosses it.

An earlier version guessed the gutter at x = 630-690 and reported ink on every page, which is simply
where the right-hand column starts. This measures the ink profile first, then tests the empty band.

    python tools/_p921_gutter_check.py
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PNGS = sorted((REPO / "outputs" / "analysis").glob("_p3supp-*.png"),
              key=lambda p: int(p.stem.split("-")[1]))

for p in PNGS:
    a = np.array(Image.open(p).convert("L"))
    ink = a < 200
    h, w = ink.shape
    col = ink.sum(axis=0)
    # the interior columns, ignoring the page margins (about 80 px each side at 150 dpi)
    interior = np.arange(100, w - 100)
    empty = interior[col[interior] == 0]
    # group the empty columns into bands
    bands = []
    if len(empty):
        start = prev = empty[0]
        for x in empty[1:]:
            if x != prev + 1:
                bands.append((start, prev))
                start = x
            prev = x
        bands.append((start, prev))
    wide = [b for b in bands if b[1] - b[0] >= 8]
    print(f"  {p.name}: empty vertical bands wider than 8 px: {wide}")
    if wide:
        g0, g1 = max(wide, key=lambda b: b[1] - b[0])
        print(f"      widest gutter {g0}-{g1} px ({g1 - g0 + 1} px wide) -> clean by construction")
