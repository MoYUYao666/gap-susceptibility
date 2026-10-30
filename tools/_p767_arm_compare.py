# -*- coding: utf-8 -*-
r"""Decide whether COCO training is broken generally or only through the LoRA path.

Three learning rates all fail on 2,000 training images: lr 1e-4 overfits (train 4.01 -> 2.45, val
3.53 -> 4.95) and both 3e-4 and 1e-3 degenerate (loss pinned at 4.15, validation at log(64) =
3.4465). Corrected retrieval falls from a frozen 0.4755 (image-to-text) to 0.004-0.007.

On 200 images the plain model trains fine - 60 steps reach loss 0.25 with the projections trained -
so the data and loss are sound and the failure is scale- or path-dependent. This runs three arms on
the same 2,000 images and the same budget and compares train and validation loss plus retrieval:

  full_ft  : all parameters, lr 1e-5
  proj     : build through the trainer but with the projection layers trainable
  lora     : rank 8, lr 1e-4 (the pattern already measured)

    python tools/_p767_arm_compare.py --images 2000 --epochs 6 --apply
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
OUT = REPO / "outputs" / "analysis" / "arm_compare.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=2000)
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--eval-images", type=int, default=500)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F
    from transformers import CLIPModel, CLIPProcessor
    from src.config import ExperimentConfig, TrainConfig, LoRAConfig, GapConfig
    from src.trainer import GapAwareTrainer
    from _p754_coco_scaleup import subset_loader, evaluate

    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    va_loader = subset_loader("val", a.eval_images, 32, False, first=False, workers=4)
    tr_loader = subset_loader("train", a.images, a.batch, True, workers=8)

    rows = []
    for arm, lr in (("full_ft", 1e-5), ("lora", 1e-4)):
        print()
        print("=" * 100)
        print(f"{arm}  lr={lr}  {a.images} images  {a.epochs} epochs")
        print("=" * 100)
        cfg = ExperimentConfig(
            name=f"cmp_{arm}", peft_method=arm,
            lora=(LoRAConfig(rank=8, alpha=16.0, apply_to_text=True, apply_to_vision=False)
                  if arm == "lora" else None),
            gap=GapConfig(compute_every_n_epochs=5, compute_per_layer=False, sample_size=200),
            train=TrainConfig(dataset="coco", batch_size=a.batch, num_epochs=a.epochs,
                              learning_rate=lr, seed=42, use_amp=False,
                              save_dir=str(REPO / "outputs" / "arm_compare" / arm)))
        tr = GapAwareTrainer(cfg)
        tr.setup_model()
        t0 = time.time()
        tr.train(tr_loader, va_loader)
        dt = time.time() - t0
        met = evaluate(tr.model, va_loader, device, processor=proc)
        row = {"arm": arm, "lr": lr, "epochs": a.epochs, "images": a.images,
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
    print("summary against the frozen baseline (i2t 0.4755 / t2i 0.2857 on a 2,000-image gallery)")
    print("=" * 100)
    for r in rows:
        print(f"  {r['arm']:<9} lr={r['lr']:<8} train {r['train_losses'][0]:.2f}->"
              f"{r['train_losses'][-1]:.2f}  val {r['val_losses'][0]:.2f}->{r['val_losses'][-1]:.2f}"
              f"  R@1 {r['R@1']:.4f}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
