# -*- coding: utf-8 -*-
r"""补全模块层的 `import sys` / `from pathlib import Path`（2026-10-06）。

## 问题

`tools/_pa_fix_style_scope.py` 把 `from figure_style import ...` 提到了模块层，但该行用到
`sys.path` 与 `Path`——而这 6 个脚本**在模块层没有 import sys / Path**
（它们是在 `main()` 里才 import 的）→ `NameError: name 'sys' is not defined`。

**这是同一类作用域错误的第三次**（torch、figsize_*、现在 sys/Path）。
**根治：把模块层需要的 import 一次性配对齐全。**

    python tools\_pa_fix_module_imports.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
T = REPO / "tools"

FILES = ["_pa_rebuild_figs_rest.py", "_pa_rebuild_fig10.py", "_pa_rebuild_fig12.py",
         "_pa_rebuild_fig4_crossmethod.py", "_pa_fix_fig14_title.py", "_fix_figure_overflow.py"]

NEED = ["import sys\n", "from pathlib import Path\n"]


def main() -> int:
    apply = "--apply" in sys.argv
    for name in FILES:
        p = T / name
        if not p.exists():
            print(f"  ⚠ 不存在：{name}")
            continue
        s = io.open(p, encoding="utf-8").read()
        lines = s.splitlines(keepends=True)
        # 找到 `from figure_style import` 所在行号
        idx = next((i for i, l in enumerate(lines) if "from figure_style import" in l), None)
        if idx is None:
            print(f"  ⚠ {name}: 无 figure_style import")
            continue
        # 检查模块层（figure_style import 之前）是否已有 import sys / Path
        head = "".join(lines[:idx])
        add = []
        if "import sys" not in head:
            add.append("import sys\n")
        if "from pathlib import Path" not in head:
            add.append("from pathlib import Path\n")
        if not add:
            print(f"  · {name}: 已齐")
            continue
        new = "".join(lines[:idx]) + "".join(add) + "".join(lines[idx:])
        if apply:
            try:
                ast.parse(new)
            except SyntaxError as e:
                print(f"  ❌ {name}: 语法错误（{e}）")
                continue
            io.open(p, "w", encoding="utf-8", newline="").write(new)
        print(f"  ✅ {name}: 补 {[a.strip() for a in add]}")

    # 语法总检
    if apply:
        bad = []
        for name in FILES:
            s = io.open(T / name, encoding="utf-8").read()
            try:
                ast.parse(s)
            except SyntaxError:
                bad.append(name)
        print(f"\n  {'✅ 全部语法通过' if not bad else '❌ ' + str(bad)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
