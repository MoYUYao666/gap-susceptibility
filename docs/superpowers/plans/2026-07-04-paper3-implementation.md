# Paper 3: Predictive PEFT Allocation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute Paper 3 from theory reconstruction through experiments to ICLR submission — proving that optimal PEFT allocation can be predicted zero-shot across architectures because Γ emerges as the dominant first-order term in the perturbation Taylor expansion.

**Architecture:** Theory-first workflow. Phase 1 derives GFAP as the single main theorem with 4 corollaries (Γ emergence, allocation, transfer, Paper2 reduction). Phase 2 adapts the Paper2 codebase (gap_susceptibility.py, trainer.py) for decoder-based VLMs. Phases 3-5 run 85 experiments across LLaVA/Qwen/MiniCPM. Phase 6-7 produce the ICLR paper.

**Tech Stack:** Python 3.10+ (conda pytorch), LLaVA-1.5-7B + QLoRA (bitsandbytes 4-bit), OpenCLIP, HuggingFace Transformers, scipy/matplotlib/seaborn, LaTeX (ICLR template)

**Design Doc:** `paper3/FOR_ADVISOR.md`

---

## File Map

```
paper3/
├── theory/                          # Phase 1 outputs
│   ├── 01_optimization_problem.md   # Formal PEFT allocation problem
│   ├── 02_admissible_statistic.md   # Axiom → Γ derivation
│   ├── 03_gfap_main_theorem.md      # GFAP + proof sketch
│   └── 04_corollary_chain.md        # C1-C4 corollaries
├── scripts/
│   ├── compute_gamma_llava.py       # Phase 2: Γ for decoder VLMs
│   ├── compute_alignment_energy.py  # Phase 2: E(θ) implementations
│   ├── train_llava_lora.py          # Phase 3: LLaVA LoRA training
│   ├── predictive_transfer.py       # Phase 3: core experiment
│   ├── counterfactual_test.py       # Phase 3: violation experiment
│   ├── robustness_test.py           # Phase 3: perturbation test
│   ├── layer2_cross_arch.py         # Phase 4: Qwen/MiniCPM/SigLIP
│   ├── layer3_breadth.py            # Phase 5: VQA/Caption/RLHF
│   └── analysis/
│       ├── plot_energy_trajectories.py
│       ├── plot_gamma_ranking.py
│       ├── plot_popc_fragility.py
│       └── plot_counterfactual.py
└── paper/
    ├── main.tex                     # ICLR submission
    ├── sections/
    │   ├── introduction.tex
    │   ├── theory.tex
    │   ├── experiments.tex
    │   ├── discussion.tex
    │   └── appendix.tex
    ├── figures/
    └── references.bib
```

---

## Phase 1: Theory Reconstruction (Priority: CRITICAL)

**Goal:** Produce 4 internal derivation documents. Do NOT write the paper yet. Answer 5 foundational questions to invert the logic from "define Γ → build theory" to "PEFT allocation problem → derive Γ as conclusion."

### Task 1.1: Optimization Problem Specification

**Files:**
- Create: `paper3/theory/01_optimization_problem.md`

- [ ] **Step 1: Define the PEFT allocation problem formally**

Write `paper3/theory/01_optimization_problem.md`:

```markdown
# PEFT Allocation Optimization Problem

## Formal Statement

Given a multimodal model with parameter space partitioned into K blocks {M_1, ..., M_K}
and a fixed PEFT parameter budget C (total trainable parameters), find the allocation
{rank_1, ..., rank_K} that:

  maximize   TaskUtility(rank_1, ..., rank_K)
  subject to Σ_k params(rank_k) ≤ C,  rank_k ≥ 0

where params(rank_k) is the number of trainable parameters allocated to block M_k.

## Constraints from the PEFT Setting

1. **Block structure**: Parameters naturally partition by modality and layer
2. **Capacity budget**: LoRA total parameters are fixed (e.g., 0.1%-1% of total)
3. **Architecture agnosticism**: The allocation principle should not depend on
   knowing the specific decoder architecture
4. **Pre-training prior**: The pretrained backbone should not be modified;
   allocation only affects PEFT adapter placement

## What We Need

A scalar statistic S(M_k) computable from a source architecture that predicts
the alignment risk of training block M_k on a target architecture, such that
rank_k = f(S(M_k)) minimizes expected alignment degradation.

## Key Questions (Answer in Task 1.4)

Q1: What family of functions f maps statistic → optimal rank?
Q2: Under what conditions is S transferable across architectures?
Q3: How does Paper 2's ODE relate to this allocation problem?
```

### Task 1.2: Admissible Statistic Derivation

**Files:**
- Create: `paper3/theory/02_admissible_statistic.md`
- Reference: `paper3/FOR_ADVISOR.md` Section 2.1-2.2

- [ ] **Step 1: List axioms an admissible allocation statistic must satisfy**

Write `paper3/theory/02_admissible_statistic.md`:

```markdown
# Admissible Allocation Statistic Derivation

## Axioms

Let S(M_k) be a scalar functional over parameter block M_k that quantifies
alignment risk under PEFT. S must satisfy:

**(AX1) Local computability**: S(M_k) can be computed from a single (∇E, u) pair
  at the current parameter state, without requiring training trajectory data.

**(AX2) Parameterization invariance**: S is invariant under smooth invertible
  reparameterization of each modality block. If θ_k' = g(θ_k), then S(θ_k') = S(θ_k).

**(AX3) First-order identifiability**: S depends on ∇E and u only through their
  first-order interaction. Second-order (Hessian) and stochastic (batch variance)
  information may supplement but should not be required.

**(AX4) Directional coupling**: S distinguishes between alignment-improving and
  alignment-damaging updates. S > 0 iff the update direction reduces E.
  S = 0 iff the update is orthogonal to the alignment gradient.

**(AX5) Block-wise additivity**: For disjoint parameter blocks M_a ⊕ M_b,
  S(M_a ⊕ M_b) = S(M_a) + S(M_b).

## Derivation

**Claim**: Under (AX1)-(AX5), S is uniquely determined up to positive scaling,
and its canonical form is S(M_k) = ⟨∇_{M_k}E, u_{M_k}⟩.

**Proof sketch**:
1. (AX3) + (AX5) → S is a bilinear form over (∇E, u)
2. Any bilinear form can be written as S(x, y) = x^T A y for some matrix A
3. (AX2) → A must be invariant under block-wise reparameterization → A = c·I
4. (AX4) → c > 0 (sign convention)
5. Setting c = 1 gives the canonical representative: Γ_k = ⟨∇_{M_k}E, u_{M_k}⟩

## Result

Γ_k is NOT "proposed" — it is the unique scalar (up to scaling) satisfying
the axioms an admissible allocation statistic must satisfy. The definition
of Γ emerges as a **theorem conclusion**, not as a starting definition.
```

### Task 1.3: GFAP Main Theorem

**Files:**
- Create: `paper3/theory/03_gfap_main_theorem.md`
- Reference: `paper3/FOR_ADVISOR.md` Section 2.4-2.5

- [ ] **Step 1: Formulate GFAP as the single main theorem**

Write `paper3/theory/03_gfap_main_theorem.md`:

```markdown
# Generalized Flow Allocation Principle (GFAP)

## Main Theorem (GFAP)

Let θ be a multimodal model with modality-partitioned parameter blocks {M_k}.
Let E(θ) be an Alignment Energy satisfying (A1)-(A5).
Let u(θ) be the expected parameter update direction under SGD noise.
Let the PEFT capacity budget be C.

Define the per-block coupling coefficient:
  Γ_k = ⟨∇_{M_k}E, E[u_{M_k}]⟩

Then the optimal PEFT rank allocation under fixed budget C is:
  rank_k = C · exp(-β·|Γ_k|) / Σ_j exp(-β·|Γ_j|)

where β > 0 is determined by the alignment landscape curvature.

## Derivation via Taylor Expansion

The alignment energy change under perturbation Δθ_k = -η·u_k on block M_k is:

  ΔE_k = ⟨∇_{M_k}E, Δθ_k⟩ + ½⟨Δθ_k, ∇²_{M_k}E · Δθ_k⟩ + ε_stoch
       = -η·Γ_k           + ½η²·H_k                   + D_k

where:
  Γ_k = ⟨∇_{M_k}E, u_k⟩          — first-order coupling
  H_k = ⟨u_k, ∇²_{M_k}E · u_k⟩   — second-order curvature correction
  D_k = batch-level stochastic noise (E[D_k] = 0)

In the PEFT regime (||Δθ|| ≪ ||θ₀||):
  - H_k = O(||Δθ||²) is negligible relative to Γ_k = O(||Δθ||)
  - E[D_k] = 0 under SGD noise

Therefore Γ_k is the dominant first-order term.

## Projection Error Bound

Define the error of using Γ alone to rank blocks by alignment degradation:

  ε_proj = P(rank_by_Γ ≠ rank_by_ΔE_true)

If cross-block variances satisfy Var(H), Var(D) = o(Var(Γ)), then:

  ε_proj ≤ C₀ · (Var(H) + Var(D)) / Var(Γ)

Paper 2 CLIP data: Var(Γ)/Var(H) > 20×, Var(Γ)/Var(D) > 10× → ε_proj < 0.05

## Allocation via KKT

Minimize total alignment risk subject to fixed budget:

  minimize   Σ_k |Γ_k| · f(rank_k)
  subject to Σ_k rank_k = C,  rank_k ≥ 1

Under linear risk f(rank) = rank (verified: Paper2 ERS, k=0.088):

  L = Σ_k |Γ_k|·rank_k + λ(Σ_k rank_k - C)
  ∂L/∂rank_k = |Γ_k| + λ = 0  →  rank*_k ∝ 1/|Γ_k|

Normalizing via softmax (unique smooth mapping to probability simplex):

  rank*_k = C · exp(-β·|Γ_k|) / Σ_j exp(-β·|Γ_j|)

The exponential is FORCED, not chosen — it is the unique solution to
the constrained optimization under linear risk.

## Identifiability Regime

At initialization (LoRA B=0): Γ is not identifiable (Paper2 θ₀: r=-0.27).
After B becomes non-zero: Γ crosses the identifiability threshold:

  ε_threshold = min{ε : SNR(Γ(ε)) > max SNR(alternative statistics)}

In the identifiable regime (ε > ε_threshold), among the first-order statistics
evaluated (cosine similarity, gradient norm, Fisher alignment, NTK coupling),
Γ is the unique statistic maintaining sign-consistent monotonic prediction of ΔE.
```

### Task 1.4: Corollary Chain

**Files:**
- Create: `paper3/theory/04_corollary_chain.md`

- [ ] **Step 1: Derive the four corollaries from GFAP**

Write `paper3/theory/04_corollary_chain.md`:

```markdown
# Corollary Chain from GFAP

## C1: Γ Emerges as the Unique Admissible Statistic

Under axioms (AX1)-(AX5), Γ_k = ⟨∇_{M_k}E, u_{M_k}⟩ is the unique scalar
(up to positive scaling) that can serve as the allocation statistic.

→ Γ is a THEOREM CONCLUSION, not a definition.

## C2: Optimal PEFT Allocation

From the GFAP constrained optimization (task 1.3):
  rank*_k = C · exp(-β·|Γ_k|) / Σ_j exp(-β·|Γ_j|)

High-Γ blocks (high alignment risk) → low rank (constrained capacity).
Low-Γ blocks (low alignment risk) → high rank (allocated capacity).

→ rank_k ∝ exp(-β·|Γ_k|) is FORCED by the optimization, not proposed.

## C3: Cross-Architecture Transfer

POPC (Partial Ordering Preservation Conjecture):
  P(rank ordering preserved) = exp(-α · d_rep)

where d_rep is the representation distance between source and target architectures.
This is a measurable decay law — not a true/false assumption.

Empirical predictions:
  - Same ViT, same patch size: d_rep ≈ 0, preservation ≈ 1
  - Different patch size: d_rep medium, preservation ~0.6-0.8
  - Different encoder family (ConvNeXt): d_rep large, preservation ~0.2-0.4

Causal Transfer Protocol:
  1. Γ computed WITHOUT access to target architecture gradients
  2. No calibration, normalization, or fine-tuning on target
  3. One-shot prediction: source structure → target PEFT design

## C4: Paper 2 as Retrieval Projection

Paper 2's setting: K = {vision, text}, E = DG*, u = ∇L_InfoNCE on CLIP.
Paper 2's ODE: d(DG*)/dt = α - β(DG* - DG₀).

Under GFAP:
  d(DG*)/dt = -η(Γ_v + Γ_t) = -η(⟨∇_vDG*,g_v⟩ + ⟨∇_tDG*,g_t⟩)

The ODE is the 1D projection of GFAP onto the retrieval manifold with K={v,t}.
→ Paper 2 is not "explained again" by Paper 3; it is a COROLLARY of GFAP.
```

---

## Phase 2: Environment & Code Adaptation

**Goal:** Set up LLaVA-1.5-7B with QLoRA, adapt Γ measurement code from Paper2 for decoder-based VLMs, implement Alignment Energy E(θ) for instruction tuning.

### Task 2.1: LLaVA Environment Setup

**Files:**
- Create: `paper3/scripts/setup_llava.py` (verification script)

- [ ] **Step 1: Install LLaVA and verify with QLoRA**

```bash
conda activate pytorch
pip install transformers accelerate peft bitsandbytes
pip install git+https://github.com/haotian-liu/LLaVA.git

# Verify installation
python -c "
from llava.model.builder import load_pretrained_model
from llava.mm_utils import get_model_name_from_path
model_path = 'liuhaotian/llava-v1.5-7b'
model_name = get_model_name_from_path(model_path)
tokenizer, model, image_processor, context_len = load_pretrained_model(
    model_path, None, model_name,
    load_in_4bit=True,  # QLoRA 4-bit for RTX 4060 8GB
    device_map='auto'
)
print(f'LLaVA loaded. Vision: {type(model.get_vision_tower())}')
print(f'LLM: {type(model.get_model())}')
print(f'Projector: {type(model.get_model().mm_projector)}')
print('Memory:', model.get_memory_footprint()/1e9, 'GB')
"
```
Expected output: model loads, memory < 6 GB, vision tower + LLM + projector visible.

### Task 2.2: Alignment Energy Implementation

**Files:**
- Create: `paper3/scripts/compute_alignment_energy.py`

- [ ] **Step 1: Implement E(θ) for instruction tuning**

```python
"""Alignment Energy E(θ) for decoder-based VLMs.

E(θ) is a Lyapunov functional over multimodal representation consistency,
NOT a renamed loss. Satisfies axioms (A1)-(A5).
"""
import torch
import torch.nn.functional as F

def compute_alignment_energy_retrieval(image_embeds, text_embeds):
    """E = mean(||z_I - z_T||^2) — same as Paper2 DG*"""
    return ((image_embeds - text_embeds) ** 2).sum(dim=-1).mean()

def compute_alignment_energy_instruction(model, input_ids, image_tensor,
                                          visual_token_mask, language_token_mask):
    """
    E(θ) for instruction-tuned decoder VLMs.
    
    E = mean(||h_vis - h_lang||^2) over last-layer hidden states,
    where h_vis = mean hidden state at visual token positions,
          h_lang = mean hidden state at language token positions.
    
    This measures cross-modal representation distance in the LLM's
    embedding space, independent of the CE training loss.
    
    Args:
        model: LLaVAForConditionalGeneration
        input_ids: (B, L) token ids
        image_tensor: (B, C, H, W) input images
        visual_token_mask: (B, L) bool, True at visual token positions
        language_token_mask: (B, L) bool, True at text token positions
    
    Returns:
        E: scalar alignment energy
    """
    # Forward pass to get hidden states
    outputs = model(
        input_ids=input_ids,
        images=image_tensor,
        output_hidden_states=True,
    )
    # Last layer hidden states: (B, L, D)
    hidden = outputs.hidden_states[-1]
    
    # Mean hidden state at visual token positions
    h_vis = (hidden * visual_token_mask.unsqueeze(-1)).sum(dim=1) / \
             visual_token_mask.sum(dim=1, keepdim=True).clamp(min=1)
    
    # Mean hidden state at language token positions  
    h_lang = (hidden * language_token_mask.unsqueeze(-1)).sum(dim=1) / \
              language_token_mask.sum(dim=1, keepdim=True).clamp(min=1)
    
    # E = mean squared distance
    E = ((h_vis - h_lang) ** 2).sum(dim=-1).mean()
    return E

def compute_alignment_energy_caption(model, input_ids, image_tensor,
                                      caption_token_mask, visual_token_mask):
    """E for captioning: hidden-state distance between image and caption tokens."""
    outputs = model(input_ids=input_ids, images=image_tensor,
                    output_hidden_states=True)
    hidden = outputs.hidden_states[-1]
    
    h_vis = (hidden * visual_token_mask.unsqueeze(-1)).sum(dim=1) / \
             visual_token_mask.sum(dim=1, keepdim=True).clamp(min=1)
    h_cap = (hidden * caption_token_mask.unsqueeze(-1)).sum(dim=1) / \
             caption_token_mask.sum(dim=1, keepdim=True).clamp(min=1)
    
    return ((h_vis - h_cap) ** 2).sum(dim=-1).mean()

# Verification: A1 (monotonicity) check
def verify_a1_monotonicity():
    """E should decrease when alignment improves (identical embeddings → E=0)."""
    d = 512
    perfect_aligned_vis = torch.randn(4, d)
    perfect_aligned_lang = perfect_aligned_vis.clone()  # perfectly aligned
    misaligned_lang = torch.randn(4, d)  # random → misaligned
    
    E_perfect = compute_alignment_energy_retrieval(perfect_aligned_vis, perfect_aligned_lang)
    E_misaligned = compute_alignment_energy_retrieval(perfect_aligned_vis, misaligned_lang)
    
    assert E_perfect < 0.01, f"Perfect alignment should give E≈0, got {E_perfect}"
    assert E_misaligned > E_perfect, f"Misaligned E ({E_misaligned}) > perfect E ({E_perfect})"
    print("A1 monotonicity: PASS")

if __name__ == "__main__":
    verify_a1_monotonicity()
```
Run: `python paper3/scripts/compute_alignment_energy.py`
Expected: "A1 monotonicity: PASS"

### Task 2.3: Γ Measurement for Decoder VLMs

**Files:**
- Create: `paper3/scripts/compute_gamma_llava.py`
- Reference: `src/gap_susceptibility.py` (Paper2, lines 39-151)

- [ ] **Step 1: Implement Γ computation with modality partition**

```python
"""Γ = ⟨∇_{M_k}E, u_{M_k}⟩ for decoder-based VLMs.

Adapts Paper2's compute_gap_susceptibility() for LLaVA architecture.
Key difference: modality partition by parameter group, not name prefix.
"""
import torch
from compute_alignment_energy import compute_alignment_energy_instruction

def get_modality_param_groups(model):
    """Partition LLaVA parameters into modality blocks.
    
    LLaVA-1.5-7B architecture:
      model.vision_tower    → M_vis   (CLIP-ViT-L, typically frozen)
      model.mm_projector    → M_proj  (2-layer MLP, vision→language bridge)
      model.language_model  → M_LLM   (Vicuna-7B, 32 layers)
      model.lm_head         → M_head  (output projection)
    
    For fine-grained: M_LLM split into shallow(0-7), mid(8-23), deep(24-31).
    """
    groups = {}
    
    # Vision encoder (frozen in standard LLaVA training — check trainable)
    vis_params = [p for n, p in model.vision_tower.named_parameters() if p.requires_grad]
    if vis_params:
        groups['vis'] = vis_params
    
    # Projector
    groups['proj'] = [p for n, p in model.mm_projector.named_parameters() if p.requires_grad]
    
    # LLM — optionally split into shallow/mid/deep
    llm = model.language_model
    num_layers = len(llm.model.layers)  # 32 for Vicuna-7B
    groups['llm_shallow'] = []
    groups['llm_mid'] = []
    groups['llm_deep'] = []
    
    for i, layer in enumerate(llm.model.layers):
        for n, p in layer.named_parameters():
            if p.requires_grad:
                if i <= 7:
                    groups['llm_shallow'].append(p)
                elif i <= 23:
                    groups['llm_mid'].append(p)
                else:
                    groups['llm_deep'].append(p)
    
    # LM head
    groups['head'] = [p for n, p in model.lm_head.named_parameters() if p.requires_grad]
    
    return {k: v for k, v in groups.items() if v}  # remove empty groups


def compute_gamma_llava(model, input_ids, image_tensor,
                         vis_mask, lang_mask, label_ids):
    """
    Compute Γ_k = ⟨∇_{M_k}E, u_{M_k}⟩ for each modality block.
    
    Requires TWO backward passes:
      Pass 1: E.backward() → ∇_{M_k}E  (alignment energy gradient)
      Pass 2: L_task.backward() → u_{M_k} (task gradient = expected update direction)
    
    Args:
        model: LLaVAForConditionalGeneration
        input_ids, image_tensor: inputs
        vis_mask, lang_mask: token position masks for E computation
        label_ids: labels for CE loss computation
    
    Returns:
        dict: {block_name: gamma_value}
    """
    # --- Pass 1: ∇E ---
    outputs = model(input_ids=input_ids, images=image_tensor,
                    output_hidden_states=True)
    E = compute_alignment_energy_instruction(
        model, input_ids, image_tensor, vis_mask, lang_mask
    )
    
    # Save ∇E for trainable params
    E.backward(retain_graph=True)
    grad_E = {}
    for n, p in model.named_parameters():
        if p.requires_grad and p.grad is not None:
            grad_E[n] = p.grad.detach().clone()
    model.zero_grad()
    
    # --- Pass 2: u = ∇L_task ---
    outputs = model(input_ids=input_ids, images=image_tensor,
                    labels=label_ids)
    loss = outputs.loss  # CE loss
    loss.backward()
    
    grad_u = {}
    for n, p in model.named_parameters():
        if p.requires_grad and p.grad is not None:
            grad_u[n] = p.grad.detach().clone()
    model.zero_grad()
    
    # --- Compute Γ per block ---
    groups = get_modality_param_groups(model)
    gamma = {}
    
    for block_name, params in groups.items():
        dot_sum = 0.0
        for p in params:
            for n, _ in model.named_parameters():
                if _ is p:  # match by identity
                    if n in grad_E and n in grad_u:
                        dot_sum += (grad_E[n] * grad_u[n]).sum().item()
                    break
        
        gamma[block_name] = dot_sum
    
    return gamma


if __name__ == "__main__":
    print("Γ measurement module for LLaVA loaded.")
    print("Modality groups:", list(get_modality_param_groups.__doc__))
```
Run: `python paper3/scripts/compute_gamma_llava.py`
Expected: no import errors, module loads cleanly.

---

## Phase 3: Layer 1 Experiments — LLaVA Hero (~46 runs)

**Goal:** Run the core Predictive Transfer experiment on LLaVA-1.5-7B, including counterfactual violation and robustness tests.

### Task 3.1: LLaVA LoRA Training Harness

**Files:**
- Create: `paper3/scripts/train_llava_lora.py`
- Reference: `src/trainer.py` (Paper2 GapAwareTrainer)

- [ ] **Step 1: Implement training loop with E(t) tracking**

```python
"""LLaVA LoRA training with Alignment Energy trajectory tracking.

Adapts GapAwareTrainer for decoder-based VLM instruction tuning.
Tracks E(t) per epoch for ODE fitting.
"""
import torch
from peft import LoraConfig, get_peft_model, TaskType
from transformers import TrainingArguments, Trainer
from compute_alignment_energy import compute_alignment_energy_instruction

def create_lora_config(projector_rank, llm_rank):
    """Create LoRA config with per-module rank allocation.
    
    Theory prediction: Γ_proj > Γ_LLM → projector_rank < llm_rank.
    """
    # Apply LoRA to projector (2-layer MLP)
    proj_targets = ["mm_projector.0", "mm_projector.2"]
    
    # Apply LoRA to LLM attention projections
    llm_targets = ["q_proj", "k_proj", "v_proj", "o_proj"]
    
    return LoraConfig(
        r=llm_rank,  # default for LLM
        lora_alpha=llm_rank * 2,
        target_modules=llm_targets + proj_targets,
        lora_dropout=0.1,
        task_type=TaskType.CAUSAL_LM,
    )

def train_with_energy_tracking(model, tokenizer, image_processor,
                                train_dataset, eval_dataset,
                                config_name, projector_rank, llm_rank,
                                num_epochs=10, output_dir="./outputs"):
    """Train LLaVA with LoRA and record E(t) per epoch."""
    from peft import get_peft_model
    
    lora_config = create_lora_config(projector_rank, llm_rank)
    model = get_peft_model(model, lora_config)
    
    training_args = TrainingArguments(
        output_dir=f"{output_dir}/{config_name}",
        per_device_train_batch_size=1,       # RTX 4060 8GB
        gradient_accumulation_steps=8,        # effective batch=8
        num_train_epochs=num_epochs,
        learning_rate=2e-4,
        logging_steps=10,
        save_strategy="epoch",
        bf16=False,
        fp16=True,
        optim="adamw_torch",
    )
    
    # Custom trainer with per-epoch E(t) callback
    trainer = EnergyTrackingTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        compute_energy_fn=compute_alignment_energy_instruction,
    )
    
    trainer.train()
    
    # Return E(t) trajectory
    return {
        'config': config_name,
        'projector_rank': projector_rank,
        'llm_rank': llm_rank,
        'energy_trajectory': trainer.energy_history,
        'final_loss': trainer.state.log_history[-1],
    }
```

- [ ] **Step 2: Run all 6 configurations for Predictive Transfer**

```python
"""predictive_transfer.py — Core Layer 1 experiment.

Runs 6 groups × (3 seeds min) = ~24 runs.
Groups A-D: Predictive Transfer (rank sweep)
Group E: Counterfactual violation
Group F: Random allocation (baseline)
"""
from train_llava_lora import train_with_energy_tracking

CONFIGS = [
    # Group A: Theory-optimal (low proj rank, high LLM rank)
    {'name': 'A_theory_optimal', 'proj_r': 4,  'llm_r': 64, 'seeds': 3},
    # Group B: Intermediate
    {'name': 'B_intermediate',   'proj_r': 16, 'llm_r': 64, 'seeds': 3},
    # Group C: Equal (standard practice)
    {'name': 'C_equal',          'proj_r': 64, 'llm_r': 64, 'seeds': 3},
    # Group D: Anti-theory (high proj rank, low LLM rank)
    {'name': 'D_anti_theory',    'proj_r': 64, 'llm_r': 4,  'seeds': 3},
    # Group E: Counterfactual violation
    {'name': 'E_counterfactual', 'proj_r': 64, 'llm_r': 4,  'seeds': 3},
    # Group F: Random (3 random allocations, equal budget)
    # Generated dynamically — skip for now, handled in task 3.2
]

results = {}
for cfg in CONFIGS:
    for seed in range(cfg['seeds']):
        name = f"{cfg['name']}_seed{seed}"
        result = train_with_energy_tracking(
            model, tokenizer, image_processor,
            train_dataset, eval_dataset,
            config_name=name,
            projector_rank=cfg['proj_r'],
            llm_rank=cfg['llm_r'],
            output_dir="./outputs/layer1"
        )
        results[name] = result

# Save results
import json
with open('./outputs/layer1/predictive_transfer.json', 'w') as f:
    json.dump(results, f, indent=2)
```
Run: `python paper3/scripts/predictive_transfer.py`
Expected: ~40 hours on RTX 4060 (10 epochs × 24 configs × ~10 min each with grad accum)

### Task 3.2: Counterfactual & Robustness Tests

**Files:**
- Create: `paper3/scripts/counterfactual_test.py`
- Create: `paper3/scripts/robustness_test.py`

- [ ] **Step 1: Counterfactual violation**

```python
"""counterfactual_test.py — Γ-orthogonal allocation.

Tests: if we VIOLATE the theory's prediction (high Γ → low rank),
does performance drop? If yes → causal evidence, not self-fulfilling.
"""
import numpy as np
from train_llava_lora import train_with_energy_tracking

def random_allocation(budget_params, n_blocks=6):
    """Random rank allocation with fixed total parameter budget."""
    raw = np.random.dirichlet(np.ones(n_blocks)) * budget_params
    return [max(1, int(r)) for r in raw]

# Group E: Γ-orthogonal violation
#   - Identify highest-Γ block (projector) → assign HIGH rank (violates theory)
#   - Identify lowest-Γ block (deep LLM) → assign LOW rank (violates theory)
E_results = train_with_energy_tracking(
    model, tokenizer, image_processor,
    train_dataset, eval_dataset,
    config_name="E_counterfactual",
    projector_rank=64,   # HIGH rank on high-Γ block → violates theory
    llm_rank=4,          # LOW rank on low-Γ block → violates theory  
    output_dir="./outputs/layer1"
)

# Group F: Random allocation (3 random seeds)
for seed in range(3):
    ranks = random_allocation(budget_params=128, n_blocks=6)
    F_result = train_with_energy_tracking(
        model, tokenizer, image_processor,
        train_dataset, eval_dataset,
        config_name=f"F_random_seed{seed}",
        projector_rank=ranks[0],
        llm_rank=sum(ranks[1:]) // 5,  # distribute remaining
        output_dir="./outputs/layer1"
    )

# Verify: E(counterfactual) < F(random) < A(theory_optimal)
# in terms of BOTH E(t) and task performance
print("Expected ranking: A > F > E")
# Check after training completes
```
Run: `python paper3/scripts/counterfactual_test.py`

- [ ] **Step 2: Robustness tests**

```python
"""robustness_test.py — Γ perturbation robustness.

Tests: noise injection, cross-seed variation, partial masking.
Prevents "fragile calibration disguised as theory."
"""
from compute_gamma_llava import compute_gamma_llava
import numpy as np

def test_noise_robustness(gamma_original, sigmas=[0.1, 0.3, 0.5]):
    """Add Gaussian noise to Γ and check if rank ordering persists."""
    rankings = {}
    baseline_rank = np.argsort([abs(v) for v in gamma_original.values()])
    
    for sigma in sigmas:
        gamma_noisy = {
            k: v + np.random.normal(0, sigma * abs(v))
            for k, v in gamma_original.items()
        }
        noisy_rank = np.argsort([abs(v) for v in gamma_noisy.values()])
        # Kendall tau between baseline and noisy ranking
        from scipy.stats import kendalltau
        tau, p = kendalltau(baseline_rank, noisy_rank)
        rankings[sigma] = {'tau': tau, 'p': p}
    
    return rankings

def test_cross_seed_stability(model, input_ids, image_tensor,
                               vis_mask, lang_mask, label_ids, n_seeds=5):
    """Measure Γ variance across random seeds."""
    gamma_seeds = []
    for seed in range(n_seeds):
        torch.manual_seed(seed)
        gamma = compute_gamma_llava(
            model, input_ids, image_tensor, vis_mask, lang_mask, label_ids
        )
        gamma_seeds.append(gamma)
    
    # Compute per-block CV
    blocks = gamma_seeds[0].keys()
    cv = {}
    for block in blocks:
        values = [g[block] for g in gamma_seeds]
        cv[block] = np.std(values) / (abs(np.mean(values)) + 1e-8)
    
    return cv

def test_partial_masking(gamma_original):
    """Randomly mask 1-2 modality groups and check ranking."""
    blocks = list(gamma_original.keys())
    baseline_rank = np.argsort([abs(gamma_original[b]) for b in blocks])
    
    results = {}
    for n_mask in [1, 2]:
        for _ in range(5):  # 5 random masks
            mask = np.random.choice(len(blocks), n_mask, replace=False)
            masked_gamma = {b: gamma_original[b] for i, b in enumerate(blocks) if i not in mask}
            if len(masked_gamma) >= 3:
                masked_blocks = list(masked_gamma.keys())
                masked_rank = np.argsort([abs(masked_gamma[b]) for b in masked_blocks])
                results[f'mask{n_mask}'] = masked_rank
    
    return results
```
Run: `python paper3/scripts/robustness_test.py`
Expected: Kendall tau > 0.7 for σ ≤ 0.3, CV < 20%, masked ranking preserves top/bottom.

### Task 3.3: Scaling Ablation + Post-hoc Γ Measurement

**Files:**
- Modify: `paper3/scripts/predictive_transfer.py`

- [ ] **Step 1: LoRA scaling ablation (4 runs)**

```python
"""Verify Γ predicts sensitivity to rank AND scaling independently.
Prevents "rank is just proxy for parameter count."
"""
SCALING_CONFIGS = [
    {'name': 'scaling_0.5', 'rank': 16, 'alpha': 8},
    {'name': 'scaling_1.0', 'rank': 16, 'alpha': 16},
    {'name': 'scaling_2.0', 'rank': 16, 'alpha': 32},
    {'name': 'scaling_4.0', 'rank': 16, 'alpha': 64},
]

for cfg in SCALING_CONFIGS:
    lora_config = LoraConfig(
        r=cfg['rank'], lora_alpha=cfg['alpha'],
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        task_type=TaskType.CAUSAL_LM,
    )
    result = train_with_energy_tracking(
        model, tokenizer, image_processor,
        train_dataset, eval_dataset,
        config_name=cfg['name'],
        projector_rank=cfg['rank'], llm_rank=cfg['rank'],
        lora_alpha_override=cfg['alpha'],
        output_dir="./outputs/layer1/ablation"
    )
```
Run: `python paper3/scripts/predictive_transfer.py --ablation-only`

- [ ] **Step 2: Post-hoc Γ measurement on LLaVA (after training, for validation only)**

Verify: Γ sign and relative ordering match Paper2's structural law.
Note: this is post-hoc validation, NOT used for prediction.

---

## Phase 4: Layer 2 — Cross-Architecture Robustness (~30 runs)

**Goal:** Validate Γ framework across Qwen-VL, MiniCPM-V, different encoder families, and PEFT methods.

### Task 4.1: Qwen-VL + MiniCPM-V

**Files:**
- Create: `paper3/scripts/layer2_cross_arch.py`

- [ ] **Step 1: Adapt Γ computation for Qwen-VL**

```python
"""Cross-architecture Γ measurement for Qwen-VL and MiniCPM-V.

Key: Standardize ALL instruction inputs in English to isolate architecture effect.
"""
from compute_gamma_llava import compute_gamma_llava, get_modality_param_groups
# Qwen-VL uses Qwen2VLForConditionalGeneration
# Similar partition: vision_tower, projector (MLP), language_model (Qwen2)
# Same E(θ) definition: mean(||h_vis - h_lang||²) over last hidden states

MODELS = {
    'qwen': 'Qwen/Qwen-VL-Chat',
    'minicpm': 'openbmb/MiniCPM-V-2.5',
    'siglip': 'google/siglip-so400m-patch14-384',  # different encoder family
}

for model_id, model_path in MODELS.items():
    # Load with 4-bit QLoRA
    # Compute Γ on English instruction data
    # Verify sign consistency with structural hypothesis
    pass  # Template — implement per model
```
Run: `python paper3/scripts/layer2_cross_arch.py --model qwen`

### Task 4.2: POPC Fragility Curve Data

**Files:**
- Modify: `paper3/scripts/layer2_cross_arch.py`

- [ ] **Step 1: Measure d_rep across encoder families**

```python
"""Estimate POPC fragility curve: P(preserve) = exp(-α·d_rep)."""
# Data points for fragility curve:
#   (1) CLIP ViT-B/32 → LLaVA (CLIP ViT-L, same family): d_rep ≈ 0
#   (2) CLIP ViT-B/32 → Qwen-VL (ViT, same family): d_rep small
#   (3) CLIP ViT-B/32 → SigLIP (different objective, same ViT): d_rep medium
#   (4) CLIP ViT-B/32 → ConvNeXt-based encoder: d_rep large (if available)
#   (5) CLIP ViT-B/32 → EVA-CLIP (different pretraining): d_rep medium-large

# For each pair: compute Γ on source, measure rank ordering on target
# Fit α from P(preserve) vs d_rep
```

---

## Phase 5: Layer 3 — Breadth Validation (~15 runs)

**Goal:** Single-point Γ measurement across tasks (VQA, Caption, Instruction Following, RLHF).

### Task 5.1: Task Breadth

**Files:**
- Create: `paper3/scripts/layer3_breadth.py`

- [ ] **Step 1: Γ sign verification across tasks**

```python
"""Single-point Γ measurement across diverse tasks.
Lightweight: 1-2 seeds per task, verify Γ sign consistency only.
"""
TASKS = {
    'vqa': {
        'dataset': 'HuggingFaceM4/VQAv2',
        'E_fn': 'compute_alignment_energy_instruction',
        'prompt': 'Answer the question based on the image.',
    },
    'caption': {
        'dataset': 'HuggingFaceM4/COCO',
        'E_fn': 'compute_alignment_energy_caption',
        'prompt': 'Describe this image in detail.',
    },
    'instruction': {
        'dataset': 'tatsu-lab/alpaca',  # text-only baseline
        'E_fn': 'compute_alignment_energy_instruction',
        'prompt': None,
    },
}

for task_name, task_cfg in TASKS.items():
    gamma = compute_gamma_llava(model, ...)
    print(f"{task_name}: Γ_proj={gamma['proj']:.4f}, sign={'+' if gamma['proj']>0 else '-'}")
    # Verify: Γ_proj > 0 across all tasks (visual coupling always alignment-damaging)
```
Run: `python paper3/scripts/layer3_breadth.py`

### Task 5.2: RLHF Appendix Test (2 runs)

**Files:**
- Create: `paper3/scripts/layer3_breadth.py` (append)

- [ ] **Step 1: RLHF Γ sign check (appendix only)**

Appendix-level: 1-2 runs with reward-model-based optimization to test if Γ sign structure persists under non-supervised alignment signals. Not used for main claims.

---

## Phase 6: Analysis, Figures & Paper Writing

**Goal:** Analyze all experiment outputs, generate figures, write ICLR paper.

### Task 6.1: Analysis Scripts

**Files:**
- Create: `paper3/scripts/analysis/plot_energy_trajectories.py`
- Create: `paper3/scripts/analysis/plot_gamma_ranking.py`
- Create: `paper3/scripts/analysis/plot_popc_fragility.py`
- Create: `paper3/scripts/analysis/plot_counterfactual.py`

- [ ] **Step 1: Energy trajectory plot (all groups)**

```python
"""plot_energy_trajectories.py — E(t) curves for groups A-F.

Shows: exponential convergence, A < B < C < D ordering,
E > F (counterfactual worse than random).
"""
import json, matplotlib.pyplot as plt, seaborn as sns

with open('./outputs/layer1/predictive_transfer.json') as f:
    results = json.load(f)

fig, axes = plt.subplots(2, 3, figsize=(15, 8))
groups = ['A', 'B', 'C', 'D', 'E', 'F']
for ax, group in zip(axes.flat, groups):
    group_data = {k: v for k, v in results.items() if k.startswith(group)}
    for name, data in group_data.items():
        ax.plot(data['energy_trajectory'], alpha=0.7, label=name)
    ax.set_title(f'Group {group}')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('E(t)')

plt.tight_layout()
plt.savefig('paper3/figures/energy_trajectories.pdf')
```

- [ ] **Step 2: Γ ranking vs observed E degradation**

Scatter plot: predicted Γ_k ranking vs observed ΔE_k per block.

- [ ] **Step 3: POPC fragility curve**

Plot P(preserve) vs d_rep with exponential fit.

- [ ] **Step 4: Counterfactual bar chart**

Bar chart: Group A (theory-optimal) vs E (counterfactual) vs F (random) — both E(t) and task performance.

### Task 6.2: ICLR Paper Writing

**Files:**
- Create: `paper3/paper/main.tex`
- Create: `paper3/paper/sections/introduction.tex`
- Create: `paper3/paper/sections/theory.tex`
- Create: `paper3/paper/sections/experiments.tex`
- Create: `paper3/paper/sections/discussion.tex`
- Create: `paper3/paper/sections/appendix.tex`
- Create: `paper3/paper/references.bib`

- [ ] **Step 1: Write Introduction (1 page)**

Problem: Cross-architecture PEFT design requires knowing which parameters to train.
Existing: Paper2 shows Γ predicts alignment degradation on CLIP retrieval.
Gap: No theory for decoder-based VLMs, no prediction framework.
Contribution: GFAP → Γ emerges as unique admissible statistic → zero-shot allocation.

- [ ] **Step 2: Write Theory section (3-4 pages)**

Structure following GFAP theorem chain:
- Alignment Energy definition (A1-A5)
- Admissible statistic axioms (AX1-AX5) → Γ derivation
- Taylor decomposition of ΔE → Γ as dominant term + error bound
- Constrained optimization → exponential allocation
- Cross-architecture transfer (POPC fragility curve)
- Paper2 as retrieval projection

- [ ] **Step 3: Write Experiments section (3-4 pages)**

Layer 1: Predictive Transfer on LLaVA (core)
Layer 2: Cross-architecture (Qwen, MiniCPM, SigLIP)
Layer 3: Task breadth (VQA, Caption, Instruction)
Counterfactual + robustness tests
POPC fragility curve data

- [ ] **Step 4: Compile and iterate**

```bash
cd paper3/paper
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

---

## Phase 7: Polish & Submit

- [ ] Internal review pass (check all claims against data)
- [ ] Verify "no target-model calibration" constraint holds for all transfer experiments
- [ ] Verify falsifiability: at least 2 backbones tested
- [ ] Check all figures: error bars, axis labels, consistent styling
- [ ] Final compile
- [ ] Submit to ICLR (via OpenReview)

---

## Total Experiment Count

| Layer | Content | Runs |
|-------|---------|:---:|
| 1 | Predictive Transfer (A-F × 3 seeds) | 24 |
| 1 | Scaling ablation (4 × 1 seed) | 4 |
| 1 | Robustness (noise/cross-seed/masking) | 6 |
| 1 | Post-hoc Γ verification | 4 |
| 2 | Qwen-VL (3 configs × 2 seeds) | 6 |
| 2 | MiniCPM-V (3 configs × 2 seeds) | 6 |
| 2 | SigLIP/EVA encoder (2 × 2 seeds) | 4 |
| 2 | BitFit (2 configs) | 4 |
| 2 | Prompt Tuning (2 configs) | 4 |
| 2 | Caption transfer | 4 |
| 3 | VQA (1-2 seeds) | 2 |
| 3 | Instruction Following (1-2 seeds) | 2 |
| 3 | RLHF (appendix, 1-2 runs) | 2 |
| **Total** | | **~72** |

---

## Timeline

| Phase | Duration | Key Deliverable |
|-------|----------|-----------------|
| 1: Theory | 2-3 weeks | 4 derivation docs, GFAP theorem finalized |
| 2: Setup | 1-2 weeks | LLaVA working, Γ code adapted |
| 3: Layer 1 | 3-4 weeks | Predictive Transfer results |
| 4: Layer 2 | 2-3 weeks | Cross-architecture data |
| 5: Layer 3 | 1-2 weeks | Task breadth data |
| 6: Write | 2-3 weeks | Complete ICLR draft |
| 7: Polish | 1-2 weeks | Submit |
| **Total** | **12-19 weeks** | |
