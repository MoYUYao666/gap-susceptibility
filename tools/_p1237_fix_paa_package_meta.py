# -*- coding: utf-8 -*-
r"""Fix the package README page counts and register PAA_submission in the a1_paa audit profile.

The cover letter came out at one page, not two; the README should state measured values. The profile should also check
the package that now exists, so a missing or renamed file is an audit failure rather than a surprise at submission.

    python tools/_p1237_fix_paa_package_meta.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "paper_a1", "PAA_submission")
PROFILES = os.path.join(REPO, "tools", "paper_audit", "profiles.py")


def pages(pdf):
    from pypdf import PdfReader
    return len(PdfReader(pdf).pages)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ms = pages(os.path.join(OUT, "Manuscript.pdf"))
    tp = pages(os.path.join(OUT, "Title Page.pdf"))
    cl = pages(os.path.join(OUT, "Cover Letter.pdf"))
    print(f"  measured pages: manuscript={ms} title={tp} cover={cl}")

    readme = os.path.join(OUT, "README.md")
    t = io.open(readme, encoding="utf-8").read()
    t = t.replace("| Cover Letter | `Cover Letter.pdf` | 2 pages;", f"| Cover Letter | `Cover Letter.pdf` | {cl} page;")
    t = t.replace("| Title page | `Title Page.pdf` | 1 page;", f"| Title page | `Title Page.pdf` | {tp} page;")
    t = t.replace("| Manuscript | `Manuscript.pdf` | %d pages" % ms, f"| Manuscript | `Manuscript.pdf` | {ms} pages")

    # register the package in the profile
    p = io.open(PROFILES, encoding="utf-8").read()
    old = ('        build_command=["pdflatex", "-interaction=nonstopmode", "main.tex"],\n'
           '        freeze_paths=["SUBMISSION/A1_NeuralNetworks"],\n'
           '        notes=("Prepared for Pattern Analysis and Applications (SCIE); not yet submitted. "')
    new = ('        package="paper_a1/PAA_submission",\n'
           '        package_expected=["Manuscript.pdf", "Title Page.pdf", "Cover Letter.pdf",\n'
           '                          "latex_source.zip", "README.md"],\n'
           '        package_map=[["main.pdf", "Manuscript.pdf"], ["title_page.pdf", "Title Page.pdf"],\n'
           '                     ["cover_letter_paa.pdf", "Cover Letter.pdf"]],\n'
           '        cover_letter="cover_letter_paa.tex",\n'
           '        build_command=["pdflatex", "-interaction=nonstopmode", "main.tex"],\n'
           '        freeze_paths=["SUBMISSION/A1_NeuralNetworks"],\n'
           '        notes=("Prepared for Pattern Analysis and Applications (SCIE); package built, not yet submitted. "')
    n = p.count(old)
    print(f"  profile block: {n}")
    if n == 1:
        p = p.replace(old, new, 1)
    else:
        print("  !! profile block not found verbatim; leaving profile unchanged")
        p = None

    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(readme, "w", encoding="utf-8", newline="").write(t)
    print("  README updated")
    if p is not None:
        io.open(PROFILES, "w", encoding="utf-8", newline="").write(p)
        print("  profile updated (package registered)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
