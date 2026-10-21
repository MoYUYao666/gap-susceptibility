# Release notes - v2.2

This release updates the analysis layer, the provenance metadata and the submission-package tooling after an independent
audit pass. It contains no manuscript source, cover letter or submission-package content.

## Included

- **Analysis scripts** (`tools/`)
  - stratified evaluation-size sensitivity analysis (subset sizes 67/134/268/536/1608);
  - appendix generators for the monitoring-rule table, the protocol-probe tables and the ODE fit-diagnostics table;
  - supplementary-table compatibility fix for two-column journal classes;
  - audit-fix tooling (page-count updates, reference registration, provenance-appendix regeneration).

- **Result archives** (`outputs/analysis/`)
  - refreshed evaluation-size sweep archive;
  - final verification report covering all repository gates;
  - staged submission-package check report.

- **Packaging tooling**
  - source-zip exclusion support (stale cover-letter sources are omitted);
  - supplementary-PDF support with a README entry;
  - clean-rebuild of package directories before assembly;
  - staged build check that selects the candidate main document matching the shipped page count.

- **Provenance metadata**
  - `docs/provenance_manifest.json` and `docs/PROVENANCE_MANIFEST_2026-10-20.md` updated with the newly added tables;
  - appendix regeneration from the manifest.

- **Verification**
  - all repository gates pass in the final verification report (frozen-archive hashes, provenance gate, claim ledger,
    manuscript audits, venue-specific checks, staged package builds).

## Excluded (by repository policy)

- Manuscript source and PDFs, cover letters, title pages, highlights, and any submission-package content.
- Model weights and datasets.

Version DOI: 10.5281/zenodo.23523263
