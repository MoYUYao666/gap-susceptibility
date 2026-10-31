# -*- coding: utf-8 -*-
r"""Final measurement of the retrieval conventions using per-example loops only.

Vectorised versions disagreed with each other and with per-example inspection, so this
computes each metric with an explicit loop over examples and no block algebra. It reports
the archive's diagonal convention, image-to-text, and text-to-image side by side.

    python tools/_p760_loop_measure.py --images 2000 --apply"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "loop_measure.json"


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

    RI, T, owners = [], [], []
    t0 = time.time()
    with torch.no_grad():
        for b in loader:
            toks = proc(text=b["caption"], return_tensors="pt", padding=True, truncation=True,
                        max_length=77)
            o = model(pixel_values=b["image"].to(device),
                      input_ids=toks["input_ids"].to(device),
                      attention_mask=toks["attention_mask"].to(device))
            RI.append(F.normalize(o.image_embeds, p=2, dim=-1).float().cpu())
            T.append(F.normalize(o.text_embeds, p=2, dim=-1).float().cpu())
            owners.extend([str(x) for x in b["image_path"]])
    RI = torch.cat(RI)
    T = torch.cat(T)
    print(f"  embedded in {time.time() - t0:.0f}s")

    order, first = [], {}
    for j, k in enumerate(owners):
        if k not in first:
            first[k] = j
            order.append(k)
    idx_of = {k: i for i, k in enumerate(order)}
    n_img, n_cap = len(order), len(owners)
    img_of_row = [idx_of[k] for k in owners]
    rows_of_img = {}
    for j, i in enumerate(img_of_row):
        rows_of_img.setdefault(i, []).append(j)
    print(f"  {n_img} unique images, {n_cap} caption rows")

    # gallery and query matrices in the same order
    I = RI[[first[k] for k in order]]            # (n_img, d)
    res = {"n_images": int(n_img), "n_rows": int(n_cap)}

    print()
    print("=" * 96)
    print("t2i: for each caption row, is its own image in the top k  (loop)")
    print("=" * 96)
    S_t2i = T @ I.T                               # (n_cap, n_img)
    for k in (1, 5, 10):
        hit = 0
        for j in range(n_cap):
            top = torch.topk(S_t2i[j], min(k, n_img)).indices.tolist()
            if img_of_row[j] in top:
                hit += 1
        res[f"t2i_R@{k}"] = hit / n_cap
        print(f"  R@{k} = {hit / n_cap:.4f}   ({hit}/{n_cap})")
    del S_t2i

    print()
    print("=" * 96)
    print("i2t: for each image, is any of its own captions in the top k  (loop)")
    print("=" * 96)
    S_i2t = I @ T.T                               # (n_img, n_cap)
    for k in (1, 5, 10):
        hit = 0
        for i in range(n_img):
            top = torch.topk(S_i2t[i], min(k, n_cap)).indices.tolist()
            if any(img_of_row[t] == i for t in top):
                hit += 1
        res[f"i2t_R@{k}"] = hit / n_img
        print(f"  R@{k} = {hit / n_img:.4f}   ({hit}/{n_img})")
    del S_i2t

    print()
    print("=" * 96)
    print("diagonal: row i's caption against row i's image  (loop, the archive's convention)")
    print("=" * 96)
    Sd = RI @ T.T
    for k in (1, 5, 10):
        hit = 0
        for i in range(len(owners)):
            top = torch.topk(Sd[i], min(k, len(owners))).indices.tolist()
            if i in top:
                hit += 1
        res[f"diagonal_R@{k}"] = hit / len(owners)
        print(f"  R@{k} = {hit / len(owners):.4f}   ({hit}/{len(owners)})")
    del Sd

    print()
    print("=" * 96)
    print("examples for hand-checking")
    print("=" * 96)
    for j in range(4):
        sim = T[j] @ I.T
        own = img_of_row[j]
        print(f"  caption row {j}: own image {own}, argmax {int(sim.argmax())}, "
              f"own rank {int((sim > sim[own]).sum()) + 1}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
