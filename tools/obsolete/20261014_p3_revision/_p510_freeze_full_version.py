# -*- coding: utf-8 -*-
r"""冻结"完整版"（11-12 页）作为备份，并搭好"7 页合规版"的工作流（2026-10-13）。

## 操作者裁决（2026-10-13 12:48）

> **"先做第 1 项，同时准备第 2 项备份"** ⇒
> **① 做到 7 页（证据移入 Supplementary）** ② **同时保留 11-12 页完整版**。

## 做法

**同一套 `sections/*.tex`，两种构建**：
- **`main.tex`** = **7 页合规版**（正文精简，细节进 `supplementary/`）
- **`main_full.tex`** = **完整版**（原样 `\input` 全部 sections，12 页）

**⇒ 用 `main_full.tex` 存档"内容完整"的状态；把删减做在 `sections/*.tex` 上。**
**⚠️ 关键：删减前必须先把 `sections/` 的当前状态**冻结**到 `sections_full/`**，
否则改完就没有完整版了。

    python tools\_p510_freeze_full_version.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
FULL = PI / "sections_full"

MAIN_FULL = r"""% ============================================================================
% main_full.tex —— **完整版**（12 页），用于存档"内容完整"的状态。
%   PRL 的 Mandatory Submission Requirements 要求双栏 ≤7 页；
%   本文件**不作为投稿件**，只用于保留全部论证与数字（回复信引用、审稿人索取）。
%   投稿件是 main.tex（7 页合规版，细节在 supplementary/）。
%   ⚠️ 本文件 \input{sections_full/...}，与 main.tex 的 sections/ 相互独立。
% ============================================================================
\documentclass[journal]{IEEEtran}

\usepackage{amsmath,amssymb,amsfonts,amsthm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{hyperref}
\usepackage{caption}
\captionsetup{skip=6pt}

\newtheorem{theorem}{Theorem}[section]
\newtheorem{corollary}{Corollary}[theorem]
\newtheorem{lemma}{Lemma}[theorem]
\newtheorem{definition}{Definition}[section]
\theoremstyle{definition}
\newtheorem{remark}{Remark}[section]
\renewcommand{\thesubsection}{\thesection.\arabic{subsection}}

\begin{document}

\title{Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation (full version)}

\author{
\IEEEauthorblockN{Hongrui Wan}
\IEEEauthorblockA{School of Electronics and Computer Science\\
University of Southampton\\
Southampton, SO17 1BJ, United Kingdom\\
Email: contact@example.com}
}

\maketitle

\input{main_body_full}

\appendix
\input{sections_full/appendix}

\bibliographystyle{IEEEtran}
\bibliography{references}

\end{document}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    src = PI / "sections"
    print(f"  源目录 {src.relative_to(PI)}：{len(list(src.glob('*.tex')))} 个 tex")
    if FULL.exists():
        print(f"  ⚠️ {FULL.relative_to(PI)} 已存在（{len(list(FULL.glob('*.tex')))} 个 tex）"
              f" —— 将被覆盖为当前状态")
    if not a.apply:
        print("  （预演）")
        return 0
    FULL.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(src.glob("*.tex")):
        shutil.copy2(f, FULL / f.name)
        n += 1
        print(f"  ✅ sections_full/{f.name:<22} {f.stat().st_size:>7,} B")
    print(f"  → 冻结 {n} 个文件")

    # 提取 main.tex 的摘要与正文骨架，生成 main_body_full.tex
    main_t = io.open(PI / "main.tex", encoding="utf-8", errors="replace").read()
    i = main_t.find("\\begin{abstract}")
    j = main_t.find("\\input{sections/introduction}")
    if i < 0 or j < 0:
        print("  🔴 无法定位摘要或正文起点")
        return 1
    body = main_t[i:j]
    body = body + "".join(f"\\input{{sections_full/{k}}}\n" for k in
                          ("introduction", "related_work", "theory", "experiments",
                           "discussion", "conclusion"))
    io.open(PI / "main_body_full.tex", "w", encoding="utf-8", newline="").write(body)
    print(f"  ✅ 已生成 main_body_full.tex（{len(body):,} 字符）")

    io.open(PI / "main_full.tex", "w", encoding="utf-8", newline="").write(MAIN_FULL)
    print(f"  ✅ 已生成 main_full.tex")
    print()
    print("  ⇒ **完整版冻结完成**：`main_full.tex` + `sections_full/`")
    print("  ⇒ 后续删减只动 `sections/`，**完整版不受影响**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
