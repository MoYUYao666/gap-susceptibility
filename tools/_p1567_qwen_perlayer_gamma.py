# -*- coding: utf-8 -*-
r"""Per-layer integrated-gradient coupling of Qwen2.5-VL-3B (second model for the layer-wise check).

    python tools/_p1567_qwen_perlayer_gamma.py
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np
import pandas as pd
import torch
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "p3_qwen_perlayer_gamma.json")
MODEL = None
for cand in glob.glob(os.path.join(REPO, "models", "ms_cache", "models", "Qwen--Qwen2.5-VL-3B-Instruct", "snapshots", "*")):
    if os.path.exists(os.path.join(cand, "config.json")):
        MODEL = cand
PARQUET = os.path.join(REPO, "paper3", "train-instr-00000.parquet")
ALPHAS = [0.0, 0.25, 0.5, 0.75, 1.0]
N_PROMPTS = 6
N_BOOT = 200


def layer_of(name):
    if "language_model.layers." in name:
        try:
            i = int(name.split("language_model.layers.")[1].split(".")[0])
            return "llm_%02d" % i
        except Exception:
            return "other"
    return "other"


def main() -> int:
    os.environ["HF_HUB_OFFLINE"] = "1"
    assert MODEL, "Qwen2.5-VL-3B not downloaded"
    from peft import LoraConfig, get_peft_model
    from transformers import AutoProcessor, BitsAndBytesConfig, Qwen2_5_VLForConditionalGeneration

    q = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
    base = Qwen2_5_VLForConditionalGeneration.from_pretrained(MODEL, quantization_config=q, device_map="auto")
    model = get_peft_model(base, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0,
                                            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]))
    proc = AutoProcessor.from_pretrained(MODEL)
    df = pd.read_parquet(PARQUET).head(N_PROMPTS)
    img = Image.new("RGB", (336, 336), (128, 128, 128))
    prompts = []
    for _, row in df.iterrows():
        conv = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": str(row["instruction"])}]},
                {"role": "assistant", "content": [{"type": "text", "text": str(row["output"])}]}]
        text = proc.apply_chat_template(conv, add_generation_prompt=False)
        inp = proc(text=[text], images=[img], return_tensors="pt")
        inp["labels"] = inp["input_ids"].clone()
        prompts.append({k: v.cuda() if torch.is_tensor(v) else v for k, v in inp.items()})
    params = [(n, p) for n, p in model.named_parameters() if p.requires_grad and layer_of(n) != "other"]
    theta = {n: p.detach().clone() for n, p in params}
    per_prompt = []
    for pi, inp in enumerate(prompts):
        acc = {}
        for alpha in ALPHAS:
            for n, p in params:
                p.data.copy_(alpha * theta[n])
            model.zero_grad(set_to_none=True)
            out = model(**inp, output_hidden_states=True)
            hs = out.hidden_states[-1]
            img_tok = model.config.image_token_id
            n_vis = int((inp["input_ids"] == img_tok).sum().item())
            if n_vis <= 0:
                n_vis = 1
            E = ((hs[:, :n_vis].mean(1) - hs[:, n_vis:].mean(1)) ** 2).sum(-1).mean()
            E.backward(retain_graph=True)
            gE = {n: p.grad.detach().float().clone() for n, p in params if p.grad is not None}
            model.zero_grad(set_to_none=True)
            loss = model(**inp).loss
            loss.backward()
            for n, p in params:
                if p.grad is None or n not in gE:
                    continue
                k = layer_of(n)
                acc[k] = acc.get(k, 0.0) + float(-(gE[n] * p.grad.detach().float()).sum()) / len(ALPHAS)
            model.zero_grad(set_to_none=True)
        for n, p in params:
            p.data.copy_(theta[n])
        per_prompt.append(acc)
        print("  prompt", pi, flush=True)
    layers = sorted({k for d in per_prompt for k in d})
    rng = np.random.default_rng(42)
    summary = {}
    for k in layers:
        vals = np.array([d.get(k, 0.0) for d in per_prompt])
        boots = [vals[rng.integers(0, len(vals), len(vals))].mean() for _ in range(N_BOOT)]
        summary[k] = {"mean": float(vals.mean()), "sd": float(vals.std(ddof=1)),
                      "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}
    json.dump({"meta": {"script": "tools/_p1567_qwen_perlayer_gamma.py", "model": "Qwen2.5-VL-3B-Instruct",
                        "n_prompts": N_PROMPTS, "alphas": ALPHAS, "n_boot": N_BOOT},
               "layers": summary}, open(OUT, "w", encoding="utf-8"), indent=1)
    print("wrote", os.path.relpath(OUT, REPO), "layers", len(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
