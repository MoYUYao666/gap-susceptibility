# -*- coding: utf-8 -*-
r"""修正模块层 import 的**顺序**（2026-10-06）。

## 问题（读文件才看清）

`_pa_fix_style_scope.py` 把共享样式块插在了**文件最前面的 import 锚点之后**，
但锚点选得太靠前，导致块内 `sys.path.insert(...)`（用 `sys`、`Path`）
出现在 `import sys` / `from pathlib import Path` **之前**：

```python
import io

# ── 共享图样式 …
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))   # ← sys/Path 还没导入
import sys
from pathlib import Path
from figure_style import (...)
```

→ `NameError: name 'sys' is not defined`。

（后来 `_pa_fix_module_imports.py` 又在**块之后**补了一份 import sys/Path，
故文件里出现重复 import——也不该有。）

## 修法

把这些文件头部的共享样式块**规范化**为固定顺序：

```python
import sys
from pathlib import Path

# ── 共享图样式（Times New Roman + 最终尺寸；定义见 tools/figure_style.py）
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from figure_style import (apply_style, figsize_full, figsize_wide,
                          save, FIG_W_FULL, OKABE_ITO)  # noqa: E402
```

并**去掉重复的 `import sys` / `from pathlib import Path`**。

    python tools\_pa_fix_import_order.py [--apply]
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

BLOCK_RE = re.compile(
    r"(# ── 共享图样式[^\n]*\n)"
    r"(?:import sys\n|from pathlib import Path\n|sys\.path\.insert\([^\n]*\n|"
    r"from figure_style import[^\n]*\n|(?:[ \t]+[^\n]*\n)|\)[^\n]*\n)*",
    re.M)

CANON = ("import sys\n"
         "from pathlib import Path\n\n"
         "# ── 共享图样式（Times New Roman + 最终尺寸；定义见 tools/figure_style.py）\n"
         "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / \"tools\"))\n"
         "from figure_style import (apply_style, figsize_full, figsize_wide,\n"
         "                          save, FIG_W_FULL, OKABE_ITO)  # noqa: E402\n")


def main() -> int:
    apply = "--apply" in sys.argv
    for name in FILES:
        p = T / name
        s = io.open(p, encoding="utf-8").read()
        m = BLOCK_RE.search(s)
        if not m:
            print(f"  ⚠ {name}: 未找到共享样式块")
            continue
        # 用规范块替换（含其前面可能已有的 import sys/Path）
        start = m.start()
        # 向上吃掉紧邻的 import sys / from pathlib import Path（避免重复）
        head = s[:start]
        while True:
            h2 = re.sub(r"(?:import sys\n|from pathlib import Path\n)\s*$", "", head)
            if h2 == head:
                break
            head = h2
        new = head + CANON + s[m.end():]
        if new == s:
            print(f"  · {name}: 已规范")
            continue
        if apply:
            try:
                ast.parse(new)
            except SyntaxError as e:
                print(f"  ❌ {name}: 语法错误（{e}）")
                continue
            io.open(p, "w", encoding="utf-8", newline="").write(new)
        print(f"  ✅ {name}")

    if apply:
        # 逐个 import 冒烟测试（不写图，只 import）
        import subprocess
        print("\n  === import 冒烟测试（--dry 或 import）===")
        for name in FILES:
            r = subprocess.run([sys.executable, "-c",
                                f"import sys; sys.path.insert(0,'tools'); "
                                f"import importlib.util as u; "
                                f"spec=u.spec_from_file_location('m','tools/{name}'); "
                                f"m=u.module_from_spec(spec); spec.loader.exec_module(m); "
                                f"print('OK')"],
                               capture_output=True, cwd=REPO, text=True)
            ok = "OK" in (r.stdout or "")
            first_err = next((l for l in (r.stderr or "").splitlines()
                              if l.strip().startswith(("NameError", "ImportError", "ModuleNotFoundError"))), "")
            print(f"    {name:<34} {'✅' if ok else '❌ ' + first_err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
