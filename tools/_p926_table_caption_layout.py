# -*- coding: utf-8 -*-
r"""Give every supplement table the same table-caption layout, with real air above the caption.

Three things were wrong at once:

1. IEEEtran sets table captions **below** the float and spaces them with `\abovecaptionskip`
   (0.75\baselineskip = 9 pt in journal mode = 3.2 mm, which is what was measured).
2. The `caption` package (which I added) overrode that, and it also warns "Unknown document class" for
   IEEEtran. Its `skip` option applied to a different gap depending on where `\caption` sits.
3. Four of the five tables put `\caption` **before** the tabular, i.e. above the table, against the
   class's own convention.

Fix: drop the `caption` package, raise `\abovecaptionskip` to 20 pt (about 7 mm), and move the captions of
tables S1, S2, S4 and S5 below their tabulars so all five match and the extra space lands between the
table and its caption.

    python tools/_p926_table_caption_layout.py [--apply]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"
B = chr(92)

CAPTION_PKG = B + "usepackage{caption}\n"
CAPTIONSETUP_OLD = B + "captionsetup{skip=23pt}   % rule-to-caption gap: 3.4 mm before, about 8 mm now\n"
SKIP_NEW = B + "setlength{" + B + "abovecaptionskip}{20pt}   % air between a table and its caption\n"


def move_caption_below(block: str) -> tuple[str, bool]:
    """Move a \\caption{...} that sits before \\begin{tabular} to just before \\end{table*}."""
    cap = re.search(re.escape(B) + r"caption\{", block)
    tab = block.find(B + "begin{tabular}")
    if cap is None or tab < 0 or cap.start() > tab:
        return block, False
    # find the matching brace of the caption argument
    i = cap.end() - 1
    depth = 0
    while i < len(block):
        if block[i] == "{":
            depth += 1
        elif block[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    assert depth == 0, "unbalanced braces in a caption"
    caption = block[cap.start(): i + 1]
    rest = block[: cap.start()] + block[i + 1:]
    end = rest.rfind(B + "end{table")
    assert end > 0, "no end{table} in this block"
    return rest[:end] + caption + "\n" + rest[end:], True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SUPP.read_text(encoding="utf-8")
    out = t

    if CAPTION_PKG in out:
        out = out.replace(CAPTION_PKG, "", 1)
        print("  dropped the caption package (IEEEtran warns it is an unknown class)")
    if CAPTIONSETUP_OLD in out:
        out = out.replace(CAPTIONSETUP_OLD, SKIP_NEW, 1)
        print(f"  captionsetup -> \\setlength{{\\abovecaptionskip}}{{20pt}}")
    elif SKIP_NEW not in out:
        anchor = B + "hypersetup{hidelinks}   % no coloured link boxes in the print version\n"
        assert out.count(anchor) == 1, "hidelinks anchor not unique"
        out = out.replace(anchor, anchor + SKIP_NEW, 1)
        print("  added \\setlength{\\abovecaptionskip}{20pt}")

    # move the captions that sit above their table
    moved = 0
    for m in list(re.finditer(re.escape(B) + r"begin\{table\*?\}", out)):
        start = m.start()
        end = out.find(B + "end{table", start)
        end = out.find("}", end) + 1          # end of \end{table} / \end{table*}
        block = out[start:end]
        new_block, changed = move_caption_below(block)
        if changed:
            out = out[:start] + new_block + out[end:]
            moved += 1
            ln = out[:start].count("\n") + 1
            print(f"  line {ln}: caption moved below the table")
    print(f"  captions moved: {moved}")

    if not a.apply:
        print("  (dry run)")
        return 0
    SUPP.write_text(out, encoding="utf-8", newline="")

    check = SUPP.read_text(encoding="utf-8")
    assert B + "usepackage{caption}" not in check
    assert B + "abovecaptionskip}{20pt}" in check
    for m in re.finditer(re.escape(B) + r"begin\{table\*?\}", check):
        start = m.start()
        end = check.find(B + "end{table", start)
        block = check[start:end]
        cap = block.find(B + "caption")
        tab = block.find(B + "begin{tabular}")
        assert cap > tab, "a caption is still above its table"
    print("  written and verified: all five captions below their tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
