# -*- coding: utf-8 -*-
"""Apply the 8-prompt additivity table and seed/stack curvature table to the typeset (first) occurrences."""
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
AN = os.path.join(REPO, "outputs", "analysis")
bs = chr(92)


def jl(p):
    return json.load(io.open(os.path.join(AN, p), encoding="utf-8"))


def share(d):
    sh = [0.5 * 5e-5 * x["ghg_full"]["0.001"] / x["g2"] for x in d["runs"]]
    return sum(sh) / len(sh)


t = io.open(SUPP, encoding="utf-8").read()

# S30
i = t.find("\\label{app:additivity}")
s = t.rfind("\\begin{tabular}", 0, i)
e = t.find("\\end{tabular}", s)
add = jl("p3_additivity_residual.json")
rows = []
for p in add["pair_residuals"]:
    name = p["A"] + "+" + p["B"]
    rows.append("%s & %.1f & %.1f & %+.1f & %+.2f & [%+.2f, %+.2f] %s" % (
        bs + "texttt{" + name.replace("_", bs + "_") + "}", p["E_union"], p["E_empty"], p["residual"],
        100 * p["relative"], p["ci95"][0], p["ci95"][1], bs * 2))
table = ("\\begin{tabular}{@{}lrrrrr@{}}\n\\toprule\n"
         "block pair & $E(A\\cup B)$ & $E(\\varnothing)$ & residual & relative & 95\\% CI \\\\\n\\midrule\n"
         + "\n".join(rows) + "\n\\bottomrule\n")
t = t[:s] + table + t[e + len("\\end{tabular}"):]
t = t.replace("measure the alignment energy $E(S)$ on four held-out instruction batches",
              "measure the alignment energy $E(S)$ on eight held-out instruction batches", 1)

# S34
i = t.find("\\label{app:highrank}")
s = t.rfind("\\begin{tabular}", 0, i)
e = t.find("\\end{tabular}", s)
vals = [share(jl("p3_hessian_probe_r8.json")), share(jl("p3_hessian_probe_r12.json")),
        share(jl("p3_hessian_probe_r16.json")), share(jl("p3_hessian_probe_r24.json")),
        share(jl("p3_hessian_probe_r24_s123.json")), share(jl("p3_hessian_probe_r24_s789.json")),
        share(jl("cloud_p3_hessian_probe_r24.json")), share(jl("p3_hessian_probe_r64_s42.json")),
        share(jl("cloud_p3_hessian_probe_r64.json"))]
labels = [("8", "42", "local"), ("12", "42", "local"), ("16", "42", "local"),
          ("24", "42", "local"), ("24", "123", "local"), ("24", "789", "local"),
          ("24", "42", "cloud"), ("64", "42", "local"), ("64", "42", "cloud")]
rows = "\n".join("%s & %s & %s & %+.4f %s" % (a, b, c, v, bs * 2) for (a, b, c), v in zip(labels, vals))
table = ("\\begin{tabular}{@{}llrr@{}}\n\\toprule\nrank & seed & stack & share at $\\eta$ \\\\\n\\midrule\n"
         + rows + "\n\\bottomrule\n")
t = t[:s] + table + t[e + len("\\end{tabular}"):]
io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
print("tables applied")
