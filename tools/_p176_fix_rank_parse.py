# -*- coding: utf-8 -*-
r"""修 `_p175` 的 rank 解析（2026-10-11）。

## bug

`strict_freeze_b32_r4` 的目录结构是 `outputs/strict_freeze_b32_r4/{arm}/seedN/`
—— **rank 写在组名里，没有 `r4/` 子目录**。
而 `strict_freeze_b16/r4` 与 `strict_freeze_oclip/r4` 是 `.../r4/{arm}/seedN/`。

我的 `load()` 只从路径找 `rN` 段 → **b32 的 rank 解析为空** → 整组读不到。

## 修法

rank 解析时若路径无 `rN` 段，**从组名里找 `_rN`**（如 `strict_freeze_b32_r4` → `r4`）。

    python tools\_p176_fix_rank_parse.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p175_recompute_all.py"

OLD = '''        rank = next((x for x in p if x and x[0] == "r" and x[1:].isdigit()), "?")'''
NEW = '''        rank = next((x for x in p if x and x[0] == "r" and x[1:].isdigit()), None)
        if rank is None:
            # 组名里带 rank 的形式（如 strict_freeze_b32_r4 → r4）
            import re as _re
            m = None
            for seg in p:
                m = _re.search(r"_r(\\d+)$", seg)
                if m:
                    rank = "r" + m.group(1)
                    break
            if rank is None:
                rank = "r4"      # 该组只有 r4 一种配置'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"=== 锚点命中 {n} ===")
    if n != 1:
        return 1
    t = t.replace(OLD, NEW, 1)
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("  ✅ 已修 rank 解析（回退到组名）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
