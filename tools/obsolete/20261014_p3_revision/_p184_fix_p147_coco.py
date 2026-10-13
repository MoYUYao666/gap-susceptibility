# -*- coding: utf-8 -*-
r"""修 `_p147` 的 COCO 取数：**只用新目录，不与旧 sweep 合并**（2026-10-11）。

## 症状

`_p147` 的 COCO 取数写了两个 glob：
```python
"outputs/coco_sweep_text_only/r4/text_only/seed*/results.json",   # 新跑 5 个
"outputs/coco_sweep/r4/text_only/seed*/results.json"              # 旧 3 个
```
→ **n=8，均值 $-0.0424$**，而**新跑单独是 $-0.0430$**。

## 为什么必须改

论文的其它秩（r2/r8/r32/r64）**全部用新跑**。r4 若混入旧 sweep，就**与其它秩口径不一致**。

## 改动

COCO 取数只保留 `coco_sweep_text_only/**`。

    python tools\_p184_fix_p147_coco.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p147_flip_corrected.py"

OLD = '''    COCO = {"text_only": ["outputs/coco_sweep_text_only/r4/text_only/seed*/results.json",
                          "outputs/coco_sweep/r4/text_only/seed*/results.json"],
            "both": ["outputs/coco_sweep/r4/both/seed*/results.json"]}'''
NEW = '''    # **只取新跑**（batch 128，5 seed）——与论文其它秩（r2/r8/r32/r64）同口径
    COCO = {"text_only": ["outputs/coco_sweep_text_only/r4/text_only/seed*/results.json"],
            "both": ["outputs/coco_sweep/r4/both/seed*/results.json"]}'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"=== 锚点命中 {n} ===")
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
    print("  ✅ 已改为只取新跑")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
