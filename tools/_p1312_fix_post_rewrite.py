# -*- coding: utf-8 -*-
"""Fix the three items from the last audit: dead appendix label, stale README abstract count, ledger abstract count.

    python tools/_p1312_fix_post_rewrite.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
BUILD = os.path.join(REPO, "tools", "_p1236_build_paa_package.py")
LEDGER = os.path.join(REPO, "tools", "_claim_ledger_a1.py")

INTRO_OLD = "and the appendix reports robustness checks."
INTRO_NEW = "and Appendix~\\ref{app:robustness} reports robustness checks."

BUILD_IMPORT_ANCHOR = "REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))"
BUILD_IMPORT_ADD = '''REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys as _sys
_sys.path.insert(0, os.path.join(REPO, "tools"))
from paper_audit.texutil import count_words as _count_words
'''

BUILD_ARG_OLD = "pages(os.path.join(A1, \"cover_letter_paa.pdf\")), 239)"
BUILD_ARG_NEW = ("pages(os.path.join(A1, \"cover_letter_paa.pdf\")), "
                 "_count_words(open(os.path.join(A1, \"main.tex\"), encoding=\"utf-8\").read()"
                 ".split(\"\\\\begin{abstract}\")[1].split(\"\\\\end{abstract}\")[0]))")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    n = t.count(INTRO_OLD)
    print(f"  intro ref: {n}")
    assert n == 1
    t = t.replace(INTRO_OLD, INTRO_NEW, 1)

    b = io.open(BUILD, encoding="utf-8").read()
    if "from paper_audit.texutil import count_words as _count_words" not in b:
        assert b.count(BUILD_IMPORT_ANCHOR) == 1
        b = b.replace(BUILD_IMPORT_ANCHOR, BUILD_IMPORT_ADD, 1)
    n2 = b.count(BUILD_ARG_OLD)
    print(f"  builder abstract arg: {n2}")
    assert n2 == 1
    b = b.replace(BUILD_ARG_OLD, BUILD_ARG_NEW, 1)

    led = io.open(LEDGER, encoding="utf-8").read()
    n3 = led.count('claim("abstract words (audit counter)", 239')
    print(f"  ledger abstract claim: {n3}")
    assert n3 == 1
    led = led.replace('claim("abstract words (audit counter)", 239', 'claim("abstract words (audit counter)", 243', 1)

    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    io.open(BUILD, "w", encoding="utf-8", newline="").write(b)
    io.open(LEDGER, "w", encoding="utf-8", newline="").write(led)
    print("  written main.tex, builder, ledger")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
