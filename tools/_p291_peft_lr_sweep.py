# -*- coding: utf-8 -*-
r"""PR R1.6 (last open item) -- LoRA / Adapter learning-rate sweep.

task-5 showed full fine-tuning is extremely lr-sensitive (zero-shot 60.9 % at lr 1e-6 down to
0.1 % at 1e-4), so a comparison at ONE shared lr is unfair.  This script closes the remaining
half of that question: it sweeps the learning rate for the two adapter methods under the
**same protocol as the full-FT sweep** (Flickr30k captions 0-1999, batch 64, fp16, 10 epochs,
AdamW wd 0.01, cosine per step, grad clip 1.0, identical evaluation: ImageNet-1K zero-shot on
the same 14,288 images, CG/DG via src/gap_metrics, R@1 on the same 1000 Flickr30k pairs).

Grid: lora_both x lora_text x adapter_both  x  lr in {1e-5, 3e-5, 1e-4, 3e-4}  x  >=2 seeds.

Code-level proof that this is PEFT and not full fine-tuning (the task-2 lesson):
  * every parameter NOT belonging to the adapter is asserted `requires_grad == False`;
  * `n_trainable` is asserted equal to (a) the count recomputed from the injected modules,
    (b) a literal expected count derived from the architecture, and (c) strictly less than the
    full model's parameter count.
All three are recorded per run in `runs[*].peft_proof`.

    python tools\_p291_peft_lr_sweep.py                         # dry run
    python tools\_p291_peft_lr_sweep.py --apply --seeds 42      # stage 1
    python tools\_p291_peft_lr_sweep.py --apply --seeds 42,123 --resume   # stage 2
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
from torch.utils.data import DataLoader  # noqa: E402
from transformers import CLIPModel  # noqa: E402

from src.dataset import _collate_fn  # noqa: E402
from src.lora import apply_lora_to_model  # noqa: E402
from src.peft_methods import apply_adapter_to_model  # noqa: E402

MODEL_ID = "openai/clip-vit-base-patch32"
TRAIN_SLICE = (0, 2000)
VAL_SLICE = (2000, 3000)
EPOCHS_DEFAULT = 10
BATCH_DEFAULT = 64
WD = 0.01
GRAD_CLIP = 1.0
N_ZS_EVAL = 14288
OUT = REPO / "outputs" / "analysis" / "pr_peft_lr_sweep.json"
CKPT_DIR = REPO / "outputs" / "analysis" / "pr_peft_sweep"
FULLFT = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep_full.json"
DEFAULT_LRS = "1e-5,3e-5,1e-4,3e-4"
DEFAULT_CONFIGS = "lora_both,lora_text,adapter_both"

# literal expected trainable-parameter counts, derived from the architecture:
#   LoRA r=8 on q_proj+v_proj: 12 layers x 2 modules x (in*8 + 8*out)
#     vision in=out=768 -> 12*2*(768*8+8*768) = 294,912 ; text in=out=512 -> 196,608
#   Adapter d=64 on self_attn+mlp: 12 layers x 2 modules x (hidden*64 + 64 + 64*hidden + hidden)
EXPECTED_TRAINABLE = {
    "lora_both": {"n": 294912 + 196608, "note": "q,v; 12 vision layers + 12 text layers"},
    "lora_text": {"n": 196608, "note": "q,v; 12 text layers only"},
    "adapter_both": {"n": 24 * (768 * 64 + 64 + 64 * 768 + 768)
                        + 24 * (512 * 64 + 64 + 64 * 512 + 512),
                     "note": "bottleneck 64 on self_attn+mlp, both towers"},
}

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


def load_p263():
    """Import the full-FT sweep so the evaluation protocol cannot drift."""
    spec = importlib.util.spec_from_file_location(
        "p263", str(REPO / "tools" / "_p263_fullft_lr_sweep.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- PEFT construction

def build_peft(config: str):
    """Return (model, peft_modules, proof dict). Asserts it is PEFT, not full fine-tuning."""
    model = CLIPModel.from_pretrained(MODEL_ID, local_files_only=True)
    n_total = sum(p.numel() for p in model.parameters())

    if config.startswith("lora"):
        vision = config == "lora_both"
        model, layers, _reported = apply_lora_to_model(
            model, rank=8, alpha=16.0, target_modules=["q_proj", "v_proj"],
            apply_to_vision=vision, apply_to_text=True)
        # `apply_lora_to_model` only replaces Linear layers; Embedding / LayerNorm /
        # projection / logit_scale keep requires_grad=True.  Freeze them explicitly so the
        # optimizer can only touch LoRA matrices.
        for name, p in model.named_parameters():
            p.requires_grad_("lora_A" in name or "lora_B" in name)
        peft = layers
        n_from_modules = sum(v.trainable_params for v in layers.values())
        base_frozen = [n for n, p in model.named_parameters()
                       if p.requires_grad and "lora_" not in n]
        inner_frozen = all(not v.original.weight.requires_grad for v in layers.values())
    elif config.startswith("adapter"):
        vision = config == "adapter_both"
        model, wrappers, _reported = apply_adapter_to_model(
            model, bottleneck_dim=64, activation="gelu", dropout=0.0,
            target_modules=None, apply_to_vision=vision, apply_to_text=True)
        peft = wrappers
        n_from_modules = sum(p.numel() for w in wrappers.values()
                             for p in w.adapter.parameters())
        base_frozen = [n for n, p in model.named_parameters()
                       if p.requires_grad and ".adapter." not in n]
        inner_frozen = all(not p.requires_grad for w in wrappers.values()
                           for n, p in w.original.named_parameters())
    else:
        raise ValueError("unknown config %s" % config)

    model = model.cuda()
    trainable = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    n_trainable = sum(p.numel() for _, p in trainable)
    expected = EXPECTED_TRAINABLE[config]["n"]
    assert not base_frozen, "base parameters are still trainable: %s" % base_frozen[:5]
    assert inner_frozen, "the wrapped original module was not frozen"
    assert n_trainable == n_from_modules, (n_trainable, n_from_modules)
    assert n_trainable == expected, \
        "trainable count %d != architecture-derived expectation %d for %s" % (
            n_trainable, expected, config)
    assert n_trainable < n_total, "n_trainable == n_total -> this is not PEFT"
    proof = {
        "config": config,
        "n_total_params": int(n_total),
        "n_trainable_params": int(n_trainable),
        "n_trainable_from_modules": int(n_from_modules),
        "n_trainable_expected_literal": int(expected),
        "expected_note": EXPECTED_TRAINABLE[config]["note"],
        "trainable_fraction": round(n_trainable / n_total, 6),
        "all_non_peft_parameters_frozen": True,
        "wrapped_original_modules_frozen": True,
        "is_peft_not_full_finetuning": bool(n_trainable < n_total),
        "trainable_param_names_sample": [n for n, _ in trainable[:4]],
        "n_trainable_tensors": len(trainable),
        "peft_module_names_sample": list(peft)[:3],
        "n_peft_modules": len(peft),
    }
    return model, peft, proof


def peft_state_dict(model) -> dict:
    return {k: v.detach().cpu().clone() for k, v in model.state_dict().items()
            if v.requires_grad or "lora_" in k or ".adapter." in k}


# --------------------------------------------------------------------------- training

def train_one(config, lr, seed, batch, amp, epochs, m263, processor, parq, train_ds, val_ds,
              ckpt_dir):
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    train_loader = DataLoader(train_ds, batch_size=batch, shuffle=True, num_workers=0,
                              collate_fn=_collate_fn, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0,
                            collate_fn=_collate_fn)
    model, peft, proof = build_peft(config)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = AdamW(params, lr=lr, weight_decay=WD)
    sched = CosineAnnealingLR(opt, T_max=epochs * len(train_loader))
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    torch.cuda.reset_peak_memory_stats()

    train_losses, seconds = [], []
    # post-injection state: for LoRA the adapter is exactly zero at init (B=0), for the
    # bottleneck Adapter `up.bias` is NOT zero, so insertion alone perturbs the geometry.  The
    # paper's "delta_old" convention measures from this state; delta_common measures from the
    # frozen model.  Recording it lets both conventions be read off the same file.
    model.eval()
    init_gap = m263.gap_and_retrieval(model, val_loader)
    model.train()
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
            torch.nn.utils.clip_grad_norm_(params, GRAD_CLIP)
            scaler.step(opt)
            scaler.update()
            sched.step()
            tot += float(loss.item())
            nb += 1
            step += 1
        train_losses.append(tot / max(nb, 1))
        seconds.append(round(time.time() - te0, 1))
        log("  %-12s lr=%-7g seed=%-5d ep%2d train=%.4f (%.0fs)"
            % (config, lr, seed, ep, train_losses[-1], seconds[-1]))

    model.eval()
    tz = time.time()
    zs = m263.zeroshot_imagenet1k(model, processor, parq, n_eval=N_ZS_EVAL)
    log("  zero-shot eval: %.2f%% on %d images (%.0fs)"
        % (zs["top1_pct"], zs["n_images"], time.time() - tz))
    fin = m263.gap_and_retrieval(model, val_loader)

    ck = Path(ckpt_dir)
    if not ck.is_absolute():
        ck = REPO / ck
    ck = ck / ("%s_lr%g_seed%d" % (config, lr, seed))
    ck.mkdir(parents=True, exist_ok=True)
    wpath = ck / "peft_state_last.pt"
    torch.save(peft_state_dict(model), wpath)
    return {
        "config": config, "lr": lr, "seed": seed, "batch": batch,
        "amp": "fp16" if amp else "fp32", "epochs": epochs,
        "steps_per_epoch": len(train_loader), "total_steps": step,
        "weight_decay": WD, "grad_clip": GRAD_CLIP, "scheduler": "cosine (per step)",
        "peft_proof": proof,
        "post_injection_gap_retrieval": {k: (round(v, 6) if isinstance(v, float) else v)
                                         for k, v in init_gap.items()},
        "history": {"train_loss": train_losses, "epoch_seconds": seconds},
        "final": {"zero_shot_imagenet1k_top1_pct": round(zs["top1_pct"], 2),
                  "zero_shot_n_images": zs["n_images"],
                  **{k: (round(v, 6) if isinstance(v, float) else v)
                     for k, v in fin.items()}},
        "final_train_loss": round(train_losses[-1], 4),
        "peak_allocated_mb": round(torch.cuda.max_memory_allocated() / 1024 ** 2, 1),
        "weights_path": str(wpath.relative_to(REPO)),
        "weights_sha1": sha1_file(wpath),
        "weights_bytes": wpath.stat().st_size,
        "error": None,
    }


# --------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--configs", default=DEFAULT_CONFIGS)
    ap.add_argument("--lrs", default=DEFAULT_LRS)
    ap.add_argument("--seeds", default="42,123")
    ap.add_argument("--batch", type=int, default=BATCH_DEFAULT)
    ap.add_argument("--epochs", type=int, default=EPOCHS_DEFAULT)
    ap.add_argument("--fp32", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--ckpt-dir", default=str(CKPT_DIR))
    args = ap.parse_args()
    configs = [c.strip() for c in args.configs.split(",") if c.strip()]
    lrs = [float(x) for x in args.lrs.split(",") if x.strip()]
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    amp = not args.fp32
    plan = [(c, lr, s) for c in configs for lr in lrs for s in seeds]

    print("plan: %d PEFT runs (batch %d, %s, %d epochs)"
          % (len(plan), args.batch, "fp16" if amp else "fp32", args.epochs))
    for c in configs:
        print("  %-13s expected trainable=%d (%s)"
              % (c, EXPECTED_TRAINABLE[c]["n"], EXPECTED_TRAINABLE[c]["note"]))
    if not args.apply:
        print("(dry run; add --apply)")
        return 0

    m263 = load_p263()
    from transformers import CLIPProcessor
    processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=True)
    import glob as _glob
    parq = sorted(_glob.glob(str(REPO / "data" / "imagenet_hf" / "*.parquet")))
    assert parq, "no ImageNet parquet shards"
    _, train_ds, val_ds = m263.build_data()

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    done, frozen, prev_runs = {}, None, []
    if args.resume and out_path.exists():
        prev = json.load(io.open(out_path, encoding="utf-8"))
        same = (prev["meta"]["protocol"]["batch"] == args.batch
                and prev["meta"]["protocol"]["epochs"] == args.epochs
                and prev["meta"]["protocol"]["zero_shot_eval_images"] == N_ZS_EVAL
                and prev["meta"]["protocol"]["amp"] == ("fp16" if amp else "fp32")
                and prev.get("frozen") is not None)
        if same:
            prev_runs = list(prev["runs"])
            for r in prev_runs:
                if not r.get("error"):
                    done[(r["config"], r["lr"], r["seed"])] = r
            frozen = prev.get("frozen")
            log("resume: file holds %d runs, %d of the %d planned are complete"
                % (len(prev_runs), len([k for k in done if k in plan]), len(plan)))
        else:
            log("ABORT: existing output has a different protocol; refusing to overwrite")
            return 2

    if frozen is None:
        if not FULLFT.exists():
            log("ABORT: %s missing (the frozen baseline is taken from the full-FT sweep so "
                "both use the identical protocol)" % FULLFT.name)
            return 3
        full = json.load(io.open(FULLFT, encoding="utf-8"))
        frozen = full["frozen"]
        frozen["_source"] = "%s :: frozen (identical evaluation protocol)" % FULLFT.name
        log("frozen baseline (from %s): zero-shot %.2f%% CG %.4f DG %.4f R@1 %.4f"
            % (FULLFT.name, frozen["zero_shot"]["top1_pct"], frozen["gap_retrieval"]["CG"],
               frozen["gap_retrieval"]["DG"], frozen["gap_retrieval"]["R@1_mean"]))

    runs = list(prev_runs)
    for config, lr, seed in plan:
        if (config, lr, seed) in done:
            log("skip %s lr=%g seed=%d (already done)" % (config, lr, seed))
            continue
        log("=== %s lr=%g seed=%d ===" % (config, lr, seed))
        try:
            rec = train_one(config, lr, seed, args.batch, amp, args.epochs, m263, processor,
                            parq, train_ds, val_ds, args.ckpt_dir)
        except Exception as e:  # noqa: BLE001
            import traceback
            rec = {"config": config, "lr": lr, "seed": seed,
                   "error": "%s: %s" % (type(e).__name__, str(e)[:400]),
                   "traceback_tail": traceback.format_exc()[-600:]}
            log("  FAILED: %s" % rec["error"])
            try:
                torch.cuda.empty_cache()
            except Exception:  # noqa: BLE001
                pass
        if not rec.get("error"):
            log("  -> zero-shot %.2f%%  CG %.4f (dCG %+.4f)  DG %.4f  R@1 %.4f  "
                "trainable=%d/%d"
                % (rec["final"]["zero_shot_imagenet1k_top1_pct"], rec["final"]["CG"],
                   rec["final"]["CG"] - frozen["gap_retrieval"]["CG"], rec["final"]["DG"],
                   rec["final"]["R@1_mean"], rec["peft_proof"]["n_trainable_params"],
                   rec["peft_proof"]["n_total_params"]))
        runs.append(rec)
        write_out(out_path, runs, frozen, configs, lrs, seeds, args.batch, amp, args.epochs,
                  parq, status="partial")

    write_out(out_path, runs, frozen, configs, lrs, seeds, args.batch, amp, args.epochs, parq,
              status="complete")
    print("\n== summary (frozen zero-shot %.2f%%) ==" % frozen["zero_shot"]["top1_pct"])
    for r in sorted([x for x in runs if not x.get("error")],
                    key=lambda x: (x["config"], x["lr"], x["seed"])):
        print("  %-13s lr=%-7g seed=%-5d zero-shot %6.2f%%  dCG %+.4f  dDG %+.4f  R@1 %6.4f"
              % (r["config"], r["lr"], r["seed"],
                 r["final"]["zero_shot_imagenet1k_top1_pct"],
                 r["final"]["CG"] - frozen["gap_retrieval"]["CG"],
                 r["final"]["DG"] - frozen["gap_retrieval"]["DG"], r["final"]["R@1_mean"]))
    print("\nwrote %s" % out_path.relative_to(REPO))
    return 0


def write_out(out_path, runs, frozen, configs, lrs, seeds, batch, amp, epochs, parq, status):
    ok = [r for r in runs if not r.get("error")]
    fcg = frozen["gap_retrieval"]["CG"]
    fdg = frozen["gap_retrieval"]["DG"]
    fzs = frozen["zero_shot"]["top1_pct"]

    def cell(rs):
        zs = [r["final"]["zero_shot_imagenet1k_top1_pct"] for r in rs]
        dc = [r["final"]["CG"] - fcg for r in rs]
        dd = [r["final"]["DG"] - fdg for r in rs]
        r1 = [r["final"]["R@1_mean"] for r in rs]
        def ms(v, nd):
            m = float(np.mean(v))
            return (round(m, nd), (round(float(np.std(v, ddof=1)), nd) if len(v) > 1 else None))
        z_m, z_s = ms(zs, 2)
        c_m, c_s = ms(dc, 4)
        d_m, d_s = ms(dd, 4)
        r_m, r_s = ms(r1, 4)
        return {"n_seeds": len(rs), "zero_shot_top1_pct_mean": z_m, "zero_shot_top1_pct_sd": z_s,
                "zero_shot_values": zs, "dCG_mean": c_m, "dCG_sd": c_s, "dCG_values": dc,
                "dDG_mean": d_m, "dDG_sd": d_s, "R@1_mean": r_m, "R@1_sd": r_s,
                "R@1_values": r1,
                "n_trainable_params": rs[0]["peft_proof"]["n_trainable_params"]}

    analysis = {"grid": {}, "best": None, "vs_fullft": None}
    for c in configs:
        for lr in lrs:
            rs = [r for r in ok if r["config"] == c and r["lr"] == lr]
            if rs:
                analysis["grid"]["%s@%g" % (c, lr)] = cell(rs)
    if ok:
        best = max(ok, key=lambda r: r["final"]["zero_shot_imagenet1k_top1_pct"])
        # best lr per config, on the paper's own axis (CG: smaller is better) and on zero-shot
        per_cfg = {}
        for c in configs:
            rs = [r for r in ok if r["config"] == c]
            if not rs:
                continue
            per_cfg[c] = {
                "best_zero_shot": max(rs, key=lambda r: r["final"][
                    "zero_shot_imagenet1k_top1_pct"])["lr"],
                "best_dCG": min(rs, key=lambda r: r["final"]["CG"])["lr"],
                "n_runs": len(rs),
            }
        analysis["best"] = {
            "best_run_by_zero_shot": {"config": best["config"], "lr": best["lr"],
                                      "seed": best["seed"],
                                      "zero_shot_top1_pct":
                                          best["final"]["zero_shot_imagenet1k_top1_pct"],
                                      "dCG": round(best["final"]["CG"] - fcg, 4),
                                      "dDG": round(best["final"]["DG"] - fdg, 4),
                                      "R@1_mean": best["final"]["R@1_mean"]},
            "best_lr_per_config": per_cfg,
        }
        if FULLFT.exists():
            full = json.load(io.open(FULLFT, encoding="utf-8"))
            fa = full["analysis"]
            best_ft = max([r for r in full["runs"] if not r.get("error")],
                          key=lambda r: r["final"]["zero_shot_imagenet1k_top1_pct"])
            analysis["vs_fullft"] = {
                "source": "%s :: analysis.per_lr / runs[*]" % FULLFT.name,
                "frozen_zero_shot_top1_pct": fzs,
                "fullft_best_lr": best_ft["lr"],
                "fullft_best_zero_shot_top1_pct":
                    best_ft["final"]["zero_shot_imagenet1k_top1_pct"],
                "fullft_best_dCG": round(best_ft["final"]["CG"] - fcg, 4),
                "fullft_best_R@1": best_ft["final"]["R@1_mean"],
                "fullft_per_lr": fa.get("per_lr", {}),
                "delta_best_peft_minus_best_fullft": {
                    "zero_shot_pp": round(best["final"]["zero_shot_imagenet1k_top1_pct"]
                                          - best_ft["final"]["zero_shot_imagenet1k_top1_pct"], 2),
                    "dCG": round(best["final"]["CG"] - best_ft["final"]["CG"], 4),
                    "R@1": round(best["final"]["R@1_mean"] - best_ft["final"]["R@1_mean"], 4),
                },
                "interpretation_rule": "positive zero_shot_pp / negative dCG favour the PEFT "
                                       "method at its own best learning rate",
            }

    payload = {
        "meta": {
            "script": "tools/_p291_peft_lr_sweep.py",
            "script_sha1": sha1_file(Path(__file__)),
            "purpose": "PR R1.6 last open item -- LoRA / Adapter learning-rate sweep under the "
                       "same protocol as the full-FT sweep, to test the strictest fairness "
                       "question (each method at its own optimum)",
            "status": status,
            "model": MODEL_ID,
            "peft_proof": "every non-PEFT parameter asserted requires_grad==False; "
                          "n_trainable asserted equal to the architecture-derived literal and "
                          "strictly smaller than n_total (runs[*].peft_proof)",
            "protocol": {"train": "flickr30k captions %s, shuffle=True, num_workers=0"
                                  % (TRAIN_SLICE,),
                         "val": "flickr30k captions %s" % (VAL_SLICE,),
                         "epochs": epochs, "batch": batch,
                         "amp": "fp16" if amp else "fp32",
                         "optimizer": "AdamW", "weight_decay": WD,
                         "scheduler": "cosine per step", "grad_clip": GRAD_CLIP,
                         "zero_shot_eval_images": N_ZS_EVAL,
                         "identical_to": "tools/_p263_fullft_lr_sweep.py (task-5)",
                         "evaluation_reused_from": "tools/_p263_fullft_lr_sweep.py "
                                                   "(zeroshot_imagenet1k / gap_and_retrieval)"},
            "grid": {"configs": configs, "lrs": lrs, "seeds": seeds},
            "expected_trainable": EXPECTED_TRAINABLE,
            "configs_detail": {
                "lora_both": "LoRA r=8 alpha=16 on q_proj,v_proj of both towers",
                "lora_text": "LoRA r=8 alpha=16 on q_proj,v_proj of the text tower only",
                "adapter_both": "bottleneck Adapter (d=64, GELU) on self_attn and mlp of both "
                                "towers",
            },
            "inputs": {"imagenet_parquet_shards": len(parq),
                       "frozen_baseline_source": frozen.get("_source", "unknown"),
                       "fullft_sweep": str(FULLFT.relative_to(REPO)) if FULLFT.exists() else None,
                       "fullft_sweep_sha1": sha1_file(FULLFT)},
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


if __name__ == "__main__":
    raise SystemExit(main())
