# -*- coding: utf-8 -*-
"""P1 patch A7: the last stale claim block and two single-run/5-seed inconsistencies."""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    # ---- supplementary: the whole "non-triviality" block, header included ----
    ("paper/sections/supplementary.tex",
     "Three lines of evidence confirm DG is not a redundant proxy for CG:",
     "We report what the correlation structure of our archive does and does not support:"),
    ("paper/sections/supplementary.tex",
     "    \\item \\textbf{CG$\\Delta$ non-predictive}: CG$\\Delta$ shows no significant correlation with \\Rk{1} ($r = 0.012$, $p = 0.915$).\n\n    \\item \\textbf{Construct validity}: DG$^2$ = CG$^2$ + $\\|\\sigma_I-\\sigma_T\\|^2$; the variance component independently correlates with \\Rk{1}.",
     "    \\item \\textbf{Change is weakly predictive}: CG$\\Delta$ correlates with \\Rk{1} at $r = +0.190$ ($p = 0.007$) and DG$\\Delta$ at $r = +0.134$ ($p = 0.055$); both are far weaker than the level correlations, so the absolute magnitude rather than the direction of change is the informative quantity.\n\n    \\item \\textbf{Construct relation}: DG$^2$ = CG$^2$ + $\\|\\sigma_I-\\sigma_T\\|^2$, so DG contains CG by construction; in our archive the two are correlated at $r = +0.945$, which is why we do not treat them as independent predictors."),
    # ---- experiments: single-run vs five-seed ----
    ("paper/sections/experiments.tex",
     "Full fine-tuning is catastrophic across all datasets, increasing CG by $+0.199$ (Flickr) and $+0.194$ (COCO).",
     "Full fine-tuning is catastrophic across all datasets, increasing CG by $+0.191 \\pm 0.008$ over five seeds on Flickr (the single archived run gives $+0.199$) and by $+0.194$ on COCO (single run)."),
    # ---- discussion: same convention ----
    ("paper/sections/discussion.tex",
     "The effect sizes are substantially smaller than on CLIP (where full FT causes CG$\\Delta = +0.199$)",
     "The effect sizes are substantially smaller than on CLIP (where full fine-tuning raises CG$\\Delta$ by $+0.191 \\pm 0.008$ over five seeds)"),
]
fails = []
for rel, old, new in EDITS:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    src = io.open(p, encoding="utf-8").read()
    n = src.count(old)
    if n != 1:
        fails.append("%s: found %d :: %s" % (rel, n, old[:60]))
        print("FAIL %s (%d)" % (rel, n))
        continue
    io.open(p, "w", encoding="utf-8", newline="").write(src.replace(old, new, 1))
    print("ok   %s" % rel)
if fails:
    print(fails)
    sys.exit(1)
print("PATCH A7 APPLIED")
