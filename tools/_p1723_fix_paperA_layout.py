# -*- coding: utf-8 -*-
r"""Fix four layout defects the operator reported in Paper A's reframed tree:

  1. duplicated subsection headings (an old short heading kept right above the new descriptive one);
  2. Table 1's bold convention contradicting its caption, and the broken bold-minus rendering
     (`\\mathbf{-0.0465}` renders as a bar over the digits; `\\bm` is the correct bold-math command);
  3. no paragraph indentation after a heading (`indentfirst` was never loaded);
  4. the old schematic figure (regenerated separately by `_p1722_fig_site_schematic.py`).

Idempotent; every substitution is asserted.
"""
import io
import os
import re

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RES = "paper合/reframed/sections/50_results.tex"
t = io.open(RES, encoding="utf-8").read()
orig = t

# ---- 1. duplicate subsection headings (delete the stale short one) ------------------------
STALE = [
    "\\subsection{The distribution gap and retrieval}\n\n",
    "\\subsection{Cross-dataset and cross-method fits}\n\n",
    "\\subsection{The measured gradient asymmetry}\n\n",
    "\\subsection{Zero-shot classification}\n\n",
]
removed = 0
for s in STALE:
    if s in t:
        t = t.replace(s, "", 1)
        removed += 1
print("stale duplicate headings removed:", removed)

# ---- 2. Table 1: bold convention + bold math --------------------------------------------
# bold must not use \mathbf inside math (breaks the minus); \bm renders bold minus and digits
n_mathbf = t.count("\\mathbf{")
t = t.replace("\\mathbf{", "\\bm{")
print("\\mathbf -> \\bm in results:", n_mathbf)

old_cap = "Each entry is $\\Delta$CG with\n$R@1$ beneath it (bold marks the smallest $\\Delta$CG in the row)"
new_cap = ("Each entry is $\\Delta$CG with\n$R@1$ beneath it (bold marks the smallest $\\Delta$CG "
           "and the best $R@1$ in the row)")
assert old_cap in t, "caption sentence not found verbatim"
t = t.replace(old_cap, new_cap, 1)

io.open(RES, "w", encoding="utf-8", newline="").write(t)
print("results section changed:", t != orig)

# ---- 3. indentfirst + bm in the two preambles -------------------------------------------
PREAMBLE_ADD = "\\usepackage{indentfirst}\n\\usepackage{bm}\n"


def patch_preamble(path, anchor=None):
    s = io.open(path, encoding="utf-8").read()
    if "\\usepackage{indentfirst}" in s:
        print("  already has indentfirst:", path)
        return
    if anchor and anchor in s:
        s = s.replace(anchor, anchor + "\n" + PREAMBLE_ADD, 1)
    elif "\\begin{document}" in s:
        s = s.replace("\\begin{document}", PREAMBLE_ADD + "\\begin{document}", 1)
    else:
        print("  WARNING: no anchor in", path)
        return
    io.open(path, "w", encoding="utf-8", newline="").write(s)
    print("  preamble patched:", path)


patch_preamble("paper合/reframed/main.tex")
patch_preamble("tools/_p1720_build_ml_package.py", anchor="\\usepackage{placeins}")
print("done")
