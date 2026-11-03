# -*- coding: utf-8 -*-
r"""Figures for the remote-sensing vision-language survey.

Two data-backed panels, nothing decorative: (a) the screened core set by theme bucket, (b) the reference-integrity funnel
from raw harvest to verified citations. Both are drawn from the pipeline's own JSON files, so the figure cannot drift from
the corpus it describes.

Typography follows the repository rule: Times New Roman text, STIX maths, CID TrueType embedding (pdf.fonttype 42).

Outputs
  paper_rsvlm_survey/figures/fig_corpus.pdf  (and .png for inspection)
"""
import io
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False,
    "font.size": 9,
})

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAMP = "2026-10-27"
core = json.load(io.open("paper_rsvlm_survey/screening/core_%s.json" % STAMP, encoding="utf-8"))
summary = json.load(io.open("paper_rsvlm_survey/literature/summary_%s.json" % STAMP, encoding="utf-8"))
vsum = json.load(io.open("paper_rsvlm_survey/literature/verify_summary_%s.json" % STAMP, encoding="utf-8"))

buckets = list(core.keys())
counts = [len(core[b]) for b in buckets]
labels = [b.split(" ", 1)[1] if " " in b else b for b in buckets]

fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7), gridspec_kw={"width_ratios": [1.15, 1.0]})

ax = axes[0]
y = range(len(buckets))
ax.barh(list(y), counts, color="#4a6fa5", height=0.62)
ax.set_yticks(list(y))
ax.set_yticklabels(labels)
ax.invert_yaxis()
ax.set_xlabel("references in the screened core set")
ax.set_title("(a) Core set by theme", loc="left", fontsize=9)
for yi, c in zip(y, counts):
    ax.text(c + 1, yi, str(c), va="center", fontsize=8)
ax.set_xlim(0, max(counts) * 1.22)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

ax = axes[1]
stages = ["harvested\n(deduplicated)", "with DOI", "verified against\nCrossRef/DataCite", "cited in the draft"]
vals = [summary["n_dedup"], summary["n_with_doi"], vsum["verified"], 75]
colors = ["#9aa7b4", "#7d93aa", "#4a6fa5", "#2f4f76"]
bars = ax.bar(range(len(stages)), vals, color=colors, width=0.62)
ax.set_xticks(range(len(stages)))
ax.set_xticklabels(stages, fontsize=7)
ax.set_ylabel("records")
ax.set_title("(b) Reference integrity funnel", loc="left", fontsize=9)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.02, str(v), ha="center", fontsize=8)
ax.set_ylim(0, max(vals) * 1.18)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

fig.tight_layout()
os.makedirs("paper_rsvlm_survey/figures", exist_ok=True)
fig.savefig("paper_rsvlm_survey/figures/fig_corpus.pdf", bbox_inches="tight")
fig.savefig("paper_rsvlm_survey/figures/fig_corpus.png", dpi=200, bbox_inches="tight")
print("wrote paper_rsvlm_survey/figures/fig_corpus.pdf/.png")
print("bucket counts:", dict(zip(labels, counts)))
print("funnel:", dict(zip([s.replace(chr(10), ' ') for s in stages], vals)))
