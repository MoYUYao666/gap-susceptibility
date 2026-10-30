# -*- coding: utf-8 -*-
r"""Commentary upgrade: turn the checklist into acceptance tests and keep the 7-page limit.

    python tools/_p1482_commentary_acceptance.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(REPO, "paper_review_prl", "MANUSCRIPT.md")

NEW_PARA = ("\n**From aspiration to acceptance test.** Each item can be checked by a reader in a minute: item 1 requires "
            "the exact checkpoint (not just the model family); item 4 an absolute parameter count as well as a fraction; "
            "item 5 the rank array or the word ``uniform''; item 9 the number of runs and the dispersion convention. A "
            "paper that passes these tests enters a comparison table without correspondence with its authors, which is "
            "the operational meaning of the reporting standard.\n")

OLD_OBJECTION_START = "One objection is worth answering."
NEW_OBJECTION = ("One objection is worth answering: the items cost space. But the space saved by omitting them is "
                 "illusory, since a result whose protocol is unstated cannot enter a comparison table at all, and a "
                 "checklist alone changes little---journals and reviewers enforce it, and stating it here makes the "
                 "requirement citable.")

OLD_LIST_START = "The list cannot be shortened much further."
NEW_LIST = ("The list cannot be shortened much further: items 5 and 6 look like one until one notices that a paper can "
            "state its rank while leaving the division unstated, and items 9 and 10 separate a design fact from a "
            "reporting convention.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MD, encoding="utf-8").read()
    changed = False
    if "From aspiration to acceptance test" not in t:
        # insert before the horizontal rule that closes section 4
        i = t.index(OLD_OBJECTION_START)
        j = t.index("\n---", i)
        t = t[:j] + NEW_PARA + t[j:]
        # compress the objection paragraph
        k = t.index(OLD_OBJECTION_START, i)
        m = t.index("\n\n", k)
        t = t[:k] + NEW_OBJECTION + t[m:]
        # compress the list paragraph
        p = t.index(OLD_LIST_START)
        q = t.index("\n\n", p)
        t = t[:p] + NEW_LIST + t[q:]
        changed = True
        print("  acceptance-test paragraph added, two paragraphs compressed")
    if a.apply and changed:
        io.open(MD, "w", encoding="utf-8", newline="").write(t)
        print("  written")
        r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "_build_prl_tex.py")], cwd=REPO,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        print((r.stdout or "")[-700:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
