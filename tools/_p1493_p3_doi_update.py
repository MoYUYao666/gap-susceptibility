# -*- coding: utf-8 -*-
r"""Point the P3 manuscript and submission fields at the v2.2 Zenodo version DOI (10.5281/zenodo.23523263).

    python tools/_p1493_p3_doi_update.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD = "10.5281/zenodo.23341223"
NEW = "10.5281/zenodo.23523263"
FILES = [
    "paper3/paper_ieee/main.tex",
    "paper3/paper_ieee/sections/conclusion.tex",
    "paper3/paper_ieee/audit_check.py",
    "paper3/paper_ieee/audit_pdf.py",
    "SUBMISSION/P3_PRL_resubmission/EM_FIELDS.md",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for rel in FILES:
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            print("  missing", rel)
            continue
        t = io.open(p, encoding="utf-8").read()
        if OLD not in t:
            print("  no old DOI in", rel)
            continue
        io.open(p, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW))
        print("  updated", rel)
    if a.apply:
        for tex in ("paper3/paper_ieee/main.tex", "paper3/paper_ieee/cover_letter_prl_resubmission.tex"):
            d = os.path.dirname(os.path.join(REPO, tex))
            r = subprocess.run(["pdflatex", "-interaction=nonstopmode", os.path.basename(tex)], cwd=d,
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            print("  rebuilt", tex, "exit", r.returncode)
        for script in ("paper3/paper_ieee/audit_check.py", "paper3/paper_ieee/audit_pdf.py"):
            r = subprocess.run([sys.executable, script], cwd=REPO, capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
            print("  ", script, "exit", r.returncode, "|", tail[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
