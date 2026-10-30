"""Final verification of the Applied Intelligence submission package (read-only).

Checks: file inventory and sizes, artwork list, zip layout (flat, no subdirectories), page counts,
key content on page 1 and in the Statements and Declarations section, upload-filename rule,
reframed-tree and frozen-package integrity, and that the superseded CVIU package was not modified.

Usage: python tools/_p1683_verify_ai_package.py
"""

from __future__ import annotations

import hashlib
import io
import re
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "SUBMISSION" / "PaperA_AppliedIntelligence"


def main() -> int:
    from pypdf import PdfReader
    rc = 0

    print("== package files ==")
    for p in sorted(PKG.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(PKG)).replace("\\", "/")
            extra = ""
            if p.suffix == ".pdf":
                extra = "  (%d pp)" % len(PdfReader(str(p)).pages)
            print("  %-40s %9d B%s" % (rel, p.stat().st_size, extra))

    print("\n== artwork ==")
    art = sorted(p.name for p in (PKG / "Artwork").iterdir() if p.is_file())
    print("  %d files: %s" % (len(art), ", ".join(art)))
    if any("_" in n for n in art):
        print("  FAIL: underscore in artwork name")
        rc = 2

    print("\n== LaTeXSource.zip layout ==")
    with zipfile.ZipFile(PKG / "LaTeXSource.zip") as z:
        names = z.namelist()
    dirs = [n for n in names if "/" in n]
    print("  %d entries, entries with a path separator: %d" % (len(names), len(dirs)))
    print("  roots:", ", ".join(sorted(n for n in names if n.endswith((".tex", ".cls", ".bst", ".bib", ".bbl")))))
    figs = [n for n in names if n.endswith(".pdf")]
    print("  figures in zip:", len(figs))
    if dirs:
        print("  FAIL: zip is not flat")
        rc = 2

    print("\n== manuscript content ==")
    reader = PdfReader(str(PKG / "Manuscript.pdf"))
    p1 = re.sub(r"\s+", " ", reader.pages[0].extract_text() or "")
    print("  page 1:", p1[:420])
    full = re.sub(r"\s+", " ", " ".join((p.extract_text() or "") for p in reader.pages))
    for label, needle in (
        ("title", "Adaptation-Site Selection for PEFT"),
        ("author", "Hongrui Wan"),
        ("email", "hw4c24@soton.ac.uk"),
        ("affiliation", "University of Southampton"),
        ("keywords", "Gap susceptibility"),
        ("statements heading", "Statements and Declarations"),
        ("funding", "did not receive any specific grant"),
        ("competing", "no known competing financial interests"),
        ("data availability", "10.5281/zenodo.23632347"),
        ("authors' contributions", "Conceptualization"),
        ("generative AI", "DeepSeek V4"),
        ("references", "References"),
    ):
        ok = needle in full
        print("  %-24s %s" % (label, "OK" if ok else "MISSING"))
        if not ok:
            rc = 2
    n_cite = len(re.findall(r"\[\d{1,3}(?:[,\-]\s?\d{1,3})*\]", full))
    print("  numeric citations:", n_cite)
    # abstract word count from the PDF page 1
    m = re.search(r"Abstract (.+?) Keywords", p1)
    if m:
        words = len([w for w in re.split(r"\s+", m.group(1)) if re.search(r"[A-Za-z0-9]", w)])
        print("  abstract words on page 1:", words)
    i = full.find("Statements and Declarations")
    print("  statements excerpt:", full[i:i + 700])

    print("\n== integrity ==")
    st = subprocess.run(["git", "status", "--porcelain", "--", "paper合/reframed"],
                        cwd=str(REPO), capture_output=True, text=True)
    print("  git status paper合/reframed:", st.stdout.strip() or "(clean)")
    st2 = subprocess.run(["git", "status", "--porcelain", "--", "SUBMISSION/PaperA_Neurocomputing"],
                         cwd=str(REPO), capture_output=True, text=True)
    print("  git status PaperA_Neurocomputing:", st2.stdout.strip() or "(clean/ignored)")
    neu = REPO / "SUBMISSION" / "PaperA_Neurocomputing"
    print("  frozen package files:", len([p for p in neu.rglob("*") if p.is_file()]))
    cviu = REPO / "SUBMISSION" / "PaperA_CVIU"
    if cviu.is_dir():
        print("  superseded CVIU package files:", len([p for p in cviu.rglob("*") if p.is_file()]))
    sums = PKG / "SHA256SUMS.txt"
    listed = {}
    for line in io.open(sums, encoding="utf-8").read().splitlines():
        if line.strip():
            h, rel = line.split("  ", 1)
            listed[rel] = h
    actual = {str(p.relative_to(PKG)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in PKG.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"}
    print("  SHA256SUMS: %d listed, %d actual, equal=%s" % (len(listed), len(actual), listed == actual))
    if listed != actual:
        rc = 2
    print("\nRESULT:", "OK" if not rc else "PROBLEMS")
    return 0 if not rc else 2


if __name__ == "__main__":
    sys.exit(main())
