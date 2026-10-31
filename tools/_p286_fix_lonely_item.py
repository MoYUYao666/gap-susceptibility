# -*- coding: utf-8 -*-
r"""把误插的 `\item` 改为散文（修 "Lonely \item" 编译错误）（2026-10-12）。

`discussion.tex` 的 Limitations 小节是**散文**（First/Second/…），不是列表环境，
`_p285` 却插入了 `\item \textbf{...}` → **LaTeX Error: Lonely \item**。

    python tools\_p286_fix_lonely_item.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "discussion.tex"

ITEM = (r"\item \textbf{Our full-fine-tuning comparison is made at one shared learning rate, "
        r"not at each method's optimum.}")
PROSE = ("Tenth, our full-fine-tuning comparison is made at one shared learning rate rather "
         "than at each method's optimum.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(ITEM)
    print(f"  锚点命中 {n}")
    if n != 1:
        return 1
    t2 = t.replace(ITEM, PROSE, 1)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p286")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    ok = "Tenth, our full-fine-tuning comparison" in t3 and r"\item \textbf{Our" not in t3
    print(f"  {'✅ 已改为散文' if ok else '🔴 失败'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
