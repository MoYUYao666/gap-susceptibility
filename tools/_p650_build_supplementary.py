# -*- coding: utf-8 -*-
r"""Recompile the supplementary material from the correct directory.

My mistake: I ran pdflatex on supplementary/supplementary.tex from paper_ieee/, but the file
includes figures as "../figures/fig3_ers.png", i.e. relative to its own directory. So the
compile must run with supplementary/ as the working directory, which is how it was built
before.

Also verifies the staged copy is the freshly built one (the earlier run failed, so the old
file was left in place).

    python tools/_p650_build_supplementary.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary"
STAGE = REPO / "SUBMISSION" / "P3_PRL_revision" / "UPLOAD"
PKG = REPO / "SUBMISSION" / "P3_PRL_revision" / "manuscript"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print(f"  working directory: {SUPP.relative_to(REPO)}")
    print(f"  before: supplementary.pdf sha {sha(SUPP / 'supplementary.pdf') if (SUPP / 'supplementary.pdf').exists() else '-'}")
    if not a.apply:
        print("  (dry run)")
        return 0
    for k in range(2):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                            "supplementary.tex"], cwd=str(SUPP), capture_output=True)
        out = r.stdout.decode("utf-8", errors="replace")
        errs = re.findall(r"^! (.*)$", out, re.M)
        pages = re.findall(r"Output written on supplementary\.pdf \((\d+) pages", out)
        print(f"  pass {k+1}: rc={r.returncode}  pages={pages[0] if pages else '?'}  "
              f"errors={len(errs)}")
        for e in errs[:4]:
            print(f"      ! {e[:110]}")
        if r.returncode != 0:
            return 1
    pdf = SUPP / "supplementary.pdf"
    print(f"  after:  supplementary.pdf sha {sha(pdf)}  ({pdf.stat().st_size:,} bytes)")
    shutil.copy2(pdf, STAGE / "P3_PRLETTERS-D-26-02378_Supplementary.pdf")
    shutil.copy2(pdf, PKG / "supplementary.pdf")
    print(f"  staged  P3_PRLETTERS-D-26-02378_Supplementary.pdf "
          f"({(STAGE / 'P3_PRLETTERS-D-26-02378_Supplementary.pdf').stat().st_size:,} bytes)")
    # confirm the new title is inside the rebuilt PDF
    r = subprocess.run(["pdftotext", "-q", "-layout", str(pdf), "-"], capture_output=True)
    t = re.sub(r"[\s\u00ad]+", "", r.stdout.decode("utf-8", errors="replace"))
    has_new = "Zero-ShotCross-ArchitectureRankAllocation" in t
    has_old = "GradientStructureLaws" in t
    print(f"  new title present: {has_new}  |  old title present: {has_old}")
    return 0 if has_new and not has_old else 1


if __name__ == "__main__":
    raise SystemExit(main())
