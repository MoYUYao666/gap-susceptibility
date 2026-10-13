"""
Experiment configuration file — LoRA fine-tuning CLIP modality gap evolution
Adapted for MacBook M5 (MPS backend)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal
import torch


@dataclass
class LoRAConfig:
    """LoRA fine-tuning configuration"""
    rank: int = 8                    # LoRA rank r
    alpha: float = 16.0             # LoRA scaling factor α
    dropout: float = 0.1            # LoRA dropout
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])
    # options: "q_proj", "k_proj", "v_proj", "out_proj", "fc1", "fc2"

    # where to apply
    apply_to_vision: bool = True    # whether to apply LoRA on the vision encoder
    apply_to_text: bool = True      # whether to apply LoRA on the text encoder

    # LoRA variants
    use_null_lora: bool = False     # Null-LoRA constraint
    use_gap_init: bool = False      # Gap-Init initialization (arXiv:2602.01522)


@dataclass
class AdapterConfig:
    """Adapter fine-tuning configuration (Houlsby bottleneck)"""
    bottleneck_dim: int = 16          # bottleneck dimension
    activation: str = "gelu"          # activation function (gelu, relu, silu)
    dropout: float = 0.0              # dropout inside the Adapter
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])
    apply_to_vision: bool = True      # whether to apply on the vision encoder
    apply_to_text: bool = True        # whether to apply on the text encoder


@dataclass
class PrefixConfig:
    """Prefix Tuning configuration"""
    prefix_length: int = 16           # number of prefix tokens
    apply_to_vision: bool = True      # whether to apply on the vision encoder
    apply_to_text: bool = True        # whether to apply on the text encoder


@dataclass
class GapConfig:
    """Modality gap measurement configuration"""
    compute_every_n_epochs: int = 2      # compute the gap once every N epochs
    compute_per_layer: bool = True       # whether to compute the gap layer by layer
    metrics: List[str] = field(default_factory=lambda: [
        "centroid_gap",                  # centroid distance
        "distribution_gap",              # Wasserstein distribution distance
        "cosine_stats",                  # cosine similarity distribution statistics
        "positive_separation",           # positive-negative sample separation
    ])
    sample_size: int = 5000              # number of samples when computing the gap (avoid OOM)


@dataclass
class MissingModalityConfig:
    """Missing modality simulation configuration"""
    image_drop_ratios: List[float] = field(default_factory=lambda: [0.0, 0.1, 0.3, 0.5])
    text_mask_ratios: List[float] = field(default_factory=lambda: [0.0, 0.1, 0.3, 0.5])
    complete_missing: bool = True


# ============================================================
# Route C enhancement configuration
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
    """Cross-platform automatic detection of the best device: CUDA > MPS > CPU"""
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


@dataclass
class TrainConfig:
    """Training configuration"""
    # model
    clip_model: str = "openai/clip-vit-base-patch32"  # ViT-B/32 (~400MB, suitable for M5)
    # alternative: "openai/clip-vit-base-patch16"

    # data
    dataset: str = "flickr30k"           # flickr30k, coco
    max_samples: Optional[int] = None    # limit the number of samples (for debugging)
    image_size: int = 224

    # training hyperparameters
    batch_size: int = 64                 # supported under M5 unified memory
    num_epochs: int = 20
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    warmup_steps: int = 100
    gradient_accumulation_steps: int = 1

    # optimizer
    optimizer: Literal["adamw", "adam"] = "adamw"
    scheduler: Literal["cosine", "linear", "none"] = "cosine"

    # logging & saving
    log_every_n_steps: int = 50
    save_dir: str = "./outputs"
    seed: int = 42

    # Mixed precision (MPS has limited float16 support, float32 is recommended)
    use_amp: bool = False

    # device (automatic detection CUDA > MPS > CPU)
    device: str = field(default_factory=_detect_device)




@dataclass
class ExperimentConfig:
    """Main experiment configuration"""
    name: str = "gap1_baseline"

    # PEFT method selection
    peft_method: str = "lora"         # "lora" | "adapter" | "prefix" | "full_ft" | "frozen"
    lora: LoRAConfig = field(default_factory=LoRAConfig)
    adapter: Optional[AdapterConfig] = None
    prefix: Optional[PrefixConfig] = None

    gap: GapConfig = field(default_factory=GapConfig)
    missing: MissingModalityConfig = field(default_factory=MissingModalityConfig)
    train: TrainConfig = field(default_factory=TrainConfig)

    # Route C enhancement
    gap_reg: GapRegConfig = field(default_factory=GapRegConfig)
    rank_schedule: RankScheduleConfig = field(default_factory=RankScheduleConfig)
    alpha_schedule: AlphaScheduleConfig = field(default_factory=AlphaScheduleConfig)
    dg_es: DGESConfig = field(default_factory=DGESConfig)

    # list of experiment variants (for batch experiments)
    lora_variants: List[LoRAConfig] = field(default_factory=list)

    def __post_init__(self):
        """If lora_variants is specified, the individual lora config is ignored"""
        if not self.lora_variants:
            self.lora_variants = [self.lora]

        # set the default adapter/prefix configuration
        if self.peft_method == "adapter" and self.adapter is None:
            self.adapter = AdapterConfig()
        if self.peft_method == "prefix" and self.prefix is None:
            self.prefix = PrefixConfig()


# ============================================================
# Preset experiment variants
# ============================================================

def get_all_experiments() -> List[ExperimentConfig]:
    """Return all experiment configurations for RQ1-RQ4"""
    experiments = []

    base = TrainConfig()

    # ---- RQ1: effect of LoRA rank ----
    for rank in [4, 8, 16, 32, 64]:
        experiments.append(ExperimentConfig(
            name=f"rq1_rank{rank}",
            lora=LoRAConfig(rank=rank, alpha=rank*2,
                           apply_to_vision=True, apply_to_text=True),
            train=base,
        ))

    # ---- RQ2: where LoRA is applied ----
    for name, vis, txt in [("vision_only", True, False),
                           ("text_only", False, True),
                           ("both", True, True)]:
        experiments.append(ExperimentConfig(
            name=f"rq2_{name}",
            lora=LoRAConfig(rank=8, alpha=16.0,
                           apply_to_vision=vis, apply_to_text=txt),
            train=base,
        ))

    # ---- Baseline: full fine-tuning, frozen ----
    experiments.append(ExperimentConfig(
        name="baseline_frozen",
        lora=LoRAConfig(rank=0, apply_to_vision=False, apply_to_text=False),
        train=base,
    ))
    experiments.append(ExperimentConfig(
        name="baseline_full_ft",
        lora=None,  # mark as full fine-tuning
        train=base,
    ))

    # ---- Gap-Init baseline (arXiv:2602.01522) ----
    # rank=1 + Gap-Init vs rank=8 standard LoRA
    for rank in [1, 2, 4, 8]:
        experiments.append(ExperimentConfig(
            name=f"gap_init_r{rank}",
            lora=LoRAConfig(rank=rank, alpha=rank*2,
                           apply_to_vision=True, apply_to_text=True,
                           use_gap_init=True),
            train=base,
        ))

    # ---- Null-LoRA baseline ----
    experiments.append(ExperimentConfig(
        name="null_lora_r8",
        lora=LoRAConfig(rank=8, alpha=16.0,
                       apply_to_vision=True, apply_to_text=True,
                       use_null_lora=True),
        train=base,
    ))

    return experiments
