# -*- coding: utf-8 -*-
"""Refine the environment text with the two-seed torch 2.4 evidence and the variance decomposition."""
import io

SUPP = "paper3/paper_ieee/supplementary/supplementary.tex"
DISC = "paper3/paper_ieee/sections/discussion.tex"
t = io.open(SUPP, encoding="utf-8").read()

old_cap = ("\\caption{Cross-environment reproducibility of the $r=5$/$r=6$ crossing (seed 42, blank-image protocol). The\n"
           "positive sign at $r=6$ is stable in all three environments; the sign at $r=5$ flips in the torch 2.4/CUDA 12.1\n"
           "environment ($+41.0$ against $-10.5$ and $-33.5$ in the two cu130 environments), so the crossing is\n"
           "environment-sensitive and the $r=5$ sign is not a cross-environment constant. Archive:\n"
           "\\texttt{outputs/analysis/p3\\_env\\_matrix3.json}.}")
new_cap = ("\\caption{Cross-environment reproducibility of the $r=5$/$r=6$ crossing (seed 42 unless stated). The positive\n"
           "sign at $r=6$ is stable in every environment. At $r=5$ the effect is near zero and its sign is not a\n"
           "cross-environment constant: seed 42 gives $-10.5$ (torch 2.9), $-33.5$ (torch 2.12) and $+41.0$ (torch 2.4),\n"
           "while a second seed in the torch 2.4 stack gives $-2.5$, so environment shifts and seed noise are of the same\n"
           "order at this rank. Archive: \\texttt{outputs/analysis/p3\\_env\\_matrix3.json}.}")
if old_cap in t:
    t = t.replace(old_cap, new_cap, 1)
else:
    print("caption pattern not found")

old_row = ("crossing stable across torch/CUDA versions & \\emph{not} supported & $r=6$ positive everywhere; $r=5$ "
           "sign flips in torch 2.4/cu121 (S29) \\\\")
new_row = ("crossing stable across torch/CUDA versions & \\emph{not} supported & $r=6$ positive everywhere; $r=5$ near "
           "zero, sign varies with seed and stack (S29, S37) \\\\")
if old_row in t:
    t = t.replace(old_row, new_row, 1)
else:
    print("claim row pattern not found")

# add the n=2 caveat to the S37 caption
old37 = ("$r_c$ as environment-conditioned. Archive: \\texttt{outputs/analysis/p3\\_env\\_variance.json}.}")
new37 = ("$r_c$ as environment-conditioned. The torch 2.4 level has only two seeds, so the environment share is\n"
         "an indicative estimate. Archive: \\texttt{outputs/analysis/p3\\_env\\_variance.json}.}")
if old37 in t:
    t = t.replace(old37, new37, 1)
io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
print("supplement refined")

d = io.open(DISC, encoding="utf-8").read()
old_lim = ("a three-environment matrix (torch 2.9/CUDA 13.0, torch 2.12/CUDA 13.0,\n"
           "torch 2.4/CUDA 12.1) keeps the $r=6$ sign positive but flips the $r=5$ sign in the oldest stack\n"
           "(Section~S29), so $r_c$ is an environment-conditioned quantity rather than a universal constant.")
new_lim = ("a three-environment matrix (torch 2.9/CUDA 13.0, torch 2.12/CUDA 13.0,\n"
           "torch 2.4/CUDA 12.1) keeps the $r=6$ sign positive while the $r=5$ effect sits near zero and its sign\n"
           "varies with both seed and stack (Sections~S29 and S37; environment variance is about 29\\% of the total at\n"
           "$r=5$). Hence $r_c$ is environment-conditioned rather than a universal constant.")
if old_lim in d:
    d = d.replace(old_lim, new_lim, 1)
    io.open(DISC, "w", encoding="utf-8", newline="").write(d)
    print("discussion refined")
else:
    print("discussion pattern not found")
