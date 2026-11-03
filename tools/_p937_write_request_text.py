# -*- coding: utf-8 -*-
r"""Write the EM request text from a single clean source, re-wrapped at 80 columns.

The incremental edits left the paragraph about the LaTeX source archive broken mid-sentence (a wrapping
bug: the text was split on runs of spaces, so the inserted paragraph's own newlines were treated as
paragraph breaks). This rewrites the whole file from one place, so the wrapping is applied once.

    python tools/_937_write_request_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EMAIL = REPO / "SUBMISSION" / "P3_PRL_revision" / "EMAIL_TO_EM_2026-10-15.txt"

HEADER = """Manuscript: PRLETTERS-D-26-02378R1
Journal: Pattern Recognition Letters
Article: Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry
Query subject (used by the operator in the form): PRLETTERS-D-26-02378R1 - request to replace the manuscript, its Supplementary Material and the LaTeX source

---- text to paste into the Editorial Manager query box ----
"""

PARAGRAPHS = [
    "Dear Editor,",

    "I am writing to request permission to replace three files in my revised submission: the "
    "manuscript, its Supplementary Material, and the LaTeX source archive. While preparing the final "
    "version I found two defects in the files that were uploaded on 13 October 2026. Neither affects "
    "any result, number, figure or conclusion. Both are internal cross-reference faults, and I would "
    "like to correct them rather than leave them in the record.",

    "1. The manuscript's pointers to the Supplementary Material do not match the supplement as "
    "submitted. Four section numbers and one range are wrong. The text says \"Supplementary Sections "
    "S1-S6\", while the supplement has nine sections. It points to Section S3 for the sample-size "
    "material and again to S3 for the second-dataset material, to Section S4 for the rank-scaling "
    "material and to Section S5 for the comparison with prior work, whereas in the submitted "
    "supplement that material sits in Sections S8 and S9. The supplement does contain all of it. Only "
    "the pointers are wrong.",

    "2. The supplement as submitted contains seven malformed cross-references, which are visible in "
    "the PDF. They print as:",

    "- \"A. Step-by-step proof of Theorem the main text\", where the theorem number is missing",

    "- \"Table the main text reports the measured per-block values\", which occurs twice",

    "- \"Table Supplementary Table S4\" and \"Table Supplementary Table S3\"",

    "- \"Table Supplementary Table S2\", which refers to a table that does not exist in the supplement",

    "- \"Figure Supplementary Figure S3\", which refers to a figure that does not exist in the "
    "supplement",

    "- \"Lemma Lemma 1 of the main text\"",

    "What I would upload as the replacement, three files:",

    "- The manuscript. Identical except for the five pointers listed above. No sentence, number, table "
    "or figure changes.",

    "- The Supplementary Material. Every cross-reference now resolves to a real object, the order of "
    "the sections is adjusted so that the numbering the manuscript uses lands on the right content, "
    "and one table that the supplement promised but did not contain, the sample-size sweep over "
    "n = 16, 64, 128 and 256, is now included. It is built from the archived per-run records (20 runs, "
    "one seed, four epochs), and its caption states the seed count and the epoch count.",

    "- The LaTeX source archive, rebuilt from the revised sources. The archive uploaded on 13 October "
    "no longer matches the manuscript and the supplement, so leaving it in place would give the "
    "journal sources that do not correspond to the PDFs. It is packaged as before: main.tex with its "
    "bibliography and six section files, two figure files, and the supplement with its own "
    "bibliography and two figure files. It compiles on its own, and extracting it into an empty folder "
    "reproduces both documents with no errors and no unresolved references.",

    "In addition to the two defects above, the replacement corrects three typographical faults in the "
    "manuscript that I found while preparing it. The theorem-like environments did not separate their "
    "number from the following note, so a statement read \"Theorem III.2(Projection Error Bound)\"; "
    "the five corollaries were named in subsection headings rather than set as corollaries; and "
    "hyperref drew a coloured box around every citation and cross-reference. None of these changes a "
    "result, a number, a table or a figure. The supplement is unchanged apart from the "
    "cross-reference repairs and the added table described above.",

    "I have checked the three files against one another, and both documents compile without any "
    "unresolved reference. If it is more convenient, I am happy to supply a marked comparison of the "
    "old and new versions, or to upload only the Supplementary Material and the source archive, in "
    "which case the manuscript changes only in the five numbers listed above.",

    "Could you let me know whether a replacement upload is possible at this stage, and in which file "
    "slots the corrected files should go?",

    "With apologies for the extra work, and thank you for your time.",

    "Sincerely,",

    "Hongrui Wan\nCorresponding author\nhw4c24@soton.ac.uk\nUniversity of Southampton",
]

WIDTH = 80


def wrap(par: str) -> str:
    if "\n" in par:                       # the signature block: keep its own line structure
        return par
    return "\n".join(textwrap.wrap(par, width=WIDTH, break_long_words=False, break_on_hyphens=False))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    body = "\n\n".join(wrap(p) for p in PARAGRAPHS) + "\n"
    text = HEADER + "\n" + body
    longest = max(len(l) for l in body.splitlines())
    print(f"  paragraphs: {len(PARAGRAPHS)}, longest body line: {longest}")
    assert longest <= WIDTH, f"a line is too long: {longest}"
    assert "*" not in body and "`" not in body and "#" not in body
    assert not any(ord(c) > 126 for c in body)
    for phrase in ("three files", "LaTeX source archive", "S1-S6", "sample-size sweep"):
        assert phrase in body, f"missing {phrase!r}"
    print("  asked for three files; source archive, supplement and manuscript all described")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(EMAIL, "w", encoding="utf-8", newline="").write(text)
    print(f"  wrote {EMAIL.name}: {len(text.splitlines())} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
