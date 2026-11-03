# -*- coding: utf-8 -*-
r"""Measure how wide the full-width Table S3 actually is, and how far it could spread.

Reported follow-up: "TABLE S3 再远一点" -- the columns should sit further apart. Table S3 is a table*, so
it may use the full text width (18.2 cm on letter paper in IEEEtran), but the columns were given 12.7 cm
in total, leaving about 5.5 cm of unused width and making the block look narrow for a full-width table.

This measures the rendered rule width in pixels and converts to cm, so the change can be verified rather
than guessed.

    python tools/_p923_measure_table_s3.py
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAGE = REPO / "outputs" / "analysis" / "_p3supp-5.png"
DPI = 150
CM_PER_PX = 2.54 / DPI


def main() -> int:
    a = np.array(Image.open(PAGE).convert("L"))
    ink = a < 200
    h, w = ink.shape
    # find long horizontal rules: rows whose ink run is longer than 8 cm
    min_run_px = int(8.0 / CM_PER_PX)
    rules = []
    for r in range(h):
        cols = np.where(ink[r])[0]
        if len(cols) > min_run_px and (cols.max() - cols.min()) > min_run_px:
            rules.append((r, int(cols.min()), int(cols.max())))
    # group consecutive rows into single rules
    groups = []
    for r, x0, x1 in rules:
        if groups and r - groups[-1][-1][0] <= 2:
            groups[-1].append((r, x0, x1))
        else:
            groups.append([(r, x0, x1)])
    print(f"  page image {w}x{h} px at {DPI} dpi ({CM_PER_PX:.4f} cm/px)")
    print(f"  horizontal rules longer than 8 cm: {len(groups)}")
    for g in groups:
        r0 = g[0][0]
        x0 = min(x for _r, x, _x1 in g)
        x1 = max(x for _r, _x0, x in g)
        print(f"    y={r0:<5} x={x0}-{x1}  width {(x1 - x0) * CM_PER_PX:.2f} cm")
    # the text block itself, from the body rows of page 3 (no full-width tables there)
    p3 = np.array(Image.open(REPO / "outputs" / "analysis" / "_p3supp-3.png").convert("L")) < 200
    cols = np.where(p3.any(axis=0))[0]
    print(f"  text block on page 3: x={cols.min()}-{cols.max()} "
          f"=> {(cols.max() - cols.min()) * CM_PER_PX:.2f} cm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
