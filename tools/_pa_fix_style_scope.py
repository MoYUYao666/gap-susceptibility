# -*- coding: utf-8 -*-
r"""把 `figure_style` 的 import 提到**模块层**（2026-10-06）。

## 问题

上一轮把 `from figure_style import apply_style, figsize_full, ...` 插在 **`main()` 内部**
（因为锚点是 `import matplotlib` 在 main 里）。但 `figsize_full(...)` / `save(...)` 的调用点在
**模块级的绘图函数**里（如 `_pa_rebuild_figs_rest.py` 的 `fig_overview()`）→
`NameError: name 'figsize_full' is not defined`。

**与之前 `torch` 那次是同一类错误**（脚本内作用域 ≠ 模块作用域）。

## 修法

把 `from figure_style import ...` **提到模块顶层**（紧跟其它 import），
`main()` 内只保留 `apply_style()` 调用。

    python tools\_pa_fix_style_scope.py [--apply]
"""
from __future__ import annotations

import ast
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
T = REPO / "tools"

FILES = ["_pa_rebuild_figs_rest.py", "_pa_rebuild_fig10.py", "_pa_rebuild_fig12.py",
         "_pa_rebuild_fig4_crossmethod.py", "_pa_fix_fig14_title.py", "_fix_figure_overflow.py"]

MODULE_IMPORT = ("# ── 共享图样式（Times New Roman + 最终尺寸；定义见 tools/figure_style.py）\n"
                 "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / \"tools\"))\n"
                 "from figure_style import (apply_style, figsize_full, figsize_wide,\n"
                 "                          save, FIG_W_FULL, OKABE_ITO)  # noqa: E402\n\n")


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for name in FILES:
        p = T / name
        if not p.exists():
            print(f"  ⚠ 不存在：{name}")
            continue
        s = io.open(p, encoding="utf-8").read()
        orig = s

        # ① 删掉 main() 里那两行局部 import（保留 apply_style() 调用）
        s = re.sub(r"[ \t]*_sys\.path\.insert\([^\n]*\n", "", s, count=1)
        s = re.sub(r"[ \t]*from figure_style import[^\n]*\n", "", s, count=1)

        # ② 在模块层插入（放在 `from pathlib import Path` 或最后一个顶层 import 之后）
        if "from figure_style import" not in s:
            anchor = None
            for cand in ("from pathlib import Path\n", "import sys\n", "import io\n"):
                i = s.find(cand)
                if i >= 0 and (anchor is None or i < anchor):
                    anchor = i + len(cand)
            if anchor is None:
                print(f"  ⚠ {name}: 找不到模块层 import 锚点")
                continue
            s = s[:anchor] + "\n" + MODULE_IMPORT + s[anchor:]
            n += 1

        if s != orig:
            if apply:
                try:
                    ast.parse(s)
                except SyntaxError as e:
                    print(f"  ❌ {name}: 语法错误（{e}）——跳过")
                    continue
                io.open(p, "w", encoding="utf-8", newline="").write(s)
            print(f"  ✅ {name}")
        else:
            print(f"  · {name}: 无改动")

    print(f"\n  {n} 个文件" + ("（已写入）" if apply else "（预演）"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
