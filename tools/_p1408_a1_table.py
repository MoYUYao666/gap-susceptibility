# -*- coding: utf-8 -*-
r"""A1: add a compact table of stopping-rule regret by held-out size to the monitoring section.

    python tools/_p1408_a1_table.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json

MAIN = "paper_a1/main.tex"
JSON = "outputs/analysis/a1_monitor_split_diagnosis.json"
ANCHOR = ("selection statistic for evaluations large enough to resolve it, not a universal stopping rule, and it buys\n"
          "early stopping rather than an accuracy gain.")

TABLE = r"""

Table~\ref{tab:monitor_regret} collects the rule regrets by held-out size.

\begin{table}[t]
\centering
\small
\caption{Stopping-rule regret (mean points from the labelled oracle) stratified by held-out size. Large: 353--1212
images (16 runs); small: 60--144 images (4 runs). The certificate rule selects the epoch by the smallest margin mass; the
sequential variant uses only the epochs seen so far.}
\label{tab:monitor_regret}
\begin{tabular}{@{}lcc@{}}
\toprule
rule & large holdout & small holdout \\
\midrule
minimum margin mass & 0.58 & 6.18 \\
last epoch & 0.52 & 4.51 \\
first epoch & 3.55 & 22.05 \\
minimum centroid gap & 1.45 & 3.65 \\
sequential minimum mass & 0.64 & 16.53 \\
\bottomrule
\end{tabular}
\end{table}"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    if "tab:monitor_regret" in t:
        print("  table already present")
        return 0
    assert t.count(ANCHOR) == 1, t.count(ANCHOR)
    t = t.replace(ANCHOR, ANCHOR + TABLE, 1)
    print("  table inserted")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
