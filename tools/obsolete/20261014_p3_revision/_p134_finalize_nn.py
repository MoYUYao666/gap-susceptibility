# -*- coding: utf-8 -*-
r"""收尾：修我写错的邮箱、更新 declaration、核对 highlights 字符数（2026-10-10）。

## ① 我的错

我在 Crossref/OpenAlex 的 `mailto=` 里写了 `contact@example.com`，
**而项目实际邮箱是 `contact@example.com`**（全项目 20 处；`hrw1n24` **0 处**）。
→ 修所有 `tools/_p1*.py` 里的该字符串（**只影响礼貌池标识，不影响取回的数据**）。

## ② `declaration.tex` 还是旧标题 + 16 September 2026

## ③ `highlights.tex` 逐条字符数核对（NN：3–5 条，每条 ≤85 含空格）

    python tools\_p134_finalize_nn.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BAD = "contact@example.com"
GOOD = "contact@example.com"

DECL_NEW = r"""\documentclass[11pt]{article}
\usepackage[T1]{fontenc}
\usepackage{mathptmx}
\usepackage[margin=1in]{geometry}
\usepackage{parskip}

\begin{document}
\thispagestyle{empty}

\begin{center}
{\Large\bfseries Declaration of Interest}\\[8pt]
Manuscript: ``Order Preservation as a Zero-Overhead Monitor for Classification Fine-Tuning:
Why the Modality Gap Is Not a Universal Health Metric''\\
Author: Hongrui Wan (University of Southampton, United Kingdom)\\
Date: 10 October 2026
\end{center}

\vspace{6pt}

\section*{Declaration of competing interests}

The author declares that they have no known competing financial interests or personal
relationships that could have appeared to influence the work reported in this paper. The
author has nothing to declare.

\section*{Funding}

This research did not receive any specific grant from funding agencies in the public,
commercial, or not-for-profit sectors.

\section*{Declaration of generative AI and AI-assisted technologies in the manuscript preparation process}

During the preparation of this work the author used Claude (Anthropic) and DeepSeek V4 in
order to draft and revise the manuscript text and to prepare experimental code and figures.
After using these tools, the author reviewed and edited the content as needed and takes full
responsibility for the content of the published article.

\end{document}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # ① 修邮箱
    print("=== ① 修我写错的邮箱 ===")
    n_files = n_hits = 0
    for f in glob.glob(str(REPO / "tools" / "*.py")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        if BAD in t:
            n = t.count(BAD)
            if a.apply:
                io.open(f, "w", encoding="utf-8", newline="").write(t.replace(BAD, GOOD))
            n_files += 1
            n_hits += n
            print(f"  {Path(f).name}: {n} 处")
    print(f"  → {'已修' if a.apply else '将修'} {n_files} 个文件 / {n_hits} 处")

    # ② declaration
    print("\n=== ② declaration.tex ===")
    d = REPO / "paper_a1" / "declaration.tex"
    cur = io.open(d, encoding="utf-8", errors="replace").read()
    print(f"  含旧标题: {cur.count('Order Preservation Governs Zero-Shot Robustness')} 处")
    print(f"  含旧日期: {cur.count('16 September 2026')} 处")
    if a.apply:
        bak = d.with_suffix(".tex.bak_nc")
        if not bak.exists():
            io.open(bak, "w", encoding="utf-8", newline="").write(cur)
        io.open(d, "w", encoding="utf-8", newline="").write(DECL_NEW)
        print("  ✅ 已更新（旧标题→新标题；日期→10 October 2026）")

    # ③ highlights 字符数
    print("\n=== ③ highlights 字符数（NN：3–5 条，每条 ≤85 含空格）===")
    h = io.open(REPO / "paper_a1" / "highlights.tex", encoding="utf-8",
                errors="replace").read()
    items = [re.sub(r"\\[a-zA-Z]+", "", x).strip()
             for x in re.findall(r"\\item\s+(.+)", h)]
    print(f"  条数: {len(items)} {'✅' if 3 <= len(items) <= 5 else '❌'}")
    over = 0
    for it in items:
        n = len(it)
        flag = "✅" if n <= 85 else "❌"
        if n > 85:
            over += 1
        print(f"   {flag} [{n:>3} 字符] {it}")
    print(f"  超 85 的条数: {over} {'✅' if over == 0 else '❌'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
