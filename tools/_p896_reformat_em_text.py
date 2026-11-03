# -*- coding: utf-8 -*-
r"""Reflow the Editorial Manager query text: no Subject line, wrapped at 80 columns.

The version first prepared began with a "Subject:" line, which the EM query form has no field for (the
operator pasted the text without it), and had lines up to 103 characters, which the form wraps itself
and can leave a stray word on its own line. This rewrites the same text as a plain, evenly wrapped
block ready to paste, and keeps the document header for the record.

    python tools/_p896_reformat_em_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "SUBMISSION" / "P3_PRL_revision" / "EMAIL_TO_EM_2026-10-15.txt"
WIDTH = 80


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    raw = io.open(SRC, encoding="utf-8").read()
    body = raw.split("\n", 1)[1] if raw.startswith("Subject:") else raw
    body = body.lstrip("\n")

    out_lines: list[str] = []
    for block in body.split("\n\n"):
        # keep the bullet list ("   - ...") as its own paragraphs, one per item
        if block.lstrip().startswith("-"):
            for item in block.split("\n"):
                item = item.strip()
                if not item:
                    continue
                wrapped = textwrap.wrap(item, width=WIDTH, subsequent_indent="  ",
                                        break_long_words=False, break_on_hyphens=False)
                out_lines.extend(wrapped)
        else:
            out_lines.extend(textwrap.wrap(" ".join(block.split()), width=WIDTH,
                                           break_long_words=False, break_on_hyphens=False))
        out_lines.append("")
    title = raw.split("\n", 1)[0].replace("Subject: ", "")

    header = [
        "Manuscript: PRLETTERS-D-26-02378R1",
        "Journal: Pattern Recognition Letters",
        "Article: Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry",
        "Query subject (used by the operator in the form): " + title,
        "",
        "---- text to paste into the Editorial Manager query box ----",
        "",
    ]
    final = "\n".join(header + out_lines).rstrip() + "\n"

    longest = max(len(l) for l in out_lines)
    print(f"  longest body line: {longest} (target <= {WIDTH})")
    assert longest <= WIDTH, f"a body line is too long: {longest}"
    assert "*" not in final and "`" not in final and "#" not in final
    assert not any(ord(c) > 126 for c in final)
    if not a.apply:
        print("  (dry run)")
        return 0
    SRC.write_text(final, encoding="utf-8", newline="")
    print(f"  wrote {SRC.relative_to(REPO).as_posix()} ({len(final.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
