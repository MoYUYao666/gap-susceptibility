# -*- coding: utf-8 -*-
r"""生成"两个决策"的决策空间示意图（PRL 稿件 Figure 1）。

横轴 = 决策一：适配容量放在哪里（视觉编码器 → 投影器 → 语言主干 → 全链）
纵轴 = 决策二：固定预算如何分配（均匀 → 估计重要性 → 用结构量 → 搜索）

图中标注的是**代表方法的大致落点**（定性示意，不是坐标精确数据），目的是让读者一眼看到
"同一目标下可有不同分配、同一分配可跨目标"——即两个决策正交。

    python tools/_make_prl_figure.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "paper_review_prl" / "figures" / "fig1_decision_space.pdf"

# (x, y, label, marker, dx, dy, ha, va)  x:0=编码器 1=投影器 2=主干 3=全链；y:0=均匀 1=重要性 2=结构量 3=搜索
# 标注位置逐点显式给定，避免自动摆放造成重叠（首版有三处重叠）
PTS = [
    (0.00, 0.0, "VPT / SSF\n(uniform)", "o", 6, -16, "center", "top"),
    (0.00, 1.0, "SAFE\n(sensitivity)", "s", 0, 10, "center", "bottom"),
    (0.80, 1.0, "Convolutional bypass", "s", 0, 10, "center", "bottom"),
    (1.45, 1.0, "CLIP-Adapter", "s", 0, 10, "center", "bottom"),
    (1.00, 0.0, "Honeybee / TokenPacker\n(projector redesign)", "o", 0, -16, "center", "top"),
    (2.00, 0.0, "LoRA / DoRA\n(uniform rank)", "o", -10, -16, "center", "top"),
    (2.00, 1.0, "AdaLoRA / ARD-LoRA\n(adaptive rank)", "s", 12, 9, "left", "bottom"),
    (2.00, 2.0, "LoRA-GA / HALoRA\n(structure-driven)", "D", -12, 10, "right", "bottom"),
    (2.00, 3.0, "AutoPEFT / PEFT-Bench\n(search / benchmark)", "^", 12, 9, "left", "bottom"),
    (2.62, 0.0, "QLoRA\n(rank + precision)", "o", 0, -16, "center", "top"),
    (3.05, 1.6, "MoRA / UniPELT\n(mixed targets)", "s", -12, 10, "right", "bottom"),
]


def main() -> int:
    fig, ax = plt.subplots(figsize=(7.2, 3.8))

    ax.set_xlim(-0.55, 3.85)
    ax.set_ylim(-0.75, 3.75)
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xticklabels(["visual\nencoder", "projector", "language\nbackbone", "full\nstack"], fontsize=8)
    ax.set_yticks([0, 1, 2, 3])
    ax.set_yticklabels(["uniform", "estimated\nimportance", "structural\nquantity", "search"],
                       fontsize=8)
    ax.set_xlabel("Decision 1: where adaptive capacity is placed", fontsize=9)
    ax.set_ylabel("Decision 2: how the budget is divided", fontsize=9)
    ax.grid(True, linestyle=":", linewidth=0.6, alpha=0.45)
    ax.set_axisbelow(True)

    for x, y, lab, mk, dx, dy, ha, va in PTS:
        ax.scatter([x], [y], marker=mk, s=44, zorder=3,
                   facecolor="white", edgecolor="black", linewidth=1.0)
        ax.annotate(lab, (x, y), textcoords="offset points", xytext=(dx, dy),
                    ha=ha, va=va, fontsize=6.3, linespacing=1.15, zorder=4)

    # 说明：同一站点对应四种分配 → 两个决策正交（置于左侧，避开顶部标签）
    ax.axvspan(1.88, 2.12, color="grey", alpha=0.10, zorder=0)
    ax.annotate("one site,\nfour divisions", (1.78, 3.42), ha="right", va="top",
                fontsize=6.2, style="italic", color="0.30", linespacing=1.2, zorder=5)
    ax.annotate("", xy=(1.90, 3.30), xytext=(1.72, 3.30),
                arrowprops=dict(arrowstyle="->", lw=0.6, color="0.45"), zorder=5)

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"写出 {OUT.relative_to(REPO)}（{OUT.stat().st_size} B）")
    print(f"  标点数: {len(PTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
