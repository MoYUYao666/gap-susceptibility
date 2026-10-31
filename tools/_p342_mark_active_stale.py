# -*- coding: utf-8 -*-
r"""就地标注「活跃待办」里的 P1 过期表述（2026-10-12）。

## 判据

`HANDOFF.md` 的历史条目**记录的是当时观测，正确，不该删**。
但**当前状态表 / 活跃待办 / 决策分支**里的 P1 表述会误导 → 需**就地标注过期**。

目标（实测定位）：

| 文件 | 内容 | 处置 |
|---|---|---|
| `文件地图.md:731` | `⏳ 待决 \| 投稿时点：…与在审 P1 同源，建议等 P1 决定` | 标注过期 → 已决（P1 拒） |
| `文件地图.md:741` | `唯一未决变量：P1（…）的决定（2026-10-04，Required Reviews Completed）` | 标注过期 |
| `HANDOFF.md:7876` | `A1…与 P1…均在审` | 标注过期 |

    python tools\_p342_mark_active_stale.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

MARK = " ⚠️**2026-10-12 已过期**：P1 已被 Pattern Recognition 拒稿，该待决项已终结。"

FIXES = [
    ("文件地图.md",
     r"| ⏳ 待决 | **投稿时点**：实证部分与在审 P1（`PR-D-26-10149`）同源，**建议等 P1 决定** |",
     r"| ⏳ 待决 | **投稿时点**：实证部分与在审 P1（`PR-D-26-10149`）同源，**建议等 P1 决定** |"
     + MARK),
    ("文件地图.md",
     r"**唯一未决变量：P1（`PR-D-26-10149`）的决定**（2026-10-04 状态日期，Required Reviews Completed）。",
     r"**唯一未决变量：P1（`PR-D-26-10149`）的决定**（2026-10-04 状态日期，Required Reviews Completed）。"
     + MARK),
    ("HANDOFF.md",
     r"⚠️ **审稿相关风险（只陈述事实，不下结论）**：A1（`NEUCOM-D-26-20952`）与 P1（`PR-D-26-10149`）**均在审**，",
     r"⚠️ **审稿相关风险（只陈述事实，不下结论）**：A1（`NEUCOM-D-26-20952`）与 P1（`PR-D-26-10149`）**均在审**，"
     + MARK + "（**A1 亦已于 2026-10-10 桌面拒稿**）"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for rel, old, new in FIXES:
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(old)
        already = MARK.strip() in t and old + MARK in t
        print(f"  {rel}: 命中 {n} ｜ 已标注 {already}")
        if n == 0 or not a.apply or already:
            continue
        t2 = t.replace(old, new)
        io.open(p, "w", encoding="utf-8", newline="").write(t2)
        total += n
    if not a.apply:
        print("  （预演）")
        return 0
    print(f"\n  → 就地标注 {total} 处")
    for rel in ("文件地图.md", "HANDOFF.md"):
        t = io.open(REPO / rel, encoding="utf-8", errors="replace").read()
        print(f"  {rel}: 过期标注共 {t.count(MARK.strip())} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
