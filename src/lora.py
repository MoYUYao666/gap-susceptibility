"""
Custom LoRA (Low-Rank Adaptation) implementation
Optimized for the CLIP Transformer structure, with per-layer control
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


class LoRALinear(nn.Module):
    """
    LoRA linear layer: W' = W + (α/r) * B @ A

    forward: h = Wx + (α/r) * B @ A @ x
    """

    def __init__(
        self,
        original: nn.Linear,
        rank: int = 8,
        alpha: float = 16.0,
        dropout: float = 0.0,
        layer_name: str = "",
    ):
        super().__init__()
        assert rank > 0, f"LoRA rank must be positive, got {rank}"

        self.original = original
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank  # α/r
        self.layer_name = layer_name

        # Freeze the original weights
        self.original.weight.requires_grad_(False)
        if self.original.bias is not None:
            self.original.bias.requires_grad_(False)

        in_features = original.in_features
        out_features = original.out_features

        # LoRA low-rank matrices
        # A: (in_features, rank), B: (rank, out_features)
        self.lora_A = nn.Parameter(torch.zeros(in_features, rank))
        self.lora_B = nn.Parameter(torch.zeros(rank, out_features))

        # Dropout
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

        # Initialization: A ~ Kaiming Uniform, B = 0
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)

        # Statistics bookkeeping
        self.register_buffer("_frozen", torch.tensor(True))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Original forward
        result = self.original(x)

        # LoRA increment: (α/r) * x @ A @ B
        delta = self.dropout(x) @ self.lora_A @ self.lora_B
        result = result + self.scaling * delta

        return result

    def merge_weights(self):
        """Merge the LoRA weights into the original weights (inference speedup)"""
        if self._frozen:
            delta = self.lora_A @ self.lora_B  # (in, out)
            self.original.weight.data = self.original.weight.data + self.scaling * delta.T
            self._frozen = torch.tensor(False)

    def unmerge_weights(self):
        """Restore the original weights (for switching tasks)"""
        if not self._frozen:
            delta = self.lora_A @ self.lora_B
            self.original.weight.data = self.original.weight.data - self.scaling * delta.T
            self._frozen = torch.tensor(True)

    @property
    def delta_weight(self) -> torch.Tensor:
        """Return the LoRA increment matrix: B^T @ A^T"""
        return self.lora_B.T @ self.lora_A.T  # (out, in)

    @property
    def trainable_params(self) -> int:
        """Number of trainable parameters"""
        return self.lora_A.numel() + self.lora_B.numel()

    @property
    def total_params(self) -> int:
        """Total parameter count"""
        return self.original.weight.numel() + self.trainable_params


class GapInitLoRALinear(LoRALinear):
    """
    Gap-Init LoRA variant (ref: "When Is Rank-1 Enough?", arXiv 2602.01522)

    Core idea: initialize the first rank component of LoRA_A along the modality gap direction,
    so that the gradient signal of the low-rank update reaches the gap geometry from the start.

    Effect: rank-1 + Gap-Init ≈ standard rank-8 performance (per the original paper's conclusion)
    """

    def __init__(self, *args, gap_direction: Optional[torch.Tensor] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.gap_direction = gap_direction
        self._gap_init_applied = False

    def apply_gap_init(self, gap_direction: torch.Tensor):
        """
        Initialize the first column of LoRA_A along the gap direction

        Args:
            gap_direction: (in_features,) — modality gap direction vector
        """
        if self._gap_init_applied:
            return

        self.gap_direction = gap_direction.to(self.lora_A.device)

        # Normalize the gap direction
        g = self.gap_direction / (self.gap_direction.norm() + 1e-8)

        # Initialize the first column of lora_A along the gap direction
        # lora_A: (in_features, rank)
        with torch.no_grad():
            # Keep the Kaiming initialization of the remaining columns
            # First column = gap direction × scale
            scale = math.sqrt(self.lora_A.shape[1])  # √rank
            self.lora_A[:, 0] = g[:self.lora_A.shape[0]] * scale

        self._gap_init_applied = True

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Trigger gap init automatically on the first forward pass (if gap_direction was provided)
        if not self._gap_init_applied and self.gap_direction is not None:
            self.apply_gap_init(self.gap_direction)

        return super().forward(x)


class NullLoRALinear(LoRALinear):
    """
    Null-LoRA variant: constrain the LoRA increment to the null space of the original weights

    Key constraint: W_0^T · ΔW ≈ 0
    Implemented by adding an orthogonalization penalty on the B matrix
    """

    def __init__(self, *args, null_constraint_weight: float = 0.01, **kwargs):
        super().__init__(*args, **kwargs)
        self.null_constraint_weight = null_constraint_weight

    def null_space_loss(self) -> torch.Tensor:
        """
        Compute the Frobenius norm of W_0^T · ΔW
        W_0: (out_features, in_features)
        ΔW = B^T @ A^T: (out_features, in_features)
        """
        W0 = self.original.weight  # (out, in)
        delta_W = self.delta_weight  # (out, in)

        # ||W_0^T @ ΔW||_F^2
        violation = torch.norm(W0.T @ delta_W, p='fro')
        return self.null_constraint_weight * violation ** 2


# ============================================================
# LoRA injection utilities
# ============================================================

def apply_lora_to_model(
    model: nn.Module,
    rank: int = 8,
    alpha: float = 16.0,
    dropout: float = 0.0,
    target_modules: Optional[List[str]] = None,
    apply_to_vision: bool = True,
    apply_to_text: bool = True,
    use_null_lora: bool = False,
    use_gap_init: bool = False,
) -> Tuple[nn.Module, Dict[str, LoRALinear], int]:
    """
    Inject LoRA into the Transformer layers of a CLIP model

    Args:
        model: CLIP model (HuggingFace transformers)
        rank: LoRA rank
        alpha: LoRA scaling factor
        dropout: LoRA dropout
        target_modules: list of target module names ["q_proj", "v_proj", "k_proj", "out_proj", "fc1", "fc2"]
        apply_to_vision: whether to inject into the vision encoder
        apply_to_text: whether to inject into the text encoder
        use_null_lora: whether to use the Null-LoRA variant
        use_gap_init: whether to use the Gap-Init LoRA variant

    Returns:
        model: the modified model
        lora_layers: {layer_name: LoRALinear} mapping
        total_trainable: total number of trainable parameters
    """
    if target_modules is None:
        target_modules = ["q_proj", "v_proj"]

    lora_layers = {}
    total_trainable = 0

    # Replace the linear layers in the vision encoder
    if apply_to_vision and hasattr(model, 'vision_model'):
        _inject_lora(
            model.vision_model, target_modules, rank, alpha, dropout,
            lora_layers, "vision", use_null_lora, use_gap_init
        )

    # Replace the linear layers in the text encoder
    if apply_to_text and hasattr(model, 'text_model'):
        _inject_lora(
            model.text_model, target_modules, rank, alpha, dropout,
            lora_layers, "text", use_null_lora, use_gap_init
        )

    total_trainable = sum(l.trainable_params for l in lora_layers.values())

    print(f"✅ LoRA injection done: rank={rank}, α={alpha}")
    print(f"   {len(lora_layers)} LoRA layers, {total_trainable:,} trainable parameters")
    print(f"   Vision encoder: {sum(1 for k in lora_layers if k.startswith('vision'))} layers")
    print(f"   Text encoder: {sum(1 for k in lora_layers if k.startswith('text'))} layers")

    return model, lora_layers, total_trainable


def _inject_lora(
    encoder: nn.Module,
    target_modules: List[str],
    rank: int,
    alpha: float,
    dropout: float,
    lora_layers: Dict[str, LoRALinear],
    prefix: str,
    use_null_lora: bool,
    use_gap_init: bool = False,
):
    """Recursively traverse the encoder, replacing the target linear layers"""
    if use_null_lora and use_gap_init:
        raise ValueError("cannot use Null-LoRA and Gap-Init at the same time")
    if use_gap_init:
        lora_cls = GapInitLoRALinear
    elif use_null_lora:
        lora_cls = NullLoRALinear
    else:
        lora_cls = LoRALinear

    for name, module in encoder.named_modules():
        for target in target_modules:
            if name.endswith(f".{target}") and isinstance(module, nn.Linear):
                full_name = f"{prefix}.{name}"
                lora_module = lora_cls(
                    original=module,
                    rank=rank,
                    alpha=alpha,
                    dropout=dropout,
                    layer_name=full_name,
                )
                # Replace that layer in the parent module
                parent_name, child_name = _split_name(name)
                parent = encoder.get_submodule(parent_name) if parent_name else encoder
                setattr(parent, child_name, lora_module)
                lora_layers[full_name] = lora_module


def _split_name(name: str) -> Tuple[str, str]:
    """Split 'encoder.layer.0.attention.q_proj' -> ('encoder.layer.0.attention', 'q_proj')"""
    parts = name.rsplit(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "", parts[0]


# ============================================================
# Utility functions
# ============================================================

def get_lora_params(model: nn.Module) -> List[nn.Parameter]:
    """Get all LoRA trainable parameters"""
    params = []
    for name, param in model.named_parameters():
        if 'lora_A' in name or 'lora_B' in name:
            params.append(param)
    return params


def compute_lora_sparsity(lora_layers: Dict[str, LoRALinear]) -> Dict[str, float]:
    """Compute the parameter ratio of each LoRA layer (trainable / total)"""
    result = {}
    for name, layer in lora_layers.items():
        ratio = layer.trainable_params / layer.total_params
        result[name] = ratio
    return result


def get_null_space_loss(lora_layers: Dict[str, LoRALinear]) -> torch.Tensor:
    """Get the null-space constraint loss of all Null-LoRA layers"""
    loss = torch.tensor(0.0)
    for layer in lora_layers.values():
        if isinstance(layer, NullLoRALinear):
            loss = loss + layer.null_space_loss()
    return loss


# ============================================================
# Gap-Init utilities (ref arXiv:2602.01522)
# ============================================================

@torch.no_grad()
def compute_gap_direction(
    model,
    dataloader,
    device: str = "mps",
    n_batches: int = 10,
) -> torch.Tensor:
    """
    Estimate the modality gap direction from data: g = μ_I - μ_T

    This is the core of Gap-Init: find, in CLIP's pretrained embedding space,
    the direction separating the image mean from the text mean.

    Args:
        model: CLIP model
        dataloader: data loader (provides (image, text) pairs)
        device: device
        n_batches: number of batches used for estimation

    Returns:
        gap_direction: (D,) — direction vector pointing from text to image
    """
    from transformers import CLIPProcessor

    model.eval()
    processor = CLIPProcessor.from_pretrained(
        "openai/clip-vit-base-patch32", local_files_only=True
    )

    all_image_embeds = []
    all_text_embeds = []

    for i, batch in enumerate(dataloader):
        if i >= n_batches:
            break

        images = batch["image"].to(device)
        texts = batch["caption"]

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

        all_image_embeds.append(outputs.image_embeds.cpu())
        all_text_embeds.append(outputs.text_embeds.cpu())

    image_embeds = torch.cat(all_image_embeds, dim=0)
    text_embeds = torch.cat(all_text_embeds, dim=0)

    # Normalize
    image_embeds = F.normalize(image_embeds, p=2, dim=-1)
    text_embeds = F.normalize(text_embeds, p=2, dim=-1)

    # Gap direction: image mean - text mean
    mu_I = image_embeds.mean(dim=0)
    mu_T = text_embeds.mean(dim=0)
    gap_direction = mu_I - mu_T  # (D,)

    # Normalize to a unit vector
    gap_direction = gap_direction / (gap_direction.norm() + 1e-8)

    print(f"📐 Gap direction estimated (n={len(image_embeds)} samples)")
    print(f"   ||μ_I - μ_T|| = {(mu_I - mu_T).norm().item():.4f}")
    print(f"   Gap direction norm: {gap_direction.norm().item():.4f}")

    return gap_direction


def apply_gap_init_to_layers(
    lora_layers: Dict[str, LoRALinear],
    gap_direction: torch.Tensor,
):
    """
    Apply the estimated gap direction to all GapInitLoRALinear layers

    For each layer, take the sub-vector of gap_direction matching its input dimension
    and set it as the direction of the first column of lora_A.
    """
    applied = 0
    for name, layer in lora_layers.items():
        if isinstance(layer, GapInitLoRALinear):
            # Take the part of gap_direction matching the layer's input dimension
            in_features = layer.lora_A.shape[0]
            if len(gap_direction) >= in_features:
                sub_gap = gap_direction[:in_features]
            else:
                # gap dimension too small (should not happen), skip
                continue
            layer.apply_gap_init(sub_gap)
            applied += 1

    print(f"🎯 Gap-Init applied to {applied}/{len(lora_layers)} LoRA layers")
