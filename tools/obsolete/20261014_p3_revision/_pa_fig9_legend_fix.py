# -*- coding: utf-8 -*-
r"""fig9 图例位置微调（2026-10-06）。

## 问题（目视复核发现）

上一版把 A、B 的图例放在**轴外上方**（`bbox_to_anchor=(0.5, 1.02)`）→ 与 y 轴顶部刻度
（`1.00`、`6`）**挤在一起**，且 B 的 x 轴刻度（1,2,3,4,5 用浮点标签）过密。

## 修法

| 面板 | 改动 |
|---|---|
| A | 图例移到**轴内右上角**（该处数值 2 左右，柱最高 2.5，右上留白） |
| B | 图例移到**轴内下方中部**（数据全在 y=0 线上，下方大片空白） |
| B | x 轴刻度改为**整数且稀疏**（1,3,5），并设 `MaxNLocator(integer=True)` |

    python tools\_pa_fig9_legend_fix.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_pa_fig9_fix.py"

REPS = [
    # A：图例移到轴内右上（留白区）
    ('    ax.legend(frameon=False, ncol=2, loc="upper center",\n'
     '              bbox_to_anchor=(0.5, 1.02), columnspacing=0.9, handlelength=1.2)\n'
     '\n'
     '    # ── B：σ=0 对照（必须精确为 0）',
     '    # 图例置于轴内右上留白（该区数值 ≤2.5，右上空）——放轴外会与 y 轴顶部刻度相挤\n'
     '    ax.legend(frameon=False, ncol=1, loc="upper right", handlelength=1.2,\n'
     '              borderaxespad=0.15)\n'
     '\n'
     '    # ── B：σ=0 对照（必须精确为 0）'),
    # B：图例移到轴内下方
    ('    ax.legend(frameon=False, ncol=2, loc="upper center",\n'
     '              bbox_to_anchor=(0.5, 1.02), columnspacing=0.9, handlelength=1.2)\n'
     '\n'
     '    # ── C：测得比值 vs 旧文声称的 2.6×',
     '    # 数据全在 y=0 线上，下方大片空白 → 图例置于轴内下方\n'
     '    ax.legend(frameon=False, ncol=2, loc="lower center", columnspacing=0.9,\n'
     '              handlelength=1.2, borderaxespad=0.2)\n'
     '\n'
     '    # ── C：测得比值 vs 旧文声称的 2.6×'),
    # B：x 轴整数稀疏刻度
    ('    ax.set_ylim(-1.0, 1.0)\n    ax.set_xlabel("Seed index")',
     '    ax.set_ylim(-1.0, 1.0)\n'
     '    ax.set_xticks([1, 3, 5])          # 整数稀疏刻度，避免浮点标签拥挤\n'
     '    ax.set_xlabel("Seed index")'),
]


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    n = 0
    for old, new in REPS:
        c = t.count(old)
        if c == 1:
            t = t.replace(old, new, 1)
            n += 1
        else:
            print(f"  ⚠ 命中 {c} 次：{old[:46]!r}")
    print(f"  {n}/{len(REPS)} 处")
    if apply and n:
        try:
            ast.parse(t)
        except SyntaxError as e:
            print(f"  ❌ 语法错误：{e}")
            return 1
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        print("  ✅ 已写入")
    elif not apply:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
