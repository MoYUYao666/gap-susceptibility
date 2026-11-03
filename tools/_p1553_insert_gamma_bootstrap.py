# -*- coding: utf-8 -*-
r"""Insert the reference-batch bootstrap of the |Gamma| allocation (S23/S32 extension)."""
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
AN = os.path.join(REPO, "outputs", "analysis")
BOOT = os.path.join(AN, "p3_gamma_bootstrap.json")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")

d = json.load(io.open(BOOT, encoding="utf-8"))
freq = d["frequencies"][:3]
rows = "\n".join("%s & %.3f \\\\" % ("/".join(str(x) for x in f["ranks"]), f["freq"]) for f in freq)
point = "/".join(str(x) for x in d["point_allocation"])
t = io.open(SUPP, encoding="utf-8").read()
if "app:gammaboot" not in t:
    sec = r"""
\section{Allocation stability under reference-batch bootstrap}
\label{app:gammaboot}

The $|\Gamma|$ allocation is computed from three reference batches. Resampling those batches 2000 times gives the
distribution in Table~\ref{tab:gammaboot}.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lr@{}}
\toprule
allocation (vision/shallow/mid/deep) & bootstrap frequency \\
\midrule
%(rows)s
\bottomrule
\end{tabular}
\caption{Bootstrap of the $|\Gamma|$ block allocation over the three reference batches (budget 16). The point
allocation of the paper is %(point)s and is reproduced in only %(pf).0f\%% of the draws; the most frequent draw is
vision-heavy, so the ranking itself is only weakly determined at this batch scale. This is consistent with the
batch-sensitivity in S23 and reinforces that no allocation advantage is claimed. Archive:
\texttt{outputs/analysis/p3\_gamma\_bootstrap.json}.}
\label{tab:gammaboot}
\end{table*}
""" % {"rows": rows, "point": point, "pf": 100 * freq[0]["freq"] if False else 100 * next(
        (f["freq"] for f in d["frequencies"] if f["ranks"] == d["point_allocation"]), 0.0)}
    t = t.replace("\\bibliographystyle{IEEEtran}", sec + "\n\\bibliographystyle{IEEEtran}", 1)
    io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
    print("S38 inserted")
else:
    print("already present")
m = json.load(io.open(MANIFEST, encoding="utf-8"))
floats = m["manuscripts"]["P3"]["floats"]
if not any(f["label"] == "tab:gammaboot" for f in floats):
    floats.append({"label": "tab:gammaboot", "kind": "table", "script": "tools/_p1552_gamma_bootstrap_archive.py",
                   "archive": "outputs/analysis/p3_gamma_bootstrap.json", "status": "verified",
                   "note": "reference-batch bootstrap of the |Gamma| allocation"})
    json.dump(m, io.open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("manifest floats:", len(floats))
