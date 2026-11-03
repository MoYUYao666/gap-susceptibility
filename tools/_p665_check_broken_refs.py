# -*- coding: utf-8 -*-
r"""Check both PDFs for broken references, with a regex that actually matches "??".

The previous attempt used r'\\?\\?' which matches a literal backslash-question-mark, not two
question marks, and reported 35,103 hits in the supplementary - obviously wrong. This uses a
tool that cannot misfire and prints the real counts plus the LaTeX logs.

    python tools/_p665_check_broken_refs.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = REPO / "paper3" / "paper_ieee"

PDFS = [
    ("main.pdf", P / "main.pdf", P / "main.log"),
    ("supplementary.pdf", P / "supplementary" / "supplementary.pdf",
     P / "supplementary" / "supplementary.log"),
    ("cover_letter_prl.pdf", P / "cover_letter_prl.pdf", P / "cover_letter_prl.log"),
    ("title_page_prl.pdf", P / "title_page_prl.pdf", None),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ok = True
    for name, pdf, log in PDFS:
        print("=" * 96)
        print(name)
        print("=" * 96)
        if not pdf.exists():
            print("  MISSING")
            ok = False
            continue
        r = subprocess.run(["pdftotext", "-q", "-layout", str(pdf), "-"], capture_output=True)
        t = r.stdout.decode("utf-8", errors="replace")
        qq = t.count("??")
        print(f"  characters: {len(t):,}   '??' occurrences: {qq}")
        for m in list(re.finditer(re.escape("??"), t))[:6]:
            seg = " ".join(t[max(0, m.start() - 70):m.start() + 40].split())
            print(f"     ...{seg[:120]}...")
        if log and log.exists():
            lt = io.open(log, encoding="utf-8", errors="replace").read()
            undef = re.findall(r"Reference `([^']+)' on page (\d+) undefined", lt)
            cites = re.findall(r"Citation `([^']+)' .* undefined", lt)
            errs = re.findall(r"^! (.*)$", lt, re.M)
            print(f"  LaTeX errors            : {len(errs)}")
            for e in errs[:3]:
                print(f"     ! {e[:110]}")
            print(f"  undefined references    : {len(undef)} {undef[:4]}")
            print(f"  undefined citations     : {len(cites)} {cites[:4]}")
            if qq or errs or undef or cites:
                ok = False
        print()
    print("=" * 96)
    print(f"OVERALL: {'ALL CLEAN' if ok else 'SOMETHING NEEDS ATTENTION'}")
    print("=" * 96)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
