# -*- coding: utf-8 -*-
r"""核实 A1 的关键词（Neural Networks 限 1–6）（2026-10-11）。

    python tools\_p186_a1_keywords.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"


def main() -> int:
    t = io.open(F, encoding="utf-8", errors="replace").read()
    print("=== 搜 \\keywords ===")
    for m in re.finditer(r"\\keywords", t):
        print("  @" + str(m.start()) + ": " + repr(t[m.start():m.start() + 320]))
    print()
    m = re.search(r"\\keywords\{(.*?)\}", t, re.S)
    if m:
        kw = m.group(1)
        n = kw.count(r"\sep") + 1
        print(f"=== 关键词（{n} 个）===")
        for i, k in enumerate(kw.split(r"\sep"), 1):
            print(f"  {i}. {k.strip()}")
        print(f"\n  个数 = {n} → {'✅ 在 1–6 内' if 1 <= n <= 6 else '🔴 超限'}")
    else:
        print("  ❌ 未找到 \\keywords{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
