# Release notes - v2.3

This release refreshes the analysis layer, the result archives and the auditing tooling. It contains code, result
archives and provenance metadata only.

## Included

- **Analysis scripts** (`tools/`)
  - environment-variance decomposition with a seed-level bootstrap;
  - per-layer coupling analysis for a second vision-language backbone;
  - third-family robustness controls (small Idefics3-family model) with multi-seed runs;
  - exact permutation tests for extreme-rank comparisons;
  - allocation-baseline reproductions, including a name-adapter port of an official allocator;
  - a content-audit script that cross-checks reported values against the JSON archives;
  - local environment scripts for torch 2.4/CUDA 12.1 and torch 2.6/CUDA 12.4.

- **Result archives** (`outputs/analysis/`, `paper3/scripts/outputs/experiments/`)
  - environment matrix archives for four software stacks;
  - variance-decomposition, permutation-test and per-layer coupling archives;
  - third-family multi-seed archives;
  - updated final-verification and provenance-gate reports.

- **Tooling and metadata**
  - provenance metadata extended for the newly added result entries;
  - release-notes and packaging housekeeping;
  - audit script that verifies archived values against their source JSON.

- **Verification**
  - all repository gates pass: frozen-archive hashes, provenance gate, claim ledger, per-project audits and the final
    verification report.

## Excluded (by repository policy)

- Model weights and datasets.

Version DOI: 10.5281/zenodo.23609295
