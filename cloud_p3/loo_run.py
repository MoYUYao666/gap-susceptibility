# -*- coding: utf-8 -*-
r"""D1 best-effort third-family runner: LLaVA-OneVision-0.5B, blank-image protocol, ranks 5 and 6.

Standalone (does not reuse paper3/scripts/run_training.py, which assumes LLaVA-1.5's 576 image tokens).
Downloads the model with the HF mirror, applies LoRA to the LLM attention projections, trains on the instruction
parquet (16 train / 4 eval, three epochs), and records the alignment energy trajectory.

    python tools/loo_run.py
"""
from __future__ import annotations

import json
import os

import pandas as pd
import torch

REPO = "/root/autodl-tmp/p3work"
OUT = os.path.join(REPO, "outputs", "analysis")
MODEL_DIR = os.path.join(REPO, "models", "loo-0.5b")
REPO_ID = "llava-hf/llava-onevision-qwen2-0.5b-instruct-hf"
PARQUET = os.path.join(REPO, "paper3", "train-instr-00000.parquet")
NUM_SAMPLES = 20
EPOCHS = 3
LR = 5e-5


def ensure_model():
    if os.path.isdir(MODEL_DIR) and os.listdir(MODEL_DIR):
        return MODEL_DIR
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ.setdefault("HF_HOME", "/root/autodl-tmp/hf")
    from huggingface_hub import snapshot_download
    snapshot_download(REPO_ID, local_dir=MODEL_DIR)
    return MODEL_DIR


def energy(model, inputs, n_vis):
    with torch.no_grad():
        out = model(**inputs, output_hidden_states=True)
    hs = out.hidden_states[-1]
    vis = hs[:, :n_vis, :].mean(dim=1)
    lang = hs[:, n_vis:, :].mean(dim=1)
    return float(((vis - lang) ** 2).sum(dim=-1).mean())


def run_rank(rank, processor, model, df):
    from peft import LoraConfig, get_peft_model
    cfg = LoraConfig(r=rank, lora_alpha=2 * rank, lora_dropout=0.0, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
    model = get_peft_model(model, cfg)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=LR)
    rows = df.head(NUM_SAMPLES).reset_index(drop=True)
    train = rows.iloc[:16]
    evals = rows.iloc[16:]
    img = torch.ones(3, 336, 336).mul(0.5)
    energy_hist = []
    for epoch in range(EPOCHS):
        model.train()
        for _, r in train.iterrows():
            conv = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": str(r["instruction"])}]},
                    {"role": "assistant", "content": [{"type": "text", "text": str(r["output"])}]}]
            text = processor.apply_chat_template(conv, add_generation_prompt=False)
            inp = processor(text=text, images=img, return_tensors="pt")
            inputs = {k: v.cuda() for k, v in inp.items()}
            inputs["labels"] = inputs["input_ids"].clone()
            loss = model(**inputs).loss
            if torch.isfinite(loss):
                opt.zero_grad(set_to_none=True)
                loss.backward()
                opt.step()
        model.eval()
        es = []
        for _, r in evals.iterrows():
            conv = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": str(r["instruction"])}]},
                    {"role": "assistant", "content": [{"type": "text", "text": str(r["output"])}]}]
            text = processor.apply_chat_template(conv, add_generation_prompt=False)
            inp = processor(text=text, images=img, return_tensors="pt")
            inputs = {k: v.cuda() for k, v in inp.items()}
            inputs["labels"] = inputs["input_ids"].clone()
            n_vis = int((inputs["input_ids"] == model.config.image_token_index).sum().item())
            if n_vis <= 0:
                n_vis = 576
            es.append(energy(model, inputs, n_vis))
        energy_hist.append(sum(es) / len(es))
    return energy_hist


def main() -> int:
    os.environ["HF_HUB_OFFLINE"] = "0"
    from transformers import AutoProcessor, BitsAndBytesConfig, LlavaOnevisionForConditionalGeneration
    path = ensure_model()
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
    base = LlavaOnevisionForConditionalGeneration.from_pretrained(path, quantization_config=quant, device_map="auto")
    processor = AutoProcessor.from_pretrained(path)
    df = pd.read_parquet(PARQUET)
    out = {}
    for rank in (5, 6):
        hist = run_rank(rank, processor, base, df)
        out["r%d" % rank] = {"E": hist, "delta_E": hist[-1] - hist[0]}
        print("rank", rank, "E", hist, "dE", hist[-1] - hist[0], flush=True)
    json.dump({"meta": {"script": "tools/loo_run.py", "repo": REPO_ID, "num_samples": NUM_SAMPLES,
                        "epochs": EPOCHS, "lr": LR}, "runs": out},
              open(os.path.join(OUT, "p3_loo_family.json"), "w", encoding="utf-8"), indent=1)
    print("wrote", os.path.join(OUT, "p3_loo_family.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
