# -*- coding: utf-8 -*-
r"""找 `tab:position`（"数据集翻转"表）的完整内容（2026-10-10）。

    python tools\_p142_show_tabposition.py
"""
from __future__ import annotations

import glob
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    for f in sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"\\label\{tab:position\}", t):
            s = t.rfind("\\begin{table}", 0, m.start())
            e = t.find("\\end{table}", m.end())
            print("=" * 72)
            print(f"{Path(f).name}  [{s}:{e}]")
            print("=" * 72)
            print(t[s:e + len("\\end{table}")])
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
