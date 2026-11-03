# -*- coding: utf-8 -*-
r"""把 Okabe-Ito 调色板应用到 `tools/_fix_figure_overflow.py`（2026-10-06）。

## 为什么

`fig1.png` 与 `fig4_effective_rank.png` 的重绘代码在 `_fix_figure_overflow.py` 里
（不在 `_pa_rebuild_figs_rest.py`），故上一轮统一配色时**漏掉了这两个**——
`fig1` 仍是旧的 `#1f77b4 / #ff7f0e / #2ca02c`（matplotlib 默认系），**配色不统一**。

    python tools\_pa_apply_palette_to_overflow.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_fix_figure_overflow.py"

ANCHOR = '    import matplotlib\n    matplotlib.use("Agg")'
INSERT = ('    # ── Okabe-Ito 色盲友好调色板（2026-10-06 统一；定义见 tools/figure_style.py）\n'
          '    import sys as _sys\n'
          '    _sys.path.insert(0, str(REPO / "tools"))\n'
          '    from figure_style import OKABE_ITO\n'
          '    import matplotlib\n'
          '    matplotlib.use("Agg")')

REPS = [
    ('color="#1f77b4", label=f"text-only, {len(seeds)} seeds"',
     'color=OKABE_ITO["blue"], label=f"text-only, {len(seeds)} seeds"'),
    ('"s--", color="#d62728",', '"s--", color=OKABE_ITO["vermil"],'),
    ('"o-", color="#1f77b4",', '"o-", color=OKABE_ITO["blue"],'),
    ('color="#1f77b4", alpha=0.12', 'color=OKABE_ITO["blue"], alpha=0.12'),
]


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "OKABE_ITO" in t:
        print("  已应用，跳过")
        return 0
    if ANCHOR not in t:
        print("  ⚠ 未找到 matplotlib 锚点")
        return 1
    n = 0
    for old, new in REPS:
        c = t.count(old)
        if c:
            t = t.replace(old, new)
            n += c
            print(f"  ✅ {c} 处：{old[:52]}…")
        else:
            print(f"  ⚠ 未命中：{old[:52]}…")
    if apply:
        t = t.replace(ANCHOR, INSERT, 1)
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        ast.parse(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "OKABE_ITO" in t2 and "#1f77b4" not in t2 and "#d62728" not in t2
        print(f"  ✅ 已写入（共替换 {n} 处色值 + 插入调色板）")
    else:
        print(f"\n  {n} 处可改（预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
