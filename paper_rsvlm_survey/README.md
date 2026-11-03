# Survey: vision-language models for remote sensing

Target: a review paper. Venue candidate **Remote Sensing (MDPI)**, verified 2026-10-27: ISSN 2072-4292, publisher page
states "indexed within Scopus, SCIE (Web of Science), Ei Compendex, ..."; submission-to-first-decision 22 days,
acceptance-to-publication 3 days (publisher statistics page). Registered in `docs/VENUE_SCI_REGISTRY.md`.

## Non-negotiable rule for this project

**Every reference must be real, resolvable and citable before it enters a draft.** The pipeline enforces it:

1. harvest real records from a live API (`tools/_p1790_rsvlm_lit_harvest.py`, OpenAlex);
2. re-verify every DOI against CrossRef and require title similarity >= 0.80
   (`tools/_p1791_rsvlm_verify_bib.py`);
3. build `survey.bib` only from verified records - no hand-typed BibTeX, ever;
4. a failed DOI is reported by name and stays out of the manuscript until it resolves.

Current corpus state: see `literature/summary_<date>.json` and `literature/verify_summary_<date>.json`.

## Layout

```
paper_rsvlm_survey/
  README.md            this file
  outline.md           section plan and the claim each section makes
  literature/
    raw_<date>.json        every record from every query, with query provenance
    dedup_<date>.json      de-duplicated by DOI
    verified_<date>.json   per-DOI CrossRef verdict with evidence
    survey.bib             bibliography built only from verified records
    summary_<date>.json    harvest counts
    verify_summary_<date>.json  verification counts and named failures
```

## Status (2026-10-28) - SUBMITTED

**Submitted to Remote Sensing on 2026-10-28, manuscript ID `remotesensing-4692108`, status Pending review.**


Complete draft in two forms: `draft/main_draft.pdf` (28 pages, wide layout with the appendix notes) and
`submission/main.pdf` (26 pages, official MDPI class, ready to upload).

- 142 citations, all verified against CrossRef/DataCite; every cited work has a full text in `literature/fulltext/`
  (156 texts, 156 pages of archived evidence altogether many times over);
- 64 numeric claims gated against the source text (`tools/_p1797_rsvlm_number_gate.py`, 64/64);
- eight tables/figures including three that carry the argument: data resources, pretraining provenance, adaptation
  efficiency, plus a hand-verified disclosure audit of eight representative papers;
- self-overlap with the group's other manuscripts: none (8-gram check).

Remaining work: deep-reading refinement of Sections 5-6 prose (the tables are done), copy-editing pass, and the
author/affiliation metadata before any submission. The MDPI package is otherwise built and hashed.
