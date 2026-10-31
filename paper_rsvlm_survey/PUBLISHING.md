# Reference corpus for the RS-VLM survey (published subset)

This directory accompanies the review *Vision–Language Models for Remote Sensing: A Survey of Pretraining,
Adaptation and Evaluation* (ISPRS Journal of Photogrammetry and Remote Sensing, manuscript PHOTO-D-26-04257).

The survey states that its reference corpus was harvested from OpenAlex, de-duplicated and verified against
CrossRef/DataCite before citation. This directory is that corpus in machine-readable form.

## What is published

| path | content |
|---|---|
| `literature/raw_2026-10-27.json` | raw records per query, exactly as returned by the OpenAlex harvest |
| `literature/dedup_2026-10-27.json` | de-duplicated records (DOI or normalised title key) |
| `literature/verified_2026-10-27.json` | records with a live CrossRef/DataCite hit at title similarity >= 0.80 |
| `literature/verify_summary_2026-10-27.json` | verification counts and the threshold used |
| `literature/summary_2026-10-27.json` | per-query harvest counts |
| `literature/seeds_verified_2026-10-27.json`, `literature/seeds_verify_summary_2026-10-27.json` | seed-reference verification |
| `literature/abstracts_2026-10-27.json`, `literature/arxiv_abstracts_2026-10-27.json` | abstracts used for screening |
| `literature/number_candidates_2026-10-27.json`, `literature/arxiv_numbers_2026-10-27.json` | numeric claims proposed by a phrase search, then read by hand |
| `literature/adaptation_numbers_2026-10-28.json` | adaptation-family numbers with source locations |
| `literature/disclosure_audit_2026-10-28.json` | the hand-verified audit of eight representative papers (Figure 3 of the review) |
| `literature/fulltext_facts_2026-10-28.json`, `literature/oa_locations_2026-10-28.json`, `literature/desktop_ingest_2026-10-28.json` | the reading record behind the audit |
| `screening/core_2026-10-27.json` | the screened core set |
| `scripts/` | the figure scripts for the two synthesis figures added for the journal version |
| `PUBLISHING_MANIFEST.json` | machine-readable counts for everything above |

## What is not published, and why

- Full-text PDFs and extracted text files are not redistributed: they are publisher content and the audit records
  the numeric facts and verdicts instead of the papers.
- The manuscript sources, the frozen submission package and the journal build directory are not part of the
  published repository (publishing boundary: code and results only, no manuscripts).

## Reproducibility

`PUBLISHING_MANIFEST.json` records the record counts and file sizes; `verify_summary_2026-10-27.json` records the
verification procedure and threshold. The bibliography of the review is generated from the verified records only.
