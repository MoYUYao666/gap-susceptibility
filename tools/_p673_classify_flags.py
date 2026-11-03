# -*- coding: utf-8 -*-
r"""Classify each flagged phrase in the submitted PDF: manuscript, cover letter, or metadata.

The first pass flagged four phrases. Whether each is a problem depends entirely on which part
of the 33-page merged file it sits in, so this locates every occurrence and prints the
surrounding text. It also establishes what the journal's own top-level record says the title
is, which is what a reader sees first.

    python tools/_p673_classify_flags.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "submitted_flag_classification.json"

FLAGS = ["unique admissible", "sharp phase transition", "Gradient Structure Laws",
         "hw4c24@soton.ac.uk"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not PDF.exists():
        print(f"  not found: {PDF}")
        return 1
    r = subprocess.run(["pdftotext", "-q", "-layout", str(PDF), "-"], capture_output=True)
    full = r.stdout.decode("utf-8", errors="replace")
    pages = full.split("\f")
    print(f"  {len(pages)} pages extracted")
    print()

    # where does the manuscript proper begin and end?
    for marker in ("Abstract", "Index Terms", "I. INTRODUCTION", "REFERENCES",
                   "Data statement", "Cover letter", "Response to Reviewers",
                   "Supplementary", "Authorship"):
        hits = [i + 1 for i, pg in enumerate(pages) if marker.lower() in pg.lower()]
        if hits:
            print(f"  marker {marker!r:<24} on pages {hits[:8]}")
    print()

    for flag in FLAGS:
        print("=" * 100)
        print(f"FLAG: {flag}")
        print("=" * 100)
        for idx, pg in enumerate(pages, 1):
            if flag.lower() in pg.lower():
                for m in re.finditer(re.escape(flag), pg, re.I):
                    seg = " ".join(pg[max(0, m.start() - 260):m.start() + 260].split())
                    print(f"  page {idx}:  ...{seg[:470]}...")
                    print()
        print()

    print("=" * 100)
    print("What the top-level record says (first page, first 700 characters)")
    print("=" * 100)
    print("  " + " ".join(pages[0].split())[:900])
    print()
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            "\n".join(f"page {i+1}" for i in range(len(pages))))
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
