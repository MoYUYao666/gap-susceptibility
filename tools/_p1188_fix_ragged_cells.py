# -*- coding: utf-8 -*-
r"""Drop the array-package column syntax and set each cell ragged-right explicitly.

`>{\raggedright\arraybackslash}p{...}` needs the array package, which this class does not load, so the build produced
seven errors ("Illegal character in array arg"). Each cell of a `p` column is its own group, so a plain `\raggedright`
at the start of the cell body achieves the same ragged setting without any package.

    python tools/_p1188_fix_ragged_cells.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUP = REPO / "paper合" / "sections" / "supplement.tex"

SPEC_OLD = (r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.15\textwidth}"
            r">{\raggedright\arraybackslash}p{0.20\textwidth}"
            r">{\raggedright\arraybackslash}p{0.55\textwidth}@{}}")
SPEC_NEW = r"\begin{tabular}{@{}p{0.15\textwidth}p{0.20\textwidth}p{0.55\textwidth}@{}}"

# first cell of each row gets the declaration after the alignment ampersand layout
CELL_STARTS = [
    ("\nCore LoRA, Section~I (30 runs) &", "\n\\raggedright Core LoRA, Section~I (30 runs) & \\raggedright"),
    ("\nRoute D combinations (5 runs) &", "\n\\raggedright Route D combinations (5 runs) & \\raggedright"),
    ("\nLayered unfreezing (appendix) &", "\n\\raggedright Layered unfreezing (appendix) & \\raggedright"),
    ("\nStrict freezing, controls (104 runs) &",
     "\n\\raggedright Strict freezing, controls (104 runs) & \\raggedright"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(SUP, encoding="utf-8").read()
    n = t.count(SPEC_OLD)
    print(f"  array-syntax table spec: {n}")
    if n != 1:
        print("  .. spec already replaced or not found; continuing with cell pass")
    else:
        t = t.replace(SPEC_OLD, SPEC_NEW, 1)
    for old, new in CELL_STARTS:
        c = t.count(old)
        print(f"  cell start {old.strip()[:34]!r}: {c}")
        if c == 1:
            t = t.replace(old, new, 1)
    # third cell of each row needs the declaration too: they follow '& ' and start with a capital or backslash
    for marker in ("&\nBatch 128,", "&\nNot the core configuration:", "&\nA different intervention:", "&\nThe arms differ only"):
        if marker in t:
            t = t.replace(marker, marker.replace("&\n", "& \\raggedright\n"), 1)
            print(f"  third cell tagged: {marker[:26]!r}")
    checks = [
        ("no array syntax left", "arraybackslash" not in t),
        ("spec is plain p columns", SPEC_NEW in t),
        ("label intact", "label{tab:config_groups}" in t),
        ("four rows", t.count("\\\\\n\\addlinespace") >= 3),
    ]
    for label, ok in checks:
        print(f"  {'OK  ' if ok else 'FAIL'} {label}")
    if not all(ok for _, ok in checks):
        return 1
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(SUP, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
