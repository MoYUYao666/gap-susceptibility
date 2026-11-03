# -*- coding: utf-8 -*-
r"""核对 A1 标题的现状（2026-10-10）。

    python tools\_p98_a1_title_check.py [--fix]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"


def main() -> int:
    t = io.open(F, encoding="utf-8", errors="replace").read()
    i = t.find("\\title")
    seg = t[i:i + 300]
    print("=== \\title 段原文（repr 前 260）===")
    print(repr(seg[:260]))

    m = re.search(r"\\title\{(.{0,240}?)\}", seg, re.S)
    if m:
        raw = m.group(1)
        has_break = "\\\\" in raw
        print("\n=== 解析 ===")
        print("  含手动换行: ", has_break)
        print("  纯文本: ", " ".join(raw.replace("\\\\", " ").split()))
        if has_break and "--fix" in sys.argv:
            new = raw.replace("\\\\", " ")
            t2 = t.replace("\\title{" + raw + "}", "\\title{" + new + "}", 1)
            io.open(F, "w", encoding="utf-8", newline="").write(t2)
            print("  ✅ 已去掉手动换行")
    else:
        print("  ⚠️ 未解析出 title 内容")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
