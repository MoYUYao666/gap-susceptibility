# -*- coding: utf-8 -*-
r"""Figures for A3, generated only from the archived run JSONs.

fig1_provenance.pdf - R@1(image->text) per dataset, provenance arm on the x axis, adaptation site as grouped bars
fig2_scaling.pdf    - R@1 against pair budget for the four provenance arms (sites vision/both), NWPU-Captions

Font rules for this repository: Times New Roman, STIX for maths, pdf.fonttype 42 (CID TrueType, no Type 3).

Usage
  python make_figures.py
"""
import glob
import io
import json
import os
import statistics as st

import matplotlib as mpl
mpl.use("Agg")
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False,
    "font.size": 9,
})
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "figures")
ARMS = ["human", "segmented", "templated", "metadata"]
SITES = ["vision", "text", "both"]
DATASETS = ["rsicd", "rsitmd", "nwpu_captions", "dior_rsvg"]
DS_LABEL = {"rsicd": "RSICD", "rsitmd": "RSITMD", "nwpu_captions": "NWPU-Captions", "dior_rsvg": "DIOR-RSVG"}
COLORS = {"vision": "#264653", "text": "#e76f51", "both": "#2a9d8f"}


def load_aggregate(path):
    if not os.path.exists(path):
        raise SystemExit("missing aggregate: %s (run aggregate_grid.py first)" % path)
    return json.loads(io.open(path, encoding="utf-8").read())


def fig1(agg):
    table = {(e["dataset"], e["arm"], e["site"]): e for e in agg["table"]}
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 5.2), sharey=True)
    axes = axes.ravel()
    width = 0.26
    for ax, ds in zip(axes, DATASETS):
        for i, site in enumerate(SITES):
            xs, ys, errs = [], [], []
            for j, arm in enumerate(ARMS):
                e = table.get((ds, arm, site))
                if not e:
                    continue
                xs.append(j + (i - 1) * width)
                ys.append(e["R@1_i2t"]["mean"])
                errs.append(e["R@1_i2t"]["std"])
            ax.bar(xs, ys, width, yerr=errs, capsize=2, color=COLORS[site],
                   label=site if ds == DATASETS[0] else None, error_kw={"lw": 0.8})
        ax.set_xticks(range(len(ARMS)))
        ax.set_xticklabels(["human", "parsed", "templ.", "meta."], fontsize=9)
        ax.set_title(DS_LABEL[ds], fontsize=10)
        ax.tick_params(axis="y", labelsize=9)
        ax.grid(axis="y", lw=0.3, alpha=0.4)
    for ax in axes[::2]:
        ax.set_ylabel("R@1 (image$\\rightarrow$text)", fontsize=9)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.02), fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out = os.path.join(FIG, "fig1_provenance.pdf")
    fig.savefig(out, bbox_inches="tight")
    print("wrote", out)


def fig2(scaling_rows, main_agg):
    table = {(e["arm"], e["site"]): e for e in main_agg["table"] if e["dataset"] == "nwpu_captions"}
    fig, ax = plt.subplots(figsize=(3.5, 2.9))
    styles = {"human": "-o", "segmented": "-s", "templated": "-^", "metadata": "-d"}
    for arm in ARMS:
        xs, ys, es = [], [], []
        e10 = table.get((arm, "both"))
        if e10:
            xs.append(10)
            ys.append(e10["R@1_i2t"]["mean"])
            es.append(e10["R@1_i2t"]["std"])
        for r in scaling_rows:
            if r["arm"] == arm and r["site"] == "both":
                xs.append(50 if arm == "human" else 31.5)
                ys.append(r["R1_50k"])
                es.append(0.0)
        order = sorted(zip(xs, ys, es))
        ax.errorbar([o[0] for o in order], [o[1] for o in order], yerr=[o[2] for o in order],
                    fmt=styles[arm], ms=4, lw=1.0, capsize=2, label=arm)
    ax.set_xlabel("image--text pairs (thousands)")
    ax.set_ylabel("R@1 (image$\\rightarrow$text), site = both")
    ax.set_xlim(5, 55)
    ax.set_xticks([10, 31.5, 50])
    ax.set_xticklabels(["10", "31.5", "50"])
    ax.tick_params(labelsize=8)
    ax.grid(lw=0.3, alpha=0.4)
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    out = os.path.join(FIG, "fig2_scaling.pdf")
    fig.savefig(out, bbox_inches="tight")
    print("wrote", out)


def main():
    os.makedirs(FIG, exist_ok=True)
    agg = load_aggregate(os.path.join(ROOT, "analysis", "full_10k_aggregate.json"))
    fig1(agg)
    scaling_path = os.path.join(ROOT, "analysis", "h2_scaling.json")
    if os.path.exists(scaling_path):
        rows = json.loads(io.open(scaling_path, encoding="utf-8").read())["rows"]
        fig2(rows, agg)
    else:
        print("skip fig2: h2_scaling.json not found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
