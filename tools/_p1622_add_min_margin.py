# -*- coding: utf-8 -*-
r"""Add the base-vs-r6 smallest equivalent margin (0.0333) to the S28 caption and to both audit needles.

The equivalence verdict for base vs r=6 was reported as "TOST p=0.0057, equivalent" without the margin that
makes it equivalent; the archive carries it in
`p3_vqa_full_equivalence.json :: contrasts.base_minus_6.accuracy.min_equivalent_margin`. Reporting it makes the
equivalence statement fully quantitative instead of an unexplained verdict.
"""
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

SUP = "paper3/paper_ieee/supplementary/supplementary.tex"
t = io.open(SUP, encoding="utf-8").read()
assert "0.0333" not in t, "the margin is already printed"

# find the sentence that reports the base-vs-r6 equivalence verdict and append the margin
pat = re.compile(r"(TOST p\$?=\$?0\.0057[^.]{0,80}?equivalent)", re.I)
m = pat.search(t)
if not m:
    # tolerate a differently worded verdict: anchor on the number itself
    m2 = re.search(r"0\.0057", t)
    assert m2, "no base-vs-r6 equivalence sentence found"
    # insert the margin right after the sentence containing 0.0057
    end = t.find(".", m2.end())
    insert_at = end + 1
else:
    insert_at = m.end()

addition = (" The smallest margin at which that equivalence holds is $0.0333$ in accuracy "
            "(field \\texttt{contrasts.base\\_minus\\_6.accuracy.min\\_equivalent\\_margin}).")
t = t[:insert_at] + addition + t[insert_at:]
io.open(SUP, "w", encoding="utf-8", newline="").write(t)
print("S28 caption extended with the 0.0333 margin")

# audit needles: ask for the new number in both checkers
for path, needle_style in (("paper3/paper_ieee/audit_check.py", "0.0333"),
                           ("paper3/paper_ieee/audit_pdf.py", "0.0333")):
    s = io.open(path, encoding="utf-8").read()
    if "0.0333" in s:
        print("needle already present in", path)
        continue
    anchor = "0.0057"
    i = s.find(anchor)
    if i < 0:
        print("WARNING: no 0.0057 anchor in", path)
        continue
    line_end = s.find("\n", i)
    line = s[i:line_end]
    indent = " " * (len(line) - len(line.lstrip()))
    new_line = '\n%s("base-r6 accuracy smallest equivalent margin 0.0333", "0.0333"),' % indent
    s = s[:line_end] + new_line + s[line_end:]
    io.open(path, "w", encoding="utf-8", newline="").write(s)
    print("needle added to", path)