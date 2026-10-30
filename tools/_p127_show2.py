# -*- coding: utf-8 -*-
r"""看那 2 条无作者条目在文件里的实际样子（2026-10-10）。

    python tools\_p127_show2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper_a1" / "main.tex"


def main() -> int:
    t = io.open(MAIN, encoding="utf-8", errors="replace").read()
    print("=== 搜 'imod' / 'hu2022lora' 出现处 ===")
    for k in ("imod", "hu2022lora"):
        print(f"\n── {k}")
        for m in re.finditer(k, t):
            s = t[max(0, m.start() - 90):m.start() + 170]
            print(f"   @{m.start()}: {repr(s[:250])}")
        if k not in t:
            print("   ❌ 文件中**完全没有**这个 key")

    print("\n=== 书目块尾部 30 行 ===")
    i = t.find("\\begin{thebibliography}")
    j = t.find("\\end{thebibliography}")
    if i > 0 and j > i:
        lines = t[i:j].splitlines()
        print(f"  块共 {len(lines)} 行")
        for ln in lines[-18:]:
            print("   " + ln.strip()[:150])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
