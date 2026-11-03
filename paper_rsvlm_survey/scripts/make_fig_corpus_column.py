# -*- coding: utf-8 -*-
r"""Column-width version of the reference-corpus figure for the GRSM two-column layout.

The original `fig_corpus.pdf` was drawn at 7.0 x 2.6 in; at the width of a single IEEE column its text would shrink to
about 4.5 pt. This script redraws the same data as two stacked panels sized for one column (~3.4 in), with 8 pt text.

Data: screening/core_2026-10-27.json (34 references per theme) and literature/verify_summary_2026-10-27.json
(826 checked, 821 verified, 5 failed) plus the harvest count (833 de-duplicated records) and the number of references
that entered the draft (75).

Usage
  python paper_rsvlm_survey/scripts/make_fig_corpus_column.py
"""
import io
import json
import os

import matplotlib as mpl
mpl.use("Agg")
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False,
    "font.size": 8,
})
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "grrsm", "fig_corpus_column.pdf")


def main():
    screening = json.loads(io.open(os.path.join(ROOT, "screening", "core_2026-10-27.json"),
                                   encoding="utf-8").read())
    verify = json.loads(io.open(os.path.join(ROOT, "literature", "verify_summary_2026-10-27.json"),
                                encoding="utf-8").read())
    themes = [k.split(" ", 1)[1] for k in screening]
    core = [len(v) for v in screening.values()]
    funnel = [833, verify["checked"], verify["verified"], 75]
    funnel_labels = ["harvested\n(de-duplicated)", "with DOI", "verified against\nCrossRef/DataCite", "cited in\nthe draft"]

    fig, axes = plt.subplots(2, 1, figsize=(3.4, 3.5), dpi=300,
                             gridspec_kw={"height_ratios": [1.0, 1.15]})
    ax = axes[0]
    ax.barh(themes[::-1], core[::-1], color="#2a9d8f", height=0.6)
    ax.set_xlabel("references in the screened core set", fontsize=8)
    ax.set_xlim(0, 40)
    ax.tick_params(labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title("(a) core set by theme", fontsize=8, loc="left")

    ax = axes[1]
    bars = ax.bar(range(len(funnel)), funnel, color=["#8d99ae", "#8d99ae", "#2a9d8f", "#e76f51"])
    for i, (b, v) in enumerate(zip(bars, funnel)):
        ax.text(i, v + 25, str(v), ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(range(len(funnel)))
    ax.set_xticklabels(funnel_labels, fontsize=6.8)
    ax.set_ylim(0, 980)
    ax.set_ylabel("records", fontsize=8)
    ax.tick_params(axis="y", labelsize=7.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title("(b) reference integrity funnel", fontsize=8, loc="left")

    fig.tight_layout(pad=0.3)
    fig.savefig(OUT, bbox_inches="tight")
    plt.close(fig)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
