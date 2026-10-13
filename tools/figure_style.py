# -*- coding: utf-8 -*-
r"""图的**统一字体（Times New Roman）与尺寸**（2026-10-06）。

## 为什么需要

操作者："**图片啥的文字也要 times new roman，然后大小你要调整好**"。

**两个问题**（实测）：

### ① 字体不是 Times
各图用 matplotlib 默认 **DejaVu Sans**（无衬线），与正文（Elsevier `elsarticle` 用 Times）**不匹配**。

### ② 尺寸不统一（**根因**）
各图在**任意画布尺寸**下绘制，再由 LaTeX 缩放到目标宽度 → 文字被整体缩小，且**倍率各不相同**：

| 图 | 画布宽 | 最终宽 | 缩放 |
|---|---|---|---|
| `fig8_weight_svd` | 13.40 in | 3.71 in | **×0.28** |
| `fig10` / `fig14` | 7.6–7.8 in | 3.71 in | ×0.48 |
| `fig1` / `fig4` | 5.60 in | 4.19 in | ×0.75 |
| `fig3` | 4.60 in | 4.19 in | ×0.91 |

**→ 同一张稿子里图的字号相差 3 倍。**

## 修法（按 `scipilot-figure-skill` 原则 1 与 4）

- **按最终尺寸出图**：`figsize` 直接设 LaTeX 里的实际宽度（原则 1：导出后不再缩放）；
- **Times New Roman**：`font.family=serif` + Times 系列；数学用 `mathtext.fontset='stix'`（与 Times 同源）；
- **字号在最终尺寸下可读**（原则 4）：刻度/轴标签 **9 pt**、图例 **8 pt**，均 ≥6 pt；
- **同时导出 PDF（矢量）**（原则 2）。

## 版心（实测）

`\textwidth = 342.7 pt = 4.760 in`（像素法，见 `tools/_measure_textblock.py`）。

| LaTeX 宽度 | 最终图宽 |
|---|---|
| `0.88\textwidth` | **4.189 in** |
| `0.78\textwidth` | **3.713 in** |

    python tools\figure_style.py            # 自测：打印配置
"""
from __future__ import annotations

# ── Okabe-Ito 色盲友好调色板（2026-10-06 统一；见 scipilot-figure-skill 原则 3）
OKABE_ITO = {
    "blue":   "#0072B2",   # 主色：text-only / LoRA / 实测
    "vermil": "#D55E00",   # 强调：both / Adapter / 预测对照
    "green":  "#009E73",   # 第三：vision-only
    "grey":   "#666666",   # 中性：Frozen / 基准
    "purple": "#CC79A7",   # 第四
    "sky":    "#56B4E9",   # 浅蓝
    "yellow": "#E69F00",   # 橙黄
}
# 语义映射：保证同一概念在不同图里同色
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

# ── 版心与最终尺寸（实测）
TEXTWIDTH_PT = 342.7
TEXTWIDTH_IN = TEXTWIDTH_PT / 72.0            # 4.760 in
FIG_W_FULL = 0.88 * TEXTWIDTH_IN              # 4.189 in（0.88\textwidth）
FIG_W_WIDE = 0.78 * TEXTWIDTH_IN              # 3.713 in（0.78\textwidth）

# ── 字号（**在最终尺寸下的 pt**；≥6 pt 方可读）
FS_TICK = 9.0
FS_LABEL = 9.0
FS_LEGEND = 8.0
FS_TITLE = 9.0
FS_ANNOT = 7.5

# ── 线宽/标记（最终尺寸下的绝对量）
LW = 1.4
MS = 4.0


def apply_style() -> None:
    """应用 Times New Roman + STIX 数学 + 统一字号。**在 import matplotlib 后调用。**"""
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
        # 不扩张画布：tight bbox 会按内容外扩，导致实际尺寸 ≠ figsize，
        # LaTeX 再缩放时字号就与其它图不一致（2026-10-06 实测 fig8 偏大 1.46×）。
        "savefig.bbox": None,
        "savefig.pad_inches": 0.01,
        # constrained layout 自动理版，避免标签被裁
        "figure.constrained_layout.use": True,
        "figure.constrained_layout.h_pad": 0.02,
        "figure.constrained_layout.w_pad": 0.02,
        "figure.dpi": 300,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    })


def figsize_full(h_ratio: float = 0.72) -> tuple[float, float]:
    """0.88\\textwidth 的图：返回 (宽, 高) in；h_ratio = 高/宽。"""
    return FIG_W_FULL, FIG_W_FULL * h_ratio


def figsize_wide(h_ratio: float = 0.72) -> tuple[float, float]:
    """0.78\\textwidth 的图。"""
    return FIG_W_WIDE, FIG_W_WIDE * h_ratio


def figsize_tall(h_ratio: float = 1.15) -> tuple[float, float]:
    """**竖排两行**的图（0.78\\textwidth 宽，每行约 2.1 in 高）。

    两个面板共享 x 轴时用竖排：并排每格仅 1.86 in 宽，图例容易压数据；
    竖排每行占满栏宽（3.71 in），图例可移到绘图区之外。
    """
    return FIG_W_WIDE, FIG_W_WIDE * h_ratio


def save(fig, path, also_pdf: bool = True) -> None:
    """按最终尺寸存 PNG（LaTeX 现用）+ PDF（矢量，原则 2）。"""
    from pathlib import Path as _P
    p = _P(path)
    fig.savefig(p, dpi=300)
    if also_pdf:
        fig.savefig(p.with_suffix(".pdf"))


if __name__ == "__main__":
    print("=== 版心与最终尺寸（实测）===")
    print(f"  textwidth = {TEXTWIDTH_PT} pt = {TEXTWIDTH_IN:.3f} in")
    print(f"  0.88 textwidth -> {FIG_W_FULL:.3f} in")
    print(f"  0.78 textwidth -> {FIG_W_WIDE:.3f} in")
    print("\n=== 字号（最终尺寸下的 pt）===")
    for k, v in (("刻度", FS_TICK), ("轴标签", FS_LABEL), ("图例", FS_LEGEND),
                 ("标题", FS_TITLE), ("标注", FS_ANNOT)):
        print(f"  {k:<8} {v} pt  {'OK >=6pt' if v >= 6 else 'FAIL <6pt'}")
    print("\n=== 字体栈 ===")
    print("  serif: Times New Roman -> Nimbus Roman -> Liberation Serif -> DejaVu Serif")
    print("  mathtext: stix (Times-compatible)")
