# -*- coding: utf-8 -*-
"""P1 patch B2: the abstract sentence, split at the line breaks that actually exist."""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
P = os.path.join(ROOT, "paper", "main_nn.tex")
EDITS = [
    ("and provide direct causal evidence",
     "and isolate its mechanism with a strict control in which only the adapters are trainable"),
    ("through noise sensitivity, gradient analysis, and effective rank tracking. Building on our",
     "the visual encoder then receives no updates at all while the gap is still reduced. Building on our"),
]
src = io.open(P, encoding="utf-8").read()
for i, (old, new) in enumerate(EDITS, 1):
    n = src.count(old)
    if n != 1:
        print("FAIL #%d (%d): %s" % (i, n, old[:60]))
        sys.exit(1)
    src = src.replace(old, new, 1)
    print("ok #%d" % i)
io.open(P, "w", encoding="utf-8", newline="").write(src)
print("PATCH B2 APPLIED")
