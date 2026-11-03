# -*- coding: utf-8 -*-
r"""Figure 2: scale versus year for the data resources with reported figures, coloured by text provenance.

Every plotted value comes from `paper_rsvlm_survey/provenance.md` (itself extracted from the real abstracts), so the figure
cannot drift from the text. Resources whose source did not report a size are absent by design, and the caption says so.

Typography: Times New Roman + STIX, CID TrueType (pdf.fonttype 42).
"""
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

# name, year, count, unit, provenance, reference key
ROWS = [
    ("MMFlood", 2022, 1748, "acquisitions", "task", "montellommflood2022"),
    ("MultiSenGE", 2022, 8157, "patches", "metadata", "wengermultisenge2022"),
    ("NWPU-Captions", 2022, 31500, "images", "human", "chengnwpucaptions2022"),
    ("BigEarthNet-MM", 2021, 590326, "pairs", "metadata", "sumbulbigearthnetmm2021"),
    ("MMRS-1M (EarthGPT)", 2024, 1000000, "pairs", "instruction", "zhangearthgpt2024"),
    ("RingMoGPT instr.", 2024, 1600000, "QA pairs", "instruction", "wangringmogpt2024"),
    ("RS5M", 2024, 5000000, "pairs", "generated", "zhangrsm2024"),
]
COLORS = {"human": "#2f4f76", "generated": "#4a6fa5", "metadata": "#8aa1b8", "instruction": "#b08a4f",
          "task": "#9aa7b4"}

fig, ax = plt.subplots(figsize=(6.6, 3.0))
for name, year, count, unit, prov, _ in ROWS:
    ax.scatter(year, count, s=46, color=COLORS[prov], edgecolor="white", linewidth=0.6, zorder=3)
    ax.annotate(name, (year, count), textcoords="offset points", xytext=(6, 5), fontsize=7)

ax.set_yscale("log")
ax.set_xlim(2020.4, 2025.2)
ax.set_ylim(1e3, 1e7)
ax.set_xlabel("year reported")
ax.set_ylabel("reported size (log scale)")
ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.6)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

handles = [plt.Line2D([], [], marker="o", linestyle="", color=COLORS[k], label=k)
           for k in ("human", "generated", "metadata", "instruction", "task")]
ax.legend(handles=handles, title="text provenance", fontsize=7, title_fontsize=7,
          loc="upper left", frameon=False, ncol=2)

fig.tight_layout()
os.makedirs("paper_rsvlm_survey/figures", exist_ok=True)
fig.savefig("paper_rsvlm_survey/figures/fig_scale.pdf", bbox_inches="tight")
fig.savefig("paper_rsvlm_survey/figures/fig_scale.png", dpi=200, bbox_inches="tight")
print("wrote paper_rsvlm_survey/figures/fig_scale.pdf/.png with", len(ROWS), "resources")
