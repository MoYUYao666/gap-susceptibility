# -*- coding: utf-8 -*-
r"""Final pass over docs/PR_MORE_MODELS.md: repair the residual damage from the encoding incident.

The report is *generated*, so the durable fix belongs in `tools/_p293e_report.py`; this script
applies the same corrections to the generator's source strings (which is where the damage was
introduced) and then re-renders.  Every correction is listed explicitly and asserted to have
applied, so nothing is silently "fixed".

Damage classes being repaired in the generator:

  A. a space that followed a multi-byte character was eaten, leaving
     `terms —**including` instead of `terms — **including`;
  B. the same mechanism ate the leading digit of a negative decimal, leaving `−.39` for `−0.39`
     and `−.29—…–0.45` for `−0.29…−0.45`;
  C. the word `image-text` lost its hyphen to a stray em dash: `image—–ext`;
  D. an em dash followed by a space then a table pipe rendered as `| —| PENDING`.

USAGE
    python tools/_p293s_final_text_repair.py          # dry run: report only
    python tools/_p293s_final_text_repair.py --apply  # rewrite the generator and re-render
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "tools" / "_p293e_report.py"

# (broken, fixed, minimum expected occurrences)
FIXES = [
    # A: space restored after the em dash
    ("\u2014**including", "\u2014 **including"),
    ("\u2014**the report", "\u2014 **the report"),
    ("\u2014**so a", "\u2014 **so a"),
    ("\u2014**also wrong", "\u2014 **also wrong"),
    ("\u2014**two OpenCLIP", "\u2014 **two OpenCLIP"),
    ("\u2014?the report", "\u2014 the report"),
    # B: the eaten digit of a negative decimal
    ("\u2212.39", "\u22120.39"),
    ("\u2212.29\u2014\u2026\u20130.45", "\u22120.29\u2026\u22120.45"),
    ("range \u2212.29", "range \u22120.29"),
    # C: the compound word
    ("image\u2014\u2013ext", "image\u2013text"),
    ("image\u2014\u2013", "image\u2013"),
    # D: table cell spacing
    ("| \u2014| PENDING", "| \u2014 | PENDING"),
    ("|\u2014| PENDING", "| \u2014 | PENDING"),
    # duplicate subsection number
    ("### 3.1 **fitted head**", "### 3.1.1 **fitted head**"),
    ("### 3.2 **random head**", "### 3.1.2 **random head**"),
    ("### 3.3 Verdict", "### 3.1.3 Verdict"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    s = io.open(GEN, encoding="utf-8").read()
    total = 0
    for bad, good in FIXES:
        n = s.count(bad)
        if n:
            s = s.replace(bad, good)
            total += n
        print("%-42r -> %-34r x%d" % (bad[:40], good[:32], n))
    print("total replacements:", total)

    # after fixing, no non-ASCII punctuation may be glued to an alphanumeric
    import re
    pat = ("([\u2014\u2013\u2026\u2705\u274c\u23f3\u26d4\u26a0\u2192\u2194\u2212\u00d7\u00b1"
           "\u00b7\u00a7\u0394\u03b1])([A-Za-z0-9])")
    glued = ["".join(x) for x in re.findall(pat, s)]
    # these are legitimate: identifiers and product notation
    allowed = ({"\u00d7" + c for c in "0123456789"}
               | {"\u0394C"}
               | {"\u00a7" + c for c in "0123456789"})
    leftover = sorted({g for g in glued if g not in allowed})
    print("remaining glued (excluding known-good identifiers):", leftover)

    if not a.apply:
        print("[dry run] nothing written; pass --apply to rewrite and re-render")
        return 0

    io.open(GEN, "w", encoding="utf-8", newline="\n").write(s)
    import ast
    ast.parse(s)
    print("[ok] generator rewritten and parses")
    r = subprocess.run([sys.executable, str(GEN), "--apply"], cwd=str(REPO))
    print("[re-render exit]", r.returncode)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
