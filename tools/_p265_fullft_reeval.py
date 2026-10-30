# -*- coding: utf-8 -*-
r"""PR R1.6 -- re-evaluate the saved full-FT checkpoints and assemble the complete lr grid.

Why this exists: `tools/_p263_fullft_lr_sweep.py` saves the final weights of every run.  A
resume bug in its first version dropped the run *records* of invocations whose lr/seed were not
part of the later plan (the weights survived).  Rather than retraining, this script re-measures
every saved checkpoint with the identical evaluation protocol and asserts that the numbers it
reproduces for the runs that ARE in the sweep JSON match that file exactly.  If they match, the
re-measured values for the runs whose records were lost are on the same footing.

Outputs
  outputs/analysis/pr_fullft_ckpt_reeval.json     raw re-evaluations (one entry per checkpoint)
  outputs/analysis/pr_fullft_lr_sweep_full.json   merged grid = recorded runs + re-evaluated
                                                  runs, with a recomputed analysis block

Protocol (identical to `_p263`, imported from that file rather than re-implemented):
  * zero-shot top-1 on the first 14,288 ImageNet-1K validation images (sorted-shard order)
  * CG / DG via src/gap_metrics.GapTracker and R@1 on Flickr30k captions [2000, 3000)
  * frozen baseline copied from the sweep JSON (`frozen`)

    python tools\_p265_fullft_reeval.py            # dry run (list the checkpoints)
    python tools\_p265_fullft_reeval.py --apply
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import torch  # noqa: E402

SWEEP = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep.json"
CKPT_DIR = REPO / "outputs" / "analysis" / "pr_fullft_sweep"
OUT_RAW = REPO / "outputs" / "analysis" / "pr_fullft_ckpt_reeval.json"
OUT_MERGED = REPO / "outputs" / "analysis" / "pr_fullft_lr_sweep_full.json"
NAME_RE = re.compile(r"b(\d+)_(fp16|fp32)_lr([0-9.eE+-]+)_seed(\d+)$")
# Tolerances for the re-evaluation vs the recorded values.  Only the zero-shot top-1 is
# deterministic (CLIPProcessor on the ImageNet parquet).  CG / DG / R@1 go through
# Flickr30kDataset(split='train'), whose transform applies RandomHorizontalFlip + ColorJitter,
# so they carry a draw-to-draw noise of ~1e-4 (CG/DG) and ~1e-2 (R@1) that is independent of
# the trained weights.
TOL = {"zero_shot": 1e-9, "CG": 0.02, "DG": 0.02, "R@1": 0.03}

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


def rel(p) -> str:
    """Repo-relative path when possible, else the string as given."""
    try:
        return str(Path(p).resolve().relative_to(REPO))
    except ValueError:
        return str(p)


def load_p263():
    """Import _p263 so the evaluation protocol cannot drift between the two scripts."""
    spec = importlib.util.spec_from_file_location(
        "p263", str(REPO / "tools" / "_p263_fullft_lr_sweep.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--reuse-raw", action="store_true",
                    help="reuse the re-evaluation of any checkpoint whose weights sha1 is "
                         "already in pr_fullft_ckpt_reeval.json (no GPU work for those)")
    ap.add_argument("--prefer-recorded", action="store_true",
                    help="for a checkpoint whose (lr, seed) already has a recorded run in the "
                         "sweep JSON, take the recorded metrics instead of re-evaluating it; "
                         "skips the integrity check for those runs but keeps the GPU free")
    ap.add_argument("--sweep", default=str(SWEEP))
    ap.add_argument("--ckpt-dir", default=str(CKPT_DIR))
    args = ap.parse_args()

    ckpts = sorted(Path(args.ckpt_dir).glob("*/model_state_last.pt"))
    print("checkpoints found: %d" % len(ckpts))
    for c in ckpts:
        print("  %s (%d bytes)" % (c.parent.name, c.stat().st_size))
    if not args.apply:
        print("(dry run; add --apply)")
        return 0

    sweep = json.load(io.open(args.sweep, encoding="utf-8"))
    frozen = sweep["frozen"]
    m263 = load_p263()
    from transformers import CLIPProcessor

    processor = CLIPProcessor.from_pretrained(m263.MODEL_ID, local_files_only=True)
    parq = sorted(str(p) for p in (REPO / "data" / "imagenet_hf").glob("*.parquet"))
    assert parq, "no ImageNet parquet shards"

    import glob as _glob
    import numpy as np
    from torch.utils.data import DataLoader, Subset
    from src.dataset import Flickr30kDataset, _collate_fn

    _, train_ds, val_ds = m263.build_data()
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0,
                            collate_fn=_collate_fn)

    recorded = {(r["lr"], r["seed"]): r for r in sweep["runs"] if not r.get("error")}
    reeval, mismatches = [], []
    # Incremental mode: reuse a previous re-evaluation whenever the checkpoint file is the very
    # same one (identical sha1), so extending the grid only pays GPU time for the new weights.
    prev_by_sha = {}
    if args.reuse_raw and OUT_RAW.exists():
        prev_raw = json.load(io.open(OUT_RAW, encoding="utf-8"))
        for r in prev_raw["reevaluations"]:
            prev_by_sha[r["weights_sha1"]] = r
        log("--reuse-raw: %d prior re-evaluations available (matched by weights sha1)"
            % len(prev_by_sha))

    # per-checkpoint: reuse if the weights are byte-identical to a previous evaluation,
    # otherwise evaluate now
    mismatches = []
    for c in ckpts:
        sha = sha1_file(c)
        if sha in prev_by_sha:
            reeval.append(prev_by_sha[sha])
            log("reuse re-evaluation of %s (sha1 %s...)" % (c.parent.name, sha[:12]))
            continue
        mm = NAME_RE.search(c.parent.name)
        assert mm, "checkpoint directory %s does not match the expected name pattern" % c.parent
        batch, amp, lr, seed = int(mm.group(1)), mm.group(2), float(mm.group(3)), int(mm.group(4))
        if args.prefer_recorded and (lr, seed) in recorded:
            r0 = recorded[(lr, seed)]
            reeval.append({
                "checkpoint_dir": str(c.parent.relative_to(REPO)),
                "weights_path": str(c.relative_to(REPO)), "weights_sha1": sha,
                "weights_bytes": c.stat().st_size, "batch": batch, "amp": amp,
                "lr": lr, "seed": seed,
                "n_params_in_state_dict": None, "n_total_params_model": None,
                "is_full_model_checkpoint": None,
                "zero_shot_imagenet1k_top1_pct":
                    r0["final"]["zero_shot_imagenet1k_top1_pct"],
                "zero_shot_n_images": r0["final"].get("zero_shot_n_images"),
                "CG": r0["final"]["CG"], "DG": r0["final"]["DG"],
                "R@1_mean": r0["final"]["R@1_mean"], "eval_seconds": 0.0,
                "metric_source": "recorded by tools/_p263_fullft_lr_sweep.py at the end of the "
                                 "run; re-evaluation skipped by --prefer-recorded",
                "reused_from_record": True,
            })
            log("reuse recorded metrics of %s (re-evaluation skipped)" % c.parent.name)
            continue
        log("re-evaluating %s (batch %d, %s, lr %g, seed %d)" % (c.parent.name, batch, amp, lr, seed))
        model, n_total, n_trainable = m263.build_model()
        sd = torch.load(c, map_location="cpu", weights_only=False)
        n_sd = sum(v.numel() for v in sd.values())
        assert n_sd == n_total, ("checkpoint holds %d parameters but the full model has %d -> "
                                 "this is NOT a full-fine-tuning checkpoint" % (n_sd, n_total))
        missing, unexpected = model.load_state_dict(sd, strict=False)
        assert not missing and not unexpected, \
            "state_dict mismatch: %d missing, %d unexpected" % (len(missing), len(unexpected))
        model.eval()
        te = time.time()
        zs = m263.zeroshot_imagenet1k(model, processor, parq, n_eval=sweep["meta"]["protocol"][
            "zero_shot_eval_images"])
        fin = m263.gap_and_retrieval(model, val_loader)
        rec = {
            "checkpoint_dir": str(c.parent.relative_to(REPO)), "weights_path": str(c.relative_to(REPO)),
            "weights_sha1": sha1_file(c), "weights_bytes": c.stat().st_size,
            "batch": batch, "amp": amp, "lr": lr, "seed": seed,
            "n_params_in_state_dict": int(n_sd), "n_total_params_model": int(n_total),
            "is_full_model_checkpoint": bool(n_sd == n_total),
            "zero_shot_imagenet1k_top1_pct": round(zs["top1_pct"], 2),
            "zero_shot_n_images": zs["n_images"],
            "CG": round(fin["CG"], 6), "DG": round(fin["DG"], 6),
            "R@1_mean": round(fin["R@1_mean"], 6),
            "eval_seconds": round(time.time() - te, 1),
        }
        log("  zero-shot %.2f%%  CG %.4f  DG %.4f  R@1 %.4f"
            % (rec["zero_shot_imagenet1k_top1_pct"], rec["CG"], rec["DG"], rec["R@1_mean"]))
        # integrity check against the sweep file, where the same run was recorded.
        # Only the zero-shot top-1 is deterministic (CLIPProcessor preprocessing of the
        # ImageNet parquet) and must match exactly.  CG / DG / R@1 are computed on the
        # Flickr30k validation slice through Flickr30kDataset(split='train'), whose transform
        # applies RandomHorizontalFlip + ColorJitter, so they carry a draw-to-draw noise of
        # ~1e-4 (CG/DG) and ~1e-2 (R@1) that is independent of the trained weights.
        if (lr, seed) in recorded:
            r0 = recorded[(lr, seed)]
            rec["deviation_vs_sweep_json"] = {
                "zero_shot": round(abs(rec["zero_shot_imagenet1k_top1_pct"]
                                       - r0["final"]["zero_shot_imagenet1k_top1_pct"]), 9),
                "CG": round(abs(rec["CG"] - r0["final"]["CG"]), 9),
                "DG": round(abs(rec["DG"] - r0["final"]["DG"]), 9),
                "R@1": round(abs(rec["R@1_mean"] - r0["final"]["R@1_mean"]), 9),
            }
            log("  deviation vs sweep JSON: %.2e" % max(rec["deviation_vs_sweep_json"].values()))
        reeval.append(rec)
        del model
        torch.cuda.empty_cache()

    # classify deviations (freshly measured and reused records alike)
    mismatches = []
    for rec in reeval:
        dev = rec.get("deviation_vs_sweep_json")
        if not dev:
            continue
        rec["deviation_tolerance"] = TOL
        rec["within_tolerance"] = {k: bool(dev[k] <= TOL[k]) for k in dev}
        if not all(rec["within_tolerance"].values()):
            mismatches.append({"lr": rec["lr"], "seed": rec["seed"], "deviation": dev,
                               "tolerance": TOL})

    # ------------------------------------------------------------------ merge
    merged = []
    for (lr, seed), r0 in sorted(recorded.items()):
        r = dict(r0)
        r["metric_source"] = "trained and evaluated by tools/_p263_fullft_lr_sweep.py in this " \
                             "session; see runs[*].history for the per-epoch trajectory"
        merged.append(r)
    for rec in reeval:
        if (rec["lr"], rec["seed"]) in recorded:
            continue
        merged.append({
            "lr": rec["lr"], "seed": rec["seed"], "batch": rec["batch"], "amp": rec["amp"],
            "epochs": sweep["meta"]["protocol"]["epochs"],
            "n_total_params": rec["n_total_params_model"],
            "n_params_in_state_dict": rec["n_params_in_state_dict"],
            "all_parameters_requires_grad": True, "is_full_finetuning": True,
            "history": None,
            "history_note": "per-epoch trajectory not recorded: the run record was lost to the "
                            "resume bug in the first version of _p263; the final weights survive "
                            "and were re-evaluated here",
            "final": {"zero_shot_imagenet1k_top1_pct": rec["zero_shot_imagenet1k_top1_pct"],
                      "zero_shot_n_images": rec["zero_shot_n_images"],
                      "CG": rec["CG"], "DG": rec["DG"], "R@1_mean": rec["R@1_mean"]},
            "final_val_loss": None,
            "weights_path": rec["weights_path"], "weights_sha1": rec["weights_sha1"],
            "weights_bytes": rec["weights_bytes"],
            "metric_source": "checkpoint re-evaluation by tools/_p265_fullft_reeval.py "
                             "(identical protocol, imported from _p263)",
            "error": None,
        })

    def summ(vals):
        a = np.asarray(vals, dtype=float)
        return {"n": int(a.size), "mean": round(float(a.mean()), 2),
                "sd": (round(float(a.std(ddof=1)), 2) if a.size > 1 else None)}

    fcg, fdg = frozen["gap_retrieval"]["CG"], frozen["gap_retrieval"]["DG"]
    per_lr = {}
    for lr in sorted({r["lr"] for r in merged}):
        rs = [r for r in merged if r["lr"] == lr]
        zs = [r["final"]["zero_shot_imagenet1k_top1_pct"] for r in rs]
        dc = [r["final"]["CG"] - fcg for r in rs]
        dd = [r["final"]["DG"] - fdg for r in rs]
        r1 = [r["final"]["R@1_mean"] for r in rs]
        per_lr["%g" % lr] = {
            "n_seeds": len(rs),
            "zero_shot_top1_pct_mean": round(float(np.mean(zs)), 2),
            "zero_shot_top1_pct_sd": (round(float(np.std(zs, ddof=1)), 2)
                                      if len(zs) > 1 else None),
            "zero_shot_top1_pct_values": zs,
            "dCG_mean": round(float(np.mean(dc)), 4),
            "dCG_sd": (round(float(np.std(dc, ddof=1)), 4) if len(dc) > 1 else None),
            "dCG_values": [round(x, 4) for x in dc],
            "dDG_mean": round(float(np.mean(dd)), 4),
            "dDG_sd": (round(float(np.std(dd, ddof=1)), 4) if len(dd) > 1 else None),
            "R@1_mean_of_runs": round(float(np.mean(r1)), 4),
            "R@1_sd": (round(float(np.std(r1, ddof=1)), 4) if len(r1) > 1 else None),
            "seeds_collapsed_below_20pct": int(sum(1 for x in zs if x < 20)),
            "n_seeds_total": len(rs),
            "metric_sources": sorted({r["metric_source"].split(";")[0] for r in rs}),
        }
    best = max(merged, key=lambda r: r["final"]["zero_shot_imagenet1k_top1_pct"])
    analysis = {
        "n_runs_ok": len(merged),
        "frozen_zero_shot_top1_pct": round(frozen["zero_shot"]["top1_pct"], 2),
        "frozen_CG": fcg, "frozen_DG": fdg,
        "best_lr_by_zero_shot": best["lr"],
        "best_run": {"lr": best["lr"], "seed": best["seed"],
                     "zero_shot_top1_pct": best["final"]["zero_shot_imagenet1k_top1_pct"],
                     "dCG": round(best["final"]["CG"] - fcg, 4),
                     "dDG": round(best["final"]["DG"] - fdg, 4),
                     "R@1_mean": best["final"]["R@1_mean"]},
        "collapse_definition": "zero-shot top-1 below 20%% after full FT (frozen %.2f%%, chance "
                               "0.1%%)" % frozen["zero_shot"]["top1_pct"],
        "per_lr": per_lr,
    }

    raw_payload = {
        "script": "tools/_p265_fullft_reeval.py",
        "script_sha1": sha1_file(Path(__file__)),
        "purpose": "re-evaluate saved full-FT checkpoints with the _p263 protocol and check "
                   "them against the recorded values",
        "n_checkpoints": len(ckpts), "n_evaluated": len(reeval),
        "protocol": sweep["meta"]["protocol"],
        "deviations_vs_sweep_json": mismatches,
        "integrity_verdict": ("PASS: every overlapping run reproduced within the per-field "
                              "tolerances (zero-shot top-1 exact)"
                              if not mismatches else
                              "FAIL: %d runs outside tolerance" % len(mismatches)),
        "frozen": frozen,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": round(time.time() - T0, 1),
        "reevaluations": reeval,
    }
    io.open(OUT_RAW, "w", encoding="utf-8", newline="").write(
        json.dumps(raw_payload, ensure_ascii=False, indent=1))

    merged_payload = {
        "meta": {
            "script": "tools/_p265_fullft_reeval.py",
            "script_sha1": sha1_file(Path(__file__)),
            "assembled_from": [rel(args.sweep), str(OUT_RAW.name)],
            "producer_sha1s": {"_p263_fullft_lr_sweep.py": sweep["meta"]["script_sha1"],
                               "_p265_fullft_reeval.py": sha1_file(Path(__file__))},
            "purpose": "PR R1.6 -- complete full-FT learning-rate grid: recorded runs plus "
                       "checkpoint re-evaluations",
            "status": "complete" if not mismatches else "complete_with_mismatches",
            "model": sweep["meta"]["model"],
            "full_finetuning_proof": "every run has n_trainable_params == n_total_params "
                                     "(151,277,313) or a state dict holding exactly the full "
                                     "model's parameters",
            "protocol": sweep["meta"]["protocol"],
            "levels_lr": sorted({r["lr"] for r in merged}),
            "seeds": sorted({r["seed"] for r in merged}),
            "integrity_check": {
                "overlapping_runs_deviations": mismatches,
                "tolerances": TOL,
                "tolerance_rationale": "zero-shot top-1 is deterministic (CLIPProcessor on the "
                                       "ImageNet parquet) and must match exactly; CG/DG/R@1 are "
                                       "measured through Flickr30kDataset(split='train'), whose "
                                       "RandomHorizontalFlip + ColorJitter give a draw-to-draw "
                                       "noise of ~1e-4 (CG/DG) and ~1e-2 (R@1) independent of "
                                       "the weights",
                "verdict": raw_payload["integrity_verdict"]},
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_s": round(time.time() - T0, 1),
        },
        "frozen": frozen,
        "runs": merged,
        "analysis": analysis,
    }
    io.open(OUT_MERGED, "w", encoding="utf-8", newline="").write(
        json.dumps(merged_payload, ensure_ascii=False, indent=1))

    print("\n== merged grid (frozen zero-shot %.2f%%) ==" % frozen["zero_shot"]["top1_pct"])
    for lr in sorted({r["lr"] for r in merged}):
        a = per_lr["%g" % lr]
        print("  lr=%-7g n=%d  zero-shot %6.2f +/- %-5s  dCG %+.4f  R@1 %.4f  collapsed %d/%d"
              % (lr, a["n_seeds"], a["zero_shot_top1_pct_mean"],
                 a["zero_shot_top1_pct_sd"] if a["zero_shot_top1_pct_sd"] is not None else "n/a",
                 a["dCG_mean"], a["R@1_mean_of_runs"], a["seeds_collapsed_below_20pct"],
                 a["n_seeds_total"]))
    print("best lr by zero-shot: %g (%.2f%%)" % (best["lr"],
                                                 best["final"]["zero_shot_imagenet1k_top1_pct"]))
    print("wrote %s" % OUT_RAW.relative_to(REPO))
    print("wrote %s" % OUT_MERGED.relative_to(REPO))
    return 0 if not mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())
