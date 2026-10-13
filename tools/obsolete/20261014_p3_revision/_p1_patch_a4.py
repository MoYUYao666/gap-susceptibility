# -*- coding: utf-8 -*-
"""P1 patch A4: fig7 caption + the §4.3 reference to it (the figure is a bar chart of
the three correlations, not a variance-component decomposition)."""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    ("paper/sections/experiments.tex",
     "We therefore present the variance component $\\sqrt{G_D^2-G_C^2}$ (Figure~\\ref{fig:normcheck}) as a descriptive decomposition of the gap rather than as evidence that DG is an independent predictor, and our monitoring proposal below does not depend on which of the two statistics is used.",
     "Figure~\\ref{fig:normcheck} summarises the comparison: both statistics predict retrieval strongly, the partial correlation of DG controlling for CG ($0.581$) is close to the CG correlation alone ($0.594$), and we therefore treat them as interchangeable rather than as evidence that DG is an independent predictor. Our monitoring proposal below does not depend on which of the two is used."),
    ("paper/sections/experiments.tex",
     "\\caption{Decomposition of the gap into centroid and variance components. DG and CG are strongly collinear in our archive ($r=+0.945$), so the variance component is presented descriptively.}",
     "\\caption{Gap--retrieval correlations over the reproducible archive ($n=204$). Both gap statistics predict retrieval strongly, but DG and CG are themselves correlated at $r=+0.945$, and partialling out CG leaves DG at $0.581$---close to the CG correlation itself. The two measures are therefore close to interchangeable here.}"),
]
fails = []
for rel, old, new in EDITS:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    src = io.open(p, encoding="utf-8").read()
    n = src.count(old)
    if n != 1:
        fails.append("%s: found %d" % (rel, n))
        print("FAIL %s (%d)" % (rel, n))
        continue
    io.open(p, "w", encoding="utf-8", newline="").write(src.replace(old, new, 1))
    print("ok   %s" % rel)
if fails:
    print(fails)
    sys.exit(1)
print("PATCH A4 APPLIED")
