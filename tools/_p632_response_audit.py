# -*- coding: utf-8 -*-
r"""Pre-submission audit of the three response boxes.

The operator is about to paste these into Editorial Manager. Editorial Manager's response
box is plain text, so anything that is not plain ASCII/Latin-1 risks being mangled. This
checks encoding, forbidden character classes, placeholders, and structural completeness
against the 33 reviewer comments.

    python tools/_p632_response_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESP = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"
OUT = REPO / "outputs" / "analysis" / "response_audit.json"

CJK = re.compile(r"[\u4e00-\u9fff]")
# characters that usually survive EM, but worth listing if present in volume
SUSPECT = {
    "smart quotes": re.compile(r"[\u2018\u2019\u201c\u201d]"),
    "en/em dash": re.compile(r"[\u2013\u2014]"),
    "non-breaking space": re.compile(r"[\u00a0\u202f]"),
    "ellipsis": re.compile(r"\u2026"),
    "bullet/arrow": re.compile(r"[\u2022\u2192\u21d2\u2713\u2717]"),
    "math symbols": re.compile(r"[\u0393\u2207\u0394\u03c4\u03bb\u03c3\u2264\u2265\u2248\u2212\u00d7]"),
}
PLACEHOLDERS = ["TODO", "TBD", "XXX", "FIXME", "PLACEHOLDER", "to be inserted",
                "[insert", "REPOSITORY DOI", "????", "??", "lorem"]
LATEX = re.compile(r"\\[a-zA-Z]{2,}|\$[^$\n]{1,40}\$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted(RESP.glob("P3_RESPONSE_Reviewer*_plain.txt"))
    print(f"  {len(files)} response boxes found")
    report = {}
    for p in files:
        raw = p.read_bytes()
        try:
            t = raw.decode("utf-8")
            enc = "utf-8"
        except UnicodeDecodeError as e:
            print(f"  {p.name}: NOT UTF-8 ({e})")
            continue
        latin1_ok = True
        try:
            raw.decode("latin-1")
        except Exception:
            latin1_ok = False
        weird = sorted({c for c in t if ord(c) > 126})
        non_latin = sorted({c for c in t if ord(c) > 255})
        print()
        print("=" * 96)
        print(f"{p.name}")
        print("=" * 96)
        print(f"  {len(t):,} characters / {len(t.splitlines())} lines / {len(raw):,} bytes")
        print(f"  pure ASCII            : {all(ord(c) < 128 for c in t)}")
        print(f"  encodable as latin-1  : {latin1_ok}")
        if non_latin:
            print(f"  chars above U+00FF    : {[f'U+{ord(c):04X} {c!r}' for c in non_latin][:10]}")
        if weird:
            print(f"  non-ASCII chars       : {len(weird)} distinct")
            for c in weird[:15]:
                print(f"      U+{ord(c):04X}  {c!r}  {unicodedata.name(c, '?')}")
        print(f"  CJK characters        : {len(CJK.findall(t))}")
        for label, rx in SUSPECT.items():
            n = len(rx.findall(t))
            if n:
                print(f"  {label:<22}: {n}")
        print(f"  LaTeX commands / $..$ : {len(LATEX.findall(t))}")
        hits = [ph for ph in PLACEHOLDERS if ph in t]
        print(f"  placeholder markers   : {hits if hits else 'none'}")
        # structure: does it use the Point N / Response convention?
        pts = re.findall(r"^Point\s+(\d+)", t, re.M)
        resp = len(re.findall(r"^Response:", t, re.M))
        print(f"  'Point N' headings    : {len(pts)}  (numbers {pts[:3]}...{pts[-3:] if pts else ''})")
        print(f"  'Response:' lines     : {resp}")
        print(f"  first 3 lines         :")
        for l in t.splitlines()[:3]:
            print(f"      {l[:100]}")
        print(f"  last 2 lines          :")
        for l in t.splitlines()[-2:]:
            print(f"      {l[:100]}")
        report[p.name] = {"chars": len(t), "lines": len(t.splitlines()),
                          "ascii": all(ord(c) < 128 for c in t),
                          "latin1": latin1_ok, "cjk": len(CJK.findall(t)),
                          "latex": len(LATEX.findall(t)),
                          "placeholders": hits, "points": len(pts), "responses": resp,
                          "non_ascii": [f"U+{ord(c):04X}" for c in weird]}
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print()
        print(f"  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
