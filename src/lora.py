"""
自定义 LoRA (Low-Rank Adaptation) 实现
针对 CLIP 的 Transformer 结构优化，支持逐层控制
"""

import os
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


class LoRALinear(nn.Module):
    """
    LoRA 线性层: W' = W + (α/r) * B @ A

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

        # 冻结原始权重
        self.original.weight.requires_grad_(False)
        if self.original.bias is not None:
            self.original.bias.requires_grad_(False)

        in_features = original.in_features
        out_features = original.out_features

        # LoRA 低秩矩阵
        # A: (in_features, rank), B: (rank, out_features)
        self.lora_A = nn.Parameter(torch.zeros(in_features, rank))
        self.lora_B = nn.Parameter(torch.zeros(rank, out_features))

        # Dropout
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

        # 初始化: A ~ Kaiming Uniform, B = 0
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)

        # 统计记录
        self.register_buffer("_frozen", torch.tensor(True))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # 原始前向
        result = self.original(x)

        # LoRA 增量: (α/r) * x @ A @ B
        delta = self.dropout(x) @ self.lora_A @ self.lora_B
        result = result + self.scaling * delta

        return result

    def merge_weights(self):
        """将 LoRA 权重合并到原始权重（推理加速）"""
        if self._frozen:
            delta = self.lora_A @ self.lora_B  # (in, out)
            self.original.weight.data = self.original.weight.data + self.scaling * delta.T
            self._frozen = torch.tensor(False)

    def unmerge_weights(self):
        """恢复原始权重（用于切换任务）"""
        if not self._frozen:
            delta = self.lora_A @ self.lora_B
            self.original.weight.data = self.original.weight.data - self.scaling * delta.T
            self._frozen = torch.tensor(True)

    @property
    def delta_weight(self) -> torch.Tensor:
        """返回 LoRA 增量矩阵: B^T @ A^T"""
        return self.lora_B.T @ self.lora_A.T  # (out, in)

    @property
    def trainable_params(self) -> int:
        """可训练参数数量"""
        return self.lora_A.numel() + self.lora_B.numel()

    @property
    def total_params(self) -> int:
        """总参数数量"""
        return self.original.weight.numel() + self.trainable_params


class GapInitLoRALinear(LoRALinear):
    """
    Gap-Init LoRA 变体（参考: "When Is Rank-1 Enough?", arXiv 2602.01522）

    核心思想: 将 LoRA_A 的第一个rank分量沿模态gap方向初始化，
    使得低秩更新的梯度信号一开始就能触及gap几何结构。

    效果: rank-1 + Gap-Init ≈ 标准 rank-8 的性能（按原论文结论）
    """

    def __init__(self, *args, gap_direction: Optional[torch.Tensor] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.gap_direction = gap_direction
        self._gap_init_applied = False

    def apply_gap_init(self, gap_direction: torch.Tensor):
        """
        将 LoRA_A 的第一列沿 gap 方向初始化

        Args:
            gap_direction: (in_features,) — 模态gap方向向量
        """
        if self._gap_init_applied:
            return

        self.gap_direction = gap_direction.to(self.lora_A.device)

        # 归一化 gap 方向
        g = self.gap_direction / (self.gap_direction.norm() + 1e-8)

        # 将 lora_A 的第一列沿 gap 方向初始化
        # lora_A: (in_features, rank)
        with torch.no_grad():
            # 保留剩余列的 Kaiming 初始化
            # 第一列 = gap 方向 × scale
            scale = math.sqrt(self.lora_A.shape[1])  # √rank
            self.lora_A[:, 0] = g[:self.lora_A.shape[0]] * scale

        self._gap_init_applied = True

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # 首次前向传播时自动触发 gap init（如果提供了gap_direction）
        if not self._gap_init_applied and self.gap_direction is not None:
            self.apply_gap_init(self.gap_direction)

        return super().forward(x)


class NullLoRALinear(LoRALinear):
    """
    Null-LoRA 变体：约束 LoRA 增量在原始权重零空间内

    关键约束: W_0^T · ΔW ≈ 0
    通过对 B 矩阵添加正交化惩罚实现
    """

    def __init__(self, *args, null_constraint_weight: float = 0.01, **kwargs):
        super().__init__(*args, **kwargs)
        self.null_constraint_weight = null_constraint_weight

    def null_space_loss(self) -> torch.Tensor:
        """
        计算 W_0^T · ΔW 的 Frobenius 范数
        W_0: (out_features, in_features)
        ΔW = B^T @ A^T: (out_features, in_features)
        """
        W0 = self.original.weight  # (out, in)
        delta_W = self.delta_weight  # (out, in)

        # ||W_0^T @ ΔW||_F^2
        violation = torch.norm(W0.T @ delta_W, p='fro')
        return self.null_constraint_weight * violation ** 2


# ============================================================
# LoRA 注入工具
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
    将 LoRA 注入 CLIP 模型的 Transformer 层

    Args:
        model: CLIP 模型 (HuggingFace transformers)
        rank: LoRA 秩
        alpha: LoRA 缩放因子
        dropout: LoRA dropout
        target_modules: 目标模块名称列表 ["q_proj", "v_proj", "k_proj", "out_proj", "fc1", "fc2"]
        apply_to_vision: 是否注入视觉编码器
        apply_to_text: 是否注入文本编码器
        use_null_lora: 是否使用 Null-LoRA 变体
        use_gap_init: 是否使用 Gap-Init LoRA 变体

    Returns:
        model: 修改后的模型
        lora_layers: {layer_name: LoRALinear} 映射
        total_trainable: 总可训练参数数
    """
    if target_modules is None:
        target_modules = ["q_proj", "v_proj"]

    lora_layers = {}
    total_trainable = 0

    # 替换视觉编码器中的线性层
    if apply_to_vision and hasattr(model, 'vision_model'):
        _inject_lora(
            model.vision_model, target_modules, rank, alpha, dropout,
            lora_layers, "vision", use_null_lora, use_gap_init
        )

    # 替换文本编码器中的线性层
    if apply_to_text and hasattr(model, 'text_model'):
        _inject_lora(
            model.text_model, target_modules, rank, alpha, dropout,
            lora_layers, "text", use_null_lora, use_gap_init
        )

    total_trainable = sum(l.trainable_params for l in lora_layers.values())

    # Freeze everything that is not a LoRA parameter.
    #
    # LoRALinear freezes only the linear layer it wraps, so without this step every other weight of
    # the adapted tower stays trainable: k_proj, out_proj, the MLP blocks, the layer norms and the
    # embedding tables all receive gradients. Measured on CLIP ViT-B/32 with rank 8 on the text
    # tower, that left 145,170,177 trainable parameters against 196,608 LoRA parameters - the run
    # was a full text-tower fine-tuning with a negligible adapter attached, not a LoRA run, and the
    # rank ablation could not have measured a rank effect.
    frozen = 0
    for name, param in model.named_parameters():
        if "lora_" in name:
            param.requires_grad_(True)
        else:
            if param.requires_grad:
                frozen += 1
            param.requires_grad_(False)

    still_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"✅ LoRA 注入完成: rank={rank}, α={alpha}")
    print(f"   {len(lora_layers)} 个 LoRA 层, {total_trainable:,} LoRA 参数")
    print(f"   视觉编码器: {sum(1 for k in lora_layers if k.startswith('vision'))} 层")
    print(f"   文本编码器: {sum(1 for k in lora_layers if k.startswith('text'))} 层")
    print(f"   已冻结非 LoRA 参数张量: {frozen}")
    print(f"   可训练参数合计: {still_trainable:,} (LoRA only)")
    if still_trainable != total_trainable:
        raise RuntimeError(
            f"LoRA scope check failed: {still_trainable:,} parameters are trainable but the "
            f"adapters hold {total_trainable:,}. Only LoRA parameters may remain trainable."
        )

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
    """递归遍历编码器，替换目标线性层"""
    if use_null_lora and use_gap_init:
        raise ValueError("不能同时使用 Null-LoRA 和 Gap-Init")
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
                # 替换父模块中的该层
                parent_name, child_name = _split_name(name)
                parent = encoder.get_submodule(parent_name) if parent_name else encoder
                setattr(parent, child_name, lora_module)
                lora_layers[full_name] = lora_module


def _split_name(name: str) -> Tuple[str, str]:
    """拆分 'encoder.layer.0.attention.q_proj' -> ('encoder.layer.0.attention', 'q_proj')"""
    parts = name.rsplit(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "", parts[0]


# ============================================================
# 工具函数
# ============================================================

def get_lora_params(model: nn.Module) -> List[nn.Parameter]:
    """获取所有 LoRA 可训练参数"""
    params = []
    for name, param in model.named_parameters():
        if 'lora_A' in name or 'lora_B' in name:
            params.append(param)
    return params


def compute_lora_sparsity(lora_layers: Dict[str, LoRALinear]) -> Dict[str, float]:
    """计算每个LoRA层的参数占比（可训练/总参数）"""
    result = {}
    for name, layer in lora_layers.items():
        ratio = layer.trainable_params / layer.total_params
        result[name] = ratio
    return result


def get_null_space_loss(lora_layers: Dict[str, LoRALinear]) -> torch.Tensor:
    """获取所有 Null-LoRA 层的零空间约束损失"""
    loss = torch.tensor(0.0)
    for layer in lora_layers.values():
        if isinstance(layer, NullLoRALinear):
            loss = loss + layer.null_space_loss()
    return loss


# ============================================================
# Gap-Init 工具（参考 arXiv:2602.01522）
# ============================================================

@torch.no_grad()
def compute_gap_direction(
    model,
    dataloader,
    device: str = "mps",
    n_batches: int = 10,
) -> torch.Tensor:
    """
    从数据中估计模态gap方向: g = μ_I - μ_T

    这是 Gap-Init 的核心：找到CLIP预训练embedding空间中
    图像均值与文本均值的差异方向。

    Args:
        model: CLIP 模型
        dataloader: 数据加载器（提供 (image, text) 对）
        device: 设备
        n_batches: 用于估计的batch数

    Returns:
        gap_direction: (D,) — 从文本指向图像的方向向量
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
            truncation=True, max_length=int(os.environ.get("PEFT_MAX_SEQ_LEN", "77")),
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

    # 归一化
    image_embeds = F.normalize(image_embeds, p=2, dim=-1)
    text_embeds = F.normalize(text_embeds, p=2, dim=-1)

    # Gap 方向: 图像均值 - 文本均值
    mu_I = image_embeds.mean(dim=0)
    mu_T = text_embeds.mean(dim=0)
    gap_direction = mu_I - mu_T  # (D,)

    # 归一化到单位向量
    gap_direction = gap_direction / (gap_direction.norm() + 1e-8)

    print(f"📐 Gap方向估计完成 (n={len(image_embeds)} samples)")
    print(f"   ||μ_I - μ_T|| = {(mu_I - mu_T).norm().item():.4f}")
    print(f"   Gap方向范数: {gap_direction.norm().item():.4f}")

    return gap_direction


def apply_gap_init_to_layers(
    lora_layers: Dict[str, LoRALinear],
    gap_direction: torch.Tensor,
):
    """
    将估计的gap方向应用到所有 GapInitLoRALinear 层

    对于每层，取 gap_direction 中对应维度的子向量，
    将其设为 lora_A 的第一列方向。
    """
    applied = 0
    for name, layer in lora_layers.items():
        if isinstance(layer, GapInitLoRALinear):
            # 取 gap_direction 中与 layer 输入维度匹配的部分
            in_features = layer.lora_A.shape[0]
            if len(gap_direction) >= in_features:
                sub_gap = gap_direction[:in_features]
            else:
                # gap维度不足（不应发生），跳过
                continue
            layer.apply_gap_init(sub_gap)
            applied += 1

    print(f"🎯 Gap-Init 已应用到 {applied}/{len(lora_layers)} 个 LoRA 层")
