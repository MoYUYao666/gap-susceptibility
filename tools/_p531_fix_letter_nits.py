# -*- coding: utf-8 -*-
r"""核验回复信的三处标记，并修正结尾的撤回条数（2026-10-13）。

    python tools\_p531_fix_letter_nits.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LETTER = REPO / "docs" / "P3_RESPONSE_LETTER.md"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(LETTER, encoding="utf-8", errors="replace").read()

    print("=" * 92)
    print("① runs[90] 的实际写法")
    print("=" * 92)
    for m in re.finditer(r"runs\[?9?0?\]?", t):
        seg = " ".join(t[max(0, m.start() - 90):m.start() + 60].split())
        print(f"  …{seg}…")

    print()
    print("=" * 92)
    print("② CLIP-derived 的出现语境（应为更正性否定）")
    print("=" * 92)
    for m in re.finditer(r"CLIP-derived", t):
        seg = " ".join(t[max(0, m.start() - 200):m.start() + 160].split())
        print(f"  …{seg}…")

    print()
    print("=" * 92)
    print("③ 结尾句")
    print("=" * 92)
    for m in re.finditer(r"[^\n]*of our claims did not survive[^\n]*", t):
        print(f"  {m.group(0)}")

    # 修正结尾：Three → Four
    old = "Three of our claims\ndid not survive them"
    new = "Four of our claims\ndid not survive them"
    print()
    if old in t:
        print(f"  ⇒ 找到待改句：{old!r}")
        if a.apply:
            io.open(LETTER, "w", encoding="utf-8", newline="").write(t.replace(old, new))
            t2 = io.open(LETTER, encoding="utf-8", errors="replace").read()
            print(f"  ✅ 已改为 Four of our claims：{'Four of our claims' in t2}")
        else:
            print("  （预演）")
    else:
        # 试单行形式
        m = re.search(r"Three of our claims", t)
        if m:
            print(f"  ⇒ 单行形式命中")
            if a.apply:
                io.open(LETTER, "w", encoding="utf-8", newline="").write(
                    t.replace("Three of our claims", "Four of our claims"))
                print("  ✅ 已改为 Four")
        else:
            print("  ⚠️ 未找到该句（可能措辞不同）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
