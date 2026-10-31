# -*- coding: utf-8 -*-
r"""Enlarge the small later figures and embed the graphical abstract in the appendix.

Figure sizing: the five figures were 0.55, 0.62, 0.55, 0.45 and 0.48 textwidths, so the two later ones (the training-time
trajectories and the task-sensitivity spectrum) rendered noticeably smaller than the rest. Widths are now 0.62-0.72, and
the graphical abstract - previously a separate portal file only - is added as an appendix figure so it is findable in the
PDF as well.

    python tools/_p1286_fix_figures_and_embed_ga.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

WIDTHS = [
    ("fig1_lambda.pdf", "0.62"),
    ("fig2_tau_top1.pdf", "0.62"),
    ("fig3_trajectory.pdf", "0.60"),
    ("fig4_spectrum.pdf", "0.62"),
    ("fig5_matched_gap.pdf", "0.72"),
]

GA_BLOCK = r"""
\subsection{Graphical abstract}
\label{app:graphical}

Figure~\ref{fig:ga} condenses the four lines of evidence into one page: (A) the matched-gap dissociation across three
perturbation families, (B) the prompt-template drift, where the gap moves while accuracy barely does, (C) the balanced
accuracy obtained when a threshold fitted on one setting is applied to another, and (D) the regret of label-free
checkpoint selection.

\begin{figure}[H]
\centering
\includegraphics[width=0.98\textwidth]{figures/graphical_abstract.pdf}
\caption{Graphical abstract. (A) Centroid gap against zero-shot top-1 for the three perturbation families on ImageNet-5k;
the open circles mark the matched-gap pair that differs by 32.7 points. (B) Ten prompt templates on five backbones:
only the text embedding changes, and the gap spread reaches 0.094 while top-1 moves by a few points. (C) Balanced
accuracy when the threshold fitted on the row's setting is applied to the column's; values below 0.5 are anti-correlated
with accuracy. (D) Mean regret of label-free checkpoint-selection rules against the labelled oracle, with bootstrap
intervals.}
\label{fig:ga}
\end{figure}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()

    changed = 0
    for name, width in WIDTHS:
        pat = re.compile(r"\\includegraphics\[[^\]]*\]\{figures/" + re.escape(name) + r"\}")
        m = pat.search(t)
        if not m:
            print(f"  !! {name} not found")
            continue
        old = m.group(0)
        new = r"\includegraphics[width=" + width + r"\textwidth]{figures/" + name + "}"
        if old != new:
            t = t.replace(old, new, 1)
            changed += 1
            print(f"  {name}: {old.split(']')[0][17:]} -> width={width}")
    print(f"  widths changed: {changed}")

    if "app:graphical" not in t:
        k = t.find("\\begin{thebibliography}")
        print(f"  bibliography anchor: {k}")
        assert k > 0
        t = t[:k] + GA_BLOCK + "\n" + t[k:]
        print("  graphical abstract embedded as an appendix figure")

    for token in ("fig:ga", "app:graphical", "graphical_abstract.pdf"):
        print(f"  present {token!r}: {t.count(token)}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
