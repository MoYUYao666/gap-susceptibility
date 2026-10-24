# Release notes - v2.4

This release refreshes the analysis layer, the result archives and the auditing tooling. It contains code,
result archives and provenance metadata only.

## Included

- **Analysis scripts** (`tools/`)
  - exact permutation matrix over all rank pairs, with Holm correction and TOST equivalence tests;
  - run-level and seed-level bootstrap confidence intervals for the monitoring and strict-freeze arms;
  - a fine-resolution re-evaluation of the margin-quality certificate (one decade below the previous grid)
    with uncached embeddings and a corrected archive-key reproduction check;
  - an objective-isolation control for a decoder vision-language model (contrastive vs generation loss at a
    fixed model, data, budget and adaptation site);
  - reproduction-check repair and manifest corrections for the affected tables;
  - Commentary compression probe and the two-decisions placement table generator.

- **Result archives** (`outputs/analysis/`)
  - rank-separation matrix, TOST and VQA equivalence archives;
  - bootstrap archives for the monitoring and strict-freeze analyses;
  - fine-epsilon certificate archive with embedding caches;
  - decoder objective-control archives;
  - updated margin-control and decoder-confound evidence.

- **Tooling and metadata**
  - provenance metadata updated for the affected tables;
  - audit expectations updated for the new page and section counts;
  - release-notes and packaging housekeeping.

- **Verification**
  - all repository gates pass: frozen-archive hashes, provenance gate, claim ledgers, per-project audits and
    the final verification report.

## Excluded (by repository policy)

- Model weights and datasets.
