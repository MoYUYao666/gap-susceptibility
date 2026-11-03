# -*- coding: utf-8 -*-
r"""Curvature check on the second VLM family (R1 comment R3.5: LLaVA and Qwen2-VL).

Finite-difference measurement of g^T H g along the gradient direction on Qwen2-VL-2B-Instruct (4-bit, LoRA rank 5),
blank-image protocol. Writes outputs/analysis/p3_hessian_probe_qwen2b_r5.json.

    python tools/_p1511_p3_qwen_hessian.py
"""
from __future__ import annotations

import json
import os
import time

import numpy as np
import pandas as pd
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "p3_hessian_probe_qwen2b_r5.json")
MODEL = os.path.join(REPO, "models", "Qwen2-VL-2B-Instruct")
PARQUET = os.path.join(REPO, "paper3", "train-instr-00000.parquet")
RANK = 5
EPS = [1e-3, 3e-4]
N_BATCH = 3


def main() -> int:
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    torch.manual_seed(42)
    np.random.seed(42)
    t0 = time.time()
    from transformers import AutoProcessor, BitsAndBytesConfig, Qwen2VLForConditionalGeneration
    from peft import LoraConfig, TaskType, get_peft_model
    from PIL import Image
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                               bnb_4bit_use_double_quant=True)
    processor = AutoProcessor.from_pretrained(MODEL, local_files_only=True)
    df = pd.read_parquet(PARQUET).head(N_BATCH)
    img = Image.new("RGB", (336, 336), (128, 128, 128))
    inputs = []
    for _, row in df.iterrows():
        text = str(row["instruction"]) + ("\n" + str(row["input"]) if str(row.get("input", "")) else "")
        conv = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": text}]}]
        prompt = processor.apply_chat_template(conv, add_generation_prompt=True)
        inp = processor(text=prompt, images=img, return_tensors="pt")
        labels = inp["input_ids"].clone()
        inputs.append({**inp, "labels": labels})
    model = Qwen2VLForConditionalGeneration.from_pretrained(MODEL, quantization_config=quant,
                                                          device_map="auto", local_files_only=True)
    lora = LoraConfig(task_type=TaskType.CAUSAL_LM, r=RANK, lora_alpha=RANK * 2, lora_dropout=0.0,
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
    pm = get_peft_model(model, lora)
    params = [(n, p) for n, p in pm.named_parameters() if p.requires_grad]
    groups = {"vision": [], "merger": [], "llm": []}
    for n, p in params:
        key = "vision" if "visual" in n else ("merger" if "merger" in n else "llm")
        groups[key].append((n, p))
    results = {"meta": {"script": "tools/_p1511_p3_qwen_hessian.py", "task": "R3.5 curvature (Qwen2-VL-2B)",
                        "model": "Qwen2-VL-2B-Instruct 4-bit + LoRA r=5", "eps": EPS, "n_batches": N_BATCH},
               "runs": []}
    for bi, batch in enumerate(inputs):
        batch = {k: v.cuda() if torch.is_tensor(v) else v for k, v in batch.items()}
        pm.zero_grad(set_to_none=True)
        out = pm(**batch)
        loss0 = out.loss
        loss0.backward()
        grads = {n: p.grad.detach().clone() for n, p in params if p.grad is not None}
        g2 = sum(float((g.float() ** 2).sum()) for g in grads.values())
        curves = {}
        for eps in EPS:
            def probe(sign):
                with torch.no_grad():
                    for n, p in params:
                        if n in grads:
                            p.add_(sign * eps * grads[n].float().to(p.dtype))
                val = float(pm(**batch).loss.item())
                with torch.no_grad():
                    for n, p in params:
                        if n in grads:
                            p.sub_(sign * eps * grads[n].float().to(p.dtype))
                return val
            lp, lm = probe(1.0), probe(-1.0)
            curves[str(eps)] = (lp - 2 * float(loss0.item()) + lm) / (eps ** 2)
        eps = EPS[-1]
        per = {}
        for gname, plist in groups.items():
            sub = {n: grads[n] for n, _ in plist if n in grads}
            if not sub:
                continue
            def probe_group(sign):
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
            lp, lm = probe_group(1.0), probe_group(-1.0)
            per[gname] = (lp - 2 * float(loss0.item()) + lm) / (eps ** 2)
        results["runs"].append({"batch": bi, "loss": float(loss0.item()), "g2": g2, "gHg": curves,
                                "per_group": per,
                                "share_at_lr": {k: 0.5 * 5e-5 * v / g2 for k, v in curves.items()}})
        print(f"  b={bi} loss={float(loss0.item()):.3f} ||g||^2={g2:.3g} gHg(1e-3)={curves['0.001']:.4g} "
              f"share@lr={results['runs'][-1]['share_at_lr']['0.001']:+.4f}", flush=True)
    results["elapsed_min"] = (time.time() - t0) / 60.0
    json.dump(results, open(OUT, "w", encoding="utf-8"), indent=1)
    print("wrote", os.path.relpath(OUT, REPO), f"({results['elapsed_min']:.1f} min)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
