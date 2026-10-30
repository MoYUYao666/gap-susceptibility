# Submission tracker

One row per submitted manuscript. Statuses are as last observed from the submission systems; the source of each row is
named so a reader can re-check it. The repository's own five manuscripts were submitted from this machine; the last row
was submitted from the Mac and is recorded here only for completeness.

| # | paper | venue | manuscript ID | submitted | last update | status | source of the record |
|---|---|---|---|---|---|---|---|
| 1 | A - cross-modal alignment under PEFT (merged 1+2) | Machine Learning (Springer, ISSN 0885-6125, SCIE) | `3f53e518-cbe8-4c22-98e7-ece2cc2f0716` | 2026-10-26 | 2026-10-26 | submitted, in review | `docs/SUBMISSION_freeze_2026-10-26.json`, `HANDOFF.md` |
| 2 | A1 - PEFT adaptation-site study | Pattern Analysis and Applications (Springer, ISSN 1863-1703, SCIE) | `0a4629f0-...` (full id in `docs/A1_VENUE_DECISION.md`) | 2026-10-26 | 2026-10-26 | submitted, in review | `HANDOFF.md`, `SUBMISSION/A1_PatternAnalysisApplications/` |
| 3 | A2 (formerly referred to as A23) - PEFT gradient-flow laws | IEEE Journal of Oceanic Engineering (ISSN 0364-9059, SCIE) | `26-0663` | original submission | 2026-10-28 | returned for clarification, resubmitted with the current 74-page version | `docs/A23_JOE_editorial_2026-10-28.md`, `SUBMISSION/A2_JOE_next_revision/` |
| 4 | P3 - power-law / ODE characterisation (SigLIP protocol) | Pattern Recognition Letters (Elsevier, ISSN 0167-8655, SCIE) | `PRLETTERS-D-26-02671` | 2026-10-21 | 2026-10-23 | With Editor | `HANDOFF.md` 2026-10-23 freeze record |
| 5 | Commentary - evaluation practice | Pattern Recognition Letters (Elsevier, ISSN 0167-8655, SCIE) | `PRLETTERS-D-26-02402` | 2026-09 (PRL) | - | in review | `docs/commentary_compression_and_table.md`, `docs/AUDIT_2026-10-18_five_manuscripts.md` |
| 6 | Survey - vision-language models for remote sensing | Remote Sensing (MDPI, ISSN 2072-4292, SCIE) | `remotesensing-4692108` | 2026-10-28 06:54:45 | 2026-10-29 | **Pending editor decision** | operator dashboard 2026-10-29 (operator-reported; previous state "Pending review") |
| 7 | Review - AI and digital twin for marine machinery maintenance | Engineering Applications of Artificial Intelligence (Elsevier, ISSN 0952-1976, SCIE) | `EAAI-26-25707` | 2026-09-23 | 2026-10-25 | **With Editor** | operator dashboard, submitted from the **Mac**; not tracked in this repository's source trees |

## Notes

- Journal indexing: every venue above is SCIE (Elsevier/Springer/IEEE/MDPI subscription or hybrid routes; no APC on the
  subscription route). The A2 venue record is in `docs/VENUE_SCI_REGISTRY.md`.
- Row 7 is recorded on the operator's instruction (2026-10-28) and no repository action follows from it: it is a Mac-side
  submission whose manuscript does not live in this checkout.
- When a decision arrives, update the row's status and, for the repository's own papers, add a dated entry in
  `HANDOFF.md`.
