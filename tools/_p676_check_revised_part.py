# -*- coding: utf-8 -*-
r"""Determine whether the REVISED manuscript (pages 21-30 of the merged PDF) is the new build.

The merged submission PDF contains, in order: the journal record page, the cover letter and
declarations, the ORIGINAL manuscript (pages 5-15), the figures, the supplementary and the
LaTeX source listing, then "Revised manuscript (marked up)" from page 21. Editorial Manager
adds the original for comparison, so the original carrying the old title and the old
affiliation is expected and harmless.

What matters is whether the revised part, pages 21 onwards, is the 13 October build. This
compares that region against the file on disk, marker by marker.

    python tools/_p676_check_revised_part.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "revised_part_check.json"


def pages_of(p: Path) -> list[str]:
    r = subprocess.run(["pdftotext", "-q", "-layout", str(p), "-"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace").split("\f")


MARKERS = {
    "new title (unbroken)": "Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry",
    "new title (any wrap)": "Zero-Shot",
    "old title": "Gradient Structure Laws as Predictors of PEFT Design",
    "DOI 23341223": "10.5281/zenodo.23341223",
    "old DOI": "10.5281/zenodo.23341083",
    "6-seed corner 2344": "2344",
    "3-seed corner 3607": "3607",
    "6-seed interior 1477": "1477",
    "3-seed interior 2241": "2241",
    "old affiliation": "School of Electronics and Computer Science",
    "withdrawn: unique admissible": "unique admissible",
    "withdrawn: sharp phase transition": "sharp phase transition",
    "not-a-proxy line": "not a proxy",
    "protocol caveat": "largest caveat",
}


def scan(text: str) -> dict:
    flat = re.sub(r"\s+", "", text)
    return {k: (v.replace(" ", "") in flat) for k, v in MARKERS.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sub_pages = pages_of(SUB)
    new_pages = pages_of(NEW)
    print(f"  submitted merged PDF : {len(sub_pages)} pages")
    print(f"  revision main.pdf    : {len(new_pages)} pages")

    revised = "\n".join(sub_pages[20:])       # from page 21
    original = "\n".join(sub_pages[4:15])     # pages 5-15
    ref = "\n".join(new_pages)

    print()
    print("=" * 104)
    print(f"  {'marker':<36} {'revised part(21+)':>18} {'original(5-15)':>16} {'disk main.pdf':>14}")
    print("=" * 104)
    rs, os_, ds = scan(revised), scan(original), scan(ref)
    for k in MARKERS:
        print(f"  {k:<36} {str(rs[k]):>18} {str(os_[k]):>16} {str(ds[k]):>14}")

    print()
    print("=" * 104)
    print("verdict")
    print("=" * 104)
    checks = {
        "revised part carries the new title": rs["new title (unbroken)"],
        "revised part carries the new DOI": rs["DOI 23341223"],
        "revised part has the 6-seed values": rs["6-seed corner 2344"] and rs["6-seed interior 1477"],
        "revised part has no 3-seed values": not rs["3-seed corner 3607"] and not rs["3-seed interior 2241"],
        "revised part has no old DOI": not rs["old DOI"],
        "revised part has no old affiliation": not rs["old affiliation"],
        "original part is the original (expected)": os_["old title"],
    }
    ok = True
    for k, v in checks.items():
        ok = ok and v
        print(f"  {'OK ' if v else 'BAD'} {k}")
    print()
    print(f"  VERDICT: {'the revised manuscript in the submission is the current build' if ok else 'THE SUBMITTED REVISION IS NOT THE CURRENT BUILD'}")

    # locate 'unique admissible' and 'sharp phase transition' precisely
    print()
    print("=" * 104)
    print("where the two withdrawn phrases still appear, page by page")
    print("=" * 104)
    for phrase in ("unique admissible", "sharp phase transition"):
        for i, pg in enumerate(sub_pages, 1):
            if phrase.lower() in pg.lower():
                part = ("record page" if i == 1 else
                        "cover letter" if i in (2, 3, 4) else
                        "ORIGINAL manuscript (pages 5-15)" if 5 <= i <= 15 else
                        "figures/supplementary/source" if 16 <= i <= 20 else
                        "REVISED manuscript (21+)")
                print(f"  {phrase!r:<26} page {i:>2}  [{part}]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
