# -*- coding: utf-8 -*-
r"""读 A1 的标题与摘要原文（精确，用于改写）（2026-10-10）。

    python tools\_p95_a1_read_title_abstract.py
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
    print("=== \\title ===")
    m = re.search(r"\\title\{(.*?)\}\s*\n", t, re.S)
    print(repr(m.group(1)) if m else "(未找到)")

    print("\n=== abstract 环境 ===")
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if not m:
        # 可能是 \abstract{...}
        m2 = re.search(r"\\(begin\{abstract\}|abstract)\b(.*?)(\\end\{abstract\}|\n\\)", t, re.S)
        print(repr(m2.group(0)[:2000]) if m2 else "(未找到 abstract)")
        return 0
    body = m.group(1)
    print(f"（{len(body)} 字符，{len(body.split())} 词）")
    print(repr(body[:2400]))
    print("\n=== 纯文本预览 ===")
    plain = " ".join(re.sub(r"\\[a-zA-Z]+\{[^}]*\}", " ", body).split())
    print(" ", plain[:1400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
