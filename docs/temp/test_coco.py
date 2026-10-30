"""Quick test — COCO dataset loading"""
import os, sys
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, ".")

from src.dataset import create_dataloaders
train, val, test = create_dataloaders(
    dataset_name="coco", data_dir=".",
    batch_size=128, max_samples=2000, pre_tokenize=False,
)
print(f"Train: {len(train.dataset)} samples, {len(train)} batches")
print(f"Val:   {len(val.dataset)} samples, {len(val)} batches")

from src.trainer import GapAwareTrainer
from src.config import ExperimentConfig, LoRAConfig, TrainConfig, GapConfig

lora = LoRAConfig(rank=8, alpha=16, apply_to_vision=False, apply_to_text=True)
train_cfg = TrainConfig(dataset="coco", batch_size=128, num_epochs=1,
                        save_dir="./outputs/test_coco", seed=42)
exp = ExperimentConfig(name="test", peft_method="lora", lora=lora,
                       gap=GapConfig(compute_every_n_epochs=1), train=train_cfg)

trainer = GapAwareTrainer(exp)
trainer.setup_model()
trainer.enable_dg_star_tracking()
print("Model loaded, starting 1-epoch test...")
trainer.train(train, val)
print("1 epoch OK — COCO works")
