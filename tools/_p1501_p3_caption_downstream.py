# -*- coding: utf-8 -*-
r"""Captioning downstream check for P3 (R1 comments R2.3 / R3.16 / R3.23).

One process per arm (bnb 4-bit memory is not released in-process):
    python tools/_p1501_p3_caption_downstream.py --rank base
    python tools/_p1501_p3_caption_downstream.py --rank 5
    python tools/_p1501_p3_caption_downstream.py --rank 6
Each arm generates captions for the four held-out samples and writes p3_caption_downstream_<rank>.json.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import subprocess
import sys
import time

import numpy as np
import pandas as pd
import torch
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_TEMPLATE = os.path.join(REPO, "outputs", "analysis", "p3_caption_downstream_%s.json")
ADAPTERS = os.path.join(REPO, "outputs", "p3_caption_adapters")
MODEL = os.path.join(REPO, "models", "llava-hf")
PARQUET = os.path.join(REPO, "paper3", "train-caption-00000.parquet")
IMAGES = os.path.join(REPO, "data", "marine_captions")
TRAIN_SCRIPT = os.path.join(REPO, "paper3", "scripts", "run_training.py")
EVAL_N = 4


def bleu4(refs, hyps) -> float:
    prec = []
    for n in range(1, 5):
        num = den = 0
        for r, h in zip(refs, hyps):
            rt, ht = r.split(), h.split()
            rc = collections.Counter(tuple(rt[i:i + n]) for i in range(len(rt) - n + 1))
            hc = collections.Counter(tuple(ht[i:i + n]) for i in range(len(ht) - n + 1))
            num += sum(min(c, rc[g]) for g, c in hc.items())
            den += max(0, len(ht) - n + 1)
        prec.append(num / den if den else 0.0)
    if min(prec) <= 0:
        return 0.0
    return float(math.exp(sum(math.log(p) for p in prec) / 4.0))


def ensure_adapter(rank: int) -> str:
    d = os.path.join(ADAPTERS, f"r{rank}")
    if os.path.exists(os.path.join(d, "adapter_config.json")):
        return d
    r = subprocess.run([sys.executable, TRAIN_SCRIPT, "--rank", str(rank), "--seed", "42", "--epochs", "3",
                        "--num-samples", "20", "--data-path", PARQUET, "--images-dir", IMAGES,
                        "--save-adapter-dir", d], cwd=REPO)
    print("  training exit", r.returncode, flush=True)
    return d


def main() -> int:
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    os.environ["HF_HUB_OFFLINE"] = "1"
    ap = argparse.ArgumentParser()
    ap.add_argument("--rank", default="base")
    args = ap.parse_args()
    rank = None if args.rank == "base" else int(args.rank)
    OUT = OUT_TEMPLATE % args.rank
    df = pd.read_parquet(PARQUET).head(EVAL_N)
    refs = [str(x) for x in df["output"].tolist()]
    from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration
    from peft import PeftModel
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                               bnb_4bit_use_double_quant=True)
    processor = AutoProcessor.from_pretrained(MODEL)
    t0 = time.time()
    base = LlavaForConditionalGeneration.from_pretrained(MODEL, quantization_config=quant, device_map="auto")
    model = base
    if rank is not None:
        d = ensure_adapter(rank)
        model = PeftModel.from_pretrained(base, d)
    hyps = []
    model.eval()
    for i, row in df.iterrows():
        img = Image.open(os.path.join(IMAGES, str(row["image"]))).convert("RGB")
        conv = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": str(row["instruction"])}]}]
        prompt = processor.apply_chat_template(conv, add_generation_prompt=True)
        inp = processor(text=prompt, images=img, return_tensors="pt")
        inp = {k: v.to("cuda") if torch.is_tensor(v) else v for k, v in inp.items()}
        with torch.no_grad():
            out = model.generate(**inp, max_new_tokens=48, do_sample=False)
        gen = processor.tokenizer.decode(out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        hyps.append(gen)
        print(f"  rank={rank} i={i} gen={gen[:90]!r}", flush=True)
    b4 = bleu4(refs, hyps)
    exact = float(np.mean([h.strip() == r.strip() for h, r in zip(hyps, refs)]))
    report = {"meta": {"script": "tools/_p1501_p3_caption_downstream.py", "task": "R2.3/R3.16/R3.23 captioning",
                       "n_eval": EVAL_N, "dataset": "marine captions", "seed": 42},
              "rank": rank, "bleu4": b4, "exact_match": exact, "hypotheses": hyps, "refs": refs,
              "elapsed_min": (time.time() - t0) / 60.0}
    json.dump(report, open(OUT, "w", encoding="utf-8"), indent=1)
    print(f"  rank={rank} BLEU-4={b4:.4f} exact={exact:.3f}")
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
