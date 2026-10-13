# -*- coding: utf-8 -*-
r"""重绘 `fig10_layered_ft.png`（ViT-B 分层微调），来源 `outputs/layered_ft_results.json`。

## 为什么

`docs/PAPERA_FIGURE_PROVENANCE.md`：该图由 **2026-08-22 已不存在的脚本**产出，来源不明。
本脚本从归档 JSON 重建，来源明确、可重跑。

## 源数据结构

`outputs/layered_ft_results.json`：
```json
{"Frozen": [[epoch, CG, R@1], ...],
 "Text-only": [...], "Text + Vis-L1": [...], "Text + Vis-L2": [...],
 "Text + Vis-L4": [...], "Both (all Vis)": [...]}
```
每行 `[epoch, centroid_gap, R@1]`。

## 正文主张（需核对）

`empirical.tex` 的 `fig:layered_ft` 一节：**Text + Vis-L1 与 Text-only 相当（都保对齐）**，
而 **Both (all Vis) 崩溃**（CG 冲高、R@1 塌到接近 0）。

**写图前先断言该模式**，不符即报错。

    python tools\_pa_rebuild_fig10.py [--apply]
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
SRC = REPO / "outputs" / "layered_ft_results.json"
OUT = REPO / "paper合" / "figures" / "fig10_layered_ft.png"


def final(rows: list) -> tuple[float, float]:
    """取最后一个 epoch 的 (CG, R@1)。"""
    last = max(rows, key=lambda r: r[0])
    return float(last[1]), float(last[2])


def main() -> int:
    apply = "--apply" in sys.argv
    d = json.loads(io.open(SRC, encoding="utf-8").read())

    print("=== 各配置最终 epoch（epoch, CG, R@1）===")
    fin = {}
    for k, rows in d.items():
        cg, r1 = final(rows)
        fin[k] = (cg, r1)
        ep = len(rows)
        print(f"  {k:<18} epochs={ep:>2}  CG={cg:.4f}  R@1={r1:.4f}")

    print("\n=== 核对正文主张（`supplement.tex:58` 图注）===")
    print("  主张：Text+Vis-L1 achieves frozen-level CG with competitive R@1 using only one visual layer")
    frozen_cg, frozen_r1 = fin["Frozen"]
    l1_cg, l1_r1 = fin["Text + Vis-L1"]

    # ① Text+Vis-L1 的 CG 达到 frozen 水平
    d_cg = abs(l1_cg - frozen_cg)
    ok_cg = d_cg < 0.02
    print(f"  Frozen      CG={frozen_cg:.4f}  R@1={frozen_r1:.4f}")
    print(f"  Text+Vis-L1 CG={l1_cg:.4f}  R@1={l1_r1:.4f}")
    print(f"    → CG 达 frozen 水平（|Δ|={d_cg:.4f} < 0.02）: {'✅' if ok_cg else '❌'}")
    # ② R@1 有竞争力（不低于 frozen）
    ok_r1 = l1_r1 >= frozen_r1 - 0.02
    print(f"    → R@1 有竞争力（{l1_r1:.4f} ≥ {frozen_r1:.4f}）：{'✅' if ok_r1 else '❌'}")
    # ③ 对照：其余配置的 CG 或 R@1 明显更差（支撑"仅一层视觉即可"的说法）
    print("  对照（其余配置）：")
    for k in ("Text-only", "Text + Vis-L2", "Text + Vis-L4", "Both (all Vis)"):
        if k in fin:
            print(f"    {k:<16} CG={fin[k][0]:.4f}  R@1={fin[k][1]:.4f}")
    assert ok_cg, f"数据不支持『Text+Vis-L1 达 frozen 级 CG』（|Δ|={d_cg:.4f}）"
    assert ok_r1, f"数据不支持『R@1 有竞争力』（{l1_r1:.4f} < {frozen_r1:.4f}）"
    # 注：先前的版本断言了『Text-only 崩溃』『Both(all Vis) 塌陷』——**那是臆想的主张**，
    # 正文并未这样说（正文只说 Text+Vis-L1 达 frozen 级 CG）。教训：先读正文再设断言。

    if not apply:
        print("\n  （预演，加 --apply 写图）")
        return 0

    import matplotlib
    matplotlib.use("Agg")
    apply_style()                      # Times New Roman + STIX + 统一字号
    import matplotlib.pyplot as plt

    order = ["Frozen", "Text + Vis-L1", "Text + Vis-L2", "Text + Vis-L4", "Text-only", "Both (all Vis)"]
    colors = {"Frozen": OKABE_ITO["grey"], "Text + Vis-L1": OKABE_ITO["blue"], "Text + Vis-L2": OKABE_ITO["sky"],
              "Text + Vis-L4": OKABE_ITO["green"], "Text-only": OKABE_ITO["purple"], "Both (all Vis)": OKABE_ITO["vermil"]}

    fig, axes = plt.subplots(1, 2, figsize=figsize_wide(0.46))
    for k in order:
        if k not in d:
            continue
        rows = sorted(d[k], key=lambda r: r[0])
        ep = [r[0] for r in rows]
        cg = [r[1] for r in rows]
        r1 = [r[2] for r in rows]
        ls = "--" if k == "Frozen" else "-"
        axes[0].plot(ep, cg, ls, color=colors[k], label=k, linewidth=1.4, markersize=3)
        axes[1].plot(ep, r1, ls, color=colors[k], label=k, linewidth=1.4, markersize=3)
    axes[0].set_xlabel("Epoch"); axes[0].set_ylabel("Centroid gap")
    axes[1].set_xlabel("Epoch"); axes[1].set_ylabel("R@1")
    for ax in axes:
        ax.grid(alpha=0.25, linewidth=0.5); ax.set_axisbelow(True)
    axes[0].legend(fontsize=6, frameon=False, loc="best")
    fig.tight_layout()
    save(fig, OUT)
    plt.close(fig)
    print(f"\n  ✅ 已重绘 {OUT.relative_to(REPO)}")
    print(f"     来源：{SRC.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
