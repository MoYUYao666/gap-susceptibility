"""
缺失模态模拟 — 在训练/推理时模拟不同程度的模态缺失

三种缺失模式:
1. 图像patch随机丢弃 (Image Patch Drop): 将部分patch替换为0或噪声
2. 文本token随机mask (Text Token Mask): 将部分token替换为[MASK]
3. 完整模态缺失 (Complete Missing): 整个图像或文本模态完全不可用
"""

import torch
import torch.nn.functional as F
from typing import Dict, Optional, Tuple


# ============================================================
# 图像模态缺失
# ============================================================

def drop_image_patches(
    pixel_values: torch.Tensor,     # (B, C, H, W)
    drop_ratio: float = 0.3,
    fill_value: float = 0.0,        # 0.0 = 归一化后的均值
    patch_size: int = 16,
) -> torch.Tensor:
    """
    随机丢弃图像patch（模拟遮挡/低质量图像）

    策略：将图像分割为patch_size×patch_size的块，
         随机选择drop_ratio比例的块清零
    """
    if drop_ratio <= 0.0:
        return pixel_values

    B, C, H, W = pixel_values.shape
    device = pixel_values.device

    # 计算patch网格
    h_patches = H // patch_size
    w_patches = W // patch_size

    # 为每个样本生成独立的mask
    mask = torch.rand(B, h_patches, w_patches, device=device) > drop_ratio  # (B, Hp, Wp)
    mask = mask.float()

    # 上采样到原图分辨率
    mask = mask.unsqueeze(1)  # (B, 1, Hp, Wp)
    mask = F.interpolate(mask, size=(H, W), mode='nearest')  # (B, 1, H, W)
    mask = mask.expand(-1, C, -1, -1)  # (B, C, H, W)

    pixel_values = pixel_values * mask + fill_value * (1 - mask)
    return pixel_values


def add_image_noise(
    pixel_values: torch.Tensor,
    noise_std: float = 0.1,
) -> torch.Tensor:
    """添加高斯噪声（模拟传感器噪声）"""
    noise = torch.randn_like(pixel_values) * noise_std
    return pixel_values + noise


# ============================================================
# 文本模态缺失
# ============================================================

def mask_text_tokens(
    input_ids: torch.Tensor,        # (B, seq_len)
    attention_mask: torch.Tensor,   # (B, seq_len)
    mask_ratio: float = 0.3,
    mask_token_id: int = 0,         # [MASK] 或 [PAD] token id, CLIP通常用0
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    随机mask文本token（模拟文本噪声/不完整）

    只mask有效token（attention_mask=1的位置），保留特殊token
    """
    if mask_ratio <= 0.0:
        return input_ids, attention_mask

    device = input_ids.device
    B, L = input_ids.shape

    # 为每个样本生成mask
    rand_mask = torch.rand(B, L, device=device) < mask_ratio

    # 只mask有效token，保护 [CLS] (token 0) 和 [SEP] (token -1)
    valid_mask = attention_mask.bool()
    rand_mask = rand_mask & valid_mask
    rand_mask[:, 0] = False   # 保护 [CLS]
    rand_mask[:, -1] = False  # 保护 [SEP]

    input_ids[rand_mask] = mask_token_id

    # 注意：不修改attention_mask，让模型自行处理masked token
    return input_ids, attention_mask


def truncate_text(
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    truncate_ratio: float = 0.5,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    截断文本后半部分（模拟不完整输入）
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
# 完整模态缺失
# ============================================================

def zero_image_modality(
    pixel_values: torch.Tensor,
) -> torch.Tensor:
    """将整个图像替换为零（模拟图像完全缺失）"""
    return torch.zeros_like(pixel_values)


def zero_text_modality(
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """将整个文本替换为单个[PAD] token（模拟文本完全缺失）"""
    B, L = input_ids.shape
    input_ids = torch.zeros(B, L, dtype=input_ids.dtype, device=input_ids.device)
    attention_mask = torch.zeros(B, L, dtype=attention_mask.dtype, device=attention_mask.device)
    attention_mask[:, 0] = 1  # 保留一个token
    return input_ids, attention_mask


# ============================================================
# 统一接口
# ============================================================

class MissingModalitySimulator:
    """
    缺失模态模拟器 — 统一接口

    用法:
        sim = MissingModalitySimulator(image_drop=0.3, text_mask=0.2)
        batch = sim(batch)  # 自动处理图像和文本
    """

    def __init__(
        self,
        image_drop_ratio: float = 0.0,      # 图像patch丢弃比例
        text_mask_ratio: float = 0.0,        # 文本token mask比例
        image_noise_std: float = 0.0,        # 图像噪声标准差
        complete_missing: Optional[str] = None,  # "image", "text", "both"
        mask_token_id: int = 0,
    ):
        self.image_drop_ratio = image_drop_ratio
        self.text_mask_ratio = text_mask_ratio
        self.image_noise_std = image_noise_std
        self.complete_missing = complete_missing
        self.mask_token_id = mask_token_id

    def __call__(self, batch: Dict) -> Dict:
        """处理一个batch"""
        batch = batch.copy()  # 避免修改原始数据

        pixel_values = batch.get("pixel_values")
        input_ids = batch.get("input_ids")
        attention_mask = batch.get("attention_mask")

        # 完整模态缺失
        if self.complete_missing == "image" and pixel_values is not None:
            pixel_values = zero_image_modality(pixel_values)
        elif self.complete_missing == "text" and input_ids is not None:
            input_ids, attention_mask = zero_text_modality(input_ids, attention_mask)
        elif self.complete_missing == "both":
            if pixel_values is not None:
                pixel_values = zero_image_modality(pixel_values)
            if input_ids is not None:
                input_ids, attention_mask = zero_text_modality(input_ids, attention_mask)

        # 图像patch丢弃
        if self.image_drop_ratio > 0 and pixel_values is not None:
            pixel_values = drop_image_patches(pixel_values, self.image_drop_ratio)

        # 图像噪声
        if self.image_noise_std > 0 and pixel_values is not None:
            pixel_values = add_image_noise(pixel_values, self.image_noise_std)

        # 文本mask
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
        """从 MissingModalityConfig 创建"""
        return cls(
            image_drop_ratio=config.image_drop_ratios[0] if config.image_drop_ratios else 0.0,
            text_mask_ratio=config.text_mask_ratios[0] if config.text_mask_ratios else 0.0,
            complete_missing=None,
        )

    @classmethod
    def identity(cls) -> "MissingModalitySimulator":
        """无缺失（对照）"""
        return cls()
