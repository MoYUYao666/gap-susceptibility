"""
Gap Susceptibility — computation module for Γ_m and β

Γ_m = ⟨∇_m DG*, g_m⟩ / ||g_m||
β   = η · ∂⟨∇DG*, ∇L⟩/∂DG*|_{DG₀}

DG* = (1/N) Σ_i ||z_i^I - z_i^T||²  (alignment energy)
"""

import torch
import torch.nn.functional as F
from typing import Dict, Tuple, Optional


def compute_dg_star(
    image_embeds: torch.Tensor,  # (N, D), L2-normalized
    text_embeds: torch.Tensor,   # (N, D), L2-normalized
) -> float:
    """
    Compute DG* = (1/N) Σ_i ||z_i^I - z_i^T||²
    Returns a Python float.
    """
    N = image_embeds.shape[0]
    sq_diffs = ((image_embeds - text_embeds) ** 2).sum(dim=-1)
    return sq_diffs.mean().item()


def compute_dg_star_tensor(
    image_embeds: torch.Tensor,
    text_embeds: torch.Tensor,
) -> torch.Tensor:
    """
    Same as compute_dg_star but returns a scalar tensor for autograd.
    """
    sq_diffs = ((image_embeds - text_embeds) ** 2).sum(dim=-1)
    return sq_diffs.mean()


def compute_gap_susceptibility(
    model,
    image_embeds: torch.Tensor,
    text_embeds: torch.Tensor,
    label_smoothing: float = 0.0,
) -> Dict[str, float]:
    """
    Compute Γ_v and Γ_t via two independent backward passes.

    Pass 1: ∇DG* w.r.t. all parameters
    Pass 2: ∇L (InfoNCE) w.r.t. all parameters

    Then Γ_m = ⟨∇_m DG*, g_m⟩ / ||g_m|| for m ∈ {v, t}

    Returns dict with:
      Gamma_v, Gamma_t, Gamma_v_ratio,
      norm_grad_DG_v, norm_grad_DG_t,
      norm_g_v, norm_g_t,
      cos_phi_v, cos_phi_t
    """
    # --- Pass 1: compute ∇DG* ---
    model.zero_grad()
    dg_star = compute_dg_star_tensor(image_embeds, text_embeds)
    dg_star.backward(retain_graph=True)

    grad_DG = {}
    for name, param in model.named_parameters():
        if param.grad is not None:
            grad_DG[name] = param.grad.clone()

    # --- Pass 2: compute ∇L (InfoNCE loss) ---
    model.zero_grad()
    logit_scale = model.logit_scale.exp()
    logits_per_image = logit_scale * image_embeds @ text_embeds.T
    logits_per_text = logits_per_image.T
    batch_size = image_embeds.shape[0]
    labels = torch.arange(batch_size, device=image_embeds.device)
    loss_i = F.cross_entropy(logits_per_image, labels, label_smoothing=label_smoothing)
    loss_t = F.cross_entropy(logits_per_text, labels, label_smoothing=label_smoothing)
    loss = (loss_i + loss_t) / 2.0
    loss.backward()

    grad_L = {}
    for name, param in model.named_parameters():
        if param.grad is not None:
            grad_L[name] = param.grad.clone()

    model.zero_grad()

    # Build set of parameter names that are actually trained (LoRA A/B matrices only)
    # This excludes logit_scale, projection heads, etc. that have requires_grad but
    # are not part of the low-rank adaptation
    trainable_names = {
        name for name, param in model.named_parameters()
        if param.requires_grad and ("lora_A" in name or "lora_B" in name)
    }
    # For full_ft, include all trainable params
    if not trainable_names:
        trainable_names = {
            name for name, param in model.named_parameters()
            if param.requires_grad
        }

    # --- Helper: accumulate per modality, ONLY for trainable params ---
    def _accumulate(modality_prefix: str) -> Dict[str, float]:
        dot_sum = 0.0
        norm_g_sq = 0.0
        norm_grad_DG_sq = 0.0
        dot_unnormalized = 0.0
        for name in grad_DG:
            if modality_prefix not in name:
                continue
            if name not in grad_L:
                continue
            if name not in trainable_names:
                continue  # skip frozen parameters
            g_dg = grad_DG[name].flatten()
            g_l = grad_L[name].flatten()
            dot_sum += (g_dg * g_l).sum().item()
            norm_g_sq += (g_l ** 2).sum().item()
            norm_grad_DG_sq += (g_dg ** 2).sum().item()
            dot_unnormalized += (g_dg * g_l).sum().item()
        norm_g = norm_g_sq ** 0.5
        norm_grad_DG = norm_grad_DG_sq ** 0.5
        denom = max(norm_grad_DG * norm_g, 1e-8)
        cos_phi = dot_unnormalized / denom
        gamma = dot_sum / max(norm_g, 1e-8)
        return {
            "Gamma": gamma,
            "norm_grad_DG": norm_grad_DG,
            "norm_g": norm_g,
            "cos_phi": cos_phi,
        }

    # HF CLIP uses "vision_model"/"text_model". OpenCLIP uses "visual."
    vis = _accumulate("vision_model")
    if vis["norm_g"] == 0 and vis["norm_grad_DG"] == 0:
        vis = _accumulate("visual.")
    txt = _accumulate("text_model")
    if txt["norm_g"] == 0 and txt["norm_grad_DG"] == 0:
        txt = _accumulate("transformer.")

    return {
        "Gamma_v": vis["Gamma"],
        "Gamma_t": txt["Gamma"],
        "Gamma_v_ratio": vis["Gamma"] / max(txt["Gamma"], 1e-8),
        "norm_grad_DG_v": vis["norm_grad_DG"],
        "norm_grad_DG_t": txt["norm_grad_DG"],
        "norm_g_v": vis["norm_g"],
        "norm_g_t": txt["norm_g"],
        "cos_phi_v": vis["cos_phi"],
        "cos_phi_t": txt["cos_phi"],
    }


def _compute_f_coupling(
    model, dataloader, device, n_batches, processor, perturbation: Optional[float]
):
    """
    Compute f(DG*) = ⟨∇_θ DG*, ∇_θ L_InfoNCE⟩.

    If perturbation is not None, adds perturbation * direction to embeddings
    before computing (to approximate f(DG₀+ε)).

    Returns (f_value, dg_star_value).
    """
    total_f = 0.0
    total_dg = 0.0
    count = 0

    for batch in dataloader:
        if count >= n_batches:
            break

        images = batch["image"].to(device)[:32]
        texts = batch["caption"][:32]

        text_inputs = processor(
            text=texts, return_tensors="pt", padding=True,
            truncation=True, max_length=77,
        )
        input_ids = text_inputs["input_ids"].to(device)
        attention_mask = text_inputs["attention_mask"].to(device)

        with torch.no_grad():
            outputs = model(
                pixel_values=images,
                input_ids=input_ids,
                attention_mask=attention_mask,
            )
            ie = F.normalize(outputs.image_embeds, p=2, dim=-1)
            te = F.normalize(outputs.text_embeds, p=2, dim=-1)

        dg_val = compute_dg_star_tensor(ie, te).item()
        total_dg += dg_val
        count += 1

    avg_dg = total_dg / max(count, 1)

    # Now compute f = ⟨∇DG*, ∇L⟩ at this DG value
    # Re-run one batch with autograd to get the inner product
    for batch in dataloader:
        images = batch["image"].to(device)[:32]
        texts = batch["caption"][:32]
        text_inputs = processor(
            text=texts, return_tensors="pt", padding=True,
            truncation=True, max_length=77,
        )
        input_ids = text_inputs["input_ids"].to(device)
        attention_mask = text_inputs["attention_mask"].to(device)

        outputs = model(
            pixel_values=images,
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        ie = F.normalize(outputs.image_embeds, p=2, dim=-1)
        te = F.normalize(outputs.text_embeds, p=2, dim=-1)

        # Apply perturbation to embeddings if requested
        if perturbation is not None:
            # Add perturbation in the direction that increases DG*
            # by scaling the difference between image and text embeddings
            diff = ie - te
            ie_pert = ie + perturbation * diff / max(diff.norm(dim=-1, keepdim=True).mean(), 1e-8)
            ie = F.normalize(ie_pert, p=2, dim=-1)

        # Compute ∇DG*
        model.zero_grad()
        dg_star_t = compute_dg_star_tensor(ie, te)
        dg_star_t.backward(retain_graph=True)

        grad_DG = {}
        for name, param in model.named_parameters():
            if param.grad is not None and param.requires_grad:
                grad_DG[name] = param.grad.detach().flatten()

        # Compute ∇L
        model.zero_grad()
        logit_scale = model.logit_scale.exp()
        logits_per_image = logit_scale * ie @ te.T
        logits_per_text = logits_per_image.T
        batch_size = ie.shape[0]
        labels = torch.arange(batch_size, device=device)
        loss_i = F.cross_entropy(logits_per_image, labels)
        loss_t = F.cross_entropy(logits_per_text, labels)
        loss = (loss_i + loss_t) / 2.0
        loss.backward()

        grad_L = {}
        for name, param in model.named_parameters():
            if param.grad is not None and param.requires_grad:
                grad_L[name] = param.grad.detach().flatten()

        model.zero_grad()

        # Only use parameters in BOTH gradient dictionaries
        # (logit_scale only appears in ∇L, not ∇DG*)
        common_names = set(grad_DG.keys()) & set(grad_L.keys())
        if common_names:
            g_dg = torch.cat([grad_DG[n] for n in common_names])
            g_l = torch.cat([grad_L[n] for n in common_names])
            f_val = (g_dg * g_l).sum().item()
            return f_val, avg_dg

        break

    return 0.0, avg_dg


def compute_beta_theoretical(
    model,
    dataloader,
    device: str = "cuda",
    n_batches: int = 5,
    learning_rate: float = 1e-4,
    eps_frac: float = 0.01,
) -> float:
    """
    Compute β = η · ∂⟨∇DG*, ∇L⟩/∂DG*|_{DG₀}

    Strategy: compute f(DG₀) and f(DG₀+ε), then:
      β ≈ η · |f(DG₀+ε) - f(DG₀)| / ε

    where f(DG*) = ⟨∇_θ DG*, ∇_θ L_InfoNCE⟩ is the gradient-flow coupling.

    ε is set as eps_frac * DG₀ (1% perturbation by default).

    Returns β as a non-negative float.
    """
    model.eval()
    from transformers import CLIPProcessor

    processor = CLIPProcessor.from_pretrained(
        "openai/clip-vit-base-patch32", local_files_only=True
    )

    # --- Compute f(DG₀) ---
    f0, dg0 = _compute_f_coupling(model, dataloader, device, n_batches, processor, None)

    # --- Compute f(DG₀ + ε) ---
    eps = eps_frac * max(dg0, 1e-8)
    f1, dg1 = _compute_f_coupling(model, dataloader, device, n_batches, processor, eps)

    f_prime = (f1 - f0) / eps
    beta = learning_rate * abs(f_prime)

    model.zero_grad()
    return beta


def estimate_alpha_from_susceptibility(
    gamma_v: float,
    gamma_t: float,
    norm_g_v: float,
    norm_g_t: float,
    learning_rate: float = 1e-4,
) -> float:
    """
    α = -η · (Γ_v · ||g_v|| + Γ_t · ||g_t||)  [Theorem 2, corrected sign]

    Γ_m > 0 → alignment-preserving modality (gradient reduces DG*)
    Γ_m < 0 → alignment-damaging modality (gradient expands DG*)

    This is the theoretical α, computable from a single
    gradient measurement without any training.
    """
    return -learning_rate * (gamma_v * norm_g_v + gamma_t * norm_g_t)
