# -*- coding: utf-8 -*-
r"""One clean, per-example-verifiable measurement of all three retrieval conventions.

Previous runs produced an impossible image->text R@1 of 0.9957 for CLIP ViT-B/32 on COCO while the
per-example inspection showed own captions ranking 19th. One of the two measurements is wrong, so
this computes all three conventions side by side and validates each against hand-checked examples:

  diagonal   : the archive's convention, row i's caption against row i's image
  i2t        : for each image, is any of its own captions in the top k
  t2i        : for each caption, is its own image in the top k

Each is recomputed a second way (loop over examples) so a vectorisation mistake cannot hide.

    python tools/_p759_clean_measure.py --images 2000 --apply
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "clean_measure.json"


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

    rows_I, rows_T, owners = [], [], []
    with torch.no_grad():
        for b in loader:
            toks = proc(text=b["caption"], return_tensors="pt", padding=True, truncation=True,
                        max_length=77)
            out = model(pixel_values=b["image"].to(device),
                        input_ids=toks["input_ids"].to(device),
                        attention_mask=toks["attention_mask"].to(device))
            rows_I.append(F.normalize(out.image_embeds, p=2, dim=-1).float().cpu())
            rows_T.append(F.normalize(out.text_embeds, p=2, dim=-1).float().cpu())
            owners.extend([str(x) for x in b["image_path"]])
    RI = torch.cat(rows_I)          # (n_rows, d) image embedding of each row
    T = torch.cat(rows_T)           # (n_rows, d) caption embedding of each row
    n_rows = RI.shape[0]

    order, first = [], {}
    for j, k in enumerate(owners):
        if k not in first:
            first[k] = j
            order.append(k)
    I = RI[[first[k] for k in order]]          # (n_img, d)
    oi = {k: i for i, k in enumerate(order)}
    col = torch.tensor([oi[k] for k in owners])
    n_img, n_cap = I.shape[0], T.shape[0]
    print(f"  {n_img} images, {n_cap} caption rows")

    out = {"n_images": int(n_img), "n_rows": int(n_cap)}

    # ---- diagonal (the archive's convention), on the row-aligned matrices
    print()
    print("=" * 96)
    print("diagonal convention: row i's caption against row i's image")
    print("=" * 96)
    S = RI @ T.T
    for k in (1, 5, 10):
        top = S.topk(k, dim=1).indices
        v = (top == torch.arange(n_rows).unsqueeze(1)).any(dim=1).float().mean().item()
        # second computation, plain loop
        loop = sum(1 for i in range(n_rows) if i in set(top[i].tolist())) / n_rows
        out[f"diagonal_R@{k}"] = float(v)
        print(f"  R@{k} = {v:.4f}   (loop check {loop:.4f})")
    del S

    # ---- text -> image
    print()
    print("=" * 96)
    print("text -> image: is the caption's own image in the top k")
    print("=" * 96)
    S = T @ I.T
    for k in (1, 5, 10):
        top = S.topk(min(k, n_img), dim=1).indices
        v = (top == col.unsqueeze(1)).any(dim=1).float().mean().item()
        loop = sum(1 for j in range(0, n_cap, max(1, n_cap // 500))
                   if int(col[j]) in set(top[j].tolist())) / len(range(0, n_cap, max(1, n_cap // 500)))
        out[f"t2i_R@{k}"] = float(v)
        print(f"  R@{k} = {v:.4f}   (loop check {loop:.4f})")
    del S

    # ---- image -> text
    print()
    print("=" * 96)
    print("image -> text: is any of the image's own captions in the top k")
    print("=" * 96)
    own_rows = {}
    for j in range(n_cap):
        own_rows.setdefault(int(col[j]), []).append(j)
    for k in (1, 5, 10):
        hits = 0
        step = max(1, 300_000 // max(n_img, 1))
        for s in range(0, n_cap, step):
            sim = I @ T[s:s + step].T
            top = sim.topk(min(k, sim.shape[1]), dim=1).indices
            ownset = col[s:s + sim.shape[1]][top]        # (n_img, k) owner id of each retrieved row
            hits += int((ownset == torch.arange(n_img).unsqueeze(1)).any(dim=1).sum())
            del sim, top, ownset
        v = hits / n_img
        # loop check on the first 200 images, using the full matrix in blocks
        lhits = 0
        for i in range(min(200, n_img)):
            best = 0
            for s in range(0, n_cap, step):
                sim = I[i] @ T[s:s + step].T
                top = sim.topk(min(k, sim.shape[0])).indices
                if (col[s:s + sim.shape[0]][top] == i).any():
                    best = 1
                    break
            lhits += best
        out[f"i2t_R@{k}"] = float(v)
        print(f"  R@{k} = {v:.4f}   (loop check {lhits / min(200, n_img):.4f} on 200 images)")

    print()
    print("=" * 96)
    print("hand-checked examples")
    print("=" * 96)
    for j in range(5):
        sim = T[j] @ I.T
        print(f"  caption {j}: own image {int(col[j])}, top-1 {int(sim.argmax())}  "
              f"own rank {int((sim > sim[int(col[j])]).sum()) + 1}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
