# -*- coding: utf-8 -*-
r"""Bring A1 into Pattern Analysis and Applications shape: keywords, a consolidated Declarations section, a separate
title page, and the AI-use note in the methods section.

PAA's guide (read from the operator's Edge tab) requires 4-6 keywords, and a Declarations section on a title page that
is separate from the manuscript. A1 currently has Neural-Networks-style scattered declaration sections and no keywords.

    python tools/_p1232_paa_frontmatter.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

KEYWORDS = r"""
\begin{keyword}
Modality gap \sep Vision--language models \sep Parameter-efficient fine-tuning \sep Zero-shot classification \sep
Order preservation
\end{keyword}"""

DECL_NEW = r"""\section*{Declarations}

\subsection*{Funding}
This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.

\subsection*{Competing interests}
The author declares no competing financial or non-financial interests.

% AUTHOR CONFIRMED 2026-09-16: no funding sources; the statements in this section are accurate as written.
\subsection*{Ethics approval and consent to participate}
Not applicable. The study analyses publicly available datasets and pre-trained models and involves no human
participants or animal subjects.

\subsection*{Consent for publication}
Not applicable.

\subsection*{Data and code availability}
The per-run result records, analysis scripts, and training configurations supporting the findings of this study are
openly available in the project's public repository at
\url{https://github.com/MoYUYao666/gap-susceptibility}, and in the versioned snapshot archived at Zenodo with DOI
\url{https://doi.org/10.5281/zenodo.23341223}.

\subsection*{Authors' contributions}
Hongrui Wan is the sole author and performed all aspects of the work: conceptualization, methodology, software,
formal analysis, investigation, validation, visualization, and writing of the manuscript.

% AUTHOR CONFIRMED 2026-09-16: the tool names and the scope of this declaration are accurate as written.
\subsection*{Use of artificial-intelligence tools}
During the preparation of this work the author used Claude (Anthropic) and DeepSeek V4 to draft and revise the
manuscript text and to prepare experimental code and figures. After using these tools, the author reviewed and edited
the content as needed and takes full responsibility for the content of the published article.

"""

AI_NOTE = (r"Manuscript preparation and part of the analysis code were produced with AI-assisted tools (Claude and "
           r"DeepSeek V4); the author reviewed all content and takes full responsibility (see Declarations).")

TITLE_PAGE = r"""\documentclass[11pt]{article}
\usepackage[a4paper,margin=2.5cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{url}
\usepackage{parskip}

\begin{document}

\begin{center}
{\Large\bfseries Order Preservation Tracks Zero-Shot Accuracy under Classification Fine-Tuning:\\[2pt]
Why the Modality Gap Is Not a Universal Health Metric}\\[1.2em]
{\large Hongrui Wan}\\[0.4em]
University of Southampton, University Road, Southampton SO17 1BJ, United Kingdom\\
Corresponding author: \texttt{hw4c24@soton.ac.uk}
\end{center}

\section*{Declarations}

\subsection*{Funding}
This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit
sectors.

\subsection*{Competing interests}
The author declares no competing financial or non-financial interests.

\subsection*{Ethics approval and consent to participate}
Not applicable. The study analyses publicly available datasets and pre-trained models and involves no human
participants or animal subjects.

\subsection*{Consent for publication}
Not applicable.

\subsection*{Data and code availability}
The per-run result records, analysis scripts, and training configurations supporting the findings of this study are
openly available in the project's public repository at \url{https://github.com/MoYUYao666/gap-susceptibility}, and in the
versioned snapshot archived at Zenodo with DOI \url{https://doi.org/10.5281/zenodo.23341223}.

\subsection*{Authors' contributions}
Hongrui Wan is the sole author and performed all aspects of the work: conceptualization, methodology, software, formal
analysis, investigation, validation, visualization, and writing of the manuscript.

\subsection*{Use of artificial-intelligence tools}
During the preparation of this work the author used Claude (Anthropic) and DeepSeek V4 to draft and revise the
manuscript text and to prepare experimental code and figures. After using these tools, the author reviewed and edited
the content as needed and takes full responsibility for the content of the published article.

\end{document}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()

    # 1. keywords right after the abstract
    if r"\begin{keyword}" not in t:
        anchor = r"\end{abstract}"
        n = t.count(anchor)
        print(f"  \\end{{abstract}}: {n}")
        assert n == 1
        t = t.replace(anchor, anchor + KEYWORDS, 1)

    # 2. replace the scattered declaration sections
    start_marker = r"\section*{Declaration of competing interest}"
    end_marker = "\\footnotesize\n\\begin{thebibliography}"
    i, j = t.find(start_marker), t.find(end_marker)
    print(f"  declaration block bounds: {i}..{j}")
    assert i > 0 and j > i
    t = t[:i] + DECL_NEW + t[j:]

    # 3. AI note in the methods-equivalent section (PAA asks for it in Methods or a suitable alternative part)
    if AI_NOTE not in t:
        setup = t.find(r"\section{Setup}")
        analysis = t.find(r"\section{Analysis", setup)
        assert setup > 0 and analysis > setup
        t = t[:analysis] + AI_NOTE + "\n\n" + t[analysis:]
        print("  AI-use note added at the end of Setup")

    checks = [
        ("keywords present", r"\begin{keyword}" in t),
        ("Declarations section", r"\section*{Declarations}" in t),
        ("old NN sections gone", r"\section*{Declaration of competing interest}" not in t
         and r"\section*{Declaration of generative AI" not in t),
        ("AI note present", AI_NOTE in t),
    ]
    for label, ok in checks:
        print(f"  {'OK  ' if ok else 'FAIL'} {label}")
    if not all(ok for _, ok in checks):
        return 1
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    io.open(os.path.join(REPO, "paper_a1", "title_page.tex"), "w", encoding="utf-8", newline="").write(TITLE_PAGE)
    print("  written main.tex and title_page.tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
