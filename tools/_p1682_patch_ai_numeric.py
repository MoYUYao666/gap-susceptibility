"""One-off patch: switch the Applied Intelligence root.tex to the numeric Springer reference style.

Why: the Applied Intelligence guide requires "Reference citations in the text ... numbers in square
brackets" and "entries in the list ... numbered consecutively" (guide lines 169/181). The same guide also
carries the generic sentence that authors "can use the bibliography style file sn-basic.bst", but
sn-basic.bst produces NAME-YEAR citations, which contradicts the journal's explicit citation rule.
The numeric Springer style `sn-mathphys-num` is therefore used (it renders "LoRA [1]").

Usage: python tools/_p1682_patch_ai_numeric.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "tools" / "_p1680_build_ai_package.py"

REPLACEMENTS = [
    (r'DCLASS = r"\documentclass[pdflatex,sn-basic,onecolumn]{sn-jnl}"',
     r'DCLASS = r"\documentclass[pdflatex,sn-mathphys-num,onecolumn]{sn-jnl}"'),
    (r"\documentclass[pdflatex,sn-basic,onecolumn]{sn-jnl}",
     r"\documentclass[pdflatex,sn-mathphys-num,onecolumn]{sn-jnl}"),
    ("sn-jnl's 'onecolumn' option reproduces the single-column condensed layout, and 'sn-basic'\n"
     "%% is the numeric reference style requested for this submission.",
     "sn-jnl's 'onecolumn' option reproduces the single-column condensed layout, and\n"
     "%% 'sn-mathphys-num' is the numeric square-bracket reference style the journal's format rules require\n"
     "%% (the guide's generic mention of sn-basic.bst is superseded: sn-basic produces name-year citations,\n"
     "%% which contradicts the journal's own \"numbers in square brackets\" rule)."),
    ("# the sn-basic class option already emits \\bibstyle{sn-basic}; a second \\bibliographystyle",
     "# the sn-mathphys-num class option already emits \\bibstyle{sn-mathphys-num}; a second \\bibliographystyle"),
    ("| `Manuscript.pdf` | full manuscript, Springer `sn-jnl` build (single column, `sn-basic` numeric bibliography) |",
     "| `Manuscript.pdf` | full manuscript, Springer `sn-jnl` build (single column, numeric square-bracket references) |"),
    ("`sn-jnl` is used with `onecolumn` (single-column condensed layout) and `sn-basic` (numeric references),",
     "`sn-jnl` is used with `onecolumn` (single-column condensed layout) and `sn-mathphys-num` (numeric\n  square-bracket references: the guide's format rules require numbers in square brackets, while the generic\n  sentence mentioning `sn-basic.bst` would give name-year citations),"),
]


def main() -> int:
    text = io.open(BUILDER, encoding="utf-8").read()
    rc = 0
    for old, new in REPLACEMENTS:
        n = text.count(old)
        print("%-55r -> %d occurrence(s)" % (old[:55], n))
        if n != 1:
            rc = 2
            continue
        text = text.replace(old, new, 1)
    if rc:
        print("FATAL: a replacement did not match exactly once")
        return rc
    io.open(BUILDER, "w", encoding="utf-8", newline="\n").write(text)
    left = text.count("sn-basic")
    print("written; remaining 'sn-basic' mentions:", left)
    return 0


if __name__ == "__main__":
    sys.exit(main())
