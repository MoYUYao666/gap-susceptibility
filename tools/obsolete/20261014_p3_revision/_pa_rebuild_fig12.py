# -*- coding: utf-8 -*-
r"""重绘 `fig12_zeroshot_more.png`（零样本 DTD / Food101），来源：`outputs/zeroshot_extra.json`。

## 为什么

`docs/PAPERA_FIGURE_PROVENANCE.md` 审计：该图由 **2026-08-22 已不存在的脚本**产出，**来源不明**。
本脚本从**归档 JSON** 重建，使来源明确、可重跑。

## 正文主张（需核对）

`empirical.tex` 的 `fig:zeroshot` 图注：
> "Zero-shot classification on DTD and Food101 after Flickr30k fine-tuning. **All fine-tuned variants
> stay within 0.8 percentage points** of the frozen baseline."

**本脚本在写图前先断言该主张**——若数据不支持就报错，而不是画一张与正文不符的图。

源数据：`outputs/zeroshot_extra.json`
```json
{"DTD": {"Frozen": 43.27, "Text-only": 43.33, "Both": 42.53},
 "Food101": {"Frozen": 80.6, "Text-only": 80.67, "Both": 79.73}}
```

    python tools\_pa_rebuild_fig12.py [--apply]
"""
from __future__ import annotations

import io

import sys
from pathlib import Path

# ── 共享图样式（Times New Roman + 最终尺寸；定义见 tools/figure_style.py）
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from figure_style import (apply_style, figsize_full, figsize_wide,
                          save, FIG_W_FULL, OKABE_ITO)  # noqa: E402

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "outputs" / "zeroshot_extra.json"
OUT = REPO / "paper合" / "figures" / "fig12_zeroshot_more.png"


def main() -> int:
    apply = "--apply" in sys.argv
    d = json.loads(io.open(SRC, encoding="utf-8").read())

    # ① 先核对正文主张：text-only ≤ 0.1 pp，both-position ≤ 0.9 pp
    #    注：原先正文笼统写"all fine-tuned variants within 0.8 pp"，本断言在重绘时发现
    #    Food101/both 偏差为 0.87 pp 而**超出**——故正文已改为分变体如实陈述
    #    （脚本 `tools/_pa_fix_zeroshot_claim.py`）。此处断言随之更新。
    print("=== 核对正文主张 ===")
    print("  text-only ≤ 0.1 pp ｜ both-position ≤ 0.9 pp")
    worst = {"text-only": 0.0, "both": 0.0}
    for ds, vals in d.items():
        frozen = vals["Frozen"]
        for k, v in vals.items():
            if k == "Frozen":
                continue
            diff = abs(v - frozen)
            grp = "text-only" if k == "Text-only" else "both"
            worst[grp] = max(worst[grp], diff)
            lim = 0.1 if grp == "text-only" else 0.9
            print(f"  {ds:<9} {k:<10} {v:6.2f}  vs Frozen {frozen:6.2f}  Δ={diff:+.2f} pp "
                  f"(上限 {lim}) {'✅' if diff <= lim else '❌'}")
    print(f"  最大偏差：text-only {worst['text-only']:.2f} pp ｜ both {worst['both']:.2f} pp")
    assert worst["text-only"] <= 0.1, f"text-only 偏差 {worst['text-only']:.2f} > 0.1"
    assert worst["both"] <= 0.9, f"both 偏差 {worst['both']:.2f} > 0.9"

    if not apply:
        print("\n  （预演，加 --apply 写图）")
        return 0

    import matplotlib
    matplotlib.use("Agg")
    apply_style()                      # Times New Roman + STIX + 统一字号
    import matplotlib.pyplot as plt
    import numpy as np

    datasets = list(d)
    variants = ["Frozen", "Text-only", "Both"]
    colors = {"Frozen": OKABE_ITO["grey"], "Text-only": OKABE_ITO["blue"], "Both": OKABE_ITO["vermil"]}
    x = np.arange(len(datasets))
    w = 0.26

    fig, ax = plt.subplots(figsize=figsize_full(0.68))
    for i, v in enumerate(variants):
        ys = [d[ds][v] for ds in datasets]
        bars = ax.bar(x + (i - 1) * w, ys, w, label=v, color=colors[v], edgecolor="black", linewidth=0.4)
        for b, y in zip(bars, ys):
            ax.text(b.get_x() + b.get_width() / 2, y + 0.6, f"{y:.2f}", ha="center", va="bottom", fontsize=6.5)
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.set_ylabel("Zero-shot accuracy (%)")
    ax.set_ylim(0, 100)
    # 图例置于轴下方（数据柱从 0 起，图内无空白），避免压柱
    ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper center",
              bbox_to_anchor=(0.5, -0.12))
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, OUT)
    plt.close(fig)
    print(f"\n  ✅ 已重绘 {OUT.relative_to(REPO)}")
    print(f"     来源：{SRC.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
