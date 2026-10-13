# -*- coding: utf-8 -*-
"""Follow-ups from the noise finding: drop the 'causal evidence' label and annotate the
footnote that describes the noise protocol."""
import io
import os
import re
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
EDITS = [
    ("paper/sections/experiments.tex",
     "5-seed statistical verification, causal evidence (noise sensitivity, gradient analysis, effective rank), layered fine-tuning",
     "5-seed statistical verification, mechanism probes (noise sensitivity, gradient analysis, effective rank), layered fine-tuning"),
    ("paper/sections/supplementary.tex",
     "$^a$R@1 degradation under Gaussian parameter noise ($\\mu$=0, $\\sigma$=0.1) applied to vision/text encoder weights.",
     "$^a$R@1 degradation under Gaussian parameter noise ($\\mu$=0, $\\sigma$=0.1) applied to vision/text encoder weights; the archived evaluation is a single draw and the seeded re-run in Figure~\\ref{fig:noise_sensitivity} does not reproduce a stable vision-versus-text ordering, so no claim rests on this row."),
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

print("\nremaining 'causal' in the manuscript:")
hits = 0
for base, _d, files in os.walk(os.path.join(ROOT, "paper", "sections")):
    for f in sorted(files):
        if not f.endswith(".tex"):
            continue
        for i, line in enumerate(io.open(os.path.join(base, f), encoding="utf-8"), 1):
            if re.search(r"causal", line, re.I):
                hits += 1
                print("  %s:%d  %s" % (f, i, line.strip()[:130]))
if not hits:
    print("  (none)")
if fails:
    sys.exit(1)
