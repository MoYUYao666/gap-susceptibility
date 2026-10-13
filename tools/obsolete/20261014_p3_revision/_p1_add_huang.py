# -*- coding: utf-8 -*-
"""
Add the Huang et al. ICCV 2025 citation supplied by the operator.

It is the closest prior work to the novelty claim: it preserves and compensates the modality
gap in CLIP-based continual learning, i.e. it acts on the gap during adaptation, whereas this
manuscript characterises how the gap evolves under PEFT position, rank and scaling choices
and isolates the mechanism with a strict control.  The claim wording already dropped "first";
this adds the citation so the positioning is explicit.

Entry inserted after hu2021lora to keep the bibliography alphabetical; cited in the related
work section and in the introduction's positioning sentence.
"""
import io
import os
import re
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
BIB = os.path.join(ROOT, "paper", "references.bib")

ENTRY = """@inproceedings{huang2025mindgap,
  author    = {Huang, Linlan and Cao, Xusheng and Lu, Haori and Meng, Yifan
               and Yang, Fei and Liu, Xialei},
  title     = {Mind the Gap: Preserving and Compensating for the Modality Gap
               in {CLIP}-Based Continual Learning},
  booktitle = {Proceedings of the IEEE/CVF International Conference on Computer
               Vision (ICCV)},
  month     = {October},
  year      = {2025},
  pages     = {3777--3786},
}

"""

src = io.open(BIB, encoding="utf-8").read()
if "huang2025mindgap" in src:
    print("entry already present")
else:
    m = re.search(r"@\w+\{hu2021lora,.*?\n\}\n", src, re.S)
    if not m:
        print("FAIL: hu2021lora entry not found")
        sys.exit(1)
    src = src[:m.end()] + "\n" + ENTRY + src[m.end():]
    io.open(BIB, "w", encoding="utf-8", newline="").write(src)
    print("ok   bib entry inserted after hu2021lora")

EDITS = [
    ("paper/sections/related_work.tex",
     "Recent theoretical work has deepened our understanding:",
     "The gap has also become an object of intervention rather than only of analysis: \\cite{huang2025mindgap} preserve and compensate it in CLIP-based continual learning, acting on the gap during adaptation. Recent theoretical work has deepened our understanding:"),
    ("paper/sections/introduction.tex",
     "we provide a systematic study of how these metrics evolve \\textit{dynamically} during fine-tuning---revealing non-monotonic interactions between PEFT configuration choices and gap evolution that are invisible in static analysis alone.",
     "we provide a systematic study of how these metrics evolve \\textit{dynamically} during fine-tuning---revealing non-monotonic interactions between PEFT configuration choices and gap evolution that are invisible in static analysis alone. Closely related, \\cite{huang2025mindgap} preserve and compensate the modality gap in CLIP-based continual learning, that is, they act on the gap during adaptation; what we characterise is how the gap responds to the choice of where, how much and at what rank to adapt, and what that response implies for monitoring."),
]
fails = []
for rel, old, new in EDITS:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    s = io.open(p, encoding="utf-8").read()
    n = s.count(old)
    if n != 1:
        fails.append("%s: found %d :: %s" % (rel, n, old[:60]))
        print("FAIL %s (%d)" % (rel, n))
        continue
    io.open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new, 1))
    print("ok   %s" % rel)
if fails:
    print(fails)
    sys.exit(1)
print("HUANG CITATION ADDED")
