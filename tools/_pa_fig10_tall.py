# -*- coding: utf-8 -*-
r"""`fig10_layered_ft`（Figure 14）：**改为上下两行共享 epoch 轴**（2026-10-06，操作者指出图例仍挡数据）。

## 问题

2 面板**并排** → 每格仅 **1.86 in 宽**，而左面板有 **6 个系列**，
图例只能落在绘图区内 → **压在 `Text + Vis-L4` 与 `Both (all Vis)` 的曲线上**。

（与已修的 Figure 15 同一故障，解法相同。）

## 改法

- **上下两行共享 x 轴**：每行占满 3.71 in 宽；
- **图例置于两行之上的公共区域**（`bbox_to_anchor`），**完全不占绘图区**；
- 配色 Okabe-Ito + **线型冗余编码**（6 个系列在灰度下也要能分）。

## 图注声称（须在图上看得出来）

> "Text+Vis-L1 achieves frozen-level CG with competitive R@1 using only one visual layer."

→ 图上须能看出 **`Text + Vis-L1` 的 CG 与 `Frozen` 几乎重合**、且 R@1 不低于 Frozen。

    python tools\_pa_fig10_tall.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from figure_style import apply_style, figsize_tall, save, OKABE_ITO  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
apply_style()
import matplotlib.pyplot as plt  # noqa: E402

SRC = ROOT / "outputs" / "layered_ft_results.json"
OUT = ROOT / "paper合" / "figures" / "fig10_layered_ft.png"


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演，加 --apply）")
        return 0
    d = json.loads(SRC.read_text(encoding="utf-8"))

    def fin(rows):
        r = max(rows, key=lambda t: t[0])
        return float(r[1]), float(r[2])

    fz = fin(d["Frozen"])
    l1 = fin(d["Text + Vis-L1"])
    print("  Frozen      CG=%.4f R@1=%.4f" % fz)
    print("  Text+Vis-L1 CG=%.4f R@1=%.4f" % l1)
    # 图注声称：Text+Vis-L1 达 frozen 级 CG 且 R@1 有竞争力
    assert abs(l1[0] - fz[0]) < 0.02, f"Text+Vis-L1 的 CG 未达 frozen 级（|Δ|={abs(l1[0]-fz[0]):.4f}）"
    assert l1[1] >= fz[1] - 0.02, f"Text+Vis-L1 的 R@1 不具竞争力（{l1[1]:.3f} < {fz[1]:.3f}）"
    print("  ✅ 图注声称成立（CG 达 frozen 级、R@1 有竞争力）")

    # 6 个系列：颜色 + 线型冗余编码
    style = {
        "Frozen":         (OKABE_ITO["grey"],   ":",  "s"),
        "Text + Vis-L1":  (OKABE_ITO["blue"],   "-",  "o"),
        "Text + Vis-L2":  (OKABE_ITO["sky"],    "--", "v"),
        "Text + Vis-L4":  (OKABE_ITO["green"],  "-.", "^"),
        "Text-only":      (OKABE_ITO["purple"], "--", "D"),
        "Both (all Vis)": (OKABE_ITO["vermil"], "-",  "P"),
    }
    order = ["Frozen", "Text + Vis-L1", "Text + Vis-L2", "Text + Vis-L4",
             "Text-only", "Both (all Vis)"]

    fig, axes = plt.subplots(2, 1, figsize=figsize_tall(1.15), sharex=True)
    for k in order:
        if k not in d:
            continue
        c, ls, mk = style[k]
        rows = sorted(d[k], key=lambda r: r[0])
        ep = [r[0] for r in rows]
        axes[0].plot(ep, [r[1] for r in rows], ls, color=c, marker=mk,
                     markersize=3.2, linewidth=1.4, label=k)
        axes[1].plot(ep, [r[2] for r in rows], ls, color=c, marker=mk,
                     markersize=3.2, linewidth=1.4, label=k)

    axes[0].set_ylabel("Centroid gap")
    axes[1].set_ylabel("R@1")
    axes[1].set_xlabel("Epoch")
    for ax in axes:
        ax.grid(alpha=0.22, linewidth=0.5)
        ax.set_axisbelow(True)
    # 图例置于两行**之上**的公共区域——完全不占绘图区。
    # 注意：不要调 `fig.subplots_adjust`——全局开了 constrained_layout，
    # 二者不兼容（会告警且被忽略）。constrained_layout 已为轴外图例留出空间。
    axes[0].legend(frameon=False, ncol=3, loc="lower center",
                   bbox_to_anchor=(0.5, 1.02), fontsize=7.5, handlelength=1.7,
                   columnspacing=1.0)
    save(fig, OUT)
    plt.close(fig)
    print(f"  ✅ 已重绘 {OUT.relative_to(ROOT)}（竖排两行，图例在轴外上方）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
