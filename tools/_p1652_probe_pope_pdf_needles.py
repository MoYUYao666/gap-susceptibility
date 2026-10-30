#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1652_probe_pope_pdf_needles.py -- print the pdftotext text around the POPE table so the
numeric-grid needle can be written against what pdftotext actually emits."""
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDF = ROOT / "paper3/paper_ieee/supplementary/supplementary.pdf"

txt = subprocess.run(["pdftotext", str(PDF), "-"], capture_output=True, text=True,
                     encoding="utf-8", errors="replace").stdout
i = txt.find("POPE second downstream")
print("=== raw text around the POPE table ===")
print(txt[max(0, i - 200):i + 1400])

flat = re.sub(r"\s+", "", txt)
print("\n=== flattened numeric run around 0.6257 ===")
j = flat.find("0.6257")
print(flat[max(0, j - 120):j + 220])
