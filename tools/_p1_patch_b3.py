# -*- coding: utf-8 -*-
"""P1 patch B3: abstract sentence (with the real line breaks) + the control table's
column spec (6 fields in a 5-column tabular caused "Extra alignment tab")."""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"

EDITS = [
    ("paper/main_nn.tex",
     "parsimonious account, and provide direct causal evidence through noise\nsensitivity, gradient analysis, and effective rank tracking.",
     "parsimonious account, and isolate its mechanism with a strict control in\nwhich only the adapters are trainable: the visual encoder then receives no updates at\nall while the gap is still reduced."),
    ("paper/sections/strict_control.tex",
     "\\begin{tabular}{lcccc}",
     "\\begin{tabular}{lccccc}"),
    # keep the generator in step so a re-run does not reintroduce the defect
    ("tools/_p1_patch_b.py",
     "\\begin{tabular}{lcccc}",
     "\\begin{tabular}{lccccc}"),
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
    print(fails)
    sys.exit(1)
print("PATCH B3 APPLIED")
