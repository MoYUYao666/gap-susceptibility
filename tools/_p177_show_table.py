# -*- coding: utf-8 -*-
r"""显示 `tab:position_strict` 的表体与表注（2026-10-11）。

    python tools\_p177_show_table.py
"""
from __future__ import annotations

import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EMP = REPO / "paper合" / "sections" / "empirical.tex"


def main() -> int:
    t = io.open(EMP, encoding="utf-8", errors="replace").read()
    i = t.find("\\label{tab:position_strict}")
    s = t.rfind("\\begin{table}", 0, i)
    e = t.find("\\end{table}", i)
    block = t[s:e + len("\\end{table}")]
    print("=" * 80)
    print(f"tab:position_strict ｜ 字符 {s}:{e}")
    print("=" * 80)
    for ln in block.splitlines():
        if ln.strip():
            print("  " + ln.rstrip()[:120])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
