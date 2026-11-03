# -*- coding: utf-8 -*-
r"""列出需限定的 Visual Fragility 句与过强概化句的确切文本（2026-10-12）。

    python tools\_p280_show_hedges.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

TARGETS = [
    ("paper合/sections/empirical.tex", r"consistent with|Visual Fragility"),
    ("paper合/sections/introduction.tex", r"inherently|spectral evidence"),
    ("paper合/sections/conclusion.tex", r"Visual Fragility"),
    ("paper合/sections/discussion.tex", r"apply to any|as the default"),
    ("paper合/sections/theory.tex", r"regardless of"),
    ("paper合/sections/validation.tex", r"regardless of|generalizes across"),
]


def main() -> int:
    for rel, pat in TARGETS:
        p = REPO / rel
        if not p.exists():
            print(f"  缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        print("=" * 100)
        print(rel)
        print("=" * 100)
        seen = 0
        for m in re.finditer(pat, t, re.I):
            seen += 1
            if seen > 6:
                continue
            ln = t[:m.start()].count("\n") + 1
            s = " ".join(t[max(0, m.start() - 260):m.start() + 300].split())
            print(f"  L{ln}: …{s[:520]}…\n")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
