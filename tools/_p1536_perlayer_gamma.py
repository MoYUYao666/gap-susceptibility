# -*- coding: utf-8 -*-
r"""Per-layer Gamma on LLaVA with bootstrap confidence intervals (C2).

Integrated-gradient sensitivity per LLM layer (and the vision tower) on the probe adapter, averaged over prompts, with
a prompt-level bootstrap for 95% intervals.

    python tools/_p1536_perlayer_gamma.py
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "p3_perlayer_gamma.json")
MODEL = os.path.join(REPO, "models", "llava-hf")
ADAPTER = os.path.join(REPO, "outputs", "p3_probe_adapter")
PARQUET = os.path.join(REPO, "paper3", "train-instr-00000.parquet")
N_PROMPTS = 8
ALPHAS = [0.0, 0.25, 0.5, 0.75, 1.0]
N_BOOT = 200


def main() -> int:
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    os.environ["HF_HUB_OFFLINE"] = "1"
    torch.manual_seed(42)
    from PIL import Image
    from peft import PeftModel
    from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration

    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                               bnb_4bit_use_double_quant=True)
    base = LlavaForConditionalGeneration.from_pretrained(MODEL, quantization_config=quant, device_map="auto")
    model = PeftModel.from_pretrained(base, ADAPTER, is_trainable=True)
    processor = AutoProcessor.from_pretrained(MODEL)
    img = Image.new("RGB", (336, 336), (128, 128, 128))
    prompts = []
    for _, row in pd.read_parquet(PARQUET).head(N_PROMPTS).iterrows():
        conv = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": str(row["instruction"])}]},
                {"role": "assistant", "content": [{"type": "text", "text": str(row["output"])}]}]
        text = processor.apply_chat_template(conv, add_generation_prompt=False)
        inp = processor(text=text, images=img, return_tensors="pt")
        inp["labels"] = inp["input_ids"].clone()
        prompts.append({k: v.cuda() if torch.is_tensor(v) else v for k, v in inp.items()})
    params = [(n, p) for n, p in model.named_parameters() if p.requires_grad]

    def layer_of(name: str) -> str:
        if "vision_tower" in name:
            return "vision"
        if "language_model" in name and "layers." in name:
            i = name.find("layers.")
            return "llm_%02d" % int(name[i + 7:].split(".")[0])
        return "other"

    per_prompt = []
    for pi, batch in enumerate(prompts):
        theta = {n: p.detach().clone() for n, p in params}
        acc = {}
        for alpha in ALPHAS:
            for n, p in params:
                p.data.copy_(alpha * theta[n])
            model.zero_grad(set_to_none=True)
            loss = model(**batch).loss
            loss.backward()
            for n, p in params:
                if p.grad is None:
                    continue
                k = layer_of(n)
                acc[k] = acc.get(k, 0.0) + float((p.grad.detach().float() * theta[n].float()).abs().sum()) / len(ALPHAS)
            model.zero_grad(set_to_none=True)
        for n, p in params:
            p.data.copy_(theta[n])
        per_prompt.append(acc)
        print(f"  prompt {pi} done", flush=True)
    layers = sorted({k for d in per_prompt for k in d})
    summary = {}
    rng = np.random.default_rng(42)
    arr = np.array([[d.get(k, 0.0) for k in layers] for d in per_prompt])
    for j, k in enumerate(layers):
        vals = arr[:, j]
        boots = [vals[rng.integers(0, len(vals), len(vals))].mean() for _ in range(N_BOOT)]
        summary[k] = {"mean": float(vals.mean()), "sd": float(vals.std(ddof=1)),
                      "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}
    out = {"meta": {"script": "tools/_p1536_perlayer_gamma.py", "task": "C2 per-layer Gamma + bootstrap",
                    "n_prompts": N_PROMPTS, "alphas": ALPHAS, "n_boot": N_BOOT, "adapter": "probe r=8"},
           "layers": summary}
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
    for k in layers:
        s = summary[k]
        print(f"  {k:8s} mean={s['mean']:.4f} ci95=[{s['ci95'][0]:.4f},{s['ci95'][1]:.4f}]")
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
