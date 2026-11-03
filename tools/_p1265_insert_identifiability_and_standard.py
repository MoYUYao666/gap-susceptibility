# -*- coding: utf-8 -*-
r"""Insert the identifiability proposition (item 3) and the minimum-reporting standard (item 7).

Item 3: Proposition 1 shows a text-side translation moves the gap and leaves accuracy invariant. Read as an
identifiability statement, it says the gap is confounded by anything that moves the text representation without moving
the decision rule - prompt wording, class-name vocabulary, template choice. Proposition 3 states this, with the
corollary that a gap reading is not attributable to the image side unless the text side is held fixed and reported.

Item 7: a five-item minimum-reporting standard for gap-based monitoring claims, as a table in the Discussion.

    python tools/_p1265_insert_identifiability_and_standard.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

PROP3_ANCHOR = r"""\begin{proposition}[The gap does not bound accuracy]"""
PROP3 = r"""\begin{proposition}[Text-side confound]
\label{prop:confound}
The map $(X,T)\mapsto(\mathrm{CG},\mathrm{top1})$ is not jointly identifiable from the gap alone: for every prompt
vocabulary $T$ and every text-side translation $v$ there is a representation $(X,T+v)$ with $\mathrm{top1}$ unchanged
and $\mathrm{CG}$ changed by an amount that depends on $v$ and on the image mean alone. Hence a reading of
$\mathrm{CG}$ cannot be attributed to the image side unless the text side is held fixed and reported.
\end{proposition}

\begin{proof}
Case $v$ uniform across classes is Proposition~\ref{prop:nonsuff}: row orderings, top-1 and $\tau$ are invariant while
$\mathrm{CG}=\|\bar t+v-\bar x\|$ moves. A prompt or vocabulary change is an instance of such a text-side map whenever it
shifts all class embeddings coherently; when it does not, the change moves both the ordering and the gap, and the gap
reading is confounded rather than merely uninformative. In neither case does the gap identify the image-side component.
\end{proof}

The practical consequence is that two laboratories can measure the same model, obtain gaps that differ by tens of
percent, and both be right: they are reading different prompt vocabularies. We test this directly: changing only the
prompt template on a fixed image set moves the centroid gap while leaving accuracy essentially unchanged, on every
backbone we tried (Section~\ref{sec:promptgap}).

"""

STANDARD_ANCHOR = r"\section{Conclusion}"
STANDARD = r"""
\subsection*{A minimum reporting standard}
\label{sec:standard}

The controls above are cheap, and the failure they detect is silent: a gap number looks plausible whatever family it was
measured in. We therefore close with the minimum we would expect a gap-based monitoring claim to report, in the spirit of
checklists already used for prediction models. None of the five items requires new experiments; all are computable from
records a careful study already has.

\begin{table}[H]
\centering
\small
\caption{Minimum reporting standard for a gap-based monitoring claim. The right column states the failure that the item
is designed to expose.}
\label{tab:standard}
\begin{tabular}{p{0.34\textwidth}p{0.60\textwidth}}
\toprule
report & what it exposes \\
\midrule
The gap together with an order statistic (e.g.\ $\tau$ on top-$k$ sets) & a first-moment number that happens to be
uncorrelated with the decision rule \\
Prompt template and class vocabulary, and whether they changed between measurements & a text-side drift counted as
image-side damage (Proposition~\ref{prop:confound}) \\
A matched-gap control across at least two perturbation families & a correlation that is carried by the family, not by
the gap \\
The benchmark and model family on which any threshold was calibrated & a threshold that does not transfer
(Section~\ref{sec:thresholds}) \\
Per-run records and the script that produced each number & a gap change that cannot be attributed to a known
intervention \\
\bottomrule
\end{tabular}
\end{table}

A study that reports the first item only is not making a smaller claim than one that reports all five; it is making an
unfalsifiable one.

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    before = len(t)

    assert "\\label{prop:confound}" not in t, "already inserted"
    k = t.find(PROP3_ANCHOR)
    print(f"  proposition-2 anchor: {k}")
    assert k > 0
    t = t[:k] + PROP3 + t[k:]

    assert "\\label{sec:standard}" not in t, "standard already inserted"
    k = t.find(STANDARD_ANCHOR)
    print(f"  conclusion anchor: {k}")
    assert k > 0
    t = t[:k] + STANDARD + t[k:]

    for token in ("prop:confound", "sec:promptgap", "sec:thresholds", "tab:standard"):
        print(f"  present {token!r}: {t.count(token)}")
    print(f"  length {before} -> {len(t)} (+{len(t) - before})")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
