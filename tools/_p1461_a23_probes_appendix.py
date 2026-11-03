# -*- coding: utf-8 -*-
r"""A23: write the two protocol-sensitivity probes (water-tank re-probe and evaluation-size sweep) into the appendix.

    python tools/_p1461_a23_probes_appendix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(REPO, "paper_a2", "main_ieee.tex")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")

ANCHOR = "where the field has vanished)."

SENT = (" Two protocol-sensitivity probes---a re-preprocessed view of the water-tank acquisition and an evaluation-size "
        "sweep on the marine class set---are reported in Appendix~\\ref{app:probes}; neither changes the boundary "
        "conclusions above.")
APP = r"""
\section{Protocol-sensitivity probes}
\label{app:probes}

Two probes bound how far the diagnostic transfers without a matched protocol. Neither is a replication; they are reported
because they mark where the diagnostic stops being informative.

\textbf{(i) Re-preprocessed water-tank view.} The water-tank acquisition was re-converted from the raw array (per-split
min--max to 8-bit, bicubic resize to $224\times224$, RGB), with all 11 stored classes (including \emph{background}) and the
paper's text template. On the 395 held-out images the top-1 is near chance for both encoders (chance $9.1\%$), and the
$\tau$--accuracy and gap--accuracy correlations reverse sign (Table~\ref{tab:watertank96}). This is an
out-of-distribution boundary, not a contradiction of the water-tank row in Table~\ref{tab:sonar-sigma}: that row uses the
full two-encoders 2{,}617-image protocol with the dataset's own class names and an adapted checkpoint, whereas the probe
uses raw-array conversion, a different class set and a frozen model. Data:
\texttt{outputs/\allowbreak analysis/\allowbreak a23\_watertank\_domain.json}.

\begin{table}[h]
\centering
\small
\caption{Re-preprocessed water-tank probe (11 classes, 395 held-out images, frozen encoders, $\lambda$ grid
$[-1,-0.5,-0.25,0,0.25,0.5,1,2]$). ``top-1 range'' is the range across the grid; $r(\tau)$ and $r(\mathrm{CG})$ are the
Pearson correlations of the accuracy with the order-preservation coefficient and the centroid gap.}
\label{tab:watertank96}
\begin{tabular}{@{}lccc@{}}
\toprule
encoder & top-1 range (\%) & $r(\tau)$ & $r(\mathrm{CG})$ \\
\midrule
BioCLIP & 8.9--18.5 & $-0.751$ & $-0.674$ \\
OceanCLIP & 4.3--17.5 & $-0.764$ & $-0.970$ \\
\bottomrule
\end{tabular}
\end{table}

\textbf{(ii) Evaluation-size sweep.} Stratified subsets of the 67-class marine evaluation set were scored on the same
$\lambda$ grid. The $\tau$--accuracy correlation is unstable below roughly a hundred images and stabilises at the full
split, so tripwire levels fitted on fewer than a hundred evaluation images are indicative only (Table~\ref{tab:neval}).
Data: \texttt{outputs/\allowbreak analysis/\allowbreak a23\_neval\_sensitivity.json}.

\begin{table}[h]
\centering
\small
\caption{Evaluation-size sweep: Pearson $r(\tau,\text{accuracy})$ on stratified subsets of the 67-class marine set (full
set: 1{,}608 images).}
\label{tab:neval}
\begin{tabular}{@{}lccccc@{}}
\toprule
encoder & $n{=}32$ & $n{=}64$ & $n{=}128$ & $n{=}256$ & full \\
\midrule
BioCLIP & 0.48 & 0.21 & 0.91 & 0.89 & 0.83 \\
OceanCLIP & $-0.64$ & 0.79 & $-0.26$ & 0.06 & 0.61 \\
\bottomrule
\end{tabular}
\end{table}

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(TEX, encoding="utf-8").read()
    changed = False
    if "app:probes" not in t:
        assert t.count(ANCHOR) == 1, t.count(ANCHOR)
        t = t.replace(ANCHOR, ANCHOR + SENT, 1)
        anchor2 = "\\section*{Data and code provenance}"
        assert anchor2 in t
        t = t.replace(anchor2, APP + "\n" + anchor2, 1)
        changed = True
        print("  appendix and main-text pointer added")
    tm = json.load(io.open(MANIFEST, encoding="utf-8"))
    floats = tm["manuscripts"]["A23"]["floats"]
    have = {e["label"] for e in floats}
    add = []
    if "tab:watertank96" not in have:
        add.append({"label": "tab:watertank96", "kind": "table", "script": "tools/_p1414_a23_watertank.py",
                    "archive": "outputs/analysis/a23_watertank_domain.json", "status": "verified",
                    "note": "appendix protocol-sensitivity probe (OOD boundary)"})
    if "tab:neval" not in have:
        add.append({"label": "tab:neval", "kind": "table", "script": "tools/_p1415_a23_neval.py",
                    "archive": "outputs/analysis/a23_neval_sensitivity.json", "status": "verified",
                    "note": "appendix evaluation-size sweep"})
    if add:
        floats.extend(add)
        changed = True
        print("  manifest entries added:", [e["label"] for e in add])
    if a.apply and changed:
        io.open(TEX, "w", encoding="utf-8", newline="").write(t)
        io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(tm, indent=1, ensure_ascii=False))
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
