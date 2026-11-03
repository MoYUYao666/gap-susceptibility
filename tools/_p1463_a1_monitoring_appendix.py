# -*- coding: utf-8 -*-
r"""A1: add the monitoring-rule variants appendix table and the main-text pointer; register new floats.

    python tools/_p1463_a1_monitoring_appendix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")

APPENDIX = r"""
\section*{Monitoring rule variants}
\label{app:monitor_variants}

Table~\ref{tab:monitor_variants} collects the rule variants behind the monitoring results. The pattern is the same on
all three task types: selecting the epoch by the held-out margin mass is close to the labelled oracle, while training to
the end, stopping at the first epoch, or using the training-split mass all cost more. The training-split mass is the
largest sample available, yet it is worse than the held-out mass, so the limiting factor is the resolution of the
evaluation split rather than the availability of labels. Data and generating scripts:
\texttt{outputs/\allowbreak analysis/\allowbreak a1\_round1\_analysis.json},
\texttt{outputs/\allowbreak analysis/\allowbreak a1\_monitor\_bothtower\_analysis.json},
\texttt{outputs/\allowbreak analysis/\allowbreak a1\_retrieval\_monitor.json};
\texttt{tools/\allowbreak \_p1434\_a1\_round1\_analysis.py},
\texttt{tools/\allowbreak \_p1452\_a1\_bothtower\_analysis.py}.

\begin{table}[h]
\centering
\small
\caption{Mean regret (points from the labelled oracle) of four epoch-selection rules and of training to the end, on the
three monitoring tasks. Classification: four domains, ten epochs; retrieval: 137 held-out image--caption pairs;
both-tower: DTD and Food-101 with rank-8 LoRA on both towers.}
\label{tab:monitor_variants}
\begin{tabular}{@{}lccc@{}}
\toprule
rule & classification & retrieval & both-tower \\
\midrule
held-out margin mass & 1.04 & 0.7 & 0.0 \\
training-split mass & 1.43 & --- & --- \\
last epoch & 1.65 & 2.9 & 1.01 \\
first epoch & 12.94 & 1.5 & 4.63 \\
\bottomrule
\end{tabular}
\end{table}

"""

POINTER = " Appendix Table~\\ref{tab:monitor_variants} collects the rule variants across the three task types."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    changed = False
    if "app:monitor_variants" not in t:
        anchor = "\\section*{Data and code provenance}"
        assert anchor in t
        t = t.replace(anchor, APPENDIX + "\n" + anchor, 1)
        key = "(\\texttt{outputs/\\allowbreak analysis/\\allowbreak a1\\_monitor\\_bothtower.json})."
        assert key in t, "both-tower sentence anchor missing"
        t = t.replace(key, key + POINTER, 1)
        changed = True
        print("  appendix and pointer added")
    tm = json.load(io.open(MANIFEST, encoding="utf-8"))
    if not any(e["label"] == "tab:monitor_variants" for e in tm["manuscripts"]["A1"]["floats"]):
        tm["manuscripts"]["A1"]["floats"].append({
            "label": "tab:monitor_variants", "kind": "table",
            "script": "tools/_p1434_a1_round1_analysis.py",
            "archive": "outputs/analysis/a1_round1_analysis.json", "status": "verified",
            "note": "appendix monitoring rule variants; also a1_monitor_bothtower_analysis.json"})
        changed = True
        print("  manifest entry added: tab:monitor_variants")
    pa = tm["manuscripts"]["paperA"]["floats"]
    if not any(e["label"] == "tab:odefit" for e in pa):
        pa.append({"label": "tab:odefit", "kind": "table",
                   "script": "tools/_p1440_paperA_ode_residuals.py",
                   "archive": "outputs/analysis/paperA_ode_residuals.json", "status": "verified",
                   "note": "appendix ODE fit diagnostics"})
        changed = True
        print("  manifest entry added: tab:odefit")
    if a.apply and changed:
        io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
        io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(tm, indent=1, ensure_ascii=False))
        print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
