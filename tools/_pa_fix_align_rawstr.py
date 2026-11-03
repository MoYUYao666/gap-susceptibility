# -*- coding: utf-8 -*-
r"""补丁：用 **raw 字符串**修正 `_pa_align_ode_numbers.py` 里 4 处未命中的表体替换（2026-10-07）。

## 问题

表格行末是**字面两个反斜杠**（LaTeX 换行 `\\`），而我在普通字符串里写 `\\\n`，
Python 把 `\\` 解析成**一个**反斜杠 → 与文件不符 → 命中 0 次。

## 修法

把这 4 处改为 **raw 字符串**（`r"..."`），使 `\\` 保持两个反斜杠。

    python tools\_pa_fix_align_rawstr.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_pa_align_ode_numbers.py"

# 4 个待修的旧块（普通字符串版）→ 新块（raw 字符串版）
FIXES = [
    # phase2 text-only
    ("""     "$r=1$   & $-0.065$ & 0.170 & 0.988 \\\\\\n$r=2$   & $-0.035$ & 0.145 & 0.986 \\\\\\n$r=4$   & $-0.045$ & 0.178 & 0.987 \\\\\\n$r=8$   & $-0.041$ & 0.167 & 0.985 \\\\\\n$r=16$  & $-0.037$ & 0.140 & 0.979 \\\\\\n$r=32$  & $-0.039$ & 0.119 & 0.980 \\\\\\n$r=64$  & $-0.036$ & 0.148 & 0.985 \\\\",\n""",
     """     r"$r=1$   & $-0.065$ & 0.170 & 0.988 \\\\\n$r=2$   & $-0.035$ & 0.145 & 0.986 \\\\\n"
     r"$r=4$   & $-0.045$ & 0.178 & 0.987 \\\\\n$r=8$   & $-0.041$ & 0.167 & 0.985 \\\\\n"
     r"$r=16$  & $-0.037$ & 0.140 & 0.979 \\\\\n$r=32$  & $-0.039$ & 0.119 & 0.980 \\\\\n"
     r"$r=64$  & $-0.036$ & 0.148 & 0.985 \\\\",
"""),
]


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    print("  当前 REPE 块（含表体的那几处）逐行预览:")
    for i, ln in enumerate(t.splitlines(), 1):
        if "-0.065" in ln or "-0.039$ & 0.164" in ln or "PEFT mean" in ln or "0.985 \\\\pm 0.008" in ln:
            print(f"    {i:>4}: {ln[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
