# -*- coding: utf-8 -*-
r"""PR R1.6 -- full fine-tuning learning-rate sweep for CLIP ViT-B/32 on Flickr30k.

R1's objection: LoRA, Adapter and full fine-tuning were compared under ONE recipe
(batch 128, 10 epochs, AdamW lr 1e-4).  Full fine-tuning is more learning-rate sensitive, so
its collapse to near-chance zero-shot accuracy may be an optimisation artefact rather than a
property of full fine-tuning.  This script sweeps the learning rate and re-measures every
quantity the manuscript uses for that claim.

Protocol (identical to the archived full-FT rerun `tools/clip_fullft_rerun.py`, so the lr=1e-4
point is directly comparable with `outputs/imagenet_zs_rerun/full_ft*`):
  * train   : Flickr30k captions [0, 2000), shuffle=True, num_workers=0
  * val     : Flickr30k captions [2000, 3000)
  * epochs  : 10, batch 64 by default, AdamW(lr, wd=0.01), cosine per step, grad clip 1.0, fp16
  * eval    : ImageNet-1K validation (14288 images, single synset template) zero-shot top-1,
              CG / DG / R@1 on the Flickr30k validation captions

Code-level proof that this is FULL fine-tuning (task-2 lesson: a large `n_trainable_params`
does not make a run "full fine-tuning"): every parameter gets `requires_grad = True` and the
script asserts `n_trainable == n_total` for every single run, recording both in the JSON.

    python tools\_p263_fullft_lr_sweep.py                       # dry run
    python tools\_p263_fullft_lr_sweep.py --apply               # 4 lrs x seed 42, batch 64 fp16
    python tools\_p263_fullft_lr_sweep.py --apply --resume      # continue after an interruption
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import io
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
from torch.optim import AdamW  # noqa: E402
from torch.optim.lr_scheduler import CosineAnnealingLR  # noqa: E402
from torch.utils.data import DataLoader, Subset  # noqa: E402
from transformers import CLIPModel, CLIPProcessor  # noqa: E402

from src.dataset import Flickr30kDataset, _collate_fn  # noqa: E402
from src.gap_metrics import GapTracker  # noqa: E402

MODEL_ID = "openai/clip-vit-base-patch32"
TEMPLATE = "a photo of a {}"
TRAIN_SLICE = (0, 2000)
VAL_SLICE = (2000, 3000)
EPOCHS_DEFAULT = 10
WD = 0.01
GRAD_CLIP = 1.0
OUT = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep.json"
CKPT_DIR = REPO / "outputs" / "analysis" / "pr_fullft_sweep"
ARCHIVED = REPO / "outputs" / "imagenet_zs_rerun" / "full_ft" / "results.json"
ARCHIVED_CG = REPO / "outputs" / "imagenet_zs_rerun" / "full_ft" / "centroid_gap.json"
DEFAULT_LRS = "1e-5,3e-5,1e-4,3e-4"

T0 = time.time()


def log(msg: str) -> None:
    print("  [%7.1fs] %s" % (time.time() - T0, msg), flush=True)


def sha1_file(path) -> str | None:
    if not path or not Path(path).exists():
        return None
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


# --------------------------------------------------------------------------- data / model

def build_data():
    ds = Flickr30kDataset("flickr30k", split="train", max_samples=None, pre_tokenize=True)
    return ds, Subset(ds, range(*TRAIN_SLICE)), Subset(ds, range(*VAL_SLICE))


def build_model(device="cuda"):
    model = CLIPModel.from_pretrained(MODEL_ID, local_files_only=True)
    for p in model.parameters():
        p.requires_grad = True
    n_total = sum(p.numel() for p in model.parameters())
    n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    assert all(p.requires_grad for p in model.parameters()), "not every parameter is trainable"
    assert n_trainable == n_total, "n_trainable != n_total -> not full fine-tuning"
    return model.to(device), n_total, n_trainable


# --------------------------------------------------------------------------- evaluation

@torch.no_grad()
def zeroshot_imagenet1k(model, processor, parq, n_eval=14288, batch=128):
    """Zero-shot top-1 on ImageNet-1K validation.

    `n_eval` defaults to 14,288 = the `n_images` recorded by the archived full-FT runs
    (`outputs/imagenet_zs_rerun/full_ft/results.json :: zero_shot_imagenet1k.n_images`), i.e.
    the first 14,288 images of the sorted-shard iteration order.  The local parquet set now
    holds the full 50,000-image validation split (14 shards); limiting the evaluation to the
    archived count keeps these numbers comparable with 0.13 / 4.12 / 3.39 %.
    """
    from datasets import Dataset as HFDataset
    ds = HFDataset.from_parquet(parq)
    n_eval = min(n_eval, len(ds))
    names = ds.features["label"].names
    texts = [TEMPLATE.format(n.replace("_", " ")) for n in names]
    ti = processor(text=texts, return_tensors="pt", padding=True).to("cuda")
    t = model.text_model(**ti)
    pooled = t[1] if isinstance(t, tuple) else t.pooler_output
    tf = F.normalize(model.text_projection(pooled), dim=-1)
    correct = total = 0
    for i in range(0, n_eval, batch):
        b = ds[i:min(i + batch, n_eval)]
        inp = processor(images=b["image"], return_tensors="pt").to("cuda")
        v = model.vision_model(**inp)
        vp = v[1] if isinstance(v, tuple) else v.pooler_output
        imf = F.normalize(model.visual_projection(vp), dim=-1)
        pred = (imf @ tf.T).argmax(-1).cpu().numpy()
        correct += int(sum(1 for p, y in zip(pred, b["label"]) if p == y))
        total += len(b["label"])
    return {"top1_pct": 100.0 * correct / total, "n_images": total, "template": TEMPLATE,
            "n_available_images": len(ds),
            "subset_rule": "first %d images in sorted-shard iteration order = the archived "
                           "protocol's n_images" % n_eval,
            "class_names": "parquet features['label'].names as-is (synset style, "
                           "underscores -> spaces)"}


@torch.no_grad()
def gap_and_retrieval(model, loader):
    """CG / DG (src/gap_metrics) and R@1 on the Flickr30k validation captions."""
    ie, te = [], []
    for b in loader:
        out = model(pixel_values=b["image"].cuda(), input_ids=b["input_ids"].cuda(),
                    attention_mask=b["attention_mask"].cuda(), return_loss=False)
        ie.append(F.normalize(out.image_embeds, dim=-1))
        te.append(F.normalize(out.text_embeds, dim=-1))
    ie, te = torch.cat(ie), torch.cat(te)
    gt = GapTracker(sample_size=10 ** 9, device="cuda")
    m = gt.compute(ie, te, epoch=0, step=0)
    S = ie @ te.T
    n = S.shape[0]
    ar = torch.arange(n, device=S.device)
    i2t = float((S.argmax(1) == ar).float().mean())
    t2i = float((S.argmax(0) == ar).float().mean())
    return {"CG": float(m.centroid_gap), "DG": float(m.distribution_gap),
            "R@1_i2t": i2t, "R@1_t2i": t2i, "R@1_mean": (i2t + t2i) / 2, "n_pairs": n}


@torch.no_grad()
def val_loss(model, loader):
    model.eval()
    tot, n = 0.0, 0
    for b in loader:
        out = model(pixel_values=b["image"].cuda(), input_ids=b["input_ids"].cuda(),
                    attention_mask=b["attention_mask"].cuda(), return_loss=False)
        ie = F.normalize(out.image_embeds, dim=-1)
        te = F.normalize(out.text_embeds, dim=-1)
        logits = model.logit_scale.exp() * ie @ te.T
        labels = torch.arange(ie.shape[0], device="cuda")
        loss = (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) / 2.0
        tot += float(loss.item())
        n += 1
    model.train()
    return tot / max(n, 1)


# --------------------------------------------------------------------------- training

def train_one(lr, seed, batch, amp, epochs, processor, parq, train_ds, val_ds,
              ckpt_dir=CKPT_DIR, n_zs_eval=14288):
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    train_loader = DataLoader(train_ds, batch_size=batch, shuffle=True, num_workers=0,
                              collate_fn=_collate_fn, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0,
                            collate_fn=_collate_fn)
    model, n_total, n_trainable = build_model()
    opt = AdamW([p for p in model.parameters() if p.requires_grad], lr=lr, weight_decay=WD)
    sched = CosineAnnealingLR(opt, T_max=epochs * len(train_loader))
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    torch.cuda.reset_peak_memory_stats()

    hist = {"train_loss": [], "val_loss": [], "R@1_mean": [], "epoch_seconds": []}
    model.train()
    step = 0
    for ep in range(1, epochs + 1):
        te0 = time.time()
        tot, nb = 0.0, 0
        for b in train_loader:
            opt.zero_grad(set_to_none=True)
            images = b["image"].cuda(non_blocking=True)
            ids = b["input_ids"].cuda(non_blocking=True)
            am = b["attention_mask"].cuda(non_blocking=True)
            with torch.amp.autocast("cuda", enabled=amp):
                out = model(pixel_values=images, input_ids=ids, attention_mask=am,
                            return_loss=False)
                ie = F.normalize(out.image_embeds, dim=-1)
                te = F.normalize(out.text_embeds, dim=-1)
                logits = model.logit_scale.exp() * ie @ te.T
                labels = torch.arange(images.shape[0], device="cuda")
                loss = (F.cross_entropy(logits, labels)
                        + F.cross_entropy(logits.T, labels)) / 2.0
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            scaler.step(opt)
            scaler.update()
            sched.step()
            tot += float(loss.item())
            nb += 1
            step += 1
        vl = val_loss(model, val_loader)
        r1 = gap_and_retrieval(model, val_loader)
        hist["train_loss"].append(tot / max(nb, 1))
        hist["val_loss"].append(vl)
        hist["R@1_mean"].append(r1["R@1_mean"])
        hist["epoch_seconds"].append(round(time.time() - te0, 1))
        log("  lr=%-7g seed=%-5d ep%2d train=%.4f val=%.4f R@1=%.4f (%.0fs)"
            % (lr, seed, ep, hist["train_loss"][-1], vl, r1["R@1_mean"],
               hist["epoch_seconds"][-1]))

    model.eval()
    tz = time.time()
    zs = zeroshot_imagenet1k(model, processor, parq, n_eval=n_zs_eval)
    log("  zero-shot eval: %.2f%% on %d images (%.0fs)"
        % (zs["top1_pct"], zs["n_images"], time.time() - tz))
    fin = gap_and_retrieval(model, val_loader)
    ckpt = Path(ckpt_dir)
    if not ckpt.is_absolute():
        ckpt = REPO / ckpt
    ckpt = ckpt / ("b%d_%s_lr%g_seed%d" % (batch, "fp16" if amp else "fp32", lr, seed))
    ckpt.mkdir(parents=True, exist_ok=True)
    wpath = ckpt / "model_state_last.pt"
    torch.save(model.state_dict(), wpath)
    return {
        "lr": lr, "seed": seed, "batch": batch, "amp": "fp16" if amp else "fp32",
        "epochs": epochs, "steps_per_epoch": len(train_loader), "total_steps": step,
        "weight_decay": WD, "grad_clip": GRAD_CLIP, "scheduler": "cosine (per step)",
        "n_total_params": int(n_total), "n_trainable_params": int(n_trainable),
        "all_parameters_requires_grad": True,
        "is_full_finetuning": bool(n_trainable == n_total),
        "history": hist,
        "final": {"zero_shot_imagenet1k_top1_pct": round(zs["top1_pct"], 2),
                  "zero_shot_n_images": zs["n_images"],
                  **{k: (round(v, 6) if isinstance(v, float) else v) for k, v in fin.items()}},
        "final_val_loss": round(hist["val_loss"][-1], 4),
        "peak_allocated_mb": round(torch.cuda.max_memory_allocated() / 1024 ** 2, 1),
        "peak_reserved_mb": round(torch.cuda.max_memory_reserved() / 1024 ** 2, 1),
        "weights_path": str(wpath.relative_to(REPO)),
        "weights_sha1": sha1_file(wpath),
        "weights_bytes": wpath.stat().st_size,
        "error": None,
    }


# --------------------------------------------------------------------------- output

def write_out(out_path, runs, frozen, lrs, seeds, batch, amp, parq, status, epochs,
              n_zs_eval) -> dict:
    ok = [r for r in runs if not r.get("error")]
    analysis = {}
    if ok and frozen:
        best = max(ok, key=lambda r: r["final"]["zero_shot_imagenet1k_top1_pct"])
        analysis = {
            "n_runs_ok": len(ok), "n_runs_failed": len(runs) - len(ok),
            "frozen_zero_shot_top1_pct": round(frozen["zero_shot"]["top1_pct"], 2),
            "best_lr_by_zero_shot": best["lr"],
            "best_run": {"lr": best["lr"], "seed": best["seed"],
                         "zero_shot_top1_pct": best["final"]["zero_shot_imagenet1k_top1_pct"],
                         "dCG": round(best["final"]["CG"] - frozen["gap_retrieval"]["CG"], 4),
                         "dDG": round(best["final"]["DG"] - frozen["gap_retrieval"]["DG"], 4),
                         "R@1_mean": best["final"]["R@1_mean"]},
            "collapse_definition": "zero-shot top-1 after full FT below 20%% (frozen = %.2f%%, "
                                   "chance for 1000 classes = 0.1%%)"
                                   % frozen["zero_shot"]["top1_pct"],
            "per_lr": {},
        }
        for lr in sorted({r["lr"] for r in ok}):
            rs = [r for r in ok if r["lr"] == lr]
            zs = [r["final"]["zero_shot_imagenet1k_top1_pct"] for r in rs]
            dc = [r["final"]["CG"] - frozen["gap_retrieval"]["CG"] for r in rs]
            dd = [r["final"]["DG"] - frozen["gap_retrieval"]["DG"] for r in rs]
            r1 = [r["final"]["R@1_mean"] for r in rs]
            analysis["per_lr"]["%g" % lr] = {
                "n_seeds": len(rs),
                "zero_shot_top1_pct_mean": round(float(np.mean(zs)), 2),
                "zero_shot_top1_pct_sd": (round(float(np.std(zs, ddof=1)), 2)
                                          if len(zs) > 1 else None),
                "zero_shot_top1_pct_values": zs,
                "dCG_mean": round(float(np.mean(dc)), 4),
                "dCG_values": [round(x, 4) for x in dc],
                "dDG_mean": round(float(np.mean(dd)), 4),
                "R@1_mean_of_runs": round(float(np.mean(r1)), 4),
                "seeds_collapsed_below_20pct": int(sum(1 for x in zs if x < 20)),
                "n_seeds_total": len(rs),
            }
    payload = {
        "meta": {
            "script": "tools/_p263_fullft_lr_sweep.py",
            "script_sha1": sha1_file(Path(__file__)),
            "purpose": "PR R1.6 -- is the full-fine-tuning collapse an artefact of an unfair "
                       "learning rate? Sweep lr and re-measure zero-shot top-1, CG, DG, R@1",
            "status": status,
            "model": MODEL_ID,
            "full_finetuning_proof": "every parameter requires_grad=True and "
                                     "n_trainable == n_total asserted for every run",
            "protocol": {"train": "flickr30k captions %s, shuffle=True, num_workers=0"
                                  % (TRAIN_SLICE,),
                         "val": "flickr30k captions %s" % (VAL_SLICE,),
                         "epochs": epochs, "batch": batch,
                         "amp": "fp16" if amp else "fp32",
                         "zero_shot_eval_images": n_zs_eval,
                         "optimizer": "AdamW", "weight_decay": WD,
                         "scheduler": "cosine per step", "grad_clip": GRAD_CLIP,
                         "matching_archive": "tools/clip_fullft_rerun.py "
                                             "(outputs/imagenet_zs_rerun/full_ft*)"},
            "levels_lr": sorted({r["lr"] for r in runs}),
            "seeds": sorted({r["seed"] for r in runs}),
            "requested_lrs": lrs, "requested_seeds": seeds,
            "grid_note": "levels_lr/seeds describe the runs present in this file; requested_* "
                         "describe the invocation that last wrote it",
            "inputs": {"imagenet_parquet_shards": len(parq),
                       "imagenet_parquet_first_sha1": sha1_file(parq[0]) if parq else None,
                       "archived_full_ft_results": str(ARCHIVED.relative_to(REPO))
                       if ARCHIVED.exists() else None,
                       "archived_full_ft_results_sha1": sha1_file(ARCHIVED),
                       "archived_full_ft_cg": str(ARCHIVED_CG.relative_to(REPO))
                       if ARCHIVED_CG.exists() else None},
            "run_order": "sequential, one GPU process at a time",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_s": round(time.time() - T0, 1),
        },
        "frozen": frozen,
        "runs": runs,
        "analysis": analysis,
    }
    out_path = Path(out_path)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    io.open(out_path, "w", encoding="utf-8", newline="").write(
        json.dumps(payload, ensure_ascii=False, indent=1))
    return payload


# --------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--lrs", default=DEFAULT_LRS)
    ap.add_argument("--seeds", default="42")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--epochs", type=int, default=EPOCHS_DEFAULT,
                    help="10 = the manuscript/archive protocol; other values are smoke tests")
    ap.add_argument("--fp32", action="store_true", help="disable fp16 autocast")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--ckpt-dir", default=str(CKPT_DIR))
    ap.add_argument("--n-zs-eval", type=int, default=14288,
                    help="zero-shot evaluation images; 14288 = the archived protocol")
    args = ap.parse_args()
    lrs = [float(x) for x in args.lrs.split(",") if x.strip()]
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    amp = not args.fp32

    parq = sorted(glob.glob(str(REPO / "data" / "imagenet_hf" / "*.parquet")))
    assert parq, "no ImageNet parquet shards found"
    processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=True)
    plan = [(lr, s) for lr in lrs for s in seeds]
    print("plan: %d full-FT runs (batch %d, %s, %d epochs) lrs=%s seeds=%s"
          % (len(plan), args.batch, "fp16" if amp else "fp32", args.epochs, lrs, seeds))
    if not args.apply:
        print("(dry run; add --apply)")
        return 0

    _, train_ds, val_ds = build_data()
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0,
                            collate_fn=_collate_fn)

    done, frozen, prev_runs = {}, None, []
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    if args.resume and out_path.exists():
        prev = json.load(io.open(out_path, encoding="utf-8"))
        # Reuse any completed (lr, seed) that is also in the current plan, so the grid can be
        # extended (more seeds, one more lr) without re-running what is already done. Only the
        # protocol fields have to match, otherwise the old runs are not comparable and the file
        # is left untouched (abort rather than overwrite).
        same = (prev["meta"]["protocol"]["batch"] == args.batch
                and prev["meta"]["protocol"]["epochs"] == args.epochs
                and prev["meta"]["protocol"]["zero_shot_eval_images"] == args.n_zs_eval
                and prev["meta"]["protocol"]["amp"] == ("fp16" if amp else "fp32")
                and prev.get("frozen") is not None)
        if same:
            # carry over EVERY run already in the file, not only the planned ones: a resumed
            # invocation must never drop results that a previous invocation produced.
            prev_runs = list(prev["runs"])
            for r in prev_runs:
                if not r.get("error"):
                    done[(r["lr"], r["seed"])] = r
            frozen = prev.get("frozen")
            log("resume: file holds %d runs, %d of the %d planned are already complete"
                % (len(prev_runs), len([k for k in done if k in plan]), len(plan)))
        else:
            log("ABORT: the existing output file has a different protocol; refusing to "
                "overwrite it. Use a different --out.")
            return 2

    if frozen is None:
        model, n_total, n_trainable = build_model()
        model.eval()
        tz = time.time()
        fz = zeroshot_imagenet1k(model, processor, parq, n_eval=args.n_zs_eval)
        fg = gap_and_retrieval(model, val_loader)
        frozen = {"n_total_params": int(n_total), "n_trainable_params": int(n_trainable),
                  "zero_shot": fz, "gap_retrieval": fg}
        log("frozen baseline: zero-shot top-1=%.2f%% (n=%d, %.0fs)  CG=%.4f DG=%.4f R@1=%.4f"
            % (fz["top1_pct"], fz["n_images"], time.time() - tz, fg["CG"], fg["DG"],
               fg["R@1_mean"]))
        del model
        torch.cuda.empty_cache()

    runs = list(prev_runs)
    for lr, seed in plan:
        if (lr, seed) in done:
            log("skip lr=%g seed=%d (already done)" % (lr, seed))
            continue
        log("=== full FT lr=%g seed=%d batch=%d %s ===" % (lr, seed, args.batch,
                                                           "fp16" if amp else "fp32"))
        try:
            rec = train_one(lr, seed, args.batch, amp, args.epochs, processor, parq,
                            train_ds, val_ds, ckpt_dir=args.ckpt_dir,
                            n_zs_eval=args.n_zs_eval)
        except Exception as e:  # noqa: BLE001
            import traceback
            rec = {"lr": lr, "seed": seed, "batch": args.batch,
                   "amp": "fp16" if amp else "fp32",
                   "error": "%s: %s" % (type(e).__name__, str(e)[:400]),
                   "traceback_tail": traceback.format_exc()[-600:]}
            log("  FAILED: %s" % rec["error"])
            try:
                torch.cuda.empty_cache()
            except Exception:  # noqa: BLE001
                pass
        if not rec.get("error"):
            log("  -> zero-shot %.2f%%  CG %.4f (frozen %.4f, dCG %+.4f)  DG %.4f  R@1 %.4f"
                % (rec["final"]["zero_shot_imagenet1k_top1_pct"], rec["final"]["CG"],
                   frozen["gap_retrieval"]["CG"],
                   rec["final"]["CG"] - frozen["gap_retrieval"]["CG"],
                   rec["final"]["DG"], rec["final"]["R@1_mean"]))
        runs.append(rec)
        write_out(out_path, runs, frozen, lrs, seeds, args.batch, amp, parq,
                  status="partial", epochs=args.epochs, n_zs_eval=args.n_zs_eval)

    write_out(out_path, runs, frozen, lrs, seeds, args.batch, amp, parq, status="complete",
              epochs=args.epochs, n_zs_eval=args.n_zs_eval)
    print("\n== summary (frozen zero-shot %.2f%%) ==" % frozen["zero_shot"]["top1_pct"])
    for r in sorted(runs, key=lambda x: (x.get("lr", 0), x.get("seed", 0))):
        if r.get("error"):
            print("  lr=%-7g seed=%-5d FAILED: %s" % (r["lr"], r["seed"], r["error"][:80]))
            continue
        print("  lr=%-7g seed=%-5d zero-shot %6.2f%%  CG %+.4f  DG %+.4f  R@1 %6.4f  "
              "final_val_loss %s  n_trainable=%s/%s"
              % (r["lr"], r["seed"], r["final"]["zero_shot_imagenet1k_top1_pct"],
                 r["final"]["CG"] - frozen["gap_retrieval"]["CG"],
                 r["final"]["DG"] - frozen["gap_retrieval"]["DG"], r["final"]["R@1_mean"],
                 ("%.3f" % r["final_val_loss"]) if r.get("final_val_loss") is not None
                 else "n/a (re-eval)",
                 r.get("n_trainable_params") or r.get("n_params_in_state_dict"),
                 r.get("n_total_params")))
    print("\nwrote %s" % out_path.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
