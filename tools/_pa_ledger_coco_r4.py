# -*- coding: utf-8 -*-
r"""台账里的 COCO r4 text_only：$-0.0414$ → $-0.0430$（2026-10-11）。

依据：`outputs/coco_sweep_text_only/r4/text_only/seed*/results.json`（5 seed，batch 128）
mean $= -0.043013$。

    python tools\_pa_ledger_coco_r4.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"
OLD = '("COCO|text_only", -0.0414)'
NEW = '("COCO|text_only", -0.0430)'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8").read()
    n = t.count(OLD)
    print(f"=== 命中 {n} ===")
    if n != 1:
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
    print("  ✅ 已改")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
