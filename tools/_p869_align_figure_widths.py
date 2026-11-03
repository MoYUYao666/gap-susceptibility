# -*- coding: utf-8 -*-
r"""Align two `\includegraphics` widths with the sizes the figures are now drawn at.

The library rule (2026-10-06) is that each figure is exported at its final printed size so LaTeX scales
it by 1.00x, which is what keeps the text inside every figure the same physical size. Two figures had
drifted, and `tools/_p868_figure_scale.py` shows both:

* `fig15_stratified_dg_r1` was widened to 0.95\textwidth when it was added. Its canvas is the standard
  0.88 width, so LaTeX was scaling it by 1.08x (its text came out slightly larger than every other
  figure); it is moved back to 0.88.
* `fig2_v5_falsification` was drawn for 0.78\textwidth while the supplement asks for 0.88, so LaTeX
  scaled it by 1.05x. It is now drawn at the full width, and the supplement is moved to 0.88 to match.

Only the width argument changes; the figure filenames and everything else on the lines are untouched.

    python tools/_p869_align_figure_widths.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOCS = [
    (REPO / "paper合" / "sections" / "empirical.tex", "figures/fig15_stratified_dg_r1.pdf", "0.95", "0.88"),
    (REPO / "paper合" / "NC_submission" / "latex_source" / "sections" / "empirical.tex",
     "figures/fig15_stratified_dg_r1.pdf", "0.95", "0.88"),
    (REPO / "paper合" / "sections" / "supplement.tex", "figures/fig2_v5_falsification.pdf", "0.78", "0.88"),
    (REPO / "paper合" / "NC_submission" / "latex_source" / "sections" / "supplement.tex",
     "figures/fig2_v5_falsification.pdf", "0.78", "0.88"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    total = 0
    for path, fig, old_w, new_w in DOCS:
        assert path.exists(), f"missing {path}"
        t = io.open(path, encoding="utf-8").read()
        old = f"\\includegraphics[width={old_w}\\textwidth]{{{fig}}}"
        new = f"\\includegraphics[width={new_w}\\textwidth]{{{fig}}}"
        c = t.count(old)
        if c == 0 and t.count(new) == 1:
            print(f"  {path.name}: already at {new_w} for {Path(fig).name}")
            continue
        assert c == 1, f"{path.name}: expected 1 occurrence of the {old_w} line, found {c}"
        if a.apply:
            io.open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
        total += 1
        print(f"  {'updated' if a.apply else 'would update'} {path.name}: {Path(fig).name} "
              f"{old_w} -> {new_w} textwidth")

    if not a.apply:
        print("  (dry run)")
        return 0
    for path, fig, _o, new_w in DOCS:
        t = io.open(path, encoding="utf-8").read()
        assert f"\\includegraphics[width={new_w}\\textwidth]{{{fig}}}" in t
    print(f"  {total} line(s) updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
