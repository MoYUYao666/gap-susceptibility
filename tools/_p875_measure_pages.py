# -*- coding: utf-8 -*-
r"""Measure every page's lowest ink row, to catch content that overruns the footer.

The footer baseline is where the page number sits on a well-filled page. Rendering the PDF at 150 dpi
and taking the lowest ink row per page gives that baseline directly (702.2 pt here), so any page whose
content reaches further down is overrunning -- which is how the page-49 defect was found: its last ink
sat at 791.5 pt, the physical paper edge, pushing the page number off the footer.

    python tools/_p875_measure_pages.py [--pdf paper合/main_nc.pdf]
"""
from __future__ import annotations

import argparse
import glob
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FOOTER_PT = 702.2          # observed baseline on a normal page
LIMIT_ROW = 1480           # 150 dpi row corresponding to ~710 pt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default="paper合/main_nc.pdf")
    a = ap.parse_args()

    pdf = Path(a.pdf)
    if not pdf.is_absolute():
        pdf = REPO / pdf
    work = REPO / "outputs" / "analysis" / "_pages"
    work.mkdir(parents=True, exist_ok=True)
    for old in glob.glob(str(work / "*.png")):
        Path(old).unlink()
    subprocess.run(["pdftoppm", "-r", "150", "-png", str(pdf), str(work / "pg")], check=False)

    from PIL import Image
    import numpy as np

    rows = {}
    for p in sorted(work.glob("pg-*.png"), key=lambda q: int(q.stem.split("-")[-1])):
        n = int(p.stem.split("-")[-1])
        arr = np.array(Image.open(p).convert("L"))
        ink = arr < 200
        r = np.where(ink.any(axis=1))[0]
        if len(r):
            rows[n] = int(r.max())

    bad = {n: (v, round(v / 150 * 72, 1)) for n, v in rows.items() if v > LIMIT_ROW}
    top = max(rows.values()) if rows else 0
    print(f"  pages measured: {len(rows)}")
    print(f"  footer baseline: {FOOTER_PT} pt (row {round(FOOTER_PT / 72 * 150)})")
    print(f"  deepest last-ink: row {top} = {top / 150 * 72:.1f} pt")
    print(f"  pages overrunning the footer: {bad if bad else 'NONE'}")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
