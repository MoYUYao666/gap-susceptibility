# -*- coding: utf-8 -*-
r"""Refine S30 additivity (8 prompts + CI) and S34 curvature (seed/environment instability)."""
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
AN = os.path.join(REPO, "outputs", "analysis")


def jl(p):
    return json.load(io.open(os.path.join(AN, p), encoding="utf-8"))


def share(d):
    sh = [0.5 * 5e-5 * x["ghg_full"]["0.001"] / x["g2"] for x in d["runs"]]
    return sum(sh) / len(sh)


def f4(x):
    return "%+.4f" % x


t = io.open(SUPP, encoding="utf-8").read()
bs = chr(92)

# --- S30 additivity ---
add = jl("p3_additivity_residual.json")
rows = []
for p in add["pair_residuals"]:
    name = p["A"] + "+" + p["B"]
    rows.append("%s & %.1f & %.1f & %+.1f & %+.2f & [%+.2f, %+.2f] %s" % (
        bs + "texttt{" + name.replace("_", bs + "_") + "}", p["E_union"], p["E_empty"], p["residual"],
        100 * p["relative"], p["ci95"][0], p["ci95"][1], bs * 2))
rows = "\n".join(rows)
i = t.find("\\label{app:additivity}")
seg_start = t.rfind("\\begin{tabular}", i - 500, i)
mid = t.find("\\bottomrule", i)
head = ("\\begin{tabular}{@{}lrrrrr@{}}\n\\toprule\n"
        "block pair & $E(A\\cup B)$ & $E(\\varnothing)$ & residual & relative & 95\\% CI \\\\\n\\midrule\n")
t = t[:seg_start] + head + rows + "\n" + t[mid:]
old_cap = ("Block-additivity residuals of the energy functional on the probe adapter. All pair residuals are below\n"
           "$0.05\\%$ of the energy scale, so the additive decomposition is empirically supported for this probe.")
new_cap = ("Block-additivity residuals of the energy functional on the probe adapter (eight held-out prompts;\n"
           "prompt-level bootstrap 95\\% CIs). All pair residuals stay within $0.12\\%$ of the energy scale and the CIs\n"
           "contain or sit close to zero, so the additive decomposition is empirically supported for this probe.")
if old_cap in t:
    t = t.replace(old_cap, new_cap, 1)
else:
    print("S30 caption pattern not found")

# --- S34 curvature ---
loc8 = share(jl("p3_hessian_probe_r8.json"))
loc12 = share(jl("p3_hessian_probe_r12.json"))
loc16 = share(jl("p3_hessian_probe_r16.json"))
loc42 = share(jl("p3_hessian_probe_r24.json"))
loc123 = share(jl("p3_hessian_probe_r24_s123.json"))
loc789 = share(jl("p3_hessian_probe_r24_s789.json"))
loc64 = share(jl("p3_hessian_probe_r64_s42.json"))
clo24 = share(jl("cloud_p3_hessian_probe_r24.json"))
clo64 = share(jl("cloud_p3_hessian_probe_r64.json"))
start = t.rfind("\\begin{tabular}", t.find("\\label{app:highrank}") - 600, t.find("\\label{app:highrank}"))
end = t.find("\\end{tabular}", start)
table = ("\\begin{tabular}{@{}llrr@{}}\n\\toprule\nrank & seed & stack & share at $\\eta$ \\\\\n\\midrule\n"
         "8 & 42 & local & " + f4(loc8) + " \\\\\n12 & 42 & local & " + f4(loc12) + " \\\\\n"
         "16 & 42 & local & " + f4(loc16) + " \\\\\n24 & 42 & local & " + f4(loc42) + " \\\\\n"
         "24 & 123 & local & " + f4(loc123) + " \\\\\n24 & 789 & local & " + f4(loc789) + " \\\\\n"
         "24 & 42 & cloud & " + f4(clo24) + " \\\\\n64 & 42 & local & " + f4(loc64) + " \\\\\n"
         "64 & 42 & cloud & " + f4(clo64) + " \\\\\n\\bottomrule")
t = t[:start] + table + t[end:]
old_cap34 = ("\\caption{Curvature across rank on the local stack (torch 2.9/CUDA 13.0) and on the cloud stack\n"
             "(torch 2.12/CUDA 13.0). Locally the second-order share stays negative through $r=24$; on the cloud stack\n"
             "it turns positive at $r=24$, so the sign of the curvature term at high rank is itself environment-sensitive,\n"
             "matching the energy-sign sensitivity in S29. At the operating learning rate the share stays below $0.6\\%$.\n"
             "Archives: \\texttt{outputs/analysis/p3\\_hessian\\_probe\\_r8/12/16/24.json},\n"
             "\\texttt{cloud\\_p3\\_hessian\\_probe\\_r24/64.json}.}")
new32 = ("Curvature across rank, seed and software stack. The second-order share shrinks with rank and at $r\\ge 24$ "
         "is below $0.6\\%$ at the operating learning rate; its sign is not stable across seeds (three local $r=24$ "
         "seeds give " + f4(loc42) + ", " + f4(loc123) + ", " + f4(loc789) + ") or stacks (cloud " + f4(clo24) +
         "). We therefore do not claim a robust curvature sign change: the first-order approximation remains accurate "
         "at the operating learning rate, while the high-rank sign is environment- and seed-dependent. Archives: "
         "\\texttt{outputs/analysis/p3\\_hessian\\_probe\\_r24*.json}, "
         "\\texttt{cloud\\_p3\\_hessian\\_probe\\_r24/64.json}.}")
if old_cap34 in t:
    t = t.replace(old_cap34, "\\caption{" + new32, 1)
else:
    print("S34 caption pattern not found")
old_row = ("curvature sign stable across ranks & \\emph{not} supported & negative locally through $r=24$; "
           "$r=24$ sign differs on the cloud stack (S34) \\\\")
new_row = ("curvature sign stable across ranks & \\emph{not} supported & high-rank share below $0.6\\%$; sign varies "
           "across seeds and stacks (S34) \\\\")
if old_row in t:
    t = t.replace(old_row, new_row, 1)
io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
print("S30/S34 refined")
