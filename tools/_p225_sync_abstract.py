# -*- coding: utf-8 -*-
r"""把 `main.tex` 的标题与摘要同步进 `abstract.tex`（修第 6 项）（2026-10-12）。

## 为什么

`abstract.tex` 是"**改了标题没改正文**"的半成品：
标题已是新版（含 "Zero-Overhead Monitor"），正文却还是旧摘要（从不提监控）。

`tools/_p222` 的第 6 项因 `re.sub` 的替换串里反斜杠被当转义而崩。
**本脚本用切片（不用 re.sub 的替换模板）**，避开该问题。

    python tools\_p225_sync_abstract.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    mt = io.open(A1 / "main.tex", encoding="utf-8", errors="replace").read()
    mabs = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", mt, re.S)
    mtitle = re.search(r"\\title\{", mt)
    if not (mabs and mtitle):
        print("  🔴 main.tex 缺 abstract 或 title")
        return 1
    # 取标题（含嵌套花括号的健壮取法）
    i = mtitle.start() + len(r"\title{")
    depth, j = 1, i
    while j < len(mt) and depth:
        if mt[j] == "{":
            depth += 1
        elif mt[j] == "}":
            depth -= 1
        j += 1
    title = mt[i:j - 1]
    body = mabs.group(1).strip()
    print(f"  main.tex 标题: {title[:90]}…")
    print(f"  main.tex 摘要: {len(body.split())} 词")

    ab = A1 / "abstract.tex"
    at = io.open(ab, encoding="utf-8", errors="replace").read()
    # ① 换标题（同样用括号配平取法）
    mt2 = re.search(r"\\title\{", at)
    if mt2:
        i2 = mt2.start() + len(r"\title{")
        depth, j2 = 1, i2
        while j2 < len(at) and depth:
            if at[j2] == "{":
                depth += 1
            elif at[j2] == "}":
                depth -= 1
            j2 += 1
        at = at[:mt2.start()] + "\\title{" + title + "}" + at[j2:]
        print("  ✅ 标题已换")
    # ② 换摘要体（切片，不用替换模板）
    m2 = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", at, re.S)
    if m2:
        at = (at[:m2.start()]
              + "\\begin{abstract}\n" + body + "\n\\end{abstract}"
              + at[m2.end():])
        print("  ✅ 摘要体已换")
    else:
        print("  🔴 abstract.tex 缺 abstract 环境")
        return 1

    if not a.apply:
        print("  （预演）")
        return 0
    bak = ab.with_suffix(".tex.bak_p225")
    if not bak.exists():
        shutil.copy2(ab, bak)
    io.open(ab, "w", encoding="utf-8", newline="").write(at)

    t2 = io.open(ab, encoding="utf-8", errors="replace").read()
    ok = ("Tracks Zero-Shot Accuracy" in t2
          and "Zero-Overhead Monitor" not in t2
          and body.split()[0] in t2)
    print(f"\n  {'✅ abstract.tex 已同步' if ok else '🔴 同步失败'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
