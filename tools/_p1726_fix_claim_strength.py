# -*- coding: utf-8 -*-
r"""Two remaining claim-strength defects found by reading the built PDF:

  1. the abstract still says the Distribution Gap *predicts* retrieval degradation, while the paper's own
     position (and its earlier correction) is "association, not a predictor";
  2. the ODE fit is said to *outperform* the linear baseline, but the margin is 0.949 vs 0.946.

Fix both in every live copy (Paper A variants and the reframed tree) with asserted replacements.
"""
import io
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FILES = [
    "paper合/main_nc.tex",
    "paper合/main_springer.tex",
    "paper合/reframed/main.tex",
    "paper合/reframed/new/front.tex",
]

OLD_ABSTR = "the Distribution Gap predicts retrieval degradation"
NEW_ABSTR = "the Distribution Gap is more strongly associated with retrieval degradation"
OLD_BETTER = "better than the Centroid Gap"
NEW_BETTER = "than the Centroid Gap is"

for p in FILES:
    if not os.path.isfile(p):
        print("  skip (absent):", p)
        continue
    t = io.open(p, encoding="utf-8").read()
    before = t
    if OLD_ABSTR in t:
        t = t.replace(OLD_ABSTR, NEW_ABSTR)
    if OLD_BETTER in t:
        t = t.replace(OLD_BETTER, NEW_BETTER)
    if t != before:
        io.open(p, "w", encoding="utf-8", newline="").write(t)
        print("  abstract fixed:", p)

# ODE fit wording (source of truth + the generated reframed copy)
FIT = [
    ("paper合/sections/validation.tex",
     "outperforming the constant baseline ($R^2=0.00$) and the linear baseline (mean $R^2=0.946$)",
     "above the constant baseline ($R^2=0.00$) and marginally above the linear baseline (mean $R^2=0.946$)"),
    ("paper合/sections/conclusion.tex",
     "substantially outperforming the constant baseline",
     "well above the constant baseline"),
]
for p, old, new in FIT:
    t = io.open(p, encoding="utf-8").read()
    if old not in t:
        print("  WARNING: sentence not found in", p)
        continue
    io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
    print("  fit wording fixed:", p)
print("done")
