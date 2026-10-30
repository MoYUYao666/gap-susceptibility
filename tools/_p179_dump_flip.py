# -*- coding: utf-8 -*-
r"""打印 validation.tex 里翻转段的真实字节（2026-10-11）。

    python tools\_p179_dump_flip.py
"""
from __future__ import annotations

import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "validation.tex"


def main() -> int:
    t = io.open(F, encoding="utf-8", errors="replace").read()
    i = t.find("depends on the evaluation corpus")
    if i < 0:
        i = t.find("-0.0288")
    if i < 0:
        print("(未找到)")
        return 1
    seg = t[max(0, i - 200):i + 900]
    print("=" * 78)
    print("repr（精确字节）")
    print("=" * 78)
    print(repr(seg))
    print()
    print("=" * 78)
    print("可读版")
    print("=" * 78)
    print(" ".join(seg.split()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
