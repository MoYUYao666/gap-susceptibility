# -*- coding: utf-8 -*-
r"""Clean the supplement preamble and set the table-to-caption spacing.

Two duplicate lines are in the preamble from earlier patches (`\usepackage{array}` and
`\hypersetup{hidelinks}` each twice). LaTeX tolerates both, but they should not be there.

Then: "TABLE S3 标题再远一点" -- the caption sat 20 px below the bottom rule on the rendered page, i.e.
3.4 mm = 10 pt, which is the class default. `\captionsetup{skip=16pt}` gives about 5.6 mm, applied to all
five supplement tables so they stay consistent.

    python tools/_p924_caption_spacing.py [--apply]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"
B = chr(92)

ARRAY = B + "usepackage{array}   % >{...} column modifiers, used by the fixed-width tables\n"
HIDE = B + "hypersetup{hidelinks}   % no coloured link boxes in the print version\n"
CAPTION = (B + "usepackage{caption}\n"
           + B + "captionsetup{skip=16pt}   % more air between a table and its caption\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SUPP.read_text(encoding="utf-8")
    problems = []
    if t.count(ARRAY) > 1:
        problems.append(f"array x{t.count(ARRAY)}")
    if t.count(HIDE) > 1:
        problems.append(f"hidelinks x{t.count(HIDE)}")
    print(f"  duplicates found: {problems if problems else 'none'}")

    out = t
    if out.count(ARRAY) > 1:
        out = out.replace(ARRAY + ARRAY, ARRAY, 1)
    if out.count(HIDE) > 1:
        out = out.replace(HIDE + HIDE, HIDE, 1)
    if B + "captionsetup{skip=16pt}" not in out:
        assert out.count(HIDE) == 1, "the hidelinks anchor is not unique after de-duplication"
        out = out.replace(HIDE, HIDE + CAPTION, 1)
        print("  caption spacing: 10 pt (3.4 mm, measured) -> 16 pt (about 5.6 mm)")
    else:
        print("  caption spacing already set")

    print(f"  array x{out.count(ARRAY)}, hidelinks x{out.count(HIDE)}, "
          f"captionsetup x{out.count(B + 'captionsetup{skip=16pt}')}")
    assert out.count(ARRAY) == 1 and out.count(HIDE) == 1
    assert out.count(B + "captionsetup{skip=16pt}") == 1

    if not a.apply:
        print("  (dry run)")
        return 0
    SUPP.write_text(out, encoding="utf-8", newline="")
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
