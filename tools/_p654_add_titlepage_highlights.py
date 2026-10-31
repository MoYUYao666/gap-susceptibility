# -*- coding: utf-8 -*-
r"""Add the title page and highlights to the staging folder, and record the retitle.

The title page legitimately carries the author's name, affiliation, e-mail and ORCID (that is
what a title page is for, and the journal requires the corresponding author's address there).
The highlights deliberately do not, which is why the two are handled differently.

    python tools/_p654_add_titlepage_highlights.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAPER = REPO / "paper3" / "paper_ieee"
SUB = PAPER / "PRL_submission"
STAGE = REPO / "SUBMISSION" / "P3_PRL_revision" / "UPLOAD"
MS = "P3_PRLETTERS-D-26-02378"

ADDS = [
    (PAPER / "title_page_prl.pdf", f"{MS}_Title_Page.pdf"),
    (SUB / "highlights.pdf", f"{MS}_Highlights.pdf"),
    (SUB / "highlights.txt", f"{MS}_Highlights.txt"),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for src, name in ADDS:
        ok = src.exists()
        print(f"  {'OK ' if ok else 'MISSING'} {name:<52} <- {src.relative_to(REPO)}"
              f"  ({src.stat().st_size if ok else 0:,} bytes)")
        if ok and a.apply:
            shutil.copy2(src, STAGE / name)
    if not a.apply:
        print("  (dry run)")
        return 0
    print()
    print("  staged folder now:")
    for p in sorted(STAGE.iterdir()):
        if p.is_file():
            print(f"    {p.stat().st_size:>10,}  {p.name}  sha {sha(p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
