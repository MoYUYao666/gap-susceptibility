# -*- coding: utf-8 -*-
r"""**重做 `fig9_noise_sensitivity.png`**——原图完全坏掉（2026-10-06）。

## 原图的问题（实测）

`fig9` 在 **3.713 in × 1.26 in** 的画布上塞了 **1×3 面板 + 总标题 + 长图例**：

| 症状 | 原因 |
|---|---|
| 三面板互相重叠 | 画布高仅 1.26 in，装不下子图 |
| 标题互相压、被裁 | `suptitle` + 各面板**长标题**（"C: measured ratio 0.76× (paper previously claimed 2.6×)"） |
| **图例盖住整个图** | 图例文字长（`$\sigma=0$ must be exactly 0`）+ 画布太小 |
| 整图不可读 | 上述叠加 |

**根因**：我把 `h_ratio` 从 0.62 改成 0.34（为让 tight bbox 裁出目标宽度），**但没有相应放大字号容量**——
3 个面板各只有 **1.24 in 宽**，却要放标题+图例。

## 修法

1. **画布加高**：`figsize_wide(0.72)`（= 3.713 × 2.67 in），三面板各约 1.24 × 2.0 in；
2. **删除 `suptitle`**——图的说明交给 LaTeX 图注（期刊标准做法，且省下大量纵向空间）；
3. **标题极简**：`A` / `B` / `C` + 必要说明放在**图注**里，不用长标题；
4. **图例**：A 面板图例移到**轴外上方**；B 的 `σ=0` 说明并入图注、不进图例；
5. **配色**：Okabe-Ito（与全稿统一）；
6. **不加** `tight_layout`（全局已开 `constrained_layout`，二者混用会冲突）。

    python tools\_pa_fig9_fix.py [--apply]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from figure_style import apply_style, figsize_wide, save, OKABE_ITO  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
apply_style()                       # Times New Roman + STIX + 统一字号
import matplotlib.pyplot as plt     # noqa: E402
import numpy as np                  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

FIXED = ROOT / "outputs" / "noise_fixed_aug.json"
OLD = ROOT / "outputs" / "noise_sensitivity.json"
OUT = ROOT / "paper合" / "figures" / "fig9_noise_sensitivity.png"


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== 重做 fig9（参数噪声探针）===")
    if not apply:
        print("  （预演，加 --apply）")
        return 0

    d = json.loads(FIXED.read_text(encoding="utf-8"))
    rows = d["rows"]
    sigs = sorted({round(r["sigma"], 3) for r in rows})
    vis = {s: [r["drop_pct"] for r in rows if r["encoder"] == "vision" and abs(r["sigma"] - s) < 1e-9] for s in sigs}
    txt = {s: [r["drop_pct"] for r in rows if r["encoder"] == "text" and abs(r["sigma"] - s) < 1e-9] for s in sigs}
    ctrl_ok = bool(d.get("control_sigma0_reproduces_baseline"))
    v01, t01 = float(np.mean(vis[0.1])), float(np.mean(txt[0.1]))
    ratio = abs(v01 / t01) if t01 else float("nan")

    CV, CT = OKABE_ITO["blue"], OKABE_ITO["vermil"]
    fig, axes = plt.subplots(1, 3, figsize=figsize_wide(0.72))

    # ── A：修正探针，按 σ 分组
    ax = axes[0]
    x, w = np.arange(len(sigs)), 0.36
    ax.bar(x - w / 2, [np.mean(vis[s]) for s in sigs], w,
           yerr=[np.std(vis[s], ddof=1) for s in sigs], capsize=2.5,
           color=CV, edgecolor="black", linewidth=0.4, label="Vision")
    ax.bar(x + w / 2, [np.mean(txt[s]) for s in sigs], w,
           yerr=[np.std(txt[s], ddof=1) for s in sigs], capsize=2.5,
           color=CT, edgecolor="black", linewidth=0.4, hatch="//", label="Text")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(["0", "0.03", "0.1"])
    ax.set_xlabel(r"Noise $\sigma$")
    ax.set_ylabel("R@1 change (%)")
    ax.set_title("A", fontweight="bold")          # 极简标题，说明交给图注
    # 图例置于轴内右上留白（该区数值 ≤2.5，右上空）——放轴外会与 y 轴顶部刻度相挤
    ax.set_ylim(-3.5, 6.5)            # 容纳误差棒上限（4.73），并给图例留位
    ax.legend(frameon=False, ncol=1, loc="upper left", handlelength=1.2,
              borderaxespad=0.15)

    # ── B：σ=0 对照（必须精确为 0）
    ax = axes[1]
    zv, zt = vis[0.0], txt[0.0]
    ax.scatter(range(1, len(zv) + 1), zv, s=22, color=CV, marker="o",
               edgecolor="black", linewidth=0.4, zorder=3, label="Vision")
    ax.scatter(range(1, len(zt) + 1), zt, s=22, color=CT, marker="s",
               edgecolor="black", linewidth=0.4, zorder=3, label="Text")
    ax.axhline(0, color="black", ls="--", lw=1.0)
    ax.set_ylim(-1.0, 1.0)
    ax.set_xticks([1, 3, 5])          # 整数稀疏刻度，避免浮点标签拥挤
    ax.set_xlabel("Seed index")
    ax.set_ylabel("R@1 change (%)")
    ax.set_title("B", fontweight="bold")
    # 数据全在 y=0 线上，下方大片空白 → 图例置于轴内下方
    ax.legend(frameon=False, ncol=1, loc="lower right", columnspacing=0.9,
              handlelength=1.2, borderaxespad=0.15)

    # ── C：测得比值 vs 旧文声称的 2.6×
    ax = axes[2]
    ax.bar([0, 1], [abs(v01), abs(t01)], width=0.55, color=[CV, CT],
           edgecolor="black", linewidth=0.4, hatch=[None, "//"])
    ax.errorbar([0], [abs(v01)], yerr=[np.std(vis[0.1], ddof=1)], fmt="none",
                ecolor="black", elinewidth=0.9, capsize=2.5)
    ax.errorbar([1], [abs(t01)], yerr=[np.std(txt[0.1], ddof=1)], fmt="none",
                ecolor="black", elinewidth=0.9, capsize=2.5)
    ax.axhline(2.6, color=OKABE_ITO["grey"], ls=":", lw=1.2)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Vision", "Text"])
    ax.set_ylabel(r"$|$R@1 change$|$ (%)")
    ax.set_title("C", fontweight="bold")
    ax.set_ylim(0, 6.6)               # 抬高上限，给标注让位（虚线在 2.6）
    ax.text(0.97, 0.99, r"claimed $2.6\times$", transform=ax.transAxes,
            ha="right", va="top", fontsize=6.5, color=OKABE_ITO["grey"])

    save(fig, OUT)
    plt.close(fig)
    print(f"  ✅ 已重绘 {OUT.relative_to(ROOT)}")
    print(f"     baseline R@1 = {d.get('baseline_R1_fixed_subset'):.4f} ｜ σ=0 复现基线: {ctrl_ok}")
    print(f"     σ=0.1  视 {v01:+.2f}%  文 {t01:+.2f}%  比值 {ratio:.2f}×（旧文声称 2.6×）")
    # 断言：正文/图注声称的两件事
    assert ctrl_ok, "σ=0 未复现基线——图注声称的负结果依据不成立"
    assert 0.5 < ratio < 1.2, f"比值 {ratio:.2f} 与图注所写 0.76 不符，需先核对图注"
    print("  ✅ 断言通过（σ=0 复现基线 ｜ 比值与图注一致）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
