# -*- coding: utf-8 -*-
r"""Repair the S28 sentence that `_p1622_add_min_margin.py` split in the middle of `$0.05$`.

The insertion anchored on the first occurrence of "0.0057" and cut the pre-declared margin in half, so the PDF
rendered "the pre-declared margin of 0. ... .05". Both audit checkers were blind to it; this script repairs the
text *and* adds a needle that asserts the intact phrase, so the failure mode cannot come back unnoticed.
"""
import io
import re

REPO_OK = True
SUP = "paper3/paper_ieee/supplementary/supplementary.tex"
t = io.open(SUP, encoding="utf-8").read()

pattern = re.compile(
    r"the pre-declared margin of \$0\.\s*The smallest margin at which that equivalence holds is \$0\.0333\$ "
    r"in accuracy\s*\(field \\texttt\{contrasts\.base\\_minus\\_6\.accuracy\.min\\_equivalent\\_margin\}\)\.05\$",
    re.S)
m = pattern.search(t)
if not m:
    # the wrapped form the file actually carries
    pattern = re.compile(
        r"the pre-declared margin of \$0\.\s+The smallest margin at which that equivalence holds is \$0\.0333\$[^\n]*\n[^\n]*?\.05\$",
        re.S)
    m = pattern.search(t)
assert m, "broken insertion not found (already repaired?)"

replacement = ("the pre-declared margin of $0.05$. The smallest margin at which that equivalence holds is $0.0333$ "
               "in accuracy (field \\texttt{contrasts.base\\_minus\\_6.accuracy.min\\_equivalent\\_margin}).")
t = t[:m.start()] + replacement + t[m.end():]
io.open(SUP, "w", encoding="utf-8", newline="").write(t)
print("S28 repaired")

# needles: the intact phrase must be present in the source and in the PDF
for path, needle in (("paper3/paper_ieee/audit_check.py",
                      '("S28 pre-declared margin intact 0.05", "the pre-declared margin of $0.05$")'),
                     ("paper3/paper_ieee/audit_pdf.py",
                      '("S28 pre-declared margin intact 0.05", "pre-declared margin of 0.05")')):
    s = io.open(path, encoding="utf-8").read()
    if "pre-declared margin intact" in s:
        print("needle already in", path)
        continue
    anchor = "0.0333"
    i = s.find(anchor)
    assert i >= 0, "no 0.0333 anchor in %s" % path
    j = s.find("\n", i)
    line = s[i:j]
    indent = " " * (len(line) - len(line.lstrip()))
    s = s[:j] + "\n%s%s," % (indent, needle) + s[j:]
    io.open(path, "w", encoding="utf-8", newline="").write(s)
    print("needle added to", path)