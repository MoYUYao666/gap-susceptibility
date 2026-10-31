# -*- coding: utf-8 -*-
r"""读 `tab:position_strict` 的表行，逐格提取 ΔCG 与 R@1（2026-10-12）。

    python tools\_p318_read_strict_rows.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    t = io.open(REPO / "paper合" / "sections" / "empirical.tex",
                encoding="utf-8", errors="replace").read()
    k = t.find("\\label{tab:position_strict}")
    i = t.rfind("\\begin{table}", 0, k)
    j = t.find("\\end{table}", k)
    body = t[i:j + 12]
    # 提取 tabular 内的行
    m = re.search(r"\\begin\{tabular\}\{[^}]*\}(.*?)\\end\{tabular\}", body, re.S)
    if not m:
        print("  🔴 找不到 tabular")
        return 1
    tab = m.group(1)
    print("=" * 100)
    print("表行（每行原样）")
    print("=" * 100)
    for line in tab.split("\\\\"):
        s = line.strip()
        if not s or s.startswith("\\toprule") or s.startswith("\\midrule") \
                or s.startswith("\\bottomrule") or s.startswith("\\cmidrule"):
            continue
        flat = re.sub(r"\s+", " ", s)
        print(f"  {flat[:190]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
