# -*- coding: utf-8 -*-
r"""`fig8c`：视觉侧受到的实际影响（有效秩变化），**不是**"收到更新的张量数"（2026-10-06 重做）。

## 为什么改

原图画 `vision_nonzero_tensors`，三臂**全是 0**（严格冻结下两个塔的权重都不可训 → 恒为 0），
**是空图，且图注把"权重不可训"说成了"梯度为零"的证据**。

改画 `vision_rank_delta_mean`（LoRA 对视觉侧的**实际**影响）：
**text_only 恰为 0，both / vision_only 非零** —— 这才是与"直接测得零视觉梯度"对应的权重侧证据。

    python tools\_pa_fig8c.py
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
apply_style()
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np               # noqa: E402

SRC = ROOT / "outputs" / "analysis" / "strict_control_summary.json"
OUT = ROOT / "paper合" / "figures" / "fig8c_vision_untouched.png"


def main() -> int:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    cfgs = d["configs"]
    names = ["text_only", "both", "vision_only"]
    lab = {"text_only": "text", "both": "both", "vision_only": "vision"}
    vals = [cfgs[k]["vision_rank_delta_mean"] for k in names]

    fig, ax = plt.subplots(figsize=figsize_wide(0.72))
    x = np.arange(3)
    colors = [OKABE_ITO["blue"] if v == 0 else OKABE_ITO["vermil"] for v in vals]
    ax.bar(x, vals, 0.5, color=colors, edgecolor="black", linewidth=0.4)
    ax.axhline(0, color="black", lw=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels([lab[k] for k in names])
    ax.set_ylabel(r"Vision-side $\Delta$ effective rank" "
" r"(LoRA effect, mean over layers)")
    ax.set_ylim(min(vals) * 1.6, max(vals) * 1.6 if max(vals) > 0 else 0.01)
    for xi, v in zip(x, vals):
        ax.annotate("%.4f" % v, (xi, v), textcoords="offset points",
                    xytext=(0, -11 if v < 0 else 5), ha="center", fontsize=7.5)
    save(fig, OUT)
    plt.close(fig)
    print("  ✅ 已重绘 fig8c_vision_untouched.png")
    print("     " + " ｜ ".join("%s=%+.4f" % (lab[k], v) for k, v in zip(names, vals)))
    # 断言：text_only 的视觉侧影响必须恰为零，其余非零
    assert vals[0] == 0.0, f"text_only 的视觉侧影响应为 0，实为 {vals[0]}"
    assert vals[1] != 0.0 and vals[2] != 0.0, "both/vision_only 的视觉侧影响应为非零"
    print("  ✅ 断言通过（text-only 恰为 0；both/vision-only 非零）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
