# -*- coding: utf-8 -*-
"""Fix two gaps found while updating the Data statements to the v2.3 snapshot.

1. `tools/_p1181_verify_paperA_consistency.py` still required the v1.0-era phrase
   "Sections E and G were produced after that snapshot".  The v2.3 snapshot *does*
   include the decoder per-run records (13 LLaVA + 53 Qwen JSONs are in the mirror;
   only the adapters are withheld), so the requirement is updated to the new wording
   and the v2.3 version DOI.
2. `tools/_p1576_refresh_a1_papera_packages.py` refreshed only A1's Manuscript.pdf
   (not Title Page.pdf) and never rewrote A1's abstract-word claim.
"""
import io

# --- 1. consistency gate -----------------------------------------------------
p = "tools/_p1181_verify_paperA_consistency.py"
t = io.open(p, encoding="utf-8").read()
old = '        need(t, "Sections E and G were produced after that snapshot", rel + ": data scope")'
new = ('        # v2.3 (2026-10-24) includes the decoder per-run records; only the adapters are withheld.\n'
       '        need(t, "10.5281/zenodo.23609295", rel + ": data DOI is the v2.3 snapshot")\n'
       '        need(t, "includes the decoder-model records of Appendix Sections E and G", rel + ": data scope")\n'
       '        need(t, "adapters are not redistributed", rel + ": adapters withheld")')
assert old in t, "gate pattern not found"
io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
print("gate updated")

# --- 2. A1 package refresh ---------------------------------------------------
p = "tools/_p1576_refresh_a1_papera_packages.py"
t = io.open(p, encoding="utf-8").read()
old = '        "copy": [["paper_a1/main.pdf", "Manuscript.pdf"]],'
new = ('        "copy": [["paper_a1/main.pdf", "Manuscript.pdf"],\n'
       '                 ["paper_a1/title_page.pdf", "Title Page.pdf"]],')
assert old in t, "A1 copy list not found"
t = t.replace(old, new, 1)
old2 = '        "words_re": None,\n    },\n    {\n        "name": "PaperA_NEUCOM",'
new2 = '        "words_re": r"(\\d+)\\s*words",\n    },\n    {\n        "name": "PaperA_NEUCOM",'
assert old2 in t, "A1 words_re not found"
t = t.replace(old2, new2, 1)
io.open(p, "w", encoding="utf-8", newline="").write(t)
print("package refresh script updated")