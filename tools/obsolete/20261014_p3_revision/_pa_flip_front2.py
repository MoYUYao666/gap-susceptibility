# -*- coding: utf-8 -*-
r"""用正则改翻转段的 3-seed 数字（容忍换行）（2026-10-11）。

    python tools\_pa_flip_front2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "validation.tex"

# 容忍任意空白（含换行）
PAT = re.compile(
    r"text-only holds the gap at \$-0\.0288\\pm0\.0013\$ on Flickr30k against "
    r"\$-0\.0188\\pm0\.0004\$ for the\s+both-position arm")
REP = (r"text-only holds the gap at $-0.0304\pm0.0039$ on Flickr30k against "
       r"$-0.0204\pm0.0028$ for the both-position arm")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    ms = list(PAT.finditer(t))
    print(f"=== 正则命中 {len(ms)} ===")
    if len(ms) != 1:
        for m in ms:
            print("   " + repr(t[max(0, m.start() - 60):m.end() + 60]))
        return 1
    t2 = PAT.sub(REP, t, count=1)
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    for k in (r"$-0.0304\pm0.0039$", r"$-0.0204\pm0.0028$"):
        assert k in t3, f"断言失败：缺 {k}"
    assert "-0.0288" not in t3 and "-0.0188" not in t3, "旧数字仍在"
    print("  ✅ 已更新为 5-seed（batch 128）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
