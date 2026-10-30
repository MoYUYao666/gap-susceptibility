# -*- coding: utf-8 -*-
r"""打印 `supplement.tex` 的 COCO 表全文与引用位置（2026-10-07）。

用于判断该表是否违反操作者刚下的硬原则：
**"所有数据必须要可复现有来源"**。

已知：本地 `outputs/theory/coco/` 只有 **3 配置 × 3 seed = 9 run**，
而该表声称 **81 recorded runs（14 配置 × 5 seeds + 5 frozen + 5 full-FT）**。

    python tools\_diag_coco_table.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "supplement.tex"


def main() -> int:
    t = io.open(F, encoding="utf-8").read()
    lines = t.splitlines()
    print("=== 含 tab:coco_ode 的 table 环境（逐行）===")
    idx = next((i for i, l in enumerate(lines) if "tab:coco_ode" in l), None)
    if idx is None:
        print("  未找到 tab:coco_ode")
        return 1
    # 向上找 begin{table}，向下找 end{table}
    a = next((i for i in range(idx, -1, -1) if "\\begin{table}" in lines[i]), 0)
    b = next((i for i in range(idx, len(lines)) if "\\end{table}" in lines[i]), len(lines) - 1)
    for i in range(a, b + 1):
        print(f"  {i+1:>4}: {lines[i][:150]}")

    print("\n=== 该表在正文中被引用的位置 ===")
    for i, l in enumerate(lines, 1):
        if "tab:coco_ode" in l and "label" not in l and "caption" not in l:
            print(f"  {i:>4}: {l.strip()[:160]}")

    print("\n=== 表内 R² 值统计 ===")
    seg = "\n".join(lines[a:b + 1])
    r2s = re.findall(r"&\s*(\d\.\d{3})\s*&", seg)
    print(f"  检出 R² 值 {len(r2s)} 个: {r2s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
