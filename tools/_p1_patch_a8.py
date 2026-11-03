# -*- coding: utf-8 -*-
"""P1 patch A8: the effective-rank definition in the supplementary footnote was a third,
different definition from the one the tracking code and Figure 8 use."""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    ("paper/sections/supplementary.tex",
     "$^c$Effective rank of image embeddings (threshold 0.99 explained variance); text-only preserves rank.",
     "$^c$Effective rank of layer-wise image embeddings, $\\exp(-\\sum_i p_i\\log p_i)$ with $p_i$ the normalised singular values of the mean-pooled token representations (the definition used by the tracking code); the legacy text-only runs reduce it, while the strict control leaves it exactly unchanged (Section~\\ref{sec:strictcontrol})."),
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
print("PATCH A8 APPLIED")
