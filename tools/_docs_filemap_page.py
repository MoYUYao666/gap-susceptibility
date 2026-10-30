# -*- coding: utf-8 -*-
r"""更新 `文件地图.md` 里 `paper合` 的页数（NC 54 → 55）（2026-10-10）。

**规则**：就地更新 + 标注日期，不静默覆盖。

    python tools\_docs_filemap_page.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FM = REPO / "文件地图.md"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(FM, encoding="utf-8", errors="replace").read()

    print("=== 文件地图里所有页数陈述 ===")
    pats = [r"\*\*39\*\*", r"\*\*40\*\*", r"\*\*49\*\*", r"\*\*54\*\*", r"\*\*55\*\*",
            r"页数", r"39（NC 版）", r"NC 版"]
    for p in pats:
        for m in re.finditer(p, t):
            s = " ".join(t[max(0, m.start() - 110):m.start() + 130].split())
            print(f"  [{p}] …{s}…")

    print("\n=== HANDOFF 里的页数陈述 ===")
    h = io.open(REPO / "HANDOFF.md", encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"(NC|Springer)[^\n]{0,40}\*\*(3\d|4\d|5\d)\*\*", h):
        s = " ".join(h[max(0, m.start() - 60):m.start() + 90].split())
        print(f"  …{s}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
