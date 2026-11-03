# -*- coding: utf-8 -*-
r"""Rebuild S33 (r=3..8 ten-seed crossing) and S35 (multi-seed real-image sweep) as whole sections."""
import glob
import io
import json
import os
import statistics as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
bs = chr(92)


def delta(f):
    try:
        d = json.load(io.open(f, encoding="utf-8"))
        return d.get("delta_E")
    except Exception:
        return None


def blank_runs(rank):
    vals = []
    for f in glob.glob(os.path.join(EXP, "cloud_verify_r%d_s*.json" % rank)):
        n = os.path.basename(f)
        if "imgs" in n or "partial" in n or "_e1_" in n:
            continue
        v = delta(f)
        if v is not None:
            vals.append(v)
    return vals


rows = []
for r in range(3, 9):
    v = blank_runs(r)
    if not v:
        continue
    rows.append("%d & %d & %+.1f & %.1f & %+.1f & %+.1f %s" % (
        r, len(v), st.mean(v), st.stdev(v) if len(v) > 1 else 0.0, min(v), max(v), bs * 2))

real = {}
for r in (4, 5, 6, 7, 8):
    for f in glob.glob(os.path.join(EXP, "cloud_verify_r%d_s*imgs_cap*.json" % r)):
        d = json.load(io.open(f, encoding="utf-8"))
        real[(r, d.get("seed", 42))] = d.get("delta_E")
real_rows = "\n".join("%d & %s & %+.1f %s" % (r, s, v, bs * 2) for (r, s), v in sorted(real.items()))

t = io.open(SUPP, encoding="utf-8").read()


def replace_section(t, title, new_block):
    head = "\\section{" + title + "}"
    start = t.find(head)
    assert start >= 0, title
    nxt = t.find("\\section{", start + len(head))
    end = nxt if nxt >= 0 else t.find("\\bibliographystyle", start)
    return t[:start] + new_block + "\n" + t[end:]


s33 = (r"""\section{Crossing position with ten seeds per rank}
\label{app:crossing10}

Ten seeds per rank are run at $r=3$ through $r=8$ under the blank-image protocol.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrrrr@{}}
\toprule
rank & $n$ & mean & sd & min & max \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Ten-seed crossing statistics. Every run at $r=3,4,5$ is negative and every run at $r=6,7,8$ is positive
(complete separation), so the crossing lies between $r=5$ and $r=6$; an exact two-sided permutation test on the
$r=5$ vs $r=6$ groups gives $p=2/\binom{20}{10}\approx1.1\times10^{-5}$, the minimum attainable with ten seeds per
group. Archive: \texttt{paper3/scripts/outputs/experiments/cloud\_verify\_r*\_s*.json}.}
\label{tab:crossing10}
\end{table*}""")

s35 = (r"""\section{Real-image rank sweep}
\label{app:realimage}

Ranks 4--8 on the caption protocol with real image--caption pairs (20 samples, three epochs); $r=5$ and $r=6$ are
repeated across three seeds.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrr@{}}
\toprule
rank & seed & $\Delta E$ \\
\midrule
""" + real_rows + r"""
\bottomrule
\end{tabular}
\caption{Real-image caption protocol: all ranks increase the alignment energy and no sign change appears, consistent
with the paper's statement that the crossing is tied to the blank-image protocol. Archive:
\texttt{paper3/scripts/outputs/experiments/cloud\_verify\_r*\_imgs\_cap*.json}.}
\label{tab:realimage}
\end{table*}""")

t = replace_section(t, "Crossing position with ten seeds per rank", s33)
t = replace_section(t, "Real-image rank sweep", s35)
io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
print("S33/S35 rebuilt")
