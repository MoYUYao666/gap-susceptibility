# -*- coding: utf-8 -*-
"""Update S29/S37/discussion with the three-seed torch 2.4 environment level (env share 48%)."""
import io
import json

REPO = "."
AN = "outputs/analysis/p3_env_variance.json"
SUPP = "paper3/paper_ieee/supplementary/supplementary.tex"
DISC = "paper3/paper_ieee/sections/discussion.tex"

v = json.load(io.open(AN, encoding="utf-8"))
envs = v["envs"]
rows = "\n".join("%s & %d & %+.1f & %.1f \\\\" % (e, d["n"], d["mean"], d["sd"]) for e, d in envs.items())
se, ss, share = v["sigma_env"], v["sigma_seed"], 100 * v["env_variance_share"]

t = io.open(SUPP, encoding="utf-8").read()
# S37 table rows
i = t.find("\\label{app:envvar}")
m = t.find("\\midrule", i)
b = t.find("\\bottomrule", m)
t = t[: m + len("\\midrule")] + "\n" + rows + "\n" + t[b:]
# S37 caption numbers
old = ("$\\sigma_{\\mathrm{env}}=22.2$,\n$\\sigma_{\\mathrm{seed}}=34.3$, environment share $29\\%$ of the total variance.")
new = ("$\\sigma_{\\mathrm{env}}=%.1f$,\n$\\sigma_{\\mathrm{seed}}=%.1f$, environment share $%.0f\\%%$ of the total variance." % (se, ss, share))
if old in t:
    t = t.replace(old, new, 1)
else:
    print("S37 stats pattern not found")
# S37 caveat sentence -> three seeds
t = t.replace("The torch 2.4 level has only two seeds, so the environment share is\nan indicative estimate.",
              "The torch 2.4 level has three seeds, so the environment share is a\nlow-power but consistent estimate.")
# S29 caption second-seed sentence
old29 = ("while a second seed in the torch 2.4 stack gives $-2.5$, so environment shifts and seed noise are of the same\n"
         "order at this rank.")
new29 = ("while two further seeds in the torch 2.4 stack give $-2.5$ and $+64.5$, so the environment shift is of the\n"
         "same order as the seed spread at this rank.")
if old29 in t:
    t = t.replace(old29, new29, 1)
else:
    print("S29 second-seed pattern not found")
# S17 claim row
old_row = ("crossing stable across torch/CUDA versions & \\emph{not} supported & $r=6$ positive everywhere; $r=5$ near "
           "zero, sign varies with seed and stack (S29, S37) \\\\")
new_row = ("crossing stable across torch/CUDA versions & \\emph{not} supported & $r=6$ positive everywhere; $r=5$ "
           "shifts with the software stack (mean $-23$/$-44$/$+34$; S29, S37) \\\\")
if old_row in t:
    t = t.replace(old_row, new_row, 1)
else:
    print("claim row pattern not found")
io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
print("supplement updated")

d = io.open(DISC, encoding="utf-8").read()
old_lim = ("keeps the $r=6$ sign positive while the $r=5$ effect sits near zero and its sign\n"
           "varies with both seed and stack (Sections~S29 and S37; environment variance is about 29\\% of the total at\n"
           "$r=5$). Hence $r_c$ is environment-conditioned rather than a universal constant.")
new_lim = ("keeps the $r=6$ sign positive while the $r=5$ mean shifts from $-23$ and $-44$ (the two cu130 stacks) to\n"
           "$+34$ (torch 2.4/CUDA 12.1); a random-effects decomposition attributes about 48\\% of the $r=5$ variance to\n"
           "the software stack (Sections~S29 and S37). Hence $r_c$ is environment-conditioned rather than a universal\n"
           "constant.")
if old_lim in d:
    d = d.replace(old_lim, new_lim, 1)
    io.open(DISC, "w", encoding="utf-8", newline="").write(d)
    print("discussion updated")
else:
    print("discussion pattern not found")
