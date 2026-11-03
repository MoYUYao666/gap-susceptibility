# -*- coding: utf-8 -*-
r"""Insert the final round: one characterization theorem, the statistic showdown table, and a robustness appendix.

Data read at build time:
  a1_statistic_showdown.json   correlations of CG / tau / margin mass with accuracy in classification and retrieval
  a1_robustness.json           half-sample stability, binomial interval, trajectory correlations

    python tools/_p1310_insert_final_round.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
AN = os.path.join(REPO, "outputs", "analysis")


def load(name):
    return json.load(io.open(os.path.join(AN, name), encoding="utf-8"))


def n(x, nd=3):
    return ("{:." + str(nd) + "f}").format(float(x))


THEOREM = r"""
\begin{theorem}[Characterization: when the gap can be a health metric]
\label{thm:characterization}
Fix a representation and its top-1 rule. Then:
(i) top-1 depends only on the ordering of the entries within each row of the similarity matrix, whereas every statistic
that depends only on the two empirical means---the centroid gap and all its monotone transforms---is invariant under a
common translation of the text side; no such statistic is therefore a sufficient statistic for top-1
(Propositions~\ref{prop:nonsuff} and~\ref{prop:firstmoment}).
(ii) for an intervention whose class-wise score spread is bounded by $\varepsilon$, a prediction can change only if its
margin satisfies $m_i\le2\varepsilon$; the fraction of predictions an adversary can change while leaving every empirical
mean unchanged is therefore the margin mass $M(\varepsilon)=n^{-1}\#\{i:m_i\le2\varepsilon\}$
(Proposition~\ref{prop:margin}).
(iii) that bound is attained: there is a zero-mean image perturbation of magnitude $c$ that leaves the centroid gap exactly
unchanged and changes top-1 by $M(cL)$, with $L=\max_c\|t_c-\bar t\|$ (Proposition~\ref{prop:lowerbound}).
Together (i)--(iii) say that a first-moment summary is a valid health metric exactly on interventions that are class-neutral,
and that the correct certificate in the general case is the margin mass, not the moment.
\end{theorem}

\begin{proof}
Part (i) is Proposition~\ref{prop:nonsuff} (text translation) combined with Proposition~\ref{prop:firstmoment} (no
first-moment statistic is sufficient). Part (ii) is the margin bound of Proposition~\ref{prop:margin} together with the
observation that all such statistics are unchanged by construction. Part (iii) is the perturbation constructed in
Proposition~\ref{prop:lowerbound}.
\end{proof}

"""

SHOWDOWN = r"""\subsection{Which statistic to monitor? A head-to-head comparison}
\label{sec:showdown}

Theorem~\ref{thm:characterization} settles what a first moment can and cannot certify, but it does not say which substitute
to use. We therefore compare the three candidates on the same frozen model and the same evaluation data, in two task
regimes: the classification families of Section~\ref{sec:matchedgap} and the image--caption retrieval set of
Section~\ref{sec:retrieval}. Table~\ref{tab:showdown} reports the Pearson correlation of each statistic with the measured
accuracy across the pooled configurations of each regime.

\begin{table}[t]
\centering
\small
\caption{Correlation of each candidate statistic with accuracy, measured on the same configurations. Classification:
17 configurations from the three perturbation families on ImageNet-5k. Retrieval: 17 configurations of the same families
on 536 image--caption pairs. The margin mass $M(\varepsilon)$ is the certificate of Theorem~\ref{thm:characterization};
$\tau_5$ is the Kendall order statistic. Source: \texttt{outputs/\allowbreak analysis/\allowbreak
a1\_statistic\_showdown.json}.}
\label{tab:showdown}
\begin{tabular}{lcc}
\toprule
statistic & classification ($r$) & retrieval ($r$) \\
\midrule
centroid gap $\mathrm{CG}$ & $-0.154$ & $-0.223$ \\
order statistic $\tau_5$ & $+0.832$ & $-0.143$ \\
margin mass $M(0.01)$ & $\mathbf{-0.996}$ & $\mathbf{-0.970}$ \\
margin mass $M(0.02)$ & $-0.988$ & $-0.921$ \\
\bottomrule
\end{tabular}
\end{table}

The ordering is unambiguous in both regimes: the gap is the weakest statistic in each, the order statistic is informative
for classification but does not transfer to retrieval, and the margin mass is the strongest in both, at $r=-0.996$ and
$r=-0.970$. This is the empirical counterpart of Theorem~\ref{thm:characterization}: $\tau$ measures how much the ordering
moved, whereas the margin mass counts the rows for which a move can change a decision, which is what both the
classification and the retrieval rule actually depend on. The margin mass requires no labels, only the similarity matrix a
validation pass already produces.

The trajectory regime is not comparable in the same table: on the two full per-epoch trajectories top-1 moves by less than
one point while $\tau$ falls, so neither CG nor $\tau$ correlates with it in a way that isolates the statistic
(see the robustness appendix). We therefore report the trajectory evidence as the epoch-by-epoch correlations of
Section~\ref{sec:epoch_sweep} rather than as a row of this table.

"""

ROBUST = r"""\subsection{Robustness checks}
\label{app:robustness}

Four checks probe the stability of the headline numbers (\texttt{outputs/\allowbreak analysis/\allowbreak
a1\_robustness.json}).

\emph{Half-sample stability.} The matched-gap sweep on CLIP ViT-B/32 is repeated on two disjoint halves of the
5{,}000-image sample (2{,}500 images each, same perturbation grid): the widest spread at $|\Delta\mathrm{CG}|\le0.03$ is
32.7 points on the first half and 32.6 on the second, against 32.7 on the full sample. The dissociation is not carried by
a subset of images.

\emph{Sampling uncertainty of the real-checkpoint pair.} Treating each top-1 as a proportion over the 5{,}000-image holdout,
the widest real pair (6.64 points) has a standard error of 0.99 points and a 95\,\% interval of $[4.70,8.58]$
($z=6.7$); the difference is not a sampling artefact.

\emph{Template dependence of the order statistic.} Across the ten prompt templates and five backbones of
Section~\ref{sec:promptgap}, $\tau_5$ against the reference template never exceeds 1 and falls to $0.54$ in the worst case,
while the accuracy range stays below 5 points. An order statistic quoted without its reference template is therefore as
ambiguous as a gap quoted without its prompt vocabulary.

\emph{Scale dependence of the margin mass.} The mass is defined at a scale $\varepsilon$; at $\varepsilon\ge0.05$ essentially
every row falls below the threshold and the statistic saturates. It is reported as a curve rather than as a single number,
and in Table~\ref{tab:showdown} at the two scales where it discriminates ($\varepsilon=0.01$ and $0.02$).

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    sd = load("a1_statistic_showdown.json")
    rb = load("a1_robustness.json")

    # 1. theorem environment
    if r"\newtheorem{theorem}" not in t:
        anchor = r"\newtheorem{corollary}{Corollary}"
        assert t.count(anchor) == 1
        t = t.replace(anchor, anchor + "\n" + r"\newtheorem{theorem}{Theorem}", 1)

    # 2. theorem block at the head of the theory section
    anchor = ("The controls in this paper are instances of one structural fact, which we state once and then use throughout.")
    assert t.count(anchor) == 1
    t = t.replace(anchor, THEOREM + anchor, 1)

    # 3. showdown before the monitoring protocol
    anchor = r"\subsection{A label-free monitoring protocol}"
    assert t.count(anchor) == 1
    t = t.replace(anchor, SHOWDOWN + "\n" + anchor, 1)

    # 4. robustness appendix before the graphical abstract
    anchor = r"\subsection{Graphical abstract}"
    assert t.count(anchor) == 1
    t = t.replace(anchor, ROBUST + "\n" + anchor, 1)

    for token in ("thm:characterization", "sec:showdown", "app:robustness", "tab:showdown"):
        print(f"  present {token!r}: {t.count(token)}")
    print(f"  classification corr: {sd['correlation_with_top1']['classification']}")
    print(f"  retrieval corr: {sd['correlation_with_top1']['retrieval']}")
    print(f"  half-sample: {rb['half_sample']['first']['widest_spread_at_0.03']:.1f} / "
          f"{rb['half_sample']['second']['widest_spread_at_0.03']:.1f}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
