# -*- coding: utf-8 -*-
r"""把字面 `\n`（反斜杠+n，非换行）替换为真换行（2026-10-13）。

## 病因（本阶段第 3 次同型）

在 Python 里用 `r"..."` 原始字符串拼 LaTeX 时，`r"...\n..."` 里的 `\n` **不是换行**，
而是**字面的反斜杠 + n** ⇒ 写进 `.tex` 后 LaTeX 当作未定义命令 ⇒ **`! Undefined control sequence`**。

**前两次**：`_p432`（27 个错误）、`_p434`（2 个残留）。**本次**：`_p500` 引入 10 个。

**⇒ 根治**：本脚本做成**通用修复器**，跑在**所有** `sections/*.tex` 上，并断言"无残留字面 `\n`"。
**并建议把这条加入收尾门禁**（每次改完 tex 跑一次）。

    python tools\_p501_strip_literal_n.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"


def fix(text: str):
    """字面 \\n → 真换行；行尾的（真换行已存在）→ 删除。"""
    n_before = len(re.findall(r"\\n", text))
    t = re.sub(r"\\n[ \t]*(?=\r?\n)", "", text)
    t = re.sub(r"\\n", "\n", t)
    return t, n_before, len(re.findall(r"\\n", t))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted(glob.glob(str(PI / "sections" / "*.tex"))) + \
        sorted(glob.glob(str(PI / "*.tex"))) + \
        sorted(glob.glob(str(PI / "supplementary" / "*.tex")))
    files = [f for f in files if ".bak" not in os.path.basename(f)]
    total = 0
    print(f"  检查 {len(files)} 个 tex")
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        t2, before, after = fix(t)
        if before:
            print(f"  {'✅' if after == 0 else '🔴'} {os.path.relpath(f, PI):<40} "
                  f"字面 \\n {before} → {after}")
            total += before
            if a.apply and after == 0:
                io.open(f, "w", encoding="utf-8", newline="").write(t2)
    print(f"  → 共修复 {total} 处字面 \\n")
    if not a.apply:
        print("  （预演）")
        return 0
    # 复核
    left = 0
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        left += len(re.findall(r"\\n", t))
    print(f"  ✅ 复核：全稿残留字面 \\n = {left}")
    return 0 if left == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
