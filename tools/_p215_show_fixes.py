# -*- coding: utf-8 -*-
r"""列出需修正的 5 处硬伤原文（2026-10-12）。

| # | 硬伤 | 位置 |
|---|---|---|
| 1 | 摘要首句 "Only the second governs" 与 Table 1 冲突 | `main.tex:33` |
| 2 | "zero-overhead monitor" 未被实现 | `main.tex:308`、标题、`highlights.tex:16` |
| 3 | `highlights.tex` r=1.000 未加限定 | `highlights.tex:14` |
| 4 | "matches to four decimals"（实际三位） | `main.tex` 附近 |
| 5 | 检索"跟随 gap"与自家数据冲突 | `main.tex` 附近 |

    python tools\_p215_show_fixes.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"


def main() -> int:
    t = io.open(A1 / "main.tex", encoding="utf-8", errors="replace").read()
    lines = t.splitlines()

    print("=" * 88)
    print("① 摘要（main.tex L30-40）")
    print("=" * 88)
    for i in range(29, min(41, len(lines))):
        print(f"  {i + 1:4} {lines[i][:104]}")

    print()
    print("=" * 88)
    print("② 'zero-overhead' / 'monitor' 出现处")
    print("=" * 88)
    for i, ln in enumerate(lines, 1):
        if re.search(r"zero-overhead|overhead|monitor", ln, re.I):
            print(f"  {i:4} {ln.strip()[:104]}")

    print()
    print("=" * 88)
    print("③ 'four decimals' / '1.000'")
    print("=" * 88)
    for i, ln in enumerate(lines, 1):
        if re.search(r"four decimals|r\s*=\s*1\.000|r\{=\}1\.000", ln, re.I):
            print(f"  {i:4} {ln.strip()[:104]}")

    print()
    print("=" * 88)
    print("④ 'retrieval' 跟随 gap 的表述")
    print("=" * 88)
    for i, ln in enumerate(lines, 1):
        if re.search(r"retrieval.{0,60}(gap|respond)|R@1.{0,40}gap|gap.{0,40}R@1", ln, re.I):
            print(f"  {i:4} {ln.strip()[:104]}")

    print()
    print("=" * 88)
    print("⑤ highlights.tex 全文")
    print("=" * 88)
    h = io.open(A1 / "highlights.tex", encoding="utf-8", errors="replace").read()
    for i, ln in enumerate(h.splitlines(), 1):
        print(f"  {i:3} {ln[:104]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
