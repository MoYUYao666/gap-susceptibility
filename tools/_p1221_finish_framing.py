# -*- coding: utf-8 -*-
r"""Finish A1's framing with plain string surgery (no regex).

1. Replace the abstract with a version that states non-sufficiency first and ends on the quantified boundary.
2. Move the non-sufficiency proposition from after `\input{related_work}` to just before it.
3. The introduction now announces four controlled experiments and carries a fourth finding.

    python tools/_p1221_finish_framing.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

ABSTRACT = r"""\begin{abstract}
Classification fine-tuning of a contrastive vision--language model moves the modality gap and erodes class-relative rank
order together. Only the second tracks zero-shot accuracy, and it is free to compute: the Kendall coefficient $\tau$
co-moves with accuracy inside a single training trajectory (mean Pearson $0.90$) and needs only the top-$k$ sets a
validation pass already produces. The gap is not merely a weaker proxy: it is not a \emph{sufficient} statistic for the
accuracy it is used to monitor. We give the structural reason---top-1 depends only on the ordering of each similarity row,
and the centroid gap is not a function of those orderings---and construct matched-gap configurations that differ by $33$
accuracy points at a gap difference of $0.03$ ($52$ points at $0.05$). A $200$-direction control shows the failure is
specific to coherent transformations (random directions at the same gap move top-1 by only $2.5$ points), which is the
regime a fine-tuning trajectory traverses. Class contraction raises the gap and the accuracy at once on all three
families (CLIP $+19.0$, OpenCLIP $+19.4$, SigLIP $+15.0$ points), so a larger gap can accompany better classification.
Under ``gap surgery'' (exact translations) classification can \emph{collapse while the gap shrinks}
($\text{CG}{:}0.82{\to}0.01$, top-1 $59.3\%{\to}32.0\%$), while real fine-tuning can \emph{grow the gap} without
zero-shot loss: the same both-position checkpoint measures $\text{CG}\Delta{=}{+}0.033$ on our subset, $+0.114$ by the
legacy logger; we quote the smaller value. Accuracy rises not from preserving frozen ranks but from \emph{class
alignment}: contraction toward class centroids improves it ($59.3\%{\to}78.6\%$) while \emph{lowering} $\tau$ to $0.615$,
below the $0.761$ of destructive Gaussian noise, so order preservation is necessary, not sufficient. Tasks fall into a
sensitivity spectrum---centroid $<$ zero-shot $<$ retrieval---with $\tau$ the better classification signal and the gap the
better retrieval one. A first-order class-dependent bias field reproduces the \emph{shape} of the measured $\tau(\lambda)$
curve but not its level: across four unrelated benchmarks the law holds at $r=0.93$--$0.99$ while the scale constant it
requires varies over $0.36$--$0.98$. We therefore report the field as a mechanism with a quantified boundary rather than
as a predictive law.
\end{abstract}"""

FINDING4 = r"""\item[(iv)] The gap is not a sufficient statistic, and the failure is structural rather than empirical: a proposition
relates top-1 to row orderings, a matched-gap control produces $33$- and $52$-point accuracy differences at gap differences
of $0.03$ and $0.05$ on CLIP, the same direction replicates on OpenCLIP and SigLIP, and a $200$-direction control shows the
effect requires coherent shifts. The first-order bias field that explains the curve's shape does not fix its level across
benchmarks, which bounds what the mechanism can be used for.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()

    # 1. abstract
    i = t.find(r"\begin{abstract}")
    j = t.find(r"\end{abstract}")
    assert i > 0 and j > i, "abstract markers"
    t = t[:i] + ABSTRACT + t[j + len(r"\end{abstract}"):]
    print("  abstract replaced")

    # 2. move the proposition before \input{related_work}
    p_start = t.find(r"\textbf{Proposition (non-sufficiency of the gap)")
    p_end_marker = r"(Section~\ref{sec:matchedgap})."
    p_end = t.find(p_end_marker, p_start)
    assert p_start > 0 and p_end > p_start, "proposition bounds"
    p_end += len(p_end_marker)
    block = t[p_start:p_end]
    t = t[:p_start] + t[p_end:]
    anchor = r"\input{related_work}"
    k = t.find(anchor)
    assert k > 0, "related_work anchor"
    t = t[:k] + block.rstrip() + "\n\n" + t[k:]
    print("  proposition moved before related_work")

    # 3. four experiments + fourth finding
    old3 = "We resolve this decoupling with three controlled experiments"
    assert t.count(old3) == 1, "three-experiments sentence"
    t = t.replace(old3, "We resolve this decoupling with four controlled experiments", 1)
    if "(iv)" not in t:
        m3 = t.find(r"\item[(iii)] Tasks fall into a sensitivity spectrum")
        assert m3 > 0, "findings anchor"
        end = t.find(r"\end{itemize}", m3)
        assert end > m3, "findings end"
        t = t[:end] + FINDING4 + "\n" + t[end:]
    print("  fourth finding added")

    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written; length", len(t))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
