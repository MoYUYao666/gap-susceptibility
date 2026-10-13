# -*- coding: utf-8 -*-
r"""改 `main_10pp.tex` 与 `title_page_prl.tex` 的院系（2026-10-13）。

## 处置

| 文件 | 改？ | 理由 |
|---|---|---|
| `sections/*`、`main.tex`、`main_full.tex`、`supplementary.tex` | ✅ 已改（`_p554`） | 投稿件与补充材料 |
| **`main_10pp.tex`** | ✅ 改 | 我冻结的 10 页副本（应与 `main.tex` 一致） |
| **`title_page_prl.tex`** | ✅ 改 | **标题页**（Guide 要求 title page 含作者信息） |
| `PRL_submission/latex_source/main.tex` | ⚠️ 待定 | 旧的 `PRL_submission/` 打包目录（2026-09-26 投稿时的源） |
| `SUBMISSION/P3_PRL/latex_source/main.tex` | ❌ **不改** | **已投出**的首次投稿版 —— 历史存档 |
| `SUBMISSION/P3_PRL_revision/manuscript/latex_source/*` | ✅ 改 | 修订包内的源（重新生成时会同步） |

    python tools\_p555_drop_department_rest.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [
    REPO / "paper3" / "paper_ieee" / "main_10pp.tex",
    REPO / "paper3" / "paper_ieee" / "title_page_prl.tex",
]
OLD = "School of Electronics and Computer Science\\\\\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    todo = []
    for p in FILES:
        if not p.exists():
            print(f"  ⚠️ 缺 {p.name}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(OLD)
        print(f"  {p.name:<24} 命中 {n} 处")
        if n:
            todo.append(p)
    if not todo:
        print("  无需改动")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    for p in todo:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        bak = p.with_suffix(".tex.bak_p555")
        if not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(t.replace(OLD, ""))
        print(f"  ✅ {p.name}")
    # 复核：paper3 下不应再有
    import re
    left = []
    for p in (REPO / "paper3").rglob("*.tex"):
        if ".bak" in p.name:
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if "School of Electronics" in t:
            left.append(p.relative_to(REPO))
    print()
    print(f"  复核 paper3/ 下残留：{len(left)} 处")
    for x in left:
        print(f"     ⚠️ {x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
