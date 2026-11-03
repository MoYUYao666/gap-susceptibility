# -*- coding: utf-8 -*-
r"""`fig14`：Adapter 分层微调，**改为上下两行**（2026-10-06 重做，操作者指出）。

## 为什么改

原图两面板**并排**：每格仅 1.86 in 宽，**左面板图例正压在两条 CG 曲线上**。
改为**上下两行共享 x 轴**：每行占满 3.71 in 宽，图例可移到绘图区之外。

图注里的数字（frozen $0.81$、text-only $+0.25$、text+vis $+0.50$、$R@1$ $0.06$/$0.005$）
在写图前**先与归档 JSON 断言核对**。

    python tools\_pa_fig14_tall.py
"""
from __future__ import annotations

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

SRC = ROOT / "outputs" / "adapter_layered_results.json"
OUT = ROOT / "paper合" / "figures" / "fig14_adapter_layered.png"


def last(rows):
    r = max(rows, key=lambda t: t[0])
    return float(r[1]), float(r[2])


def main() -> int:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    fz, a1, a2 = last(d["Frozen"]), last(d["Adapter Text-only"]), last(d["Adapter Text+Vis"])
    g1, g2 = a1[0] - fz[0], a2[0] - fz[0]
    print("  frozen CG=%.4f R@1=%.4f" % fz)
    print("  text-only  CG=%.4f (%+.2f)  R@1=%.3f" % (a1[0], g1, a1[1]))
    print("  text+vis   CG=%.4f (%+.2f)  R@1=%.3f" % (a2[0], g2, a2[1]))

    CV, CT, CGR = OKABE_ITO["blue"], OKABE_ITO["vermil"], OKABE_ITO["grey"]
    fig, axes = plt.subplots(2, 1, figsize=figsize_tall(1.15), sharex=True)

    style = {"Frozen": (CGR, "s", ":"),
             "Adapter Text-only": (CV, "o", "-"),
             "Adapter Text+Vis": (CT, "D", "--")}
    for name, (c, mk, ls) in style.items():
        rows = sorted(d[name], key=lambda r: r[0])
        ep = [r[0] for r in rows]
        axes[0].plot(ep, [r[1] for r in rows], ls, color=c, marker=mk,
                     markersize=3.6, linewidth=1.4, label=name)
        axes[1].plot(ep, [r[2] for r in rows], ls, color=c, marker=mk,
                     markersize=3.6, linewidth=1.4, label=name)

    axes[0].set_ylabel("Centroid gap")
    axes[1].set_ylabel("R@1")
    axes[1].set_xlabel("Epoch")
    for ax in axes:
        ax.grid(alpha=0.22, linewidth=0.5)
        ax.set_axisbelow(True)
    # 图例移出绘图区（并排版曾压在数据线上）
    axes[0].legend(frameon=False, ncol=3, loc="upper center",
                   bbox_to_anchor=(0.5, 1.20), fontsize=7.5, handlelength=1.5,
                   columnspacing=0.9)
    save(fig, OUT)
    plt.close(fig)
    print("  ✅ 已重绘 fig14_adapter_layered.png（竖排两行）")
    assert abs(fz[0] - 0.81) < 0.02, f"frozen CG 应≈0.81，实为 {fz[0]:.4f}"
    assert abs(g1 - 0.25) < 0.03, f"text-only 增量应≈0.25，实为 {g1:.4f}"
    assert abs(g2 - 0.50) < 0.03, f"text+vis 增量应≈0.50，实为 {g2:.4f}"
    assert a1[1] < 0.10 and a2[1] < 0.05, "R@1 应塌到接近 0"
    print("  ✅ 断言通过（0.81 ｜ +0.25 ｜ +0.50 ｜ R@1≈0）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
