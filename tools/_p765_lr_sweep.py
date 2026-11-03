# -*- coding: utf-8 -*-
r"""Find a learning rate at which LoRA actually converges on COCO within a feasible budget.

Established: the trainer's LoRA path does learn - six epochs on 200 images drop the train loss from
3.34 to 1.84 - but the validation loss rises over the same span (3.47 to 5.57), so the model is
overfitting a tiny subset while still far from fitting it. Training the projections reaches 0.25 in
60 steps at lr 1e-3, which is a hundred times the LoRA learning rate, so the LoRA path is
effectively undertrained rather than broken.

This sweeps the learning rate on a fixed 2,000-image training set with a held-out validation set and
reports train and validation loss per epoch, which distinguishes "needs a larger step" from "needs
more data".

    python tools/_p765_lr_sweep.py --images 2000 --epochs 4 --apply
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
OUT = REPO / "outputs" / "analysis" / "coco_lr_sweep.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=2000)
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lrs", type=str, default="1e-4,3e-4,1e-3")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    from src.config import ExperimentConfig, TrainConfig, LoRAConfig, GapConfig
    from src.trainer import GapAwareTrainer
    from _p754_coco_scaleup import subset_loader, evaluate

    lrs = [float(x) for x in a.lrs.split(",")]
    tr_loader = subset_loader("train", a.images, a.batch, True, workers=8)
    va_loader = subset_loader("val", 500, 32, False, first=False, workers=4)

    rows = []
    for lr in lrs:
        print()
        print("=" * 100)
        print(f"lr = {lr}")
        print("=" * 100)
        t0 = time.time()
        cfg = ExperimentConfig(
            name=f"sweep_lr{lr}", peft_method="lora",
            lora=LoRAConfig(rank=8, alpha=16.0, apply_to_text=True, apply_to_vision=False),
            gap=GapConfig(compute_every_n_epochs=1, compute_per_layer=False, sample_size=200),
            train=TrainConfig(dataset="coco", batch_size=a.batch, num_epochs=a.epochs,
                              learning_rate=lr, seed=42, use_amp=False,
                              save_dir=str(REPO / "outputs" / "lr_sweep" / f"lr{lr}")))
        tr = GapAwareTrainer(cfg)
        tr.setup_model()
        tr.train(tr_loader, va_loader)
        dt = time.time() - t0
        _, val_l, _ = None, None, None
        met = evaluate(tr.model, va_loader, "cuda" if __import__("torch").cuda.is_available()
                       else "cpu")
        row = {"lr": lr, "epochs": a.epochs, "images": a.images, "seconds": round(dt, 1),
               "train_losses": [round(x, 4) for x in tr.train_losses],
               "val_losses": [round(x, 4) for x in tr.val_losses],
               "R@1": met["R@1"], "R@5": met["R@5"], "R@10": met["R@10"],
               "n_unique_images": met["n_unique_images"]}
        rows.append(row)
        print(f"  train {row['train_losses']}")
        print(f"  val   {row['val_losses']}")
        print(f"  corrected R@1 = {met['R@1']:.4f}  R@5 = {met['R@5']:.4f}  "
              f"({met['n_unique_images']} gallery images, {dt:.0f}s)")

    print()
    print("=" * 100)
    print("summary")
    print("=" * 100)
    for r in rows:
        print(f"  lr={r['lr']:<8} train {r['train_losses'][0]:.3f}->{r['train_losses'][-1]:.3f}  "
              f"val {r['val_losses'][0]:.3f}->{r['val_losses'][-1]:.3f}  R@1={r['R@1']:.4f}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
