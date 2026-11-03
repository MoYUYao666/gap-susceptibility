# -*- coding: utf-8 -*-
"""Verify the MANUAL items that can be checked mechanically, for the A1 fix evidence file."""
import io
import os
import re

from pypdf import PdfReader

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BBL = os.path.join(REPO, "paper_a1", "main.bbl")
PDF = os.path.join(REPO, "paper_a1", "main.pdf")

# E-09/E-10: reference list structure
bbl = io.open(BBL, encoding="utf-8", errors="ignore").read() if os.path.exists(BBL) else ""
items = re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", bbl)
print(f"  E-10 bibitems: {len(items)}")
missing = []
for m in re.finditer(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}(.*?)(?=\\bibitem|\\end\{thebibliography\})", bbl, re.S):
    key, body = m.group(1), re.sub(r"\s+", " ", m.group(2))
    has_year = bool(re.search(r"\b(19|20)\d{2}\b", body))
    has_title = body.count(".") >= 1
    if not (has_year and has_title):
        missing.append(key)
print(f"  E-10 items lacking a year/title-like body: {missing if missing else 'none'}")

# E-06: code/data citations with URL or DOI
with_url = len(re.findall(r"\\url\{|doi|DOI|zenodo|github", bbl, re.I))
print(f"  E-06 url/doi tokens in the reference list: {with_url}")

# E-04 / G-08: PDF page numbers and reference list numbering
reader = PdfReader(PDF)
tail = "".join((p.extract_text() or "") for p in reader.pages[-4:])
nums = re.findall(r"(?m)^\s*(\d{1,3})\.\s", tail)
print(f"  E-04 candidate reference indices found on last pages: {len(nums)}")
first = (reader.pages[0].extract_text() or "")
print(f"  G-08 page number on page 1: {bool(re.search(r'(?m)^\\s*1\\s*$', first))} | total pages {len(reader.pages)}")

# G-07: contribution list (i)-(iv)
tex = io.open(os.path.join(REPO, "paper_a1", "main.tex"), encoding="utf-8").read()
labels = re.findall(r"\\item\[\((i{1,3}|iv|v)\)\]", tex)
print(f"  G-07 list labels: {labels}")
