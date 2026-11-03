# -*- coding: utf-8 -*-
r"""Item F: a one-page graphical abstract summarising the paper's four panels of evidence.

Panels (all data read from the archives):
  A  matched gap: centroid gap against top-1 across three perturbation families, widest matched pair marked
  B  prompt templates: gap against top-1 for ten templates on five backbones
  C  threshold transfer: balanced accuracy when a threshold fitted on one setting is applied to another
  D  monitoring: mean regret of each checkpoint-selection rule with bootstrap intervals

Writes paper_a1/figures/graphical_abstract.pdf and .png, and a standalone one-page PDF for the portal.

    python tools/_p1276_graphical_abstract.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
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
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")
FIG = os.path.join(REPO, "paper_a1", "figures")
OUT_PNG = os.path.join(FIG, "graphical_abstract.png")
OUT_PDF = os.path.join(FIG, "graphical_abstract.pdf")

C = {"T": "#1f77b4", "P": "#d62728", "N": "#7f7f7f", "frozen": "#000000"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    fam = json.load(io.open(os.path.join(AN, "a1_matched_gap_families.json"), encoding="utf-8"))
    prompt = json.load(io.open(os.path.join(AN, "a1_prompt_template_gap.json"), encoding="utf-8"))
    thr = json.load(io.open(os.path.join(AN, "a1_threshold_transfer.json"), encoding="utf-8"))
    mon = json.load(io.open(os.path.join(AN, "a1_monitor_uncertainty.json"), encoding="utf-8"))

    fig, axes = plt.subplots(2, 2, figsize=(11, 7.4))
    fig.suptitle("The modality gap is not a universal health metric", fontsize=13, fontweight="bold", y=0.99)

    # A: matched gap
    ax = axes[0, 0]
    for key in ("T", "P", "N"):
        rows = [r for r in fam["rows"] if r["family"] == key]
        ax.scatter([r["CG"] for r in rows], [r["top1"] for r in rows], s=28, c=C[key], label=key, alpha=0.9)
    b = fam["max_matched_gap_spread_tol003"]
    if b:
        for r in (b["a"], b["b"]):
            ax.scatter([r["CG"]], [r["top1"]], s=90, facecolors="none", edgecolors="k", linewidths=1.2)
        ax.annotate("%.1f points at $|\\Delta CG|=%.3f$" % (b["spread"], b["dCG"]),
                    xy=(b["CG"], (b["a"]["top1"] + b["b"]["top1"]) / 2), fontsize=8,
                    xytext=(b["CG"] + 0.05, (b["a"]["top1"] + b["b"]["top1"]) / 2))
    ax.axhline(fam["frozen"]["top1"], ls="--", lw=0.8, c="k")
    ax.set_xlabel("centroid gap"); ax.set_ylabel("zero-shot top-1 (%)")
    ax.set_title("A  matched gap: three families, one gap value", fontsize=9)
    ax.legend(fontsize=7, frameon=False)

    # B: prompt templates
    ax = axes[0, 1]
    marks = ["o", "s", "^", "D", "v"]
    for (tag, v), mk in zip(prompt["models"].items(), marks):
        ax.scatter([r["CG"] for r in v["rows"]], [r["top1"] for r in v["rows"]], s=22, marker=mk, label=tag, alpha=0.85)
    ax.set_xlabel("centroid gap"); ax.set_ylabel("zero-shot top-1 (%)")
    ax.set_title("B  prompt template only: gap moves, accuracy barely", fontsize=9)
    ax.legend(fontsize=6, frameon=False)

    # C: threshold transfer
    ax = axes[1, 0]
    settings = list(thr["settings"].keys())
    M = np.full((len(settings), len(settings)), np.nan)
    for i, s in enumerate(settings):
        for j, t in enumerate(settings):
            if s == t:
                continue
            v = thr["transfer"].get(s, {}).get(t, {}).get("balanced_accuracy")
            if v is not None:
                M[i, j] = v
    im = ax.imshow(M, cmap="RdBu_r", vmin=0.0, vmax=1.0)
    ax.set_xticks(range(len(settings)), [s[:9] for s in settings], fontsize=6, rotation=45, ha="right")
    ax.set_yticks(range(len(settings)), [s[:9] for s in settings], fontsize=6)
    ax.set_title("C  a threshold fitted elsewhere: balanced accuracy", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    for (i, j), v in np.ndenumerate(M):
        if np.isfinite(v):
            ax.text(j, i, "%.2f" % v, ha="center", va="center", fontsize=5.5,
                    color="k" if 0.25 < v < 0.75 else "w")

    # D: monitoring regret
    ax = axes[1, 1]
    rules = ["argmax_tau", "cusum", "patience2", "last_epoch"]
    labels = ["$\\tau$-max", "CUSUM", "patience-2", "last epoch"]
    vals = [mon["rules"][r]["mean"] for r in rules]
    los = [mon["rules"][r]["mean"] - mon["rules"][r]["ci95"][0] for r in rules]
    his = [mon["rules"][r]["ci95"][1] - mon["rules"][r]["mean"] for r in rules]
    ax.bar(labels, vals, yerr=[los, his], capsize=4, color=["#2ca02c", "#17becf", "#bcbd22", "#8c564b"])
    ax.set_ylabel("regret vs labelled oracle (points)")
    ax.set_title("D  label-free checkpoint selection", fontsize=9)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    if not a.apply:
        print("  (dry run)")
        return 0
    os.makedirs(FIG, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=300)
    fig.savefig(OUT_PDF)
    print("  wrote", os.path.relpath(OUT_PNG, REPO), "and", os.path.relpath(OUT_PDF, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
