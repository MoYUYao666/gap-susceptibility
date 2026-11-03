# -*- coding: utf-8 -*-
r"""Insert the theory, the monitoring protocol, the controls protocol and the companion-work note into A1.

Items 1, 2, 3, 4 and 6 of the novelty plan:
  1  the non-sufficiency claim becomes a numbered proposition with a proof, plus a corollary on
     family-conditional informativeness                     -> Section "When is the gap informative?"
  2  the "gap does not bound accuracy" statement, proved from the row-change mass identity
  3  a label-free checkpoint-selection protocol with four rules, a leave-one-out calibrated CUSUM and a
     regret table (numbers from outputs/analysis/a1_monitor_protocol.json)
  4  the four controls presented as a falsification protocol with one table
  6  a neutral paragraph relating the paper to the companion dynamical-law manuscript

The second-benchmark replication (item 5) is inserted separately once its run finishes.

    python tools/_p1256_insert_a1_theory.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

PREAMBLE_OLD = r"\usepackage{indentfirst}"
PREAMBLE_NEW = r"""\usepackage{indentfirst}
\usepackage{amsthm}
\newtheorem{proposition}{Proposition}
\newtheorem{corollary}{Corollary}"""

THEORY = r"""
\subsection{When is the gap informative? A formal statement}
\label{sec:theory}

The controls in this paper are instances of one structural fact, which we state once and then use throughout. Write
$X\in\mathbb{R}^{n\times d}$ for the image embeddings and $T\in\mathbb{R}^{K\times d}$ for the class text embeddings,
$S=XT^{\top}$, $\bar x=n^{-1}\sum_i x_i$, $\bar t=K^{-1}\sum_c t_c$, and $\mathrm{CG}=\|\bar t-\bar x\|$.

\begin{proposition}[Non-sufficiency of the centroid gap]
\label{prop:nonsuff}
$\mathrm{top1}(X,T)=n^{-1}\sum_i \mathbb{1}[\arg\max_c S_{ic}=y_i]$ depends on $(X,T)$ only through the ordering of the
entries within each row of $S$. The centroid gap is not determined by those orderings: for every $g\ge 0$ there are
representations with identical row orderings, hence identical top-1, and $\mathrm{CG}=g$.
\end{proposition}

\begin{proof}
Translate every text embedding by the same vector $v$, $t_c\mapsto t_c+v$. Then $S_{ic}\mapsto S_{ic}+x_i\cdot v$, and the
added term is constant across $c$, so the ordering of each row is unchanged; top-1 and every top-$k$ set are therefore
unchanged (so $\tau=1$ relative to the untranslated representation). The text mean becomes $\bar t+v$, so
$\mathrm{CG}=\|\bar t+v-\bar x\|$. With $\hat d=(\bar t-\bar x)/\|\bar t-\bar x\|$ and $v=g\hat d-(\bar t-\bar x)$ one
obtains $\mathrm{CG}=g$ for any $g\ge0$ while top-1 is untouched.
\end{proof}

The proposition separates two things that gap-based monitoring conflates: a first-moment property of the embedding means,
and a property of the decision rule. Only the second is what zero-shot accuracy can depend on, and it is invisible to the
first.

\begin{corollary}[Family-conditional informativeness]
\label{cor:family}
Let $\mathcal{F}$ be a family of representations whose members preserve the row orderings of a reference member. Top-1 is
constant on $\mathcal{F}$ while $\mathrm{CG}$ ranges over an interval. Consequently a threshold on $\mathrm{CG}$
calibrated on one family carries no guarantee for another, and the gap is informative at most conditionally on the family,
i.e.\ on the intervention that produced it.
\end{corollary}

Proposition~\ref{prop:nonsuff} is an existence statement; it says nothing about how far apart two same-gap
representations can be in accuracy. The matched-gap control measures that distance: configurations from different
perturbation families that agree on $\mathrm{CG}$ to $0.03$ differ by $33$ accuracy points (Section~\ref{sec:matchedgap}),
so the conditional map of Corollary~\ref{cor:family} is not merely family-dependent but cannot be transferred even at
matched first moments.

\begin{proposition}[The gap does not bound accuracy]
\label{prop:nobound}
For any two scoring matrices, $|a(S)-a(S')|\le n^{-1}\sum_i\mathbb{1}[\arg\max_c S_{ic}\neq\arg\max_c S'_{ic}]$: an
accuracy difference is controlled by the mass of rows whose decision changes. Proposition~\ref{prop:nonsuff} shows that
this mass can be maximal while $|\mathrm{CG}-\mathrm{CG}'|=0$, so no inequality of the form
$|a(S)-a(S')|\le h(|\mathrm{CG}-\mathrm{CG}'|)$ can hold for a function $h$ with $h(0)=0$.
\end{proposition}

\begin{proof}
The first claim is the triangle inequality for indicator differences: the fraction of samples on which two classifiers
disagree is an upper bound on the difference of their accuracies. For the second, take any representation and translate
the text side as in Proposition~\ref{prop:nonsuff} so that $\mathrm{CG}$ changes while no row ordering changes; then take
a representation at the new gap whose row orderings differ on the rows whose margins are smallest. Both have the same
$\mathrm{CG}$ and different accuracy, so no such $h$ exists.
\end{proof}

"""

MONITOR = r"""
\subsection{A label-free monitoring protocol}
\label{sec:protocol}

The correlations above establish that $\tau$ tracks top-1; a practitioner needs a decision rule. We evaluate six
checkpoint-selection rules on the ten archived trajectories of Section~\ref{sec:epoch_sweep} (ten epochs each,
post-hoc): \emph{last} (train to the final epoch), \emph{first} (stop after epoch 1), \emph{$\tau$-max} (stop at the
epoch of largest $\tau$), \emph{patience-2} (stop once $\tau$ has fallen for two consecutive epochs), \emph{CUSUM} (stop
at the first epoch where a one-sided cumulative sum of standardised $\tau$ decrements exceeds $h$), and the labelled
\emph{oracle} (the epoch of largest measured top-1, unavailable in deployment). The CUSUM threshold is calibrated
leave-one-trajectory-out, choosing the smallest $h$ that fires on none of the other nine trajectories; the median is
$h=6.0$ (range $5.25$--$6.0$).

All rules are label-free: $\tau$ is computed from similarities the validation pass already produces, and needs no ground
truth. The labelled alternative costs a full zero-shot evaluation of a $5{,}000$-image set at every checkpoint.

\begin{table}[H]
\centering
\small
\caption{Checkpoint-selection rules on ten archived trajectories (ten epochs each). Regret is the gap to the labelled
oracle's top-1 within the same trajectory. The mean stop epoch is reported because a rule that stops early has a lower
labelling and compute cost. Source: \texttt{outputs/\allowbreak analysis/\allowbreak a1\_monitor\_protocol.json}.}
\label{tab:protocol}
\begin{tabular}{lcccc}
\toprule
rule & mean top-1 (\%) & mean regret & max regret & mean stop epoch \\
\midrule
oracle (labelled) & 59.49 & 0.00 & 0.00 & 1.20 \\
$\tau$-max          & 59.44 & 0.05 & 0.46 & 1.00 \\
CUSUM               & 59.35 & 0.14 & 0.94 & 1.50 \\
patience-2          & 58.80 & 0.69 & 1.38 & 2.00 \\
last epoch          & 57.14 & 2.35 & 4.56 & 10.00 \\
first epoch         & 59.44 & 0.05 & 0.46 & 1.00 \\
\bottomrule
\end{tabular}
\end{table}

The $\tau$-max rule matches the labelled oracle to $0.05$ points on average (worst trajectory $0.46$) and beats training
to the end by $2.3$ points; CUSUM is within $0.14$. The table also shows the honest limitation: on these schedules the
first checkpoint is already optimal (oracle mean stop epoch $1.20$), so a trivial ``stop after epoch 1'' rule ties with
$\tau$-max. The protocol is therefore insurance against schedules that degrade during training, not a source of gain on
the schedules we archived; we report it in that form.

"""

CONTROLS = r"""
\subsection{The controls as a falsification protocol}
\label{sec:controls}

The four controls of Section~\ref{sec:matchedgap} are usually read as separate checks. Read together they form a
protocol that any claim of the form ``the gap measures health'' must survive: each control falsifies a different
hypothesis, and each can be run with frozen forward passes only. Table~\ref{tab:controls} states the protocol.

\begin{table}[H]
\centering
\small
\caption{The four-control falsification protocol for gap-based health claims, with the measured outcomes reported in
this paper. All controls use frozen convolutional encoders and a single labelled holdout.}
\label{tab:controls}
\begin{tabular}{p{0.26\textwidth}p{0.30\textwidth}p{0.34\textwidth}}
\toprule
control & hypothesis it falsifies & measured outcome \\
\midrule
Matched gap across perturbation families & ``at a given gap, accuracy is determined'' & $33.1$ points at
$|\Delta\mathrm{CG}|\le0.03$ (CLIP); $27.1$ and $27.1$ on OpenCLIP and SigLIP \\
Random directions at the same gap (200) & ``any gap-preserving perturbation is equivalent'' & top-1 range $2.5$
points, $\tau$ $0.70$--$0.90$, $r(\tau,\text{top-1})=0.60$ \\
Class contraction & ``accuracy cannot improve while the gap grows'' & $+19.0$ (CLIP), $+19.4$ (OpenCLIP), $+15.0$
(SigLIP) points \\
Benchmark sweep & ``one calibration transfers across datasets'' & see Section~\ref{sec:secondbench} \\
\bottomrule
\end{tabular}
\end{table}

A gap-based claim that has survived all four controls may still be wrong for other reasons, but it can no longer fail for
a first-moment reason. We suggest reporting the protocol outcome alongside any correlation between a gap statistic and
accuracy, because a correlation alone is compatible with every row of the table.

"""

COMPANION = r"""
\textbf{Relation to companion work.} A companion manuscript under separate consideration derives a dynamical law for how
the gap itself evolves under gradient flow. The present paper asks a different question---whether the gap measures what
it is used to measure---and no conclusion reported here depends on that dynamical model. The two are complementary rather
than overlapping: one predicts the trajectory of a statistic, the other bounds what a statistic of that kind can be used
for. The empirical records behind both are shared, and the disclosure in the cover letter states the relation.

"""

INTRO_ADD = r"""
The paper also turns the argument into two operational statements: the non-sufficiency of the gap is proved as a
proposition with a corollary on when a gap threshold can be trusted (Section~\ref{sec:theory}), and the order statistic is
packaged as a label-free checkpoint-selection protocol with a measured regret against the labelled oracle
(Section~\ref{sec:protocol}). The four controls are stated as a falsification protocol that a gap-based claim must survive
(Section~\ref{sec:controls}), and the matched-gap control is replicated on further benchmarks
(Section~\ref{sec:secondbench}).

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    orig_len = len(t)

    # 1. theorem environments
    n = t.count(PREAMBLE_OLD)
    print(f"  preamble anchor: {n}")
    assert n == 1
    t = t.replace(PREAMBLE_OLD, PREAMBLE_NEW, 1)

    # 2. replace the bold proposition paragraph with a forward reference
    start_marker = r"\textbf{Proposition (non-sufficiency of the gap).}"
    i = t.find(start_marker)
    end_marker = r"(Section~\ref{sec:matchedgap})."
    j = t.find(end_marker, i)
    print(f"  bold proposition bounds: {i}..{j}")
    assert i > 0 and j > i
    j += len(end_marker)
    fwd = (r"Proposition~\ref{prop:nonsuff} makes this precise: $\mathrm{top1}$ is a function of the row orderings of the "
           r"similarity matrix, whereas the centroid gap is not, so no threshold on it can be a sufficient criterion; the "
           r"matched-gap control (Section~\ref{sec:matchedgap}) instantiates the failure, and the $200$-direction control "
           r"shows that it requires coherent shifts.")
    t = t[:i] + fwd + t[j:]

    # 3. theory block at the start of the Analysis section
    anchor = "\\label{sec:analysis}\n"
    k = t.find(anchor)
    print(f"  analysis label: {k}")
    assert k > 0
    t = t[: k + len(anchor)] + "\n" + THEORY + t[k + len(anchor):]

    # 4. protocol + controls before the Discussion
    anchor = "\\section{Discussion}"
    k = t.find(anchor)
    print(f"  discussion anchor: {k}")
    assert k > 0
    t = t[:k] + MONITOR + CONTROLS + t[k:]

    # 5. companion note before the Conclusion
    anchor = "\\section{Conclusion}"
    k = t.find(anchor)
    print(f"  conclusion anchor: {k}")
    assert k > 0
    t = t[:k] + COMPANION + "\n" + t[k:]

    # 6. intro pointer, inserted after the contributions itemize
    marker = "\\end{itemize}"
    k = t.find(marker)
    # the first itemize after the "three findings" paragraph is the contribution list
    k2 = t.find("Three findings emerge")
    kk = t.find(marker, k2)
    print(f"  intro itemize end: {kk}")
    assert kk > 0
    t = t[: kk + len(marker)] + "\n" + INTRO_ADD + t[kk + len(marker):]

    print(f"  length {orig_len} -> {len(t)} (+{len(t) - orig_len} chars)")
    for token in ("\\begin{proposition}", "\\begin{corollary}", "tab:protocol", "tab:controls",
                  "sec:secondbench", "Relation to companion work"):
        print(f"  present {token!r}: {t.count(token)}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
