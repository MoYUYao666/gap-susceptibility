# -*- coding: utf-8 -*-
r"""One long-enough run to decide whether this pipeline can learn COCO at all.

Everything so far used too few optimisation steps to be conclusive: 2,000 images at batch 64 is 31
steps per epoch, so four epochs is 125 steps, and the losses are still falling at the end. A single
well-resolved run answers the question the larger dataset depends on: with a sane learning rate and
enough epochs, does validation loss fall and does retrieval improve over the frozen baseline of
R@1 = 0.4755 (image-to-text) / 0.2857 (text-to-image) on the 2,000-image gallery?

Frozen reference for comparison is recomputed here at the same gallery size.

    python tools/_p766_long_run.py --images 2000 --epochs 15 --lr 3e-5 --apply
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
OUT = REPO / "outputs" / "analysis" / "coco_long_run.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=2000)
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--eval-images", type=int, default=500)
    ap.add_argument("--arm", type=str, default="text_only")
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

    print()
    print("=" * 100)
    print(f"frozen baseline on a {a.eval_images}-image gallery")
    print("=" * 100)
    frozen = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device).eval()
    fm = evaluate(frozen, va_loader, device, processor=proc)
    print(f"  R@1 = {fm['R@1']:.4f}  R@5 = {fm['R@5']:.4f}  R@10 = {fm['R@10']:.4f}  "
          f"(i2t {fm['R@1_i2t']:.4f} / t2i {fm['R@1_t2i']:.4f})")
    del frozen
    torch.cuda.empty_cache()

    print()
    print("=" * 100)
    print(f"{a.arm} LoRA r=8, lr={a.lr}, {a.images} images, {a.epochs} epochs")
    print("=" * 100)
    cfg = ExperimentConfig(
        name=f"long_{a.arm}", peft_method="lora",
        lora=LoRAConfig(rank=8, alpha=16.0, apply_to_text=True,
                        apply_to_vision=(a.arm == "both")),
        gap=GapConfig(compute_every_n_epochs=5, compute_per_layer=False, sample_size=200),
        train=TrainConfig(dataset="coco", batch_size=a.batch, num_epochs=a.epochs,
                          learning_rate=a.lr, seed=42, use_amp=False,
                          save_dir=str(REPO / "outputs" / "long_run")))
    tr = GapAwareTrainer(cfg)
    tr.setup_model()
    t0 = time.time()
    tr.train(tr_loader, va_loader)
    dt = time.time() - t0
    met = evaluate(tr.model, va_loader, device, processor=proc)

    print()
    print(f"  train losses: {[round(x, 3) for x in tr.train_losses]}")
    print(f"  val losses  : {[round(x, 3) for x in tr.val_losses]}")
    print(f"  corrected R@1 = {met['R@1']:.4f}  R@5 = {met['R@5']:.4f}  R@10 = {met['R@10']:.4f}")
    print(f"  i2t R@1 = {met['R@1_i2t']:.4f}   t2i R@1 = {met['R@1_t2i']:.4f}")
    print(f"  frozen was i2t {fm['R@1_i2t']:.4f} / t2i {fm['R@1_t2i']:.4f}")
    print(f"  {dt:.0f}s for {a.epochs} epochs on {a.images} images")

    res = {"arm": a.arm, "images": a.images, "epochs": a.epochs, "lr": a.lr,
           "train_losses": [float(x) for x in tr.train_losses],
           "val_losses": [float(x) for x in tr.val_losses],
           "finetuned": met, "frozen": fm, "seconds": round(dt, 1)}
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
