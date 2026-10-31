# Submission checklist - Remote Sensing (MDPI), review article

Target: **Remote Sensing** (MDPI), ISSN 2072-4292, SCIE verified 2026-10-27 (publisher page). Manuscript type: `review`.
This checklist is the manual that accompanies `paper_rsvlm_survey/submission/`.

## Package contents

| file | what it is |
|---|---|
| `main.tex` | MDPI wrapper: title block, abstract, keywords, then the eight section files |
| `0*.tex` | the section sources (introduction, foundations, datasets, pretraining, adaptation, evaluation, open problems, conclusion) |
| `References.bib` | 832 verified entries, of which 105 are cited |
| `fig_corpus.pdf`, `fig_scale.pdf` | the two data figures (Times New Roman, CID TrueType) |
| `LaTeXSource.zip` | all of the above plus `Definitions/` (MDPI class), 23 entries |
| `CoverLetter.pdf` | the required cover letter (2 pages), built from `cover_letter.tex` |
| `SHA256SUMS.txt` | hash of every file in the folder |

## Journal requirements, checked

| requirement | status |
|---|---|
| abstract at most 200 words | **199** |
| keywords 3-10 | 6 |
| figures embedded and readable at 300 dpi | vector PDFs; fonts Times New Roman + STIX, CID TrueType (no Type 3) |
| references numbered and complete | 832 bib entries, all with author/title/journal/year/DOI; the 142 cited ones verified live |
| data availability statement | present (corpus, scripts, provenance archive) |
| author contributions / funding / conflicts | filled: Hongrui Wan, University of Southampton, hw4c24@soton.ac.uk, ORCID 0009-0003-8649-7504; no external funding; no competing interests |
| AI-use disclosure | present in the acknowledgments (AI assistant for retrieval, verification scripting and language editing) |
| page/format | 26 pages in the official class, US letter, MDPI margins |

## Build and verify

```powershell
cd paper_rsvlm_survey/submission
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```
Expected: 26 pages, 0 errors, 0 undefined citations/references.

## Reproducibility chain behind the numbers

1. harvest: `tools/_p1790_rsvlm_lit_harvest.py` (OpenAlex queries, archived raw/de-duplicated dumps);
2. verification: `tools/_p1791_rsvlm_verify_bib.py` (CrossRef/DataCite, title similarity >= 0.80) -> 821/826 verified;
3. seeds: `tools/_p1793_rsvlm_seed_refs.py` (11 foundational preprints, identifiers resolved live);
4. abstracts: `tools/_p1794_rsvlm_abstracts.py`; figures: `_p1795`, `_p1796`; screening: `_p1792`;
5. numeric provenance: `provenance.md` + gate `tools/_p1797_rsvlm_number_gate.py` (64/64 rows);
6. disclosure audit: `tools/_p1801_rsvlm_disclosure_audit.py` -> `literature/disclosure_audit_2026-10-28.json`;
7. full texts: 156 archived texts under `literature/fulltext/`, every cited work covered.

## Before the upload

1. ~~fill in authors, affiliations, ORCIDs, corresponding author, funding, acknowledgements~~ - done 2026-10-28;
2. confirm the current MDPI template version (the class was downloaded 2026-10-28);
3. no preprint per the operator's decision (MDPI permits posting one later);
4. after submission, archive the submission receipt in `HANDOFF.md`.
