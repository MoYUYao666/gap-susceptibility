# -*- coding: utf-8 -*-
r"""P3 supplement: replace the two-column-incompatible longtable with a table* provenance table and add table refs.

    python tools/_p1470_p3_supp_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")


def rows(manuscript):
    d = json.load(io.open(MANIFEST, encoding="utf-8"))
    out = []
    for e in sorted(d["manuscripts"][manuscript]["floats"], key=lambda x: x["label"]):
        sc = (e.get("script") or "--").replace("\\", "/")
        arcs = e.get("archives") or ([e["archive"]] if e.get("archive") else [])
        arc = ", ".join(os.path.basename(a) for a in arcs if a) or "--"
        lab = e["label"].replace("_", "\\_")
        out.append("\\raggedright %s & \\raggedright\\path{%s} & \\raggedright\\path{%s} & \\texttt{%s} \\\\"
                   % (lab, sc, arc, e["status"]))
    return out


BLOCK = r"""\section{Data and code provenance}
\label{app:provenance}

This appendix lists, for every table (T) and figure (F) that reports our own results, the generating script and the
result archive (file names; full relative paths in the repository).

\begin{table*}[h]
\centering
\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}p{0.22\textwidth}p{0.28\textwidth}p{0.26\textwidth}l@{}}
\toprule
item & generating script & result archive & status \\
\midrule
%s
\bottomrule
\end{tabular}
\end{table*}

"""


def add_ref(t, label, sentence):
    if "Table~\\ref{%s}" % label in t:
        return t, False
    i = t.find("\\label{%s}" % label)
    assert i >= 0, label
    j = t.find("\n", i)
    return t[:j + 1] + "\n" + sentence + "\n" + t[j + 1:], True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(SUPP, encoding="utf-8").read()
    changed = False
    start = t.find("\\section{Data and code provenance}")
    assert start >= 0
    if "longtable" in t[start:start + 3000]:
        end = t.find("\\endgroup", start)
        assert end > start
        end += len("\\endgroup")
        t = t[:start] + (BLOCK % "\n".join(rows("P3"))) + t[end:]
        changed = True
        print("  S13 longtable replaced by table*")
    t, c = add_ref(t, "app:seed5", "Table~\\ref{tab:seed5} lists the per-seed values used in this section.")
    changed |= c
    if c:
        print("  S14 table reference added")
    t, c = add_ref(t, "app:numsamples", "Table~\\ref{tab:numsamples} lists the four sample windows.")
    changed |= c
    if c:
        print("  S15 table reference added")
    if a.apply and changed:
        io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
