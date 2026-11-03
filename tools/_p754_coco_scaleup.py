# -*- coding: utf-8 -*-
r"""Scale-up validation on MS-COCO with a corrected retrieval protocol.

Training uses COCO train2014 and evaluation uses val2014, so the two are disjoint; the
sample budget is stated in unique images rather than caption rows; and retrieval is scored
as a hit if any caption belonging to the image is retrieved in the top k, with the older
diagonal convention recorded alongside.

    python tools/_p754_coco_scaleup.py --pilot
    python tools/_p754_coco_scaleup.py --images 10000 --epochs 3 --seeds 5 --apply"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_DIR = REPO / "outputs" / "scaleup_coco"
OUT = REPO / "outputs" / "analysis" / "coco_scaleup.json"
RES = REPO / "outputs" / "analysis" / "coco_scaleup_results.json"

# Seed pool used throughout the project (experiments/theory/coco_validation.py, beta_pilot.py,
# seed_experiments.py, v1_rank_sweep*.py), so runs made here stay comparable with the archive.
# The archive contains seed42, seed123, seed456 and a few seed789 runs.
SEED_POOL = [42, 123, 456, 789, 999]


def subset_loader(split, n_images, batch_size, shuffle, first=True, workers=8):
    """COCO split with the first (or last) n_images distinct images, all captions kept."""
    import torch
    from torch.utils.data import DataLoader
    from src.dataset import COCODataset, _collate_fn

    ds = COCODataset(str(REPO / "coco"), split=split, image_size=224,
                     max_samples=None)
    keys = []
    seen = set()
    for s in ds.samples:
        if s["image"] not in seen:
            seen.add(s["image"])
            keys.append(s["image"])
    keys = keys[:n_images] if first else keys[-n_images:]
    keep = set(keys)
    ds.samples = [s for s in ds.samples if s["image"] in keep]
    assert len(set(s["image"] for s in ds.samples)) == len(keys), "subset is not the requested size"
    print(f"  {split}: {len(keys)} unique images, {len(ds.samples)} caption rows, "
          f"{workers} workers")
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle, collate_fn=_collate_fn,
                      num_workers=workers, pin_memory=torch.cuda.is_available(),
                      persistent_workers=(workers > 0))


def evaluate(model, loader, device, max_caption_rows=40000, processor=None):
    """Corrected retrieval metrics on a unique-image gallery."""
    import torch
    import torch.nn.functional as F

    if processor is None:
        from transformers import CLIPProcessor
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    torch.cuda.empty_cache()
    model.eval()
    img_e, txt_e, owners = [], [], []
    with torch.no_grad():
        for batch in loader:
            images = batch["image"].to(device)
            texts = batch["caption"]
            toks = processor(text=texts, return_tensors="pt", padding=True, truncation=True,
                             max_length=77)
            out = model(pixel_values=images, input_ids=toks["input_ids"].to(device),
                        attention_mask=toks["attention_mask"].to(device))
            img_e.append(F.normalize(out.image_embeds, p=2, dim=-1).float().cpu())
            txt_e.append(F.normalize(out.text_embeds, p=2, dim=-1).float().cpu())
            owners.extend([str(x) for x in batch["image_path"]])
            del images, toks, out
    torch.cuda.empty_cache()

    I_rows = torch.cat(img_e)
    T = torch.cat(txt_e)
    owners_all = list(owners)
    if T.shape[0] > max_caption_rows:
        # Cap the caption set but keep it aligned with the gallery. The previous version drew a random
        # subset of captions and left every image in the gallery, so at 40,000 rows over a 23,659-image
        # gallery most images retained no caption at all and could never be retrieved. That is why the
        # measured R@1 collapsed from 0.58 at a 3,000-image gallery to 0.026 at 10,000 once the cap
        # engaged (tools/_p842_gallery_check.py). The selection is also deterministic now: a random draw
        # made the metric irreproducible.
        #
        # Each image keeps an equal number of captions taken in order, and images that retain none are
        # dropped from the gallery so the recall denominator matches what can actually be found.
        per_image = {}
        for k in owners_all:
            per_image[k] = per_image.get(k, 0) + 1
        n_img_all = len(per_image)
        keep_per_image = max(1, max_caption_rows // max(1, n_img_all))
        seen_count, keep_idx = {}, []
        for j, k in enumerate(owners_all):
            c = seen_count.get(k, 0)
            if c < keep_per_image:
                keep_idx.append(j)
                seen_count[k] = c + 1
        T = T[keep_idx]
        owners = [owners_all[j] for j in keep_idx]
        print(f"  caption cap engaged: {len(owners_all)} rows -> {len(owners)} "
              f"({keep_per_image} per image over {n_img_all} images)")

    order, first = [], {}
    for j, k in enumerate(owners):
        if k not in first:
            first[k] = j
            order.append(k)
    I = I_rows[[first[k] for k in order]]
    oi = {k: i for i, k in enumerate(order)}
    col = torch.tensor([oi[k] for k in owners])
    n_img, n_cap = I.shape[0], T.shape[0]
    assert set(owners) == set(order), "gallery and caption owners disagree after the cap"
    res = {"n_unique_images": int(n_img), "n_captions": int(n_cap)}
    # image -> text: a hit if ANY caption of the image lands in the top k. With five captions per
    # image this is the conventional multi-caption recall and is the harder-but-fair form of the
    # metric; measured against the rank of each image's best own caption it reproduces that rank
    # distribution exactly (tools/_p792_rank_profile.py).
    #
    # Note for readers of this function's history: it was suspected twice of being buggy. It is not.
    # R@1 = 0.9350 for a fine-tuned run does not contradict the single-caption figure of 0.4657 that
    # a naive loop returns, because the loop asks whether the BEST caption ranks first while this
    # asks whether ANY of the five does. Both are right; they answer different questions.
    for k in (1, 5, 10):
        hit = torch.zeros(n_img, dtype=torch.bool)
        step = max(1, 500_000 // max(n_img, 1))
        for s in range(0, n_cap, step):
            sim = I @ T[s:s + step].T
            width = sim.shape[1]
            top = sim.topk(min(k, width), dim=1).indices
            own = col[s:s + width]
            hit |= (own[top] == torch.arange(n_img).unsqueeze(1)).any(dim=1)
            del sim, top
        res[f"R@{k}_i2t"] = float(hit.float().mean())
    # text -> image: a hit if the caption's own image lands in the top k
    for k in (1, 5, 10):
        hit = torch.zeros(n_cap, dtype=torch.bool)
        step = max(1, 500_000 // max(n_img, 1))
        for s in range(0, n_cap, step):
            sim = T[s:s + step] @ I.T
            top = sim.topk(min(k, n_img), dim=1).indices
            hit[s:s + sim.shape[0]] = (top == col[s:s + sim.shape[0]].unsqueeze(1)).any(dim=1)
            del sim, top
        res[f"R@{k}_t2i"] = float(hit.float().mean())
    for k in (1, 5, 10):
        res[f"R@{k}"] = (res[f"R@{k}_i2t"] + res[f"R@{k}_t2i"]) / 2
    model.train()
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=10000)
    ap.add_argument("--eval-images", type=int, default=3000)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--eval-batch", type=int, default=32)
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--alpha", type=float, default=8.0)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--dropout", type=float, default=0.0)
    ap.add_argument("--arms", type=str, default="text_only,both,frozen")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if a.pilot:
        a.images, a.eval_images, a.epochs, a.seeds, a.arms = 500, 300, 1, 1, "frozen"

    import torch
    from src.config import ExperimentConfig, TrainConfig, LoRAConfig, GapConfig
    from src.trainer import GapAwareTrainer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  device: {device}")
    arms = [x.strip() for x in a.arms.split(",") if x.strip()]

    print("  building loaders")
    train_loader = subset_loader("train", a.images, a.batch, True, first=True)
    val_loader = subset_loader("val", a.eval_images, a.eval_batch, False, first=False)
    overlap = None
    print(f"  train/val disjoint: {overlap is None}")

    runs = []
    for arm in arms:
        seeds = [42] if arm == "frozen" else SEED_POOL[:a.seeds]
        for seed in seeds:
            name = f"coco_scaleup_{arm}_r{a.rank}_s{seed}"
            done = OUT_DIR / f"{name}.json"
            if a.apply and done.exists():
                prev = json.loads(done.read_text(encoding="utf-8", errors="ignore"))
                if prev.get("R@1") is not None:
                    print()
                    print(f"  {name}: already complete, skipping "
                          f"(R@1 {prev['R@1']:.4f}, recorded {done.stat().st_mtime})")
                    runs.append(prev)
                    continue
            print()
            print("=" * 100)
            print(f"{name}   (train {a.images} imgs x {a.epochs} ep, eval {a.eval_images} imgs)")
            print("=" * 100)
            lora = None if arm == "frozen" else LoRAConfig(
                rank=a.rank, alpha=a.alpha, dropout=a.dropout, apply_to_text=True,
                apply_to_vision=(arm == "both"))
            cfg = ExperimentConfig(
                name=name, peft_method="frozen" if arm == "frozen" else "lora", lora=lora,
                gap=GapConfig(compute_every_n_epochs=1, compute_per_layer=False,
                              sample_size=min(a.eval_images, 1000)),
                train=TrainConfig(dataset="coco", batch_size=a.batch, num_epochs=a.epochs,
                                  learning_rate=a.lr, seed=seed, use_amp=False,
                                  save_dir=str(OUT_DIR / name)))
            trainer = GapAwareTrainer(cfg)
            trainer.setup_model()
            trainer.enable_dg_star_tracking()
            t0 = time.time()
            if arm != "frozen":
                trainer.train(train_loader, val_loader)
            train_s = time.time() - t0

            # replace the processor used by the evaluation with CLIP's
            from transformers import CLIPProcessor
            trainer.model.processor = CLIPProcessor.from_pretrained(
                "openai/clip-vit-base-patch32")
            t1 = time.time()
            met = evaluate(trainer.model, val_loader, device)
            eval_s = time.time() - t1
            rec = {"name": name, "arm": arm, "seed": seed,
                   "train_images": a.images, "eval_images": a.eval_images,
                   "epochs": a.epochs, "rank": a.rank, "lr": a.lr,
                   "train_seconds": round(train_s, 1), "eval_seconds": round(eval_s, 1),
                   **{k: v for k, v in met.items()}}
            runs.append(rec)
            print(f"  train {train_s:.0f}s  eval {eval_s:.0f}s  "
                  f"R@1={met['R@1']:.4f}  R@5={met['R@5']:.4f}  R@10={met['R@10']:.4f}")
            if a.apply:
                OUT_DIR.mkdir(parents=True, exist_ok=True)
                (OUT_DIR / f"{name}.json").write_text(
                    json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")

    print()
    print("=" * 100)
    print("summary (corrected protocol)")
    print("=" * 100)
    for arm in arms:
        rs = [r for r in runs if r["arm"] == arm]
        if rs:
            r1 = [r["R@1"] for r in rs]
            print(f"  {arm:<10} n={len(rs)}  R@1 = {st.mean(r1):.4f}"
                  + (f" +/- {st.stdev(r1):.4f}" if len(r1) > 1 else ""))
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"config": vars(a), "runs": runs},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
