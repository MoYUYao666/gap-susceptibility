# P3 v2 — code and derived results

This directory contains the **analysis code and derived result JSONs** for the P3 v2 paper:

> *What Does Zero-Shot PEFT Rank Allocation Measure? Identifiability Limits, a Protocol-Aware Benchmark, and a
> Minimax Baseline*

The manuscript source, cover letter and submission package are intentionally not published here; this repository
contains the reproducible analysis layer only.

## Contents

- `analysis/pact_pilot.py` — PACT pilot on the reference-batch sweep.
- `analysis/heldout_downstream.py` — held-out caption/instruction evaluation.
- `analysis/benchmark_eval.py` — Flickr30k, COCO5k, VQA-RAD, POPE, MarineLife-16K, iNaturalist, DTD, ScienceQA and
  MMBench loaders/evaluators.
- `analysis/summarize_benchmarks.py`, `analysis/summarize_heldout.py` — paired bootstrap summaries.
- `analysis/allocation_diff.py` — r5−r6 forest-plot data and vector figure.
- `analysis/train_qwen_vqa.py`, `analysis/qwen_benchmark_eval.py` — Qwen2-VL-2B cross-architecture check.
- `figures/make_figures.py`, `figures/make_downstream.py` — figure-generation scripts.
- `PROVENANCE.md` — artifact-to-source map.
- `../../outputs/analysis/p3_pact_pilot.json` and `../../outputs/analysis/p3_v2_*.json` — derived result JSONs.

## Data

The public benchmark parquet files are not committed (size/licensing):
- ScienceQA test: `https://hf-mirror.com/datasets/derek-thomas/ScienceQA/resolve/main/data/test-00000-of-00001-f0e719df791966ff.parquet`
- MMBench English dev: `https://hf-mirror.com/datasets/lmms-lab/MMBench/resolve/main/en/dev-00000-of-00001.parquet`

Flickr30k/COCO/A4 data are from the paper's archived public benchmark sources; no raw datasets are committed. The Qwen
adapter was trained locally and is not distributed.

## Notes

- This is a measurement/audit analysis, not a state-of-the-art allocation method.
- No private manuscript or submission metadata is included.
- No new release/tag is created for this update.
