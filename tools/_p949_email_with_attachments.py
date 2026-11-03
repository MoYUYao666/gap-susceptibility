# -*- coding: utf-8 -*-
r"""Write the request as a plain email with the three replacement files attached.

Operator finding, 2026-10-15: the submission system's **Send E-mail** has no attachment path, so the files
can only reach the journal by email. This version of the request is written for that route: it says
plainly why the journal is receiving files by email rather than through the system, identifies the
submission, lists the three attachments, and leaves the office free to say "leave it until revision".

Send to the address the journal has already written to you from (a notification from the submission
system carries it), or to the handling editor. Do not invent an address: the author guide page for this
journal is not publicly reachable.

    python tools/_p949_email_with_attachments.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REV = REPO / "SUBMISSION" / "P3_PRL_revision"
OUT = REV / "EMAIL_direct_with_attachments.txt"

SUBJECT = ("PRLETTERS-D-26-02378R1 - replacement files (manuscript, Supplementary Material, "
           "LaTeX source)")

PARAGRAPHS = [
    "Dear Editor,",

    "I am the corresponding author of PRLETTERS-D-26-02378R1, \"Zero-Shot Cross-Architecture Rank "
    "Allocation from Gradient Geometry\", which is currently under review. I wrote earlier today "
    "through the submission system to ask whether I may replace three files, and I am following that "
    "up by email because the system's message function does not carry attachments.",

    "While preparing the final version I found two defects in the files uploaded on 13 October. Neither "
    "affects any result, number, figure or conclusion. First, the manuscript's pointers to the "
    "Supplementary Material do not match the supplement: four section numbers and one range are wrong, "
    "because the supplement has nine sections while the text refers to six and to sections S3, S4 and "
    "S5 for material that sits in S8 and S9. Second, the supplement contains seven malformed "
    "cross-references, which are visible in the PDF: a theorem reference with no number, two \"Table "
    "the main text\" pointers, three \"Table Supplementary Table Sx\" pointers, a figure pointer, and a "
    "doubled \"Lemma Lemma\". Two of those refer to a table and a figure that do not exist.",

    "The three attached files would replace the versions on record:",

    "- PRLETTERS-D-26-02378_Manuscript.pdf - the manuscript, 10 pages. Identical to the submitted "
    "version except for five pointers; no sentence, number, table or figure changes.",

    "- PRLETTERS-D-26-02378_Supplementary.pdf - the Supplementary Material, 6 pages. Every "
    "cross-reference resolves, the section order is aligned with the numbering the manuscript uses, and "
    "the sample-size table that the supplement promised but did not contain is now included.",

    "- P3_PRLETTERS-D-26-02378_LaTeX_Source.zip - the source archive, rebuilt so that it matches the "
    "revised sources. It contains main.tex with its bibliography and six section files, two figure "
    "files, and the supplement with its own bibliography and two figure files, and it compiles on its "
    "own: extracting it into an empty folder reproduces both documents with no errors and no unresolved "
    "references.",

    "If it is easier for the office, nothing needs to change now: the faults are typographical, and I "
    "will apply exactly these corrections at the revision stage. I would be grateful for a one-line "
    "indication of which you prefer, so that I do not leave a request open while the review is running.",

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
    assert longest <= WIDTH, longest
    assert not any(c in body for c in "*`#")
    assert not any(ord(c) > 126 for c in body)
    for phrase in ("under review", "three attached files", "revision stage"):
        assert phrase in body, phrase

    header = (
        "Manuscript: PRLETTERS-D-26-02378R1\n"
        "Journal: Pattern Recognition Letters\n"
        "Status: Under Review\n"
        "\n"
        "Send this with the three files attached (total about 0.9 MB):\n"
        "  SUBMISSION/P3_PRL_revision/UPLOAD_2026-10-15/P3_PRLETTERS-D-26-02378_Manuscript.pdf\n"
        "  SUBMISSION/P3_PRL_revision/UPLOAD_2026-10-15/P3_PRLETTERS-D-26-02378_Supplementary.pdf\n"
        "  SUBMISSION/P3_PRL_revision/UPLOAD_2026-10-15/P3_PRLETTERS-D-26-02378_LaTeX_Source.zip\n"
        "\n"
        "To: the address the journal has written to you from, or the handling editor. The journal's\n"
        "author-guide page is not publicly reachable, so no address is suggested here rather than a\n"
        "guessed one.\n"
        "\n"
        "Subject: " + SUBJECT + "\n"
        "\n"
        "---- body ----\n"
    )
    text = header + "\n" + body
    if not a.apply:
        print("  (dry run)")
        print(f"  body: {len(PARAGRAPHS)} paragraphs, longest line {longest}")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(text)
    print(f"  wrote {OUT.name}: {len(text.splitlines())} lines, longest body line {longest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
