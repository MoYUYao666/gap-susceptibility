"""Add CoverLetter.pdf to the staged A23 next-revision package and keep its listing consistent.

The package (`SUBMISSION/A2_JOE_next_revision/`) previously recorded CoverLetter as "not supplied".
This script:

  1. verifies the built `CoverLetter.pdf` (exists, 1-2 pages, readable by pypdf, no `_` in the upload
     filename);
  2. updates the two README rows that say the cover letter is not supplied;
  3. removes LaTeX build by-products (`*.aux`, `*.out`, `*.log`) so the package stays upload-clean;
  4. rewrites `SHA256SUMS.txt` over every remaining file except itself (the package's own convention:
     README.md is listed, SHA256SUMS.txt is not), and prints the listing.

It never touches a manuscript source, `SUBMISSION/A23_JOE/`, or `SUBMISSION/_frozen_submitted/`.

Idempotent: a README that already mentions CoverLetter.pdf is left alone; the hash file is always
recomputed from the current bytes.

Usage:
    python tools/_p1667_a23_coverletter_package.py [--apply]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "SUBMISSION" / "A2_JOE_next_revision"
PDF = PKG / "CoverLetter.pdf"
SUMS = PKG / "SHA256SUMS.txt"
README = PKG / "README.md"

ROW_A_OLD = "| Cover letter | `-` | not supplied |"
ROW_A_NEW = ("| Cover letter | `CoverLetter.pdf` | 2 pages; revision letter "
             "(source: `revision_cover_letter.tex`) |")

ROW_B_OLD = ("| `CoverLetter.pdf` | not supplied: the submission-era cover letter is stale, the revision "
             "letter is still to be written |")
ROW_B_NEW = ("| `CoverLetter.pdf` | **written 2026-10-25** from `revision_cover_letter.tex`: 2 pages, "
             "0 LaTeX errors, 0 overfull boxes, Times-compatible fonts (TeXGyreTermesX text + newtx math). "
             "It states that the multi-encoder transfer analysis is new material added after submission, "
             "that the added claim is bounded (21 units / 441 pairs / 29 survivors, all sonar-target), the "
             "new fifth limitation, the 64 -> 73 page growth, and the v2.5 archive DOI cited by the current "
             "draft |")

BYPRODUCTS = ("*.aux", "*.out", "*.log")


def sha256_of(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rc = 0

    if not PDF.is_file():
        print("ERROR: %s missing - build it first (pdflatex -jobname=CoverLetter revision_cover_letter.tex)" % PDF)
        return 2
    from pypdf import PdfReader
    pages = len(PdfReader(str(PDF)).pages)
    print("CoverLetter.pdf: %d pages, %d bytes, underscore in name: %s"
          % (pages, PDF.stat().st_size, "_" in PDF.name))
    if not 1 <= pages <= 2:
        print("ERROR: the letter must be 1-2 pages, got %d" % pages)
        rc = 2
    if "_" in PDF.name:
        print("ERROR: upload filename must not contain an underscore")
        rc = 2
    if rc:
        return rc

    text = io.open(README, encoding="utf-8").read()
    edits = []
    if ROW_A_NEW not in text:
        edits.append((ROW_A_OLD, ROW_A_NEW))
    if ROW_B_NEW not in text:
        edits.append((ROW_B_OLD, ROW_B_NEW))
    for old, new in edits:
        if text.count(old) != 1:
            print("ERROR: README row not found exactly once: %r" % old[:60])
            rc = 2
            continue
        text = text.replace(old, new, 1)
        print("  README row updated: %s" % new.split("|")[1].strip())
    if rc:
        return rc

    # by-products removal first, THEN the hash listing: listing a file that is about to be deleted
    # would make SHA256SUMS.txt self-inconsistent (this happened on the first run and was fixed).
    stale = []
    for pat in BYPRODUCTS:
        stale += sorted(PKG.glob(pat))
    print("\nbuild by-products: %s" % ([p.name for p in stale] or "none"))

    if not args.apply:
        files = sorted(p for p in PKG.iterdir() if p.is_file() and p != SUMS and p not in stale)
        print("package files that would be listed (%d):" % len(files))
        for p in files:
            print("  %-32s %8d B" % (p.name, p.stat().st_size))
        print("\n(preview; pass --apply to write)")
        return 0

    io.open(README, "w", encoding="utf-8", newline="\n").write(text)
    for p in stale:
        p.unlink()
    files = sorted(p for p in PKG.iterdir() if p.is_file() and p != SUMS)
    lines = ["%s  %s" % (sha256_of(p), p.name) for p in files]
    print("\npackage files listed (%d):" % len(files))
    for p in files:
        print("  %-32s %8d B  %s" % (p.name, p.stat().st_size, sha256_of(p)))
    io.open(SUMS, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("\nwrote README.md and SHA256SUMS.txt (%d entries)" % len(lines))
    return rc


if __name__ == "__main__":
    sys.exit(main())
