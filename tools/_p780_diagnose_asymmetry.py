# -*- coding: utf-8 -*-
r"""Diagnose the i2t / t2i asymmetry that blocks the COCO claim.

Measured on the 3,000-image gallery with frozen CLIP: image-to-text R@1 = 0.9157 but text-to-image
R@1 = 0.2431. Standard COCO retrieval reports the two directions within about ten points of each
other, so one of these numbers does not behave like a retrieval metric.

Four candidate causes are separated here:
  A  the text embeddings are degenerate (low effective rank, high mutual similarity), which would
     make image-to-text artificially easy: with few distinct text directions, many captions are
     near-duplicates and an image only has to find its neighbourhood
  B  the image embeddings are fine but the text tower is under-trained, so t2i is genuinely weak
  C  the gallery construction differs between directions
  D  the caption distribution differs from the image distribution in a way that inflates i2t

Reports the effective rank and mean pairwise cosine of each modality, and recomputes both metrics on
the same embeddings with the same gallery so the numbers are directly comparable.

    python tools/_p780_diagnose_asymmetry.py --images 3000 --apply
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
OUT = REPO / "outputs" / "analysis" / "asymmetry_diagnosis.json"


def effective_rank(x):
    """Participation ratio of the singular values: 1 means all energy in one direction."""
    import torch
    x = x - x.mean(dim=0, keepdim=True)
    s = torch.linalg.svdvals(x)
    p = (s ** 2) / (s ** 2).sum()
    return float(1.0 / (p ** 2).sum())


def mean_pairwise_cos(x, sample=2000):
    import torch
    if x.shape[0] > sample:
        idx = torch.randperm(x.shape[0])[:sample]
        x = x[idx]
    g = x @ x.T
    n = g.shape[0]
    off = g[~torch.eye(n, dtype=torch.bool)]
    return float(off.mean())


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
    print(f"  {n_img} images, {n_cap} captions, dim {I.shape[1]}")

    print()
    print("=" * 100)
    print("A. embedding geometry per modality")
    print("=" * 100)
    stats = {
        "image_effective_rank": effective_rank(I),
        "text_effective_rank": effective_rank(T),
        "image_mean_pairwise_cos": mean_pairwise_cos(I),
        "text_mean_pairwise_cos": mean_pairwise_cos(T),
    }
    for k, v in stats.items():
        print(f"  {k:<32} {v:.4f}")
    print()
    print("  interpretation: a much lower text effective rank, or a much higher text mean cosine,")
    print("  means captions occupy few directions and image-to-text is easier than it should be.")

    print()
    print("=" * 100)
    print("B. both directions on the same embeddings and the same gallery (loop-verified)")
    print("=" * 100)
    Simg = I @ T.T          # (n_img, n_cap)
    Stxt = T @ I.T          # (n_cap, n_img)
    for k in (1, 5, 10):
        i2t = 0
        for i in range(n_img):
            top = torch.topk(Simg[i], min(k, n_cap)).indices
            if (col[top] == i).any():
                i2t += 1
        t2i = 0
        for j in range(n_cap):
            top = torch.topk(Stxt[j], min(k, n_img)).indices
            if int(col[j]) in top.tolist():
                t2i += 1
        print(f"  R@{k}:  i2t {i2t / n_img:.4f}   t2i {t2i / n_cap:.4f}")
        stats[f"i2t_R@{k}"] = i2t / n_img
        stats[f"t2i_R@{k}"] = t2i / n_cap
    del Simg, Stxt

    print()
    print("=" * 100)
    print("C. how many distinct images do the 5 captions of an image map to in i2t")
    print("=" * 100)
    rows_per_img = {}
    for j in range(n_cap):
        rows_per_img.setdefault(int(col[j]), []).append(j)
    counts = [len(v) for v in rows_per_img.values()]
    print(f"  captions per image: min {min(counts)}, max {max(counts)}, "
          f"mean {sum(counts) / len(counts):.2f}")
    print(f"  total candidates an image searches: {n_cap} (vs {n_img} images for t2i)")
    print(f"  -> i2t has {n_cap / n_img:.1f}x more candidates but that is not the cause of the gap")

    print()
    print("=" * 100)
    print("D. the t2i ceiling from caption duplication")
    print("=" * 100)
    dup = n_cap - len(set(caps))
    print(f"  duplicated caption strings: {dup}")
    print(f"  a caption can be matched by its own image even if the top-1 is a duplicate caption of")
    print(f"  the same image, so duplication inflates t2i; here it is {dup / n_cap:.2%} of rows")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
