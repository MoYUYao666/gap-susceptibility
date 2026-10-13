# Cross-Modal Alignment under PEFT

Understanding and predicting how parameter-efficient fine-tuning reshapes cross-modal alignment in vision-language models.

**Hongrui Wan**

---

## Papers

### Paper 1: Protect, Don't Perturb
**An Empirical Study of Cross-Modal Alignment under PEFT of Vision-Language Models**

- 116 experiments, 14 figures, 43 references
- Key finding: text-only fine-tuning overwhelmingly preserves alignment across 5 architectures
- Distribution Gap predicts retrieval ($r = -0.827$, partial $r = -0.807$)
- Visual Fragility: causal evidence via noise sensitivity, gradient contribution, effective rank
- **Submitted to Pattern Recognition** (transferred from Neurocomputing, 2026-07)

### Paper 2: Gap Susceptibility
**A Dynamical Theory of Cross-Modal Alignment under PEFT**

- 224 experiments, 5 random seeds, 2 datasets (Flickr30k, MS-COCO), 3 PEFT methods
- Introduces Gap Susceptibility $\Gamma_m = \|\nabla_m DG^*\| \cdot \cos\phi_m$
- First-order ODE $d(DG^*)/dt = \alpha - \beta(DG^*-DG_0)$ with $R^2 = 0.984 \pm 0.009$
- Effective Rank Saturation: $\|g_v\|$ flat across ranks ($k = 0.09$)
- Cross-dataset validation on MS-COCO ($R^2 = 0.973 \pm 0.018$)
- **Ready for submission**

### Paper 3: Predictive PEFT Allocation
**Gradient Structure Laws as Predictors of PEFT Design**

- 126 runs on the present protocol plus a 57-run capacity-matched allocation study; 2 architectures (LLaVA-1.5-7B, Qwen2-VL-7B)
- **Representation Theorem**: $\Gamma$ is canonical up to positive scaling **given R1-R5 and the additivity axiom R3'**. R3 alone does not imply R3' --- we prove that with a counterexample ($\|\nabla E\|^2$ is block-decomposable but not additive)
- The crossing in alignment energy on LLaVA is **bracketed** at $r \in [5,6]$, not sharp; its location belongs to the measurement protocol, and we do not claim an architecture dependence
- **Negative results we report rather than hide**: the allocation rule beats the uniform-rank baseline at one learning rate, reverses at another, and vanishes under matched training loss; it is indistinguishable from a random allocation at the same parameter budget; and AdaLoRA, swept over the same learning rates, reaches lower alignment energy than any of our arms
- Cross-architecture zero-shot Predictive Transfer
- **Submitted to Pattern Recognition Letters** (`PRLETTERS-D-26-02378`, decision: Revise)

---

## Repository Structure

```
├── paper/              # Paper 1: LaTeX + figures + submission (PR)
├── paper2/             # Paper 2: LaTeX + figures + submission
├── paper3/             # Paper 3
│   ├── paper_ieee/         ← IEEEtran version (submitted to Pattern Recognition Letters)
│   ├── scripts/            ← Experiment scripts (LLaVA, Qwen-VL)
│   ├── theory/             ← Theory derivations (Representation Theorem, GFAP)
│   └── literature_review.md ← 40+ papers
├── src/                # Shared code (trainer, lora, gap_susceptibility, dataset)
├── experiments/        # Experiment runners + data download
├── outputs/            # Results (224 runs Paper2, 126 + 57 runs Paper3)
├── flickr30k/          # Flickr30k dataset (~30GB)
├── coco/               # MS-COCO dataset (~25GB)
└── docs/               # Documentation
```

## Key Metrics

| | Paper 1 | Paper 2 | Paper 3 |
|---|:--:|:--:|:--:|
| Experiments | 116 | 224 | 126 + 57 |
| Models | CLIP, BLIP-1, SigLIP, ViT-L | CLIP, SigLIP, OpenCLIP | LLaVA-7B, Qwen2-VL-7B |
| PEFT Methods | LoRA, Adapter | LoRA, Adapter, BitFit | LoRA |
| Datasets | Flickr30k, COCO | Flickr30k, COCO | Alpaca |
| Seeds | 3-5 | 5 | 3-5 |
| Core Concept | Visual Fragility | Gap Susceptibility $\Gamma$ | Representation Theorem |
| Key Result | Text-only is optimal | ODE $R^2 > 0.97$ | Zero-shot allocation without target gradients |
| Status | → Pattern Recognition | Ready | → PRL (Revise) |

## Setup

```bash
# Paper 2 (CLIP training)
pip install torch transformers scipy

# Paper 3 (LLaVA training)  
conda create -n paper3 python=3.10
pip install torch==2.5.1 bitsandbytes transformers==4.48.3 peft datasets

# Data download (Paper2)
python experiments/download_data.py
```

---

## Hardware and environment

Every run in this repository was produced on one of two configurations, and the archived
run records state which:

| Configuration | Used for | Notes |
|---|---|---|
| Local workstation | LLaVA-1.5-7B sweeps, CLIP retrieval sweeps | **NVIDIA RTX 4060 Laptop, 8 GB**; QLoRA 4-bit; ~34 min per LLaVA run |
| Cloud | Qwen2-VL-7B sweeps | NVIDIA A800 80 GB |
| CPU only | a few Qwen2-VL-2B runs (marked per run) | bf16; initial energy differs from GPU by 0.09%, recorded per run so runs are not mixed |

Peak memory for the local runs fits in 8 GB with QLoRA 4-bit and `batch=1`. Runs are
single-GPU and sequential; no cluster is required.

## Data availability

Datasets and model releases used here are **public**: Alpaca, ShareGPT, MS-COCO, Flickr30k,
an ImageNet subset, and the HuggingFace model cards for CLIP ViT-B/32, LLaVA-1.5-7B,
Qwen2-VL-7B and Qwen2-VL-2B.

What this repository adds is **derived data**: the per-run result JSON files under
`outputs/`, the analysis scripts that compute every statistic reported in the papers, and
the training configurations. **Every number in the papers traces to a named script and a
named JSON field.** The per-run records are append-only and each carries its own
hyper-parameters, so a rewritten aggregate file cannot silently change a cited number.

A versioned snapshot of this repository is archived on Zenodo; see the badge above
(DOI minted from the `v1.0-prl-revision` release).

## Citation

If you use this code or these results, please cite the corresponding paper:

```bibtex
@article{wan2026gradient,
  title   = {Gradient Structure Laws as Predictors of {PEFT} Design:
             Zero-Shot Cross-Architecture Rank Allocation},
  author  = {Wan, Hongrui},
  journal = {Pattern Recognition Letters},
  note    = {Manuscript PRLETTERS-D-26-02378, under revision},
  year    = {2026}
}
```

## License

See `LICENSE` in this repository.
