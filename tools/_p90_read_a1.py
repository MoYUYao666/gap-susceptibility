# -*- coding: utf-8 -*-
r"""读 A1（`paper_a1/main.tex`）的摘要与各节主张（2026-10-10）。

用途：诊断"significance 不足"卡在哪里，并看 `paper合` 的新证据能否支撑 A1。

    python tools\_p90_read_a1.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper_a1" / "main.tex"


def main() -> int:
    t = io.open(F, encoding="utf-8", errors="replace").read()
    print(f"=== {F.relative_to(REPO)} ｜ {len(t.splitlines())} 行 ===")

    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    if m:
        print("\n=== 摘要 ===")
        print(" ", " ".join(m.group(1).split())[:1600])
    else:
        print("\n（未找到 abstract 环境）")

    print("\n=== 各节标题 ===")
    for mm in re.finditer(r"\\section\*?\{([^}]*)\}", t):
        print("  •", mm.group(1)[:80])

    print("\n=== 各节首段（判断主张）===")
    secs = list(re.finditer(r"\\section\*?\{([^}]*)\}", t))
    for i, mm in enumerate(secs):
        end = secs[i + 1].start() if i + 1 < len(secs) else min(len(t), mm.end() + 2500)
        body = t[mm.end():end]
        # 去掉图表环境
        body = re.sub(r"\\begin\{(figure|table|tabular|longtable)\}.*?\\end\{\1\}", " ", body, flags=re.S)
        first = " ".join(body.split())[:420]
        print(f"\n  ── {mm.group(1)[:60]}")
        print(f"     {first}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
