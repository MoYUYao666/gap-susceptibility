# -*- coding: utf-8 -*-
r"""**重做 `fig8_weight_svd.png`**——与原 `fig9` 同样的"画布太小"故障（2026-10-06）。

## 问题（目视确认）

`fig8` 是 **1×3 面板**，但画布只有 **3.710 × 1.260 in**（`h_ratio=0.34` 时 3 个面板各约 1.24 in 宽）：

| 症状 | 原因 |
|---|---|
| 文字互相重叠、被裁 | 每面板约 1.24 × 1.0 in，装不下轴标签 |
| `suptitle` 与面板标题相撞 | 长总标题 + 各面板**长标题** |
| **图例盖住柱** | `loc` 默认 + 画布太小 |
| 三个长注释溢出 | `annotate` 文字过长 |

**与 `fig9` 完全同源**（我把 `h_ratio` 从 0.62 降到 0.34 时，没相应缩小文字容量）。

## 修法（与 `fig9` 一致）

1. 画布 **`figsize_wide(0.72)`**（3.713 × 2.67 in）；
2. **删 `suptitle`**（说明交给 LaTeX 图注）；
3. 面板标题压成 **A / B / C**；
4. 图例移到**轴内空白区**；长注释改短并移位；
5. 配色统一 **Okabe-Ito**；
6. 去掉 `tight_layout`（全局已开 `constrained_layout`，混用会冲突）。

    python tools\_pa_fig8_fix.py [--apply]
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

SRC = ROOT / "outputs" / "analysis" / "strict_control_summary.json"
OUT = ROOT / "paper合" / "figures" / "fig8_weight_svd.png"


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== 重做 fig8（权重/谱证据）===")
    if not apply:
        print("  （预演，加 --apply）")
        return 0

    d = json.loads(SRC.read_text(encoding="utf-8"))
    cfgs = d["configs"]
    names = ["text_only", "both", "vision_only"]
    # 短标签：面板仅 1.24 in 宽，长标签必然重叠；含义由 LaTeX 图注说明
    label = {"text_only": "text", "both": "both", "vision_only": "vision"}
    ntr = [cfgs[k]["n_trainable_params"] for k in names]
    dvis = [cfgs[k]["vision_rank_delta_mean"] for k in names]
    dtext = [cfgs[k]["text_rank_delta_mean"] for k in names]
    legacy = d["legacy"]["legacy text-only (single)"]["n_trainable_params"]
    nz = [cfgs[k]["vision_nonzero_tensors"][0] for k in names]
    ntotal = d["frozen"]["tensors"]

    CV, CT = OKABE_ITO["blue"], OKABE_ITO["vermil"]
    fig, axes = plt.subplots(1, 3, figsize=figsize_wide(0.72))
    x = np.arange(len(names))

    # ── A：严格冻结下视觉/文本侧的有效秩变化
    ax = axes[0]
    ax.bar(x - 0.2, dvis, 0.4, color=CV, edgecolor="black", linewidth=0.4, label="Vision")
    ax.bar(x + 0.2, dtext, 0.4, color=CT, edgecolor="black", linewidth=0.4,
           hatch="//", label="Text")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([label[k] for k in names], rotation=45, ha="right")
    ax.set_ylabel(r"$\Delta$ effective rank")
    ax.set_title("A", fontweight="bold")
    ax.margins(x=0.18)
    ax.legend(frameon=False, ncol=2, loc="lower center", handlelength=1.1,
              columnspacing=0.8, borderaxespad=0.15, fontsize=7)

    # ── B：可训预算（严格 vs 旧协议）
    ax = axes[1]
    ax.bar([0, 1, 2], ntr, color=CV, edgecolor="black", linewidth=0.4, width=0.55)
    ax.bar([3], [legacy], color=OKABE_ITO["grey"], edgecolor="black",
           linewidth=0.4, width=0.55)
    ax.set_yscale("log")
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xticklabels(["text", "both", "vis", "legacy"], fontsize=7.5, rotation=45, ha="right")
    ax.set_ylabel("Trainable parameters")
    ax.set_title("B", fontweight="bold")
    # 短标注（先前是两句长文字，在 1.24 in 宽里必然溢出）
    ax.text(1, max(ntr) * 2.2, "strict", ha="center", fontsize=7, color=CV)
    ax.text(3, legacy * 1.5, "legacy", ha="center", fontsize=7,
            color=OKABE_ITO["grey"])

    # ── C：视觉侧收到更新的张量数
    ax = axes[2]
    ax.bar(x, nz, 0.5, color=OKABE_ITO["green"], edgecolor="black", linewidth=0.4)
    ax.axhline(ntotal, color=OKABE_ITO["grey"], ls="--", lw=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels([label[k] for k in names], rotation=45, ha="right")
    ax.set_ylabel("Vision tensors updated")
    ax.set_ylim(0, ntotal * 1.45)
    ax.set_title("C", fontweight="bold")
    ax.text(0.96, 0.86, f"frozen = {ntotal}", transform=ax.transAxes,
            ha="right", va="top", fontsize=7, color=OKABE_ITO["grey"])

    save(fig, OUT)
    plt.close(fig)
    print(f"  ✅ 已重绘 {OUT.relative_to(ROOT)}")
    for k in names:
        print("     %-12s trainable=%-9d vision_nonzero=%d  dRank_vis=%+.4f  dRank_txt=%+.4f"
              % (k, cfgs[k]["n_trainable_params"], cfgs[k]["vision_nonzero_tensors"][0],
                 cfgs[k]["vision_rank_delta_mean"], cfgs[k]["text_rank_delta_mean"]))
    # 断言：正文/图注声称的"文本侧适配完全不碰视觉侧"
    assert nz[0] == 0, f"text-only 的 vision_nonzero_tensors 应为 0，实为 {nz[0]}"
    print("  ✅ 断言通过（text-only 的视觉侧更新张量数 = 0，与图注一致）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
