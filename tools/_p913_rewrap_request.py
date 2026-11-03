# -*- coding: utf-8 -*-
r"""Re-wrap the body of the prepared EM request at 80 columns, keeping its header block intact.

The file is "header lines, a separator, then the text to paste". Only the text after the separator is
re-wrapped, so this can be run again after any paragraph is inserted.

    python tools/_p913_rewrap_request.py [--apply]
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    raw = io.open(EMAIL, encoding="utf-8").read()
    assert SEP in raw, "the separator line is missing"
    head, body = raw.split(SEP, 1)
    body = body.lstrip("\n")

    out: list[str] = []
    for block in body.split("\n\n"):
        if block.lstrip().startswith("-"):
            for item in block.split("\n"):
                item = item.strip()
                if item:
                    out.extend(textwrap.wrap(item, width=WIDTH, subsequent_indent="  ",
                                             break_long_words=False, break_on_hyphens=False))
        else:
            out.extend(textwrap.wrap(" ".join(block.split()), width=WIDTH,
                                     break_long_words=False, break_on_hyphens=False))
        out.append("")

    body_txt = "\n".join(out).strip() + "\n"
    longest = max(len(l) for l in body_txt.splitlines())
    print(f"  body longest line: {longest}")
    assert longest <= WIDTH, f"a line is too long: {longest}"
    assert "*" not in body_txt and "`" not in body_txt and "#" not in body_txt
    assert not any(ord(c) > 126 for c in body_txt)
    if not a.apply:
        print("  (dry run)")
        return 0

    io.open(EMAIL, "w", encoding="utf-8", newline="").write(head + SEP + "\n\n" + body_txt)
    check = io.open(EMAIL, encoding="utf-8").read()
    assert "typographical" in check and check.count(SEP) == 1
    print(f"  written; {len(check.splitlines())} lines total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
