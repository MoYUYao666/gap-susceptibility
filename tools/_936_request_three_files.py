# -*- coding: utf-8 -*-
r"""Update the prepared request so it asks to replace three files, not two.

The replacement set now includes the LaTeX source archive (operator: "latexsource也需要重传"), so the
request text has to say three files and name them. The query already sent through the Editorial Manager
cannot be edited, so this is kept ready for a follow-up message.

    python tools/_936_request_three_files.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EMAIL = REPO / "SUBMISSION" / "P3_PRL_revision" / "EMAIL_TO_EM_2026-10-15.txt"
SEP = "---- text to paste into the Editorial Manager query box ----"
WIDTH = 80

SUBJECT_OLD = "I am writing to request permission to replace two files in my revised submission: the manuscript and\nits Supplementary Material."
SUBJECT_NEW = ("I am writing to request permission to replace three files in my revised submission: the\n"
               "manuscript, its Supplementary Material, and the LaTeX source archive.")

WHOLE_OLD = "What I would upload as the replacement:"
WHOLE_NEW = ("What I would upload as the replacement:\n"
             "\n"
             "   The LaTeX source archive, rebuilt from the revised sources. The archive uploaded on\n"
             "   13 October no longer matches the manuscript and the supplement, so leaving it in place\n"
             "   would give the journal sources that do not correspond to the PDFs. It is packaged as\n"
             "   before (main.tex with its bibliography and six section files, two figure files, and the\n"
             "   supplement with its own bibliography and two figure files), and it compiles on its own:\n"
             "   extracting it into an empty folder gives the manuscript and the supplement with no\n"
             "   errors and no unresolved references.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    raw = io.open(EMAIL, encoding="utf-8").read()
    head, body = raw.split(SEP, 1)
    flat = body.replace("\n", " ")

    if "three files in my revised submission" in flat and "LaTeX source archive, rebuilt" in flat:
        print("  already updated to three files")
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0

    body = " ".join(body.split())
    for old, new in ((SUBJECT_OLD.replace("\n", " "), SUBJECT_NEW.replace("\n", " ")),
                     (WHOLE_OLD, WHOLE_NEW.replace("\n", " "))):
        assert old in body, f"anchor not found: {old[:60]!r}"
        body = body.replace(old, new, 1)

    # re-wrap to 80 columns, paragraph per blank line, bullets kept as bullets
    out = []
    for block in body.split("   "):
        block = block.strip()
        if not block:
            continue
        out.extend(textwrap.wrap(block, width=WIDTH - 3, initial_indent="   ",
                                 subsequent_indent="   ", break_long_words=False, break_on_hyphens=False))
        out.append("")
    text = "\n".join(out).rstrip() + "\n"
    assert max(len(l) for l in text.splitlines()) <= WIDTH
    io.open(EMAIL, "w", encoding="utf-8", newline="").write(head + SEP + "\n\n" + text)
    check = io.open(EMAIL, encoding="utf-8").read()
    assert "three files" in check and "LaTeX source archive" in check
    print("  request text now asks to replace three files, with the source archive described")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
