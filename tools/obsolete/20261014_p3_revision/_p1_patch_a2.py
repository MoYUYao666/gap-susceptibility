# -*- coding: utf-8 -*-
"""P1 patch A2: the matched d=16 Adapter pair (+0.2368 / +0.5003), not the 5-run mean."""
import io
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    ("paper/sections/introduction.tex",
     "Adapter, measured against the frozen model ($+0.185$ vs. $+0.500$)",
     "Adapter, measured against the frozen model ($+0.237$ vs. $+0.500$)"),
    ("paper/sections/experiments.tex",
     "than both-position Adapter ($+0.185$ vs. $+0.500$, measured against the frozen baseline)",
     "than both-position Adapter ($+0.237$ vs. $+0.500$, measured against the frozen baseline)"),
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
print("PATCH A2 APPLIED")
