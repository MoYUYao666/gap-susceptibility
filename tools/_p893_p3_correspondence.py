# -*- coding: utf-8 -*-
r"""Verify that every supplement pointer in P3's main text lands on the right content.

The audit (`tools/_p880`) found six mismatches; after the restructure this re-checks each pointer
against the supplement's actual sections, from the two compiled PDFs, so the check is on what a reader
sees rather than on the sources.

    python tools/_p893_p3_correspondence.py
"""
from __future__ import annotations

import re
from pathlib import Path

import pypdf

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper3" / "paper_ieee" / "main.pdf"
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.pdf"

# (pointer as printed in the main text, what the main text says it holds, a marker that must appear in
#  that supplement section)
EXPECT = [
    ("S9", "sample-size robustness: crossing stable over sizes 16..256", "0.0078"),
    ("S9", "second dataset (ShareGPT): same bracketing", "ShareGPT"),
    ("S5", "rank scaling: Delta E monotone, collapses at r >= 24", "2860"),
    ("S9", "comparison with prior rank-allocation and PEFT-selection methods", "GFAP"),
    ("S7", "downstream check on real Flickr30k pairs", "0.7241"),
]


def sections(text: str) -> dict[str, str]:
    """Split the supplement PDF text on its numbered section headings.

    IEEEtran prints them in caps with no space after the number ("S1. FULLAXIOMDERIVATION OF"),
    while subsections come out mixed case ("A. Step-by-step proof"), so requiring the following text to
    start upper-case keeps subsection letters out of the split.
    """
    t = text.replace("\n", " ")
    marks = [(m.start(), m.group(1), m.group(0).strip()) for m in
             re.finditer(r"\bS(\d)\.\s+[A-Z]", t)]
    out: dict[str, str] = {}
    for i, (pos, num, heading) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(t)
        if num not in out:
            out[num] = t[pos:end]
            out["_head_" + num] = heading
    return out


def main() -> int:
    main_t = "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(MAIN).pages)
    supp_t = "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(SUPP).pages)
    secs = sections(supp_t)

    print("  supplement sections parsed from the PDF:")
    for n in sorted(k for k in secs if not k.startswith("_")):
        print(f"    S{n}: {secs['_head_' + n][:60]}  ({len(secs[n])} chars)")
    print()
    ok = True
    for ptr, claim, marker in EXPECT:
        num = ptr.lstrip("S")
        body = secs.get(num, "")
        hit = marker in body
        ok &= hit
        print(f"  {'OK ' if hit else 'MISS'} S{num}: {claim}")
        print(f"        marker {marker!r} {'found' if hit else 'NOT found'} in S{num} "
              f"({len(body)} chars)")
    print()
    # the main text must not quote any supplement number that does not exist
    quoted = sorted(set(re.findall(r"Supplementary Section[s]?[~ ]S?(\d)", main_t)))
    range_hit = re.findall(r"S1--S9|S1\u2013S9", main_t)
    print(f"  supplement numbers quoted by the main text: {quoted}")
    print(f"  range sentence present: {bool(range_hit)}")
    exists = all(q in secs for q in quoted)
    print(f"  every quoted number exists in the supplement: {exists}")
    missing = [q for q in quoted if q not in secs]
    if missing:
        print(f"    missing: {missing}")
    print()
    print("  " + ("CORRESPONDENCE VERIFIED" if ok and exists else "CORRESPONDENCE STILL BROKEN"))
    return 0 if ok and exists else 1


if __name__ == "__main__":
    raise SystemExit(main())
