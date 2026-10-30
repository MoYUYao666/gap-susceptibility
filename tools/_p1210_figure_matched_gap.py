# -*- coding: utf-8 -*-
r"""Figure for the matched-gap result: CG against top-1 for three perturbation families.

The three families trace different curves in the (gap, accuracy) plane. The point of the figure is that the mapping is
not a function: two probe points with gaps differing by 0.03 differ by 33 accuracy points, and at a 0.04 tolerance the
spread reaches 52 points.

    python tools/_p1210_figure_matched_gap.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import matplotlib

# --- figure style: Times New Roman text, STIX math (project standing rule, 2026-10-18) ---
import matplotlib as _mpl
_mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False,
})
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "outputs", "analysis", "a1_matched_gap_families.json")
FIGDIR = os.path.join(REPO, "paper_a1", "figures")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(SRC, encoding="utf-8"))
    rows = d["rows"]
    frozen = d["frozen"]
    print("  rows:", len(rows), " frozen:", frozen)

    style = {"T": ("#1f77b4", "o", "translation along the gap direction (lambda)"),
             "P": ("#2ca02c", "s", "contraction toward the class prototype (alpha)"),
             "N": ("#d62728", "^", "isotropic noise on image embeddings (sigma)")}
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    for fam, (c, m, lab) in style.items():
        xs = [r["CG"] for r in rows if r["family"] == fam]
        ys = [r["top1"] for r in rows if r["family"] == fam]
        if not xs:
            continue
        ax.scatter(xs, ys, s=46, c=c, marker=m, label=lab, zorder=3, edgecolors="white", linewidths=0.6)
    # annotate the lambda points of family T
    for r in rows:
        if r["family"] == "T":
            ax.annotate(f"λ={r['param']:g}", (r["CG"], r["top1"]), textcoords="offset points",
                        xytext=(5, 5), fontsize=7, color="#1f77b4")
    ax.axhline(frozen["top1"], color="grey", ls=":", lw=1)
    ax.annotate("frozen", (ax.get_xlim()[1], frozen["top1"]), textcoords="offset points",
                xytext=(-6, 4), fontsize=7, color="grey", ha="right")

    best = d.get("max_matched_gap_spread_tol003")
    if best:
        for k in ("a", "b"):
            p = best[k]
            ax.scatter([p["CG"]], [p["top1"]], s=150, facecolors="none", edgecolors="black", linewidths=1.1, zorder=4)
        ax.annotate(f"same gap (ΔCG={best['dCG']:.3f}),\n{best['spread']:.1f} points apart",
                    (best["a"]["CG"], (best["a"]["top1"] + best["b"]["top1"]) / 2),
                    textcoords="offset points", xytext=(28, -6), fontsize=7.5,
                    arrowprops=dict(arrowstyle="-", lw=0.8, color="black"))
    ax.set_xlabel("centroid gap  CG")
    ax.set_ylabel("zero-shot top-1 (%)")
    ax.set_title("Top-1 is not a function of the modality gap", fontsize=10)
    ax.legend(fontsize=6.8, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=3, frameon=False,
              handletextpad=0.4, columnspacing=1.2)
    ax.grid(alpha=0.25, lw=0.6)
    fig.tight_layout()

    if a.apply:
        os.makedirs(FIGDIR, exist_ok=True)
        for ext in ("pdf", "png"):
            p = os.path.join(FIGDIR, "fig5_matched_gap." + ext)
            fig.savefig(p, dpi=300, bbox_inches="tight")
            print("  wrote", os.path.relpath(p, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
