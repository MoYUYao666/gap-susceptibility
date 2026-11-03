# -*- coding: utf-8 -*-
"""Rank pages by their largest internal white gap, then by ink coverage extremes."""
import glob
import os

import numpy as np
from PIL import Image

OUT = "outputs/_pagecheck"
rows = []
for p in sorted(glob.glob(os.path.join(OUT, "p-*.png"))):
    n = int(os.path.basename(p).split("-")[1].split(".")[0])
    a = np.asarray(Image.open(p).convert("L"))
    dark = a < 200
    dark[730:, :] = False
    rowink = dark.any(axis=1)
    idx = np.where(rowink)[0]
    if len(idx) == 0:
        rows.append((n, 0, 0.0))
        continue
    top, bottom = idx.min(), idx.max()
    gaps, run = [], 0
    for y in range(top, bottom + 1):
        if not rowink[y]:
            run += 1
        else:
            if run:
                gaps.append(run)
                run = 0
    g = max(gaps) if gaps else 0
    rows.append((n, g, dark.mean()))

print("top pages by largest internal white gap:")
for n, g, cov in sorted(rows, key=lambda r: -r[1])[:8]:
    print(f"  p{n}: gap {g}pt | ink {cov*100:.1f}%")
print("\nlowest ink coverage (possible sparse page):")
for n, g, cov in sorted(rows, key=lambda r: r[2])[:6]:
    print(f"  p{n}: ink {cov*100:.1f}% | gap {g}pt")
