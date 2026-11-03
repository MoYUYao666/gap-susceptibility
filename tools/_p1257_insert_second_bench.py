# -*- coding: utf-8 -*-
r"""Insert the second-benchmark replication (item 5) into A1 and fill the controls table's last row.

Numbers come from outputs/analysis/a1_matched_gap_second_dataset.json (frozen CLIP ViT-B/32, identical protocol):
  DTD       47 classes, 5,000 images, frozen CG 1.019, top-1 41.62 %
  Food-101 101 classes, 5,000 images, frozen CG 0.953, top-1 80.64 %
  largest top-1 spread at |dCG| <= 0.03: 10.1 (DTD), 12.1 (Food-101)
  largest top-1 spread at |dCG| <= 0.05: 15.1 (DTD), 42.1 (Food-101), the latter inside the T family
  class contraction: 41.62 -> 59.42 (+17.8) with CG 1.019 -> 1.069 (DTD);
                     80.64 -> 98.80 (+18.2) with CG 0.953 -> 1.003 (Food-101)

    python tools/_p1257_insert_second_bench.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

SECTION = r"""
\subsection{Replication on further benchmarks}
\label{sec:secondbench}

The control above uses ImageNet-5k, so the dissociation could be a property of that benchmark. We therefore repeat the
identical protocol---the same frozen CLIP ViT-B/32, the same three perturbation families, the same definition of the
centroid gap---on two locally available benchmarks: DTD ($47$ classes, $5{,}000$ images; frozen $\mathrm{CG}=1.019$,
top-1 $41.62\,\%$) and Food-101 ($101$ classes, $5{,}000$ images; frozen $\mathrm{CG}=0.953$, top-1 $80.64\,\%$).

The dissociation reappears on both, and at comparable magnitudes. At $|\Delta\mathrm{CG}|\le0.03$ the largest top-1 spread
is $10.1$ points on DTD and $12.1$ points on Food-101; at $|\Delta\mathrm{CG}|\le0.05$ it is $15.1$ and $42.1$ points
(\texttt{outputs/\allowbreak analysis/\allowbreak a1\_matched\_gap\_second\_dataset.json}). On Food-101 the widest
matched pair lies inside a single family: the $\lambda=0.5$ and $\lambda=2.0$ translations have gaps $0.482$ and $0.447$
($\Delta\mathrm{CG}=0.034$) and top-1 $71.7\,\%$ and $29.6\,\%$, so a $3.4\,\%$ change of the first moment accompanies a
$42$-point change of accuracy.

The contraction family reverses again on both benchmarks: DTD moves from $41.62\,\%$ to $59.42\,\%$ ($+17.8$ points) while
the gap grows from $1.019$ to $1.069$, and Food-101 moves from $80.64\,\%$ to $98.80\,\%$ ($+18.2$ points) while the gap
grows from $0.953$ to $1.003$. Accuracy improves as the gap grows, as it does on all three ImageNet architectures
(Section~\ref{sec:matchedgap}).

What does not replicate is the level. The same family parameter produces different gaps on different benchmarks---the
frozen gap is $1.019$ on DTD, $0.953$ on Food-101 and $0.855$ on ImageNet-5k---so an absolute threshold fitted on one
benchmark cannot be carried to another. That is the benchmark-level counterpart of the family dependence in
Corollary~\ref{cor:family}: the gap is informative, if at all, conditionally on the benchmark and on the intervention
that produced it.

"""

CONTROLS_OLD = r"""Benchmark sweep & ``one calibration transfers across datasets'' & see Section~\ref{sec:secondbench} \\"""

CONTROLS_NEW = r"""Benchmark sweep & ``one calibration transfers across datasets'' & $10.1$ (DTD) and $12.1$ (Food-101)
points at $|\Delta\mathrm{CG}|\le0.03$; $15.1$ and $42.1$ at $0.05$ \\"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    before = len(t)

    anchor = "\\section{Discussion}"
    k = t.find(anchor)
    print(f"  discussion anchor: {k}")
    assert k > 0
    assert "\\label{sec:secondbench}" not in t, "already inserted"
    t = t[:k] + SECTION + t[k:]

    n = t.count(CONTROLS_OLD)
    print(f"  controls last row: {n}")
    assert n == 1
    t = t.replace(CONTROLS_OLD, CONTROLS_NEW, 1)

    for token in ("sec:secondbench", "10.1", "42.1", "17.8", "18.2"):
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
