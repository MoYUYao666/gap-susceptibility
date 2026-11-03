# -*- coding: utf-8 -*-
r"""Repair the supplement's hand-written pointers to the main text's numbered objects.

The supplement is compiled on its own, so it cannot \ref into the main text; its pointers are plain text
and have to be kept in step by hand. Two things went wrong:

* a replacement run twice left "Corollary~5 of the main text of the main text of the main text of ...";
* with the lemma now numbered by section, the lemma is III.1, so "Lemma~2" was wrong.

Final state, matching what the main text prints (verified by tools/_p910_p3_numbering_check.py):
`Lemma~III.1 of the main text`, `Corollary~5 of the main text`, `Theorem~1`.

    python tools/_p911_fix_supp_pointers.py [--apply]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"

# applied in order; the final one collapses any number of repeated tails to one
FIXES = [
    (r"Corollary~5 of the main text(?: of the main text)+", "Corollary~5 of the main text"),
    (r"Lemma~2 of the main text", "Lemma~III.1 of the main text"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SUPP.read_text(encoding="utf-8")
    out = t
    for pattern, repl in FIXES:
        hits = re.findall(pattern, out)
        if not hits:
            print(f"  nothing to do for {pattern[:40]!r}")
            continue
        out = re.sub(pattern, repl, out)
        print(f"  {len(hits)} occurrence(s) of {pattern[:40]!r} -> {repl!r}")

    if out == t:
        print("  file unchanged")
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0
    SUPP.write_text(out, encoding="utf-8", newline="")

    check = SUPP.read_text(encoding="utf-8")
    assert not re.search(r"of the main text(?: of the main text)+", check), "repetition remains"
    assert "Lemma~III.1 of the main text" in check
    assert "Corollary~5 of the main text" in check
    print("  written and verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
