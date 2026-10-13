# -*- coding: utf-8 -*-
"""
P1 patch F: round-2 artefact-review fixes.

F1 Table 1 (tab:overview) printed the Adapter best CG delta as the own-baseline -0.217 under
   a caption that promises the best change relative to the frozen baseline; the frozen-
   relative value is +0.064 (outputs/analysis/adapter_common_baseline.json).
F2 two bibliography notes were written as multi-line fields with protected braces, which is
   what the review saw as garbled output; simplified to single lines.
F3 the manuscript carried no Funding statement and no generative-AI declaration, although the
   author used both tools (declared in the A1 package) and Elsevier requires the declaration.
   Added with the same wording as A1.
F4-F6 file-level items (regenerating the stale declaration/cover-letter PDFs, archiving the
   pre-remediation artefacts, the revision letter's Prefix claim) are handled outside this
   script.

Rejected: the review's note that "p = 0.70, Welch" should be 0.66-0.67. Recomputed with the
sample standard deviation (the convention the paper uses elsewhere, sd 0.00303) the strict
vs mixed comparison gives t = -0.398, p = 0.7017.
"""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    ("paper/sections/experiments.tex",
     "Adapter & 7 & $-$0.217 & 0.574 \\\\",
     "Adapter & 7 & $+$0.064 & 0.574 \\\\"),
    ("paper/references.bib",
     "  doi       = {10.48550/arXiv.2510.03268},\n  note      = {The Convergent Representation of Contrastive Vision-Language Models: Geometry, Modality Gap and Shared Space Alignment (ICML 2026 version)},\n}",
     "  doi       = {10.48550/arXiv.2510.03268},\n  note      = {ICML 2026 version: The Convergent Representation of Contrastive Vision-Language Models},\n}"),
    ("paper/references.bib",
     "  doi       = {10.48550/arXiv.2512.18504},\n  note      = {Published version: IEEE Xplore, document 11463397 (title: {GTMA}:\n               Dynamic Representation Optimization for {OOD} {VLMs})},\n}",
     "  doi       = {10.48550/arXiv.2512.18504},\n  note      = {Published version: IEEE Xplore document 11463397},\n}"),
    ("paper/main_nn.tex",
     "\\section*{Data availability}\nData will be made available on request.\n\n\\bibliographystyle{elsarticle-num}",
     "\\section*{Data availability}\nAll datasets and model releases used in this study are public; every result JSON, analysis\nscript and figure is archived in the project repository, which will be made public on\npublication (available to the reviewers on request).\n\n"
     "\\section*{Funding}\nThis research did not receive any specific grant from funding agencies in the public,\ncommercial, or not-for-profit sectors.\n\n"
     "\\section*{Declaration of generative AI and AI-assisted technologies in the manuscript preparation process}\n"
     "During the preparation of this work the author used Claude (Anthropic) and DeepSeek V4 in\n"
     "order to draft and revise the manuscript text and to prepare experimental code and figures.\n"
     "After using these tools, the author reviewed and edited the content as needed and takes full\n"
     "responsibility for the content of the published article.\n\n"
     "\\bibliographystyle{elsarticle-num}"),
    # the revision letter must not claim a Prefix comparison the manuscript does not contain
    ("paper/cover_letter_revision.tex",
     "the Adapter and Prefix comparisons, the layered fine-tuning results",
     "the Adapter comparison, the layered fine-tuning results"),
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
    print("\nFAILURES (%d):" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("\nPATCH F APPLIED")
