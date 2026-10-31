#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1651_check_supp_pages.py -- where the POPE subsection lands and whether any page is
mostly blank (float-placement artefact), after the supplement edit."""
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUPP = ROOT / "paper3/paper_ieee/supplementary/supplementary.pdf"

n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(SUPP)],
                                                    capture_output=True, text=True,
                                                    encoding="utf-8", errors="replace").stdout).group(1))
print("pages:", n)
for p in range(1, n + 1):
    out = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), str(SUPP), "-"],
                         capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout or ""
    t = re.sub(r"\s+", " ", out)
    marks = []
    if "second downstream task: POPE" in t or "POPE second downstream task" in t:
        marks.append("POPE")
    for m in re.finditer(r"VQA-RAD downstream check", t):
        marks.append("VQA")
    secs = re.findall(r"S(\d+)\s+[A-Z]", t)
    print("  p%-2d chars=%-5d %-10s %s" % (p, len(t), ",".join(sorted(set(marks))),
                                            ("starts S%s" % secs[0]) if secs else ""))
