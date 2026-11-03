# -*- coding: utf-8 -*-
r"""Paper A 整改 · 重建 fig8（严格冻结证据）——替换带过时注释框的旧图。

## 为什么必须重建

旧 `fig8_weight_svd.png`（2026-08-02）有两个问题，**审稿人肉眼可见**：
1. 图内**注释框**写着 "**text-only has zero vision-side ΔW → fragile visual space fully protected**"，
   而正文已把这类因果措辞删掉（改为严格冻结口径）；
2. 注释框还称 "Image SVD: Full FT shows strongest singular value collapse"，
   但同图 panel B 的图例显示 **Frozen eff=200、text-only eff=200、Full FT eff=185** ——
   **Full FT 才是最"塌"的那个**，文字与图自相矛盾。

## 新图的数据来源（全部已归档，可复核）

`outputs/analysis/strict_control_summary.json`（严格冻结实验，5 seeds/配置，视觉侧 `vision_nonzero_tensors=0`）

| 配置 | 可训参数 | 视觉侧非零张量 | 有效秩变化（视觉侧，逐层均值） |
|---|---|---|---|
| frozen | —（参照） | 0 / 199 | — |
| text_only | 196,608 | **0** | **0.0000** |
| both | 491,520 | 0 | −0.0421 |
| vision_only | 294,912 | 0 | −0.0588 |

对照旧（未严格冻结）协议：text-only 可训 **145,170,177**（≈96% 模型）→ 该协议下测得的"视觉侧变化"
是冻结失效的假象，不作为证据。

    python tools\_pa_fig8_rebuild.py
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
SRC = ROOT / "outputs" / "analysis" / "strict_control_summary.json"
OUT = ROOT / "paper合" / "figures" / "fig8_weight_svd.png"


def main() -> int:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    cfgs = d["configs"]
    names = ["text_only", "both", "vision_only"]
    label = {"text_only": "text-only", "both": "both", "vision_only": "vision-only"}
    ntr = [cfgs[k]["n_trainable_params"] for k in names]
    dvis = [cfgs[k]["vision_rank_delta_mean"] for k in names]
    dtext = [cfgs[k]["text_rank_delta_mean"] for k in names]
    legacy = d["legacy"]["legacy text-only (single)"]["n_trainable_params"]

    fig, axes = plt.subplots(1, 3, figsize=figsize_wide(0.34))

    # A: vision-side effective-rank change (the key corrected result)
    ax = axes[0]
    x = np.arange(len(names))
    ax.bar(x - 0.2, dvis, 0.4, label="vision side", color="#1f77b4", alpha=0.9)
    ax.bar(x + 0.2, dtext, 0.4, label="text side", color="#d62728", alpha=0.9)
    ax.axhline(0, color="0.3", lw=0.9)
    ax.set_xticks(x); ax.set_xticklabels([label[k] for k in names], fontsize=9)
    ax.set_ylabel("effective-rank change (mean over layers)")
    ax.set_title("A: under strict freezing", fontweight="bold", fontsize=10)
    ax.legend(fontsize=7)
    for xi, v in zip(x, dvis):
        ax.annotate(("%+.3f" % v), (xi - 0.2, v), textcoords="offset points",
                    xytext=(0, -12 if v < 0 else 4), ha="center", fontsize=7)

    # B: trainable budget — legacy vs strict
    ax = axes[1]
    ax.bar([0, 1, 2], ntr, color="#1f77b4", alpha=0.9, width=0.55)
    ax.bar([3], [legacy], color="#7f7f7f", alpha=0.9, width=0.55)
    ax.set_yscale("log")
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xticklabels(["text-only", "both", "vision-only", "text-only\n(legacy)"], fontsize=8)
    ax.set_ylabel("trainable parameters (log scale)")
    ax.set_title("B: what the optimizer could touch", fontweight="bold", fontsize=10)
    ax.annotate("strict freezing", (1, max(ntr) * 1.6), ha="center", fontsize=8, color="#1f77b4")
    ax.annotate("un-frozen\n(not used as evidence)", (3, legacy * 1.6), ha="center", fontsize=7, color="0.35")

    # C: vision-side non-zero tensor count
    ax = axes[2]
    nz = [cfgs[k]["vision_nonzero_tensors"][0] for k in names]
    ax.bar(x, nz, 0.5, color="#2ca02c", alpha=0.9)
    ax.axhline(d["frozen"]["tensors"], color="0.4", ls="--", lw=1.2,
               label="total vision tensors (%d)" % d["frozen"]["tensors"])
    ax.set_xticks(x); ax.set_xticklabels([label[k] for k in names], fontsize=9)
    ax.set_ylabel("vision tensors receiving any update")
    ax.set_ylim(0, d["frozen"]["tensors"] * 1.15)
    ax.set_title("C: vision side untouched", fontweight="bold", fontsize=10)
    ax.legend(fontsize=7, loc="upper left")

    fig.suptitle("Strict-freezing control: weight-level evidence for the Visual Fragility interpretation",
                 fontweight="bold", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    save(fig, OUT)
    plt.close(fig)
    print(f"写出 {OUT.relative_to(ROOT)}")
    for k in names:
        print("  %-12s trainable=%-10d vision_nonzero=%d  dRank_vis=%+.4f  dRank_txt=%+.4f"
              % (k, cfgs[k]["n_trainable_params"], cfgs[k]["vision_nonzero_tensors"][0],
                 cfgs[k]["vision_rank_delta_mean"], cfgs[k]["text_rank_delta_mean"]))
    print("  legacy text-only trainable=%d（旧协议，不作证据）" % legacy)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
