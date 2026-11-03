# -*- coding: utf-8 -*-
r"""重做 `fig8c` 与 `fig14`（2026-10-06，操作者指出）。

## `fig8c_vision_untouched`（Figure 10）——**数据选错，图注也错**

原图画 `vision_nonzero_tensors`，三个臂**全是 0** → **空图**。
原因：**严格冻结下两个塔的原始权重都不可训**，"收到更新的视觉张量数"**恒为 0**——
**这是冻结协议的必然产物，不是发现**。

**真正有信息的是 `vision_rank_delta_mean`**（LoRA 对视觉侧的**实际**影响）：

| 臂 | `vision_nonzero_tensors` | **`vision_rank_delta_mean`** |
|---|---|---|
| text_only | 0 | **0.0000** ← 恰好为零 |
| both | 0 | **−0.0421** ← **非零** |
| vision_only | 0 | **−0.0588** |

**图注也错**：原文写 "the text-only **and the both-position** strict arms leave the vision side at
zero"——**both 臂明明非零**。且把"权重不可训"与"梯度为零"混为一谈——**后者才是可测的发现**。

## `fig14_adapter_layered`（Figure 15）——**图例压住数据线**

左面板图例正压在两条 CG 曲线上；且 2 面板并排仅 1.86 in/格，偏挤。
→ **改上下两行**（共享 x 轴），每行占满 3.71 in 宽，图例移出绘图区。

    python tools\_pa_fix_fig8c_fig14.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

# ── ① 给样式库加"竖排"尺寸
FS = REPO / "tools" / "figure_style.py"
OLD_FN = ('def figsize_wide(h_ratio: float = 0.72) -> tuple[float, float]:\n'
          '    """0.78\\textwidth 的图。"""\n'
          '    return FIG_W_WIDE, FIG_W_WIDE * h_ratio')
NEW_FN = (OLD_FN + '\n\n\n'
          'def figsize_tall(h_ratio: float = 1.15) -> tuple[float, float]:\n'
          '    """**竖排两行**的图（0.78\\textwidth 宽，每行约 2.1 in 高）。\n\n'
          '    用于两个面板共享 x 轴的场景——并排时每格仅 1.86 in 宽，竖排则每行占满栏宽。\n'
          '    """\n'
          '    return FIG_W_WIDE, FIG_W_WIDE * h_ratio')

# ── ② fig8c：改画 vision_rank_delta
FIG8C = '''# -*- coding: utf-8 -*-
r"""`fig8c`：视觉侧受到的实际影响（有效秩变化），**不是**"收到更新的张量数"（2026-10-06 重做）。

## 为什么改

原图画 `vision_nonzero_tensors`，三臂**全是 0**（严格冻结下两个塔的权重都不可训 → 恒为 0），
**是空图，且图注把"权重不可训"说成了"梯度为零"的证据**。

改画 `vision_rank_delta_mean`（LoRA 对视觉侧的**实际**影响）：
**text_only 恰为 0，both / vision_only 非零** —— 这才是与"直接测得零视觉梯度"对应的权重侧证据。

    python tools\\_pa_fig8c.py
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
    ax.set_ylabel(r"Vision-side $\Delta$ effective rank" "\n" r"(LoRA effect, mean over layers)")
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
'''

# ── ③ fig14：改竖排两行
FIG14 = '''# -*- coding: utf-8 -*-
r"""`fig14`：Adapter 分层微调，**改为上下两行**（2026-10-06 重做）。

## 为什么改

原图 2 面板**并排**：每格仅 1.86 in 宽，**左面板图例正压在两条 CG 曲线上**。
改为**上下两行共享 x 轴**：每行占满 3.71 in 宽，图例移出绘图区。

图注里的数字（frozen $0.81$、text-only $+0.25$、text+vis $+0.50$、$R@1$ $0.06$/$0.005$）
在写图前**先与归档 JSON 断言核对**。

    python tools\\_pa_fig14_tall.py
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
    fz = last(d["Frozen"])
    a1 = last(d["Adapter Text-only"])
    a2 = last(d["Adapter Text+Vis"])
    g1, g2 = a1[0] - fz[0], a2[0] - fz[0]
    print("  frozen CG=%.4f R@1=%.4f" % fz)
    print("  text-only  CG=%.4f (+%.2f)  R@1=%.3f" % (a1[0], g1, a1[1]))
    print("  text+vis   CG=%.4f (+%.2f)  R@1=%.3f" % (a2[0], g2, a2[1]))

    CV, CT = OKABE_ITO["blue"], OKABE_ITO["vermil"]
    CG_ = OKABE_ITO["grey"]
    fig, axes = plt.subplots(2, 1, figsize=figsize_tall(1.15), sharex=True)

    style = {"Frozen": (CG_, "s", "--"), "Adapter Text-only": (CV, "o", "-"),
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
    # 图例移出绘图区（原并排版压在数据线上）
    axes[0].legend(frameon=False, ncol=3, loc="upper center",
                   bbox_to_anchor=(0.5, 1.16), fontsize=7.5, handlelength=1.6,
                   columnspacing=1.0)
    save(fig, OUT)
    plt.close(fig)
    print("  ✅ 已重绘 fig14_adapter_layered.png（竖排两行）")
    # 断言：图注里的数字
    assert abs(fz[0] - 0.81) < 0.02, f"frozen CG 应≈0.81，实为 {fz[0]:.4f}"
    assert abs(g1 - 0.25) < 0.03, f"text-only 增量应≈0.25，实为 {g1:.4f}"
    assert abs(g2 - 0.50) < 0.03, f"text+vis 增量应≈0.50，实为 {g2:.4f}"
    assert a1[1] < 0.10 and a2[1] < 0.05, "R@1 应塌到接近 0"
    print("  ✅ 断言通过（0.81 / +0.25 / +0.50 / R@1≈0）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演，加 --apply）")
        return 0

    # ① 样式库
    t = io.open(FS, encoding="utf-8").read()
    if "def figsize_tall" not in t:
        assert OLD_FN in t, "未找到 figsize_wide 定义"
        io.open(FS, "w", encoding="utf-8", newline="").write(t.replace(OLD_FN, NEW_FN, 1))
        print("  ✅ figure_style.py：已加 figsize_tall()")

    # ② ③ 写两个绘图脚本
    for path, body in ((REPO / "tools" / "_pa_fig8c.py", FIG8C),
                       (REPO / "tools" / "_pa_fig14_tall.py", FIG14)):
        io.open(path, "w", encoding="utf-8", newline="").write(body)
        import ast
        ast.parse(body)
        print(f"  ✅ 已写 {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
