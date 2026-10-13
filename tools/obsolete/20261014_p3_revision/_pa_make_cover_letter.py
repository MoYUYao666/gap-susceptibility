# -*- coding: utf-8 -*-
r"""为 Paper A 生成 Neurocomputing 的 cover letter。

## 须知（依据 `_guide_neurocomputing.txt` 与既有先例）

- Neurocomputing 为 **single anonymized** → 稿件**无需匿名**，cover letter 可署名；
- 本稿**从未投稿**，故无历史披露义务；但**主动披露与姊妹稿的关系**是既有做法
  （A23 的封面信同时披露 A1 与 P1），且本稿正文的实证部分来自同一批实验；
- Highlights 单独文件已备（`highlights_nc.txt/.pdf`）。

## 内容要点（全部有据）

1. 问题与贡献（OD 理论 + 实证刻画）；
2. **诚实呈现新结果**：严格冻结对照在 CLIP 支持"只适配文本侧"、在 SigLIP **方向相反**
   ——这是本文与既有认知最不同的一点；
3. 为何适合 Neurocomputing（ML/表示学习方向、长文友好、single anonymized）；
4. 合规：摘要 234 词 ≤250、highlights 单独文件、数据可得性、利益声明、无版面费。

    python tools\_pa_make_cover_letter.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "paper合" / "cover_letter_nc.tex"

TEX = r"""\documentclass[11pt]{article}
\usepackage[letterpaper,margin=1in]{geometry}
\usepackage[hidelinks]{hyperref}
\pagestyle{empty}
\begin{document}

\begin{flushright}
Hongrui Wan \\
\href{mailto:contact@example.com}{contact@example.com} \\
University of Southampton \\
\today
\end{flushright}

\vspace{1em}

\noindent Dear Editors,

\vspace{0.6em}
\noindent\textbf{Submission of a research article to \emph{Neurocomputing}}

\vspace{0.6em}
I am pleased to submit my manuscript ``\emph{Protect, Don't Perturb: From Empirical Regularities to a
Dynamical Theory of Cross-Modal Alignment under PEFT}'' for consideration in \emph{Neurocomputing}.

\vspace{0.5em}
\noindent\textbf{What the paper does.}
Fine-tuning a vision--language model on a small corpus can widen the gap between its image and text
embeddings, and practitioners have adopted the rule of adapting the text side while leaving the visual
encoder alone. This paper asks what governs that behaviour, and answers it with a dynamical account.
It derives \emph{Gap Susceptibility} from gradient flow and obtains a first-order ODE for the alignment
energy whose perturbation force is the projected task gradient and whose restoring coefficient is stable
within parameter-efficient fine-tuning. Across the archived runs the ODE predicts complete gap
trajectories at a median $R^2$ of 0.97, against 0.00 for a constant baseline.

\vspace{0.5em}
\noindent\textbf{A result that qualifies the received rule.}
The paper's most consequential finding is a negative one about scope. A strict-freezing control, which
trains only the adapter matrices so that the two arms differ solely in where the adapters sit, confirms
the text-only ordering on CLIP: text-only reduces the gap more than the both-position arm
($-0.046$ against $-0.026$ over five seeds, paired $t=+10.0$). Repeating the same control at the same
budget on SigLIP \emph{reverses} it: text-only increases the gap while both-position reduces it
($+0.066$ against $-0.011$, paired $t=-52.7$, consistent across all five seeds). The text-only advantage
is therefore a property of the architecture rather than a universal default, and the manuscript reports
it as such rather than asserting the familiar rule. A second finding cuts across architectures: both
positions retrieve better than text-only on CLIP and on SigLIP, while reducing the gap more on only one of
them, so a smaller gap is not a proxy for retrieval quality.

\vspace{0.5em}
\noindent\textbf{Why \emph{Neurocomputing}.}
The work sits in the Journal's areas of machine learning and representation learning, and its mode is the
one the Journal accommodates well: a dynamical theory grounded in an accompanying empirical study, with
the theory's scope stated explicitly. It is a single-author submission and is not under consideration
elsewhere.

\vspace{0.5em}
\noindent\textbf{Compliance.}
The abstract is 234 words, within the stated limit. Highlights are supplied as a separate file. The
manuscript carries a data-availability statement and a declaration of competing interests. No part of it
has been published previously, and it reports no results that are not traceable to the archived result
files described in the manuscript.

\vspace{0.5em}
\noindent\textbf{Related work by the author.}
For transparency: I have separate manuscripts under review at other journals arising from neighbouring
research on cross-modal alignment. None of them contains the dynamical theory presented here, and this
manuscript does not cite any of them.

\vspace{0.5em}
\noindent I would be glad to provide any further information the editorial office requires.

\vspace{1em}

\noindent Sincerely,

\vspace{1em}

\noindent Hongrui Wan \\
University of Southampton \\
\href{mailto:contact@example.com}{contact@example.com}

\end{document}
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if apply:
        OUT.write_text(TEX, encoding="utf-8")
        print(f"  ✅ 写出 {OUT.name}")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
