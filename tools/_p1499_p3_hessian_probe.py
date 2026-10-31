# -*- coding: utf-8 -*-
r"""Direct empirical curvature check for the P3 first-order argument (R1 comment R3.5).

Measures the finite-difference Hessian quadratic form g^T H g along the gradient direction on the LLaVA-1.5-7B
4-bit + LoRA setup used by the paper, per block group, and compares the second-order term with the first-order
term of the alignment-energy change.

    D:\Anaconda\envs\pytorch\python.exe tools/_p1499_p3_hessian_probe.py
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import time

import numpy as np
import pandas as pd
import torch
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_TEMPLATE = os.path.join(REPO, "outputs", "analysis", "p3_hessian_probe_r%d_s%d.json")
MODEL = os.path.join(REPO, "models", "llava-hf")
PARQUET = os.path.join(REPO, "paper3", "train-instr-00000.parquet")
IMAGES = os.path.join(REPO, "data", "marine_captions")
RANKS_DEFAULT = [5, 6]
EPS = [1e-3, 3e-4]
N_BATCH = 3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rank", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    RANKS = [args.rank]
    OUT = OUT_TEMPLATE % (args.rank, args.seed)
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    t0 = time.time()
    from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration
    from peft import LoraConfig, TaskType, get_peft_model

    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                               bnb_4bit_use_double_quant=True)
    processor = AutoProcessor.from_pretrained(MODEL)
    df = pd.read_parquet(PARQUET).head(N_BATCH)
    img_tok = processor.tokenizer.convert_tokens_to_ids("<image>")
    imgs = [Image.new("RGB", (336, 336), (128, 128, 128)) for _ in range(N_BATCH)]
    inputs = []
    for i, row in df.iterrows():
        text = f"USER: {row['instruction']}\nASSISTANT: {row['output']}"
        toks = processor.tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
        ids = torch.cat([torch.full((1, 576), img_tok, dtype=torch.long), toks["input_ids"][:, 1:]], dim=1)
        am = torch.cat([torch.ones(1, 576, dtype=torch.long), toks["attention_mask"][:, 1:]], dim=1)
        pv = processor.image_processor(imgs[i], return_tensors="pt")["pixel_values"].squeeze(0)
        inputs.append({"input_ids": ids[0], "attention_mask": am[0], "pixel_values": pv,
                       "labels": ids[0].clone()})
    results = {"meta": {"script": "tools/_p1499_p3_hessian_probe.py", "task": "R1 R3.5 curvature",
                        "model": "llava-hf 4-bit nf4 + LoRA qkvo", "n_batches": N_BATCH, "eps": EPS,
                        "protocol": "blank-image instruction batch, no optimizer step"}, "runs": []}
    for rank in RANKS:
        gc.collect()
        torch.cuda.empty_cache()
        model = LlavaForConditionalGeneration.from_pretrained(MODEL, quantization_config=quant, device_map="auto")
        lora = LoraConfig(task_type=TaskType.CAUSAL_LM, r=rank, lora_alpha=rank * 2, lora_dropout=0.0,
                          target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
        pm = get_peft_model(model, lora)
        params = [(n, p) for n, p in pm.named_parameters() if p.requires_grad]
        groups = {"vision": [], "proj": [], "llm": []}
        for n, p in params:
            key = "vision" if "vision_tower" in n else ("proj" if "multi_modal_projector" in n else "llm")
            groups[key].append((n, p))
        for bi, batch in enumerate(inputs):
            batch = {k: v.unsqueeze(0).cuda() for k, v in batch.items()}
            pm.zero_grad(set_to_none=True)
            out = pm(**batch)
            loss0 = out.loss
            loss0.backward()
            grads = {n: p.grad.detach().clone() for n, p in params if p.grad is not None}
            g2 = sum(float((g.float() ** 2).sum()) for g in grads.values())
            gnorm = float(np.sqrt(g2))
            # finite-difference curvature along the full gradient direction
            curve = {}
            for eps in EPS:
                def probe(sign: float) -> float:
                    with torch.no_grad():
                        for n, p in params:
                            if n in grads:
                                p.add_(sign * eps * grads[n].float().to(p.dtype))
                    o = pm(**batch)
                    val = float(o.loss.item())
                    with torch.no_grad():
                        for n, p in params:
                            if n in grads:
                                p.sub_(sign * eps * grads[n].float().to(p.dtype))
                    return val
                lp, lm = probe(+1.0), probe(-1.0)
                ghg = (lp - 2.0 * float(loss0.item()) + lm) / (eps ** 2)
                curve[str(eps)] = ghg
            # per-group curvature at the smaller eps
            eps = EPS[-1]
            per = {}
            for gname, plist in groups.items():
                sub = {n: grads[n] for n, _ in plist if n in grads}
                if not sub:
                    continue
                def probe_group(sign: float) -> float:
                    with torch.no_grad():
                        for n, p in plist:
                            if n in sub:
                                p.add_(sign * eps * sub[n].float().to(p.dtype))
                    val = float(pm(**batch).loss.item())
                    with torch.no_grad():
                        for n, p in plist:
                            if n in sub:
                                p.sub_(sign * eps * sub[n].float().to(p.dtype))
                    return val
                lp, lm = probe_group(+1.0), probe_group(-1.0)
                per[gname] = (lp - 2.0 * float(loss0.item()) + lm) / (eps ** 2)
            # first-order coefficient in the same units: ||g||^2 (loss change per unit step)
            curves = {k: v for k, v in curve.items()}
            results["runs"].append({"rank": rank, "batch": bi, "loss": float(loss0.item()),
                                    "grad_norm": gnorm, "g2": g2,
                                    "ghg_full": curves, "ghg_per_group_eps3e-4": per,
                                    "second_order_over_first_order": {
                                        k: (0.5 * float(k) * v / g2) if g2 > 0 else None
                                        for k, v in curves.items()}})
            print(f"  r={rank} b={bi} loss={float(loss0.item()):.4f} ||g||={gnorm:.4g} "
                  f"gHg(1e-3)={curve['0.001']:.4g} ratio={0.5 * 1e-3 * curve['0.001'] / g2:.4g}", flush=True)
        del pm, model
        gc.collect()
        torch.cuda.empty_cache()
    results["elapsed_min"] = (time.time() - t0) / 60.0
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)
    print("wrote", os.path.relpath(OUT, REPO), f"({results['elapsed_min']:.1f} min)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
