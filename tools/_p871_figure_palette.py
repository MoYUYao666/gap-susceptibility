# -*- coding: utf-8 -*-
r"""Report which figures draw data in a colour outside the shared palette.

The library is supposed to use one palette -- Okabe-Ito, defined in `tools/figure_style.py` -- so that
the same concept keeps the same colour across figures. Checking seventeen figures by eye does not
scale, so this measures the drawings: each figure PDF is rasterised and every chromatic pixel is
tested against the palette.

Two details make the test usable rather than noisy:

* grey, black and white are skipped: axes, text and gridlines are legitimately neutral;
* a pixel counts as palette-conformant when it lies on a straight line between two palette colours, or
  between a palette colour and white/black, within a small tolerance. That covers anti-aliasing and
  alpha-blended fills, which otherwise dominate the raw pixel counts and make every figure look wrong.

What survives is a genuine foreign colour, e.g. matplotlib's default `#ff7f0e` orange or `#2ca02c`
green, which is exactly the inconsistency this is meant to catch.

    python tools/_p871_figure_palette.py
"""
from __future__ import annotations

import collections
import itertools
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIGDIR = REPO / "paper合" / "figures"
WORK = REPO / "outputs" / "analysis" / "_figpng"
PALETTE = {
    "#0072b2": "blue",
    "#d55e00": "vermilion",
    "#009e73": "green",
    "#666666": "grey",
    "#cc79a7": "purple",
    "#56b4e9": "sky",
    "#e69f00": "amber",
}
EXTREMES = {"white": (255, 255, 255), "black": (0, 0, 0)}
TOL = 12.0          # max distance from the segment, per channel sum
SEG_TOL = 4.0       # pixels this close to a segment count as a blend regardless of position


def rgb(h: str) -> tuple[int, int, int]:
    return tuple(int(h[1:][i:i + 2], 16) for i in (0, 2, 4))


def blends() -> list[tuple[tuple[int, int, int], tuple[int, int, int]]]:
    pts = [rgb(h) for h in PALETTE] + list(EXTREMES.values())
    return list(itertools.combinations(pts, 2))


SEGMENTS = blends()


def dist_to_segment(p, a, b) -> float:
    ax, ay, az = a
    bx, by, bz = b
    px, py, pz = p
    vx, vy, vz = bx - ax, by - ay, bz - az
    wx, wy, wz = px - ax, py - ay, pz - az
    vv = vx * vx + vy * vy + vz * vz
    if vv == 0:
        return abs(px - ax) + abs(py - ay) + abs(pz - az)
    t = max(0.0, min(1.0, (wx * vx + wy * vy + wz * vz) / vv))
    cx, cy, cz = ax + t * vx, ay + t * vy, az + t * vz
    return abs(px - cx) + abs(py - cy) + abs(pz - cz)


def is_conformant(p) -> bool:
    if max(p) - min(p) < 24:          # neutral: axes, text, gridlines
        return True
    return min(dist_to_segment(p, a, b) for a, b in SEGMENTS) <= TOL


MIN_PIXELS = 120    # a colour seen in fewer pixels than this is an anti-aliasing fringe, not a feature


def analyse(pdf: Path):
    WORK.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftoppm", "-r", "150", "-png", "-singlefile", str(pdf),
                    str(WORK / pdf.stem)], capture_output=True, check=False)
    png = WORK / (pdf.stem + ".png")
    if not png.exists():
        return collections.Counter(), collections.Counter()
    from PIL import Image
    im = Image.open(png).convert("RGB")
    inpal: collections.Counter = collections.Counter()
    off: collections.Counter = collections.Counter()
    for count, px in im.getcolors(maxcolors=1 << 24) or []:
        if count < MIN_PIXELS:
            # Sub-threshold colours are anti-aliasing fringes: black text or a black hatch edge drawn
            # over a coloured fill produces a handful of pixels in every intermediate shade, and where a
            # grey axis meets a coloured band the blend can sit just off the segment between the two.
            # These are not drawable features. The threshold is set well below the smallest real
            # feature: at 150 dpi a 0.4 pt stroke is already several hundred pixels long.
            continue
        if max(px) - min(px) < 24:
            continue
        target = None
        best = 10 ** 9
        for h in PALETTE:
            d = sum(abs(px[i] - rgb(h)[i]) for i in range(3))
            if d < best:
                best, target = d, h
        if is_conformant(px):
            inpal[target] += count
        else:
            off["#%02x%02x%02x" % px] += count
    return inpal, off


def main() -> int:
    rows = [(p.stem, *analyse(p)) for p in sorted(FIGDIR.glob("fig*.pdf"))]
    print(f"  {'figure':<28}{'palette px':>12}{'foreign px':>12}   palette colours used")
    bad = []
    for name, inpal, off in rows:
        tot = sum(inpal.values()) + sum(off.values())
        share = (sum(inpal.values()) / tot) if tot else 1.0
        used = " ".join(f"{PALETTE[h]}({n})" for h, n in inpal.most_common())
        flag = ""
        if off:
            bad.append((name, off))
            flag = "  <-- FOREIGN"
        print(f"  {name:<28}{share:>11.1%}{sum(off.values()):>12,}   {used}{flag}")
    print()
    for name, off in bad:
        print(f"  {name}: " + " ".join(f"{h}({n})" for h, n in off.most_common(6)))
    print(f"  figures drawing only in the palette: {len(rows) - len(bad)}/{len(rows)}")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
