# Gradient Structure Laws as Predictors of PEFT Design

Code and results for **zero-shot cross-architecture rank allocation** in
parameter-efficient fine-tuning of vision-language models.

Submitted to *Pattern Recognition Letters* (manuscript `PRLETTERS-D-26-02378`,
decision: revise).

---

## What this repository is

This repository holds the **code and the derived results** behind the manuscript:

- **per-run result records** — every number in the paper traces to a named script and a
  named JSON field under `outputs/`
- **analysis, audit and verification scripts** — the tools that compute the reported
  statistics and gate the manuscript, under `tools/`
- **training and experiment code** — under `src/`, `exp/` and `experiments/`

It deliberately contains **no manuscript source, no PDF, no cover letter and no
supplementary material**.

## The claim, and what we had to give up

Acting on the reviewer reports changed the paper's claims. Four of those changes are
**against** what was originally submitted, and they are recorded here rather than in a
footnote:

1. **The Representation Theorem no longer claims uniqueness from R1–R5 alone.** Block
   decomposability does not imply bilinearity. We state the missing property as an explicit
   axiom (**R3′**, cross-block additivity) and prove that it does **not** follow from the
   earlier requirements, by counterexample: `‖∇E‖²` is block-decomposable but not additive.

2. **The allocation rule's advantage does not survive our own controls.** It beats the
   uniform-rank baseline at one learning rate (5e-5: `+1478 ± 1563` vs `+5048 ± 1900`,
   `p = 0.0055`) and **reverses at another** (3e-4: `+5968` vs `+2842`). Once the arms are
   matched on training loss (0.5872 vs 0.5826) the difference vanishes, and the rule is
   **indistinguishable from a random allocation at the same parameter budget**
   (`p = 0.2057`). We have withdrawn the claim that it beats the uniform baseline.

3. **The "sharp phase transition" is a bracketed crossing.** The crossing in alignment
   energy on LLaVA is bracketed at `r ∈ [5, 6]` (permutation `p = 0.100`), not sharp, and
   its location belongs to the measurement protocol. The apparent architecture dependence
   was a **visual-token-budget artefact** and that reading is withdrawn.

4. **The 30× variance ratio is withdrawn.** 98.9% of that spread is between-rank variance,
   not an effect of the allocation.

We also implemented **AdaLoRA** at matched budget and swept both methods over the same
learning rates. It reaches lower alignment energy than any of our arms (`−1468` / `−757`),
and the paper now says so.

Full detail, including the axiom derivation and the counterexample, is in the manuscript and
its supplementary material.

## Repository structure

```
outputs/          Per-run result records (the provenance for every number)
  theory/           ODE fits, β estimates, Γ measurements
  analysis/         Aggregation, audits, cross-checks
tools/            Analysis, audit, plotting and verification scripts
  audit/            Claim and reference auditors
src/              Shared code (trainer, LoRA, gap susceptibility, metrics, datasets)
exp/              Supplementary experiment scripts
experiments/      Experiment runners and data download
```

## Hardware and environment

Every run was produced on one of three configurations, and each archived run record states
which:

| Configuration | Used for | Notes |
|---|---|---|
| Local workstation | LLaVA-1.5-7B sweeps, CLIP retrieval sweeps | NVIDIA RTX 4060 Laptop, **8 GB**; QLoRA 4-bit; ~34 min per LLaVA run |
| Cloud | Qwen2-VL-7B sweeps | NVIDIA A800 80 GB |
| CPU only | a few Qwen2-VL-2B runs (marked per run) | bf16; initial energy differs from GPU by 0.09%, recorded per run so runs are never mixed |

Peak memory for the local runs fits in 8 GB with QLoRA 4-bit and `batch=1`. Runs are
single-GPU and sequential; no cluster is required.

## Setup

```bash
# Training environment for the LLaVA / Qwen2-VL experiments
python -m venv .venv && . .venv/bin/activate      # or: conda create -n peft python=3.10
pip install -r requirements.txt
pip install torch==2.5.1 bitsandbytes transformers==4.48.3 peft datasets
```

## Data availability

The datasets and model releases used here are **public**: Alpaca, ShareGPT, MS-COCO,
Flickr30k, an ImageNet subset, and the HuggingFace model cards for CLIP ViT-B/32,
LLaVA-1.5-7B, Qwen2-VL-7B and Qwen2-VL-2B.

What this repository adds is **derived data**: the per-run result JSON files under
`outputs/`, the analysis scripts that compute every reported statistic, and the training
configurations. The per-run records are **append-only** and each carries its own
hyper-parameters, so a rewritten aggregate file cannot silently change a cited number.

A versioned snapshot of this repository is archived on Zenodo:

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23609295.svg)](https://doi.org/10.5281/zenodo.23609295)

**Latest version DOI: [10.5281/zenodo.23609295](https://doi.org/10.5281/zenodo.23609295)** — this resolves to the
`v2.3` release and is the persistent identifier to cite for the current code and results. The earlier
`v1.0-prl-revision` snapshot remains available under
[10.5281/zenodo.23341223](https://doi.org/10.5281/zenodo.23341223).

## Reproducing a reported number

Every archived record carries its own provenance. To trace a figure quoted in the paper:

```bash
# find the run records behind a statistic
grep -rl "<the statistic's field name>" outputs/ | head

# re-run the analysis that produced it
python tools/<the_named_script>.py
```

The per-run files are the source of truth; aggregate files under `outputs/analysis/` are
derived from them and are regenerated by the analysis scripts.

## License

No licence file is currently included in this repository. Until one is added, the default
of "all rights reserved" applies, and reuse should be discussed with the author. If you
need this code under a specific licence, please open an issue.
