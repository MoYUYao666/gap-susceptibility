# -*- coding: utf-8 -*-
r"""Re-run Paper A's Flickr30k rank sweep with a genuinely frozen base model.

The paper's ODE fit (mean R^2 = 0.949) rests on the trajectories in
outputs/theory/v1_trajectory, whose 49 runs cover ranks 1 to 64 and were produced by the adapter
wrapper that left the whole text tower trainable. To keep the fit's provenance honest the rank grid
is re-run on Flickr30k with the fixed wrapper, where a rank-r adapter holds all 196,608 r/8 of the
trainable parameters.

Grid matched to the archive: ranks 1, 2, 4, 8, 16, 32, 64 at alpha = 2r, one seed.
Hyperparameters use the corrected values (lr 1e-5, adapter dropout 0), because lr 1e-4 with dropout
0.1 was measured to destroy learning on this data.

Reports per rank the change in centroid and distribution gap over training, plus retrieval on a
disjoint evaluation set.

    python tools/_p812_flickr_rank.py --pilot
    python tools/_p812_flickr_rank.py --apply
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
OUT_DIR = REPO / "outputs" / "flickr_rank"
OUT = REPO / "outputs" / "analysis" / "flickr_rank.json"

RANKS = [1, 2, 4, 8, 16, 32, 64]
SEED_POOL = [42, 123, 456]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=5000)
    ap.add_argument("--eval-images", type=int, default=1000)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--eval-batch", type=int, default=32)
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--arms", type=str, default="text_only")
    ap.add_argument("--ranks", type=str, default=",".join(str(r) for r in RANKS))
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--dropout", type=float, default=0.0)
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if a.pilot:
        a.images, a.eval_images, a.epochs, a.batch, a.ranks = 300, 200, 1, 32, "8"

    import torch
    from transformers import CLIPProcessor
    from src.config import ExperimentConfig, TrainConfig, LoRAConfig, GapConfig
    from src.trainer import GapAwareTrainer
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "fl", str(REPO / "tools" / "_p754_coco_scaleup.py"))
    fl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fl)

    def loaders(n_images, eval_images, batch, eval_batch, workers=8):
        """Flickr30k: training from the train split, evaluation from the test split."""
        from torch.utils.data import DataLoader
        from src.dataset import Flickr30kDataset, _collate_fn
        out = []
        for split, n, bs, shuffle in (("train", n_images, batch, True),
                                      ("test", eval_images, eval_batch, False)):
            ds = Flickr30kDataset(str(REPO / "flickr30k"), split=split, image_size=224,
                                  pre_tokenize=False)
            keys, seen = [], set()
            for s in ds.samples:
                if s["image"] not in seen:
                    seen.add(s["image"])
                    keys.append(s["image"])
            keep = set(keys[:n])
            ds.samples = [s for s in ds.samples if s["image"] in keep]
            print(f"  {split}: {len(set(s['image'] for s in ds.samples))} images, "
                  f"{len(ds.samples)} captions")
            out.append(DataLoader(ds, batch_size=bs, shuffle=shuffle, collate_fn=_collate_fn,
                                  num_workers=workers,
                                  pin_memory=torch.cuda.is_available()))
        return out

    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    ranks = [int(x) for x in a.ranks.split(",") if x.strip()]
    arms = [x.strip() for x in a.arms.split(",") if x.strip()]
    seeds = SEED_POOL[:a.seeds]
    print(f"  device {device}; ranks {ranks}; arms {arms}; seeds {seeds}")
    print(f"  Flickr30k: {a.images} train images, {a.eval_images} eval images, "
          f"{a.epochs} epochs, batch {a.batch}, lr {a.lr}, dropout {a.dropout}, alpha = 2r")

    tr_loader, va_loader = loaders(a.images, a.eval_images, a.batch, a.eval_batch)

    runs = []
    for arm in arms:
        for rank in ranks:
            for seed in seeds:
                name = f"flickr_rank{rank}_{arm}_s{seed}"
                agg = OUT_DIR / f"{name}.json"
                if a.apply and agg.exists():
                    prev = json.loads(agg.read_text(encoding="utf-8", errors="ignore"))
                    if prev.get("R@1") is not None:
                        print(f"  {name}: already complete, skipping")
                        runs.append(prev)
                        continue
                print()
                print("=" * 100)
                print(f"{name}   (alpha={2 * rank})")
                print("=" * 100)
                cfg = ExperimentConfig(
                    name=name, peft_method="lora",
                    lora=LoRAConfig(rank=rank, alpha=2.0 * rank, dropout=a.dropout,
                                    apply_to_text=True, apply_to_vision=(arm == "both")),
                    gap=GapConfig(compute_every_n_epochs=1, compute_per_layer=False,
                                  sample_size=min(a.eval_images, 500)),
                    train=TrainConfig(dataset="flickr30k", batch_size=a.batch,
                                      num_epochs=a.epochs, learning_rate=a.lr, seed=seed,
                                      use_amp=False, save_dir=str(OUT_DIR / name)))
                tr = GapAwareTrainer(cfg)
                tr.setup_model()
                tr.enable_dg_star_tracking()
                n_train = sum(p.numel() for p in tr.model.parameters() if p.requires_grad)
                t0 = time.time()
                tr.train(tr_loader, va_loader)
                train_s = time.time() - t0
                met = fl.evaluate(tr.model, va_loader, device, processor=proc)
                gh = tr.gap_tracker.history
                cg = [g.centroid_gap for g in gh] if gh else []
                dg = [g.distribution_gap for g in gh] if gh else []
                rec = {"name": name, "arm": arm, "rank": rank, "seed": seed, "alpha": 2 * rank,
                       "dataset": "flickr30k", "train_images": a.images,
                       "epochs": a.epochs, "batch": a.batch, "lr": a.lr, "dropout": a.dropout,
                       "n_trainable_params": int(n_train),
                       "cg_first": cg[0] if cg else None, "cg_last": cg[-1] if cg else None,
                       "dCG": (cg[-1] - cg[0]) if len(cg) > 1 else None,
                       "dg_first": dg[0] if dg else None, "dg_last": dg[-1] if dg else None,
                       "dDG": (dg[-1] - dg[0]) if len(dg) > 1 else None,
                       "R@1": met["R@1"], "R@5": met["R@5"], "R@10": met["R@10"],
                       "R@1_i2t": met["R@1_i2t"], "R@1_t2i": met["R@1_t2i"],
                       "n_eval_images": met["n_unique_images"],
                       "n_eval_captions": met["n_captions"],
                       "train_seconds": round(train_s, 1)}
                runs.append(rec)
                print(f"  trainable {n_train:,}  dCG {rec['dCG']:+.4f}  dDG {rec['dDG']:+.4f}  "
                      f"R@1 {rec['R@1']:.4f}  ({train_s:.0f}s)")
                if a.apply:
                    OUT_DIR.mkdir(parents=True, exist_ok=True)
                    agg.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
                del tr
                torch.cuda.empty_cache()

    print()
    print("=" * 100)
    print("summary by rank (Flickr30k)")
    print("=" * 100)
    print(f"  {'rank':>5} {'trainable':>12} {'dCG':>9} {'dDG':>9} {'R@1':>8} {'i2t':>8}")
    for rank in ranks:
        rs = [r for r in runs if r["rank"] == rank]
        if not rs:
            continue
        print(f"  {rank:>5} {rs[0]['n_trainable_params']:>12,} "
              f"{st.mean(r['dCG'] for r in rs):>+9.4f} {st.mean(r['dDG'] for r in rs):>+9.4f} "
              f"{st.mean(r['R@1'] for r in rs):>8.4f} {st.mean(r['R@1_i2t'] for r in rs):>8.4f}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"config": vars(a), "runs": runs},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
