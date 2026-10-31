# -*- coding: utf-8 -*-
r"""看论文里"数据集翻转"那段与相关表（2026-10-10）。

    python tools\_p141_find_flip_claim.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEC = REPO / "paper合" / "sections"


def main() -> int:
    for f in sorted(SEC.glob("*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        hits = []
        for pat in (r"flip", r"reverse[sd]?", r"COCO", r"dataset.{0,30}dependen"):
            for m in re.finditer(pat, t, re.I):
                s = " ".join(t[max(0, m.start() - 230):m.start() + 330].split())
                if "COCO" in s or "flip" in s.lower():
                    hits.append((pat, s))
        if hits:
            print(f"\n{'=' * 70}\n{f.name}\n{'=' * 70}")
            seen = set()
            for pat, s in hits:
                if s[:70] in seen:
                    continue
                seen.add(s[:70])
                print(f"  [{pat}] {s[:430]}")
                print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
