# -*- coding: utf-8 -*-
r"""修 `_p222` 的锚点重叠（#4 吞掉 #5）（2026-10-12）。

## 问题

- 锚点 #4 = `"Only the second governs zero-shot accuracy, and it is free to monitor: "`
- 锚点 #5 = `"it is free to monitor: the Kendall ..."`  ← **与 #4 尾部重叠**

#4 替换后，`"it is free to monitor: "` 已不存在 → #5 无法命中。
**修法**：删掉 #5，把 #4 的替换文本改长，一次把两句都改掉。

    python tools\_p224_fix_overlap.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p222_a1_writing_fixes.py"

OLD_4 = '''GOVERNS_OLD = ("Only the second governs zero-shot accuracy, and it is free to monitor: ")
GOVERNS_NEW = ("Only the second tracks zero-shot accuracy, and it is free to compute: ")'''
NEW_4 = '''GOVERNS_OLD = ("Only the second governs zero-shot accuracy, and it is free to monitor: "
              "the Kendall order-preservation coefficient $\\\\tau$ follows from the top-$k$ "
              "class sets a validation pass already produces.")
GOVERNS_NEW = ("Only the second tracks zero-shot accuracy, and it is free to compute: "
              "the Kendall order-preservation coefficient $\\\\tau$ co-moves with it inside a "
              "single training trajectory (mean Pearson $0.90$ over ten runs, $10/10$ positive) "
              "and follows from the top-$k$ class sets a validation pass already produces.")'''

OLD_LIST = '''        (GOVERNS_OLD, GOVERNS_NEW),
        (LEGACY_OLD, LEGACY_NEW),'''
NEW_LIST = '''        (GOVERNS_OLD, GOVERNS_NEW),'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n1, n2 = t.count(OLD_4), t.count(OLD_LIST)
    print(f"  === 锚点：GOVERNS 块 {n1} ｜ 调用列表 {n2} ===")
    if n1 != 1 or n2 != 1:
        return 1
    t = t.replace(OLD_4, NEW_4, 1).replace(OLD_LIST, NEW_LIST, 1)
    # 删掉不再使用的 LEGACY_* 定义（避免误用）
    t = t.replace('''LEGACY_OLD = ("it is free to monitor: the Kendall order-preservation coefficient $\\\\tau$ "
              "follows from the top-$k$ class sets a validation pass already produces.")
LEGACY_NEW = ("the Kendall order-preservation coefficient $\\\\tau$ tracks it closely within a "
              "training trajectory (mean Pearson $0.90$ over ten runs) and follows from the "
              "top-$k$ class sets a validation pass already produces.")

''', "")
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("  ✅ 已合并锚点 4/5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
