# -*- coding: utf-8 -*-
r"""Compile the freshly built P3 source archive in a temporary folder and report what fails.

The rebuild script's own check caught that the extracted supplement does not compile cleanly. This keeps
the extracted tree and prints the first errors so the cause is visible.

    python tools/_p934_probe_source_zip.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ZIP = REPO / "SUBMISSION" / "P3_PRL_revision" / "UPLOAD_2026-10-15" / "P3_PRLETTERS-D-26-02378_LaTeX_Source.zip"

tmp = Path(tempfile.mkdtemp(prefix="p3_probe_"))
print(f"  extracted to {tmp}")
with zipfile.ZipFile(ZIP) as z:
    z.extractall(tmp)
    print(f"  entries: {len(z.namelist())}")

for folder, stem in ((tmp, "main"), (tmp / "supplementary", "supplementary")):
    for cmd in (["pdflatex", "-interaction=nonstopmode", f"{stem}.tex"],
                ["bibtex", stem],
                ["pdflatex", "-interaction=nonstopmode", f"{stem}.tex"],
                ["pdflatex", "-interaction=nonstopmode", f"{stem}.tex"]):
        subprocess.run(cmd, cwd=folder, capture_output=True)
    log = (folder / f"{stem}.log").read_text(encoding="utf-8", errors="replace")
    errs = [l for l in log.splitlines() if l.startswith("!")]
    undef = sorted(set(re.findall(r"(?:Reference|Citation) `([^']+)'", log)))
    print()
    print(f"=== {stem}: {len(errs)} errors, {len(undef)} undefined {undef[:6]}")
    for e in errs[:6]:
        print(f"    {e[:120]}")
    # the source line each error points at
    for m in list(re.finditer(r"^!.*?\n(?:.*\n){0,4}?l\.(\d+)(.*)$", log, re.M))[:6]:
        print(f"    error at {stem}.tex:{m.group(1)} -> {m.group(2)[:90]}")
    if (folder / f"{stem}.pdf").exists():
        import pypdf
        print(f"    pages: {len(pypdf.PdfReader(str(folder / (stem + '.pdf'))).pages)}")
    else:
        print("    no PDF produced")
print()
print(f"  kept for inspection: {tmp}")
