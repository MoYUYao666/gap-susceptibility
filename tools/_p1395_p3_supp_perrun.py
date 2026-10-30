# -*- coding: utf-8 -*-
r"""P3: add a per-run table to the supplement (every re-run with its full energy trajectory).

    python tools/_p1395_p3_supp_perrun.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

SUPP = os.path.join("paper3", "paper_ieee", "supplementary", "supplementary.tex")
BASE = os.path.join("outputs", "analysis", "p3_rerun_protocol.json")
EXTRA = os.path.join("outputs", "analysis", "p3_rerun_extra.json")
ANCHOR = "\\bibliographystyle{IEEEtran}"
HEAD = "\\section{Per-Run Energy Trajectories}"
LABEL = "tab:supp-perrun"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    runs = {}
    for p in (BASE, EXTRA):
        if os.path.exists(p):
            d = json.load(io.open(p, encoding="utf-8"))
            for k, v in d["runs"].items():
                if v.get("ok"):
                    runs[k] = v
    order = sorted(runs, key=lambda k: (int(k[1:].split("_")[0]), int(k.split("s")[-1])))
    rows = []
    for k in order:
        v = runs[k]
        E = v["E"]
        rank = int(k[1:].split("_")[0])
        seed = int(k.split("_s")[-1])
        rows.append("%d & %d & %s & %+.1f \\\\" % (
            rank, seed, " & ".join("%.1f" % x for x in E[:4]), v["delta_E"]))
    sec = r"""
\section{Per-Run Energy Trajectories}
\label{sec:supp-perrun}

Table~\ref{tab:supp-perrun} lists every run of the current-protocol re-run individually, so the aggregate in
Table~\ref{tab:supp-rerun} can be checked run by run. All runs use the same script defaults (20 samples, 16 train / 4 eval,
lr $5\times10^{-5}$, three epochs) and differ only in rank and seed.

\begin{table}[h]
\centering
\caption{Per-run energy trajectories on the current protocol.}
\label{tab:supp-perrun}
\begin{tabular}{@{}lrrrrrr@{}}
\toprule
Rank & Seed & $E(0)$ & $E(1)$ & $E(2)$ & $E(3)$ & $\Delta E$ \\
\midrule
%s
\bottomrule
\end{tabular}
\end{table}

""" % "\n".join(rows)
    t = io.open(SUPP, encoding="utf-8").read()
    if HEAD in t:
        # replace existing section block up to the bibliography
        i = t.find(HEAD)
        j = t.find(ANCHOR, i)
        t = t[:i] + sec.strip("\n") + "\n\n" + t[j:]
        print("  section regenerated")
    else:
        assert t.count(ANCHOR) == 1
        t = t.replace(ANCHOR, sec.strip("\n") + "\n\n" + ANCHOR, 1)
        print("  section inserted")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
