# -*- coding: utf-8 -*-
r"""修 `fig14_adapter_layered.png` 的标题并重绘（2026-10-05）。

## 问题

图上标题为 **"Adapter: Text-only Also Preserves Alignment"** —— 与数据不符：

| 配置 | CG | R@1 |
|---|---|---|
| Frozen | 0.8143 | 0.6850 |
| Adapter Text-only | 1.0644（**+0.250**） | **0.0600** |
| Adapter Text+Vis | 1.3168（+0.503） | 0.0050 |

**两个 Adapter 配置都把 CG 抬高、把 R@1 打到接近 0** —— 谈不上"preserves alignment"。
（`fig14` 的图注也已同步修正：`tools/_pa_fix_fig14_caption.py`。）

## 改法

标题改为**中性、如实**的 "Adapter layered fine-tuning"，并保留"Text-only 升幅约为 Text+Vis 一半"
这一**数据支持**的对比。

    python tools\_pa_fix_fig14_title.py [--apply]
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
SRC = REPO / "outputs" / "adapter_layered_results.json"
OUT = REPO / "paper合" / "figures" / "fig14_adapter_layered.png"


def main() -> int:
    apply = "--apply" in sys.argv
    d = json.loads(io.open(SRC, encoding="utf-8").read())
    fin = {k: max(rows, key=lambda r: r[0]) for k, rows in d.items()}
    fz = fin["Frozen"]
    a1 = fin["Adapter Text-only"]
    a2 = fin["Adapter Text+Vis"]
    print("=== 数据核对 ===")
    for k, r in (("Frozen", fz), ("Adapter Text-only", a1), ("Adapter Text+Vis", a2)):
        print(f"  {k:<20} CG={r[1]:.4f}  R@1={r[2]:.4f}")
    gap1, gap2 = a1[1] - fz[1], a2[1] - fz[1]
    print(f"  CG 升幅：text-only {gap1:+.4f} ｜ text+vis {gap2:+.4f} ｜ 比值 {gap2/gap1:.2f}×")
    # 断言：① 两者 CG 都高于 frozen（故都不能称"preserves"/"frozen-level"）
    assert gap1 > 0.1 and gap2 > 0.1, "CG 未明显高于 frozen，标题结论需重估"
    # 断言：② text-only 的升幅确实更小
    assert gap1 < gap2, "text-only 的 CG 升幅并不更小"
    # 断言：③ 两者 R@1 都塌陷
    assert a1[2] < 0.2 and a2[2] < 0.2, "R@1 未塌陷"
    print("  → ✅ 三者断言成立：两者 CG 均升（text-only 升幅更小），R@1 均塌陷")

    if not apply:
        print("\n  （预演，加 --apply 重绘）")
        return 0

    import matplotlib
    matplotlib.use("Agg")
    apply_style()                      # Times New Roman + STIX + 统一字号
    import matplotlib.pyplot as plt

    order = ["Frozen", "Adapter Text-only", "Adapter Text+Vis"]
    colors = {"Frozen": OKABE_ITO["grey"], "Adapter Text-only": OKABE_ITO["blue"], "Adapter Text+Vis": OKABE_ITO["vermil"]}
    fig, axes = plt.subplots(1, 2, figsize=figsize_wide(0.46))
    for k in order:
        rows = sorted(d[k], key=lambda r: r[0])
        ep = [r[0] for r in rows]
        mk = "s" if k == "Frozen" else "o"
        axes[0].plot(ep, [r[1] for r in rows], mk + "-", color=colors[k], label=k,
                     linewidth=1.6, markersize=5)
        axes[1].plot(ep, [r[2] for r in rows], mk + "-", color=colors[k], label=k,
                     linewidth=1.6, markersize=5)
    axes[0].set_title("Centroid gap", fontsize=9)
    axes[1].set_title("R@1", fontsize=9)
    for ax in axes:
        ax.set_xlabel("Epoch")
        ax.grid(alpha=0.25, linewidth=0.5)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("CG"); axes[1].set_ylabel("R@1")
    # 图例移出绘图区，避免压数据（操作者指出"图例挡住图片"）
    axes[0].legend(fontsize=7, frameon=False, loc="upper left", bbox_to_anchor=(0.02, 0.98))
    # 中性、如实的总标题（原为"Text-only Also Preserves Alignment"，与数据不符）
    fig.suptitle("Adapter layered fine-tuning: both configurations raise the gap",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save(fig, OUT)
    plt.close(fig)
    print(f"\n  ✅ 已重绘 {OUT.relative_to(REPO)}（标题已改为中性）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
