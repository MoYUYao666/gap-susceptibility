# -*- coding: utf-8 -*-
r"""Sync the Paper A cover letters and the final-verification page expectation to the current build.

Paper A's Neurocomputing build is now 75 pages (Section H on the decoder confound added one page) and
the Springer variant 54.  The cover letters still claim 74, and `tools/_p1454_final_verify.py` still
expects (74,)/(53,).  The consistency gate checks the cover-letter claim against the PDF page count.

    python tools/_p1590_sync_paperA_pagecounts.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

LETTERS = ["paper合/cover_letter_nc.tex", "paper合/cover_letter.tex", "paper合/cover_letter_nc_revision.tex"]
FV = "tools/_p1454_final_verify.py"

# Stale wording in the A23 hand-off records (the negative control IS in the main text).
HANDOFF_OLD = "margin 证书在通用 CLIP 上**饱和失效**"
OBJ_OLD = 'stale: "Recorded as a negative control; OceanCLIP weights are not present locally'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    for path in LETTERS:
        t = io.open(path, encoding="utf-8").read()
        n = len(re.findall(r"\b74 pages\b", t))
        print("%-34s '74 pages' occurrences: %d" % (os.path.basename(path), n))
        if a.apply and n:
            io.open(path, "w", encoding="utf-8", newline="").write(t.replace("74 pages", "75 pages"))

    t = io.open(FV, encoding="utf-8").read()
    old = ('PAGES = {"paper_a1/main.pdf": (64,), "paper合/main_nc.pdf": (74,), "paper合/main_springer.pdf": (53,),')
    new = ('PAGES = {"paper_a1/main.pdf": (64,), "paper合/main_nc.pdf": (75,), "paper合/main_springer.pdf": (54,),')
    assert old in t, "PAGES line not found"
    print("final_verify PAGES line found")
    if a.apply:
        io.open(FV, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())