# -*- coding: utf-8 -*-
"""Render every page of A1 and flag layout anomalies: blank pages, ink outside the margins, huge white gaps."""
import glob
import os
import subprocess
import sys

import numpy as np
from PIL import Image

PDF = sys.argv[1] if len(sys.argv) > 1 else "paper_a1/main.pdf"
OUT = "outputs/_pagecheck"
os.makedirs(OUT, exist_ok=True)
for f in glob.glob(os.path.join(OUT, "*.png")):
    os.remove(f)

exe = r"D:\texlive\2025\bin\windows\pdftoppm.exe"
subprocess.run([exe, "-r", "72", "-png", PDF, os.path.join(OUT, "p")], check=True, timeout=900)

pages = sorted(glob.glob(os.path.join(OUT, "p-*.png")))
print(f"pages rendered: {len(pages)}")
flags = []
for p in pages:
    n = int(os.path.basename(p).split("-")[1].split(".")[0])
    a = np.asarray(Image.open(p).convert("L"))
    h, w = a.shape
    dark = a < 200
    cov = dark.mean()
    cols = np.where(dark.any(axis=0))[0]
    rows = np.where(dark.any(axis=1))[0]
    if len(cols) == 0:
        flags.append((n, "BLANK page"))
        continue
    # letter size at 72 dpi: 612 x 792 px; content window with 1in margins = 72..540 x 72..720
    left, right = cols.min(), cols.max()
    top, bottom = rows.min(), rows.max()
    issues = []
    if cov < 0.02:
        issues.append(f"nearly blank (ink {cov*100:.1f}%)")
    if right > 552:
        issues.append(f"ink beyond right margin (x={right})")
    if left < 60:
        issues.append(f"ink beyond left margin (x={left})")
    if bottom > 738:
        issues.append(f"ink below bottom margin (y={bottom})")
    # largest vertical white gap between the first and last ink row
    rowink = dark.any(axis=1)
    gaps, run = [], 0
    for y in range(top, bottom + 1):
        if not rowink[y]:
            run += 1
        else:
            if run:
                gaps.append((run, y - run))
                run = 0
    if gaps:
        g, y0 = max(gaps)
        if g > 220:
            issues.append(f"white gap {g}px around y={y0}")
    if issues:
        flags.append((n, "; ".join(issues)))

print(f"flagged pages: {len(flags)}")
for n, why in flags:
    print(f"  p{n}: {why}")
