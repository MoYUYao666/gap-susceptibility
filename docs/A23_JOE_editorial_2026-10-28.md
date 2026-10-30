# A23 (IEEE JOE) — editorial clarification round, 2026-10-28

Decision: **Returned for clarification** (editorial office, Margaret Hayden); not sent for review. Three items to fix, then
resubmit. No author response letter is required at this stage.

## Decision on the base version (important)

The Editorial Office is handling the **submitted** manuscript (64 pages, JOE number 26-0663, source archived as
`SUBMISSION/A23_JOE/A23_latex_source.zip`). The repository also held a post-submission working draft (74 pages) with
content changes prepared for a future revision round. **Sending that draft would have changed the abstract and the content
during a formatting-only round**, so the resubmission was rebuilt from the submitted source instead:

- base = `SUBMISSION/A23_JOE/A23_latex_source.zip` (13 entries, compiles to 64 pages, 0 errors);
- only the three requested formatting fixes were applied;
- **abstract unchanged** (SHA-256 of the abstract body identical before and after: `d9c0b7bd…`);
- rebuilt manuscript = **65 pages** (the caption-above change adds one page), 0 errors, 0 undefined references, and a
  standalone compile of the new source zip also gives 65 pages.

## Item 1 — table captions in IEEE style

All **24** tables (16 in `root.tex`, 8 in the five `ext_part*.tex` files) rebuilt: caption above the table body, label as
`TABLE` + Roman numeral from the IEEE class, descriptive text wrapped in `\MakeUppercase`, trailing punctuation removed.
Verified in the rebuilt PDF by text extraction (`TABLE I`, `TABLE II`, ... with the descriptive line in capitals).

## Item 2 — figure lettering at least 8 pt

All seven figures regenerated so that the smallest glyph is at least 8 pt **at the printed width**, not at the drawing
size: canvases matched to the printed widths, base font 10–11 pt, every tick label, axis label, legend entry and annotation
set explicitly. Fig. 6 had no surviving generator script; it was rebuilt from `outputs/sonar_protocol_full.json` by the new
`tools/_p1800_a23_fig6_regen.py`, so it plots exactly the numbers cited in Table II. Effective minimum sizes:

| figure | printed width | saved width | effective min |
|---|---|---|---|
| Fig. 1 | 6.01 in | 6.28 in | **9.6 pt** |
| Fig. 2 | 6.01 in | 6.34 in | **9.5 pt** |
| Fig. 3 | 4.87 in | 3.81 in | **12.8 pt** |
| Fig. 4 | 5.01 in | 3.91 in | **12.8 pt** |
| Fig. 5 | 5.44 in | 6.01 in | **9.1 pt** |
| Fig. 6 | 5.87 in | 5.84 in | **10.1 pt** |
| Fig. 7 | 6.01 in | 6.92 in | **8.9 pt** |

Scripts: `tools/clip_a2_figures.py` (figs 1–5), `tools/clip_a2_fig7.py` (fig 7), `tools/_p1800_a23_fig6_regen.py` (fig 6,
new). Fig. 7 also prints slightly wider (0.84 `\textwidth`) so its smallest glyph clears the threshold.

## Item 3 — copy of the companion manuscript

The Editorial Office asked for "a copy of the second companion manuscript currently under review at Pattern Recognition".
Attached is the companion **as it now stands**: *Protect, Don't Perturb: Cross-Modal Alignment under PEFT of
Vision-Language Models*, currently under consideration at *Machine Learning* (`3f53e518-cbe8-4c22-98e7-ece2cc2f0716`,
55 pages). The earlier, shorter Pattern-Recognition version (PR-D-26-10149, 43 pages) is kept alongside for the record.

**Status correction:** the Pattern-Recognition version is **no longer under review** there (it received a decision after
review); the submission cover letter (`paper_a2/cover_letter.tex`) was corrected, and the clarification letter
(`CoverLetter.pdf`) states the correct status.

## Package

`SUBMISSION/A23_JOE_resubmission_2026-10-28/`

- `Manuscript.pdf` 65 pages; `LaTeXSource.zip` 13 entries (`root.tex` + five `ext_part*.tex` + seven figures);
- `CoverLetter.pdf` (1 page), `Supplementary.pdf` (43 pages, frozen bundle unchanged), `Highlights.pdf`,
  `DeclarationOfInterest.docx`, `README.md`, `SHA256SUMS.txt` (7 entries);
- `companion_for_editor/` for the email only, outside the portal package and not hashed there.

The older `SUBMISSION/A23_JOE_next_revision/` folder is the 74-page post-review draft and now carries a
`NOT_FOR_THIS_ROUND.md` note so it cannot be uploaded by mistake.
