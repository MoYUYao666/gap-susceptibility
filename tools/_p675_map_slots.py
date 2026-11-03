# -*- coding: utf-8 -*-
r"""Find which Editorial Manager slot each part of the merged PDF came from.

Submitted PDFs carry an EM annotation naming the source: a line like
"Click here to access/download;Manuscript;manuscript.pdf". Those annotations are the
authoritative statement of what was attached where, so this reads them and maps them to the
pages that follow.

    python tools/_p675_map_slots.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "submitted_slot_map.json"


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

    print("=" * 100)
    print("EM annotations: which file was attached under which slot")
    print("=" * 100)
    ann = re.compile(r"Click\s*here\s*to\s*access/download\s*;?\s*([^;\n]*)\s*;?\s*([^\n]*)",
                     re.I)
    found = []
    for i, pg in enumerate(pages, 1):
        for m in ann.finditer(pg):
            slot, fname = m.group(1).strip(), m.group(2).strip()
            print(f"  page {i:>2}:  slot={slot!r}  file={fname!r}")
            found.append((i, slot, fname))
        for m in re.finditer(r"Click\s*here\s*to\s*view\s*linked\s*References", pg, re.I):
            print(f"  page {i:>2}:  (linked references marker)")
    if not found:
        print("  no annotation matched; printing every line containing 'Click here'")
        for i, pg in enumerate(pages, 1):
            for line in pg.splitlines():
                if "click here" in line.lower():
                    print(f"  page {i}: {line.strip()[:150]}")

    print()
    print("=" * 100)
    print("page-by-page content map")
    print("=" * 100)
    NEW = "Zero-ShotCross-ArchitectureRankAllocationfromGradientGeometry"
    OLD = "GradientStructureLawsasPredictors"
    for i, pg in enumerate(pages, 1):
        flat = re.sub(r"\s+", "", pg)
        tags = []
        if NEW in flat:
            tags.append("NEW-TITLE")
        if OLD in flat:
            tags.append("OLD-TITLE")
        if "2344" in flat:
            tags.append("6-seed-values")
        if "3607" in flat:
            tags.append("3-seed-values")
        if "SchoolofElectronicsandComputerScience" in flat:
            tags.append("OLD-AFFILIATION")
        if "Abstract—" in pg or "Abstract -" in pg:
            tags.append("HAS-ABSTRACT")
        if "Data statement" in pg:
            tags.append("DATA-STATEMENT")
        if "Response" in pg and "Reviewer" in pg:
            tags.append("RESPONSE")
        if "Highlights" in pg:
            tags.append("HIGHLIGHTS")
        if "Authorship" in pg or "declaration" in pg.lower():
            tags.append("DECLARATION")
        head = " ".join(pg.split())[:70]
        print(f"  {i:>2}  {','.join(tags) if tags else '-':<62} | {head}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
