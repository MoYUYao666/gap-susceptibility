# -*- coding: utf-8 -*-
r"""Full-scale COCO validation: the largest evaluation this repository can actually support.

Reviewer R2-3 asks for broader validation on larger datasets. No new dataset is required: the
existing runs used 3,000 of the 40,504 available COCO val images, because the loader truncated on
caption rows rather than images. This evaluates on the full val2014 split.

Configuration is the one already validated in this session, so the only variable is scale:
  frozen CLIP ViT-B/32, and the adapter-only configuration with the base frozen, rank 8, text-only,
  three seeds (42, 123, 456), fresh LoRA adapter with all 196,608 parameters trainable.

Retrieval is scored with the corrected protocol: a hit if any caption belonging to the image is
retrieved among the top k, over a unique-image gallery, both directions, with the rank of each
image's best caption reported as an implementation-independent cross-check.

    python tools/_p818_full_coco.py --eval-only
    python tools/_p818_full_coco.py --apply
"""
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
sys.path.insert(0, str(REPO / "tools"))
OUT_DIR = REPO / "outputs" / "full_coco"
OUT = REPO / "outputs" / "analysis" / "full_coco.json"
SEED_POOL = [42, 123, 456]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-images", type=int, default=10000)
    ap.add_argument("--eval-images", type=int, default=0, help="0 means all of val2014")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--eval-batch", type=int, default=32)
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--eval-only", action="store_true", help="frozen baseline only, no training")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F
    from transformers import CLIPModel, CLIPProcessor
    from src.config import ExperimentConfig, TrainConfig, LoRAConfig, GapConfig
    from src.trainer import GapAwareTrainer
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "fl", str(REPO / "tools" / "_p754_coco_scaleup.py"))
    fl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fl)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    # every val2014 image with its captions
    n_eval = a.eval_images if a.eval_images > 0 else 10 ** 9
    val_loader = fl.subset_loader("val", n_eval, a.eval_batch, False, first=False, workers=8)
    print(f"  full-scale evaluation built; device {device}")

    def evaluate_model(model):
        t0 = time.time()
        met = fl.evaluate(model, val_loader, device, max_caption_rows=300000, processor=proc)
        met["seconds"] = round(time.time() - t0, 1)
        return met

    results = {"config": vars(a), "runs": []}

    # ---- frozen baseline, no training ----
    print()
    print("=" * 100)
    print("frozen CLIP, full val2014 gallery")
    print("=" * 100)
    frozen = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device).eval()
    fz = evaluate_model(frozen)
    print(f"  {fz['n_unique_images']} images / {fz['n_captions']} captions in {fz['seconds']}s")
    print(f"  R@1 {fz['R@1']:.4f}  R@5 {fz['R@5']:.4f}  R@10 {fz['R@10']:.4f}  "
          f"(i2t {fz['R@1_i2t']:.4f} / t2i {fz['R@1_t2i']:.4f})")
    results["runs"].append({"arm": "frozen", "seed": None, **fz})
    del frozen
    torch.cuda.empty_cache()

    if a.eval_only:
        if a.apply:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  wrote {OUT.relative_to(REPO)}")
        return 0

    tr_loader = fl.subset_loader("train", a.train_images, a.batch, True, workers=8)
    for seed in SEED_POOL[:a.seeds]:
        name = f"full_text_only_r{a.rank}_s{seed}"
        agg = OUT_DIR / f"{name}.json"
        if a.apply and agg.exists():
            prev = json.loads(agg.read_text(encoding="utf-8", errors="ignore"))
            if prev.get("R@1") is not None:
                print(f"  {name}: already complete, skipping")
                results["runs"].append(prev)
                continue
        print()
        print("=" * 100)
        print(f"{name}   (adapter-only, base frozen)")
        print("=" * 100)
        cfg = ExperimentConfig(
            name=name, peft_method="lora",
            lora=LoRAConfig(rank=a.rank, alpha=2.0 * a.rank, dropout=0.0,
                            apply_to_text=True, apply_to_vision=False),
            gap=GapConfig(compute_every_n_epochs=1, compute_per_layer=False, sample_size=1000),
            train=TrainConfig(dataset="coco", batch_size=a.batch, num_epochs=a.epochs,
                              learning_rate=a.lr, seed=seed, use_amp=False,
                              save_dir=str(OUT_DIR / name)))
        tr = GapAwareTrainer(cfg)
        tr.setup_model()
        n_train = sum(p.numel() for p in tr.model.parameters() if p.requires_grad)
        print(f"  trainable parameters: {n_train:,} (adapter only)")
        t0 = time.time()
        tr.train(tr_loader, val_loader)
        train_s = time.time() - t0
        met = evaluate_model(tr.model)
        gh = tr.gap_tracker.history
        rec = {"name": name, "arm": "text_only", "seed": seed, "rank": a.rank,
               "n_trainable_params": int(n_train), "train_images": a.train_images,
               "epochs": a.epochs, "lr": a.lr, "train_seconds": round(train_s, 1), **met}
        print(f"  train {train_s:.0f}s  eval {met['seconds']}s  R@1 {met['R@1']:.4f} "
              f"(i2t {met['R@1_i2t']:.4f} / t2i {met['R@1_t2i']:.4f})")
        results["runs"].append(rec)
        if a.apply:
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            agg.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        del tr
        torch.cuda.empty_cache()

    print()
    print("=" * 100)
    print("summary, full val2014 gallery")
    print("=" * 100)
    for arm in ("frozen", "text_only"):
        rs = [r for r in results["runs"] if r["arm"] == arm]
        if not rs:
            continue
        r1 = [r["R@1"] for r in rs]
        print(f"  {arm:<10} n={len(rs)}  R@1 {st.mean(r1):.4f}"
              + (f" +/- {st.stdev(r1):.4f}" if len(r1) > 1 else ""))
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
