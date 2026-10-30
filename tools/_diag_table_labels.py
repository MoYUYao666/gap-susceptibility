# -*- coding: utf-8 -*-
r"""定位 `\label{tab:*}` 比 `\begin{table}` 多出的那一个（2026-10-05）。

## 现象

`paper合/sections/*.tex` 中：`\begin{table}` = **7** 个，`\label{tab:*}` = **8** 个
→ **多出 1 个**。可能原因：① 重复 label（引用会静默指向错误对象）；② label 写在 table 环境之外；
③ `longtable` 等其他表环境。

    python tools\_diag_table_labels.py
"""
from __future__ import annotations

import io
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEC = REPO / "paper合" / "sections"


def main() -> int:
    print("=== ① 所有 tab: label 及其所在文件/行 ===")
    found: list[tuple[str, int, str]] = []
    for f in sorted(SEC.glob("*.tex")):
        for i, line in enumerate(io.open(f, encoding="utf-8", errors="ignore").read().splitlines(), 1):
            for m in re.finditer(r"\\label\{(tab:[^}]+)\}", line):
                found.append((f.name, i, m.group(1)))
    for fn, ln, lab in found:
        print(f"  {fn}:{ln}  {lab}")

    print("\n=== ② 重复检测 ===")
    c = Counter(lab for _, _, lab in found)
    dup = {k: v for k, v in c.items() if v > 1}
    print(f"  重复 label: {dup if dup else '无 ✅'}")

    print("\n=== ③ 各文件里的表环境（含 longtable / table*）===")
    for f in sorted(SEC.glob("*.tex")):
        s = io.open(f, encoding="utf-8", errors="ignore").read()
        envs = re.findall(r"\\begin\{(table\*?|longtable|tabular)\}", s)
        labs = re.findall(r"\\label\{(tab:[^}]+)\}", s)
        if envs or labs:
            print(f"  {f.name}: 环境 {dict(Counter(envs))} ｜ tab label {len(labs)} → {labs}")

    print("\n=== ④ 结论 ===")
    n_env = sum(len(re.findall(r"\\begin\{table\*?\}", io.open(f, encoding='utf-8', errors='ignore').read()))
                for f in SEC.glob("*.tex"))
    n_lab = len(found)
    print(f"  table 环境 {n_env} ｜ tab label {n_lab}")
    if dup:
        print("  ⚠ 存在重复 label —— 引用会静默指向错误对象")
    elif n_lab > n_env:
        print("  ⚠ label 多于环境：可能有 label 写在 table 之外，或表环境未闭合")
    else:
        print("  ✅ 数量一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
