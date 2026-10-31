# -*- coding: utf-8 -*-
r"""A23: write the leave-one-domain-out calibration probe into the appendix.

    python tools/_p1479_a23_calib_lodo_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(REPO, "paper_a2", "main_ieee.tex")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
AN = os.path.join(REPO, "outputs", "analysis", "a23_calib_lodo.json")

BODY_SENT = (" The same separation holds across domains: a leave-one-domain-out fit transfers the slope of the "
             "$\\tau$--accuracy relation (held-out Pearson $0.38$--$0.64$) but not its intercept (mean absolute error "
             "$13$--$28$ accuracy points; Appendix~\\ref{app:probes}, Table~\\ref{tab:calib_lodo}).")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(AN, encoding="utf-8"))
    rows = []
    for held, r in d["lodo"].items():
        rows.append("%s & %d & $%+.1f$ & %.1f & %.2f \\\\" % (
            held.replace("imagenet5k", "ImageNet-5k").replace("fish67", "fish-67"),
            r["n_test"], r["slope"], r["mae"], r["pearson"]))
    app = (r"""\textbf{(iii) Cross-domain calibration.} Fitting $\mathrm{top1}=a+b\tau$ on four domains and predicting the
fifth separates transfer of the relation from transfer of the calibration: the slope stays positive and large
($+33$ to $+51$ accuracy points per unit $\tau$), the held-out correlation is $0.38$--$0.64$, but the mean absolute error
is $13.5$--$27.8$ accuracy points because the intercept is domain-specific (Table~\ref{tab:calib_lodo}). The relation
transfers; absolute calibration does not, which is why the tripwire levels are fitted per domain. Data:
\texttt{outputs/\allowbreak analysis/\allowbreak a23\_calib\_lodo.json}.

\begin{table}[h]
\centering
\small
\caption{Leave-one-domain-out calibration of top-1 from $\tau$ (linear fit on the other four domains; 106 conditions in
total). $n$ is the number of held-out conditions.}
\label{tab:calib_lodo}
\begin{tabular}{@{}lcccc@{}}
\toprule
held-out domain & $n$ & slope & MAE (pp) & Pearson $r$ \\
\midrule
%s
\bottomrule
\end{tabular}
\end{table}

""" % "\n".join(rows))
    t = io.open(TEX, encoding="utf-8").read()
    changed = False
    if "tab:calib_lodo" not in t:
        anchor = "\\section*{Data and code provenance}"
        assert anchor in t
        t = t.replace(anchor, app + "\n" + anchor, 1)
        # short pointer in the calibration paragraph
        key = "tripwire levels fitted on fewer than about 270 evaluation images are indicative only."
        assert key in t
        t = t.replace(key, key + BODY_SENT, 1)
        changed = True
        print("  appendix probe and body pointer added")
    tm = json.load(io.open(MANIFEST, encoding="utf-8"))
    floats = tm["manuscripts"]["A23"]["floats"]
    if not any(e["label"] == "tab:calib_lodo" for e in floats):
        floats.append({"label": "tab:calib_lodo", "kind": "table", "script": "tools/_p1478_a23_lodo_calibration.py",
                       "archive": "outputs/analysis/a23_calib_lodo.json", "status": "verified",
                       "note": "appendix leave-one-domain-out calibration probe"})
        changed = True
        print("  manifest entry added: tab:calib_lodo")
    if a.apply and changed:
        io.open(TEX, "w", encoding="utf-8", newline="").write(t)
        io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(tm, indent=1, ensure_ascii=False))
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
