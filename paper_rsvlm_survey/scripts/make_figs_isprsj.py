# -*- coding: utf-8 -*-
r"""Two synthesis figures for the ISPRS J version of the RS-VLM survey.

fig_provenance.pdf  - the four text provenances, what each can teach and what each can measure, with the pair budget
                      each source can supply for the RSICD-scale corpora used in the companion experiment.
fig_audit.pdf       - the disclosure audit matrix: eight representative papers x four reporting items, hand-verified.

Fonts: Times New Roman + STIX, pdf.fonttype 42 (repository figure rule).
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
    "font.size": 9,
})
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def provenance_figure(out):
    rows = [
        ("Metadata strings", "class labels, sensor,\nimage statistics", "which class and what\nthe image looks like", "one text per image\n(10,921)"),
        ("Annotation-derived", "detected objects with\ncounts and positions", "what is present\nand where", "one text per image\n(10,921)"),
        ("Fixed templates", "objects rendered through\nthe same sentence frame", "template reuse, not\nimage content", "one text per image\n(10,921)"),
        ("Human captions", "whole-image prose written\nfor the image", "the whole image at the\ngranularity evaluated", "3--4 texts per image\n(40,384)"),
    ]
    fig, ax = plt.subplots(figsize=(7.4, 3.4), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(rows) + 0.6)
    ax.axis("off")
    headers = ["provenance", "what the text contains", "what it can teach", "pairs available"]
    xs = [0.1, 2.3, 5.1, 7.9]
    widths = [2.0, 2.6, 2.6, 2.0]
    for x, w, h in zip(xs, widths, headers):
        ax.add_patch(Rectangle((x, len(rows)), w, 0.55, facecolor="#264653", edgecolor="none"))
        ax.text(x + 0.1, len(rows) + 0.28, h, color="white", fontsize=9, va="center")
    colors = ["#e9c46a", "#8ab17d", "#e76f51", "#2a9d8f"]
    for i, (name, contains, teaches, pairs) in enumerate(reversed(rows)):
        y = i
        ax.add_patch(Rectangle((xs[0], y), widths[0], 0.9, facecolor=colors[i], alpha=0.25, edgecolor="none"))
        ax.text(xs[0] + 0.08, y + 0.45, name, fontsize=9, fontweight="bold", va="center")
        ax.text(xs[1] + 0.08, y + 0.45, contains, fontsize=8, va="center")
        ax.text(xs[2] + 0.08, y + 0.45, teaches, fontsize=8, va="center")
        ax.text(xs[3] + 0.08, y + 0.45, pairs, fontsize=8, va="center")
    ax.text(0.1, -0.45, "Pair counts refer to the RSICD-scale corpora (10,921 images); the companion controlled study holds the budget fixed.",
            fontsize=7.5, color="#444444")
    fig.tight_layout(pad=0.2)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def audit_figure(out, audit_json):
    d = json.loads(io.open(audit_json, encoding="utf-8").read())
    papers = d["papers"]
    items = ["repeated runs", "dispersion", "compute disclosure", "cross-region evaluation"]
    short = ["repeated\nruns", "dispersion", "compute\ndisclosure", "cross-region\nevaluation"]
    fig, ax = plt.subplots(figsize=(7.4, 3.6), dpi=300)
    ax.set_xlim(0, len(items) + 1.2)
    ax.set_ylim(-0.6, len(papers) + 0.6)
    ax.axis("off")
    for j, s in enumerate(short):
        ax.text(1.05 + j * 0.95 + 0.40, len(papers) + 0.15, s, ha="center", va="center", fontsize=8)
    for i, p in enumerate(papers):
        y = len(papers) - i - 0.5
        ax.text(0.92, y, p["paper"], ha="right", va="center", fontsize=8)
        for j, it in enumerate(items):
            yes = bool(p["items"][it]["verdict"])
            ax.add_patch(Rectangle((1.05 + j * 0.95, y - 0.32), 0.80, 0.64,
                                   facecolor="#2a9d8f" if yes else "#f1f1f1",
                                   edgecolor="#bbbbbb", linewidth=0.4))
            ax.text(1.05 + j * 0.95 + 0.40, y, "yes" if yes else "no", ha="center", va="center",
                    fontsize=7.5, color="white" if yes else "#777777")
    ax.text(0.92, -0.42, "hand-verified against the archived full texts (one reading per cell)",
            ha="right", fontsize=7.5, color="#444444")
    fig.tight_layout(pad=0.2)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def main():
    dst = os.path.join(ROOT, "isprsj")
    os.makedirs(dst, exist_ok=True)
    provenance_figure(os.path.join(dst, "fig_provenance.pdf"))
    audit_figure(os.path.join(dst, "fig_audit.pdf"),
                 os.path.join(ROOT, "literature", "disclosure_audit_2026-10-28.json"))
    print("wrote fig_provenance.pdf and fig_audit.pdf to", dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
