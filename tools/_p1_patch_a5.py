# -*- coding: utf-8 -*-
"""P1 patch A5: Table 4 (cross-method comparison) — group means, common baseline, n stated.

Fixes an inconsistency introduced by patch A: the Adapter row was given the best-config
value (+0.064, d=64) inside a column headed "Mean CG Delta".  The group mean on the common
baseline is +0.229 over the seven archived Adapter runs (R@1 mean 0.173).  Full fine-tuning
is the five-seed mean +0.191 (R@1 mean 0.5972, outputs/flickr30k_seeds/summary.json).
"""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    ("paper/sections/experiments.tex",
     "\\caption{Cross-method comparison.}",
     "\\caption{Cross-method comparison: group means over the archived runs, all deltas measured against the frozen model on the identical protocol (CG 0.818). Adapter $n=7$ runs; full fine-tuning $n=5$ seeds; the LoRA row is the mean over the LoRA catalog. The right-hand column names the best configuration of each group rather than its mean.}"),
    ("paper/sections/experiments.tex",
     "LoRA & $-$0.004 & 0.669 & $r$=8, $\\alpha$=64, text-only \\\\\nAdapter & $+$0.064 & 0.574 & $d$=64, text-only (vs.\\ frozen) \\\\\nFull FT & $+$0.199 & 0.527 & N/A \\\\",
     "LoRA & $-$0.004 & 0.669 & $r$=8, $\\alpha$=64, text-only \\\\\nAdapter & $+$0.229 & 0.173 & $d$=64, text-only ($+$0.064, R@1 0.574) \\\\\nFull FT & $+$0.191 & 0.597 & N/A \\\\"),
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
print("PATCH A5 APPLIED")
