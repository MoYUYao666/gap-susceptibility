# -*- coding: utf-8 -*-
r"""提取 P3 理论的关键段落（AX1–AX5 / bisection 论证 / Corollary 2），供修理论用（2026-10-12）。

    python tools\_p415_dump_p3_theory.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TH = REPO / "paper3" / "paper_ieee" / "sections" / "theory.tex"
AP = REPO / "paper3" / "paper_ieee" / "sections" / "appendix.tex"


def show(t: str, pat: str, label: str, before=200, after=2200):
    i = t.find(pat)
    print("=" * 100)
    print(f"{label}  ← 关键词 {pat!r}")
    print("=" * 100)
    if i < 0:
        print("  🔴 未找到")
        return
    print(t[max(0, i - before):i + after])
    print()


def main() -> int:
    th = io.open(TH, encoding="utf-8", errors="replace").read()
    ap = io.open(AP, encoding="utf-8", errors="replace").read()

    # AX 定义
    print("=" * 100)
    print("theory.tex 里的 AX1–AX5（所有出现）")
    print("=" * 100)
    for m in re.finditer(r"AX\d[^)]{0,10}\)", th):
        ln = th[:m.start()].count("\n") + 1
        seg = " ".join(th[max(0, m.start() - 260):m.start() + 300].split())
        print(f"  L{ln}: …{seg[:460]}…")
        print()

    show(th, "Representation Theorem", "Representation Theorem 段", 100, 2600)
    show(th, "Optimal Allocation", "Corollary 2（最优分配）", 100, 2000)
    show(ap, "AX3", "appendix 里对 AX3 的引用", 300, 1200)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
