# -*- coding: utf-8 -*-
r"""Two loose ends from the submission audit.

1. Page 21 of the submitted file contains "unique admissible". That phrase was withdrawn only
   in its unqualified form; the revision keeps it where the theorem holds *given R3'*. This
   prints the sentence so the distinction can be judged rather than assumed.

2. The disk file reports 11 pages while the submission record says 10. If the extra page is a
   blank one produced by pdftotext's trailing form feed, nothing is wrong; if it holds content,
   the manuscript grew past the intended length.

    python tools/_p677_loose_ends.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUB = Path(r"C:\Users\hongr\Desktop\PRLETTERS-D-26-02378_R1.pdf")
NEW = REPO / "SUBMISSION" / "P3_PRL_revision" / "manuscript" / "main.pdf"


def pages_of(p: Path) -> list[str]:
    r = subprocess.run(["pdftotext", "-q", "-layout", str(p), "-"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace").split("\f")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sp = pages_of(SUB)
    np_ = pages_of(NEW)

    print("=" * 104)
    print("1. 'unique admissible' in the revised part: qualified or not?")
    print("=" * 104)
    for i, pg in enumerate(sp, 1):
        if i < 21 or "unique admissible" not in pg.lower():
            continue
        for m in re.finditer(r"unique admissible", pg, re.I):
            seg = " ".join(pg[max(0, m.start() - 420):m.start() + 220].split())
            print(f"  page {i}:")
            print(f"    ...{seg}...")
            print()

    print("=" * 104)
    print("2. page counts")
    print("=" * 104)
    for label, pages in (("submitted merged PDF", sp), ("disk main.pdf", np_)):
        nonblank = [i for i, p in enumerate(pages, 1) if len(p.strip()) > 20]
        print(f"  {label:<24} pages={len(pages)}  pages with >20 chars={len(nonblank)}  "
              f"({nonblank[0]}-{nonblank[-1]})")
        for i, p in enumerate(pages, 1):
            if len(p.strip()) <= 20:
                print(f"      page {i}: effectively blank ({len(p.strip())} chars)")

    print()
    print("=" * 104)
    print("3. the submitted revision's own first page (title line)")
    print("=" * 104)
    if len(sp) >= 21:
        head = " ".join(sp[20].split())
        print("  " + head[:300])

    print()
    print("=" * 104)
    print("4. does the submitted revision match the file on disk, marker by marker?")
    print("=" * 104)
    marks = ["Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry",
             "10.5281/zenodo.23341223", "2344", "1477", "5048", "0.0055",
             "adjacent to it", "R3", "additivity", "largest caveat"]
    for m in marks:
        flat_sub = re.sub(r"\s+", "", "\n".join(sp[20:]))
        flat_new = re.sub(r"\s+", "", "\n".join(np_))
        print(f"  {m[:56]:<58} submitted={m.replace(' ','') in flat_sub!s:<5} "
              f"disk={m.replace(' ','') in flat_new!s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
