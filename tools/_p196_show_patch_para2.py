# -*- coding: utf-8 -*-
r"""用正则定位 patch-size 归因段并打印全文（2026-10-11）。

    python tools\_p196_show_patch_para2.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"


def main() -> int:
    t = io.open(F, encoding="utf-8", errors="replace").read()
    pat = re.compile(r"a\s+property\s+not\s+of\s+vision-language", re.S)
    ms = list(pat.finditer(t))
    print(f"命中 {len(ms)}")
    for m in ms:
        # 段落边界：前后各找两个换行
        s = t.rfind("\n\n", 0, m.start())
        e = t.find("\n\n", m.end())
        para = t[s if s > 0 else 0:e if e > 0 else len(t)]
        print("=" * 80)
        print(repr(para))
        print()
        print("可读版:")
        print(" ".join(para.split()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
