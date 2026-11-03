# -*- coding: utf-8 -*-
r"""Record which of the 2026-10-24 consistency findings also exist in the SUBMITTED P3 package.

Verified directly against `SUBMISSION/P3_PRL_resubmission/` (2026-10-21, frozen): the LaTeXSource.zip extracted to
a temp directory, plus the text layer of the submitted Manuscript.pdf and Supplementary.pdf.
"""
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

NOTE = """
---

## Appendix added 2026-10-24 (evening): do the consistency findings exist in the SUBMITTED package?

Checked directly against `SUBMISSION/P3_PRL_resubmission/` (the 2026-10-21 submission, frozen):
the sources inside `LaTeXSource.zip` plus the text layer of `Manuscript.pdf` and `Supplementary.pdf`.

| Finding | Present in the submitted package? | Evidence |
|---|---|---|
| `discussion` r=5 mean `+34` | **no** | 0 occurrences in either the sources or the PDFs |
| environment share `48%` | **no** | 0 occurrences |
| `three-environment` / `three-stack` | **no** | 0 occurrences; the submitted text has no stack-count sentence of that form |
| S17 coupling `97.9%` | **no** | 0 occurrences (neither 97.9 nor 98.1 appears in the submitted PDFs) |
| stale `(S44)` pointer | **no** | 0 occurrences |
| `1434 training pairs` / `4302 optimizer steps` | **no** | 0 occurrences |
| 451-question VQA, exact 15-pair permutation, TOST | **no** - correctly absent | these are new evidence produced after submission (0 occurrences of 451 / 184756 / 0.071 / 1.08e-5) |
| main text pointing to `Supplementary Sections S1--S9` | **YES - one occurrence** | `LaTeXSource.zip :: main.tex:108`, and the submitted `Supplementary.pdf` actually carries **S1-S17** (17 sections) |

Interpretation: every number-level inconsistency listed in this document was introduced into the **working draft**
during the local revision work that followed the submission, or is new evidence; none of them is in the submitted
version. The single exception is the supplementary range pointer, which was correct for the *first* submission
(whose supplement ended at S9) and was not updated when the supplement grew to S17 before the resubmission. It is
a stale cross-reference only: it changes no number, table or claim, and the working draft now points at S1-S43.

The frozen package is therefore left untouched (policy: never modify a submitted artefact), and no erratum is
warranted on this basis. If a revision is invited, the working draft already carries the corrected pointer.
"""

p = "docs/P3_CHANGE_SUMMARY_2026-10-24.md"
t = io.open(p, encoding="utf-8").read()
if "do the consistency findings exist in the SUBMITTED package" not in t:
    io.open(p, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n" + NOTE)
    print("submitted-package appendix recorded")
else:
    print("already recorded")