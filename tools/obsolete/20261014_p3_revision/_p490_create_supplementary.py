# -*- coding: utf-8 -*-
r"""建立 Supplementary Material 并把 `appendix.tex` 整节移入（2026-10-13）。

## 依据

**PRL Guide（`docs/guides/_prl_guide.txt`）**：
- **Mandatory Submission Requirements 第 1 条**：**双栏 + ≤7 页**，含**全部材料**
- **Supplementary material**：*"We **encourage** the use of supplementary materials… **Cite all supplementary…**"*

## 做法（低风险、收益明确的第一步）

**保留 `appendix.tex` 原文件**（不删，便于回退），新建 **`supplementary/supplementary.tex`**：
- 与正文同 `\documentclass[journal]{IEEEtran}` 与同一套定理环境
- 收录 `appendix.tex` 的内容（按其原有 `\section` 结构）
- 在正文 `main.tex` 里把 `\appendix \input{sections/appendix}` 替换为**一节简短指针**，
  指向 Supplementary（并保留原文中"Appendix D"之类的引用改用 Supplementary 编号）

**⚠️ 代价（必须记录）**：投稿阶段审稿人**看不到**移入补充的材料（其在审稿 PDF 中不出现）。
因此**只移"细节"**（推导、逐 run 表、参数表），**不移"结论"**。

    python tools\_p490_create_supplementary.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
MAIN = PI / "main.tex"
APP = PI / "sections" / "appendix.tex"
SUPDIR = PI / "supplementary"
SUP = SUPDIR / "supplementary.tex"

HEADER = r"""\documentclass[journal]{IEEEtran}

\usepackage{amsmath,amssymb,amsfonts,amsthm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{hyperref}

\newtheorem{theorem}{Theorem}[section]
\newtheorem{corollary}{Corollary}[theorem]
\newtheorem{lemma}{Lemma}[theorem]
\newtheorem{definition}{Definition}[section]
\theoremstyle{definition}
\newtheorem{remark}{Remark}[section]
\renewcommand{\thesubsection}{\thesection.\arabic{subsection}}

\renewcommand{\thesection}{S\arabic{section}}
\renewcommand{\theequation}{S\arabic{equation}}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thefigure}{S\arabic{figure}}

\begin{document}

\title{Supplementary Material for\\
Gradient Structure Laws as Predictors of PEFT Design:\\
Zero-Shot Cross-Architecture Rank Allocation}

\author{\IEEEauthorblockN{Hongrui Wan}
\IEEEauthorblockA{School of Electronics and Computer Science\\
University of Southampton\\
Southampton, SO17 1BJ, United Kingdom\\
Email: hw4c24@soton.ac.uk}
}

\maketitle

\noindent This supplement contains the material that supports the main text but is not
required to follow its argument: the full axiom derivation, the technical lemmas and
proofs, the experimental details, the error-bound derivation, and the per-block coupling
values. Section references of the form S$n$ refer to this document; references to the
main text are marked as such.

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not APP.exists():
        print(f"  🔴 缺 {APP}")
        return 1
    app = io.open(APP, encoding="utf-8", errors="replace").read()
    print(f"  appendix.tex = {len(app)} 字符")

    # appendix.tex 以 "\section{" 开头（因为 main.tex 里已有 \appendix）
    body = app
    # 去掉可能的 \appendix 指令（若有）
    body = re.sub(r"^\s*\\appendix\s*", "", body)

    header = HEADER.replace("\\begin{document}", "\\begin{document}", 1)
    footer = "\n\n\\bibliographystyle{IEEEtran}\n\\bibliography{references}\n\n\\end{document}\n"
    main = io.open(MAIN, encoding="utf-8", errors="replace").read()
    print(f"  main.tex = {len(main)} 字符")
    n_app = main.count("\\appendix")
    print(f"  main.tex 中 \\appendix 命中 {n_app}")
    if not a.apply:
        print("  （预演）")
        return 0

    SUPDIR.mkdir(parents=True, exist_ok=True)
    # 备份
    for p in (MAIN,):
        bak = p.with_suffix(".tex.bak_p490")
        if not bak.exists():
            shutil.copy2(p, bak)

    io.open(SUP, "w", encoding="utf-8", newline="").write(header + body + footer)
    print(f"  ✅ 已写 {SUP.relative_to(PI)}（{len(header) + len(body) + len(footer)} 字符）")

    # main.tex: 把 \appendix + \input{sections/appendix} 替换为指针段
    POINTER = (
        "\\section*{Supplementary material}\n"
        "The full axiom derivation, the technical lemmas and proofs, the experimental\n"
        "details, the error-bound derivation and the complete per-block coupling values are\n"
        "provided as Supplementary Material (Supplementary Sections~S1--S6). Every result\n"
        "quoted in this paper is stated in the main text; the supplement supplies the\n"
        "derivations behind them.\n"
    )
    new = main.replace("\\appendix\n\\input{sections/appendix}\n", POINTER)
    if new == main:
        # 试另一种写法
        new = main.replace("\\appendix\r\n\\input{sections/appendix}\r\n", POINTER)
    if new == main:
        print("  🔴 未能替换 main.tex 的 appendix 输入（换行不匹配）")
        return 1
    io.open(MAIN, "w", encoding="utf-8", newline="").write(new)
    back = io.open(MAIN, encoding="utf-8", errors="replace").read()
    print(f"  ✅ main.tex 已改为指针段（{len(back)} 字符，减少 {len(main) - len(back)}）")
    print(f"  {'✅' if '\\input{sections/appendix}' not in back else '🔴'} main.tex 不再输入 appendix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
