# -*- coding: utf-8 -*-
r"""Verify the two retrieval directions on concrete examples.

Padding is not the cause: padding_side is right and all three padding modes give identical
embeddings. So one of the two numbers is wrong. image->text R@1 = 0.9957 is higher than CLIP ViT-B/32
achieves on COCO in the literature, which suggests the image side is being scored too generously.

This prints, for a handful of captions, which image ranks first and whether that image is the
caption's own, so the direction that is wrong can be identified directly.

    python tools/_p758_direction_check.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "direction_check.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=2000)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F
    from transformers import CLIPModel, CLIPProcessor
    sys.path.insert(0, str(REPO / "tools"))
    from _p754_coco_scaleup import subset_loader

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device).eval()
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    loader = subset_loader("val", a.images, a.batch, False, first=False, workers=8)

    I_rows, T, owners, caps = [], [], [], []
    with torch.no_grad():
        for b in loader:
            toks = proc(text=b["caption"], return_tensors="pt", padding=True, truncation=True,
                        max_length=77)
            out = model(pixel_values=b["image"].to(device),
                        input_ids=toks["input_ids"].to(device),
                        attention_mask=toks["attention_mask"].to(device))
            I_rows.append(F.normalize(out.image_embeds, p=2, dim=-1).float().cpu())
            T.append(F.normalize(out.text_embeds, p=2, dim=-1).float().cpu())
            owners.extend([str(x) for x in b["image_path"]])
            caps.extend(list(b["caption"]))
    I_rows = torch.cat(I_rows)
    T = torch.cat(T)
    order, first = [], {}
    for j, k in enumerate(owners):
        if k not in first:
            first[k] = j
            order.append(k)
    I = I_rows[[first[k] for k in order]]
    oi = {k: i for i, k in enumerate(order)}
    col = torch.tensor([oi[k] for k in owners])
    n_img, n_cap = I.shape[0], T.shape[0]
    print(f"  {n_img} images, {n_cap} captions")

    print()
    print("=" * 100)
    print("text -> image: for five captions, which image ranks first")
    print("=" * 100)
    for j in [0, 1, 2, 3, 4]:
        sim = T[j] @ I.T
        top = int(sim.argmax())
        own = int(col[j])
        print(f"  caption {j}: own image {own}, top-1 {top}  "
              f"{'HIT' if top == own else 'MISS'}  sim_own={float(sim[own]):.4f} "
              f"sim_top={float(sim[top]):.4f}")
        print(f"     \"{caps[j][:80]}\"")

    print()
    print("=" * 100)
    print("image -> text: for five images, how many of its own captions are in the top 10")
    print("=" * 100)
    for i in [0, 1, 2, 3, 4]:
        sim = I[i] @ T.T
        top = sim.topk(10).indices
        own_rows = (col == i).nonzero().flatten()
        n_own_in_top10 = int((col[top] == i).sum())
        print(f"  image {i}: {len(own_rows)} own captions, {n_own_in_top10} of them in the top 10; "
              f"best own rank = {int((sim > sim[own_rows].max()).sum()) + 1}")

    print()
    print("=" * 100)
    print("gallery sanity: is any image duplicated in the gallery?")
    print("=" * 100)
    print(f"  unique keys = {len(set(owners))}, rows = {len(owners)}, "
          f"gallery rows = {n_img}")
    print(f"  images per key: min={min((col == i).sum().item() for i in range(min(n_img, 500)))}, "
          f"max={max((col == i).sum().item() for i in range(min(n_img, 500)))}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"n_images": int(n_img), "n_captions": int(n_cap)},
                                  indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
