# -*- coding: utf-8 -*-
r"""Insert the matched-gap control into A1 as a new subsection, with figure and table.

The existing subsection already establishes non-monotonicity (lambda = 0.5 shrinks the gap to 0.41 yet top-1 falls to
47.6%, lambda = 1 shrinks it to 0.01 and top-1 falls to 32.0%). What it lacks is an explicit *matched-gap* comparison,
which is the strongest form of "the gap is not a sufficient statistic": two configurations at the same centroid gap with
very different accuracy. This experiment supplies it, on a protocol stated in the text (the gap direction is estimated on
the benchmark itself, so no Flickr30k rows are needed).

Numbers come from outputs/analysis/a1_matched_gap_families.json (5,000 ImageNet images, CLIP ViT-B/32, 1,000 classes).

    python tools/_p1211_insert_matched_gap.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

ANCHOR = "\\subsection{Order preservation"

BLOCK = r"""
\subsection{A matched-gap control: the same gap can hide 33 accuracy points}
\label{sec:matchedgap}

The non-monotonicity above already implies that the mapping from gap to accuracy is not injective, but it does not yet
compare two configurations \emph{at the same gap}. Figure~\ref{fig:matchedgap} makes that comparison explicit. Holding the
model, the benchmark and the class list fixed, we sweep three perturbation families that each trace a curve in the
(gap, accuracy) plane: translation along the gap direction (the surgery family, parameter $\lambda$), contraction toward
each image's own class prototype (parameter $a$), and isotropic Gaussian noise on the image embeddings ($\sigma$, three
seeds). The gap direction is estimated on this benchmark rather than on Flickr30k, which is why the absolute centroid gaps
in this subsection are slightly larger than in Figure~\ref{fig:lambda}; the comparison below is between points measured
under one and the same convention.

Two matched-gap pairs settle the question. On the return branch of the translation family, $\lambda=0.5$ leaves
$\mathrm{CG}=0.426$ with top-1 $46.8\%$, while $\lambda=2$ restores the gap to $\mathrm{CG}=0.398$ --- a difference of
$0.028$ --- and top-1 collapses to $14.1\%$: \textbf{33 points of accuracy at an essentially identical gap}. Relaxing the
tolerance to $0.05$ widens the spread to \textbf{52 points}: $\lambda=0.25$ gives $\mathrm{CG}=0.651$ with $55.6\%$, and
$\lambda=4$ gives $\mathrm{CG}=0.613$ with $3.5\%$. The direction of the effect also reverses under a different family:
class contraction \emph{raises} the gap ($0.855$ frozen to $0.897$ at $a=0.5$) and \emph{raises} accuracy at the same time
($59.1\%$ to $78.1\%$), so a larger gap accompanies better classification. The noise family is the control: it leaves both
quantities essentially unchanged ($\mathrm{CG}$ $0.849$--$0.856$, top-1 $57.9$--$59.2\%$).

Measured at matched gap, the spread is therefore not a small correction but the whole range of the effect. This is what
"the gap is a first-moment statistic while accuracy is a rank decision" means operationally: a first moment can be
restored by a transformation that has already destroyed the ordering the decision uses.

\begin{figure}[H]
\centering
\includegraphics[width=0.62\textwidth]{figures/fig5_matched_gap.pdf}
\caption{Top-1 is not a function of the centroid gap. Each family traces its own curve; circles mark the matched-gap pair
($\mathrm{CG}$ within $0.03$) that differ by $32.7$ accuracy points, and the squares mark the family-mean noise points.
The dashed line is the frozen baseline.}
\label{fig:matchedgap}
\end{figure}

\begin{table}[H]
\centering
\caption{Matched-gap control on 5{,}000 ImageNet images (CLIP ViT-B/32, 1{,}000 classes; gap direction estimated on the
benchmark). The two shaded rows are the matched pairs: gap differences of $0.028$ and $0.038$ accompany accuracy
differences of $32.7$ and $52.1$ points.}
\label{tab:matchedgap}
\small
\begin{tabular}{@{}llccc@{}}
\toprule
Family & Setting & CG & top-1 (\%) & $\Delta$ vs frozen \\
\midrule
---      & frozen                     & 0.855 & 59.1 & --- \\
\midrule
translation & $\lambda=0.25$          & 0.651 & 55.6 & $-3.5$ \\
translation & $\lambda=0.5$           & 0.426 & 46.8 & $-12.3$ \\
translation & $\lambda=1$             & 0.045 & 33.6 & $-25.5$ \\
translation & $\lambda=2$             & 0.398 & 14.1 & $-45.0$ \\
translation & $\lambda=4$             & 0.613 & 3.5  & $-55.6$ \\
\midrule
contraction & $a=0.1$                 & 0.865 & 63.3 & $+4.2$ \\
contraction & $a=0.25$                & 0.878 & 69.2 & $+10.1$ \\
contraction & $a=0.5$                 & 0.897 & 78.1 & $+19.0$ \\
\midrule
noise       & $\sigma=0.05$ (3 seeds) & 0.855 & 58.9 & $-0.2$ \\
noise       & $\sigma=0.2$ (3 seeds)  & 0.849 & 57.9 & $-1.2$ \\
\bottomrule
\end{tabular}
\end{table}

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    if "sec:matchedgap" in t:
        print("  already inserted")
        return 0
    n = t.count(ANCHOR)
    print(f"  anchor {ANCHOR!r}: {n}")
    if n != 1:
        print("  !! anchor not unique")
        return 1
    if not a.apply:
        print("  (dry run)")
        return 0
    i = t.find(ANCHOR)
    t = t[:i] + BLOCK.lstrip("\n") + t[i:]
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  inserted; new length", len(t))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
