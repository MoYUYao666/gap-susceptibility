# -*- coding: utf-8 -*-
r"""全项目搜 A1 的关键词定义（2026-10-11）。

    python tools\_p187_find_keywords.py
"""
from __future__ import annotations

import glob
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    print("=== 搜 'keywords' / 'keyword' / 'sep'（不区分大小写）===")
    for f in sorted(glob.glob(str(REPO / "paper_a1" / "*.tex"))):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"keyword", t, re.I):
            seg = " ".join(t[max(0, m.start() - 60):m.start() + 260].split())
            print(f"  [{Path(f).name}] …{seg[:280]}…")
        if re.search(r"\\sep", t):
            for m in re.finditer(r"\\sep", t):
                seg = " ".join(t[max(0, m.start() - 200):m.start() + 200].split())
                print(f"  [{Path(f).name}] \\sep 上下文: …{seg[:300]}…")
    print()
    print("=== main.tex 的文档类与 frontmatter 附近 ===")
    t = io.open(REPO / "paper_a1" / "main.tex", encoding="utf-8",
                errors="replace").read()
    i = t.find("\\begin{abstract}")
    print("  abstract 前 400 字符:")
    print("   " + repr(t[max(0, i - 400):i]))
    j = t.find("\\end{abstract}")
    print("  abstract 后 400 字符:")
    print("   " + repr(t[j:j + 400]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
