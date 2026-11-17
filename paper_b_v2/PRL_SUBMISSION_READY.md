# Paper B v2 — Pattern Recognition Letters submission readiness

Date: 2026-11-17
Status: **prepared, not uploaded** (portal login unavailable).

## Target

- Journal: Pattern Recognition Letters
- ISSN: 0167-8655 / 1872-7344
- Publisher: Elsevier
- Indexing: SCIE (registry entry verified 2026-10-25; re-check MJL before upload)
- No manuscript ID yet. Upload note: per PRL Guide, the official authorship form must be uploaded under the item type "Cover Letter"; `CoverLetter.pdf` already merges both.

## Compliance

| item | value |
|---|---|
| Manuscript pages | **7** (PRL limit) |
| Abstract | **250 words** (limit 250) |
| References | 28 rendered |
| Highlights | 5 items, longest 69 characters (limit 85) |
| Graphical abstract | included |
| Declarations | included (PDF + DOCX) |
| Author contributions | `AuthorContributions.pdf` (CRediT) |
| Official authorship form | `AuthorshipConfirmation.pdf` (PRL mandatory form, date 2026-11-17) |
| Supplementary | `Supplementary.pdf` (2 pages; full VQA/per-run/reproducibility appendices) |
| Source | PRL `elsarticle` source, 4 zip entries |
| Fonts | embedded, no Type 3 |
| Overfull/undefined | none in PRL build |

## Package

`SUBMISSION/PaperBv2_PRL_2026-11-15/`

- `Manuscript.pdf` — 7 pages
- `Supplementary.pdf` — 2 pages
- `TitlePage.pdf`
- `CoverLetter.pdf`
- `Declarations.pdf` / `.docx`
- `Highlights.pdf` / `.docx`
- `GraphicalAbstract.pdf`
- `AuthorContributions.pdf` — CRediT statement
- `AuthorshipConfirmation.pdf` — official PRL Authorship Confirmation form (upload under item type Cover Letter)
- `CoverLetter.pdf` — 2 pages: letter + official form
- `LaTeXSource.zip`
- `README.md`
- `SHA256SUMS.txt`

## Gate

`paper_b_v2/gate_check_prl.py` → **PASS**

- 7 pages
- 28 references
- abstract 250
- package manuscript 7 pages
- source zip entries 4

Report: `paper_b_v2/results/gate_report_prl.json`

## Notes

- The 12-page expanded manuscript remains at `paper_b_v2/manuscript/main.pdf` as an internal archive; the PRL submission uses the separate 7-page `prl/main_prl.pdf`.
- No upload, no manuscript ID. Do not claim submitted.
