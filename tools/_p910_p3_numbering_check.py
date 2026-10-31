# -*- coding: utf-8 -*-
r"""Verify P3's numbering after the corollary/lemma restructuring, across both documents.

Checks, on the compiled PDFs rather than the sources:

* the numbers the main text prints for its theorem-like objects;
* that no reference in the main text is unresolved;
* that the two numbers the supplement writes by hand ("Lemma 2 of the main text",
  "Corollary 5 of the main text") match what the main text now prints;
* that the old awkward forms are gone ("Lemma III.1.1", subsection "D. Corollary 1: ...").

    python tools/_p910_p3_numbering_check.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pypdf

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper3" / "paper_ieee" / "main.pdf"
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.pdf"


def text(p: Path) -> str:
    return "\n".join((pg.extract_text() or "") for pg in pypdf.PdfReader(str(p)).pages)


def main() -> int:
    m, s = text(MAIN), text(SUPP)
    ok = True

    cor = sorted(set(re.findall(r"Corollary\s+(\d+)", m)), key=int)
    lem = sorted(set(re.findall(r"Lemma\s+(III\.\d+(?:\.\d+)?)", m)))
    thm = sorted(set(re.findall(r"Theorem\s+(III\.\d+)", m)))
    print(f"  main text prints: corollaries {cor}, lemma {lem}, theorems {thm}")
    checks = [
        (cor == [str(i) for i in range(1, 6)], f"corollaries should be 1..5, are {cor}"),
        (lem == ["III.1"], f"lemma should be III.1, is {lem}"),
        (thm == ["III.1", "III.2"], f"theorems should be III.1/III.2, are {thm}"),
    ]
    for good, why in checks:
        if not good:
            print(f"  BAD  {why}")
        ok &= good

    for bad in ("Lemma III.1.1", "Corollary 1: First-Order", "Corollary 5: Paper"):
        hit = bad in m
        ok &= not hit
        print(f"  {'OK ' if not hit else 'BAD'} old form absent: {bad!r}")

    sub = re.findall(r"[A-H]\.\s+([A-Z][A-Za-z-]+)", m)
    print(f"  subsection titles (first words): {sub[:10]}")

    print(f"  unresolved marks in main: {m.count('??')} | supplement: {s.count('??')}")
    ok &= m.count("??") == 0 and s.count("??") == 0

    # the numbers the supplement writes by hand must match what the main text prints
    for probe in ("Lemma~III.1 of the main text", "Corollary~5 of the main text"):
        printed = probe.replace("~", " ")
        present = printed in s
        print(f"  supplement says {printed!r}: {present}")
        ok &= present
    broken = re.search(r"of the main text(?: of the main text)+", s)
    print(f"  repeated pointer tails in supplement: {'YES' if broken else 'none'}")
    ok &= broken is None
    print()
    print("  " + ("NUMBERING CONSISTENT" if ok else "NUMBERING STILL INCONSISTENT"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
