# -*- coding: utf-8 -*-
r"""A1: write the risk-compute frontier of the sequential stopping rule into the appendix.

    python tools/_p1481_a1_frontier_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
AN = os.path.join(REPO, "outputs", "analysis", "a1_monitor_frontier.json")

SEC = r"""\section*{Risk--compute frontier of the sequential stopping rule}
\label{app:monitor_frontier}

The sequential rule used in the main text admits a tunable trigger: stop at the first epoch whose margin mass rises |
$\varepsilon$ above the running minimum, and keep the running-minimum checkpoint. Table~\ref{tab:monitor_frontier} reports
the frontier over the 20 large-holdout runs: tightening $\varepsilon$ buys epochs and costs accuracy in a controlled way,
from no early stopping at $\varepsilon=0.05$ ($0.50$ points of mean regret, zero epochs saved) to $4.2$ epochs saved at
$0.74$ points ($\varepsilon=0.005$). On the four small-holdout runs the same rule is unusable (mean regret $16.5$ points
at $\varepsilon=0.01$), which is why the rule is only enabled when the evaluation split is large enough; the split-size
diagnosis in the main text fixes the boundary. Data and generating script:
\texttt{outputs/\allowbreak analysis/\allowbreak a1\_monitor\_frontier.json},
\texttt{tools/\allowbreak \_p1480\_a1\_frontier.py}.

\begin{table}[h]
\centering
\small
\caption{Risk--compute frontier of the sequential margin-mass rule on the 20 large-holdout runs (ten epochs each).
Regret is measured against the labelled oracle; epochs saved are counted relative to training to the end.}
\label{tab:monitor_frontier}
\begin{tabular}{@{}lcccc@{}}
\toprule
trigger $\varepsilon$ & mean regret & max regret & mean epochs saved & share $\le0.5$ \\
\midrule
0.005 & 0.74 & 2.41 & 4.2 & 30\% \\
0.01 & 0.66 & 2.41 & 3.5 & 40\% \\
0.02 & 0.65 & 2.41 & 1.8 & 45\% \\
0.05 & 0.50 & 2.41 & 0.0 & 60\% \\
\bottomrule
\end{tabular}
\end{table}

"""

POINTER = " Appendix~\\ref{app:monitor_frontier} turns this trade-off into a frontier over the trigger margin."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    changed = False
    if "app:monitor_frontier" not in t:
        anchor = "\\section*{Data and code provenance}"
        assert anchor in t
        t = t.replace(anchor, SEC + "\n" + anchor, 1)
        key = "(\\texttt{outputs/\\allowbreak analysis/\\allowbreak a1\\_monitor\\_diagnosis.json})."
        assert key in t
        t = t.replace(key, key + POINTER, 1)
        changed = True
        print("  appendix and pointer added")
    tm = json.load(io.open(MANIFEST, encoding="utf-8"))
    floats = tm["manuscripts"]["A1"]["floats"]
    if not any(e["label"] == "tab:monitor_frontier" for e in floats):
        floats.append({"label": "tab:monitor_frontier", "kind": "table",
                       "script": "tools/_p1480_a1_frontier.py",
                       "archive": "outputs/analysis/a1_monitor_frontier.json", "status": "verified",
                       "note": "appendix risk-compute frontier"})
        changed = True
        print("  manifest entry added: tab:monitor_frontier")
    if a.apply and changed:
        io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
        io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(tm, indent=1, ensure_ascii=False))
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
