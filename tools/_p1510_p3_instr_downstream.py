# -*- coding: utf-8 -*-
r"""Instruction-following downstream check for P3 (R1 comments R2.3 / R3.16).

Trains LLaVA LoRA adapters (r=5, r=6) on the instruction parquet and evaluates held-out instruction-following outputs
(token F1, exact match, BLEU-4, CLIP image-text similarity is not applicable here because the protocol uses a blank
image). One process per arm:

    python tools/_p1510_p3_instr_downstream.py --rank base
    python tools/_p1510_p3_instr_downstream.py --rank 5
    python tools/_p1510_p3_instr_downstream.py --rank 6
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
OUT_TEMPLATE = os.path.join(REPO, "outputs", "analysis", "p3_instr_downstream_%s.json")
ADAPTERS = os.path.join(REPO, "outputs", "p3_instr_adapters")
MODEL = os.path.join(REPO, "models", "llava-hf")
PARQUET = os.path.join(REPO, "paper3", "train-instr-00000.parquet")
TRAIN_SCRIPT = os.path.join(REPO, "paper3", "scripts", "run_training.py")
EVAL_N = 4


def token_f1(refs, hyps):
    f1s = []
    for r, h in zip(refs, hyps):
        rt = collections.Counter(r.lower().split())
        ht = collections.Counter(h.lower().split())
        common = sum((rt & ht).values())
        if common == 0:
            f1s.append(0.0)
        else:
            p = common / max(sum(ht.values()), 1)
            rec = common / max(sum(rt.values()), 1)
            f1s.append(2 * p * rec / (p + rec))
    return sum(f1s) / len(f1s)


def bleu4(refs, hyps):
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


def ensure_adapter(rank):
    d = os.path.join(ADAPTERS, f"r{rank}")
    if os.path.exists(os.path.join(d, "adapter_config.json")):
        return d
    r = subprocess.run([sys.executable, TRAIN_SCRIPT, "--rank", str(rank), "--seed", "42", "--epochs", "3",
                        "--num-samples", "20", "--data-path", PARQUET, "--save-adapter-dir", d], cwd=REPO)
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
    refs = [str(r["output"]) for _, r in df.iterrows()]
    prompts = [str(r["instruction"]) + ("\n" + str(r["input"]) if str(r.get("input", "")) else "")
               for _, r in df.iterrows()]
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
    blank = Image.new("RGB", (336, 336), (128, 128, 128))
    hyps = []
    model.eval()
    for i, prompt in enumerate(prompts):
        conv = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
        text = processor.apply_chat_template(conv, add_generation_prompt=True)
        inp = processor(text=text, images=blank, return_tensors="pt")
        inp = {k: v.to("cuda") if torch.is_tensor(v) else v for k, v in inp.items()}
        with torch.no_grad():
            out = model.generate(**inp, max_new_tokens=64, do_sample=False)
        gen = processor.tokenizer.decode(out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        hyps.append(gen)
        print(f"  rank={rank} i={i} gen={gen[:90]!r}", flush=True)
    report = {"meta": {"script": "tools/_p1510_p3_instr_downstream.py", "task": "R2.3/R3.16 instruction following",
                       "n_eval": EVAL_N, "dataset": "instruction parquet", "seed": 42},
              "rank": rank, "bleu4": bleu4(refs, hyps), "token_f1": token_f1(refs, hyps),
              "exact_match": float(np.mean([h.strip() == r.strip() for h, r in zip(hyps, refs)])),
              "hypotheses": hyps, "refs": refs, "elapsed_min": (time.time() - t0) / 60.0}
    json.dump(report, open(OUT, "w", encoding="utf-8"), indent=1)
    print(f"  rank={rank} BLEU-4={report['bleu4']:.4f} F1={report['token_f1']:.4f}")
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
