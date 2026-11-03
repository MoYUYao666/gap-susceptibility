# -*- coding: utf-8 -*-
r"""Paper A 整改 · 重建 fig9（参数噪声敏感性）——从**修正后**的归档数据出图。

## 为什么必须重建

正文已按 [M1] 把噪声证据线**撤回**（图注也写明 "the corrected probe finds no stable ordering …,
so this panel is retained for transparency only"），但随稿的 `fig9_noise_sensitivity.png`
仍是 **2026-08-02 的旧图**，画的是被撤回的 2.6× 结论。**图与文字矛盾**，审稿人一看即知。

## 数据来源（已归档，可复核）

- **修正探针**：`outputs/noise_fixed_aug.json`
  设计：`num_workers=0` + 每次评估前用常量种子重放增强 + 噪声抽样仅依赖 run seed；
  `control_sigma0_reproduces_baseline = true`（σ=0 完美复现基线）。
- **旧探针**：`outputs/noise_sensitivity.json`（单配置，被撤回的那次）

## 图的设计（如实呈现"为什么撤回"）

- **A**：修正探针 σ=0.1，视/文各自的 drop% 均值 ± sd（5 seeds）→ **误差棒重叠、无稳定排序**
- **B**：σ=0 对照校验（修正探针必须复现基线）→ 证明设计可信
- **C**：旧探针 vs 修正探针在 σ=0.1 的对比 → **直观展示撤回的理由**

    python tools\_pa_fig9_noise_rebuild.py
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "tools"))
from figure_style import apply_style, figsize_wide, save
import matplotlib
matplotlib.use("Agg")
apply_style()          # Times New Roman + STIX + 统一字号
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(r"D:\Realdesktop\Wan\Important\New")
FIXED = ROOT / "outputs" / "noise_fixed_aug.json"
OUT = ROOT / "paper合" / "figures" / "fig9_noise_sensitivity.png"


def main() -> int:
    d = json.loads(FIXED.read_text(encoding="utf-8"))
    rows = d["rows"]
    sig = [0.0, 0.03, 0.1]
    vis, txt = [], []
    for s in sig:
        vis.append([r["drop_pct"] for r in rows if r["encoder"] == "vision" and abs(r["sigma"] - s) < 1e-9])
        txt.append([r["drop_pct"] for r in rows if r["encoder"] == "text" and abs(r["sigma"] - s) < 1e-9])
    base = d["baseline_R1_fixed_subset"]
    ctrl_ok = d.get("control_sigma0_reproduces_baseline")

    fig, axes = plt.subplots(1, 3, figsize=figsize_wide(0.34))

    # --- A: corrected probe by sigma ---
    ax = axes[0]
    x = np.arange(len(sig))
    w = 0.36
    ax.bar(x - w / 2, [np.mean(v) for v in vis], w, yerr=[np.std(v, ddof=1) for v in vis],
           capsize=4, label="Vision encoder", color="#1f77b4", alpha=0.85)
    ax.bar(x + w / 2, [np.mean(t) for t in txt], w, yerr=[np.std(t, ddof=1) for t in txt],
           capsize=4, label="Text encoder", color="#d62728", alpha=0.85)
    ax.axhline(0, color="0.3", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels([("%.2f" % s) for s in sig])
    ax.set_xlabel("Noise $\\sigma$"); ax.set_ylabel("R@1 drop (%)")
    ax.set_title("A: corrected probe (5 seeds)", fontweight="bold", fontsize=10)
    ax.legend(fontsize=7, loc="upper left")

    # --- B: sigma=0 control ---
    ax = axes[1]
    zero_v = vis[0]; zero_t = txt[0]
    ax.scatter(range(1, len(zero_v) + 1), zero_v, s=42, color="#1f77b4", label="Vision", zorder=3)
    ax.scatter(range(1, len(zero_t) + 1), zero_t, s=42, marker="s", color="#d62728", label="Text", zorder=3)
    ax.axhline(0, color="0.2", ls="--", lw=1.4, label="$\\sigma=0$ must be exactly 0")
    ax.set_ylim(-3, 3)
    ax.set_xlabel("seed index"); ax.set_ylabel("R@1 drop (%)")
    ax.set_title("B: $\\sigma{=}0$ control %s" % ("(reproduces baseline)" if ctrl_ok else "(FAILED)"),
                 fontweight="bold", fontsize=10)
    ax.legend(fontsize=7)

    # --- C: why the line was withdrawn ---
    ax = axes[2]
    old = json.loads((ROOT / "outputs" / "noise_sensitivity.json").read_text(encoding="utf-8"))
    # 旧探针只有 vision 的 sigma 序列可用作对照；标出旧文所称的 2.6x 与实际比值
    v1 = np.mean(vis[-1]); t1 = np.mean(txt[-1])
    ax.bar([0, 1], [abs(v1), abs(t1)], color=["#1f77b4", "#d62728"], alpha=0.85, width=0.55)
    ax.errorbar([0], [abs(v1)], yerr=[np.std(vis[-1], ddof=1)], fmt="none", ecolor="0.2", capsize=5)
    ax.errorbar([1], [abs(t1)], yerr=[np.std(txt[-1], ddof=1)], fmt="none", ecolor="0.2", capsize=5)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Vision", "Text"])
    ax.set_ylabel("|R@1 drop| (%) at $\\sigma{=}0.1$")
    ratio = abs(v1 / t1) if t1 else float("nan")
    ax.set_title("C: measured ratio %.2f$\\times$ (paper previously claimed 2.6$\\times$)"
                 % ratio, fontweight="bold", fontsize=10)
    ax.set_ylim(0, max(abs(v1), abs(t1)) * 2.4)

    fig.suptitle("Parameter-noise probe: corrected design and why the earlier claim was withdrawn",
                 fontweight="bold", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save(fig, OUT)
    plt.close(fig)
    print(f"写出 {OUT.relative_to(ROOT)}")
    print(f"  baseline R@1 = {base:.4f} ｜ σ=0 对照复现基线: {ctrl_ok}")
    print(f"  σ=0.1  视 {v1:+.2f}%  文 {t1:+.2f}%  比值 {ratio:.2f}×  （旧文声称 2.6×）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
