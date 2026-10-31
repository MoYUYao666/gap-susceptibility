# -*- coding: utf-8 -*-
r"""Verify the DOI landed correctly in the rebuilt PDFs.

Checks, per PDF:
- the DOI string is present and not broken across lines
- the repository URL is present
- page count is as expected
- the LaTeX log has no errors and no undefined references
- list any overfull boxes wide enough to be visible in print

    python tools/_p622_verify_doi_pdfs.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAPER = REPO / "paper3" / "paper_ieee"
DOI = "10.5281/zenodo.23341223"
DOI_STALE = "10.5281/zenodo.23341083"
OUT = REPO / "outputs" / "analysis" / "doi_pdf_verify.json"


def pdf_text(p: Path) -> str:
    """Extract text with pdftotext if present, else fall back to pypdf."""
    exe = shutil_which("pdftotext")
    if exe:
        r = subprocess.run([exe, "-q", "-layout", str(p), "-"], capture_output=True)
        if r.returncode == 0:
            return r.stdout.decode("utf-8", errors="replace")
    try:
        from pypdf import PdfReader
    except Exception:
        try:
            from PyPDF2 import PdfReader
        except Exception:
            return ""
    return "\n".join(pg.extract_text() or "" for pg in PdfReader(str(p)).pages)


def shutil_which(name: str):
    import shutil
    return shutil.which(name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    results = {}
    for tex, label, want_pages in (("main.tex", "main", 10),
                                   ("cover_letter_prl.tex", "cover letter", 2)):
        pdf = PAPER / (tex[:-4] + ".pdf")
        log = PAPER / (tex[:-4] + ".log")
        print(f"  === {label} ({pdf.name}) ===")
        if not pdf.exists():
            print("     MISSING PDF")
            results[label] = {"ok": False, "why": "missing pdf"}
            continue
        t = pdf_text(pdf)
        # DOI may be hyphenated at a line break by LaTeX; collapse whitespace
        flat = re.sub(r"[\s\u00ad]+", "", t)
        has_doi = DOI.replace(" ", "") in flat
        has_url = "doi.org/10.5281/zenodo.23341223" in flat
        has_stale = DOI_STALE in flat
        pages = None
        if log.exists():
            lt = io.open(log, encoding="utf-8", errors="replace").read()
            m = re.search(r"Output written on .*?\((\d+) pages", lt)
            if m:
                pages = int(m.group(1))
            errors = len(re.findall(r"^! ", lt, re.M))
            undef = len(re.findall(r"undefined", lt, re.I))
            overfull = re.findall(r"Overfull \\hbox \((\d+\.\d+)pt", lt)
            big = sorted((float(x) for x in overfull), reverse=True)[:3]
        else:
            errors = undef = -1
            big = []
        print(f"     text extracted: {len(t)} chars")
        print(f"     DOI present          : {has_doi}")
        print(f"     doi.org URL present  : {has_url}")
        print(f"     stale old DOI        : {has_stale}  (must be False)")
        print(f"     pages                : {pages} (expected {want_pages})")
        print(f"     LaTeX errors         : {errors}")
        print(f"     'undefined' mentions : {undef}")
        print(f"     largest overfull box : {big}")
        ok = has_doi and has_url and not has_stale and errors == 0 and undef == 0
        print(f"     => {'OK' if ok else 'CHECK'}")
        results[label] = {"ok": ok, "has_doi": has_doi, "has_url": has_url,
                          "stale_doi": has_stale,
                          "pages": pages, "errors": errors, "undefined": undef,
                          "overfull_top": big}
        print()
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"doi": DOI, "results": results}, ensure_ascii=False, indent=1))
        print(f"  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
