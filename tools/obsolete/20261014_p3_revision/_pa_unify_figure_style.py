# -*- coding: utf-8 -*-
r"""统一修图的**图例遮挡**与**配色**（2026-10-06，操作者指出的两个问题）。

## 问题（操作者）："图片有的图例会挡住图片""图片的配色不高级"

### 图例遮挡（实测）

| 图 | 问题 |
|---|---|
| `fig4.png` | **我刚重做的就有**：图例在 `lower right`，正压在 `Adapter text+vision` 柱上 |
| 其余各图 | 多数用 `loc="best"` 或默认位置，未逐张核对 |

### 配色

先前各脚本各自为政：有的用 matplotlib 默认（`#1f77b4` 等**饱和蓝橙红**），有的混用。
**不统一、饱和度偏高、未做色盲与灰度检查。**

## 本脚本的处置（按 `scipilot-figure-skill` 硬性原则）

1. **配色统一为 Okabe-Ito**（色盲友好国际标准）：

   | 语义 | 色值 | 用途 |
   |---|---|---|
   | 主色/蓝 | `#0072B2` | text-only / LoRA / 实测 |
   | 强调/朱红 | `#D55E00` | both / Adapter / 预测对照 |
   | 第三/绿 | `#009E73` | vision-only |
   | 中性灰 | `#666666` | Frozen / 基准 |
   | 第四/紫 | `#CC79A7` | 其他 |

2. **冗余编码**：不同类别同时用**颜色 + 线型/marker/斜纹**（灰度打印也能分）；
3. **图例放框外**（`bbox_to_anchor`）或**数据空白区**，并**逐张目视复核**；
4. **出灰度版**自检（原则 3）。

    python tools\_pa_unify_figure_style.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PALETTE = '''# ── Okabe-Ito 色盲友好调色板（2026-10-06 统一；见 scipilot-figure-skill 原则 3）
OKABE_ITO = {
    "blue":   "#0072B2",   # 主色：text-only / LoRA / 实测
    "vermil": "#D55E00",   # 强调：both / Adapter / 预测对照
    "green":  "#009E73",   # 第三：vision-only
    "grey":   "#666666",   # 中性：Frozen / 基准
    "purple": "#CC79A7",   # 第四
    "sky":    "#56B4E9",   # 浅蓝
    "yellow": "#E69F00",   # 橙黄
}
# 语义映射，供各绘图脚本共用，保证同一概念在不同图里同色
SEMANTIC = {
    "text_only":   OKABE_ITO["blue"],
    "both":        OKABE_ITO["vermil"],
    "vision_only": OKABE_ITO["green"],
    "frozen":      OKABE_ITO["grey"],
    "measured":    OKABE_ITO["blue"],
    "predicted":   OKABE_ITO["vermil"],
    "lora":        OKABE_ITO["blue"],
    "adapter":     OKABE_ITO["vermil"],
}

'''

STYLE_MODULE = REPO / "tools" / "figure_style.py"

TARGETS = [
    ("tools/_pa_rebuild_figs_rest.py", [
        ('colors = {"Frozen": "#444444", "Text + Vis-L1": "#2ca02c", "Text + Vis-L2": "#98df8a",\n'
         '              "Text + Vis-L4": "#c5b0d5", "Text-only": "#1f77b4", "Both (all Vis)": "#d62728"}',
         'from figure_style import OKABE_ITO as _OI\n'
         '    colors = {"Frozen": _OI["grey"], "Text + Vis-L1": _OI["blue"], "Text + Vis-L2": _OI["sky"],\n'
         '              "Text + Vis-L4": _OI["green"], "Text-only": _OI["purple"], "Both (all Vis)": _OI["vermil"]}'),
        ('color="#1f77b4", linewidth=1.6', 'color=OKABE_ITO["blue"], linewidth=1.6'),
        ('color="#d62728", linewidth=1.4', 'color=OKABE_ITO["vermil"], linewidth=1.4'),
        ('fill_between(ep, lo, hi, alpha=0.18, color="#1f77b4"',
         'fill_between(ep, lo, hi, alpha=0.18, color=OKABE_ITO["blue"]'),
        ('ax.plot(xs, [math.sqrt(r / ranks[0]) for r in ranks], "s--", color="#d62728",',
         'ax.plot(xs, [math.sqrt(r / ranks[0]) for r in ranks], "s--", color=OKABE_ITO["vermil"],'),
        ('ax.plot(xs, [v / vals[0] for v in vals], "o-", color="#1f77b4",',
         'ax.plot(xs, [v / vals[0] for v in vals], "o-", color=OKABE_ITO["blue"],'),
        ('ax.fill_between(xs, 0.95, 1.05, color="#1f77b4", alpha=0.12',
         'ax.fill_between(xs, 0.95, 1.05, color=OKABE_ITO["blue"], alpha=0.12'),
        ('ax.plot([int(x) for x in xs], [vals[x] for x in xs], "o-", color="#1f77b4", linewidth=1.5, markersize=5)',
         'ax.plot([int(x) for x in xs], [vals[x] for x in xs], "o-", color=OKABE_ITO["blue"], linewidth=1.5, markersize=5)'),
    ]),
    ("tools/_pa_rebuild_fig10.py", [
        ('colors = {"Frozen": "#444444", "Text + Vis-L1": "#2ca02c", "Text + Vis-L2": "#98df8a",\n'
         '              "Text + Vis-L4": "#c5b0d5", "Text-only": "#1f77b4", "Both (all Vis)": "#d62728"}',
         'from figure_style import OKABE_ITO as _OI\n'
         '    colors = {"Frozen": _OI["grey"], "Text + Vis-L1": _OI["blue"], "Text + Vis-L2": _OI["sky"],\n'
         '              "Text + Vis-L4": _OI["green"], "Text-only": _OI["purple"], "Both (all Vis)": _OI["vermil"]}'),
    ]),
    ("tools/_pa_fix_fig14_title.py", [
        ('colors = {"Frozen": "#7f7f7f", "Adapter Text-only": "#1f77b4", "Adapter Text+Vis": "#d62728"}',
         'from figure_style import OKABE_ITO as _OI\n'
         '    colors = {"Frozen": _OI["grey"], "Adapter Text-only": _OI["blue"], "Adapter Text+Vis": _OI["vermil"]}'),
        ('axes[0].legend(fontsize=7, frameon=False, loc="center right")',
         '# 图例移出绘图区，避免压数据（操作者指出"图例挡住图片"）\n'
         '    axes[0].legend(fontsize=7, frameon=False, loc="upper left", bbox_to_anchor=(0.02, 0.98))'),
    ]),
    ("tools/_pa_rebuild_fig12.py", [
        ('colors = {"Frozen": "#444444", "Text-only": "#1f77b4", "Both": "#ff7f0e"}',
         'from figure_style import OKABE_ITO as _OI\n'
         '    colors = {"Frozen": _OI["grey"], "Text-only": _OI["blue"], "Both": _OI["vermil"]}'),
        ('ax.legend(fontsize=7, frameon=False, ncol=3, loc="lower center")',
         '# 图例置于轴下方（数据柱从 0 起，图内无空白），避免压柱\n'
         '    ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper center",\n'
         '              bbox_to_anchor=(0.5, -0.12))'),
    ]),
]


def main() -> int:
    apply = "--apply" in sys.argv

    # ① 写共享样式模块
    if apply:
        io.open(STYLE_MODULE, "w", encoding="utf-8", newline="").write(PALETTE)
        print(f"  ✅ 已写 {STYLE_MODULE.relative_to(REPO)}（Okabe-Ito + 语义映射）")
    else:
        print(f"  将写 {STYLE_MODULE.relative_to(REPO)}")

    # ② 替换各脚本里的配色与图例位置
    n = 0
    for rel, reps in TARGETS:
        p = REPO / rel
        if not p.exists():
            print(f"  ⚠ 不存在：{rel}")
            continue
        s = io.open(p, encoding="utf-8").read()
        hit = 0
        for old, new in reps:
            if old in s:
                s = s.replace(old, new)
                hit += 1
        if hit:
            print(f"  ✅ {Path(rel).name}: {hit}/{len(reps)} 处")
            n += hit
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(s)
                import ast
                ast.parse(s)
        else:
            print(f"  ⚠ {Path(rel).name}: 0 处命中")

    print(f"\n  共 {n} 处")
    if not apply:
        print("  （预演，加 --apply）")
        return 0

    # ③ 图例遮挡自检：把图例定位改为避免数据区的写法后，逐张渲染复核
    print("\n  === 下一步：重绘各图并逐张目视复核图例 ===")
    print("     python tools\\_pa_rebuild_figs_rest.py --apply")
    print("     python tools\\_pa_rebuild_fig10.py --apply")
    print("     python tools\\_pa_rebuild_fig12.py --apply")
    print("     python tools\\_pa_fix_fig14_title.py --apply")
    print("     python tools\\_pa_rebuild_fig4_crossmethod.py --apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
