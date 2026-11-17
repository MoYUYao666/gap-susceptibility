# v3.2 — Paper B v2 checkpoint-selection data

Date: 2026-11-17

This release adds the derived data, analysis code, theory notes, and submission gates for the Paper B v2
manuscript on PEFT checkpoint selection.

## Added

- `paper_b_v2/` — results, analysis, experiments, theory notes, gates, and a data README.
- `outputs/paper_b/` — per-run checkpoint JSON records.
- `paper_b/` — CLIP matrix runner code used for the frozen runs.
- Root README and citation metadata updated for v3.2.

## Evidence

- 552 runs / 1656 checkpoints.
- CLIP-B/32: 324 runs; CLIP-B/16: 144; SigLIP-B/16: 36.
- TextVQA, VQAv2, ChartQA Qwen2-VL sweeps: 16 runs each.

## Excluded

- No manuscript source, PDF, cover letter, declarations, or model weights.
- No raw datasets.
- No changes to prior tags or releases; v3.1 remains frozen.
