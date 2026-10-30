# -*- coding: utf-8 -*-
"""Re-run the page check with the page-number footer excluded from the margin test."""
import glob
import json
import os

import numpy as np
from PIL import Image

OUT = "outputs/_pagecheck"
pages = sorted(glob.glob(os.path.join(OUT, "p-*.png")))
flags = []
for p in pages:
    n = int(os.path.basename(p).split("-")[1].split(".")[0])
    a = np.asarray(Image.open(p).convert("L"))
    h, w = a.shape
    dark = a < 200
    dark[730:, :] = False          # footer (page number) is not content
    cov = dark.mean()
    cols = np.where(dark.any(axis=0))[0]
    rows = np.where(dark.any(axis=1))[0]
    if len(cols) == 0:
        flags.append((n, "BLANK page"))
        continue
    left, right = cols.min(), cols.max()
    top, bottom = rows.min(), rows.max()
    issues = []
    if cov < 0.02:
        issues.append(f"nearly blank (ink {cov * 100:.1f}%)")
    if right > 552:
        issues.append(f"content beyond right margin (x={right})")
    if left < 60:
        issues.append(f"content beyond left margin (x={left})")
    if top < 40:
        issues.append(f"content above top margin (y={top})")
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
        if g > 240:
            issues.append(f"white gap {g}pt around y={y0}")
    if issues:
        flags.append((n, "; ".join(issues)))

print(f"pages checked: {len(pages)} | flagged: {len(flags)}")
for n, why in flags:
    print(f"  p{n}: {why}")
