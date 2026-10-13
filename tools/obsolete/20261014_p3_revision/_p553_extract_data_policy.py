# -*- coding: utf-8 -*-
r"""提取 PRL Guide 的「Research data / Data statement / Data linking」正文要求（2026-10-13）。

    python tools\_p553_extract_data_policy.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GUIDE = REPO / "docs" / "guides" / "_prl_guide.txt"


def main() -> int:
    g = io.open(GUIDE, encoding="utf-8", errors="replace").read()
    print(f"  Guide {len(g):,} 字符")
    print()
    # 找正文小节的第二次出现（第一次是目录）
    for title in ("Research data", "Data statement", "Data linking",
                  "Co-submission of related data, methods or protocols"):
        pos = [m.start() for m in re.finditer(re.escape(title), g)]
        print("=" * 96)
        print(f"【{title}】出现 {len(pos)} 次")
        print("=" * 96)
        if len(pos) >= 1:
            # 取最后一次（正文在目录之后）
            p = pos[-1]
            seg = g[p:p + 1900]
            # 截到下一个明显的小节标题
            for stop in ("\nVideo\n", "\nArticle structure\n", "\nReferences\n",
                         "\nSubmission checklist\n", "\nTables\n"):
                k = seg.find(stop, 60)
                if k > 0:
                    seg = seg[:k]
            print("\n".join("  " + l for l in seg.splitlines() if l.strip())[:2400])
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
