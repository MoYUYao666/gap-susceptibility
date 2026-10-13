# -*- coding: utf-8 -*-
r"""打印 `empirical.tex` 里含"patch size 归因"那段的全文（2026-10-11）。

    python tools\_p195_show_patch_para.py
"""
from __future__ import annotations

import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"


def main() -> int:
    t = io.open(F, encoding="utf-8", errors="replace").read()
    key = "a property not of vision-language adaptation in general"
    i = t.find(key)
    if i < 0:
        print("(未找到)")
        return 1
    s = t.rfind("\n\n", 0, i)
    e = t.find("\n\n", i)
    para = t[s:e]
    print("=" * 80)
    print(f"段落范围 {s}:{e}（{len(para)} 字符）")
    print("=" * 80)
    print(repr(para))
    print()
    print("=" * 80)
    print("可读版")
    print("=" * 80)
    print(" ".join(para.split()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
