# -*- coding: utf-8 -*-
r"""Establish the truth about the image-to-text branch, which still reports R@1 above 0.9.

The loop measurement and a plain argmax both gave i2t R@1 = 0.4203 on the frozen model over a
3,000-image gallery, while the chunked evaluate() reported 0.9157 for the same embeddings. The
chunked version was changed to accumulate a per-image flag, yet the scale-up still records 0.9324
for the fine-tuned runs, so either the fix did not take effect or the two are measuring different
things.

This recomputes i2t for one saved checkpoint with the three implementations side by side, and prints
the actual hit counts, so the discrepancy is located rather than argued about.

    python tools/_p790_i2t_truth.py --apply
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
OUT = REPO / "outputs" / "analysis" / "i2t_truth.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-images", type=int, default=3000)
    ap.add_argument("--batch", type=int, default=32)
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
    loader = subset_loader("val", a.eval_images, a.batch, False, first=False, workers=8)

    # load the s42 text_only checkpoint
    name = "coco_scaleup_text_only_r8_s42"
    cfg = ExperimentConfig(
        name=name, peft_method="lora",
        lora=LoRAConfig(rank=8, alpha=8.0, dropout=0.0, apply_to_text=True, apply_to_vision=False),
        gap=GapConfig(compute_every_n_epochs=1, compute_per_layer=False, sample_size=200),
        train=TrainConfig(dataset="coco", batch_size=64, num_epochs=3, learning_rate=1e-5,
                          seed=42, save_dir=str(REPO / "outputs" / "scaleup_coco" / name)))
    tr = GapAwareTrainer(cfg)
    tr.setup_model()
    ck = REPO / "outputs" / "scaleup_coco" / name / "best_checkpoint.pt"
    sd = torch.load(ck, map_location="cpu", weights_only=False)
    msd = tr.model.state_dict()
    loadable = {k: v for k, v in sd["trainable_state_dict"].items()
                if k in msd and msd[k].shape == v.shape}
    tr.model.load_state_dict(loadable, strict=False)
    print(f"  loaded {len(loadable)}/{len(sd['trainable_state_dict'])} tensors "
          f"(n_trainable_params recorded {sd['n_trainable_params']:,})")

    # embed once
    RI, T, owners = [], [], []
    with torch.no_grad():
        for b in loader:
            toks = proc(text=b["caption"], return_tensors="pt", padding=True, truncation=True,
                        max_length=77)
            o = tr.model(pixel_values=b["image"].to(device),
                         input_ids=toks["input_ids"].to(device),
                         attention_mask=toks["attention_mask"].to(device))
            RI.append(F.normalize(o.image_embeds, p=2, dim=-1).float().cpu())
            T.append(F.normalize(o.text_embeds, p=2, dim=-1).float().cpu())
            owners.extend([str(x) for x in b["image_path"]])
    RI = torch.cat(RI)
    T = torch.cat(T)
    order, first = [], {}
    for j, k in enumerate(owners):
        if k not in first:
            first[k] = j
            order.append(k)
    I = RI[[first[k] for k in order]]
    idx = {k: i for i, k in enumerate(order)}
    col = torch.tensor([idx[k] for k in owners])
    n_img, n_cap = I.shape[0], T.shape[0]
    print(f"  {n_img} images, {n_cap} captions")

    print()
    print("=" * 100)
    print("i2t under three implementations")
    print("=" * 100)
    # 1 loop
    t0 = time.time()
    hit = 0
    for i in range(n_img):
        top = torch.topk(I[i] @ T.T, 1).indices
        if (col[top] == i).any():
            hit += 1
    loop = hit / n_img
    print(f"  loop + topk          R@1 = {loop:.4f}   ({hit}/{n_img})   {time.time()-t0:.0f}s")

    # 2 chunked as currently written in evaluate()
    t0 = time.time()
    hits = torch.zeros(n_img, dtype=torch.bool)
    step = max(1, 500_000 // max(n_img, 1))
    for s in range(0, n_cap, step):
        sim = I @ T[s:s + step].T
        width = sim.shape[1]
        top = sim.topk(1, dim=1).indices
        own = col[s:s + width]
        hits |= (own[top] == torch.arange(n_img).unsqueeze(1)).any(dim=1)
        del sim, top
    chunked = float(hits.float().mean())
    print(f"  chunked (in evaluate) R@1 = {chunked:.4f}   ({int(hits.sum())}/{n_img})   "
          f"{time.time()-t0:.0f}s")

    # 3 what evaluate() actually returns
    met = evaluate(tr.model, loader, device, processor=proc)
    print(f"  evaluate() itself    R@1 = {met['R@1']:.4f}   i2t {met['R@1_i2t']:.4f}   "
          f"t2i {met['R@1_t2i']:.4f}")

    print()
    print("=" * 100)
    print("reading")
    print("=" * 100)
    same = abs(chunked - loop) < 1e-9
    print(f"  the chunked form matches the loop: {same}")
    if not same:
        print("  -> the difference is in how the per-image hit is accumulated, not in the data")
    print(f"  gallery is {n_img} unique images; an i2t R@1 around 0.9 would mean nearly every image")
    print(f"  has one of its own captions ranked first out of {n_cap} candidates, which the frozen")
    print(f"  model does not achieve (it scores {0.4203:.4f} on the same gallery).")

    res = {"n_images": int(n_img), "n_captions": int(n_cap), "i2t_loop": loop,
           "i2t_chunked": chunked, "i2t_evaluate": met["R@1_i2t"],
           "t2i_evaluate": met["R@1_t2i"], "R1_evaluate": met["R@1"],
           "loaded_tensors": len(loadable),
           "checkpoint_n_trainable": int(sd["n_trainable_params"])}
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
