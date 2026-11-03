# -*- coding: utf-8 -*-
r"""核验回复信里两处"疑似问题"是否真问题（2026-10-13）。

    python tools\_p537_check_letter_flags.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LETTER = REPO / "docs" / "P3_RESPONSE_LETTER.md"


def main() -> int:
    t = io.open(LETTER, encoding="utf-8", errors="replace").read()
    print(f"  回复信 {len(t):,} 字符")
    print()
    print("=" * 92)
    print("① runs[90] 的实际写法与语境")
    print("=" * 92)
    for m in re.finditer(r"runs\s*\[\s*90\s*\]", t):
        seg = " ".join(t[max(0, m.start() - 260):m.start() + 120].split())
        print(f"  ✅ 命中：…{seg}…")
    n = len(re.findall(r"runs\s*\[\s*90\s*\]", t))
    print(f"  ⇒ 共 {n} 处")

    print()
    print("=" * 92)
    print("② 'reduces uncertainty by' 的实际语境（应为更正性否定）")
    print("=" * 92)
    hits = list(re.finditer(r"reduces? (?:allocation )?uncertainty", t, re.I))
    print(f"  命中 {len(hits)} 处")
    for m in hits:
        seg = " ".join(t[max(0, m.start() - 420):m.start() + 260].split())
        print(f"  …{seg}…")

    print()
    print("=" * 92)
    print("③ 判定")
    print("=" * 92)
    ok = True
    if n == 0:
        print("  🔴 runs[90] 真的不在信里")
        ok = False
    else:
        print("  ✅ runs[90] 在信里（先前检查的正则太字面）")
    if not hits:
        print("  ✅ 无 'reduces uncertainty'")
    else:
        # 判断是否为否定语境
        neg = all(any(k in " ".join(t[max(0, m.start() - 420):m.start() + 260].split()).lower()
                      for k in ("must not", "withdrawn", "do not", "no longer", "not read",
                                "cannot", "not support"))
                  for m in hits)
        print(f"  {'✅ 全部为否定/撤回语境（正确）' if neg else '🔴 有非否定用法'}")
        ok = ok and neg
    print()
    print(f"  **判定：{'✅ 两处均为误报，信是正确的' if ok else '🔴 需处理'}**")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
