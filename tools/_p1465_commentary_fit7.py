# -*- coding: utf-8 -*-
"""Trim the Commentary back to 7 pages: shorter new sentence + compact long author lists in the bibliography."""
import io
import re

# 1. shorten the inserted sentence
md = "paper_review_prl/MANUSCRIPT.md"
t = io.open(md, encoding="utf-8").read()
old = (" The sensitivity is not limited to answer formats: when the same content is presented to a multimodal model as "
       "rendered pixels rather than as text, the measured gap depends on rendering choices such as font and resolution "
       "[sun2026reading], so the evaluation pipeline itself is part of the reported quantity.")
new = (" The measured gap can itself be an evaluation artifact: rendering choices such as font and resolution change it "
       "[sun2026reading], so the pipeline is part of the reported quantity.")
assert t.count(old) == 1
t = t.replace(old, new, 1)
io.open(md, "w", encoding="utf-8", newline="").write(t)
print("sentence shortened")

# 2. compact author lists longer than four authors
b = "tools/_build_prl_tex.py"
s = io.open(b, encoding="utf-8").read()
old2 = '        au = clean_markup(r.get("authors") or "Unknown")'
new2 = ('        au = clean_markup(r.get("authors") or "Unknown")\n'
        '        if au.count(", ") >= 4 and "et al" not in au:\n'
        '            au = ", ".join(au.split(", ")[:3]) + " et al."')
assert s.count(old2) == 1
s = s.replace(old2, new2, 1)
io.open(b, "w", encoding="utf-8", newline="").write(s)
print("bibliography author compaction added")
