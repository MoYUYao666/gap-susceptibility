# -*- coding: utf-8 -*-
r"""Local upgrade A4: the two revision figures, drawn only from archived JSONs.

Figure A: pre-registered cross-backbone test - mean Delta CG per backbone and adaptation site with 95% CIs, so the
          CLIP-family narrowing and the OpenCLIP reversal are both visible in one panel.
Figure B: the four descriptions compared on the same 862 trajectories, in-sample R^2 against 5-fold cross-validated
          R^2, which is the panel that answers "is the ODE just flexible?".

Fonts: Times New Roman with STIX maths, CID TrueType embedding (pdf.fonttype = 42), per the project rule.
"""
import io
import json
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False,
    "font.size": 9,
    "axes.linewidth": 0.8,
})

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = "paper合/reframed/figures"
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ Figure A
stats = json.load(io.open("outputs/analysis/paperA_prereg_stats.json", encoding="utf-8"))
backbones = ["CLIP B/32", "CLIP B/16", "OpenCLIP B/32"]
sites = ["text_only", "both", "vision_only"]
labels = {"text_only": "text-only", "both": "both", "vision_only": "vision-only"}

fig, ax = plt.subplots(figsize=(6.4, 2.9))
width = 0.26
xpos = np.arange(len(backbones))
for j, site in enumerate(sites):
    means, errs = [], []
    for b in backbones:
        rec = stats["backbones"].get(b, {}).get(site)
        means.append(rec["mean"] if rec else np.nan)
        errs.append(rec["ci95"] if rec else np.nan)
    ax.bar(xpos + (j - 1) * width, means, width, yerr=errs, capsize=2.5,
           label=labels[site], edgecolor="black", linewidth=0.5,
           color=["#4c72b0", "#dd8452", "#55a868"][j])
ax.axhline(0.0, color="black", linewidth=0.7, linestyle="--")
ax.set_xticks(xpos)
ax.set_xticklabels(backbones)
ax.set_ylabel(r"mean $\Delta$CG (95% CI)")
ax.legend(frameon=False, ncol=3, loc="upper left", fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fa = os.path.join(OUT, "fig_prereg_cross_backbone.pdf")
fig.savefig(fa)
plt.close(fig)
print("wrote", fa)

# ------------------------------------------------------------------ Figure B
cv = json.load(io.open("outputs/analysis/paperA_competing_models_cv.json", encoding="utf-8"))
ins = json.load(io.open("outputs/analysis/paperA_competing_models.json", encoding="utf-8"))
models = ["constant", "linear", "power", "ode"]
nice = {"constant": "constant", "linear": "linear", "power": "power law", "ode": "ODE (this work)"}
ins_r2 = {}
for r in ins.get("series", []):
    for m in models:
        v = r.get(m + "_r2")
        if isinstance(v, (int, float)) and np.isfinite(v):
            ins_r2.setdefault(m, []).append(v)
in_means = [float(np.mean(ins_r2.get(m, [np.nan]))) for m in models]
cv_means = [cv["models"].get(m, {}).get("median_cv_r2", np.nan) for m in models]

fig, ax = plt.subplots(figsize=(4.4, 2.9))
x = np.arange(len(models))
ax.bar(x - 0.19, in_means, 0.36, label="in-sample", color="#4c72b0", edgecolor="black", linewidth=0.5)
ax.bar(x + 0.19, cv_means, 0.36, label="5-fold CV (median)", color="#c44e52", edgecolor="black", linewidth=0.5)
ax.set_xticks(x)
ax.set_xticklabels([nice[m] for m in models], rotation=12)
ax.set_ylabel(r"$R^2$ over 862 trajectories")
ax.legend(frameon=False, fontsize=8, loc="lower right")
ax.spines[["top", "right"]].set_visible(False)
ax.set_ylim(min(0, min(cv_means)) - 0.05, 1.0)
fig.tight_layout()
fb = os.path.join(OUT, "fig_competing_models_cv.pdf")
fig.savefig(fb)
plt.close(fig)
print("wrote", fb)
print("in-sample:", [round(v, 3) for v in in_means])
print("5-fold  :", [round(v, 3) for v in cv_means])
