# -*- coding: utf-8 -*-
"""P1 patch A3: captions for the regenerated fig1 and fig5."""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    ("paper/sections/experiments.tex",
     "\\caption{Modality gap evolution during PEFT. Full fine-tuning explodes the gap; text-only and low-rank configurations preserve or reduce it.}",
     "\\caption{Modality gap evolution during PEFT; all series are Flickr30k runs (batch 128, 10 epochs, 5{,}000 samples, gap evaluated every two epochs). Markers are single archived runs and the shaded band is the mean $\\pm$ standard deviation over five seeds of the text-only configuration. Full fine-tuning enlarges the gap monotonically, both-position LoRA ends slightly below the frozen value, and text-only stays closest to it.}"),
    ("paper/sections/experiments.tex",
     "yet the both-position run (R@1 = 0.66) and the $\\alpha$-annealed text-only run (R@1 = 0.64) later recover, while the plain text-only run does not (R@1 = 0.13), illustrating the premature stopping discussed in the text.",
     "yet the both-position run (R@1 = 0.66) and the $\\alpha$=4 text-only run (R@1 = 0.64) later recover, while the $\\alpha$=16 text-only run does not (R@1 = 0.13) in spite of producing the largest first-checkpoint spike, illustrating the premature stopping discussed in the text."),
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
print("PATCH A3 APPLIED")
