#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Measure the frozen Qwen2-VL-2B baseline under the same clean gap definition.

Why this is needed. `tools/_p1150_qwen_clean_sweep.py` records the gap **after** each epoch only, exactly as the
original `_p47` did -- and `_p47`-derived "reduction" percentages were computed from the **epoch-1** value, which
mixes training progress into what is presented as a change from the frozen model. That is a defect, not a
convention: a reduction should be measured against the untrained model.

This script measures the untrained model on the same 400 Flickr30k samples with the same clean definition
(I = mean pool over image-token positions, T = mean pool over caption positions, both L2-normalised, no projection),
so the sweep's per-arm reductions can be quoted against a real baseline.

It imports the measurement function from the sweep itself rather than re-implementing it, so the two cannot drift.

    python _p1163_qwen_frozen_baseline.py --out /root/p3/outputs/vlm_clean/frozen_baseline.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

MDIR = Path("/root/autodl-tmp/hf/hub/models--Qwen--Qwen2-VL-2B-Instruct/snapshots/main")
SWEEP = Path("/root/p3/tools/_p1150_qwen_clean_sweep.py")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/root/p3/outputs/vlm_clean/frozen_baseline.json")
    ap.add_argument("--maxsamples", type=int, default=400)
    ap.add_argument("--batch", type=int, default=2)
    a = ap.parse_args()

    sys.path.insert(0, "/root/p3")
    spec = importlib.util.spec_from_file_location("qsweep", str(SWEEP))
    q = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(q)
    print("  imported the measurement from", SWEEP.name, flush=True)

    import torch
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
    from src.dataset import create_dataloaders

    torch.manual_seed(0)
    loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                      batch_size=a.batch, max_samples=a.maxsamples)
    batches = list(loader)
    print(f"  {len(batches)} batches x batch {a.batch}", flush=True)

    model = Qwen2VLForConditionalGeneration.from_pretrained(
        str(MDIR), torch_dtype=torch.bfloat16, device_map="cuda")
    model.config.use_cache = False
    model.eval()
    proc = AutoProcessor.from_pretrained(str(MDIR), trust_remote_code=True)
    tokenizer = proc.tokenizer
    image_token_id = int(getattr(model.config, "image_token_id", None)
                         or getattr(model.config, "image_token_index", 151655))
    print(f"  image_token_id = {image_token_id}", flush=True)

    cache = q.precompute_inputs(proc, batches)
    # `pooled` only needs the projections for its legacy branch; identity keeps that branch harmless here.
    proj = torch.nn.Identity()
    II, TT, counts = [], [], None
    t0 = time.time()
    with torch.no_grad():
        for bi, _b in enumerate(batches):
            inp = {k: (v.to("cuda") if hasattr(v, "to") else v) for k, v in cache[bi].items()}
            (I, T), _legacy, c = q.pooled(model, inp, tokenizer, image_token_id, proj, proj)
            II.append(I)
            TT.append(T)
            counts = counts or c
    I = torch.cat(II)
    T = torch.cat(TT)
    dg, cg = q.dg_cg(I, T)
    rec = {
        "tag": "frozen_baseline",
        "dg_star": dg, "cg": cg,
        "n_pairs": int(I.shape[0]),
        "image_token_id": image_token_id,
        "token_counts_first_batch": counts,
        "max_samples": a.maxsamples, "batch": a.batch,
        "measurement": {
            "I": "mean pool of final hidden state over image-token positions",
            "T": "mean pool of final hidden state over caption positions",
            "normalisation": "L2 per side, no projection",
            "note": "untrained model; this is the baseline for the sweep's per-arm reductions",
        },
        "elapsed_sec": round(time.time() - t0, 1),
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  FROZEN clean DG* = {dg:.6f}   CG = {cg:.6f}   over {rec['n_pairs']} pairs "
          f"({rec['elapsed_sec']}s)", flush=True)
    print("  wrote", a.out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
