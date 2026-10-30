# -*- coding: utf-8 -*-
r"""Regenerate Paper A's Figure 1 (adaptation-site schematic) with text that fits its boxes.

The old asset had box text overflowing the frame. This redraws the same diagram: three boxes
(adaptation site -> gradient-flow direction -> gap trajectory), two arrows, a header line and a
bottom caveat line that carries no numbers (the empirical ordering lives in Table 1).
Fonts follow the repository rule: Times New Roman text, STIX math, CID TrueType (pdf.fonttype 42).
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False,
})

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "paper合", "figures", "fig_site_schematic")

fig, ax = plt.subplots(figsize=(7.0, 2.35))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

BOX_H = 0.46
Y0 = 0.30
boxes = [
    (0.015, 0.235, "adaptation site",
     ["text tower only", "both towers", "vision tower only"]),
    (0.375, 0.245, "gradient-flow direction",
     ["projection of $g_v$ on $u$", "(the $\\Gamma$ axis)"]),
    (0.735, 0.250, "gap trajectory",
     ["$CG_{\\mathrm{shallow}}\\!\\to\\!CG_{\\mathrm{deep}}$", "$\\alpha$: which term dominates"]),
]

for x, w, title, lines in boxes:
    ax.add_patch(FancyBboxPatch((x, Y0), w, BOX_H, boxstyle="round,pad=0.004,rounding_size=0.012",
                                linewidth=0.9, edgecolor="black", facecolor="white"))
    ax.text(x + w / 2, Y0 + BOX_H - 0.085, title, ha="center", va="center", fontsize=9.2, fontweight="bold")
    n = len(lines)
    for k, line in enumerate(lines):
        ax.text(x + w / 2, Y0 + BOX_H - 0.175 - k * 0.088, line,
                ha="center", va="center", fontsize=8.2)

arrow_kw = dict(arrowstyle="-|>", mutation_scale=9, linewidth=0.9, color="black")
ax.add_patch(FancyArrowPatch((0.252, Y0 + BOX_H / 2), (0.372, Y0 + BOX_H / 2), **arrow_kw))
ax.add_patch(FancyArrowPatch((0.622, Y0 + BOX_H / 2), (0.732, Y0 + BOX_H / 2), **arrow_kw))

ax.text(0.5, 0.93, "Adaptation site sets the gradient-flow component along the gap axis, "
                   "hence the gap dynamics", ha="center", va="center", fontsize=9.0)
ax.text(0.5, 0.13,
        "empirical: which site gives the smallest $|\\Delta CG|$ depends on the site itself "
        "and on the pre-training objective (Table 1)",
        ha="center", va="center", fontsize=8.6)

fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
fig.savefig(OUT + ".pdf", bbox_inches="tight", pad_inches=0.02)
fig.savefig(OUT + ".png", dpi=300, bbox_inches="tight", pad_inches=0.02)
print("wrote", OUT + ".pdf", os.path.getsize(OUT + ".pdf"), "bytes")
