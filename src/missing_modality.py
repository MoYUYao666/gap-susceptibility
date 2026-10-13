"""
Missing modality simulation — simulate different degrees of modality missing during training/inference

Three missing modes:
1. Image Patch Drop: replace some patches with 0 or noise
2. Text Token Mask: replace some tokens with [MASK]
3. Complete Missing: the entire image or text modality is completely unavailable
"""

import torch
import torch.nn.functional as F
from typing import Dict, Optional, Tuple


# ============================================================
# Image modality missing
# ============================================================

def drop_image_patches(
    pixel_values: torch.Tensor,     # (B, C, H, W)
    drop_ratio: float = 0.3,
    fill_value: float = 0.0,        # 0.0 = mean after normalization
    patch_size: int = 16,
) -> torch.Tensor:
    """
    Randomly drop image patches (simulates occlusion / low-quality images)

    Strategy: split the image into patch_size×patch_size blocks,
         randomly select a drop_ratio fraction of blocks and zero them out
    """
    if drop_ratio <= 0.0:
        return pixel_values

    B, C, H, W = pixel_values.shape
    device = pixel_values.device

    # compute the patch grid
    h_patches = H // patch_size
    w_patches = W // patch_size

    # generate an independent mask for each sample
    mask = torch.rand(B, h_patches, w_patches, device=device) > drop_ratio  # (B, Hp, Wp)
    mask = mask.float()

    # upsample to the original image resolution
    mask = mask.unsqueeze(1)  # (B, 1, Hp, Wp)
    mask = F.interpolate(mask, size=(H, W), mode='nearest')  # (B, 1, H, W)
    mask = mask.expand(-1, C, -1, -1)  # (B, C, H, W)

    pixel_values = pixel_values * mask + fill_value * (1 - mask)
    return pixel_values


def add_image_noise(
    pixel_values: torch.Tensor,
    noise_std: float = 0.1,
) -> torch.Tensor:
    """Add Gaussian noise (simulates sensor noise)"""
    noise = torch.randn_like(pixel_values) * noise_std
    return pixel_values + noise


# ============================================================
# Text modality missing
# ============================================================

def mask_text_tokens(
    input_ids: torch.Tensor,        # (B, seq_len)
    attention_mask: torch.Tensor,   # (B, seq_len)
    mask_ratio: float = 0.3,
    mask_token_id: int = 0,         # [MASK] or [PAD] token id, CLIP usually uses 0
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Randomly mask text tokens (simulates text noise / incompleteness)

    Only masks valid tokens (positions where attention_mask=1), keeps special tokens
    """
    if mask_ratio <= 0.0:
        return input_ids, attention_mask

    device = input_ids.device
    B, L = input_ids.shape

    # generate a mask for each sample
    rand_mask = torch.rand(B, L, device=device) < mask_ratio

    # only mask valid tokens, protect [CLS] (token 0) and [SEP] (token -1)
    valid_mask = attention_mask.bool()
    rand_mask = rand_mask & valid_mask
    rand_mask[:, 0] = False   # protect [CLS]
    rand_mask[:, -1] = False  # protect [SEP]

    input_ids[rand_mask] = mask_token_id

    # note: attention_mask is not modified; let the model handle the masked tokens itself
    return input_ids, attention_mask


def truncate_text(
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    truncate_ratio: float = 0.5,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Truncate the second half of the text (simulates incomplete input)
    """
    if truncate_ratio <= 0.0:
        return input_ids, attention_mask

    B, L = input_ids.shape
    for i in range(B):
        valid_len = attention_mask[i].sum().item()
        truncate_len = int(valid_len * (1 - truncate_ratio))
        if truncate_len > 1:
            start_idx = int(valid_len) - truncate_len
            attention_mask[i, start_idx:] = 0

    return input_ids, attention_mask


# ============================================================
# Complete modality missing
# ============================================================

def zero_image_modality(
    pixel_values: torch.Tensor,
) -> torch.Tensor:
    """Replace the entire image with zeros (simulates a completely missing image)"""
    return torch.zeros_like(pixel_values)


def zero_text_modality(
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Replace the entire text with a single [PAD] token (simulates completely missing text)"""
    B, L = input_ids.shape
    input_ids = torch.zeros(B, L, dtype=input_ids.dtype, device=input_ids.device)
    attention_mask = torch.zeros(B, L, dtype=attention_mask.dtype, device=attention_mask.device)
    attention_mask[:, 0] = 1  # keep one token
    return input_ids, attention_mask


# ============================================================
# Unified interface
# ============================================================

class MissingModalitySimulator:
    """
    Missing modality simulator — unified interface

    Usage:
        sim = MissingModalitySimulator(image_drop=0.3, text_mask=0.2)
        batch = sim(batch)  # handles image and text automatically
    """

    def __init__(
        self,
        image_drop_ratio: float = 0.0,      # image patch drop ratio
        text_mask_ratio: float = 0.0,        # text token mask ratio
        image_noise_std: float = 0.0,        # image noise std
        complete_missing: Optional[str] = None,  # "image", "text", "both"
        mask_token_id: int = 0,
    ):
        self.image_drop_ratio = image_drop_ratio
        self.text_mask_ratio = text_mask_ratio
        self.image_noise_std = image_noise_std
        self.complete_missing = complete_missing
        self.mask_token_id = mask_token_id

    def __call__(self, batch: Dict) -> Dict:
        """Process one batch"""
        batch = batch.copy()  # avoid modifying the original data

        pixel_values = batch.get("pixel_values")
        input_ids = batch.get("input_ids")
        attention_mask = batch.get("attention_mask")

        # complete modality missing
        if self.complete_missing == "image" and pixel_values is not None:
            pixel_values = zero_image_modality(pixel_values)
        elif self.complete_missing == "text" and input_ids is not None:
            input_ids, attention_mask = zero_text_modality(input_ids, attention_mask)
        elif self.complete_missing == "both":
            if pixel_values is not None:
                pixel_values = zero_image_modality(pixel_values)
            if input_ids is not None:
                input_ids, attention_mask = zero_text_modality(input_ids, attention_mask)

        # image patch drop
        if self.image_drop_ratio > 0 and pixel_values is not None:
            pixel_values = drop_image_patches(pixel_values, self.image_drop_ratio)

        # image noise
        if self.image_noise_std > 0 and pixel_values is not None:
            pixel_values = add_image_noise(pixel_values, self.image_noise_std)

        # text mask
        if self.text_mask_ratio > 0 and input_ids is not None:
            input_ids, attention_mask = mask_text_tokens(
                input_ids, attention_mask, self.text_mask_ratio, self.mask_token_id
            )

        if pixel_values is not None:
            batch["pixel_values"] = pixel_values
        if input_ids is not None:
            batch["input_ids"] = input_ids
            batch["attention_mask"] = attention_mask

        return batch

    @classmethod
    def from_config(cls, config) -> "MissingModalitySimulator":
        """Create from MissingModalityConfig"""
        return cls(
            image_drop_ratio=config.image_drop_ratios[0] if config.image_drop_ratios else 0.0,
            text_mask_ratio=config.text_mask_ratios[0] if config.text_mask_ratios else 0.0,
            complete_missing=None,
        )

    @classmethod
    def identity(cls) -> "MissingModalitySimulator":
        """No missing modality (control)"""
        return cls()
