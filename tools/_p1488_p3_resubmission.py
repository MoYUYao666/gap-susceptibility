# -*- coding: utf-8 -*-
r"""P3 soundness hardening 3: explicit real-image numbers in the conclusion + resubmission cover letter.

    python tools/_p1488_p3_resubmission.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "paper3", "paper_ieee")
CONC = os.path.join(BASE, "sections", "conclusion.tex")
LETTER = os.path.join(BASE, "cover_letter_prl_resubmission.tex")

OLD = "it does not reappear\nunder real image--text pairs at the scales we could run."
NEW = ("it does not reappear\nunder real image--text pairs at the scales we could run ($\\Delta E=+83.0$ against $-7.5$ at $r=5$ and "
       "$r=6$ under the instruction protocol, and $+66.5$ against $-39.5$ under the caption protocol).")

LETTER_TEX = r"""\documentclass[11pt]{article}
\usepackage[letterpaper,margin=1in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{url}
\pagestyle{empty}
\begin{document}
\sloppy

\begin{flushright}
Hongrui Wan \\
\href{mailto:hw4c24@soton.ac.uk}{hw4c24@soton.ac.uk} \\
University of Southampton \\
\today
\end{flushright}

\vspace{1em}

\noindent Prof.\ Yonghuai Liu \\
Editor-in-Chief, \emph{Pattern Recognition Letters}

\vspace{0.8em}
\noindent\textbf{Re: new submission --- ``Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry:
Identifiability, Negative Results, and Protocol Dependence''}

\vspace{0.6em}
Dear Professor Liu,

\vspace{0.6em}
This letter accompanies a \emph{new submission} that replaces the manuscript rejected on 21 October 2026
(\texttt{PRLETTERS-D-26-02378R1}). We do not dispute the decision. Instead of resubmitting the same paper, we have
restructured it around the question the Associate Editor identified --- the soundness of the technical choices and the
interpretation of the results --- and we list the substantive changes below so that the new version can be judged on its
own terms.

\textbf{What changed.}
\begin{enumerate}
  \item \textbf{The negative results are now the paper's explicit content.} A claim-status table (Supplementary
        Section~S17) separates what the paper supports from what it does not: zero-shot allocation beating uniform rank is
        \emph{not} supported (the advantage reverses across learning rates and vanishes at matched training loss), the
        crossing generalising to real images is \emph{not} supported, and AdaLoRA is better in our own comparison.
  \item \textbf{The crossing is now a statistical statement.} Five seeds per rank give $-23.0\pm22.3$ at $r=5$ and
        $+65.5\pm38.5$ at $r=6$, with an exact two-sided permutation test at $p=0.008$ (the minimum attainable with five
        seeds per group); the per-seed table and the protocol-window table are in the supplement (S14, S16).
  \item \textbf{The blank-image protocol is bounded by a real-image control.} The sign pattern reverses under real
        image--text pairs ($\Delta E=+83.0$ against $-7.5$ at $r=5$ and $r=6$ under the instruction protocol, $+66.5$
        against $-39.5$ under the caption protocol), so the crossing is stated as a property of the measurement
        protocol, not of the model.
  \item \textbf{The additivity assumption (R3$'$) is stated as an assumption.} It is listed in the claim-status table
        with the consequence if it is violated; it is not used as if it were derived.
  \item \textbf{Reproducibility is now complete.} The data statement points to the public repository and the frozen
        version DOI, and a provenance appendix (S13) maps every table and figure to its generating script and archive.
\end{enumerate}

\textbf{What did not change.} The theorem, the transfer result and the identifiability argument are the same; the
revision is about scope, evidence and interpretation rather than about adding a new mechanism.

We would be grateful if the manuscript could be considered for review as a new submission. We understand that the
decision is in the Editor's hands and that a re-review is not guaranteed.

\vspace{1em}
Yours sincerely,

\vspace{2em}
Hongrui Wan \\
University of Southampton

\end{document}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    c = io.open(CONC, encoding="utf-8").read()
    if "83.0" not in c:
        assert c.count(OLD) == 1, c.count(OLD)
        c = c.replace(OLD, NEW, 1)
        io.open(CONC, "w", encoding="utf-8", newline="").write(c)
        print("  real-image numbers added to the conclusion")
    if not os.path.exists(LETTER):
        io.open(LETTER, "w", encoding="utf-8", newline="").write(LETTER_TEX)
        print("  resubmission cover letter written")
    if a.apply:
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "cover_letter_prl_resubmission.tex"], cwd=BASE,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        print("  cover letter build exit", r.returncode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
