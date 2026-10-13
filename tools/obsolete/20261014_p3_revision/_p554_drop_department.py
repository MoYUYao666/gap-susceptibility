# -*- coding: utf-8 -*-
r"""改作者块：去掉院系，只留 University of Southampton（2026-10-13）。

## 操作者要求

> **"为什么 Hongrui Wan 后面会有 School of Electronics and Computer Science，不要写"**

**原状**：
```
\IEEEauthorblockA{School of Electronics and Computer Science\\
University of Southampton\\
Southampton, SO17 1BJ, United Kingdom\\
Email: contact@example.com}
```

**⇒ 改为**（去掉院系，保留单位、地址、邮箱）：
```
\IEEEauthorblockA{University of Southampton\\
Southampton, SO17 1BJ, United Kingdom\\
Email: contact@example.com}
```

**⚠️ Guide 要求**：**"The institutional email address needs to be provided for all the authors
both in the submission system and in the footnote of the first page of the manuscript"** ——
⇒ **邮箱必须保留**（本次不动）。

    python tools\_p554_drop_department.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
TARGETS = [PI / "main.tex", PI / "main_full.tex", PI / "main_body_full.tex",
           PI / "supplementary" / "supplementary.tex"]

OLD = "School of Electronics and Computer Science\\\\\n"
NEW = ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    found = []
    for p in TARGETS:
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(OLD)
        if n:
            found.append((p, n))
            print(f"  {p.relative_to(PI)}: 命中 {n} 处")
    if not found:
        print("  ⚠️ 未命中（可能已改或写法不同）—— 逐文件列出含 'School of' 的位置：")
        for p in TARGETS:
            if not p.exists():
                continue
            t = io.open(p, encoding="utf-8", errors="replace").read()
            for m in __import__("re").finditer(r"School of[^\\\\\n]*", t):
                ln = t[:m.start()].count("\n") + 1
                print(f"     {p.relative_to(PI)}:{ln}  {m.group(0)!r}")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    for p, n in found:
        t = io.open(p, encoding="utf-8", errors="replace").read()
        bak = p.with_suffix(".tex.bak_p554")
        if not bak.exists():
            shutil.copy2(p, bak)
        t2 = t.replace(OLD, NEW)
        io.open(p, "w", encoding="utf-8", newline="").write(t2)
        print(f"  ✅ {p.relative_to(PI)}：{len(t):,} → {len(t2):,} 字符")
    print()
    print("  复核（作者块应只剩 3 行）：")
    for p in TARGETS:
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        i = t.find("\\IEEEauthorblockA")
        if i < 0:
            continue
        j = t.find("}", i)
        blk = t[i:j + 1]
        print(f"  ── {p.relative_to(PI)}")
        for l in blk.splitlines():
            print(f"       {l}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
