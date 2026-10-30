# -*- coding: utf-8 -*-
r"""Re-run Paper A's rank ablation with a genuinely frozen base model.

The archived ablation varied rank while 144,973,569 of 145,170,177 trainable parameters were ordinary
tower weights, so it could not measure a rank effect. The rerun uses the fixed adapter wrapper, where
a rank-r adapter holds all of the trainable parameters.

Protocol alignment with the paper (experiments/theory/v1_rank_sweep.py and sections/empirical.tex):
  ranks 1, 2, 4, 8, 16, 32, 64; alpha = 2r; batch 128; 10 epochs; 5,000 samples; one seed (42)

One deliberate divergence: the archived runs used lr 1e-4 with adapter dropout 0.1, which was measured
to destroy learning on this data (train loss pinned near log(batch) and retrieval below the frozen
baseline). The rerun uses lr 1e-5 with dropout 0, the setting that converges. This is stated in the
paper's method note.

Reports per rank: the change in centroid gap over training, and retrieval under the corrected
protocol on a disjoint 3,000-image gallery.

    python tools/_p805_rank_rerun.py --pilot
    python tools/_p805_rank_rerun.py --apply
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
OUT_DIR = REPO / "outputs" / "rank_rerun"
OUT = REPO / "outputs" / "analysis" / "rank_rerun.json"

RANKS = [2, 4, 8, 16, 32, 64]          # rank 1 is a degenerate adapter; kept out of the first pass
SEED_POOL = [42, 123, 456]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=5000)
    ap.add_argument("--eval-images", type=int, default=3000)
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
        a.images, a.eval_images, a.epochs, a.batch, a.ranks = 500, 300, 1, 32, "8"

    import torch
    from transformers import CLIPProcessor
    from src.config import ExperimentConfig, TrainConfig, LoRAConfig, GapConfig
    from src.trainer import GapAwareTrainer
    from _p754_coco_scaleup import subset_loader, evaluate

    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    ranks = [int(x) for x in a.ranks.split(",") if x.strip()]
    arms = [x.strip() for x in a.arms.split(",") if x.strip()]
    seeds = SEED_POOL[:a.seeds]
    print(f"  device {device}; ranks {ranks}; arms {arms}; seeds {seeds}")
    print(f"  {a.images} train images, {a.eval_images} eval images, {a.epochs} epochs, "
          f"batch {a.batch}, lr {a.lr}, dropout {a.dropout}, alpha = 2r")

    tr_loader = subset_loader("train", a.images, a.batch, True, workers=8)
    va_loader = subset_loader("val", a.eval_images, a.eval_batch, False, first=False, workers=4)

    runs = []
    for arm in arms:
        for rank in ranks:
            for seed in seeds:
                name = f"rank{rank}_{arm}_s{seed}"
                done = OUT_DIR / f"{name}.json"
                if a.apply and done.exists():
                    prev = json.loads(done.read_text(encoding="utf-8", errors="ignore"))
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
                                  sample_size=min(a.eval_images, 1000)),
                    train=TrainConfig(dataset="coco", batch_size=a.batch, num_epochs=a.epochs,
                                      learning_rate=a.lr, seed=seed, use_amp=False,
                                      save_dir=str(OUT_DIR / name)))
                tr = GapAwareTrainer(cfg)
                tr.setup_model()
                tr.enable_dg_star_tracking()
                n_train = sum(p.numel() for p in tr.model.parameters() if p.requires_grad)
                t0 = time.time()
                tr.train(tr_loader, va_loader)
                train_s = time.time() - t0
                met = evaluate(tr.model, va_loader, device, processor=proc)

                gh = tr.gap_tracker.history
                cg = [g.centroid_gap for g in gh] if gh else []
                dg = [g.distribution_gap for g in gh] if gh else []
                rec = {"name": name, "arm": arm, "rank": rank, "seed": seed,
                       "alpha": 2 * rank, "train_images": a.images, "epochs": a.epochs,
                       "batch": a.batch, "lr": a.lr, "dropout": a.dropout,
                       "n_trainable_params": int(n_train),
                       "cg_first": cg[0] if cg else None, "cg_last": cg[-1] if cg else None,
                       "dCG": (cg[-1] - cg[0]) if len(cg) > 1 else None,
                       "dg_first": dg[0] if dg else None, "dg_last": dg[-1] if dg else None,
                       "dDG": (dg[-1] - dg[0]) if len(dg) > 1 else None,
                       "R@1": met["R@1"], "R@5": met["R@5"], "R@10": met["R@10"],
                       "R@1_i2t": met["R@1_i2t"], "R@1_t2i": met["R@1_t2i"],
                       "train_seconds": round(train_s, 1),
                       "train_loss_first": tr.train_losses[0] if tr.train_losses else None,
                       "train_loss_last": tr.train_losses[-1] if tr.train_losses else None}
                runs.append(rec)
                print(f"  trainable {n_train:,}  dCG {rec['dCG']:+.4f}  R@1 {rec['R@1']:.4f}  "
                      f"({train_s:.0f}s)")
                if a.apply:
                    OUT_DIR.mkdir(parents=True, exist_ok=True)
                    done.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
                del tr
                torch.cuda.empty_cache()

    print()
    print("=" * 100)
    print("summary by rank")
    print("=" * 100)
    print(f"  {'rank':>5} {'trainable':>12} {'dCG':>9} {'R@1':>8} {'i2t':>8} {'t2i':>8}")
    for rank in ranks:
        rs = [r for r in runs if r["rank"] == rank]
        if not rs:
            continue
        print(f"  {rank:>5} {rs[0]['n_trainable_params']:>12,} "
              f"{st.mean(r['dCG'] for r in rs):>+9.4f} {st.mean(r['R@1'] for r in rs):>8.4f} "
              f"{st.mean(r['R@1_i2t'] for r in rs):>8.4f} {st.mean(r['R@1_t2i'] for r in rs):>8.4f}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"config": vars(a), "runs": runs},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
