# -*- coding: utf-8 -*-
r"""给 `fig2` / `fig8` / `fig9` 三个绘图脚本接上统一字体与最终尺寸（2026-10-06）。

## 为什么单独处理

上一轮自动补丁对这三个**失败并已回滚**——它们的 `import matplotlib` 在**模块顶层**
（不在 `main()` 里），缩进为 0，而我按 4 空格缩进插入 → `SyntaxError: unexpected indent`。

## 三个脚本的画布与最终宽度

| 脚本 | 现画布 | LaTeX 宽度 | 最终宽 | 缩放 |
|---|---|---|---|---|
| `_pa_fig8_rebuild.py`（1×3 面板） | 13.5 in | `0.78\textwidth` | 3.713 in | **×0.275** |
| `_pa_fig9_noise_rebuild.py`（1×3） | 13.5 in | `0.78\textwidth` | 3.713 in | ×0.275 |
| `_pa_fig2_corr.py`（1×2） | 8.0 in | `0.88\textwidth` | 4.189 in | ×0.524 |

**→ 这正是"字号差 3 倍"的来源**：`fig8` 的 9 pt 字被压到 2.5 pt。

    python tools\_pa_style_3figs.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
T = REPO / "tools"

PLAN = {
    "_pa_fig8_rebuild.py": (
        'import matplotlib\nmatplotlib.use("Agg")\nimport matplotlib.pyplot as plt',
        'import sys as _sys\n_sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "tools"))\n'
        'from figure_style import apply_style, figsize_wide, save\n'
        'import matplotlib\nmatplotlib.use("Agg")\napply_style()          # Times New Roman + STIX + 统一字号\n'
        'import matplotlib.pyplot as plt',
        [("fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.9))",
          "fig, axes = plt.subplots(1, 3, figsize=figsize_wide(0.32))"),
         ('fig.savefig(OUT, dpi=300, bbox_inches="tight")', "save(fig, OUT)")],
    ),
    "_pa_fig9_noise_rebuild.py": (
        'import matplotlib\nmatplotlib.use("Agg")\nimport matplotlib.pyplot as plt',
        'import sys as _sys\n_sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "tools"))\n'
        'from figure_style import apply_style, figsize_wide, save\n'
        'import matplotlib\nmatplotlib.use("Agg")\napply_style()          # Times New Roman + STIX + 统一字号\n'
        'import matplotlib.pyplot as plt',
        [("fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.8))",
          "fig, axes = plt.subplots(1, 3, figsize=figsize_wide(0.32))"),
         ('fig.savefig(OUT, dpi=300, bbox_inches="tight")', "save(fig, OUT)")],
    ),
    "_pa_fig2_corr.py": (
        'import matplotlib\nmatplotlib.use("Agg")\nimport matplotlib.pyplot as plt',
        'import sys as _sys\n_sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "tools"))\n'
        'from figure_style import apply_style, figsize_full, save\n'
        'import matplotlib\nmatplotlib.use("Agg")\napply_style()          # Times New Roman + STIX + 统一字号\n'
        'import matplotlib.pyplot as plt',
        [("fig, axes = plt.subplots(1, 2, figsize=(8, 3.5))",
          "fig, axes = plt.subplots(1, 2, figsize=figsize_full(0.46))"),
         ('fig.savefig(out, dpi=300, bbox_inches="tight")', "save(fig, out)")],
    ),
}


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for name, (old_imp, new_imp, reps) in PLAN.items():
        p = T / name
        if not p.exists():
            print(f"  ⚠ 不存在：{name}")
            continue
        s = io.open(p, encoding="utf-8").read()
        orig = s
        hits = []
        if "from figure_style import" in s:
            print(f"  · {name}: 已接入样式")
        elif old_imp in s:
            s = s.replace(old_imp, new_imp, 1)
            hits.append("接入 apply_style")
        else:
            print(f"  ⚠ {name}: 未匹配 import 锚点")
        for old, new in reps:
            if old in s:
                s = s.replace(old, new)
                hits.append(old[:44])
        if s != orig:
            if apply:
                try:
                    ast.parse(s)
                except SyntaxError as e:
                    print(f"  ❌ {name}: 语法错误（{e}）——跳过")
                    continue
                io.open(p, "w", encoding="utf-8", newline="").write(s)
            print(f"  ✅ {name}: {', '.join(hits)}")
            n += len(hits)
        else:
            print(f"  ⚠ {name}: 无改动")
    print(f"\n  共 {n} 处" + ("（已写入）" if apply else "（预演）"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
