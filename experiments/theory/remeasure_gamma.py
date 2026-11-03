"""
Re-measure Gamma at theta_0 (before training) using fixed code (only trainable params).
Validates Theorem 2: alpha_pred = -eta * (Gamma_v * ||g_v|| + Gamma_t * ||g_t||)
"""
import os, sys, json
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch, torch.nn.functional as F
import numpy as np
from src.config import ExperimentConfig, LoRAConfig, TrainConfig, GapConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders
from src.gap_susceptibility import compute_gap_susceptibility

ETA = 1e-4
BATCH = 128

CONFIGS = [
    {"name": "text_r8", "rank": 8, "alpha": 16, "vis": False, "txt": True},
    {"name": "both_r8", "rank": 8, "alpha": 16, "vis": True,  "txt": True},
    {"name": "both_r16","rank":16, "alpha": 32, "vis": True,  "txt": True},
    {"name": "text_r64","rank":64, "alpha":128,"vis": False, "txt": True},
]


def main():
    print(f"{'Config':15s} {'Gamma_v':>10s} {'Gamma_t':>10s} {'|g_v|':>10s} {'|g_t|':>10s} {'a_step':>10s} {'a_epoch':>10s} {'V1 a_fit':>10s} {'cos_v':>8s} {'cos_t':>8s}")
    print("-" * 110)

    # Reference V1 alpha_fit values
    v1_ref = {"text_r8": -0.0481, "both_r8": -0.0415, "both_r16": -0.0470, "text_r64": -0.0539}

    for cfg in CONFIGS:
        lora = LoRAConfig(rank=cfg["rank"], alpha=cfg["alpha"],
                          apply_to_vision=cfg["vis"], apply_to_text=cfg["txt"])
        train = TrainConfig(dataset="flickr30k", batch_size=BATCH, num_epochs=1,
                            save_dir=str(PROJECT_ROOT / "outputs" / "tmp"), seed=42)
        exp = ExperimentConfig(name=cfg["name"], peft_method="lora", lora=lora,
                               gap=GapConfig(compute_every_n_epochs=1), train=train)

        trainer = GapAwareTrainer(exp)
        trainer.setup_model()
        train_loader, val_loader, _ = create_dataloaders(
            dataset_name="flickr30k", data_dir=str(PROJECT_ROOT),
            batch_size=BATCH, max_samples=2000, num_workers=0)

        # Measure Gamma BEFORE any training (at theta_0)
        trainer.model.eval()
        for batch in val_loader:
            images = batch["image"].to(trainer.device)[:64]
            texts = batch["caption"][:64]
            ti = trainer.processor(text=texts, return_tensors="pt",
                                   padding=True, truncation=True, max_length=77)
            outputs = trainer.model(
                pixel_values=images,
                input_ids=ti["input_ids"].to(trainer.device),
                attention_mask=ti.get("attention_mask",
                    torch.ones_like(ti["input_ids"])).to(trainer.device))
            ie = F.normalize(outputs.image_embeds, p=2, dim=-1)
            te = F.normalize(outputs.text_embeds, p=2, dim=-1)
            gamma = compute_gap_susceptibility(trainer.model, ie, te)
            break

        gv, gt = gamma["Gamma_v"], gamma["Gamma_t"]
        ngv, ngt = gamma["norm_g_v"], gamma["norm_g_t"]
        a_step = -ETA * (gv * ngv + gt * ngt)  # per gradient step

        # Convert to per-epoch: α_epoch = α_step × steps_per_epoch
        # V1 used 10000 samples, 80% train = 8000, batch=128 → 62.5 steps/epoch
        steps_per_epoch = 8000 / BATCH  # ≈ 62.5
        a_epoch = a_step * steps_per_epoch
        cv, ct = gamma["cos_phi_v"], gamma["cos_phi_t"]

        ref = v1_ref.get(cfg['name'], 0)
        print(f"{cfg['name']:15s} {gv:>10.4f} {gt:>10.4f} {ngv:>10.4f} {ngt:>10.4f} {a_step:>10.4f} {a_epoch:>10.4f} {ref:>10.4f} {cv:>8.4f} {ct:>8.4f}")


if __name__ == "__main__":
    main()
