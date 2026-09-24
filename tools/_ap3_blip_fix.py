# -*- coding: utf-8 -*-
"""
ap3-side cleanup: the merged manuscript calls the third backbone BLIP-2 and cites the
Q-Former paper (li2023blip2), while the numbers it quotes (+0.047 vs +0.152, R@1 0.175) are
P1's BLIP-1 runs.  P1's methodology describes those runs as "BLIP-1 ... cross-attention
decoder, BERT text encoder ... ITC + ITM + LM", which is BLIP-1 (li2022blip), and ap3's own
refs.bib already carries both entries.  Aligned with the source of the numbers.

Not touched here: ap3 also quotes P1's superseded r = -0.827 and its 116-experiment count;
those belong to ap3's own pre-submission pass and are listed in docs/P1_REMEDIATION_LOG.md.
"""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    ("paper_ap3/sections/04_mechanism.tex",
     "BLIP-2 (350M, Q-Former)~\\cite{li2023blip2}", "BLIP-1~\\cite{li2022blip}"),
    ("paper_ap3/sections/04_mechanism.tex",
     "On BLIP-2, text-only produces", "On BLIP-1, text-only produces"),
    ("paper_ap3/sections/04_mechanism.tex",
     "on Flickr30k, BLIP-2 and ViT-L", "on Flickr30k, BLIP-1 and ViT-L"),
    ("paper_ap3/sections/04_mechanism.tex",
     "BLIP-2    & $\\mathbf{+0.047}$", "BLIP-1    & $\\mathbf{+0.047}$"),
    ("paper_ap3/sections/01_intro.tex",
     "CLIP ViT-L/14, BLIP-2, SigLIP)", "CLIP ViT-L/14, BLIP-1, SigLIP)"),
    ("paper_ap3/sections/08_conclusion.tex",
     "CLIP ViT-B/32, BLIP-2, SigLIP)", "CLIP ViT-B/32, BLIP-1, SigLIP)"),
]
fails = []
for rel, old, new in EDITS:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    src = io.open(p, encoding="utf-8").read()
    n = src.count(old)
    if n != 1:
        fails.append("%s: found %d :: %s" % (rel, n, old[:50]))
        print("FAIL %s (%d)" % (rel, n))
        continue
    io.open(p, "w", encoding="utf-8", newline="").write(src.replace(old, new, 1))
    print("ok   %s" % rel)

# confirm no stray BLIP-2 references remain in ap3 prose
stray = []
for base, _dirs, files in os.walk(os.path.join(ROOT, "paper_ap3", "sections")):
    for f in files:
        if f.endswith(".tex"):
            s = io.open(os.path.join(base, f), encoding="utf-8").read()
            if "BLIP-2" in s:
                stray.append(f)
print("remaining BLIP-2 mentions in ap3: %s" % (stray or "none"))

if fails:
    print(fails)
    sys.exit(1)
print("AP3 BLIP FIX APPLIED")
