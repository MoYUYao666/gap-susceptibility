# -*- coding: utf-8 -*-
"""
Regenerate Paper A Figure 2 (correlation panels) from the reproducible correlation set.

Why: the shipped fig2.png was drawn from a ~17-point scatter while its title read
"n = 81", and the r printed on it (-0.827) came from a separate correlations.json
whose n=81 subset cannot be reconstructed (paper/scripts/generate_figures.py:74-77).
The caption and Table 5 in the manuscript now report the reproducible rule and its
values, so the figure must be drawn from exactly that set.

Input : outputs/analysis/dg_r1_reproducible.json  (written by tools/p1_dg_r1_recompute.py)
Output: paper/figures/fig2.png, paper/figures/fig2.svg
"""
import io
import json
import os
import sys

import sys as _sys
_sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "tools"))
from figure_style import apply_style, figsize_full, save
import matplotlib
matplotlib.use("Agg")
apply_style()          # Times New Roman + STIX + 统一字号
import matplotlib.pyplot as plt
import numpy as np

ROOT = r"D:\Realdesktop\Wan\Important\New"
SRC = os.path.join(ROOT, "outputs", "analysis", "dg_r1_reproducible.json")
FIG = os.path.join(ROOT, "paper合", "figures")


def main():
    with io.open(SRC, encoding="utf-8") as fh:
        d = json.load(fh)
    rows = d["rows"]
    p = d["primary"]
    dg = np.array([r["dg_final"] for r in rows], float)
    cg = np.array([r["cg_final"] for r in rows], float)
    r1 = np.array([r["r1"] for r in rows], float)
    n = len(rows)
    print("plotting n=%d  DG r=%+.3f  CG r=%+.3f" % (n, p["DG_vs_R1"], p["CG_vs_R1"]))

    fig, axes = plt.subplots(1, 2, figsize=figsize_full(0.46))
    for ax, x, rv, lab, col in ((axes[0], dg, p["DG_vs_R1"], "Distribution Gap", "#1f77b4"),
                                (axes[1], cg, p["CG_vs_R1"], "Centroid Gap", "#ff7f0e")):
        ax.scatter(x, r1, c=col, alpha=0.35, s=14, edgecolors="none", rasterized=True)
        z = np.polyfit(x, r1, 1)
        xs = np.linspace(x.min(), x.max(), 100)
        ax.plot(xs, np.polyval(z, xs), "--", color="0.25", lw=1.6)
        ax.set_xlabel(lab, labelpad=11)
        ax.set_ylabel("R@1", labelpad=6)
        ax.set_title("r = %.3f    n = %d" % (rv, n), fontweight="bold", pad=8)
        lo, hi = ax.get_ylim()
        ax.set_ylim(lo - 0.03, hi + 0.06)
    axes[0].set_ylim(axes[0].get_ylim()[0] - 0.02, axes[0].get_ylim()[1] + 0.04)
    fig.tight_layout()
    for ext in ("png", "svg"):
        out = os.path.join(FIG, "fig2." + ext)
        save(fig, out)
        print("wrote %s" % out)
    plt.close(fig)
    return 0


if __name__ == "__main__":
    sys.exit(main())
