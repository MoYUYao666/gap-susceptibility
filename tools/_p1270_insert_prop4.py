# -*- coding: utf-8 -*-
r"""Item A: state the general form of the non-sufficiency result (no first-moment statistic is sufficient).

Proposition 1 covers the centroid gap. The same proof gives the general statement: any statistic that depends on a
representation only through the two empirical means cannot be a sufficient statistic for top-1, because a common
translation of the text embeddings moves the means and leaves every row ordering intact. The centroid gap, the
normalised gap and monotone transforms of either are instances.

    python tools/_p1270_insert_prop4.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

ANCHOR = r"""The practical consequence is that two laboratories can measure the same model, obtain gaps that differ by tens of
percent, and both be right: they are reading different prompt vocabularies. We test this directly: changing only the
prompt template on a fixed image set moves the centroid gap while leaving accuracy essentially unchanged, on every
backbone we tried (Section~\ref{sec:promptgap})."""

ADD = r"""

\begin{proposition}[No first-moment statistic is sufficient]
\label{prop:firstmoment}
Let $f$ be a statistic that depends on a representation only through the two empirical means,
$f=F(\bar x,\bar t)$. Unless $F$ does not depend on $\bar t$, $f$ is not a sufficient statistic for top-1: for every
representation $(X,T)$ and every $v\in\mathbb{R}^{d}$ the translated representation $(X,\{t_c+v\}_c)$ has the same
top-1 while $f$ evaluates to $F(\bar x,\bar t+v)$. The centroid gap, the normalised gap
$\mathrm{CG}/\|\bar t\|$ and every monotone transform of either are instances.
\end{proposition}

\begin{proof}
Text translation preserves every row ordering (Proposition~\ref{prop:nonsuff}) and hence top-1 and every top-$k$ set;
it moves $\bar t$ by exactly $v$. A statistic that changes while the quantity it is used to predict stays fixed cannot be
sufficient for that quantity.
\end{proof}

The proposition fixes the scope of the critique: it is not an accident of the centroid statistic. Any summary of the
first moments --- including the normalised and angular versions used in practice, and the mean part of distributional
variants --- inherits the same failure, because the failure lives in the difference between a mean and a decision rule,
not in the choice of norm.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    print(f"  anchor occurrences: {t.count(ANCHOR)}")
    assert t.count(ANCHOR) == 1
    assert "prop:firstmoment" not in t
    before = len(t)
    t = t.replace(ANCHOR, ANCHOR + ADD, 1)
    print(f"  length {before} -> {len(t)} (+{len(t) - before})")
    print(f"  present prop:firstmoment: {t.count('prop:firstmoment')}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
