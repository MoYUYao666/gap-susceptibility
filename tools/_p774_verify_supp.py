# -*- coding: utf-8 -*-
r"""Verify the duplicate headings are gone from the compiled supplementary, and check the submitted copy.

The source fix is in paper3/paper_ieee/supplementary/supplementary.tex. Two things need checking:

  1. the freshly compiled PDF shows each heading once
  2. whether the supplementary that was already submitted with the PRLetters revision carries the
     duplicates, which would be worth knowing even though that file cannot be changed now

    python tools/_p774_verify_supp.py --apply
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
OUT = REPO / "outputs" / "analysis" / "supp_duplicate_check.json"

HEADINGS = [
    "Comparison with Prior Work",
    "Rank Scaling and",
    "Second-Dataset Validation",
    "Sample Size Robustness",
    "Downstream check",
    "Decoder VLM",
]


def pdftext(p: Path):
    r = subprocess.run(["pdftotext", "-q", "-layout", str(p), "-"], capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {}

    targets = []
    fresh = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.pdf"
    if fresh.exists():
        targets.append(("rebuilt from the fixed source", fresh))
    sub = REPO / "SUBMISSION" / "P3_PRL_revision" / "UPLOAD"
    if sub.exists():
        for p in sorted(sub.glob("*Supplementary*.pdf")):
            targets.append(("submitted revision package", p))
    old = REPO / "SUBMISSION" / "_superseded_P3_PRL_submitted_2026-09-26"
    if old.exists():
        for p in sorted(old.rglob("*upplement*.pdf")):
            targets.append(("superseded first submission", p))

    if not targets:
        print("  no supplementary PDFs found")

    for label, p in targets:
        t = pdftext(p)
        flat = re.sub(r"\s+", " ", t)
        print("=" * 100)
        print(f"{label}")
        print(f"  {p.relative_to(REPO)}   ({p.stat().st_size:,} bytes, {t.count(chr(12)) + 1} pages)")
        print("=" * 100)
        row = {}
        for h in HEADINGS:
            n = flat.count(h)
            row[h] = n
            flag = "DUPLICATE" if n > 1 else ("ok" if n == 1 else "absent")
            print(f"  [{flag:>9}] {h:<28} occurrences in the PDF text: {n}")
        report[str(p.relative_to(REPO))] = row
        print()

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
