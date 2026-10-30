# -*- coding: utf-8 -*-
r"""Check the supplement for overflow and column collisions.

The p{} rework of the tables caused one round of "text runs into the next column" (Table S4 was wider
than the 3.5 in column). This looks for the same class of fault from the rendered pages:

* LaTeX overfull boxes reported in the log;
* ink in the gutter between the two columns, which is what a table overflowing its column looks like.

    python tools/_p920_supp_overflow_check.py
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
SUPPDIR = REPO / "paper3" / "paper_ieee" / "supplementary"
LOGS = [SUPPDIR / "supplementary.log"]
PNGS = sorted((REPO / "outputs" / "analysis").glob("_p3supp-*.png"), key=lambda p: int(p.stem.split("-")[1]))

B = chr(92)
print("=== LaTeX overfull / underfull boxes ===")
for log in LOGS:
    if not log.exists():
        print(f"  {log.name}: missing")
        continue
    t = log.read_text(encoding="utf-8", errors="replace")
    # "Overfull \hbox (12.3pt too wide) ..." — the box kind is matched with a character class so the
    # pattern contains no backslash escape that Python's re would reject
    hbox = [float(m) for m in re.findall(r"Overfull [^ ]box \(([0-9.]+)pt", t)]
    vbox = [float(m) for m in re.findall(r"Overfull [^ ]vbox \(([0-9.]+)pt", t)]
    print(f"  {log.name}: overfull boxes {len(hbox)} {[f'{x:.1f}pt' for x in hbox[:5]]}, "
          f"overfull vbox {len(vbox)} {[f'{x:.1f}pt' for x in vbox[:5]]}")

print()
print("=== ink in the gutter between the two columns ===")
# Measured from the rendered pages: the two text columns are separated by an empty 625-648 px band at
# 150 dpi. The title on page 1 and the full-width table* legitimately span it, so the test starts below
# the title block. (An earlier version guessed the band at 630-690 and reported "ink" on every page,
# which was simply the right-hand column starting at 648.)
GUTTER = (626, 648)
TITLE_BAND = 400
for p in PNGS:
    a = np.array(Image.open(p).convert("L"))
    ink = a < 200
    band = ink[TITLE_BAND:, GUTTER[0]:GUTTER[1]]
    total = int(band.sum())
    rows = int((band.any(axis=1)).sum())
    verdict = "clean" if total == 0 else f"{total} px on {rows} rows"
    print(f"  {p.name}: gutter {verdict}")

