# -*- coding: utf-8 -*-
r"""给所有绘图脚本统一加 **Times New Roman + 最终尺寸**（2026-10-06，操作者要求）。

## 改什么

对每个绘图脚本做三件事：

1. **接入共享样式**：`from figure_style import apply_style, figsize_full, figsize_wide, save`
   并在 `import matplotlib` 之后立即 `apply_style()`；
2. **画布改为最终尺寸**：`figsize=(5.6, 3.4)` → `figsize=figsize_full(0.60)` 等
   （**按 LaTeX 里的实际宽度出图，导出后不再缩放**——skill 原则 1）；
3. **出口改为 `save(fig, OUT)`**，同时出 PNG（稿子现用）与 PDF（矢量，原则 2）。

## 为什么

先前各图在**任意画布**下画，再由 LaTeX 缩放，导致**文字被缩小且倍率不一**
（`fig8` ×0.28、`fig10` ×0.48、`fig1` ×0.75）→ 同一稿子字号差 3 倍。
现在按最终尺寸出图，**9 pt 刻度 / 8 pt 图例就是最终的 9 pt / 8 pt**。

    python tools\_pa_apply_figure_style.py [--apply]
"""
from __future__ import annotations

import ast
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
T = REPO / "tools"

IMPORT_ANCHOR = "import matplotlib\n    matplotlib.use(\"Agg\")\n    import matplotlib.pyplot as plt"
IMPORT_NEW = ("import sys as _sys\n"
              "    _sys.path.insert(0, str(Path(__file__).resolve().parents[1] / \"tools\"))\n"
              "    from figure_style import apply_style, figsize_full, figsize_wide, save\n"
              "    import matplotlib\n"
              "    matplotlib.use(\"Agg\")\n"
              "    apply_style()                       # Times New Roman + STIX + 统一字号\n"
              "    import matplotlib.pyplot as plt")

# 脚本 -> (画布替换规则, 出口替换规则)
PLAN = {
    "_pa_rebuild_figs_rest.py": [
        ("fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.1))",
         "fig, axes = plt.subplots(1, 2, figsize=figsize_wide(0.60))"),
        ("fig, ax = plt.subplots(figsize=(5.6, 3.4))",
         "fig, ax = plt.subplots(figsize=figsize_full(0.60))"),
        ("fig, ax = plt.subplots(figsize=(4.6, 3.2))",
         "fig, ax = plt.subplots(figsize=(FIG_W_FULL, FIG_W_FULL * 0.66))"),
        ("fig, ax = plt.subplots(figsize=(5.0, 3.3))",
         "fig, ax = plt.subplots(figsize=(FIG_W_FULL, FIG_W_FULL * 0.66))"),
    ],
    "_pa_rebuild_fig10.py": [
        ("fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.1))",
         "fig, axes = plt.subplots(1, 2, figsize=figsize_wide(0.60))"),
    ],
    "_pa_rebuild_fig12.py": [
        ("fig, ax = plt.subplots(figsize=(5.2, 3.4))",
         "fig, ax = plt.subplots(figsize=figsize_full(0.68))"),
    ],
    "_pa_rebuild_fig4_crossmethod.py": [
        ("fig, ax = plt.subplots(figsize=(5.6, 3.4))",
         "fig, ax = plt.subplots(figsize=figsize_full(0.66))"),
    ],
    "_fix_figure_overflow.py": [
        ("fig, ax = plt.subplots(figsize=(5.6, 3.7))",
         "fig, ax = plt.subplots(figsize=figsize_full(0.66))"),
    ],
    "_pa_fix_fig14_title.py": [
        ("fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.1))",
         "fig, axes = plt.subplots(1, 2, figsize=figsize_wide(0.60))"),
    ],
    "_pa_fig8_rebuild.py": [],
    "_pa_fig9_noise_rebuild.py": [],
    "_pa_fig2_corr.py": [],
}

# 出口：把 fig.savefig(OUT, dpi=300) / fig.savefig(OUT) 换成 save(fig, OUT)（同时出 PDF）
SAVE_PATTERNS = [
    ("fig.savefig(OUT, dpi=300)", "save(fig, OUT)"),
    ("fig.savefig(OUT)", "save(fig, OUT)"),
    ("fig.savefig(OUT, dpi=300)\n", "save(fig, OUT)\n"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    grand = 0
    for name, reps in PLAN.items():
        p = T / name
        if not p.exists():
            print(f"  ⚠ 不存在：{name}")
            continue
        s = io.open(p, encoding="utf-8").read()
        orig = s
        hits = []

        # ① 导入并应用样式
        if "from figure_style import" not in s:
            if IMPORT_ANCHOR in s:
                s = s.replace(IMPORT_ANCHOR, IMPORT_NEW, 1)
                hits.append("接入 apply_style")
            elif 'matplotlib.use("Agg")' in s:
                s = s.replace('matplotlib.use("Agg")',
                              'matplotlib.use("Agg")\n'
                              '    _sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))\n'
                              '    from figure_style import apply_style, figsize_full, figsize_wide, save, FIG_W_FULL\n'
                              '    apply_style()', 1)
                s = s.replace("    import sys\n", "    import sys as _sys\n", 1)
                hits.append("接入 apply_style（备选锚点）")

        # ② 画布尺寸
        for old, new in reps:
            if old in s:
                s = s.replace(old, new)
                hits.append(old.split("figsize=")[-1][:22])

        # ③ 出口
        for old, new in SAVE_PATTERNS:
            if old in s:
                s = s.replace(old, new)
                hits.append("save()")
                break

        if s != orig:
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(s)
                try:
                    ast.parse(s)
                except SyntaxError as e:
                    print(f"  ❌ {name}: 语法错误 {e}")
                    io.open(p, "w", encoding="utf-8", newline="").write(orig)
                    print("     已回滚")
                    continue
            print(f"  ✅ {name}: {', '.join(hits)}")
            grand += len(hits)
        else:
            print(f"  ⚠ {name}: 无改动")

    print(f"\n  共 {grand} 处" + ("（已写入）" if apply else "（预演）"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
