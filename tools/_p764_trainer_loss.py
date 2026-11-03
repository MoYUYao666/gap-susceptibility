# -*- coding: utf-8 -*-
r"""Run the trainer's LoRA path on a tiny COCO subset and watch the loss step by step.

Ground truth established so far:
  - the plain model fits this data easily: 60 steps on 200 images reach loss 0.25 when the
    projections train, and 0.73 when only logit_scale trains
  - the trainer's LoRA path reaches only ~3.5 after two epochs on 2,000 images, which is log(32),
    the value of an uninformative model
  - the trainer injects LoRA before moving the model to the device, so device placement is correct

Therefore something in the trainer's step differs from the plain training loop. This runs the
trainer on 200 images and prints the loss per epoch, which distinguishes "learns slowly" from
"does not learn".

    python tools/_p764_trainer_loss.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
OUT = REPO / "outputs" / "analysis" / "trainer_loss.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=200)
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    from src.config import ExperimentConfig, TrainConfig, LoRAConfig, GapConfig
    from src.trainer import GapAwareTrainer
    from _p754_coco_scaleup import subset_loader

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tr_loader = subset_loader("train", a.images, a.batch, True, workers=4)
    va_loader = subset_loader("val", 100, a.batch, False, first=False, workers=2)

    cfg = ExperimentConfig(
        name="trainer_loss_probe", peft_method="lora",
        lora=LoRAConfig(rank=8, alpha=16.0, apply_to_text=True, apply_to_vision=False),
        gap=GapConfig(compute_every_n_epochs=1, compute_per_layer=False, sample_size=100),
        train=TrainConfig(dataset="coco", batch_size=a.batch, num_epochs=a.epochs,
                          learning_rate=a.lr, seed=42, use_amp=False,
                          save_dir=str(REPO / "outputs" / "trainer_loss_probe")))
    tr = GapAwareTrainer(cfg)
    tr.setup_model()

    # confirm device placement of every lora parameter
    lora_dev = {str(p.device) for nm, p in tr.model.named_parameters() if "lora_" in nm}
    print(f"  lora parameter devices: {lora_dev}")
    print(f"  model device: {next(tr.model.parameters()).device}")

    # the model's own zero-step loss, before any training
    import torch.nn.functional as F
    b = next(iter(tr_loader))
    toks = tr.processor(text=b["caption"], return_tensors="pt", padding=True,
                              truncation=True, max_length=77)
    with torch.no_grad():
        out = tr.model(pixel_values=b["image"].to(device),
                       input_ids=toks["input_ids"].to(device),
                       attention_mask=toks["attention_mask"].to(device))
        ie = F.normalize(out.image_embeds, p=2, dim=-1)
        te = F.normalize(out.text_embeds, p=2, dim=-1)
        logits = tr.model.logit_scale.exp() * ie @ te.T
        labels = torch.arange(logits.shape[0], device=device)
        l0 = ((F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) / 2).item()
    print(f"  zero-step loss on one training batch (via trainer's model): {l0:.4f}")
    print(f"  log(batch) = {torch.log(torch.tensor(float(a.batch))):.4f}")

    print()
    print("=" * 100)
    print(f"trainer.train on {a.images} images, {a.epochs} epochs, lr {a.lr}")
    print("=" * 100)
    tr.train(tr_loader, va_loader)
    losses = tr.train_losses
    print()
    print(f"  per-epoch train loss: {[round(x, 4) for x in losses]}")
    print(f"  first {losses[0]:.4f} -> last {losses[-1]:.4f}  (drop {losses[0] - losses[-1]:+.4f})")

    res = {"zero_step_loss": l0, "epoch_losses": losses, "images": a.images,
           "epochs": a.epochs, "lr": a.lr, "lora_devices": sorted(lora_dev)}
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
