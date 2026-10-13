# Cross-Modal Alignment under PEFT

Understanding and predicting how parameter-efficient fine-tuning reshapes cross-modal alignment in vision-language models.

**Hongrui Wan** · University of Southampton · `hw4c24@soton.ac.uk`

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

- 181 runs, 2 architectures (LLaVA-1.5-7B, Qwen2-VL-7B), 4 sample sizes
- **Representation Theorem**: $\Gamma = \langle \nabla E, u \rangle$ is the unique admissible PEFT allocation statistic
- Alignment phase transition at $r_c \in [5,6]$ on LLaVA; no transition on Qwen-VL
- Counterfactual validation: $\Gamma$-based allocation reduces uncertainty by $32\times$
- Cross-architecture zero-shot Predictive Transfer
- **Prepared for IEEE TNNLS**

---

## Repository Structure

```
├── paper/              # Paper 1: LaTeX + figures + submission (PR)
├── paper2/             # Paper 2: LaTeX + figures + submission
├── paper3/             # Paper 3
│   ├── paper_ICLR_backup/  ← ICLR format backup
│   ├── paper_ieee/         ← IEEE TNNLS version
│   ├── scripts/            ← Experiment scripts (LLaVA, Qwen-VL)
│   ├── theory/             ← Theory derivations (Representation Theorem, GFAP)
│   └── literature_review.md ← 40+ papers
├── src/                # Shared code (trainer, lora, gap_susceptibility, dataset)
├── experiments/        # Experiment runners + data download
├── outputs/            # Results (224 runs Paper2, 181 runs Paper3)
├── flickr30k/          # Flickr30k dataset (~30GB)
├── coco/               # MS-COCO dataset (~25GB)
└── docs/               # Documentation
```

## Key Metrics

| | Paper 1 | Paper 2 | Paper 3 |
|---|:--:|:--:|:--:|
| Experiments | 116 | 224 | 181 |
| Models | CLIP, BLIP-1, SigLIP, ViT-L | CLIP, SigLIP, OpenCLIP | LLaVA-7B, Qwen2-VL-7B |
| PEFT Methods | LoRA, Adapter | LoRA, Adapter, BitFit | LoRA |
| Datasets | Flickr30k, COCO | Flickr30k, COCO | Alpaca |
| Seeds | 3-5 | 5 | 3-5 |
| Core Concept | Visual Fragility | Gap Susceptibility $\Gamma$ | Representation Theorem |
| Key Result | Text-only is optimal | ODE $R^2 > 0.97$ | Phase transition $r_c \in [5,6]$ |
| Status | → Pattern Recognition | Ready | → IEEE TNNLS |

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
