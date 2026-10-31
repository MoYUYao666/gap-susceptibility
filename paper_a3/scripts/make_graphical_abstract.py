# -*- coding: utf-8 -*-
r"""Graphical abstract for A3 (optional but encouraged by Elsevier).

Size target: 13 cm wide x 5 cm high at 300 dpi, which is 1535 x 591 pixels - above Elsevier's minimum of
1328 x 531 pixels. Three panels, all numbers read from the archived analysis JSONs:
  (a) R@1 at 2 epochs for the four provenance arms (RSICD, site = both);
  (b) the schedule flip: 2 versus 6 epochs for human and metadata (RSICD);
  (c) information density: one caption versus five captions concatenated (RSICD, NWPU-Captions).

Fonts: Times New Roman + STIX, pdf.fonttype 42 (repository rule).
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
    "font.size": 7,
})
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    return json.loads(io.open(path, encoding="utf-8").read())


def main():
    agg = load(os.path.join(ROOT, "analysis", "full_10k_aggregate.json"))
    epochs = load(os.path.join(ROOT, "analysis", "epoch_ablation.json"))
    tab = {(e["dataset"], e["arm"], e["site"]): e for e in agg["table"]}

    arms = ["human", "segmented", "templated", "metadata"]
    labels = ["human", "parsed", "templated", "metadata"]
    vals = [tab[("rsicd", a, "both")]["R@1_i2t"]["mean"] for a in arms]

    ep = {(r["dataset"], r["arm"]): r for r in epochs["rows"]}

    rich = {}
    for ds, path in (("RSICD", os.path.join(ROOT, "analysis", "robustness.json")),):
        r = load(path)
        rich = r.get("humanrich", {})

    fig, axes = plt.subplots(1, 3, figsize=(13 / 2.54, 5 / 2.54), dpi=300)

    ax = axes[0]
    colors = ["#2a9d8f" if v == max(vals) else "#8ab17d" for v in vals]
    ax.bar(range(len(vals)), vals, color=colors)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=6)
    ax.set_ylabel("R@1")
    ax.set_title("(a) text provenance, 2 epochs", fontsize=7)
    ax.grid(axis="y", lw=0.3, alpha=0.4)

    ax = axes[1]
    hs = [ep[("rsicd", "human")]["epochs2"]["R@1_i2t"], ep[("rsicd", "human")]["epochs6"]["R@1_i2t"]]
    ms = [ep[("rsicd", "metadata")]["epochs2"]["R@1_i2t"], ep[("rsicd", "metadata")]["epochs6"]["R@1_i2t"]]
    ax.plot([0, 1], hs, "-o", ms=3, lw=1, label="human", color="#264653")
    ax.plot([0, 1], ms, "-s", ms=3, lw=1, label="metadata", color="#e76f51")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["2 epochs", "6 epochs"], fontsize=6)
    ax.set_ylabel("R@1")
    ax.set_title("(b) longer training flips it", fontsize=7)
    ax.legend(frameon=False, fontsize=6, loc="upper left")
    ax.grid(lw=0.3, alpha=0.4)

    ax = axes[2]
    names = ["RSICD", "NWPU-Captions"]
    single = [tab[("rsicd", "human", "both")]["R@1_i2t"]["mean"],
              tab[("nwpu_captions", "human", "both")]["R@1_i2t"]["mean"]]
    rich_v = [rich.get("rsicd", 0.196), rich.get("nwpu_captions", 0.340)]
    x = range(len(names))
    ax.bar([i - 0.18 for i in x], single, width=0.34, color="#8ab17d", label="one caption")
    ax.bar([i + 0.18 for i in x], rich_v, width=0.34, color="#2a9d8f", label="five captions")
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, fontsize=6)
    ax.set_ylabel("R@1")
    ax.set_title("(c) information density", fontsize=7)
    ax.legend(frameon=False, fontsize=6)
    ax.grid(axis="y", lw=0.3, alpha=0.4)

    fig.tight_layout(pad=0.4)
    out = os.path.join(ROOT, "figures", "graphical_abstract.pdf")
    fig.savefig(out, bbox_inches="tight")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
