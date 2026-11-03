# -*- coding: utf-8 -*-
r"""更新台账：`tab:position_strict` 的 r4 两行改为 **3-seed 均值**（2026-10-10）。

## 为什么门禁原先失败

我先前的台账把 r4 行的"稿件值"写成**某个单 seed 的值**，
而表里（现在）是**3-seed 均值** → 逐条断言失败。

**修法**：台账改为对**同一目录下全部 seed 的均值**做断言（`--tags` 对应的全目录）。

    python tools\_pa_ledger_3seed.py [--apply]
"""
from __future__ import annotations

import ast
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"

# 表里现在的 3-seed 均值（`tools/_pa_table_3seed.py` 算出）
NEW_VALUES = {
    ("b32", "text_only"): (-0.0288, 0.621),
    ("b32", "both"): (-0.0188, 0.679),
    ("b32", "vision_only"): (0.0127, 0.670),
    ("b16", "text_only"): (-0.0172, 0.651),
    ("b16", "both"): (0.0107, 0.707),
    ("b16", "vision_only"): (0.0313, 0.686),
}


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "3-seed 均值" in t and "mean_over_seeds" in t:
        print("  已改，跳过")
        return 0

    # 找 r4 相关的 claim 调用（稿件值 + 路径），替换为 means 版本
    pat = re.compile(
        r'claim\(\s*"(CLIP B/(?:32|16)@r4 [^"]*)",\s*([-\d.]+),\s*'
        r'_one\(REPO / "([^"]+)",\s*"([a-z_]+)",\s*"([a-z0-9_]+)",\s*"([a-z_]+)"\),\s*'
        r'"([^"]*)",\s*tol=([\d.]+)\)')
    hits = pat.findall(t)
    print(f"  找到 r4 claim 调用: {len(hits)} 条")

    if not hits:
        # 打印实际形态，便于手工对齐
        for m in re.finditer(r'claim\("[^"]*r4[^"]*".*?\)\n', t, re.S):
            print("   ", ' '.join(m.group(0).split())[:150])
        print("  ⚠️ 自动替换失败——请按上方实际形态手工改")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
