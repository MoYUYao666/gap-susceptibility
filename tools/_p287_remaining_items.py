# -*- coding: utf-8 -*-
r"""列出剩余 PR 改稿项的确切文本（2026-10-12）。

    python tools\_p287_remaining_items.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
I = REPO / "paper合" / "sections" / "introduction.tex"
D = REPO / "paper合" / "sections" / "discussion.tex"
RW = REPO / "paper合" / "sections" / "related_work.tex"
C = REPO / "paper合" / "sections" / "conclusion.tex"
E = REPO / "paper合" / "sections" / "empirical.tex"


def show(p: Path, pat: str, label: str, n: int = 4, w: int = 320):
    print("=" * 96)
    print(f"{label}  [{p.name}]")
    print("=" * 96)
    if not p.exists():
        print("  ❌ 缺文件")
        return
    t = io.open(p, encoding="utf-8", errors="replace").read()
    c = 0
    for m in re.finditer(pat, t, re.I):
        c += 1
        if c > n:
            continue
        ln = t[:m.start()].count("\n") + 1
        s = " ".join(t[max(0, m.start() - 150):m.start() + w].split())
        print(f"  L{ln}: …{s[:440]}…\n")
    print(f"  共 {c} 处\n")


def main() -> int:
    show(D, r"pre-hoc|without training", "R2.5/discussion:56 pre-hoc 承诺")
    show(D, r"88 of 94|eightyeight|88", "归档缺口：88 of 94")
    show(C, r"five model architectures|383 experiments|117", "conclusion 计数")
    show(E, r"seven backbones|five dimensions|six", "empirical 计数")
    show(I, r"unified explanation for all", "introduction 概化")
    show(D, r"apply to any|as the default", "discussion 概化（已改则无）")
    show(RW, r"\\subsection\{Surveys and Broader Context\}", "related_work 插入点")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
