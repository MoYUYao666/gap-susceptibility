# -*- coding: utf-8 -*-
r"""修 `_p14_coco_sweep_driver.py` 的变量作用域 bug（2026-10-07）。

## Bug

原写法：

```python
for ln in (r.stdout or "").splitlines()[-3:] if 'r' in dir() else []:
```

**两个错误**：
1. `'r' in dir()` **恒为真**（模块层 `import re` 引入了名字 `r`）→ 守卫无效；
2. `r` 在 `try` 内定义，**若 `subprocess` 超时则未定义** → `NameError`。

**→ 超时分支一旦触发就会崩，正好在最需要日志的时候。**

## 修法

把 `r` 改名为 `pr`（避免与 `re` 混淆），并在 `try` 前**显式初始化**
`ok_this` 与 `out_lines`，取代不可靠的 `dir()` 守卫。

    python tools\_p14_fix_scope.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p14_coco_sweep_driver.py"

OLD = """        log(f"▶ {site} r={rk}")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=4 * 3600, cwd=str(REPO))
            if r.returncode == 0:
                ok += 1
                log(f"   ✅ rc=0")
            else:
                fail += 1
                err = next((l for l in (r.stderr or "").splitlines() if "Error" in l), "")
                log(f"   ❌ rc={r.returncode} {err[:140]}")
        except subprocess.TimeoutExpired:
            fail += 1
            log("   ⚠ 超时（4 h）")"""

NEW = """        log(f"▶ {site} r={rk}")
        ok_this, out_lines = False, []
        try:
            pr = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=4 * 3600, cwd=str(REPO))
            out_lines = (pr.stdout or "").splitlines()
            if pr.returncode == 0:
                ok += 1
                ok_this = True
            else:
                fail += 1
                err = next((l for l in (pr.stderr or "").splitlines() if "Error" in l), "")
                out_lines = [(err or ("rc=%d" % pr.returncode))[:150]]
        except subprocess.TimeoutExpired:
            fail += 1
            out_lines = ["超时（4 h）"]"""

TAIL_OLD = """        log(f"   {'✅ rc=0' if ok_this else '❌ 失败'}")
        for ln in out_lines[-3:]:
            log("   | " + ln[:150])"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "ok_this, out_lines = False, []" in t and "pr = subprocess.run" in t:
        print("  已修，跳过")
        return 0
    c = t.count(OLD)
    print(f"  命中 {c} 次")
    if c != 1:
        print("  实际片段:")
        i = t.find('log(f"▶ {site}')
        print(repr(t[i:i + 700]))
        return 1
    if not apply:
        print("  （预演）")
        return 0
    new = t.replace(OLD, NEW, 1)
    ast.parse(new)
    io.open(F, "w", encoding="utf-8", newline="").write(new)
    t2 = io.open(F, encoding="utf-8").read()
    assert "ok_this, out_lines = False, []" in t2 and "pr = subprocess.run" in t2
    assert "dir()" not in t2, "旧的 dir() 守卫仍在"
    print("  ✅ 已修并断言通过（超时分支不再 NameError）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
