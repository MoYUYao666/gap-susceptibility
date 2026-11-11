# -*- coding: utf-8 -*-
"""Top-journal-style A4 figures: design, CG-DG regime scatter, forest plot, validity heatmap."""
from __future__ import annotations
import io, json, os
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
mpl.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
                     "mathtext.fontset": "stix", "pdf.fonttype": 42, "ps.fonttype": 42,
                     "axes.unicode_minus": False, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
                     "ytick.major.width": 0.6, "font.size": 8})
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "paper_a4", "figures")
A = json.load(io.open(os.path.join(REPO, "outputs", "a4", "a4_controlled_analysis_2026-11-10.json"), encoding="utf-8"))
BOOT = json.load(io.open(os.path.join(REPO, "outputs", "a4", "a4_controlled_bootstrap_2026-11-10.json"), encoding="utf-8"))
CTRL = json.load(io.open(os.path.join(REPO, "outputs", "a4", "a4_controlled_peft_2026-11-10.json"), encoding="utf-8"))
FROZEN = json.load(io.open(os.path.join(REPO, "outputs", "a4", "a4_analysis_2026-11-09.json"), encoding="utf-8"))
COL = {"both": "#0072B2", "text": "#D55E00", "vision": "#009E73", "frozen": "#555555"}


def fig_design():
    fig, ax = plt.subplots(figsize=(7.0, 3.1))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4.2); ax.axis("off")
    boxes = [
        (0.15, 1.2, 2.9, 1.8, "Frozen benchmark", "5 encoders x 6 datasets\n30 cells, 4 readouts\n3 interventions + placebo"),
        (3.45, 1.2, 2.9, 1.8, "Controlled PEFT", "90 runs / 270 checkpoints\n2 backbones, 3 datasets\n3 sites, ranks 4/16/64"),
        (6.75, 1.2, 2.9, 1.8, "Validity tests", "CG-DG redundancy\nmetric -> readout prediction\nintervention + placebo\nsite / regime transport"),
    ]
    for (x, y, w, h, title, body) in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.06",
                                    linewidth=0.8, edgecolor="0.25", facecolor="0.95"))
        ax.text(x + 0.15, y + h - 0.28, title, fontsize=10.5, fontweight="bold", va="top")
        ax.text(x + 0.15, y + h - 0.62, body, fontsize=9.0, va="top", linespacing=1.25)
    ax.add_patch(FancyArrowPatch((3.05, 2.1), (3.42, 2.1), arrowstyle="-|>", mutation_scale=8, linewidth=0.8, color="0.25"))
    ax.add_patch(FancyArrowPatch((6.35, 2.1), (6.72, 2.1), arrowstyle="-|>", mutation_scale=8, linewidth=0.8, color="0.25"))
    ax.text(5.0, 3.65, "What does the modality gap measure?", ha="center", fontsize=10.5, fontweight="bold")
    ax.text(5.0, 0.55, "Question: for which readout, intervention and regime is a gap/geometry metric a valid health metric?",
            ha="center", fontsize=8.2, style="italic")
    fig.tight_layout(pad=0.2)
    fig.savefig(os.path.join(OUT, "fig1_design.pdf"), bbox_inches="tight", pad_inches=0.02); fig.savefig(os.path.join(OUT, "fig1_design.png"), dpi=250, bbox_inches="tight", pad_inches=0.02); plt.close(fig)


def fig_cg_dg():
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.0), gridspec_kw={"wspace": 0.32})
    # frozen cells
    cells = FROZEN["cells"]
    for ds in sorted(set(r["dataset"] for r in cells)):
        x = [r["original_CG"] for r in cells if r["dataset"] == ds]
        y = [r["original_DG"] for r in cells if r["dataset"] == ds]
        axs[0].scatter(x, y, s=20, alpha=0.85, edgecolor="white", linewidth=0.3, label=ds)
    lo = min(min(r["original_CG"], r["original_DG"]) for r in cells) - 0.03
    hi = max(max(r["original_CG"], r["original_DG"]) for r in cells) + 0.03
    axs[0].plot([lo, hi], [lo, hi], color="0.65", lw=0.7, ls="--")
    r = FROZEN["C1_original_CG_DG_spearman"]["rho"]
    axs[0].set_title("Frozen cells (n=30), rho=%.3f" % r, fontsize=9)
    axs[0].set_xlabel("CG"); axs[0].set_ylabel("DG"); axs[0].legend(fontsize=6.5, frameon=False, loc="upper left")
    # controlled checkpoints
    for tw in ("both", "text", "vision"):
        x, y = [], []
        for run in CTRL["runs"]:
            if run["run"].get("tower", "both") != tw: continue
            for e in run["epochs"]:
                x.append(e["conditions"]["original"]["CG"]); y.append(e["conditions"]["original"]["DG"])
        axs[1].scatter(x, y, s=7, alpha=0.28, color=COL[tw], edgecolor="none", label=tw)
    r2 = A["by_tower"]["both"]["CG"] if False else A["CG_DG"]["original"]["rho"]
    axs[1].set_title("Controlled checkpoints (n=270), rho=%.3f" % r2, fontsize=9)
    axs[1].set_xlabel("CG"); axs[1].set_ylabel("DG"); axs[1].legend(fontsize=6.5, frameon=False, loc="upper left")
    for ax in axs:
        ax.tick_params(labelsize=8, length=2.8, pad=2)
        for s in ax.spines.values(): s.set_linewidth(0.6)
        ax.grid(alpha=0.15, lw=0.4)
    fig.text(0.5, -0.02, "Dashed line: CG=DG. Frozen points are encoder x dataset cells; controlled points are checkpoints, coloured by adaptation site.", ha="center", fontsize=7.0)
    fig.tight_layout(pad=0.2)
    fig.savefig(os.path.join(OUT, "fig2_cg_dg.pdf"), bbox_inches="tight", pad_inches=0.02); fig.savefig(os.path.join(OUT, "fig2_cg_dg.png"), dpi=250, bbox_inches="tight", pad_inches=0.02); plt.close(fig)


def fig_forest():
    reads = ["classification_top1", "R1_i2t", "R1_t2i", "ARI"]
    labels = ["Class.", "i2t", "t2i", "ARI"]
    sites = ["both", "text", "vision"]
    conds = [("mean_center", "Mean-center"), ("gap_project", "Gap-project")]
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.9), sharey=True, gridspec_kw={"wspace": 0.12})
    y0 = np.arange(len(reads))[::-1]
    for ax, (cond, title) in zip(axs, conds):
        for si, site in enumerate(sites):
            vals = [BOOT["by_site"][site]["%s__%s" % (cond, k)] for k in reads]
            means = np.array([v["mean"] for v in vals]); lo = np.array([v["lo"] for v in vals]); hi = np.array([v["hi"] for v in vals])
            off = (si - 1) * 0.18
            ax.errorbar(means, y0 + off, xerr=[means - lo, hi - means], fmt="o", ms=3.2,
                        color=COL[site], ecolor=COL[site], elinewidth=0.8, capsize=1.8, label=site)
        ax.axvline(0, color="0.35", lw=0.7, ls="--")
        ax.set_yticks(y0); ax.set_yticklabels(labels, fontsize=8.5)
        ax.set_title(title, fontsize=8); ax.tick_params(labelsize=8, length=2.8, pad=2)
        ax.set_xlabel("Change vs original (points)", fontsize=8)
        for s in ax.spines.values(): s.set_linewidth(0.6)
        ax.grid(axis="x", alpha=0.15, lw=0.4)
        ax.legend(fontsize=6.8, frameon=False, loc="lower left")
    fig.tight_layout(pad=0.2)
    fig.savefig(os.path.join(OUT, "fig3_forest.pdf"), bbox_inches="tight", pad_inches=0.02); fig.savefig(os.path.join(OUT, "fig3_forest.png"), dpi=250, bbox_inches="tight", pad_inches=0.02); plt.close(fig)


def fig_validity():
    metrics = ["CG", "DG", "spec_eff_rank", "spec_top1_share"]
    mlabels = ["CG", "DG", "Spec. ER", "Spec. top-1"]
    targets = ["classification_top1", "R1_i2t", "R1_t2i", "ARI"]
    tlabels = ["Class.", "i2t", "t2i", "ARI"]
    frozen = np.full((4, 4), np.nan); ctrl = np.full((4, 4), np.nan)
    for i, m in enumerate(metrics):
        for j, t in enumerate(targets):
            v = FROZEN["C3_predictive_spearman"].get("class__%s__%s" % (m, t), {})
            frozen[i, j] = v.get("rho") if v.get("rho") is not None else np.nan
            v = A["predictive"].get("%s__%s" % (m, t), {})
            ctrl[i, j] = v.get("rho") if v.get("rho") is not None else np.nan
    fig, axs = plt.subplots(1, 2, figsize=(6.2, 2.8), gridspec_kw={"wspace": 0.35})
    for ax, mat, title in zip(axs, [frozen, ctrl], ["Frozen cells", "Controlled checkpoints"]):
        im = ax.imshow(mat, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(range(4)); ax.set_xticklabels(tlabels, fontsize=8)
        ax.set_yticks(range(4)); ax.set_yticklabels(mlabels, fontsize=8)
        ax.set_title(title, fontsize=9); ax.tick_params(length=2.5)
        for i in range(4):
            for j in range(4):
                if np.isfinite(mat[i, j]):
                    ax.text(j, i, "%.2f" % mat[i, j], ha="center", va="center", fontsize=7.2,
                            color="white" if abs(mat[i, j]) > 0.5 else "black")
    fig.colorbar(im, ax=axs, fraction=0.025, pad=0.02).set_label("Spearman rho", fontsize=8)
    fig.tight_layout(pad=0.2)
    fig.savefig(os.path.join(OUT, "fig4_validity.pdf"), bbox_inches="tight", pad_inches=0.02); fig.savefig(os.path.join(OUT, "fig4_validity.png"), dpi=250, bbox_inches="tight", pad_inches=0.02); plt.close(fig)


if __name__ == "__main__":
    fig_design(); fig_cg_dg(); fig_forest(); fig_validity(); print("figures written")
