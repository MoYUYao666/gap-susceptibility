# -*- coding: utf-8 -*-
"""
P1 patch G: correction-letter LaTeX error, the revision letter's Prefix claim, and the
reconciliation of the two 2026-08-14 letters the journal already holds.

G1 cover_letter_zeroshot_correction.tex:47 uses $\\text{CG}$ without amsmath, which is an
   undefined control sequence; LaTeX still emitted a PDF, so the copy on file renders
   incompletely there. Fixed to plain CG$\\Delta$.
G2 the revision letter claims "the Adapter and Prefix comparisons"; the manuscript reports
   Adapter only and its conclusion lists prefix tuning as unexplored.
G3 the revision letter silently supersedes both 08-14 letters (zero-shot protocol and the
   change-score correlations); two rows now reconcile them.
"""
import io
import os
import re
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"


def edit(rel, pattern, repl, flags=0, expect=1):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    src = io.open(p, encoding="utf-8").read()
    new, n = re.subn(pattern, repl, src, count=expect, flags=flags)
    if n != expect:
        print("FAIL %s: %d matches for %s" % (rel, n, pattern[:50]))
        return False
    io.open(p, "w", encoding="utf-8", newline="").write(new)
    print("ok   %s" % rel)
    return True


ok = []
ok.append(edit("paper/cover_letter_zeroshot_correction.tex",
               r"\$\\text\{CG\}\\Delta=\+0\.237\$", r"CG$\\Delta=+0.237$"))
ok.append(edit("paper/cover_letter_revision.tex",
               r"the Adapter and\s+Prefix\s+comparisons,", "the Adapter comparison,"))
ROW = ("Zero-shot protocol & The 2026-08-14 letter reported the ImageNet values as frozen "
       "59.37 / text-only 58.76 / full fine-tuning 0.13\\% on a 14{,}288-image subset, and "
       "stated that the table footnote said so & The manuscript reports the same measurement "
       "on the full 50{,}000-image validation set (59.28 / 58.66 / 2.6\\% over three retrained "
       "seeds) and gives that protocol in the footnote. The two describe the same conclusion "
       "measured on different subsets, and the manuscript is the version to rely on. \\\\\n"
       "\\addlinespace\n"
       "Change-score correlations & The 2026-08-14 letter corrected them to $r=-0.042$ "
       "($p=0.713$) and $r=+0.012$ ($p=0.915$) & Recomputed on the reproducible archive they "
       "are $+0.134$ ($p=0.055$) and $+0.190$ ($p=0.007$); both remain far weaker than the "
       "level correlations, which is the point the manuscript makes. \\\\\n")
ok.append(edit("paper/cover_letter_revision.tex", r"\\bottomrule", ROW + "\\bottomrule"))

sys.exit(0 if all(ok) else 1)
