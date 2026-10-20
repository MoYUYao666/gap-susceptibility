# Release notes - v2.1

This release adds the analysis layer produced for the alignment-monitoring and gap-diagnostics work, together with the
tooling that keeps the repository's numbers traceable. It contains no manuscript source, cover letter or submission
package.

## Included

- **Analysis scripts** (`tools/`)
  - checkpoint-monitoring analyses on the training split and the held-out split;
  - retrieval-task monitoring analysis;
  - evaluation-size sensitivity analysis for the order-preservation diagnostic;
  - first-order ODE fit diagnostics by adaptation family;
  - cross-file consistency report for shared numbers, page counts and archive DOIs;
  - provenance gate and manifest renderer;
  - staged submission-package build checker.

- **Result archives** (`outputs/analysis/`)
  - monitoring, retrieval, evaluation-size, ODE-diagnostic, consistency and package-check JSON files;
  - the water-tank acoustic diagnostic archive (reported as an out-of-distribution boundary, not as a replication).

- **Provenance metadata**
  - `docs/provenance_manifest.json` and `docs/PROVENANCE_MANIFEST_2026-10-20.md`: every result table/figure is mapped to
    its generating script and result archive (98 entries: 95 verified, 3 exempt with reasons).

- **Notes**
  - `docs/DEEPINFER_NOTES_2026-10-20.md`: applicability note for the DeepInfer inference framework.

## Excluded (by repository policy)

- Manuscript source and PDFs, cover letters, title pages, highlights, and any submission-package content.
- Model weights and datasets.

## Verification

- Every JSON archive under `outputs/analysis/` is produced by a script in `tools/` and the provenance gate passes.
- Submission packages were checked to compile standalone from their own `latex_source.zip` with matching page counts
  (details in `outputs/analysis/staged_package_check.json`).
