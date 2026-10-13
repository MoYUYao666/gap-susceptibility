# -*- coding: utf-8 -*-
"""
The 2.6x parameter-noise claim is a single unreproducible draw.

The archived single evaluation (baseline R@1 0.705) recorded vision 9.22% versus text 3.55%
degradation at sigma = 0.1, which is the 2.6x the caption quotes.  Three seeded re-runs
(outputs/noise_sensitivity_seeds.json, 4 minutes, forward passes only) give 2.15% +/- 4.41 for
the vision encoder and -0.01% +/- 1.93 for the text encoder at the same sigma, with the vision
encoder worse in only two of three seeds; the evaluation subset is also redrawn per run
(baseline R@1 0.685-0.695), which inflates the spread.  The ordering the caption asserts is
therefore not supported.

This patch (a) rewrites the caption to describe the figure as the single evaluation it is,
report the seeded result, and say the ordering is not relied on, and (b) checks the rest of
the manuscript for any remaining reliance on that experiment.
"""
import io
import os
import re
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"

OLD = ("\\caption{Parameter noise sensitivity and effective rank tracking. (A) Vision encoder "
       "degrades 2.6$\\times$ more than text encoder under equivalent parameter noise "
       "($\\sigma=0.1$). (B--C) Effective rank of vision and text embeddings under Frozen vs.\\ "
       "text-only fine-tuning.}")
NEW = ("\\caption{Parameter noise sensitivity and effective rank tracking. (A) Retrieval "
       "degradation under Gaussian parameter noise, from the single archived evaluation "
       "(baseline \\Rk{1} 0.705), in which vision noise cost 9.2\\% against 3.6\\% for text "
       "noise at $\\sigma=0.1$. A seeded re-run over three seeds gives $2.2\\% \\pm 4.4$ for the "
       "vision encoder against $-0.0\\% \\pm 1.9$ for the text encoder at the same $\\sigma$, "
       "with the vision encoder worse in only two of the three and the evaluation subset redrawn "
       "each run; the ordering shown here is therefore not stable and no claim rests on it. "
       "(B--C) Effective rank of vision and text embeddings under Frozen vs.\\ text-only "
       "fine-tuning.}")

P = os.path.join(ROOT, "paper", "sections", "supplementary.tex")
src = io.open(P, encoding="utf-8").read()
if OLD not in src:
    print("FAIL: fig9 caption not found")
    sys.exit(1)
io.open(P, "w", encoding="utf-8", newline="").write(src.replace(OLD, NEW, 1))
print("ok   fig9 caption rewritten")

print("\nremaining mentions of noise in the manuscript (check each for reliance):")
for base, _d, files in os.walk(os.path.join(ROOT, "paper", "sections")):
    for f in sorted(files):
        if not f.endswith(".tex"):
            continue
        for i, line in enumerate(io.open(os.path.join(base, f), encoding="utf-8"), 1):
            if re.search(r"noise", line, re.I):
                print("  %s:%d  %s" % (f, i, line.strip()[:130]))
