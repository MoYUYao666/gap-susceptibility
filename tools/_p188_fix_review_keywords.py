# -*- coding: utf-8 -*-
r"""修 `_final_review.py` 的关键词检查（支持 `keyword` 环境）（2026-10-11）。

## 我上一版的错

只找了 `\keywords{...}`，而 A1 用的是 `\begin{keyword}...\end{keyword}`（elsarticle 风格）
→ 误报"关键词 0 个"。

    python tools\_p188_fix_review_keywords.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_final_review.py"

OLD = '    m = re.search(r"\\\\keywords\\{(.*?)\\}", t, re.S)\n    nkw = m.group(1).count("\\\\sep") + 1 if m else 0'
NEW = ('    m = re.search(r"\\\\keywords\\{(.*?)\\}", t, re.S)\n'
       '    if not m:\n'
       '        m = re.search(r"\\\\begin\\{keyword\\}(.*?)\\\\end\\{keyword\\}", t, re.S)\n'
       '    nkw = m.group(1).count("\\\\sep") + 1 if m else 0')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"=== 锚点命中 {n} ===")
    if n != 1:
        # 退一步：打印含 keywords 的行
        for i, ln in enumerate(t.splitlines(), 1):
            if "keywords" in ln or "sep" in ln:
                print(f"  L{i}: {ln.rstrip()[:110]}")
        return 1
    t2 = t.replace(OLD, NEW, 1)
    try:
        ast.parse(t2)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    print("  ✅ 已修（支持 keyword 环境）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
