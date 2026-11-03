# -*- coding: utf-8 -*-
r"""Work out which manuscript version each part of the 33-page merged PDF contains.

Page 1 is the journal's record page. Page 5 starts a manuscript whose title is the OLD one and
whose affiliation line still reads "School of Electronics and Computer Science"; page 21 starts
a manuscript with the NEW title. If the attached Manuscript file is the 12 October version,
the reviewer is reading the pre-revision paper - which would explain the withdrawn claims
("unique admissible", "sharp phase transition") appearing inside a manuscript rather than only
in the cover letter.

This measures each manuscript-looking section against both versions.

    python tools/_p674_identify_versions.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PDF = Path(r"C:\Users\hongr\Desktop\PRLETTERS-D-26-02378_R1.pdf")
NEW_PDF = REPO / "SUBMISSION" / "P3_PRL_revision" / "manuscript" / "main.pdf"
OLD_PDF = (REPO / "SUBMISSION" / "_superseded_P3_PRL_submitted_2026-09-26"
           / "manuscript.pdf")

# markers that distinguish the two versions without ambiguity
NEW_ONLY = [
    "Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry",
    "2344",            # 6-seed corner value
    "1477",            # 6-seed interior value
    "10.5281/zenodo.23341223",
]
OLD_ONLY = [
    "Gradient Structure Laws as Predictors of PEFT Design",
    "3607",            # superseded 3-seed corner value
    "2241",            # superseded 3-seed interior value
    "School of Electronics and Computer Science",
]


def text_of(p: Path) -> str:
    if not p.exists():
        return ""
    r = subprocess.run(["pdftotext", "-q", "-layout", str(p), "-"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    full = text_of(PDF)
    pages = full.split("\f")
    print(f"  merged file: {len(pages)} pages, {len(full):,} characters")

    print()
    print("=" * 100)
    print("reference files on disk")
    print("=" * 100)
    for label, p in (("revision main.pdf", NEW_PDF), ("old submitted manuscript", OLD_PDF)):
        t = text_of(p)
        print(f"  {label:<30} exists={p.exists()}  chars={len(t):,}")
        for s in NEW_ONLY[:2] + OLD_ONLY[:2]:
            if s.replace(" ", "") in re.sub(r"\s+", "", t):
                print(f"      contains: {s}")

    print()
    print("=" * 100)
    print("per page: which version's markers are present")
    print("=" * 100)
    print(f"  {'pg':>3}  {'new-title':>9} {'old-title':>9} {'2344':>5} {'3607':>5} "
          f"{'Sci-and-Eng':>11} {'chars':>7}")
    sections = []
    for i, pg in enumerate(pages, 1):
        flat = re.sub(r"\s+", "", pg)
        marks = {
            "new_title": "Zero-ShotCross-ArchitectureRankAllocationfromGradientGeometry" in flat,
            "old_title": "GradientStructureLawsasPredictors" in flat,
            "2344": "2344" in flat,
            "3607": "3607" in flat,
            "scieng": "SchoolofElectronicsandComputerScience" in flat,
        }
        if any(marks.values()):
            print(f"  {i:>3}  {str(marks['new_title']):>9} {str(marks['old_title']):>9} "
                  f"{str(marks['2344']):>5} {str(marks['3607']):>5} "
                  f"{str(marks['scieng']):>11} {len(pg):>7}")
        sections.append((i, marks, len(pg)))

    print()
    print("=" * 100)
    print("sections that look like a full manuscript (contain an abstract)")
    print("=" * 100)
    for i, pg in enumerate(pages, 1):
        if re.search(r"Abstract[—\-–]", pg) or "Abstract:" in pg:
            flat = re.sub(r"\s+", "", pg)
            which = []
            if "Zero-ShotCross-ArchitectureRankAllocationfromGradientGeometry" in flat:
                which.append("NEW")
            if "GradientStructureLawsasPredictors" in flat:
                which.append("OLD")
            print(f"  page {i}: {'/'.join(which) or '?'}  ({len(pg):,} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
