# -*- coding: utf-8 -*-
r"""改台账 `NEW_ROWS` 表为 5-seed 值（2026-10-11）。

## 归档现值（`recomputed_tables.json`）

| 骨干 | text_only | both | vision_only |
|---|---|---|---|
| CLIP B/32@r4 | $-0.030382$ | $-0.020375$ | $+0.016577$ |
| CLIP B/16@r4 | $-0.016574$ | $+0.012357$ | $+0.037551$ |

    python tools\_pa_ledger_newrows.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"

OLD = '''    NEW_ROWS = {
        "CLIP B/32@r4": ("outputs/strict_freeze_b32_r4",
                         {"text_only": (-0.0288, 0.621), "both": (-0.0188, 0.679),
                          "vision_only": (+0.0127, 0.670)}),
        "CLIP B/16@r4": ("outputs/strict_freeze_b16/r4",
                         {"text_only": (-0.0172, 0.651), "both": (+0.0107, 0.707),
                          "vision_only": (+0.0313, 0.686)}),
    }'''

NEW = '''    NEW_ROWS = {
        "CLIP B/32@r4": ("outputs/strict_freeze_b32_r4",
                         {"text_only": (-0.030382, 0.621), "both": (-0.020375, 0.679),
                          "vision_only": (+0.016577, 0.670)}),
        "CLIP B/16@r4": ("outputs/strict_freeze_b16/r4",
                         {"text_only": (-0.016574, 0.651), "both": (+0.012357, 0.707),
                          "vision_only": (+0.037551, 0.686)}),
    }'''

OLD_C = ("    # 表值为 **3-seed 均值**（2026-10-10 起；此前误用单 seed，见表注）")
NEW_C = ("    # 表值为 **5-seed 均值，batch 128**（2026-10-11 起；此前 3 seed，见表注）")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8").read()
    n1, n2 = t.count(OLD), t.count(OLD_C)
    print(f"=== 锚点：NEW_ROWS {n1} ｜ 注释 {n2} ===")
    if n1 != 1:
        return 1
    t = t.replace(OLD, NEW, 1)
    if n2 == 1:
        t = t.replace(OLD_C, NEW_C, 1)
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("  ✅ NEW_ROWS 已改为 5-seed 值")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
