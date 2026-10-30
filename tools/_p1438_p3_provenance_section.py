# -*- coding: utf-8 -*-
"""Make the P3 provenance appendix a numbered supplement section and cite it from the main text."""
import io

supp = "paper3/paper_ieee/supplementary/supplementary.tex"
t = io.open(supp, encoding="utf-8").read()
assert "\\section*{Data and code provenance}" in t
t = t.replace("\\section*{Data and code provenance}", "\\section{Data and code provenance}", 1)
io.open(supp, "w", encoding="utf-8", newline="").write(t)
print("supp section numbered")

ac = "paper3/paper_ieee/audit_check.py"
t = io.open(ac, encoding="utf-8").read()
old = 'check("supplement: twelve S-sections", n_sections == 12, f"{n_sections} sections")'
new = 'check("supplement: thirteen S-sections", n_sections == 13, f"{n_sections} sections")'
assert t.count(old) == 1, t.count(old)
io.open(ac, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
print("audit_check updated")

main = "paper3/paper_ieee/main.tex"
t = io.open(main, encoding="utf-8").read()
sent = (" The generating script and result archive of every table and figure are listed\n"
        "in Supplementary Section~S13.\n")
anchor = "\\section*{Supplementary material}"
assert anchor in t
t = t.replace(anchor, sent + "\n" + anchor, 1)
io.open(main, "w", encoding="utf-8", newline="").write(t)
print("main data statement extended")
