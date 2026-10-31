# -*- coding: utf-8 -*-
r"""Rewrite the portal-text extraction to read the typeset PDF, not the LaTeX source.

The first attempt stripped LaTeX macros, which silently deleted \beta, \pm and \% and produced text that was not
paste-ready ("gives =-0.95 0.08"). The compiled manuscript already carries the correct glyphs, so the abstract and the
keyword line are taken from the PDF text layer; highlights come from the plain-text file that was already clean.

    python tools/_p1240_portal_text_pdf.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re

from pypdf import PdfReader

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PA = os.path.join(REPO, "paper合")
OUT = os.path.join(PA, "NC_submission", "PORTAL_TEXT.md")

TITLE = ("Adaptation Site and the Modality Gap: Empirical Regularities and a Gradient-Flow Theory for PEFT of "
         "Contrastive Dual-Encoders")


def clean(s: str) -> str:
    s = s.replace("\u00ad", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    pdf = os.path.join(PA, "main_nc.pdf")
    reader = PdfReader(pdf)
    first = "\n".join((p.extract_text() or "") for p in reader.pages[:3])

    # abstract: from "Abstract" to the keyword line
    m = re.search(r"Abstract\s*(.*?)\s*Keywords", first, re.S | re.I)
    if not m:
        print("  !! abstract/Keyword markers not found on the first pages")
        return 1
    abstract = clean(m.group(1))
    km = re.search(r"Keywords\s*(.*?)(?:\n\s*\n|1\.?\s*Introduction)", first, re.S | re.I)
    keywords = clean(km.group(1)) if km else ""
    keywords = re.sub(r"\s*[·•]\s*", ", ", keywords).strip(" ,")

    hl = io.open(os.path.join(PA, "highlights_nc.txt"), encoding="utf-8").read()
    items = [l.strip("- ").strip() for l in hl.splitlines() if l.strip().startswith("-")]

    print(f"  abstract words: {len(abstract.split())}")
    print(f"  abstract tail: ...{abstract[-160:]}")
    print(f"  keywords: {keywords}")
    print(f"  highlights: {len(items)}, max chars {max(len(x) for x in items)}")

    text = f"""# Neurocomputing portal — plain-text fields (copy-paste)

Extracted from the typeset `paper合/main_nc.pdf` by `tools/_p1240_portal_text_pdf.py`, so the glyphs are the ones the
manuscript renders (no LaTeX-stripping artefacts).

## Title

{TITLE}

## Abstract ({len(abstract.split())} words)

{abstract}

## Keywords

{keywords}

## Highlights ({len(items)} items, max {max(len(x) for x in items)} chars)

{chr(10).join("- " + x for x in items)}
"""
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(text)
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
