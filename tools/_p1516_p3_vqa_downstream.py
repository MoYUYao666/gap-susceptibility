# -*- coding: utf-8 -*-
r"""VQA-RAD downstream check for P3 (R1 comments R2.3 / R3.16 / R3.23).

One arm per process:
    python tools/_p1516_p3_vqa_downstream.py --rank base --eval-n 50
    python tools/_p1516_p3_vqa_downstream.py --rank 5 --train-samples 200 --eval-n 50
    python tools/_p1516_p3_vqa_downstream.py --rank 6 --train-samples 200 --eval-n 50

The arm trains a LLaVA LoRA adapter on the VQA-RAD training split (blank-free: real images), then answers held-out
questions; accuracy is normalised exact match plus token F1.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import string
import subprocess
import sys
import time

import numpy as np
import pandas as pd
import torch
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_TEMPLATE = os.path.join(REPO, "outputs", "analysis", "p3_vqa_downstream_%s.json")
ADAPTERS = os.path.join(REPO, "outputs", "p3_vqa_adapters")
MODEL = os.path.join(REPO, "models", "llava-hf")
TRAIN_PARQUET = os.path.join(REPO, "paper3", "train-vqarad.parquet")
TEST_PARQUET = os.path.join(REPO, "paper3", "test-vqarad.parquet")
IMAGES = os.path.join(REPO, "data", "vqa_rad", "images")
TRAIN_SCRIPT = os.path.join(REPO, "paper3", "scripts", "run_training.py")


def norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[%s]" % re.escape(string.punctuation), " ", s)
    return " ".join(s.split())


def token_f1(refs, hyps):
    f1s = []
    for r, h in zip(refs, hyps):
        rt = collections.Counter(r.split())
        ht = collections.Counter(h.split())
        c = sum((rt & ht).values())
        if c == 0:
            f1s.append(0.0)
        else:
            p = c / max(sum(ht.values()), 1)
            rec = c / max(sum(rt.values()), 1)
            f1s.append(2 * p * rec / (p + rec))
    return sum(f1s) / len(f1s)


def ensure_adapter(rank, train_samples, epochs):
    d = os.path.join(ADAPTERS, f"r{rank}")
    if os.path.exists(os.path.join(d, "adapter_config.json")):
        return d
    r = subprocess.run([sys.executable, TRAIN_SCRIPT, "--rank", str(rank), "--seed", "42", "--epochs", str(epochs),
                        "--num-samples", str(train_samples), "--data-path", TRAIN_PARQUET,
                        "--images-dir", IMAGES, "--save-adapter-dir", d], cwd=REPO)
    print("  training exit", r.returncode, flush=True)
    return d


def main() -> int:
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    os.environ["HF_HUB_OFFLINE"] = "1"
    ap = argparse.ArgumentParser()
    ap.add_argument("--rank", default="base")
    ap.add_argument("--train-samples", type=int, default=200)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--eval-n", type=int, default=50)
    args = ap.parse_args()
    rank = None if args.rank == "base" else int(args.rank)
    OUT = OUT_TEMPLATE % args.rank
    df = pd.read_parquet(TEST_PARQUET).head(args.eval_n)
    from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration
    from peft import PeftModel
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                               bnb_4bit_use_double_quant=True)
    processor = AutoProcessor.from_pretrained(MODEL)
    t0 = time.time()
    base = LlavaForConditionalGeneration.from_pretrained(MODEL, quantization_config=quant, device_map="auto")
    model = base
    if rank is not None:
        d = ensure_adapter(rank, args.train_samples, args.epochs)
        model = PeftModel.from_pretrained(base, d, is_trainable=False)
    hyps, refs = [], []
    model.eval()
    for i, row in df.iterrows():
        img = Image.open(os.path.join(IMAGES, str(row["image"]))).convert("RGB")
        conv = [{"role": "user", "content": [{"type": "image"},
                                             {"type": "text", "text": "Answer briefly. " + str(row["instruction"])}]}]
        text = processor.apply_chat_template(conv, add_generation_prompt=True)
        inp = processor(text=text, images=img, return_tensors="pt")
        inp = {k: v.to("cuda") if torch.is_tensor(v) else v for k, v in inp.items()}
        with torch.no_grad():
            out = model.generate(**inp, max_new_tokens=16, do_sample=False)
        gen = processor.tokenizer.decode(out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        hyps.append(gen)
        refs.append(str(row["output"]))
        if i < 3:
            print(f"  rank={rank} i={i} gen={gen[:60]!r} ref={refs[-1][:40]!r}", flush=True)
    nref = [norm(r) for r in refs]
    nhyp = [norm(h) for h in hyps]
    exact = float(np.mean([a == b for a, b in zip(nhyp, nref)]))
    relaxed = float(np.mean([set(a.split()) <= set(b.split()) for a, b in zip(nref, nhyp)]))
    yn_pairs = [(a, b) for a, b in zip(nref, nhyp) if a.split()[:1] in (["yes"], ["no"])]
    yn_acc = float(np.mean([a.split()[:1] == b.split()[:1] for a, b in yn_pairs])) if yn_pairs else None
    report = {"meta": {"script": "tools/_p1516_p3_vqa_downstream.py", "task": "R2.3/R3.16/R3.23 VQA-RAD",
                       "n_eval": len(refs), "train_samples": args.train_samples if rank is not None else 0,
                       "epochs": args.epochs, "prompt": "Answer briefly. <question>"},
              "rank": rank, "accuracy": exact, "relaxed_accuracy": relaxed, "yes_no_accuracy": yn_acc,
              "n_yes_no": len(yn_pairs),
              "token_f1": token_f1(nref, nhyp), "hypotheses": hyps, "refs": refs,
              "elapsed_min": (time.time() - t0) / 60.0}
    json.dump(report, open(OUT, "w", encoding="utf-8"), indent=1)
    print(f"  rank={rank} accuracy={exact:.3f} F1={report['token_f1']:.3f}")
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
