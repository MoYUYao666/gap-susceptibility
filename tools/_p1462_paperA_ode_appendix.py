# -*- coding: utf-8 -*-
r"""Paper A: add the ODE-fit diagnostics appendix (per-family and per-site) and reference it from the text.

    python tools/_p1462_paperA_ode_appendix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC = os.path.join(REPO, "paper合", "sections", "ode_diagnostics_appendix.tex")
PANEL = os.path.join(REPO, "paper合", "sections", "provenance_appendix.tex")
MAINS = [os.path.join(REPO, "paper合", "main_nc.tex"), os.path.join(REPO, "paper合", "main_springer.tex")]
EMP = os.path.join(REPO, "paper合", "sections", "empirical.tex")

APPENDIX = r"""
\section*{ODE fit diagnostics: family and site structure}
\label{app:odefit}

The first-order reduction is fitted per run; the table reports its residual structure over the 96 archived runs, so that
the quantitative claims can be scoped to the families where the reduction holds. The fit is excellent for LoRA (95\% of
runs above $R^2=0.9$), good for full fine-tuning (64\%), and poor for the adapter family (7\%, minimum $0.001$); by
adaptation site the means are $0.924$ (other), $0.864$ (text-only) and $0.827$ (both), and the restoring coefficient
$\beta$ is strongly site-dependent (coefficient of variation $1.27$--$1.77$ across sites), which is why $\beta$ is never
pooled across sites. Data and generating script:
\texttt{outputs/\allowbreak analysis/\allowbreak paperA\_ode\_residuals.json},
\texttt{tools/\allowbreak \_p1440\_paperA\_ode\_residuals.py}.

\begin{table}[h]
\centering
\small
\caption{ODE fit quality by adaptation family (96 archived runs). $R^2$ is the trajectory fit of the first-order
reduction; ``$>0.9$'' is the share of runs above that value.}
\label{tab:odefit}
\begin{tabular}{@{}lcccc@{}}
\toprule
family & runs & mean $R^2$ & min $R^2$ & share $>0.9$ \\
\midrule
LoRA & 55 & 0.949 & 0.814 & 95\% \\
full fine-tuning & 11 & 0.922 & 0.847 & 64\% \\
adapter & 30 & 0.669 & 0.001 & 7\% \\
\bottomrule
\end{tabular}
\end{table}

"""

POINTER = " (per-family and per-site residual structure in Appendix Table~\\ref{tab:odefit})."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    changed = False
    if not os.path.exists(SEC):
        io.open(SEC, "w", encoding="utf-8", newline="").write(APPENDIX)
        changed = True
        print("  appendix file written")
    for m in MAINS:
        t = io.open(m, encoding="utf-8").read()
        if "ode_diagnostics_appendix" not in t:
            anchor = "\\input{sections/provenance_appendix}"
            assert anchor in t, m
            t = t.replace(anchor, "\\input{sections/ode_diagnostics_appendix}\n\n" + anchor, 1)
            io.open(m, "w", encoding="utf-8", newline="").write(t)
            changed = True
            print("  input added to", os.path.basename(m))
    e = io.open(EMP, encoding="utf-8").read()
    key = "restricted to the two families that satisfy the first-order reduction; the adapter family enters only"
    if key in e and "tab:odefit" not in e:
        i = e.find("the adapter family enters only")
        j = e.find("through the qualitative position ordering.", i)
        assert j > i
        j = e.find(".", j) + 1
        e = e[:j] + POINTER + e[j:]
        io.open(EMP, "w", encoding="utf-8", newline="").write(e)
        changed = True
        print("  main-text pointer added")
    if a.apply and changed:
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
