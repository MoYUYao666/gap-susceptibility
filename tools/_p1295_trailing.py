# -*- coding: utf-8 -*-
"""Flag pages whose trailing whitespace exceeds a threshold (float pushed to the next page)."""
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
    idx = np.where(dark.any(axis=1))[0]
    if len(idx) == 0:
        continue
    last = idx.max()
    trailing = 720 - last
    rows.append((n, trailing))
print("pages with trailing whitespace > 250 pt (possible pushed float):")
for n, t in sorted(rows, key=lambda r: -r[1])[:12]:
    print(f"  p{n}: {t} pt trailing")
