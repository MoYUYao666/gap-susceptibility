"""Fix the leftover Python source fragments in 07_discussion.tex (a content defect that gets printed into the PDF).

Defect: three lines of Python raw-string source got mixed into the limitations paragraph
      r'gradient-path gating ... '
      r'image-token path ... '
      r'not, and that the crossing ...'
They are typeset as body text by LaTeX and show up in the PDF as "’ r’gradient-path ..." (a compile audit cannot catch content-level defects).
Fix: strip the r'...' wrapper and the stray ' at the end of the line, splice the prose back together as intended; leave all other text untouched.
"""
import re
import sys

P = 'paper_ap3/sections/07_discussion.tex'
OLD = ("isolated: '\r\n"
       "       r'gradient-path gating (Section~\\ref{sec:gradmask}, Table~\\ref{tab:gradmask}) shows that blocking the '\r\n"
       "       r'image-token path removes $79\\%$ of the $r{=}6$ damage while blocking the language-token path does '\r\n"
       "       r'not, and that the crossing itself still requires")
NEW = ("isolated: gradient-path gating (Section~\\ref{sec:gradmask}, Table~\\ref{tab:gradmask}) shows that blocking "
       "the image-token path removes $79\\%$ of the $r{=}6$ damage while blocking the language-token path does not, "
       "and that the crossing itself still requires")

src = open(P, encoding='utf-8', newline='').read()
if OLD not in src:
    print('FATAL: anchor not found (it may already be fixed, or the file changed)')
    sys.exit(1)
src = src.replace(OLD, NEW, 1)
open(P, 'w', encoding='utf-8', newline='').write(src)

# Verification: there should be no full line starting with r'
leftover = [i + 1 for i, ln in enumerate(src.split('\r\n')) if ln.lstrip().startswith("r'")]
print(f'Fix complete; leftover lines starting with r\': {leftover if leftover else "none"}')
print(f'Count of "gradient-path gating" occurrences: {len(re.findall("gradient-path gating", src))}')
