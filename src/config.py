"""
实验配置文件 — LoRA微调CLIP模态差距演化
适配 MacBook M5 (MPS backend)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal
import torch


@dataclass
class LoRAConfig:
    """LoRA 微调配置"""
    rank: int = 8                    # LoRA 秩 r
    alpha: float = 16.0             # LoRA 缩放因子 α
    dropout: float = 0.1            # LoRA dropout
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])
    # 可选: "q_proj", "k_proj", "v_proj", "out_proj", "fc1", "fc2"

    # 作用位置
    apply_to_vision: bool = True    # 是否在视觉编码器上应用LoRA
    apply_to_text: bool = True      # 是否在文本编码器上应用LoRA

    # LoRA 变体
    use_null_lora: bool = False     # Null-LoRA 约束
    use_gap_init: bool = False      # Gap-Init 初始化 (arXiv:2602.01522)


@dataclass
class AdapterConfig:
    """Adapter 微调配置（Houlsby bottleneck）"""
    bottleneck_dim: int = 16          # 瓶颈维度
    activation: str = "gelu"          # 激活函数 (gelu, relu, silu)
    dropout: float = 0.0              # Adapter 内部 dropout
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])
    apply_to_vision: bool = True      # 是否在视觉编码器上应用
    apply_to_text: bool = True        # 是否在文本编码器上应用


@dataclass
class PrefixConfig:
    """Prefix Tuning 配置"""
    prefix_length: int = 16           # Prefix token 数量
    apply_to_vision: bool = True      # 是否在视觉编码器上应用
    apply_to_text: bool = True        # 是否在文本编码器上应用


@dataclass
class GapConfig:
    """模态差距度量配置"""
    compute_every_n_epochs: int = 2      # 每N个epoch计算一次gap
    compute_per_layer: bool = True       # 是否逐层计算gap
    metrics: List[str] = field(default_factory=lambda: [
        "centroid_gap",                  # 质心距离
        "distribution_gap",              # Wasserstein分布距离
        "cosine_stats",                  # 余弦相似度分布统计
        "positive_separation",           # 正负样本分离度
    ])
    sample_size: int = 5000              # 计算gap时的采样数量（避免OOM）


@dataclass
class MissingModalityConfig:
    """缺失模态模拟配置"""
    image_drop_ratios: List[float] = field(default_factory=lambda: [0.0, 0.1, 0.3, 0.5])
    text_mask_ratios: List[float] = field(default_factory=lambda: [0.0, 0.1, 0.3, 0.5])
    complete_missing: bool = True


# ============================================================
# Route C 增强配置
# ============================================================

@dataclass
class GapRegConfig:
    """Gap-Regularized Loss (Route C1)"""
    enabled: bool = False
    lambda_reg: float = 0.1
    target: str = "centroid_gap"


@dataclass
class RankScheduleConfig:
    """Dynamic Rank Scheduler (Route C2)"""
    enabled: bool = False
    initial_rank: int = 8
    schedule: List[tuple] = field(default_factory=lambda: [(3, 4), (6, 2)])


@dataclass
class AlphaScheduleConfig:
    """α Annealing (Route C4)"""
    enabled: bool = False
    alpha_max: float = 64.0
    alpha_min: float = 4.0
    decay: float = 0.3


@dataclass
class DGESConfig:
    """DG-Guided Early Stopping (Route E)"""
    enabled: bool = False
    patience: int = 2


def _detect_device() -> str:
    """跨平台自动检测最佳设备: CUDA > MPS > CPU"""
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


@dataclass
class TrainConfig:
    """训练配置"""
    # 模型
    clip_model: str = "openai/clip-vit-base-patch32"  # ViT-B/32 (~400MB, 适合M5)
    # 备选: "openai/clip-vit-base-patch16"

    # 数据
    dataset: str = "flickr30k"           # flickr30k, coco
    max_samples: Optional[int] = None    # 限制样本数（调试用）
    image_size: int = 224

    # 训练参数
    batch_size: int = 64                 # M5 统一内存下可支持
    num_epochs: int = 20
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    warmup_steps: int = 100
    gradient_accumulation_steps: int = 1

    # 优化器
    optimizer: Literal["adamw", "adam"] = "adamw"
    scheduler: Literal["cosine", "linear", "none"] = "cosine"

    # 日志 & 保存
    log_every_n_steps: int = 50
    save_dir: str = "./outputs"
    seed: int = 42

    # Mixed precision (MPS 对 float16 支持有限，建议 float32)
    use_amp: bool = False

    # 设备（自动检测 CUDA > MPS > CPU）
    device: str = field(default_factory=_detect_device)




@dataclass
class ExperimentConfig:
    """主实验配置"""
    name: str = "gap1_baseline"

    # PEFT 方法选择
    peft_method: str = "lora"         # "lora" | "adapter" | "prefix" | "full_ft" | "frozen"
    lora: LoRAConfig = field(default_factory=LoRAConfig)
    adapter: Optional[AdapterConfig] = None
    prefix: Optional[PrefixConfig] = None

    gap: GapConfig = field(default_factory=GapConfig)
    missing: MissingModalityConfig = field(default_factory=MissingModalityConfig)
    train: TrainConfig = field(default_factory=TrainConfig)

    # Route C 增强
    gap_reg: GapRegConfig = field(default_factory=GapRegConfig)
    rank_schedule: RankScheduleConfig = field(default_factory=RankScheduleConfig)
    alpha_schedule: AlphaScheduleConfig = field(default_factory=AlphaScheduleConfig)
    dg_es: DGESConfig = field(default_factory=DGESConfig)

    # 实验变体列表（用于批量实验）
    lora_variants: List[LoRAConfig] = field(default_factory=list)

    def __post_init__(self):
        """如果指定了lora_variants，则忽略单独的lora配置"""
        if not self.lora_variants:
            self.lora_variants = [self.lora]

        # 设置默认 adapter/prefix 配置
        if self.peft_method == "adapter" and self.adapter is None:
            self.adapter = AdapterConfig()
        if self.peft_method == "prefix" and self.prefix is None:
            self.prefix = PrefixConfig()


# ============================================================
# 预设实验变体
# ============================================================

def get_all_experiments() -> List[ExperimentConfig]:
    """返回RQ1-RQ4的所有实验配置"""
    experiments = []

    base = TrainConfig()

    # ---- RQ1: LoRA rank 影响 ----
    for rank in [4, 8, 16, 32, 64]:
        experiments.append(ExperimentConfig(
            name=f"rq1_rank{rank}",
            lora=LoRAConfig(rank=rank, alpha=rank*2,
                           apply_to_vision=True, apply_to_text=True),
            train=base,
        ))

    # ---- RQ2: LoRA 作用位置 ----
    for name, vis, txt in [("vision_only", True, False),
                           ("text_only", False, True),
                           ("both", True, True)]:
        experiments.append(ExperimentConfig(
            name=f"rq2_{name}",
            lora=LoRAConfig(rank=8, alpha=16.0,
                           apply_to_vision=vis, apply_to_text=txt),
            train=base,
        ))

    # ---- Baseline: 全量微调, 冻结 ----
    experiments.append(ExperimentConfig(
        name="baseline_frozen",
        lora=LoRAConfig(rank=0, apply_to_vision=False, apply_to_text=False),
        train=base,
    ))
    experiments.append(ExperimentConfig(
        name="baseline_full_ft",
        lora=None,  # 标记为全量微调
        train=base,
    ))

    # ---- Gap-Init 基线 (arXiv:2602.01522) ----
    # rank=1 + Gap-Init vs rank=8 标准LoRA
    for rank in [1, 2, 4, 8]:
        experiments.append(ExperimentConfig(
            name=f"gap_init_r{rank}",
            lora=LoRAConfig(rank=rank, alpha=rank*2,
                           apply_to_vision=True, apply_to_text=True,
                           use_gap_init=True),
            train=base,
        ))

    # ---- Null-LoRA 基线 ----
    experiments.append(ExperimentConfig(
        name="null_lora_r8",
        lora=LoRAConfig(rank=8, alpha=16.0,
                       apply_to_vision=True, apply_to_text=True,
                       use_null_lora=True),
        train=base,
    ))

    return experiments
