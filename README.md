# Code and results: remote-sensing vision–language models and parameter-efficient fine-tuning

This repository holds the **code and the derived results** behind several manuscripts on vision–language models,
remote-sensing retrieval and parameter-efficient adaptation. It deliberately contains **no manuscript sources, no PDFs,
no cover letters and no datasets or model weights**.

## Projects

| project | what is here | status of the manuscript |
|---|---|---|
| **Controlled text-provenance study (A3)** — `paper_a3/` | four public corpora, seven text sources (human captions, parsed-object descriptions, templates, metadata, human-rich, a repeated-text control and two LLM generators), frozen CLIP backbones with LoRA adapters, 338 run records, and the analysis layer that writes every reported number | under review at the ISPRS Journal of Photogrammetry and Remote Sensing |
| **Remote-sensing vision–language survey** — `paper_rsvlm_survey/` | the reference corpus (harvest, de-duplication, DOI verification, screening, hand-verified disclosure audit), the corpus trend analysis and the figure scripts used in the article | white paper submitted to IEEE Geoscience and Remote Sensing Magazine; the full review is ready |
| **Rank allocation under PEFT (P3)** — `outputs/`, `tools/`, `src/`, `exp/`, `experiments/` | per-run result records, analysis and audit scripts, training code, and the claim ledger behind the paper | under review at Pattern Recognition Letters (new submission after the earlier decision) |

## Repository structure

```
paper_a3/            A3: corpus manifests, run records, analysis, training/evaluation code
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

Archived snapshots are published as GitHub releases; the Zenodo DOI for a snapshot, where one has been registered, is
recorded on its release page. From v2.8 the published tree contains code and results only; the working planning
documents that earlier tags included are no longer part of the repository.

## License

No licence file is currently included. Until one is added, the default of "all rights reserved" applies, and reuse
should be discussed with the author.

### Release history

- **v3.0** (2026-11-03): first clean snapshot of the code and results. Earlier releases are retired.

Archived snapshots are published as GitHub releases; the Zenodo DOI for a snapshot, where one has been registered,
is recorded on its release page.
