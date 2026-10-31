# -*- coding: utf-8 -*-
r"""Resolve the contradiction between the chunked evaluation (i2t 0.9293) and the loop (i2t 0.4203).

Both were run on the same frozen model over the same 3,000-image / 15,010-caption gallery, yet they
disagree by more than a factor of two. One of them is wrong, and the large-scale claim rests on the
chunked one.

This computes i2t three independent ways on identical embeddings:
  1. the loop used in _p780
  2. the chunked form used in _p754's evaluate()
  3. an explicit per-image argmax with no topk
and also reports the mean rank of an image's own captions, which is a shape-only statistic that
cannot be fooled by a top-k bug.

    python tools/_p781_resolve_contradiction.py --images 3000 --apply
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
OUT = REPO / "outputs" / "analysis" / "asymmetry_resolved.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=3000)
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
    loader = subset_loader("val", a.images, a.batch, False, first=False, workers=8)

    RI, T, owners, caps = [], [], [], []
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
            caps.extend(list(b["caption"]))
    RI = torch.cat(RI)
    T = torch.cat(T)
    order, first = [], {}
    for j, k in enumerate(owners):
        if k not in first:
            first[k] = j
            order.append(k)
    I = RI[[first[k] for k in order]]
    oi = {k: i for i, k in enumerate(order)}
    col = torch.tensor([oi[k] for k in owners])
    n_img, n_cap = I.shape[0], T.shape[0]
    print(f"  {n_img} images, {n_cap} captions")
    print(f"  owner ids range: {int(col.min())} .. {int(col.max())}")
    print(f"  first 8 owners: {owners[:8]}")
    print(f"  first 8 owner ids: {col[:8].tolist()}")

    S = I @ T.T      # (n_img, n_cap)

    print()
    print("=" * 100)
    print("i2t, three independent computations")
    print("=" * 100)
    # 1. loop with topk
    hit = 0
    for i in range(n_img):
        top = torch.topk(S[i], 1).indices
        if (col[top] == i).any():
            hit += 1
    print(f"  1. loop + topk            R@1 = {hit / n_img:.4f}   ({hit}/{n_img})")
    # 2. chunked form as in _p754's evaluate()
    hits = 0
    step = max(1, 300_000 // max(n_img, 1))
    for s in range(0, n_cap, step):
        sim = I @ T[s:s + step].T
        width = sim.shape[1]
        top = sim.topk(min(1, width), dim=1).indices
        own = col[s:s + width]
        img_ids = torch.arange(n_img)
        hits += int((own[top[:, :1]] == img_ids.unsqueeze(1)).any(dim=1).sum())
        del sim, top
    print(f"  2. chunked (as in evaluate) R@1 = {hits / n_img:.4f}   ({hits}/{n_img})")
    # 3. argmax only
    am = S.argmax(dim=1)
    hit3 = int((col[am] == torch.arange(n_img)).sum())
    print(f"  3. plain argmax             R@1 = {hit3 / n_img:.4f}   ({hit3}/{n_img})")

    print()
    print("=" * 100)
    print("mean rank of an image's own captions (shape-only statistic)")
    print("=" * 100)
    best = []
    for i in range(0, n_img, max(1, n_img // 300)):
        own = (col == i).nonzero().flatten()
        m = S[i][own].max()
        rank = int((S[i] > m).sum()) + 1
        best.append(rank)
    best_t = torch.tensor(best, dtype=torch.float)
    print(f"  sampled {len(best)} images: mean best own-caption rank = {best_t.mean():.1f}, "
          f"median = {best_t.median():.1f}, min = {best_t.min():.0f}, max = {best_t.max():.0f}")
    print(f"  random baseline rank = {n_cap / 2:.0f}")

    print()
    print("=" * 100)
    print("t2i for comparison")
    print("=" * 100)
    St = T @ I.T
    amt = St.argmax(dim=1)
    print(f"  t2i plain argmax R@1 = {float((amt == col).float().mean()):.4f}")
    own_rank = []
    for j in range(0, n_cap, max(1, n_cap // 300)):
        m = St[j][int(col[j])]
        own_rank.append(int((St[j] > m).sum()) + 1)
    ort = torch.tensor(own_rank, dtype=torch.float)
    print(f"  sampled {len(own_rank)} captions: mean own-image rank = {ort.mean():.1f}, "
          f"median = {ort.median():.1f}")
    print(f"  random baseline rank = {n_img / 2:.0f}")

    res = {"n_images": int(n_img), "n_captions": int(n_cap),
           "i2t_loop_R1": hit / n_img, "i2t_chunked_R1": hits / n_img, "i2t_argmax_R1": hit3 / n_img,
           "i2t_mean_best_rank": float(best_t.mean()), "i2t_median_best_rank": float(best_t.median()),
           "t2i_argmax_R1": float((amt == col).float().mean()),
           "t2i_mean_own_rank": float(ort.mean())}
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
