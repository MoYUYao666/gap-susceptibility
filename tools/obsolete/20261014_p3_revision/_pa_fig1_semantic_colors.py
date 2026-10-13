# -*- coding: utf-8 -*-
r"""给 `fig1.png` 的三条线加**显式语义配色**（2026-10-06）。

## 问题

上一轮只把 `fill_between` 改用 Okabe-Ito，**三条主线仍走 matplotlib 默认色轮**
（`#1f77b4` 蓝 / `#ff7f0e` 橙 / `#2ca02c` 绿）——故 `fig1` 配色与其余图**不统一**。

## 语义映射（与 `tools/figure_style.py` 一致，保证同一概念跨图同色）

| 系列 | 颜色 | 冗余编码 |
|---|---|---|
| Full FT | 中性灰 `#666666` | 点线 `:` |
| text-only | 蓝 `#0072B2` | 实线 `-` |
| both | 朱红 `#D55E00` | 虚线 `--` |

**冗余编码（线型）是必要的**：仅靠颜色在灰度打印或色觉异常读者那里会失效。

    python tools\_pa_fig1_semantic_colors.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_fix_figure_overflow.py"

OLD = ('    for k, rel in arms.items():\n'
       '        d = json.loads(io.open(REPO / rel, encoding="utf-8").read())\n'
       '        dcg = d["centroid_gap"][-1] - d["centroid_gap"][0]\n'
       '        ax.plot(d["epoch"], d["centroid_gap"], "-", linewidth=1.5, label=f"{k} (ΔCG {dcg:+.3f})")')

NEW = ('    # 语义配色 + **线型冗余编码**（灰度/色觉异常下仍可区分）\n'
       '    _style = {"Full FT": (OKABE_ITO["grey"], ":"),\n'
       '              "text-only": (OKABE_ITO["blue"], "-"),\n'
       '              "both": (OKABE_ITO["vermil"], "--")}\n'
       '    for k, rel in arms.items():\n'
       '        d = json.loads(io.open(REPO / rel, encoding="utf-8").read())\n'
       '        dcg = d["centroid_gap"][-1] - d["centroid_gap"][0]\n'
       '        _c, _ls = _style.get(k, (OKABE_ITO["purple"], "-"))\n'
       '        ax.plot(d["epoch"], d["centroid_gap"], _ls, color=_c, linewidth=1.6,\n'
       '                label=f"{k} (ΔCG {dcg:+.3f})")')


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if '_style = {"Full FT"' in t:
        print("  已应用，跳过")
        return 0
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        # 打印实际片段帮助定位
        i = t.find("for k, rel in arms.items():")
        print("     实际：")
        print(repr(t[i:i + 320]))
        return 1
    print("  ✅ 命中 fig1 的绘图循环")
    if apply:
        io.open(F, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW, 1))
        t2 = io.open(F, encoding="utf-8").read()
        assert '_style = {"Full FT"' in t2 and 'OKABE_ITO["vermil"], "--"' in t2
        ast.parse(t2)
        print("  ✅ 已写入并断言通过")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
