# -*- coding: utf-8 -*-
r"""修 `abstract.tex` 的旧标题（含 `\\` 换行，故精确匹配抓不到）（2026-10-10）。

    python tools\_p137_fix_abstract.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "abstract.tex"
NEW = ("Order Preservation as a Zero-Overhead Monitor for Classification Fine-Tuning: "
       "Why the Modality Gap Is Not a Universal Health Metric")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()

    m = re.search(r"\\title\{(.*?)\}\s*\n", t, re.S)
    print("=== 现 title ===")
    print(" ", repr(m.group(1)) if m else "(未找到)")

    # 用正则吃掉内部可能存在的 \\ 与换行
    pat = re.compile(r"\\title\{(?:The Modality Gap Is Not a Universal Health Metric|"
                     r"Order Preservation as a Zero-Overhead Monitor).*?\}\s*\n", re.S)
    m2 = pat.search(t)
    if not m2:
        print("  ❌ 未匹配到 title 块")
        return 1
    new_block = "\\title{" + NEW + "}\n"
    t2 = t[:m2.start()] + new_block + t[m2.end():]

    print("\n=== 改后 title ===")
    m3 = re.search(r"\\title\{(.*?)\}\s*\n", t2, re.S)
    print(" ", repr(m3.group(1)) if m3 else "(?)")

    if not a.apply:
        print("\n  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_nc")
    if not bak.exists():
        bak.write_text(t, encoding="utf-8")
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    assert "Universal Health Metric:\\" not in t3, "旧标题仍在"
    assert "Zero-Overhead Monitor" in t3
    print("\n  ✅ 已修；旧标题 0 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
