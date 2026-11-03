# -*- coding: utf-8 -*-
r"""Verify the A1 framing rewrite: abstract length and coherence, proposition moved once, no duplicated text."""
import io
import os
import re

from pypdf import PdfReader

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
PDF = os.path.join(REPO, "paper_a1", "main.pdf")

t = io.open(MAIN, encoding="utf-8").read()
i, j = t.find(r"\begin{abstract}"), t.find(r"\end{abstract}")
body = t[i + len(r"\begin{abstract}"):j]
plain = re.sub(r"\\[a-zA-Z]+\*?(\{[^{}]*\})?", " ", body)
plain = re.sub(r"\$[^$]*\$", " X ", plain)
words = [w for w in re.split(r"\s+", plain) if re.search(r"[A-Za-z]{2,}", w)]
print(f"  abstract words (approx): {len(words)}")

for label, needle, expect in (
    ("proposition occurrences", r"\textbf{Proposition (non-sufficiency of the gap)", 1),
    ("abstract 'sufficient'", r"not a \emph{sufficient} statistic", 1),
    ("boundary sentence", "quantified boundary", None),
    ("finding (iv)", r"\item[(iv)]", 1),
):
    n = t.count(needle)
    ok = (n == expect) if expect is not None else (n >= 1)
    print(f"  {'OK  ' if ok else 'FAIL'} {label:<26} count={n}")

# the proposition must sit before related_work and after the findings list
p = t.find(r"\textbf{Proposition (non-sufficiency of the gap)")
rw = t.find(r"\input{related_work}")
setup = t.find(r"\section{Setup}")
print(f"  {'OK  ' if p < rw < setup else 'FAIL'} proposition order: {p} < {rw} < {setup}")

pdf = "".join((pg.extract_text() or "") for pg in PdfReader(PDF).pages)
flat = re.sub(r"\s+", " ", pdf)
print("  pages:", len(PdfReader(PDF).pages))
for needle in ("sufficient statistic", "four controlled experiments", "0.36", "0.98"):
    print(f"  {'OK  ' if needle in flat else 'MISS'} pdf: {needle!r}")
