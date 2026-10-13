# -*- coding: utf-8 -*-
r"""PR R1.6 -- 8 GB feasibility probe for FULL fine-tuning of CLIP ViT-B/32.

The manuscript states one optimisation recipe for every method (batch 128, 10 epochs, AdamW
lr 1e-4). This probe asks, with measurements rather than guesses, which full-fine-tuning
configurations actually run on this machine's single RTX 4060 Laptop (8 GB).

Each configuration runs in its OWN subprocess, so a CUDA out-of-memory in one probe cannot
poison the allocator of the next one.  The child does `--steps` real optimisation steps
(forward + backward + AdamW) on the Flickr30k training split and reports peak allocated
memory, wall time and, if it fails, the exact error text.  Nothing is silently reduced: every
attempted configuration is recorded, successful or not.

Code-level proof that this really is FULL fine-tuning (the task-2 lesson: a large
`n_trainable_params` does not make a run "full fine-tuning"):
  * every parameter has `requires_grad = True`,
  * `n_trainable == sum(p.numel() for p in model.parameters()) == n_total`,
  * asserted in the child and re-asserted by the parent on the child's JSON.

    python tools\_p262_fullft_feasibility.py            # dry run (print the plan)
    python tools\_p262_fullft_feasibility.py --apply    # run the probes
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

OUT = REPO / "outputs" / "analysis" / "pr_fullft_feasibility.json"
LOGDIR = REPO / "outputs" / "analysis" / "_p262_logs"
MODEL_ID = "openai/clip-vit-base-patch32"
TRAIN_SLICE = (0, 2000)          # the archived full-FT protocol (clip_fullft_rerun.py)
PROBE_STEPS = 3
CONFIGS = [
    # name, batch, amp, note
    ("manuscript_b128_fp32", 128, False,
     "the recipe the manuscript states for every method (batch 128, fp32 AdamW)"),
    ("b128_fp16", 128, True, "batch 128 with fp16 autocast (same batch, mixed precision)"),
    ("b64_fp32", 64, False, "batch 64, fp32"),
    ("b64_fp16", 64, True,
     "batch 64 + fp16 autocast = the configuration of the archived full-FT rerun "
     "(tools/clip_fullft_rerun.py, outputs/imagenet_zs_rerun/full_ft*)"),
    ("b32_fp32", 32, False, "batch 32, fp32"),
]


def child(batch: int, amp: bool, steps: int) -> int:
    """Run one probe in this process and print a single JSON line."""
    import numpy as np
    import torch
    from torch.optim import AdamW
    from torch.utils.data import DataLoader
    from transformers import CLIPModel

    from src.dataset import Flickr30kDataset, _collate_fn

    torch.manual_seed(42)
    np.random.seed(42)
    res: dict = {"batch": batch, "amp": "fp16" if amp else "fp32", "steps_requested": steps}

    model = CLIPModel.from_pretrained(MODEL_ID, local_files_only=True)
    for p in model.parameters():
        p.requires_grad = True
    n_total = sum(p.numel() for p in model.parameters())
    n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    res["n_total_params"] = int(n_total)
    res["n_trainable_params"] = int(n_trainable)
    res["all_parameters_requires_grad"] = all(p.requires_grad for p in model.parameters())
    assert res["all_parameters_requires_grad"], "not every parameter is trainable"
    assert n_trainable == n_total, "n_trainable != n_total -> not full fine-tuning"

    model = model.cuda()
    ds = Flickr30kDataset("flickr30k", split="train", max_samples=None, pre_tokenize=True)
    sub = torch.utils.data.Subset(ds, range(*TRAIN_SLICE))
    loader = DataLoader(sub, batch_size=batch, shuffle=False, num_workers=0,
                        collate_fn=_collate_fn, drop_last=True)
    opt = AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4,
                weight_decay=0.01)
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    free0, total = torch.cuda.mem_get_info()
    res["gpu_free_before_mb"] = round(free0 / 1024 ** 2, 1)
    res["gpu_total_mb"] = round(total / 1024 ** 2, 1)

    def step(b):
        opt.zero_grad(set_to_none=True)
        images = b["image"].cuda(non_blocking=True)
        ids = b["input_ids"].cuda(non_blocking=True)
        am = b["attention_mask"].cuda(non_blocking=True)
        with torch.amp.autocast("cuda", enabled=amp):
            out = model(pixel_values=images, input_ids=ids, attention_mask=am, return_loss=False)
            ie = out.image_embeds / out.image_embeds.norm(dim=-1, keepdim=True)
            te = out.text_embeds / out.text_embeds.norm(dim=-1, keepdim=True)
            logits = model.logit_scale.exp() * ie @ te.T
            labels = torch.arange(images.shape[0], device="cuda")
            loss = (torch.nn.functional.cross_entropy(logits, labels)
                    + torch.nn.functional.cross_entropy(logits.T, labels)) / 2.0
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt)
        scaler.update()
        return float(loss.item())

    torch.cuda.reset_peak_memory_stats()
    losses, times = [], []
    model.train()
    it = iter(loader)
    for i in range(steps):
        t0 = time.time()
        losses.append(step(next(it)))
        times.append(time.time() - t0)
        print("  step %d loss=%.4f %.2fs peak=%.0f MB"
              % (i + 1, losses[-1], times[-1], torch.cuda.max_memory_allocated() / 1024 ** 2),
              flush=True)
    res.update({"ok": True, "losses": [round(x, 4) for x in losses],
                "step_seconds": [round(x, 3) for x in times],
                "step_seconds_mean": round(sum(times) / len(times), 3),
                "peak_allocated_mb": round(torch.cuda.max_memory_allocated() / 1024 ** 2, 1),
                "peak_reserved_mb": round(torch.cuda.max_memory_reserved() / 1024 ** 2, 1)})
    print("PROBE_JSON " + json.dumps(res, ensure_ascii=False), flush=True)
    return 0


def run_probe(name: str, batch: int, amp: bool) -> dict:
    LOGDIR.mkdir(parents=True, exist_ok=True)
    log = LOGDIR / ("%s.log" % name)
    cmd = [sys.executable, str(Path(__file__).resolve()), "--probe", name,
           "--batch", str(batch), "--steps", str(PROBE_STEPS)]
    if amp:
        cmd.append("--amp")
    t0 = time.time()
    with io.open(log, "w", encoding="utf-8", newline="") as fh:
        try:
            p = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=str(REPO),
                               timeout=900)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            rc = -9
    txt = io.open(log, encoding="utf-8", errors="replace").read()
    rec = {"config": name, "batch": batch, "amp": "fp16" if amp else "fp32",
           "returncode": rc, "wall_s": round(time.time() - t0, 1),
           "log": str(log.relative_to(REPO))}
    payload = None
    for line in txt.splitlines():
        if line.startswith("PROBE_JSON "):
            payload = json.loads(line[len("PROBE_JSON "):])
    if payload is not None:
        rec.update(payload)
        rec["outcome"] = "ok"
        # the parent re-asserts the code-level full-fine-tuning proof
        assert payload["all_parameters_requires_grad"] is True
        assert payload["n_trainable_params"] == payload["n_total_params"]
    else:
        rec["outcome"] = "failed"
        low = txt.lower()
        if "out of memory" in low:
            rec["error_kind"] = "cuda_oom"
        elif "timeout" in low or rc == -9:
            rec["error_kind"] = "timeout"
        else:
            rec["error_kind"] = "other"
        rec["error_text"] = txt.strip().splitlines()[-1][:500] if txt.strip() else "(no output)"
        rec["traceback_tail"] = "\n".join(txt.strip().splitlines()[-25:])
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--probe", default=None, help="child mode: probe name")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--steps", type=int, default=PROBE_STEPS)
    ap.add_argument("--amp", action="store_true")
    args = ap.parse_args()

    if args.probe:
        return child(args.batch, args.amp, args.steps)

    print("plan: %d full-fine-tuning configurations, %d optimisation steps each"
          % (len(CONFIGS), PROBE_STEPS))
    for name, batch, amp, note in CONFIGS:
        print("  %-22s batch=%-4d amp=%-5s  %s" % (name, batch, amp and "fp16" or "fp32", note))
    if not args.apply:
        print("(dry run; add --apply)")
        return 0

    import torch
    results = []
    for name, batch, amp, note in CONFIGS:
        print("\n== probe %s (batch=%d, %s) ==" % (name, batch, amp and "fp16" or "fp32"),
              flush=True)
        rec = run_probe(name, batch, amp)
        rec["note"] = note
        results.append(rec)
        if rec["outcome"] == "ok":
            print("  OK  peak_alloc=%.0f MB  peak_reserved=%.0f MB  step=%.2fs"
                  % (rec["peak_allocated_mb"], rec["peak_reserved_mb"],
                     rec["step_seconds_mean"]), flush=True)
        else:
            print("  FAILED (%s): %s" % (rec.get("error_kind"), rec.get("error_text")),
                  flush=True)

    payload = {
        "meta": {
            "script": "tools/_p262_fullft_feasibility.py",
            "purpose": "PR R1.6 -- measure which FULL fine-tuning configurations of "
                       "openai/clip-vit-base-patch32 actually run on one RTX 4060 Laptop "
                       "(8 GB); manuscript recipe is batch 128 / fp32 AdamW",
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
            "gpu_total_mb": (round(torch.cuda.get_device_properties(0).total_memory / 1024 ** 2, 1)
                             if torch.cuda.is_available() else None),
            "model": MODEL_ID,
            "train_slice": "flickr30k captions [%d, %d) (the archived full-FT protocol)"
                           % TRAIN_SLICE,
            "probe_steps": PROBE_STEPS,
            "full_finetuning_proof": "all parameters requires_grad=True and "
                                     "n_trainable == n_total, asserted in the child process and "
                                     "re-asserted here on the child's JSON",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "isolation": "each configuration ran in its own subprocess; logs in %s"
                         % LOGDIR.relative_to(REPO).as_posix(),
        },
        "configurations": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(payload, ensure_ascii=False, indent=1))
    print("\nwrote %s" % OUT.relative_to(REPO))
    ok = [r for r in results if r["outcome"] == "ok"]
    print("feasible: %s" % [r["config"] for r in ok])
    print("infeasible: %s" % [r["config"] for r in results if r["outcome"] != "ok"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
