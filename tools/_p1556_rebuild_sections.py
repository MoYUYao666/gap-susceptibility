# -*- coding: utf-8 -*-
"""Rebuild S30 (8-prompt additivity), S34 (seed/stack curvature) and add S38 (allocation bootstrap) cleanly."""
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
AN = os.path.join(REPO, "outputs", "analysis")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
bs = chr(92)


def jl(p):
    return json.load(io.open(os.path.join(AN, p), encoding="utf-8"))


def share(d):
    sh = [0.5 * 5e-5 * x["ghg_full"]["0.001"] / x["g2"] for x in d["runs"]]
    return sum(sh) / len(sh)


def replace_section(t, title, new_block):
    head = "\\section{" + title + "}"
    start = t.find(head)
    assert start >= 0, title
    nxt = t.find("\\section{", start + len(head))
    end = nxt if nxt >= 0 else t.find("\\bibliographystyle", start)
    return t[:start] + new_block + "\n" + t[end:]


t = io.open(SUPP, encoding="utf-8").read()

# ---- S30 ----
add = jl("p3_additivity_residual.json")
rows = []
for p in add["pair_residuals"]:
    name = p["A"] + "+" + p["B"]
    rows.append("%s & %.1f & %.1f & %+.1f & %+.2f & [%+.2f, %+.2f] %s" % (
        bs + "texttt{" + name.replace("_", bs + "_") + "}", p["E_union"], p["E_empty"], p["residual"],
        100 * p["relative"], p["ci95"][0], p["ci95"][1], bs * 2))
s30 = (r"""\section{Additivity residual of the block decomposition}
\label{app:additivity}

We test the additivity assumption (R3$'$) directly on the probe adapter: zero the LoRA $B$ matrices outside a block
subset $S$ and measure the alignment energy $E(S)$ on eight held-out instruction batches; per-prompt residuals are
bootstrap-resampled for the intervals in Table~\ref{tab:additivity}.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrrrr@{}}
\toprule
block pair & $E(A\cup B)$ & $E(\varnothing)$ & residual & relative & 95\% CI \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Block-additivity residuals of the energy functional on the probe adapter (eight held-out prompts;
prompt-level bootstrap 95\% CIs). All pair residuals stay within $0.12\%$ of the energy scale and the CIs contain or
sit close to zero, so the additive decomposition is empirically supported for this probe. Archive:
\texttt{outputs/analysis/p3\_additivity\_residual.json}.}
\label{tab:additivity}
\end{table*}""")
t = replace_section(t, "Additivity residual of the block decomposition", s30)

# ---- S34 ----
vals = [share(jl("p3_hessian_probe_r8.json")), share(jl("p3_hessian_probe_r12.json")),
        share(jl("p3_hessian_probe_r16.json")), share(jl("p3_hessian_probe_r24.json")),
        share(jl("p3_hessian_probe_r24_s123.json")), share(jl("p3_hessian_probe_r24_s789.json")),
        share(jl("cloud_p3_hessian_probe_r24.json")), share(jl("p3_hessian_probe_r64_s42.json")),
        share(jl("cloud_p3_hessian_probe_r64.json"))]
labels = [("8", "42", "local"), ("12", "42", "local"), ("16", "42", "local"),
          ("24", "42", "local"), ("24", "123", "local"), ("24", "789", "local"),
          ("24", "42", "cloud"), ("64", "42", "local"), ("64", "42", "cloud")]
rows = "\n".join("%s & %s & %s & %+.4f %s" % (a, b, c, v, bs * 2) for (a, b, c), v in zip(labels, vals))
cap34 = ("Curvature across rank, seed and software stack. The second-order share shrinks with rank and at $r\\ge 24$ "
         "is below $0.6\\%$ at the operating learning rate; its sign is not stable across seeds (three local $r=24$ "
         "seeds give " + ("%+.4f" % vals[3]) + ", " + ("%+.4f" % vals[4]) + ", " + ("%+.4f" % vals[5]) + ") or stacks "
         "(cloud " + ("%+.4f" % vals[6]) + "). We therefore do not claim a robust curvature sign change: the first-order "
         "approximation remains accurate at the operating learning rate, while the high-rank sign is environment- and "
         "seed-dependent. Archives: \\texttt{outputs/analysis/p3\\_hessian\\_probe\\_r24*.json}, "
         "\\texttt{cloud\\_p3\\_hessian\\_probe\\_r24/64.json}.")
s34 = (r"""\section{Curvature at high rank}
\label{app:highrank}

The finite-difference curvature probe is repeated at $r=8$ through $r=64$, on the local and the cloud stack and,
for $r=24$, across seeds.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}llrr@{}}
\toprule
rank & seed & stack & share at $\eta$ \\
\midrule
""" + rows + "\n" + r"""\bottomrule
\end{tabular}
\caption{""" + cap34 + r"""}
\label{tab:highrank}
\end{table*}""")
t = replace_section(t, "Curvature at high rank", s34)

# ---- S38 bootstrap ----
boot = jl("p3_gamma_bootstrap.json")
freq = boot["frequencies"][:3]
brows = "\n".join("%s & %.3f %s" % ("/".join(str(x) for x in f["ranks"]), f["freq"], bs * 2) for f in freq)
point = "/".join(str(x) for x in boot["point_allocation"])
point_freq = 100 * next((f["freq"] for f in boot["frequencies"] if f["ranks"] == boot["point_allocation"]), 0.0)
s38 = (r"""\section{Allocation stability under reference-batch bootstrap}
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
""" + brows + r"""
\bottomrule
\end{tabular}
\caption{Bootstrap of the $|\Gamma|$ block allocation over the three reference batches (budget 16). The point
allocation of the paper is """ + point + r""" and is reproduced in only """ + ("%.0f" % point_freq) + r"""\% of the draws;
the most frequent draw is vision-heavy, so the ranking itself is only weakly determined at this batch scale. This is
consistent with the batch sensitivity in S23 and reinforces that no allocation advantage is claimed. Archive:
\texttt{outputs/analysis/p3\_gamma\_bootstrap.json}.}
\label{tab:gammaboot}
\end{table*}""")
if "app:gammaboot" not in t:
    t = t.replace("\\bibliographystyle{IEEEtran}", s38 + "\n\n\\bibliographystyle{IEEEtran}", 1)
io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
print("S30/S34 rebuilt, S38 present:", "app:gammaboot" in t)

mf = json.load(io.open(MANIFEST, encoding="utf-8"))
floats = mf["manuscripts"]["P3"]["floats"]
if not any(f["label"] == "tab:gammaboot" for f in floats):
    floats.append({"label": "tab:gammaboot", "kind": "table", "script": "tools/_p1552_gamma_bootstrap_archive.py",
                   "archive": "outputs/analysis/p3_gamma_bootstrap.json", "status": "verified",
                   "note": "reference-batch bootstrap of the |Gamma| allocation"})
json.dump(mf, io.open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("floats:", len(floats))
