# -*- coding: utf-8 -*-
r"""测量 Elsevier 双栏模板（cas-dc）在 7 页内能装多少词 + 多少条参考文献。

做法：生成一份填充稿，正文用**可计数的拉丁词填充**，参考文献用 natbib 生成 N 条，
编译后用 pdfinfo 读页数，从而反推出"7 页 ≈ 多少词 + 多少引用"的预算。

    python tools/_prl_capacity_test.py
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "paper_review_prl"
TEX = OUT / "_capacity_test.tex"
PDF = OUT / "_capacity_test.pdf"

# 常见英文词，用于生成可计数的填充文本
WORDS = ("the of and to in a is that for it as with on be by this are from or an at which "
         "we can model data method results show that performance training adapters rank budget "
         "multimodal vision language evaluation benchmark protocol comparable evidence").split()


def filler(n_words: int, seed: int = 0) -> str:
    out = []
    for i in range(n_words):
        out.append(WORDS[(i * 7 + seed) % len(WORDS)])
    # 组成句子，便于断行
    text = " ".join(out)
    return re.sub(r"(\. )", ".\n\n", text)


def build(n_body_words: int, n_refs: int) -> int:
    body = filler(n_body_words)
    refs = "\n".join(
        f"\\bibitem{{r{i}}} A. Author{i}, B. Author{i}, Title of reference number {i} for the "
        f"capacity measurement, Journal of Testing {i} ({2000 + i % 25}) 1--10."
        for i in range(1, n_refs + 1)
    )
    tex = rf"""\documentclass[a4paper,fleqn]{{cas-dc}}
\usepackage[numbers]{{natbib}}
\usepackage{{amsmath,amssymb}}
\begin{{document}}
\shorttitle{{Capacity test}}
\shortauthors{{H. Wan}}
\title[mode=title]{{Capacity measurement for a seven-page double-column review}}
\author[1]{{Hongrui Wan}}
\affiliation[1]{{organization={{University of Southampton}}, city={{Southampton}}, country={{United Kingdom}}}}
\begin{{abstract}}
Capacity measurement only. This document determines how many words and references fit in seven
double-column pages so the writing budget can be fixed in advance.
\end{{abstract}}
\begin{{highlights}}
\item Capacity test only
\item Measures the seven-page budget
\item Informs the writing plan
\end{{highlights}}
\begin{{keywords}}
capacity test \sep word budget \sep page limit
\end{{keywords}}
\maketitle

\section{{Introduction}}
{body}

\section{{Body}}
{body}

\section{{Discussion}}
{body}

\begin{{thebibliography}}{{00}}
{refs}
\end{{thebibliography}}
\end{{document}}
"""
    TEX.write_text(tex, encoding="utf-8", newline="")
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", TEX.name], cwd=OUT, capture_output=True)
    subprocess.run(["bibtex", TEX.stem], cwd=OUT, capture_output=True)
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", TEX.name], cwd=OUT, capture_output=True)

    info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True).stdout.decode("utf-8", "ignore")
    m = re.search(r"Pages:\s+(\d+)", info)
    return int(m.group(1)) if m else -1


def main() -> int:
    total_words = 3 * 1500   # 三节，每节 1500 词
    n_refs = 50
    print(f"测试：正文约 {total_words} 词（3×1500）+ {n_refs} 条参考文献")
    pages = build(total_words, n_refs)
    print(f"  → 实测 {pages} 页\n")
    if pages < 0:
        return 1

    # 线性外推：按文档总页数比例估"7 页容量"
    print("=== 估算：7 页双栏的容量 ===")
    if pages > 0:
        words_per_page = total_words / pages
        refs_per_page = n_refs / pages
        budget_words = int(words_per_page * 7)
        print(f"  正文词密度 ≈ {words_per_page:.0f} 词/页")
        print(f"  参考文献密度 ≈ {refs_per_page:.1f} 条/页")
        print(f"  若 7 页全给正文 → 约 {budget_words} 词")
        print(f"  若 7 页含 55 条引用（约 {55/refs_per_page:.1f} 页）→ 正文余约 "
              f"{int(words_per_page * (7 - 55/refs_per_page))} 词")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
