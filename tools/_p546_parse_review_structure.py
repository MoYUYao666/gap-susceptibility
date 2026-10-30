# -*- coding: utf-8 -*-
r"""解析三个审稿人的**原始结构**（Summary / Strengths / Weaknesses 编号），
以便按 EM 的「每审稿人一个回复框」组织回复（2026-10-13）。

    python tools\_p546_parse_review_structure.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "docs" / "_inbox" / "P3_reviews" / "_reviews.txt"


def main() -> int:
    t = io.open(SRC, encoding="utf-8", errors="replace").read()
    print(f"  源 {len(t):,} 字符")
    # 找每个 Reviewer 段
    marks = [(m.start(), m.group(1)) for m in re.finditer(r"^Reviewer (\d)\s*$", t, re.M)]
    print(f"  找到审稿人标记 {len(marks)} 个：{[(m[1], m[0]) for m in marks]}")
    print()
    for k, (pos, num) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(t)
        seg = t[pos:end]
        print("=" * 96)
        print(f"Reviewer {num}（{len(seg):,} 字符）")
        print("=" * 96)
        # 小节标题
        for m in re.finditer(r"^(Summary|Strengths|Weaknesses|Comments|General|Minor|Major)\s*$",
                             seg, re.M | re.I):
            print(f"    小节: {m.group(1)}")
        # 编号点
        pts = re.findall(r"^(\d+)\.\s*(.{0,90})", seg, re.M)
        print(f"    编号点 {len(pts)} 个：")
        for n, txt in pts:
            print(f"      {n}. {' '.join(txt.split())[:86]}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
