# -*- coding: utf-8 -*-
r"""Two figures for the upgrade package (Times New Roman + STIX + CID TrueType).

  P1-7  A1: real fine-tuning campaign. Panel (a) matched-gap scatter over the 72 campaign checkpoints with the widest pair
        annotated; panel (b) margin mass M(0.01) against transfer accuracy.
  P2-12 Paper A: adaptation-site schematic. How the adaptation site sets the gradient-flow direction and therefore the
        initial gap velocity alpha (text-only vs both vs vision-only).

Outputs: paper_a1/figures/fig6_campaign.{pdf,png}, paper合/figures/fig_site_schematic.{pdf,png}

    python tools/_p1333_upgrade_figures.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np
import matplotlib as mpl
mpl.use("Agg")
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False,
})
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")


def campaign_figure(apply):
    camp = json.load(io.open(os.path.join(AN, "a1_campaign.json"), encoding="utf-8"))
    an = json.load(io.open(os.path.join(AN, "a1_campaign_analysis.json"), encoding="utf-8"))
    pts = []
    for key, run in camp["runs"].items():
        for c in run["checkpoints"]:
            pts.append((c["CG"], c["top1"], c["mass_0.01"], run["tower"], run["dataset"]))
    cg = np.array([p[0] for p in pts])
    t1 = np.array([p[1] for p in pts])
    m1 = np.array([p[2] for p in pts])
    tower = np.array([p[3] for p in pts])
    width = np.array([p[4] for p in pts])
    col = {"text": "#1f77b4", "both": "#d62728"}
    mk = {"dtd": "o", "food101": "s", "inat_wild": "^"}
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.5))
    ax = axes[0]
    for tw in ("text", "both"):
        for ds in ("dtd", "food101", "inat_wild"):
            sel = (tower == tw) & (width == ds)
            if sel.any():
                ax.scatter(cg[sel], t1[sel], s=22, c=col[tw], marker=mk[ds], alpha=0.85,
                           edgecolors="k", linewidths=0.25,
                           label=f"{'text' if tw == 'text' else 'both'} / {ds}")
    w = an["pairs"]["widest"]["all"]
    ax.plot([w["a"]["CG"], w["b"]["CG"]], [w["a"]["top1"], w["b"]["top1"]], "k--", lw=1.0)
    ax.annotate(r"$\Delta$CG = %.4f" % w["dCG"] + "\n" + r"$\Delta$top-1 = %.1f" % w["dtop1"],
                xy=((w["a"]["CG"] + w["b"]["CG"]) / 2, (w["a"]["top1"] + w["b"]["top1"]) / 2),
                xytext=(0.42, 38), fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.7))
    ax.set_xlabel("centroid gap CG")
    ax.set_ylabel("ImageNet-5k top-1 (%)")
    ax.set_title("(a) 72 real fine-tuned checkpoints", fontsize=9)
    ax.legend(fontsize=6.2, frameon=False, loc="upper left", ncol=2)
    ax.tick_params(labelsize=7.5)
    ax = axes[1]
    for tw in ("text", "both"):
        sel = tower == tw
        ax.scatter(m1[sel], t1[sel], s=22, c=col[tw], alpha=0.85, edgecolors="k", linewidths=0.25,
                   label="text tower" if tw == "text" else "both towers")
    r = an["correlation"]["M(0.01)"]
    ax.set_xlabel(r"margin mass $M(0.01)$")
    ax.set_ylabel("ImageNet-5k top-1 (%)")
    ax.set_title(r"(b) $r = %.3f$" % r, fontsize=9)
    ax.legend(fontsize=6.5, frameon=False, loc="upper right")
    ax.tick_params(labelsize=7.5)
    for ax in axes:
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.tight_layout()
    base = os.path.join(REPO, "paper_a1", "figures", "fig6_campaign")
    if apply:
        fig.savefig(base + ".pdf", bbox_inches="tight")
        fig.savefig(base + ".png", dpi=300, bbox_inches="tight")
        print("  wrote", os.path.relpath(base + ".pdf", REPO))
    plt.close(fig)


def site_schematic(apply):
    fig, ax = plt.subplots(figsize=(8.4, 2.9))
    ax.axis("off")
    boxes = [
        ("adaptation site", "text tower only\nboth towers\nvision tower only", 0.09),
        ("gradient-flow direction", r"$g=\nabla_\theta L$" + "\n" + "projects on\n" + r"$u$ (gap axis)", 0.38),
        ("gap trajectory", r"$d(CG)/dt = -\alpha\,(CG-CG_\infty)$" + "\n" + r"$\alpha$ sign / size" + "\n" + "depends on site", 0.67),
    ]
    for title, body, x in boxes:
        ax.add_patch(plt.Rectangle((x - 0.085, 0.25), 0.17, 0.5, fill=False, lw=1.2))
        ax.text(x, 0.68, title, ha="center", va="center", fontsize=8.5, fontweight="bold")
        ax.text(x, 0.45, body, ha="center", va="center", fontsize=7.5)
    for x0 in (0.18, 0.47):
        ax.annotate("", xy=(x0 + 0.2, 0.5), xytext=(x0, 0.5),
                    arrowprops=dict(arrowstyle="->", lw=1.0))
    ax.text(0.5, 0.10, r"empirical: $\alpha_{\mathrm{text-only}}<\alpha_{\mathrm{both}}$ on CLIP, reversed on SigLIP",
            ha="center", va="center", fontsize=7.5)
    ax.text(0.5, 0.88, "Adaptation site sets the gradient-flow component along the gap axis, hence the gap dynamics",
            ha="center", va="center", fontsize=8.5)
    base = os.path.join(REPO, "paper合", "figures", "fig_site_schematic")
    if apply:
        fig.savefig(base + ".pdf", bbox_inches="tight")
        fig.savefig(base + ".png", dpi=300, bbox_inches="tight")
        print("  wrote", os.path.relpath(base + ".pdf", REPO))
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    campaign_figure(a.apply)
    site_schematic(a.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
