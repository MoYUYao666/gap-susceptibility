# -*- coding: utf-8 -*-
r"""Audit the PDF the operator submitted, to confirm what actually went in.

Path: C:\Users\hongr\Desktop\PRLETTERS-D-26-02378_R1.pdf

Checks the properties that matter for the record: page count, title, DOI, presence of the
superseded numbers, abstract and keyword wording, and that no internal document paths,
placeholders or author contact details leaked into the submitted file.

    python tools/_p672_audit_submitted_pdf.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "submitted_pdf_audit.json"
CANDIDATES = [
    Path(r"C:\Users\hongr\Desktop\PRLETTERS-D-26-02378_R1.pdf"),
]

NEW_TITLE = "Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry"
OLD_TITLE = "Gradient Structure Laws as Predictors of PEFT Design"
DOI = "10.5281/zenodo.23341223"
OLD_DOI = "10.5281/zenodo.23341083"

MUST_BE_ABSENT = [
    "Gradient Structure Laws as Predictors",
    OLD_DOI,
    "3607", "2241",                      # superseded 3-seed values
    "unique admissible",                 # withdrawn uniqueness claim
    "sharp phase transition",            # withdrawn
    "reduces uncertainty by",            # withdrawn 30x claim
    "docs/P3_",                          # internal document paths
    "to be inserted", "REPOSITORY DOI",
    "hw4c24@soton.ac.uk",                # contact detail (title page keeps it; main text should not)
    "TODO", "TBD", "PLACEHOLDER",
    "??",
]

MUST_BE_PRESENT = [
    NEW_TITLE,
    DOI,
    "2344", "1477",                      # current 6-seed values
    "did not receive any specific grant",  # the journal's required funding sentence
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    pdf = next((p for p in CANDIDATES if p.exists()), None)
    if pdf is None:
        print("  submitted PDF not found:")
        for p in CANDIDATES:
            print(f"    {p}")
        return 1
    print(f"  file: {pdf}")
    print(f"  size: {pdf.stat().st_size:,} bytes")
    r = subprocess.run(["pdftotext", "-q", "-layout", str(pdf), "-"], capture_output=True)
    t = r.stdout.decode("utf-8", errors="replace")
    flat = re.sub(r"[\s\u00ad]+", "", t)
    pages = t.count("\f") + 1
    print(f"  text: {len(t):,} characters, about {pages} page breaks")
    print()

    print("=" * 100)
    print("MUST BE PRESENT")
    print("=" * 100)
    ok = True
    for s in MUST_BE_PRESENT:
        hit = s.replace(" ", "") in flat
        ok = ok and hit
        print(f"  {'OK ' if hit else 'MISSING'} {s[:70]}")

    print()
    print("=" * 100)
    print("MUST BE ABSENT")
    print("=" * 100)
    for s in MUST_BE_ABSENT:
        n = flat.count(s.replace(" ", ""))
        good = n == 0
        ok = ok and good
        print(f"  {'OK ' if good else f'FOUND x{n}'} {s[:70]}")
        if n:
            i = flat.find(s.replace(" ", ""))
            print(f"        context: ...{flat[max(0, i - 80):i + 80]}...")

    print()
    print("=" * 100)
    print("Key numbers, as they appear in the submitted text")
    print("=" * 100)
    for num, label in (("2344", "corner 6-seed"), ("1477", "interior 6-seed"),
                       ("5048", "uniform 6-seed"), ("0.0055", "p at 5e-5"),
                       ("5968", "reversal experimental"), ("2842", "reversal uniform"),
                       ("0.21", "inverse vs uniform p"), ("98.9", "between-rank share"),
                       ("1468", "AdaLoRA margin"), ("0.100", "permutation p")):
        print(f"  {'OK ' if num in flat else 'ABSENT'} {num:<8} {label}")

    print()
    print("=" * 100)
    print("Abstract in the submitted PDF (first 400 characters)")
    print("=" * 100)
    m = re.search(r"(We allocate PEFT rank.*?)(?:Index Terms|Keywords|I\.\s*INTRODUCTION)", t, re.S)
    if m:
        print("  " + " ".join(m.group(1).split())[:600])
    else:
        print("  abstract start not located by pattern")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"file": str(pdf), "bytes": pdf.stat().st_size, "characters": len(t),
             "present": {s: (s.replace(" ", "") in flat) for s in MUST_BE_PRESENT},
             "absent": {s: flat.count(s.replace(" ", "")) for s in MUST_BE_ABSENT}},
            ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    print()
    print(f"  OVERALL: {'ALL CHECKS PASSED' if ok else 'SOMETHING NEEDS ATTENTION'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
