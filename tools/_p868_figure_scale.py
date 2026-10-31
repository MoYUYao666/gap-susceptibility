# -*- coding: utf-8 -*-
r"""Check that each figure's natural width matches the width the LaTeX asks for.

The library was made consistent on 2026-10-06 by exporting each figure at its final size, so that
LaTeX scales by 1.00x and every figure's text is the same physical size. That property is invisible
unless it is measured, and one figure (the new stratified plot) had drifted to 0.95\textwidth
against a canvas built for 0.88, which is exactly the drift this checks for.

    python tools/_p868_figure_scale.py
"""
from __future__ import annotations

import io
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIGDIR = REPO / "paper合" / "figures"
TEXDIRS = [REPO / "paper合" / "sections", REPO / "paper合" / "NC_submission" / "latex_source" / "sections"]
TEXTWIDTH_IN = 4.760          # measured with tools/_measure_textblock.py
TOL = 0.05                    # inches


def declared() -> dict[str, float]:
    out: dict[str, float] = {}
    pat = re.compile(r"\\includegraphics\[width=([\d.]+)\\textwidth\]\{figures/([^}]+)\}")
    for d in TEXDIRS:
        for p in sorted(d.glob("*.tex")):
            for m in pat.finditer(io.open(p, encoding="utf-8").read()):
                out[m.group(2)] = float(m.group(1))
    return out


def natural_in(p: Path) -> tuple[float, float]:
    out = subprocess.run(["pdfinfo", str(p)], capture_output=True).stdout.decode("utf-8", "replace")
    m = re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", out)
    assert m, f"cannot read the page size of {p.name}"
    return float(m.group(1)) / 72.0, float(m.group(2)) / 72.0


def main() -> int:
    decl = declared()
    bad = 0
    print(f"  {'figure':<30}{'natural':>9}{'target':>9}{'scale':>8}")
    for name in sorted(decl):
        p = FIGDIR / name
        if not p.exists():
            print(f"  {name:<30}  MISSING")
            bad += 1
            continue
        w, _h = natural_in(p)
        target = decl[name] * TEXTWIDTH_IN
        scale = target / w
        flag = "" if abs(w - target) <= TOL else "  <-- off"
        if flag:
            bad += 1
        print(f"  {name:<30}{w:>8.3f}in{target:>8.3f}in{scale:>7.2f}x{flag}")
    print(f"  figures whose natural width matches the requested width: "
          f"{len(decl) - bad}/{len(decl)}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
