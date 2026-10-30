# -*- coding: utf-8 -*-
r"""Fix the P2 audit items: cover-letter page counts, beta CV rounding, builder zip-exclude support.

    python tools/_p1471_fix_p2_items.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDER = os.path.join(REPO, "tools", "_p1336_build_venue_package.py")
LETTERS = [
    (os.path.join(REPO, "paper_a1", "cover_letter_paa_revision.tex"), "The manuscript is 61 pages",
     "The manuscript is 64 pages"),
    (os.path.join(REPO, "paper合", "cover_letter_nc_revision.tex"), "manuscript is 72 pages",
     "manuscript is 74 pages"),
    (os.path.join(REPO, "paper3", "paper_ieee", "cover_letter_prl_revision.tex"),
     "10 pages of main text plus 6 pages of supplementary material.",
     "10 pages of main text plus 7 pages of supplementary material."),
]
ODE = os.path.join(REPO, "paper合", "sections", "ode_diagnostics_appendix.tex")


def patch_builder():
    t = io.open(BUILDER, encoding="utf-8").read()
    if "--zip-exclude" in t:
        return False
    t = t.replace('    ap.add_argument("--source", default=None, help="directory whose .tex files and figures are zipped")',
                  '    ap.add_argument("--source", default=None, help="directory whose .tex files and figures are zipped")\n'
                  '    ap.add_argument("--zip-exclude", default="", help="comma-separated file names to omit from latex_source.zip")', 1)
    old = '''        tex_files = sorted(glob.glob(os.path.join(src_dir, "*.tex")))'''
    new = '''        excl = {x.strip() for x in a.zip_exclude.split(",") if x.strip()}
        tex_files = [f for f in sorted(glob.glob(os.path.join(src_dir, "*.tex")))
                     if os.path.basename(f) not in excl]'''
    assert t.count(old) == 1
    t = t.replace(old, new, 1)
    io.open(BUILDER, "w", encoding="utf-8", newline="").write(t)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    # cover-letter page counts
    for path, old, new in LETTERS:
        t = io.open(path, encoding="utf-8").read()
        if old in t:
            io.open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            print("  updated", os.path.basename(path))
    # beta CV rounding
    t = io.open(ODE, encoding="utf-8").read()
    if "1.27--1.77" in t:
        io.open(ODE, "w", encoding="utf-8", newline="").write(t.replace("1.27--1.77", "1.27--1.76", 1))
        print("  beta CV fixed to 1.27--1.76")
    # builder support for excluding stale cover letters from the source zip
    print("  builder patched:", patch_builder())
    # rebuild the three revision cover letters
    for path in ("paper_a1/cover_letter_paa_revision.tex", "paper合/cover_letter_nc_revision.tex",
                 "paper3/paper_ieee/cover_letter_prl_revision.tex"):
        d = os.path.dirname(os.path.join(REPO, path))
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", os.path.basename(path)], cwd=d,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        print("  rebuilt", path, "exit", r.returncode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
