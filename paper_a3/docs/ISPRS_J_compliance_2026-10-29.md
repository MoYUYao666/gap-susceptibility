# ISPRS J submission compliance (guide backed up 2026-10-29)

Source: `docs/ISPRS_J_guide_for_authors_2026-10-29.pdf` (18 pages, sha256
`39c9dd950720482466da8f27e974020c1af8d4498733a4e405bc747a35edfcaf`), read in full. The guide was retrieved through the
journal's "Guide for authors" link; its embedded hyperlinks were used to fetch the official templates rather than
reconstructing them.

| guide requirement | where stated | our package | status |
|---|---|---|---|
| types of paper: Papers / Review / Perspective / Comments | guide §Types of paper | research paper (controlled experiments), not a review or perspective | ok |
| abstract: factual, self-contained, no references | §Abstract | 221 words, no citations, corpus names glossed | ok |
| keywords: at most 6, American spelling | §Keywords | 5 keywords | ok |
| highlights / graphical abstract files where applicable | §Submission checklist | `Highlights.pdf` (5 bullets, all <= 85 characters) and `GraphicalAbstract.pdf` (13.3 x 5.3 cm, Times New Roman, CID TrueType) | ok (graphical abstract optional but supplied) |
| declaration of competing interest: journal template, **.docx, not converted** | §Declaration of competing interest | `DeclarationOfCompetingInterest.docx`, filled from the journal's template (only the "no known competing interests" option kept) | ok |
| declaration of generative AI: dedicated section **before the references** | §Declaration of generative AI in scientific writing | section added in `08_declarations.tex` with the exact title and the required statement form | ok |
| CRediT author contributions | §Author contributions | CRediT statement added (single author, all applicable roles) | ok |
| funding statement | §Formatting of funding sources | recommended no-funding sentence added | ok |
| data statement | §Data statement | data availability section added (corpora, run records, scripts, manifests) | ok |
| sections numbered 1, 1.1, ...; headings on separate lines | §Sections | numbered sections and subsections, headings on their own lines | ok |
| figures: captions below, vector or >=300 dpi, fonts embedded | §Artwork, §Figure captions | two vector PDF figures, Times New Roman + STIX, CID TrueType | ok |
| tables: captions above, no vertical rules, minimal shading | §Tables | captions above, horizontal rules only | ok |
| references: consistent style, DOI encouraged; no strict format at submission | §References | numbered Elsevier-style list, 26 entries, all with DOI | ok |
| LaTeX: elsarticle recommended | §LaTeX | manuscript built with `elsarticle` | ok |
| single-anonymized peer review | §Peer review | no anonymisation needed | n/a |
| Article Transfer Service | §Article Transfer Service | automatic offer if editor suggests another journal; no action needed at submission | noted |
| submission as single PDF allowed at first submission ("Your Paper Your Way") | §New submissions | PDF plus LaTeX source zip both provided | ok |
| declaration that work is not published / not under consideration | §Submission declaration | stated in the cover letter | ok |
| language: consistent British or American English | §Language | predominantly British spelling in prose; CRediT role names follow the official American spelling of the taxonomy | minor note |
| permission for copyrighted material | §Submission checklist | no third-party figures; only numbers from cited papers | ok |

## Files that must be uploaded (order suggested by the submission checklist)

1. `Manuscript.pdf` (21 pages) or the LaTeX source zip (both provided; the PDF is the refereeing file).
2. `LaTeXSource.zip` (23 entries: main.tex, nine section files, generated tables, `References.bib`, two number files, figures).
3. `CoverLetter.pdf`.
4. `DeclarationOfCompetingInterest.docx` - **must stay .docx**.
5. `Highlights.pdf`.
6. `GraphicalAbstract.pdf` (optional).
7. Data statement: present in the manuscript; no separate file required.

## Not fixed here

- ORCID is not requested by the guide and is not in the manuscript; it can be entered in the submission system.
- Repository DOI for the corpora will be registered upon acceptance (data statement says so).
