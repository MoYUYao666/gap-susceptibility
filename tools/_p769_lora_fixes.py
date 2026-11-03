# -*- coding: utf-8 -*-
r"""Test whether LoRA recovers with a smaller step, no dropout, or more capacity.

Established on the same 2,000 COCO images and the same six epochs:

  frozen           image-to-text R@1 = 0.4755
  full fine-tuning image-to-text R@1 = 0.7180   (train loss 0.80 -> 0.10)
  LoRA r=8, lr 1e-4 image-to-text R@1 = 0.0070  (train loss 4.01 -> 2.45, val rising)

Full fine-tuning works at lr 1e-5; LoRA at lr 1e-4 collapses. Two candidate causes remain: the step
size is too large for the adapter path, and the default dropout of 0.1 is being applied inside the
adapter. This runs both fixes and a capacity increase, so the cause can be named rather than guessed.

    python tools/_p769_lora_fixes.py --images 2000 --epochs 6 --apply
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

CONFIGS = [
    # label, rank, alpha, dropout, lr
    ("r8_lr1e-5_drop0", 8, 8.0, 0.0, 1e-5),
    ("r8_lr1e-4_drop0", 8, 8.0, 0.0, 1e-4),
    ("r64_lr1e-4_drop0", 64, 64.0, 0.0, 1e-4),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=2000)
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--eval-images", type=int, default=500)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    from transformers import CLIPProcessor
    from src.config import ExperimentConfig, TrainConfig, LoRAConfig, GapConfig
    from src.trainer import GapAwareTrainer
    from _p754_coco_scaleup import subset_loader, evaluate

    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    va_loader = subset_loader("val", a.eval_images, 32, False, first=False, workers=4)
    tr_loader = subset_loader("train", a.images, a.batch, True, workers=8)

    rows = []
    for label, rank, alpha, dropout, lr in CONFIGS:
        print()
        print("=" * 100)
        print(f"{label}   rank={rank} alpha={alpha} dropout={dropout} lr={lr}")
        print("=" * 100)
        cfg = ExperimentConfig(
            name=label, peft_method="lora",
            lora=LoRAConfig(rank=rank, alpha=alpha, dropout=dropout,
                            apply_to_text=True, apply_to_vision=False),
            gap=GapConfig(compute_every_n_epochs=5, compute_per_layer=False, sample_size=200),
            train=TrainConfig(dataset="coco", batch_size=a.batch, num_epochs=a.epochs,
                              learning_rate=lr, seed=42, use_amp=False,
                              save_dir=str(REPO / "outputs" / "lora_fixes" / label)))
        tr = GapAwareTrainer(cfg)
        tr.setup_model()
        t0 = time.time()
        tr.train(tr_loader, va_loader)
        dt = time.time() - t0
        met = evaluate(tr.model, va_loader, device, processor=proc)
        row = {"label": label, "rank": rank, "alpha": alpha, "dropout": dropout, "lr": lr,
               "train_losses": [round(float(x), 3) for x in tr.train_losses],
               "val_losses": [round(float(x), 3) for x in tr.val_losses],
               "R@1": round(met["R@1"], 4), "R@1_i2t": round(met["R@1_i2t"], 4),
               "R@1_t2i": round(met["R@1_t2i"], 4), "seconds": round(dt, 1)}
        rows.append(row)
        print(f"  train {row['train_losses']}")
        print(f"  val   {row['val_losses']}")
        print(f"  R@1 {row['R@1']:.4f} (i2t {row['R@1_i2t']:.4f} / t2i {row['R@1_t2i']:.4f})  "
              f"{dt:.0f}s")
        del tr
        torch.cuda.empty_cache()

    print()
    print("=" * 100)
    print("summary   (frozen i2t 0.4755 / t2i 0.2857 ; full_ft i2t 0.7180 / t2i 0.3859)")
    print("=" * 100)
    for r in rows:
        print(f"  {r['label']:<20} train {r['train_losses'][0]:.2f}->{r['train_losses'][-1]:.2f}  "
              f"val {r['val_losses'][0]:.2f}->{r['val_losses'][-1]:.2f}  "
              f"i2t {r['R@1_i2t']:.4f}")
    if a.apply:
        out = REPO / "outputs" / "analysis" / "lora_fixes.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
