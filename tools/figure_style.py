# -*- coding: utf-8 -*-
r"""**Unified font (Times New Roman) and size** for figures (2026-10-06).

## Why this is needed

Operator: "**the text in the figures should also be times new roman, and you must adjust the size properly**".

**Two problems** (measured):

### ① The font is not Times
Each figure uses matplotlib's default **DejaVu Sans** (sans-serif), which does **not match** the body text (Elsevier `elsarticle` uses Times).

### ② The sizes are inconsistent (**root cause**)
Each figure is drawn at an **arbitrary canvas size** and then scaled by LaTeX to the target width → the text is scaled down as a whole, and **each scale factor differs**:

| Figure | Canvas width | Final width | Scale |
|---|---|---|---|
| `fig8_weight_svd` | 13.40 in | 3.71 in | **×0.28** |
| `fig10` / `fig14` | 7.6–7.8 in | 3.71 in | ×0.48 |
| `fig1` / `fig4` | 5.60 in | 4.19 in | ×0.75 |
| `fig3` | 4.60 in | 4.19 in | ×0.91 |

**→ Font sizes differ by 3x among figures in the same manuscript.**

## The fix (per `scipilot-figure-skill` principles 1 and 4)

- **Draw at the final size**: set `figsize` directly to the actual LaTeX width (principle 1: no rescaling after export);
- **Times New Roman**: `font.family=serif` + the Times family; math uses `mathtext.fontset='stix'` (same origin as Times);
- **Font sizes readable at the final size** (principle 4): ticks/axis labels **9 pt**, legend **8 pt**, both ≥6 pt;
- **Also export PDF (vector)** (principle 2).

## Text block (measured)

`\textwidth = 342.7 pt = 4.760 in` (pixel method, see `tools/_measure_textblock.py`).

| LaTeX width | Final figure width |
|---|---|
| `0.88\textwidth` | **4.189 in** |
| `0.78\textwidth` | **3.713 in** |

    python tools\figure_style.py            # self-test: print the configuration
"""
from __future__ import annotations

# ── Okabe-Ito colorblind-friendly palette (unified 2026-10-06; see scipilot-figure-skill principle 3)
OKABE_ITO = {
    "blue":   "#0072B2",   # primary: text-only / LoRA / measured
    "vermil": "#D55E00",   # emphasis: both / Adapter / predicted control
    "green":  "#009E73",   # third: vision-only
    "grey":   "#666666",   # neutral: Frozen / baseline
    "purple": "#CC79A7",   # fourth
    "sky":    "#56B4E9",   # light blue
    "yellow": "#E69F00",   # orange-yellow
}
# Semantic mapping: the same concept keeps the same color across figures
SEMANTIC = {
    "text_only":   OKABE_ITO["blue"],
    "both":        OKABE_ITO["vermil"],
    "vision_only": OKABE_ITO["green"],
    "frozen":      OKABE_ITO["grey"],
    "measured":    OKABE_ITO["blue"],
    "predicted":   OKABE_ITO["vermil"],
    "lora":        OKABE_ITO["blue"],
    "adapter":     OKABE_ITO["vermil"],
}

# ── Text block and final sizes (measured)
TEXTWIDTH_PT = 342.7
TEXTWIDTH_IN = TEXTWIDTH_PT / 72.0            # 4.760 in
FIG_W_FULL = 0.88 * TEXTWIDTH_IN              # 4.189 in (0.88\textwidth)
FIG_W_WIDE = 0.78 * TEXTWIDTH_IN              # 3.713 in (0.78\textwidth)

# ── Font sizes (**pt at the final size**; ≥6 pt is readable)
FS_TICK = 9.0
FS_LABEL = 9.0
FS_LEGEND = 8.0
FS_TITLE = 9.0
FS_ANNOT = 7.5

# ── Line widths/markers (absolute quantities at the final size)
LW = 1.4
MS = 4.0


def apply_style() -> None:
    """Apply Times New Roman + STIX math + unified font sizes. **Call after importing matplotlib.**"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Nimbus Roman", "Liberation Serif",
                       "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "axes.unicode_minus": False,
        "font.size": FS_LABEL,
        "axes.labelsize": FS_LABEL,
        "axes.titlesize": FS_TITLE,
        "xtick.labelsize": FS_TICK,
        "ytick.labelsize": FS_TICK,
        "legend.fontsize": FS_LEGEND,
        "axes.linewidth": 0.8,
        "lines.linewidth": LW,
        "lines.markersize": MS,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "grid.linewidth": 0.5,
        "grid.alpha": 0.25,
        # No canvas expansion: tight bbox expands to the content, making the actual size ≠ figsize,
        # so when LaTeX rescales, font sizes become inconsistent with the other figures (measured 2026-10-06: fig8 1.46x too big).
        "savefig.bbox": None,
        "savefig.pad_inches": 0.01,
        # constrained layout arranges the figure automatically, avoiding clipped labels
        "figure.constrained_layout.use": True,
        "figure.constrained_layout.h_pad": 0.02,
        "figure.constrained_layout.w_pad": 0.02,
        "figure.dpi": 300,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    })


def figsize_full(h_ratio: float = 0.72) -> tuple[float, float]:
    """Figure at 0.88\\textwidth: returns (width, height) in in; h_ratio = height/width."""
    return FIG_W_FULL, FIG_W_FULL * h_ratio


def figsize_wide(h_ratio: float = 0.72) -> tuple[float, float]:
    """Figure at 0.78\\textwidth."""
    return FIG_W_WIDE, FIG_W_WIDE * h_ratio


def figsize_tall(h_ratio: float = 1.15) -> tuple[float, float]:
    """**Two stacked rows** figure (0.78\\textwidth wide, each row about 2.1 in tall).

    Use stacking when two panels share the x axis: side by side each panel is only 1.86 in wide
    and the legend easily covers the data; stacked, each row fills the column (3.71 in) and the legend can move outside the axes.
    """
    return FIG_W_WIDE, FIG_W_WIDE * h_ratio


def save(fig, path, also_pdf: bool = True) -> None:
    """Save at the final size as PNG (currently used by LaTeX) + PDF (vector, principle 2)."""
    from pathlib import Path as _P
    p = _P(path)
    fig.savefig(p, dpi=300)
    if also_pdf:
        fig.savefig(p.with_suffix(".pdf"))


if __name__ == "__main__":
    print("=== Text block and final sizes (measured) ===")
    print(f"  textwidth = {TEXTWIDTH_PT} pt = {TEXTWIDTH_IN:.3f} in")
    print(f"  0.88 textwidth -> {FIG_W_FULL:.3f} in")
    print(f"  0.78 textwidth -> {FIG_W_WIDE:.3f} in")
    print("\n=== Font sizes (pt at the final size) ===")
    for k, v in (("tick", FS_TICK), ("axis label", FS_LABEL), ("legend", FS_LEGEND),
                 ("title", FS_TITLE), ("annotation", FS_ANNOT)):
        print(f"  {k:<8} {v} pt  {'OK >=6pt' if v >= 6 else 'FAIL <6pt'}")
    print("\n=== Font stack ===")
    print("  serif: Times New Roman -> Nimbus Roman -> Liberation Serif -> DejaVu Serif")
    print("  mathtext: stix (Times-compatible)")
