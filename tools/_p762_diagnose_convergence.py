# -*- coding: utf-8 -*-
r"""Find out why LoRA fine-tuning does not converge on COCO.

Frozen CLIP scores R@1 = 0.48 (i2t) on COCO val under the corrected protocol, but two epochs of
text-only LoRA leave R@1 at 0.007 with the loss stuck near log(batch) = 3.47, the value a model
scores when it has learned nothing. Three hypotheses, tested in order of cost:

  H1  the optimiser is not actually updating the LoRA parameters
  H2  the learning rate is far too small for LoRA at rank 8
  H3  the training data itself is not learnable (caption/image misalignment in the train loader)

The decisive test is overfitting a tiny subset: a working pipeline drives the loss well below
log(batch) on 200 images within a few dozen steps. Reported alongside: the loss when only
logit_scale trains, which bounds how much of the loss is scale-related.

    python tools/_p762_diagnose_convergence.py --apply
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
OUT = REPO / "outputs" / "analysis" / "diagnose_convergence.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=200)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F
    from transformers import CLIPModel, CLIPProcessor
    from _p754_coco_scaleup import subset_loader

    device = "cuda" if torch.cuda.is_available() else "cpu"
    loader = subset_loader("train", a.images, a.batch, True, workers=4)
    print(f"  {a.images} train images, batch {a.batch}, {a.steps} steps")

    def run(mode, lr):
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
        proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        model.train()
        for p in model.parameters():
            p.requires_grad = False
        if mode == "logit_scale":
            model.logit_scale.requires_grad = True
            params = [model.logit_scale]
        elif mode == "proj":
            for n, p in model.named_parameters():
                if "projection" in n:
                    p.requires_grad = True
            params = [p for p in model.parameters() if p.requires_grad]
        else:  # full
            for p in model.parameters():
                p.requires_grad = True
            params = list(model.parameters())
        opt = torch.optim.AdamW(params, lr=lr)
        it = iter(loader)
        losses, gnorms = [], []
        for step in range(a.steps):
            try:
                b = next(it)
            except StopIteration:
                it = iter(loader)
                b = next(it)
            toks = proc(text=b["caption"], return_tensors="pt", padding=True, truncation=True,
                        max_length=77)
            out = model(pixel_values=b["image"].to(device),
                        input_ids=toks["input_ids"].to(device),
                        attention_mask=toks["attention_mask"].to(device))
            ie = F.normalize(out.image_embeds, p=2, dim=-1)
            te = F.normalize(out.text_embeds, p=2, dim=-1)
            logits = model.logit_scale.exp() * ie @ te.T
            labels = torch.arange(logits.shape[0], device=device)
            loss = (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) / 2
            opt.zero_grad()
            loss.backward()
            gn = sum(float(p.grad.norm()) for p in params if p.grad is not None)
            opt.step()
            losses.append(float(loss))
            gnorms.append(gn)
        return losses, gnorms

    results = {}
    print()
    for mode, lr in (("logit_scale", 1e-2), ("proj", 1e-3), ("full", 1e-5)):
        losses, gnorm = run(mode, lr)
        results[mode] = {"lr": lr, "first": losses[0], "last": losses[-1],
                         "min": min(losses), "grad_norm_first": gnorm[0],
                         "grad_norm_last": gnorm[-1]}
        print("=" * 100)
        print(f"{mode}  (lr={lr})")
        print("=" * 100)
        print(f"  loss {losses[0]:.4f} -> {losses[-1]:.4f}   (min {min(losses):.4f}, "
              f"log(batch) = {torch.log(torch.tensor(float(a.batch))):.3f})")
        print(f"  grad norm {gnorm[0]:.4f} -> {gnorm[-1]:.4f}")
        print(f"  first five losses: {[round(x, 3) for x in losses[:5]]}")
        print(f"  last five losses : {[round(x, 3) for x in losses[-5:]]}")
        print()

    print("=" * 100)
    print("verdict")
    print("=" * 100)
    import math
    chance = math.log(a.batch)
    for mode, r in results.items():
        drop = r["first"] - r["last"]
        print(f"  {mode:<12} drop = {drop:+.4f}   final {r['last']:.4f} vs chance {chance:.4f}  "
              f"=> {'LEARNING' if r['last'] < chance - 0.3 else 'NOT LEARING'}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
