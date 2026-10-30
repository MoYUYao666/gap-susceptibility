# MDPI submission form - copy/paste pack (Remote Sensing, Review)

Author account: hw4c24@soton.ac.uk (already logged in on the browser tab).

## Step 1 - Submission Details (file uploads)

| slot | what to upload | file |
|---|---|---|
| Manuscript Files | the LaTeX source package (zip) | `paper_rsvlm_survey/submission/LaTeXSource.zip` (680 KB) |
| Manuscript PDF (optional but recommended) | the compiled PDF | `paper_rsvlm_survey/submission/main.pdf` (26 pages) |
| Cover Letter (required) | the letter | `paper_rsvlm_survey/submission/CoverLetter.pdf` (1 page) |
| Supplementary (optional) | the reproducibility archive: corpus metadata + verification scripts + provenance table | leave empty for now (see note below) |
| Figures / Graphical abstract / Video abstract | not needed: figures are inside the source zip | - |

Note on the supplementary: putting the whole `literature/` tree (156 PDFs) online is not appropriate; if the editors ask
for the archive, supply `paper_rsvlm_survey/literature/summary_2026-10-27.json`,
`verify_summary_2026-10-27.json`, `disclosure_audit_2026-10-28.json` and `provenance.md` as a small zip (all under 1 MB).

## Step 2 - Manuscript Information

**Title:** Vision--Language Models for Remote Sensing: A Survey of Pretraining, Adaptation and Evaluation

**Article type:** Review

**Abstract (199 words):**

Remote sensing has stopped borrowing natural-image vision--language models and started building its own. This survey
reviews that transition along three axes imposed by the overhead setting: geometry (a downward view at a variable ground
sampling distance), heterogeneity (optical, multispectral and SAR sensors sharing one text embedding) and geography
(spatially autocorrelated tiles that leak across random splits). We organise the field by what its text actually is,
because that is the binding resource: metadata-derived strings, segmentation-derived descriptions, human-written captions
and instruction data differ in what they can teach and in what they can measure. On that basis we compare pretraining
recipes and adaptation families under stated budgets, and argue that the weakest link is evaluation rather than capacity;
an audit of eight representative papers finds none reporting repeated runs or dispersion. The corpus is archived with its
queries and verified mechanically: 833 de-duplicated records were harvested from OpenAlex, 826 carried DOIs, and 821 were
verified against CrossRef or DataCite with a title-similarity threshold before any of them was cited. We close with the
reporting protocol - region-disjoint splits, caption provenance, seed counts and compute budgets - that would make the
field's results comparable without new datasets.

**Keywords:** remote sensing; vision--language models; parameter-efficient adaptation; evaluation protocol; benchmarking;
multimodal retrieval

**Sections (suggested order for the journal's field):** Introduction; Foundations; Datasets; Pretraining; Adaptation;
Evaluation; Open Problems; Conclusion.

## Step 3 - Author Information

| field | value |
|---|---|
| First name | Hongrui |
| Last name | Wan |
| E-mail | hw4c24@soton.ac.uk |
| Affiliation | University of Southampton |
| Address1 | University Road, Highfield |
| Address2 | (blank) |
| Zip Code | SO17 1BJ |
| City | Southampton |
| Country/Region | **United Kingdom** |
| ORCID | 0009-0003-8649-7504 |
| Facebook / Twitter | blank |

## Step 4 - Suggest and Exclude Reviewers

Leave empty unless the editor requires suggestions; if required, propose 3 names from the reference list who are not
co-authors (for example the corresponding authors of RemoteCLIP, RS5M/GeoRSCLIP and ChangeCLIP), with institutional
e-mails taken from the papers' own first pages.

## Step 5 - Statements

| statement | answer |
|---|---|
| Originality / not published / not under consideration | **Yes** (also stated in the cover letter) |
| Preprint | **No** |
| Conflicts of interest | **None** |
| Funding | **None** ("This research received no external funding") |
| Data availability | "The reference corpus, harvest and verification scripts, numeric provenance table and disclosure audit are archived with the manuscript and are available from the author; the corpus metadata and scripts are portable and can be deposited in a repository on request." |
| AI use disclosure | "An AI assistant was used for literature retrieval, verification scripting and language editing; all sources were verified against publisher records and the author takes full responsibility for the content." |
| Ethical approval / informed consent | Not applicable |
| Author contributions | "Conceptualization, methodology, software, validation, formal analysis, investigation, data curation, writing - original draft preparation, writing - review and editing, visualization: H.W." |
