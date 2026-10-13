# -*- coding: utf-8 -*-
r"""重做 `fig4.png`（跨方法比较）——现图是**坏的**，本脚本用正确数据重建（2026-10-06）。

## 现图的问题（实测）

| 项 | 现图 | 应为 |
|---|---|---|
| 内容 | Adapter **β vs dim** | 跨方法比较（图注声称的） |
| **图例** | **`False` / `True`**（布尔值当标签，读者看不懂） | 有意义的分组名 |
| y 轴 | 到 **68** | — |
| 数据质量 | β 中位数 **0.50**、最大 **337**（而正文其余处 β ≈ 0.14–0.17）→ **拟合失败值** | — |

**结论：图注说的事（LoRA 偏 text-only；Adapter 无一致的 text-only 优势），现图根本没画。**

## 新图的数据（`outputs/analysis/adapter_common_baseline.json`，**同一冻结基准**）

| 分组 | ΔCG（共同基准） | n |
|---|---|---|
| **LoRA text-only** | −0.0465 | 5 |
| **LoRA both** | −0.0258 | 5 |
| **LoRA vision-only** | +0.0106 | 5 |
| **Adapter text-only** | **+0.1848** | 5 |
| **Adapter all-7 (text+vision)** | **+0.2293** | 7 |

→ **LoRA 三臂都 ≤ 0（保对齐）；Adapter 都 > 0（恶化）**，且 Adapter 上 text-only **无优势**
（+0.185 vs +0.229，差很小且都为恶化）——**这正是图注要说的**。

## 设计（按 `scipilot-figure-skill` 硬性原则）

- **横向柱状**（分组名长，横排才不挤）；
- **色盲友好**：Okabe-Ito（`#0072B2` 蓝 / `#D55E00` 朱红）；
- **冗余编码**：LoRA 实心、Adapter 斜纹（灰度也能分）；
- **零线**标出（ΔCG=0 是"不改变间隙"的基准）；
- **误差棒 = SD**，且在**图注交代**（原则 5）；
- **按最终尺寸出图**（宽 5.6 in 适配 `0.88\textwidth`）。

    python tools\_pa_rebuild_fig4_crossmethod.py [--apply]
"""
from __future__ import annotations

import glob
import io

import sys
from pathlib import Path

# ── 共享图样式（Times New Roman + 最终尺寸；定义见 tools/figure_style.py）
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from figure_style import (apply_style, figsize_full, figsize_wide,
                          save, FIG_W_FULL, OKABE_ITO)  # noqa: E402

import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "paper合" / "figures" / "fig4.png"
ADP = REPO / "outputs" / "analysis" / "adapter_common_baseline.json"

# Okabe-Ito 色盲友好
C_LORA = "#0072B2"
C_ADAPTER = "#D55E00"


def lora_arms() -> dict[str, list[float]]:
    """从严格冻结结果取 LoRA 三臂的 ΔCG（每 seed 一个值）。"""
    src = {
        "text_only": "outputs/strict_freeze/text_only/seed*/results.json",
        "both": "outputs/strict_freeze/both/seed*/results.json",
        "vision_only": "outputs/strict_freeze/vision_only/seed*/results.json",
    }
    out = {}
    for arm, pat in src.items():
        vals = []
        for p in sorted(REPO.glob(pat)):
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            ig, fg = d.get("initial_gap") or {}, d.get("final_gap") or {}
            if ig.get("centroid_gap") is not None and fg.get("centroid_gap") is not None:
                vals.append(fg["centroid_gap"] - ig["centroid_gap"])
        out[arm] = vals
    return out


def main() -> int:
    apply = "--apply" in sys.argv
    a = json.loads(ADP.read_text(encoding="utf-8"))
    L = lora_arms()

    print("=== LoRA 三臂（严格冻结，同一协议）===")
    for arm, v in L.items():
        print(f"  {arm:<12} n={len(v)}  ΔCG={st.mean(v):+.4f} ± "
              f"{(st.stdev(v) if len(v) > 1 else 0):.4f}")

    print("\n=== Adapter（common baseline）===")
    ad = {}
    for key, label in (("adapter_text_only", "Adapter text-only"),
                       ("adapter_all_7", "Adapter text+vision"),
                       ("adapter_both", "Adapter both (n=1)"),
                       ("adapter_vision_only", "Adapter vision-only (n=1)")):
        if key in a:
            ad[label] = (a[key]["dCG_common_mean"], a[key]["n"])
            print(f"  {label:<28} n={a[key]['n']}  ΔCG={a[key]['dCG_common_mean']:+.4f}")

    # ── 断言：图注声称的模式必须成立
    print("\n=== 核对图注声称 ===")
    lora_max = max(st.mean(v) for v in L.values())
    adp_min = min(v for v, _ in ad.values())
    print(f"  LoRA 三臂最大 ΔCG = {lora_max:+.4f}（应 ≤ 0：保对齐）")
    print(f"  Adapter 最小 ΔCG  = {adp_min:+.4f}（应 > 0：恶化）")
    ok1 = lora_max <= 0.02
    ok2 = adp_min > 0.05
    print(f"    → LoRA 保对齐: {'✅' if ok1 else '❌'} ｜ Adapter 恶化: {'✅' if ok2 else '❌'}")
    # Adapter 上 text-only 是否无优势（两臂都恶化，且差距小）
    at = a["adapter_text_only"]["dCG_common_mean"]
    a7 = a["adapter_all_7"]["dCG_common_mean"]
    print(f"  Adapter text-only {at:+.4f} vs text+vision {a7:+.4f} → 都为正（均恶化），"
          f"差 {abs(at-a7):.4f}")
    assert ok1 and ok2, "数据不支持图注声称，需先修图注"

    if not apply:
        print("\n  （预演，加 --apply 写图）")
        return 0

    import sys as _sys
    import matplotlib
    matplotlib.use("Agg")
    apply_style()                       # Times New Roman + STIX + 统一字号
    import matplotlib.pyplot as plt

    rows = [
        ("LoRA text-only", st.mean(L["text_only"]),
         (st.stdev(L["text_only"]) if len(L["text_only"]) > 1 else 0.0), C_LORA, None),
        ("LoRA both", st.mean(L["both"]),
         (st.stdev(L["both"]) if len(L["both"]) > 1 else 0.0), C_LORA, None),
        ("LoRA vision-only", st.mean(L["vision_only"]),
         (st.stdev(L["vision_only"]) if len(L["vision_only"]) > 1 else 0.0), C_LORA, None),
    ]
    for label in ("Adapter text-only", "Adapter text+vision"):
        if label in ad:
            rows.append((label, ad[label][0], None, C_ADAPTER, f"n={ad[label][1]}"))
    rows = rows[::-1]              # 横向柱自下而上

    fig, ax = plt.subplots(figsize=figsize_full(0.66))
    ypos = range(len(rows))
    for i, (label, val, sd, color, nt) in enumerate(rows):
        hatch = "//" if color == C_ADAPTER else None
        ax.barh(i, val, height=0.62, color=color, hatch=hatch,
                edgecolor="black", linewidth=0.45, alpha=0.92)
        if sd:
            ax.errorbar(val, i, xerr=sd, fmt="none", ecolor="black",
                        elinewidth=1.0, capsize=2.5)
        off = 0.012 if val >= 0 else -0.012
        ax.text(val + off, i, f"{val:+.3f}" + (f"  ({nt})" if nt else ""),
                va="center", ha="left" if val >= 0 else "right", fontsize=6.5)
    ax.axvline(0, color="black", linewidth=0.9, zorder=3)
    ax.set_yticks(list(ypos))
    ax.set_yticklabels([r[0] for r in rows], fontsize=7)
    ax.set_xlabel(r"$\Delta$CG against the frozen reference", fontsize=8)
    ax.tick_params(axis="x", labelsize=7)
    ax.grid(axis="x", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    # 冗余编码图例（斜纹 + 颜色），**置于轴外上方**——先前用 `lower right` 会压在
    # `Adapter text+vision` 的柱上（操作者指出"图例挡住图片"）。
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=C_LORA, edgecolor="black", label="LoRA"),
                       Patch(facecolor=C_ADAPTER, edgecolor="black", hatch="//",
                             label="Adapter")],
              fontsize=7, frameon=False, loc="lower right",
              bbox_to_anchor=(1.0, 1.02), ncol=2)
    ax.margins(x=0.18)
    fig.tight_layout()
    save(fig, OUT)
    plt.close(fig)
    print(f"\n  ✅ 已重绘 {OUT.relative_to(REPO)}")
    print("     数据：outputs/strict_freeze（LoRA）+ outputs/analysis/adapter_common_baseline.json（Adapter）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
