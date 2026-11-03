# -*- coding: utf-8 -*-
r"""A large-scale, corrected retrieval reference point: frozen CLIP on 10,000 COCO val images.

Reviewer R1-W4 asked the retrieval protocol to be verified before any cross-model conclusion, and
R2-3 asked for a larger dataset. The archive's COCO numbers are R@1 < 0.001 with an evaluation set
built from 10,000 caption rows (about 2,000 distinct images) and scored with a convention that the
caption multiplicity breaks.

This evaluates frozen CLIP on 10,000 distinct val2014 images with all their captions - five times
the images the archive used - under the corrected protocol, and also reports the old diagonal figure
on the same embeddings so the difference is measured rather than asserted.

    python tools/_p756_frozen_reference.py --images 10000 --apply
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
OUT = REPO / "outputs" / "analysis" / "frozen_reference_large.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=10000)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F
    from transformers import CLIPModel, CLIPProcessor
    from _p754_coco_scaleup import subset_loader

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device).eval()
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    print(f"  device {device}; evaluating frozen CLIP on {a.images} val images")
    loader = subset_loader("val", a.images, a.batch, False, first=False, workers=8)

    img_e, txt_e, owners = [], [], []
    t0 = time.time()
    with torch.no_grad():
        for bi, batch in enumerate(loader):
            toks = proc(text=batch["caption"], return_tensors="pt", padding=True,
                        truncation=True, max_length=77)
            out = model(pixel_values=batch["image"].to(device),
                        input_ids=toks["input_ids"].to(device),
                        attention_mask=toks["attention_mask"].to(device))
            img_e.append(F.normalize(out.image_embeds, p=2, dim=-1).float().cpu())
            txt_e.append(F.normalize(out.text_embeds, p=2, dim=-1).float().cpu())
            owners.extend([str(x) for x in batch["image_path"]])
            if bi % 50 == 0:
                print(f"     batch {bi}, {time.time() - t0:.0f}s")
    I_rows = torch.cat(img_e)
    T = torch.cat(txt_e)
    print(f"  embedded {len(owners)} rows in {time.time() - t0:.0f}s")

    order, first = [], {}
    for j, k in enumerate(owners):
        if k not in first:
            first[k] = j
            order.append(k)
    I = I_rows[[first[k] for k in order]]
    oi = {k: i for i, k in enumerate(order)}
    col = torch.tensor([oi[k] for k in owners])
    n_img, n_cap = I.shape[0], T.shape[0]
    print(f"  gallery: {n_img} unique images, {n_cap} captions")

    res = {"n_images": int(n_img), "n_captions": int(n_cap),
           "seconds_embed": round(time.time() - t0, 1)}

    # corrected protocol
    for k in (1, 5, 10):
        hit = torch.zeros(n_img, dtype=torch.bool)
        step = max(1, 300_000 // max(n_img, 1))
        for s in range(0, n_cap, step):
            sim = I @ T[s:s + step].T
            top = sim.topk(min(k, sim.shape[1]), dim=1).indices
            hit |= (col[s:s + sim.shape[1]][top] == torch.arange(n_img).unsqueeze(1)).any(dim=1)
            del sim, top
        res[f"R@{k}_i2t"] = float(hit.float().mean())
    for k in (1, 5, 10):
        hit = torch.zeros(n_cap, dtype=torch.bool)
        step = max(1, 300_000 // max(n_img, 1))
        for s in range(0, n_cap, step):
            sim = T[s:s + step] @ I.T
            top = sim.topk(min(k, n_img), dim=1).indices
            hit[s:s + sim.shape[0]] = (top == col[s:s + sim.shape[0]].unsqueeze(1)).any(dim=1)
            del sim, top
        res[f"R@{k}_t2i"] = float(hit.float().mean())
    for k in (1, 5, 10):
        res[f"R@{k}"] = (res[f"R@{k}_i2t"] + res[f"R@{k}_t2i"]) / 2

    # the archive's convention on the same embeddings, for comparison
    N = min(I_rows.shape[0], T.shape[0])
    S = I_rows[:N] @ T[:N].T
    for k in (1, 5, 10):
        top = S.topk(k, dim=1).indices
        res[f"old_R@{k}"] = float((top == torch.arange(N).unsqueeze(1)).any(dim=1).float().mean())
    del S

    print()
    print("=" * 100)
    print(f"frozen CLIP, {n_img} val images, {n_cap} captions")
    print("=" * 100)
    for k in (1, 5, 10):
        print(f"  R@{k}:  corrected {res[f'R@{k}']:.4f}  (i2t {res[f'R@{k}_i2t']:.4f} / "
              f"t2i {res[f'R@{k}_t2i']:.4f})   old convention {res[f'old_R@{k}']:.4f}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
