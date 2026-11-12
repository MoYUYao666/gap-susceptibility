# Code and results: remote-sensing vision–language models and parameter-efficient fine-tuning

This repository holds the **code and the derived results** behind several manuscripts on vision–language models,
remote-sensing retrieval and parameter-efficient adaptation. It deliberately contains **no manuscript sources, no PDFs,
no cover letters and no datasets or model weights**.

## Projects

| project | what is here | status of the manuscript |
|---|---|---|
| **Controlled text-provenance study (A3)** — `paper_a3/` | four public corpora, seven text sources (human captions, parsed-object descriptions, templates, metadata, human-rich, a repeated-text control and two LLM generators), frozen CLIP backbones with LoRA adapters, 338 run records, and the analysis layer that writes every reported number | under review at the ISPRS Journal of Photogrammetry and Remote Sensing |
| **Remote-sensing vision–language survey** — `paper_rsvlm_survey/` | the reference corpus (harvest, de-duplication, DOI verification, screening, hand-verified disclosure audit), the corpus trend analysis and the figure scripts used in the article | white paper submitted to IEEE Geoscience and Remote Sensing Magazine; the full review is ready |
| **Modality-gap validity under PEFT (A4)** — `paper_a4/`, `outputs/a4/` | frozen 5-encoder x 6-dataset readout matrix, 136 trained PEFT runs / 408 checkpoints, 20 public-checkpoint external cells, analysis and figure scripts |
| **Zero-shot rank allocation measurement (P3 v2)** — `paper3/upgrade_v2/`, `outputs/analysis/p3_v2_*` | PACT protocol audit, nine public downstream evaluations, Qwen2-VL-2B cross-architecture check, and the r5-r6 allocation-contrast forest plot; analysis code and derived result JSONs only | manuscript candidate for **Pattern Recognition**; not submitted |

## Repository structure

```
paper3/upgrade_v2/   P3 v2: PACT audit, public-benchmark analysis, cross-architecture checks, derived JSONs
paper_a3/            A3: corpus manifests, run records, analysis, training/evaluation code
paper_a4/            A4: controlled PEFT runs, external validation, analysis/figure scripts
paper_rsvlm_survey/  Survey: reference corpus, corpus analysis, figure and build scripts
outputs/             Per-run result records for the PEFT projects (provenance for every number)
tools/               Analysis, audit, plotting and verification scripts
src/                 Shared code (trainer, LoRA, gap susceptibility, metrics, datasets)
exp/                 Supplementary experiment scripts
experiments/         Experiment runners and data download
```

## How the numbers are produced

Every number quoted in the manuscripts is written by a script from an archived JSON record. The per-run records are
append-only: each carries its own hyper-parameters, GPU, wall time and seed dispersion, so a regenerated aggregate
cannot silently change a cited number. The project-level mappings are in `paper_a3/PROVENANCE.md` and
`paper_rsvlm_survey/PUBLISHING.md`.

## Hardware and environment

| configuration | used for | notes |
|---|---|---|
| Local workstation | CLIP retrieval and PEFT sweeps, LoRA training | NVIDIA RTX 4060 Laptop, 8 GB; bf16; peak allocation below 5 GB |
| Cloud | the larger P3 sweeps | NVIDIA A800 80 GB |
| CPU only | a few small runs (marked in the run records) | recorded per run so configurations are never mixed |

## Setup

```bash
python -m venv .venv && . .venv/bin/activate      # or: conda create -n peft python=3.10
pip install -r requirements.txt
```

The A3 training and analysis entry points are in `paper_a3/scripts/`; the survey corpus tools are in
`paper_rsvlm_survey/scripts/`.

## Data availability

The datasets and model releases used here are public: the remote-sensing corpora, their annotation files and the
public CLIP checkpoints named in each project README. What this repository adds is **derived data**: the per-run result
JSONs, the analysis scripts, the frozen text corpora and the audit records.

The v3.0 snapshot is archived on Zenodo: DOI [10.5281/zenodo.23922049](https://doi.org/10.5281/zenodo.23922049).
**2026-11-13 repository update (no new release):** adds the P3 v2 analysis layer — PACT pilot, nine public downstream evaluations (Flickr30k, COCO5k, VQA-RAD, POPE, MarineLife-16K, iNaturalist, DTD, ScienceQA, MMBench), the Qwen2-VL-2B cross-architecture check, and the r5-r6 allocation-contrast summary. This is code and derived results only; it is not a new release or tag.

The v3.1 snapshot is archived under DOI [10.5281/zenodo.24125200](https://doi.org/10.5281/zenodo.24125200) and adds the November 2026 evidence round (restored COCO ODE grid, ImageNet-R new-dataset check,
full 400-class rare-species evaluation, second acoustic backbone and deployment operating points, P3 16-seed
allocation power analysis, the full-protocol SigLIP rank-4 grid, and the A4 modality-gap/PEFT evidence block:
90 controlled LoRA runs (270 checkpoints), 46 robustness runs, 20 public-checkpoint external cells, and the
spectral-bound analysis); its version DOI is [10.5281/zenodo.24125200](https://doi.org/10.5281/zenodo.24125200). From v2.8 the published tree contains code and results only; the working planning
documents that earlier tags included are no longer part of the repository.

## License

No licence file is currently included. Until one is added, the default of "all rights reserved" applies, and reuse
should be discussed with the author.

### Release history

- **v3.0** (2026-11-03): first clean snapshot of the code and results. Earlier releases are retired.
- **v3.1** (2026-11-11; DOI 10.5281/zenodo.24125200): adds the November 2026 evidence round (Paper A COCO-ODE and ImageNet-R result JSONs, A1 full rare-species, A2 second-backbone/deployment results, P3 16-seed power analysis and SigLIP rank-4 grid, and the A4 modality-gap/PEFT block: 90 controlled LoRA runs / 270 checkpoints, 46 robustness runs, 20 public-checkpoint cells and the spectral-bound analysis) plus the corresponding analysis scripts.

Archived snapshots are published as GitHub releases; the Zenodo DOI for a snapshot, where one has been registered,
is recorded on its release page.
