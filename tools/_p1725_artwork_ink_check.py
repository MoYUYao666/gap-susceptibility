# -*- coding: utf-8 -*-
r"""Render every artwork file and measure how close the ink comes to the canvas edge (clipping check),
then tile the figures into contact sheets for the visual pass. Also render the manuscript into page grids.
"""
import glob
import os
import subprocess

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from PIL import Image

ART = sorted(glob.glob("SUBMISSION/PaperA_MachineLearning/Artwork/*.pdf"))
OUT = os.path.join(os.environ.get("TEMP", "."), "art_check")
os.makedirs(OUT, exist_ok=True)
for f in glob.glob(os.path.join(OUT, "*")):
    os.remove(f)

rows = []
for p in ART:
    base = os.path.join(OUT, os.path.splitext(os.path.basename(p))[0])
    subprocess.run(["pdftoppm", "-r", "200", "-png", p, base], check=True)
    pngs = sorted(glob.glob(base + "*.png"))
    im = Image.open(pngs[0]).convert("L")
    a = np.array(im)
    H, W = a.shape
    ink = a < 245
    ys, xs = np.where(ink)
    if len(xs) == 0:
        rows.append((os.path.basename(p), W, H, -1, -1, -1, -1, "EMPTY"))
        continue
    left, right = int(xs.min()), int(W - 1 - xs.max())
    top, bottom = int(ys.min()), int(H - 1 - ys.max())
    m = min(left, right, top, bottom)
    verdict = "CLIPPED" if m <= 1 else ("tight" if m < 6 else "ok")
    rows.append((os.path.basename(p), W, H, left, right, top, bottom, verdict))

print("%-26s %5s %5s  margin L R T B        verdict" % ("figure", "W", "H"))
for r in rows:
    print("%-26s %5d %5d  %4d %4d %4d %4d   %s" % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))

bad = [r for r in rows if r[7] in ("CLIPPED", "tight", "EMPTY")]
print("\nfigures needing attention:", bad if bad else "none")

# ---- contact sheets: 9 figures per sheet (3x3), width capped for the image reader ----------
for si in range(0, len(ART), 9):
    batch = ART[si:si + 9]
    ims = []
    for p in batch:
        base = os.path.join(OUT, os.path.splitext(os.path.basename(p))[0])
        pngs = sorted(glob.glob(base + "*.png"))
        ims.append(Image.open(pngs[0]).convert("RGB"))
    cw = max(i.width for i in ims)
    ch = max(i.height for i in ims)
    sheet = Image.new("RGB", (cw * 3 + 40, ch * 3 + 40), "white")
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % 3) * (cw + 10), (k // 3) * (ch + 10)))
    if sheet.width > 1560:
        r = 1560 / sheet.width
        sheet = sheet.resize((1560, int(sheet.height * r)), Image.LANCZOS)
    out = os.path.join(OUT, "art_sheet_%02d.png" % (si // 9 + 1))
    sheet.save(out)
    print("sheet:", out, sheet.size, "| figures:", [os.path.basename(b) for b in batch])
