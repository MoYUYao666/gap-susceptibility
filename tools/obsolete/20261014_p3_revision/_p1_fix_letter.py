# -*- coding: utf-8 -*-
"""
Repair cover_letter_revision.tex after an re.sub replacement-string pitfall.

re.subn processes escape sequences in the *replacement*: \\a became BEL, \\b became
backspace, and \\\\ collapsed to a single backslash, so the two inserted rows lost
\\addlinespace, \\bottomrule and their row terminators.  The fix uses a lambda so the
replacement is inserted verbatim.
"""
import io
import os
import re
import sys

P = os.path.join(r"D:\Realdesktop\Wan\Important\New", "paper", "cover_letter_revision.tex")
src = io.open(P, encoding="utf-8").read()

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

# match everything from the corrupted first row up to the corrupted bottomrule
pat = re.compile(r"Zero-shot protocol &.*?ottomrule", re.S)
if not pat.search(src):
    print("corrupted block not found; nothing to repair")
    sys.exit(1)
fixed = pat.sub(lambda m: ROW + "\\bottomrule", src, count=1)
# sanity: no control characters left
bad = [c for c in ("\x07", "\x08", "\x0c", "\x0b") if c in fixed]
if bad:
    print("control characters still present: %r" % bad)
    sys.exit(1)
io.open(P, "w", encoding="utf-8", newline="").write(fixed)
print("repaired cover_letter_revision.tex")
