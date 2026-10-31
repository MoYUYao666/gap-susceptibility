# -*- coding: utf-8 -*-
r"""Check whether the LoRA adapters are wired into the forward pass at all.

The plain model learns COCO captions easily: 60 steps on 200 images drive the contrastive loss from
0.88 to 0.25 with the projections trained, and even logit_scale alone fits the subset. The trainer's
LoRA path, by contrast, sits at loss 3.5-4.0 for two epochs, which is what a model scores when the
loss sees untrained representations.

So the question is whether apply_lora_to_model actually injects modules the forward pass calls. This
checks the wiring directly: compare the loss and embeddings before and after injection, and confirm
the adapter weights are read during a forward pass (by perturbing them and seeing the output move).

    python tools/_p763_lora_wiring.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT = REPO / "outputs" / "analysis" / "lora_wiring.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F
    from transformers import CLIPModel, CLIPProcessor
    from src.lora import apply_lora_to_model

    device = "cuda" if torch.cuda.is_available() else "cpu"
    mid = "openai/clip-vit-base-patch32"
    proc = CLIPProcessor.from_pretrained(mid)
    caps = ["a dog on grass", "two people and a bike", "a plate of pasta", "a red bus in traffic"]

    def forward(model):
        img = torch.zeros(len(caps), 3, 224, 224, device=device)
        toks = proc(text=caps, return_tensors="pt", padding=True, truncation=True, max_length=77)
        out = model(pixel_values=img, input_ids=toks["input_ids"].to(device),
                    attention_mask=toks["attention_mask"].to(device))
        return F.normalize(out.image_embeds, p=2, dim=-1), F.normalize(out.text_embeds, p=2, dim=-1)

    print("=" * 100)
    print("1. baseline model")
    print("=" * 100)
    base = CLIPModel.from_pretrained(mid).to(device).eval()
    with torch.no_grad():
        bi, bt = forward(base)
    print(f"  image embeds {tuple(bi.shape)}, text embeds {tuple(bt.shape)}")

    print()
    print("=" * 100)
    print("2. inject LoRA (text tower, rank 8) and see whether the forward pass changes")
    print("=" * 100)
    lora_model = CLIPModel.from_pretrained(mid).to(device).eval()
    n = apply_lora_to_model(lora_model, rank=8, alpha=16.0, dropout=0.0,
                            target_modules=["q_proj", "v_proj"],
                            apply_to_vision=False, apply_to_text=True)
    print(f"  apply_lora_to_model returned: {n}")
    lora_params = [(nm, p) for nm, p in lora_model.named_parameters() if "lora_" in nm]
    print(f"  {len(lora_params)} lora tensors present")
    for nm, p in lora_params[:6]:
        print(f"     {nm:<70} {tuple(p.shape)}  requires_grad={p.requires_grad}")

    with torch.no_grad():
        li, lt = forward(lora_model)
    d_t = float((lt - bt).abs().max())
    d_i = float((li - bi).abs().max())
    print(f"  text embeddings changed by max {d_t:.6f}; image embeddings by max {d_i:.6f}")
    print(f"  -> the adapter {'IS' if d_t > 1e-6 else 'IS NOT'} read by the forward pass")

    print()
    print("=" * 100)
    print("3. perturb the adapters and see whether the loss responds")
    print("=" * 100)
    with torch.no_grad():
        for nm, p in lora_params:
            p.add_(torch.randn_like(p) * 0.05)
        pi, pt = forward(lora_model)
    print(f"  after perturbation, text embeddings changed by max "
          f"{float((pt - lt).abs().max()):.6f}")
    print(f"  image embeddings changed by max {float((pi - li).abs().max()):.6f}")

    print()
    print("=" * 100)
    print("4. is the trainer's model the same object the loss is built from?")
    print("=" * 100)
    from src.config import ExperimentConfig, TrainConfig, LoRAConfig, GapConfig
    from src.trainer import GapAwareTrainer
    cfg = ExperimentConfig(name="wire", peft_method="lora",
                           lora=LoRAConfig(rank=8, alpha=16.0, apply_to_text=True,
                                           apply_to_vision=False),
                           gap=GapConfig(compute_every_n_epochs=1, compute_per_layer=False,
                                         sample_size=100),
                           train=TrainConfig(dataset="coco", batch_size=8, num_epochs=1,
                                             save_dir=str(REPO / "outputs" / "wire")))
    tr = GapAwareTrainer(cfg)
    tr.setup_model()
    tp = [(nm, p) for nm, p in tr.model.named_parameters() if "lora_" in nm]
    print(f"  trainer model has {len(tp)} lora tensors; "
          f"trainable total = {sum(1 for p in tr.model.parameters() if p.requires_grad)}")
    # does the trainer's forward see them?
    img = torch.zeros(4, 3, 224, 224, device=device)
    toks = tr.model.processor(text=caps, return_tensors="pt", padding=True, truncation=True,
                              max_length=77)
    with torch.no_grad():
        out = tr.model(pixel_values=img, input_ids=toks["input_ids"].to(device),
                       attention_mask=toks["attention_mask"].to(device))
        t0 = F.normalize(out.text_embeds, p=2, dim=-1)
        for nm, p in tp:
            p.add_(torch.randn_like(p) * 0.1)
        out2 = tr.model(pixel_values=img, input_ids=toks["input_ids"].to(device),
                        attention_mask=toks["attention_mask"].to(device))
        t1 = F.normalize(out2.text_embeds, p=2, dim=-1)
    print(f"  perturbing the trainer's lora tensors changed its text embeddings by max "
          f"{float((t1 - t0).abs().max()):.6f}")
    print(f"  -> the trainer's forward pass {'DOES' if float((t1-t0).abs().max()) > 1e-6 else 'DOES NOT'}"
          f" read the adapters")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"n_lora_tensors": len(lora_params),
                                   "text_embed_delta": d_t, "image_embed_delta": d_i,
                                   "trainer_lora_tensors": len(tp)},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
