# -*- coding: utf-8 -*-
r"""Write the follow-up message for the Editorial Office after P3 moved to Under Review.

Context: `PRLETTERS-D-26-02378R1` went to **Under Review** on 2026-10-15, and the replacement request was
sent through the Editorial Manager query form on the same day. A manuscript under review cannot be
replaced from the author side; the Editorial Office can still act on it, but the reviewers may already
hold the submitted files.

The follow-up is deliberately short and does not re-argue the request: it acknowledges the new status,
asks which of two timings the office prefers, and states that either answer is fine.

    python tools/_p946_followup_under_review.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "SUBMISSION" / "P3_PRL_revision" / "EMAIL_TO_EM_2026-10-15_FOLLOWUP_under_review.txt"

HEADER = """Manuscript: PRLETTERS-D-26-02378R1
Journal: Pattern Recognition Letters
Status: Under Review (seen 2026-10-15)
Follows: the replacement request sent earlier the same day
Query subject: PRLETTERS-D-26-02378R1 - follow-up to the file replacement request

---- text to paste into the Editorial Manager query box ----
"""

PARAGRAPHS = [
    "Dear Editorial Office,",

    "I wrote earlier today to ask whether I may replace three files of my revised submission "
    "(the manuscript, its Supplementary Material, and the LaTeX source archive), because the uploaded "
    "supplement contains several broken cross-references and the manuscript's pointers to it do not "
    "match. I see that the manuscript has since moved to Under Review, so I would like to ask how you "
    "would prefer to handle it.",

    "If the replacement can be applied now, I can upload the three files immediately, and the "
    "reviewers would then be reading files whose references resolve. If it is easier for the office to "
    "leave the files as they are, that is equally acceptable: the faults are typographical, they do not "
    "affect any result, number, figure or conclusion, and I can apply the same corrections at the "
    "revision stage.",

    "Either way I would be grateful for a one-line indication of your preference, so that I do not "
    "leave a pending request open while the review is running.",

    "Thank you for your time.",

    "Sincerely,",

    "Hongrui Wan\nCorresponding author\nhw4c24@soton.ac.uk\nUniversity of Southampton",
]

WIDTH = 80


def wrap(par: str) -> str:
    if "\n" in par:
        return par
    return "\n".join(textwrap.wrap(par, width=WIDTH, break_long_words=False, break_on_hyphens=False))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    body = "\n\n".join(wrap(p) for p in PARAGRAPHS) + "\n"
    longest = max(len(l) for l in body.splitlines())
    print(f"  paragraphs {len(PARAGRAPHS)}, longest body line {longest}")
    assert longest <= WIDTH
    assert not any(c in body for c in "*`#")
    assert not any(ord(c) > 126 for c in body)
    for phrase in ("Under Review", "three files", "revision"):
        assert phrase in body, f"missing {phrase!r}"
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(HEADER + "\n" + body)
    print(f"  wrote {OUT.name} ({len((HEADER + body).splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
