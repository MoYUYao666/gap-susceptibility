# -*- coding: utf-8 -*-
r"""Add the local rank-sensitivity control to the P3 supplement.

    python tools/_p1360_p3_supplement_control.py [--apply]
"""
from __future__ import annotations

import argparse
import io

TEX = "paper3/paper_ieee/supplementary/supplementary.tex"

SECTION = r"""

\section{Local Rank-Sensitivity Control on CLIP}
\label{sec:supp-rank-control}

The main text reports a critical rank for LLaVA-1.5-7B under the blank-image protocol and attributes the crossing to
the measurement protocol and system rather than to low-rank adaptation in general. To probe that boundary we ran the
cheaper local analogue: CLIP ViT-B/32 with LoRA on the text tower, ranks $4$--$64$, on DTD (47 classes) with a per-class
held-out split (40 training and 15 held-out images per class), six epochs and two seeds. Table~\ref{tab:supp-rank}
reports the results. Increasing the rank does not inflate the gap: the centroid gap stays inside $[0.744, 0.792]$ across
all 60 checkpoints (the largest within-run change is $0.031$), and the held-out accuracy varies between $55.9\%$ and
$65.1\%$ without divergence or collapse at $r=32$ or $r=64$. The pooled correlations are $r(\text{rank},\text{top-1}) =
-0.10$ and $r(\text{rank},\text{CG}) = -0.43$, i.e.\ the larger ranks are, if anything, slightly \emph{closer} in the
embedding space. This is consistent with the main text's attribution: a phenomenon that is a property of one system and
protocol need not reappear on another, and a control that fails to reproduce it is a boundary on the claim rather than
evidence for it. We therefore report the control here and do not transfer it to the LLaVA statement.

\begin{table}[h]
\centering
\caption{Local rank sensitivity: CLIP ViT-B/32, text-tower LoRA, DTD (47 classes; 40 training and 15 held-out images per
class), six epochs, two seeds. Entries are means over the two seeds; the gap is the centroid gap on the held-out split.}
\label{tab:supp-rank}
\begin{tabular}{@{}rrrrrr@{}}
\toprule
Rank & Trainable params & Best top-1 & Last top-1 & CG (epoch 1) & CG (epoch 6) \\
\midrule
4  & 147{,}456  & 63.5 & 63.0 & 0.786 & 0.760 \\
8  & 294{,}912  & 64.0 & 63.5 & 0.780 & 0.764 \\
16 & 589{,}824  & 64.0 & 64.0 & 0.772 & 0.763 \\
32 & 1{,}179{,}648 & 64.1 & 63.3 & 0.773 & 0.770 \\
64 & 2{,}359{,}296 & 64.1 & 62.1 & 0.762 & 0.763 \\
\bottomrule
\end{tabular}
\end{table}

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(TEX, encoding="utf-8").read()
    if "Local Rank-Sensitivity Control on CLIP" in t:
        print("  section already present")
        return 0
    anchor = "\\bibliographystyle{IEEEtran}"
    assert t.count(anchor) == 1, t.count(anchor)
    t = t.replace(anchor, SECTION.strip("\n") + "\n\n" + anchor, 1)
    print("  section inserted")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(TEX, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
