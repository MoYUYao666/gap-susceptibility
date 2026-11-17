#!/usr/bin/env python3
"""Pattern Recognition Letters submission gate for Paper B v2."""

from __future__ import annotations

import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "paper_b_v2/manuscript/prl/main_prl.pdf"
SRC = ROOT / "paper_b_v2/manuscript/prl_src"
PKG = ROOT / "SUBMISSION/PaperBv2_PRL_2026-11-15"
REPORT = ROOT / "paper_b_v2/results/gate_report_prl.json"
fails, notes = [], []


def require(cond, msg):
    if not cond:
        fails.append(msg)


def pdf_pages(path: Path) -> int:
    out = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout
    return int(re.search(r"Pages:\s+(\d+)", out).group(1))


def pdf_text(path: Path) -> str:
    return subprocess.run(["pdftotext", str(path), "-"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


require(PDF.exists(), "PRL PDF missing")
if PDF.exists():
    pages = pdf_pages(PDF)
    notes.append(f"PRL PDF pages: {pages}")
    require(pages <= 7, f"PRL page limit exceeded: {pages}")
    text = pdf_text(PDF)
    refs = len(re.findall(r"^\[\d+\]", text, re.M))
    notes.append(f"rendered references: {refs}")
    require(refs >= 20, f"references <20: {refs}")
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}",
                         (ROOT / "paper_b_v2/manuscript/prl/main_prl.tex").read_text(encoding="utf-8"), re.S).group(1)
    abstract = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", " ", abstract)
    abstract = re.sub(r"[\\{}%]", " ", abstract)
    words = len(abstract.split())
    notes.append(f"abstract words: {words}")
    require(words <= 250, f"abstract >250: {words}")
    fonts = subprocess.run(["pdffonts", str(PDF)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace").stdout
    require("Type 3" not in fonts, "Type 3 font present")
    require("no" in fonts.lower() or "yes" in fonts.lower(), "font embedding unreadable")

require((SRC / "main.tex").exists(), "PRL source main.tex missing")
require((SRC / "references.bib").exists(), "PRL source references missing")
require((SRC / "figures").exists(), "PRL source figures missing")

required = ["Manuscript.pdf", "Supplementary.pdf", "TitlePage.pdf", "CoverLetter.pdf", "Declarations.pdf", "Declarations.docx",
            "Highlights.pdf", "Highlights.docx", "GraphicalAbstract.pdf", "AuthorshipConfirmation.pdf", "AuthorContributions.pdf",
            "LaTeXSource.zip", "README.md", "SHA256SUMS.txt"]
for f in required:
    require((PKG / f).exists(), f"package missing {f}")
if (PKG / "Manuscript.pdf").exists():
    pkg_pages = pdf_pages(PKG / "Manuscript.pdf")
    notes.append(f"package manuscript pages: {pkg_pages}")
    require(pkg_pages == pages, f"package page mismatch: {pkg_pages} vs {pages}")

# Official Pattern Recognition Letters authorship form
form = PKG / "AuthorshipConfirmation.pdf"
if form.exists():
    form_text = subprocess.run(["pdftotext", "-layout", str(form), "-"], capture_output=True, text=True,
                                encoding="utf-8", errors="replace").stdout
    require("Pattern Recognition Letters" in form_text, "authorship form is not the PRL official form")
    require("Authorship Confirmation" in form_text, "authorship form title missing")
    require("November 17, 2026" in form_text, "authorship form date is stale")
    notes.append("official PRL authorship form: present")
if (PKG / "CoverLetter.pdf").exists():
    cl_pages = pdf_pages(PKG / "CoverLetter.pdf")
    notes.append(f"CoverLetter.pdf pages: {cl_pages}")
    require(cl_pages >= 2, "CoverLetter.pdf should include the official authorship form")

if (PKG / "LaTeXSource.zip").exists():
    names = zipfile.ZipFile(PKG / "LaTeXSource.zip").namelist()
    require(any(n == "main.tex" for n in names), "source zip missing main.tex")
    require(any(n == "references.bib" for n in names), "source zip missing references.bib")
    require(any(n.startswith("figures/") for n in names), "source zip missing figures")
    require(not any("paper3" in n.lower() or "wan2026" in n.lower() for n in names), "old trace in source zip")
    notes.append(f"source zip entries: {len(names)}")

out = {"status": "PASS" if not fails else "FAIL", "fails": fails, "notes": notes}
REPORT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, indent=2))
raise SystemExit(0 if not fails else 1)
