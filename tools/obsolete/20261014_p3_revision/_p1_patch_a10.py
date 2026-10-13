# -*- coding: utf-8 -*-
"""P1 patch A10: ViT-L retrieval caveat + the clustered bootstrap result ([F8])."""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    # (a) extend the catalog footnote to ViT-L
    ("paper/sections/supplementary.tex",
     "$^\\dagger$ BLIP-1 full fine-tuning failed to produce valid gap measurements; BLIP-1 R@1 values are near-random (test set 5K images) except rank-4.",
     "$^\\dagger$ BLIP-1 full fine-tuning failed to produce valid gap measurements; BLIP-1 R@1 values are near-random (test set 5K images) except rank-4. ViT-L retrieval is at chance for every configuration (R@1 $\\le$ 0.005), so only the gap columns are interpreted for that backbone."),
    # (b) discussion: replace the "future work" caveat with the measured result
    ("paper/sections/discussion.tex",
     "Our analysis treats each experiment as one observation, so runs sharing a configuration are not fully independent; the values describe this archive rather than a population, and a mixed-effects or clustered treatment would be the natural next step.",
     "Our analysis treats each experiment as one observation, so runs sharing a configuration are not fully independent; a bootstrap that resamples experiment families rather than rows (12 clusters, 10{,}000 resamples) leaves the association essentially unchanged (DG $r=-0.738$, 95\\% CI $[-0.889,-0.613]$), so the association is robust to clustering within this archive, though still not a population estimate."),
    # (b) supplementary section E: report it as a fourth item
    ("paper/sections/supplementary.tex",
     "    \\item \\textbf{Construct relation}: DG$^2$ = CG$^2$ + $\\|\\sigma_I-\\sigma_T\\|^2$, so DG contains CG by construction; in our archive the two are correlated at $r = +0.945$, which is why we do not treat them as independent predictors.\n\\end{enumerate}",
     "    \\item \\textbf{Construct relation}: DG$^2$ = CG$^2$ + $\\|\\sigma_I-\\sigma_T\\|^2$, so DG contains CG by construction; in our archive the two are correlated at $r = +0.945$, which is why we do not treat them as independent predictors.\n\n    \\item \\textbf{Robustness to clustering}: resampling experiment families rather than rows (12 clusters, 10{,}000 resamples) gives DG $r = -0.738$ (95\\% CI $[-0.889, -0.613]$) and CG $r = -0.607$ ($[-0.777, -0.462]$); no resample yields a non-negative correlation for either statistic.\n\\end{enumerate}"),
]
fails = []
for rel, old, new in EDITS:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    src = io.open(p, encoding="utf-8").read()
    n = src.count(old)
    if n != 1:
        fails.append("%s: found %d :: %s" % (rel, n, old[:70]))
        print("FAIL %s (%d)" % (rel, n))
        continue
    io.open(p, "w", encoding="utf-8", newline="").write(src.replace(old, new, 1))
    print("ok   %s" % rel)
if fails:
    print(fails)
    sys.exit(1)
print("PATCH A10 APPLIED")
