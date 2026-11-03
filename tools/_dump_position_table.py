# -*- coding: utf-8 -*-
r"""打印 `tab:position_strict` 表格环境全文，供精确改写（2026-10-08）。

    python tools\_dump_position_table.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"


def main() -> int:
    t = io.open(F, encoding="utf-8").read()
    lines = t.splitlines()
    print(f"  文件 {F.name} ｜ {len(lines)} 行 ｜ 换行符 CRLF={'\\r\\n' in t}")
    # 找 label 所在行 → 向上找 begin{table}，向下找 end{table}
    lab = next((i for i, l in enumerate(lines) if "\\label{tab:position_strict}" in l), None)
    if lab is None:
        print("  ❌ 未找到 label")
        return 1
    a = next((i for i in range(lab, -1, -1) if "\\begin{table}" in lines[i]), 0)
    b = next((i for i in range(lab, len(lines)) if "\\end{table}" in lines[i]), len(lines) - 1)
    print(f"  表格 L{a+1}–L{b+1}")
    print("  " + "─" * 74)
    for i in range(a, b + 1):
        print(f"  {i+1:>4}| {lines[i]}")

    # 打印正文里引用该表的段落（前后各一段）
    print("\n  === 引用该表的正文段 ===")
    for i, l in enumerate(lines):
        if "ref{tab:position_strict}" in l:
            print(f"  L{i+1}: {l.strip()[:400]}")

    # 打印含 patch-16 结论的那句（完整）
    print("\n  === 含规律结论的完整句子 ===")
    for m in re.finditer(r"[^.]*(?:every patch-1?6|patch-16 backbone|Patch size)[^.]*\.", t):
        s = " ".join(m.group(0).split())
        if len(s) > 30:
            print(f"  • {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
