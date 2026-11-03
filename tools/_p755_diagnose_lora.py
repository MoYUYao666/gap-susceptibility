# -*- coding: utf-8 -*-
r"""Diagnose why LoRA fine-tuning on COCO does not converge.

Frozen CLIP scores R@1 = 0.52 under the corrected protocol, but two epochs of text-only LoRA leave
R@1 at 0.007 while the training loss only drifts from 3.99 to 3.53. That is not an under-training
signature - the loss is far above what a contrastive objective reaches when it is learning.

Questions to settle:
  1. Are the LoRA parameters actually receiving gradients and changing?
  2. Does the model's own forward pass at evaluation differ from training (processor mismatch)?
  3. Is the contrastive loss scale sane (logit_scale)?

A short run answers all three.

    python tools/_p755_diagnose_lora.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=200)
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F
    from src.config import ExperimentConfig, TrainConfig, LoRAConfig, GapConfig
    from src.trainer import GapAwareTrainer
    sys.path.insert(0, str(REPO / "tools"))
    from _p754_coco_scaleup import subset_loader

    device = "cuda" if torch.cuda.is_available() else "cpu"
    ds_loader = subset_loader("train", a.images, a.batch, True, workers=4)

    cfg = ExperimentConfig(
        name="diag_lora", peft_method="lora",
        lora=LoRAConfig(rank=8, alpha=16.0, apply_to_text=True, apply_to_vision=False),
        gap=GapConfig(compute_every_n_epochs=1, compute_per_layer=False, sample_size=200),
        train=TrainConfig(dataset="coco", batch_size=a.batch, num_epochs=1,
                          learning_rate=a.lr, seed=42, use_amp=False,
                          save_dir=str(REPO / "outputs" / "diag_lora")))
    tr = GapAwareTrainer(cfg)
    tr.setup_model()

    print("=" * 100)
    print("1. which parameters are trainable")
    print("=" * 100)
    trainable = [(n, p) for n, p in tr.model.named_parameters() if p.requires_grad]
    print(f"  {len(trainable)} trainable tensors")
    for n, p in trainable[:8]:
        print(f"     {n:<70} {tuple(p.shape)}")
    if not trainable:
        print("  !! nothing is trainable")

    print()
    print("=" * 100)
    print("2. do they move when optimised directly on the contrastive loss")
    print("=" * 100)
    import copy
    before = {n: p.detach().clone() for n, p in trainable[:6]}
    params = [p for _, p in trainable]
    opt = torch.optim.AdamW(params, lr=a.lr)
    tr.model.train()
    it = iter(ds_loader)
    losses = []
    for step in range(a.steps):
        try:
            batch = next(it)
        except StopIteration:
            it = iter(ds_loader)
            batch = next(it)
        images = batch["image"].to(device)
        toks = tr.model.processor(text=batch["caption"], return_tensors="pt", padding=True,
                                  truncation=True, max_length=77)
        out = tr.model(pixel_values=images, input_ids=toks["input_ids"].to(device),
                       attention_mask=toks["attention_mask"].to(device))
        ie = F.normalize(out.image_embeds, p=2, dim=-1)
        te = F.normalize(out.text_embeds, p=2, dim=-1)
        scale = tr.model.model.logit_scale.exp()
        logits = scale * ie @ te.T
        labels = torch.arange(logits.shape[0], device=device)
        loss = (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) / 2
        opt.zero_grad()
        loss.backward()
        gnorm = sum(float(p.grad.norm()) for p in params if p.grad is not None)
        opt.step()
        losses.append(float(loss))
        if step % 10 == 0 or step == a.steps - 1:
            print(f"  step {step:>3}  loss = {float(loss):.4f}  logit_scale = {float(scale):.2f}  "
                  f"grad_norm = {gnorm:.4f}")

    print()
    print(f"  loss: first {losses[0]:.4f} -> last {losses[-1]:.4f}  "
          f"(change {losses[-1] - losses[0]:+.4f})")
    moved = sum(1 for n, _ in trainable[:6]
                if not torch.equal(before[n], dict(trainable)[n].detach()))
    print(f"  of the first 6 trainable tensors, {moved} changed")

    print()
    print("=" * 100)
    print("3. retrieval after these steps, corrected protocol")
    print("=" * 100)
    from _p754_coco_scaleup import evaluate
    vl = subset_loader("val", 300, 32, False, first=False, workers=4)
    met = evaluate(tr.model, vl, device)
    print(f"  R@1 = {met['R@1']:.4f}   R@5 = {met['R@5']:.4f}   R@10 = {met['R@10']:.4f}   "
          f"({met['n_unique_images']} images, {met['n_captions']} captions)")

    if a.apply:
        out = REPO / "outputs" / "analysis" / "diagnose_lora.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"trainable_tensors": len(trainable),
                                   "losses": losses, "retrieval": met},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
