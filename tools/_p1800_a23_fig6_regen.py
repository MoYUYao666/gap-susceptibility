# -*- coding: utf-8 -*-
r"""Regenerate A23 figure 6 (sonar gap-surgery dose-response) with print-legal font sizes.

Why: the IEEE JOE editorial office requires every lettering and symbol in every figure to be at least 8 pt in print. The
figure had no surviving generator script, so this rebuilds it from the archive `outputs/sonar_protocol_full.json` (the same
numbers the caption and Table `tab:sonar-exact` cite) and sets every font to 10 pt at a figure width equal to the printed
width (0.82 \textwidth = 5.87 in for IEEEtran), so the printed size is 10 pt, not a scaled-down 6-7 pt.

Panels: (a) order preservation tau vs lambda; (b) zero-shot retention (top-1 as a percentage of each model's frozen top-1).
Typography: Times New Roman + STIX, 300 dpi PNG (the manuscript includes PNGs for this figure set).
"""
import io
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 10,
    "axes.titlesize": 10,
    "axes.labelsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTDIR = "paper_a2/figures"
os.makedirs(OUTDIR, exist_ok=True)

d = json.load(io.open("outputs/sonar_protocol_full.json", encoding="utf-8"))
SERIES = [
    ("clip_frozen", "CLIP frozen", "#4C72B0", "o"),
    ("sonar_ft_full", "SonarCLIP (full 2,617)", "#C44E52", "s"),
    ("clip_flickrft", "CLIP + Flickr (terrestrial)", "#55A868", "^"),
]

fig, axes = plt.subplots(1, 2, figsize=(5.87, 2.35))
ax = axes[0]
for key, label, color, marker in SERIES:
    rows = sorted([r for r in d[key]["rows"] if isinstance(r["lambda"], (int, float))], key=lambda r: float(r["lambda"]))
    ax.plot([r["lambda"] for r in rows], [r["tau_meas"] for r in rows], marker=marker, ms=4, lw=1.2,
            color=color, label=label)
ax.axhline(1.0, ls=":", c="gray", lw=0.8)
ax.set_xlabel(r"$\lambda$")
ax.set_ylabel(r"$\tau$ (order preservation)")
ax.set_ylim(-0.15, 1.05)
ax.legend(fontsize=10, frameon=True, framealpha=0.95, loc="lower left")
ax.set_title("(a) Order preservation", fontsize=10)

ax = axes[1]
for key, label, color, marker in SERIES:
    rows = sorted([r for r in d[key]["rows"] if isinstance(r["lambda"], (int, float))], key=lambda r: float(r["lambda"]))
    base = d[key]["top1_0"]
    ax.plot([r["lambda"] for r in rows], [100.0 * r["top1"] / base for r in rows], marker=marker, ms=4, lw=1.2,
            color=color, label=label)
ax.set_xlabel(r"$\lambda$")
ax.set_ylabel("zero-shot retention (% of frozen)")
ax.set_title("(b) Zero-shot retention", fontsize=10)

for ax in axes:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, "fig6_sonar_lambda.png"), bbox_inches="tight")
print("wrote", os.path.join(OUTDIR, "fig6_sonar_lambda.png"))
