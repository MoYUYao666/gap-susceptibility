# -*- coding: utf-8 -*-
r"""Explain the 0.4657 versus 0.9350 difference on the real embeddings, rather than guessing.

The synthetic test could not separate the two implementations because a hit is guaranteed there by
construction. This computes, on the real 3,000-image gallery, the actual rank of each image's best
own caption, which is a shape-only statistic that no top-k bookkeeping can distort.

If the median best-own-caption rank is small then most images do have one of their own captions near
the top, and a value near 0.9 is a real property of the embeddings rather than a bug.

    python tools/_p792_rank_profile.py --apply
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
OUT = REPO / "outputs" / "analysis" / "rank_profile.json"


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
    from _p754_coco_scaleup import subset_loader

    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    loader = subset_loader("val", a.eval_images, a.batch, False, first=False, workers=8)

    name = "coco_scaleup_text_only_r8_s42"
    cfg = ExperimentConfig(
        name=name, peft_method="lora",
        lora=LoRAConfig(rank=8, alpha=8.0, dropout=0.0, apply_to_text=True, apply_to_vision=False),
        gap=GapConfig(compute_every_n_epochs=1, compute_per_layer=False, sample_size=200),
        train=TrainConfig(dataset="coco", batch_size=64, num_epochs=3, learning_rate=1e-5,
                          seed=42, save_dir=str(REPO / "outputs" / "scaleup_coco" / name)))
    tr = GapAwareTrainer(cfg)
    tr.setup_model()
    sd = torch.load(REPO / "outputs" / "scaleup_coco" / name / "best_checkpoint.pt",
                    map_location="cpu", weights_only=False)
    msd = tr.model.state_dict()
    tr.model.load_state_dict({k: v for k, v in sd["trainable_state_dict"].items()
                              if k in msd and msd[k].shape == v.shape}, strict=False)

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
    RI, T = torch.cat(RI), torch.cat(T)
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

    # per-image rank of its best own caption, computed in blocks but with the rank taken globally
    S = I @ T.T
    ranks = torch.empty(n_img, dtype=torch.float)
    for i in range(n_img):
        best = S[i][col == i].max()
        ranks[i] = float((S[i] > best).sum()) + 1
    del S
    print()
    print("=" * 100)
    print("rank of each image's best own caption (out of 15,010 candidates)")
    print("=" * 100)
    for q in (1, 5, 10, 25, 50, 75, 90, 95, 99):
        print(f"  {q:>3}th percentile rank: {float(torch.quantile(ranks, q/100)):.0f}")
    print(f"  mean {float(ranks.mean()):.1f}   median {float(ranks.median()):.0f}")
    for thr in (1, 5, 10):
        frac = float((ranks <= thr).float().mean())
        print(f"  fraction of images whose best own caption ranks within top {thr:>2}: {frac:.4f}")

    res = {"n_images": int(n_img), "n_captions": int(n_cap),
           "median_best_rank": float(ranks.median()),
           "mean_best_rank": float(ranks.mean()),
           "frac_rank_le_1": float((ranks <= 1).float().mean()),
           "frac_rank_le_5": float((ranks <= 5).float().mean()),
           "frac_rank_le_10": float((ranks <= 10).float().mean())}
    print()
    print("  reading: 'fraction whose best own caption ranks within top k' IS the image-to-text R@k")
    print("  under the conventional protocol, computed without any top-k bookkeeping.")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
