# -*- coding: utf-8 -*-
"""A4 figures: redundancy, intervention effects, predictive validity."""
from __future__ import annotations
import io, json, os
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
mpl.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix", "pdf.fonttype": 42, "ps.fonttype": 42, "axes.unicode_minus": False,
})
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = json.load(io.open(os.path.join(REPO, "outputs", "a4", "a4_analysis_2026-11-09.json"), encoding="utf-8"))
OUT = os.path.join(REPO, "paper_a4", "figures")
rows = A["cells"]

# Fig 1: CG vs DG
fig, ax = plt.subplots(figsize=(4.2, 3.4))
colors = {"dtd": "#1f77b4", "inat": "#ff7f0e", "nksid": "#2ca02c", "marine": "#d62728", "coco5k": "#9467bd", "flickr30k": "#8c564b"}
for ds in sorted(set(r["dataset"] for r in rows)):
    xs = [r["original_CG"] for r in rows if r["dataset"] == ds]
    ys = [r["original_DG"] for r in rows if r["dataset"] == ds]
    ax.scatter(xs, ys, s=22, color=colors.get(ds, "gray"), label=ds, alpha=0.85, edgecolor="none")
lo = min(min(r["original_CG"], r["original_DG"]) for r in rows) - 0.03
hi = max(max(r["original_CG"], r["original_DG"]) for r in rows) + 0.03
ax.plot([lo, hi], [lo, hi], "--", color="0.6", lw=0.8)
rho = A["C1_original_CG_DG_spearman"]["rho"]
ax.set_xlabel("Centroid gap (CG)"); ax.set_ylabel("Distribution gap (DG)")
ax.set_title(r"Original cells: $\rho = %.3f$" % rho)
ax.legend(fontsize=6, frameon=False, ncol=2)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig1_cg_dg.pdf")); fig.savefig(os.path.join(OUT, "fig1_cg_dg.png"), dpi=200); plt.close(fig)

# Fig 2: intervention effects
keys = ["classification_top1", "R1_i2t", "R1_t2i", "ARI", "mixed_R1"]
labels = ["Class.", "i2t", "t2i", "ARI", "Mixed"]
conds = ["mean_center", "gap_project", "random_project"]
colors2 = ["#1b9e77", "#d95f02", "#7570b3"]
fig, ax = plt.subplots(figsize=(5.2, 3.2))
x = np.arange(len(keys)); w = 0.26
for i, c in enumerate(conds):
    vals = [A["C2_effect_means"][c].get(k, {"mean": np.nan})["mean"] for k in keys]
    ax.bar(x + (i - 1) * w, vals, w, label=c.replace("_", "-"), color=colors2[i], edgecolor="white", linewidth=0.3)
ax.axhline(0, color="0.2", lw=0.8)
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_ylabel("Change relative to original")
ax.legend(fontsize=7, frameon=False)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig2_interventions.pdf")); fig.savefig(os.path.join(OUT, "fig2_interventions.png"), dpi=200); plt.close(fig)

# Fig 3: predictive heatmaps
def heat(kind, axes, title):
    metrics = ["CG", "DG", "spec_eff_rank", "spec_top1_share"]
    targets = ["classification_top1", "R1_i2t", "R1_t2i", "ARI"] if kind == "class" else ["R1_i2t", "R1_t2i"]
    mat = np.full((len(metrics), len(targets)), np.nan)
    for i, m in enumerate(metrics):
        for j, t in enumerate(targets):
            v = A["C3_predictive_spearman"].get("%s__%s__%s" % (kind, m, t), {})
            mat[i, j] = v.get("rho") if v.get("rho") is not None else np.nan
    im = axes.imshow(mat, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    axes.set_xticks(range(len(targets))); axes.set_xticklabels([t.replace("classification_top1", "Class.").replace("R1_", "R1 ").upper() for t in targets], fontsize=7)
    axes.set_yticks(range(len(metrics))); axes.set_yticklabels(["CG", "DG", "Spec. ER", "Spec. top1"], fontsize=7)
    for i in range(len(metrics)):
        for j in range(len(targets)):
            if np.isfinite(mat[i, j]):
                axes.text(j, i, "%.2f" % mat[i, j], ha="center", va="center", fontsize=7,
                          color="white" if abs(mat[i, j]) > 0.5 else "black")
    axes.set_title(title, fontsize=9)
    return im

fig, axs = plt.subplots(1, 2, figsize=(6.4, 2.8), gridspec_kw={"width_ratios": [4, 2]})
im = heat("class", axs[0], "Class datasets")
heat("caption", axs[1], "Caption datasets")
fig.colorbar(im, ax=axs, fraction=0.025, pad=0.02).set_label("Spearman rho", fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig3_validity.pdf")); fig.savefig(os.path.join(OUT, "fig3_validity.png"), dpi=200); plt.close(fig)
print("figures written")
