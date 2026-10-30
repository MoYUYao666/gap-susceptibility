# -*- coding: utf-8 -*-
r"""Add the three new A1 pieces: the random-direction control, the cross-model replication, and the boundary result.

1. Section 5.2 gains a control paragraph: 200 random directions translated to the same gap move top-1 by only 2.5 points,
   so the 33/52-point dissociation requires coherent transformations -- stated honestly, and it preempts the objection
   that the lambda pair was chosen post hoc.
2. Section 5.2 also gains the OpenCLIP replication (contraction reversal +19.4 points; return branch 27.1 points at a
   0.066 gap difference). The SigLIP path produced a broken baseline (1.86% zero-shot), so it is not reported.
3. A new subsection after "Mechanism: the class bias field" records the boundary of the first-order law: it keeps shape
   across four benchmarks (r = 0.93-0.99) but not level (best constant varies 0.36-0.98).
4. A short proposition in the Analysis section states non-sufficiency precisely.

Numbers come from outputs/analysis/a1_random_direction_gap.json, a1_matched_gap_crossmodel.json and
a1_closed_form_calibration.json / a1_crossbenchmark_closed_form.json.

    python tools/_p1215_add_a1_novelty_blocks.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

PROP = r"""
\textbf{Proposition (non-sufficiency of the gap).} Write $S = XT^{\top}$ for the image--text similarity matrix and
$\mathrm{top1}(X) = n^{-1}\sum_i \mathbb{1}[\arg\max_c S_{ic} = y_i]$. Then $\mathrm{top1}$ depends on $X$ only through
the ordering of each row of $S$. The centroid gap $\mathrm{CG}=\|\bar t-\bar x\|$ is not a function of those orderings:
configurations with $|\Delta \mathrm{CG}|\le 0.03$ can differ in top-1 by more than $30$ points (Section~\ref{sec:matchedgap}),
so no threshold on $\mathrm{CG}$ can be a sufficient health criterion for zero-shot classification. The construction is
not generic in the perturbation: random directions at the same gap move top-1 by only $2.5$ points, so the failure is
specific to coherent transformations of the kind fine-tuning applies (Section~\ref{sec:matchedgap}).

"""

CONTROL = r"""
\textbf{Is the matched pair an artefact of the chosen $\lambda$?} No selection is involved in the aggregation reported
next, but a single pair invites that objection, so we sampled it: $200$ random unit directions in image-embedding space
were each translated by the amount that restores the centroid gap to the frozen value, and top-1 was measured for every
member. The gap is matched tightly ($\mathrm{CG}=0.858\pm0.003$, maximum deviation $0.013$), and top-1 spans only
$57.0$--$59.5\%$ (mean $58.7\%$, frozen $59.1\%$): random perturbations that preserve the gap also preserve accuracy, to
$2.5$ points. The collapse reported above is therefore specific to \emph{coherent} shifts along one direction, which is
the regime a fine-tuning trajectory traverses; it is not a statement that every perturbation at a fixed gap destroys
classification. The order statistic separates the same ensemble where the gap cannot: $\tau$ ranges $0.70$--$0.90$
across the matched-gap members and correlates with their top-1 at $r=0.60$.

"""

CROSS = r"""
\textbf{Cross-model replication.} The same sweep on OpenCLIP laion2B reproduces both signatures. Class contraction
raises the gap ($0.791$ frozen to $1.187$ at $a=0.5$) and raises top-1 at the same time ($62.4\%\to 81.8\%$, $+19.4$
points against $+19.0$ on CLIP), and the return branch of the translation family again restores the gap while destroying
accuracy ($\lambda=0.5$: $\mathrm{CG}=0.394$, top-1 $55.6\%$; $\lambda=2$: $\mathrm{CG}=0.328$, top-1 $28.5\%$; a
$0.066$ gap difference carrying $27.1$ points). SigLIP base-patch16-224 could not be scored on this protocol---its
zero-shot ImageNet baseline came out at $1.86\%$, far below the published range, which indicates a broken text-tower path
in our harness rather than a property of the model---so we do not report a SigLIP row.

"""

BOUNDARY = r"""
\subsection{The first-order law keeps shape but not level across benchmarks}
\label{sec:boundary}

The class bias field above is evaluated on the data it is fitted to, so its agreement is self-consistency rather than
prediction: the \emph{exact} inversion condition reproduces the measured $\tau(\lambda)$ with $\mathrm{MAE}=0.0013$ and
$r=1.000$ precisely because it inverts the same per-image margins that define the measured $\tau$. Replacing the per-image
field by its aggregate form---$\tau(\lambda)=1-2\,\mathbb{E}[\bar\Phi(d/(|\lambda|\,\|g\|\,\sigma_b))]$, which needs only a
margin distribution and a bias scale---costs accuracy but is a genuine predictor, and it is wrong in level: $\mathrm{MAE}$
$0.115$, $r=0.987$, and top-1 off by $16.3$ points on average.

One constant repairs the level on the fitting benchmark: an effective scale $\sigma_{b,\mathrm{eff}}=k\sqrt{2}\sigma_m$
with $k=0.550$ lowers the $\tau$ error to $\mathrm{MAE}=0.017$. Frozen at that value and applied to four unrelated
benchmarks with their own gap directions, the law keeps its shape but not its level: $r=0.93$--$0.99$ everywhere, yet the
constant that each benchmark would prefer ranges over $0.36$--$0.98$ (rare-species $0.64$, iNat $0.36$, DTD $0.98$,
Food-101 $0.94$), with residual $\mathrm{MAE}$ $0.079$--$0.120$. The failure is structural and informative: at
$|\lambda|\ge2$ the measured $\tau$ becomes negative while the aggregate model saturates above zero, so what the closed
form lacks is the \emph{joint} margin--bias structure and not a better scalar. We therefore report the field as a
descriptive mechanism with a quantified boundary rather than as a predictive law, and we state the boundary explicitly
because it bounds what the mechanism can be used for.

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()

    # 1+2: extend the matched-gap subsection, before its figure
    anchor_fig = "\\begin{figure}[H]\n\\centering\n\\includegraphics[width=0.62\\textwidth]{figures/fig5_matched_gap.pdf}"
    if CONTROL.strip().split("\n")[0] not in t:
        n = t.count(anchor_fig)
        print(f"  matched-gap figure anchor: {n}")
        if n != 1:
            print("  !! anchor not unique")
            return 1
        t = t.replace(anchor_fig, CONTROL.lstrip("\n") + "\n" + CROSS.lstrip("\n") + "\n" + anchor_fig, 1)

    # 4: proposition at the end of the analysis section (before Setup)
    if "Proposition (non-sufficiency of the gap)" not in t:
        anchor_setup = "\\section{Setup}"
        n = t.count(anchor_setup)
        print(f"  Setup anchor: {n}")
        if n != 1:
            return 1
        t = t.replace(anchor_setup, PROP.lstrip("\n") + "\n" + anchor_setup, 1)

    # 3: boundary subsection after the bias-field mechanism subsection
    if "sec:boundary" not in t:
        anchor_scope = "\\subsection{Scope of the order-preservation statistic}"
        n = t.count(anchor_scope)
        print(f"  scope anchor: {n}")
        if n != 1:
            return 1
        t = t.replace(anchor_scope, BOUNDARY.lstrip("\n") + "\n" + anchor_scope, 1)

    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written; length", len(t))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
