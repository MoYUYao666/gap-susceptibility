# -*- coding: utf-8 -*-
r"""Third-family control: SmolVLM-500M-Instruct (Idefics3 family), blank-image protocol, ranks 5 and 6.

    python tools/_p1568_smolvlm_run.py
"""
from __future__ import annotations

import argparse
import glob
import json
import os

import pandas as pd
import torch
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "p3_smolvlm_family.json")
PARQUET = os.path.join(REPO, "paper3", "train-instr-00000.parquet")
MODEL = None
for cand in glob.glob(os.path.join(REPO, "models", "ms_cache", "models", "HuggingFaceTB--SmolVLM-500M-Instruct", "snapshots", "*")):
    if os.path.exists(os.path.join(cand, "config.json")):
        MODEL = cand
NUM_SAMPLES = 20
EPOCHS = 3
LR = 5e-5
SEED = 42


def energy(model, inputs, img_id):
    with torch.no_grad():
        out = model(**inputs, output_hidden_states=True)
    hs = out.hidden_states[-1]
    mask = inputs["input_ids"][0] == img_id
    if mask.sum() == 0:
        return float("nan")
    vis = hs[0][mask].mean(0)
    lang = hs[0][~mask].mean(0)
    return float(((vis - lang) ** 2).sum())


def run_rank(rank, proc, model, df, img_id):
    torch.manual_seed(SEED)
    from peft import LoraConfig, get_peft_model
    model = get_peft_model(model, LoraConfig(r=rank, lora_alpha=2 * rank, lora_dropout=0.0,
                                             target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]))
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=LR)
    rows = df.head(NUM_SAMPLES).reset_index(drop=True)
    train, evals = rows.iloc[:16], rows.iloc[16:]
    img = Image.new("RGB", (384, 384), (128, 128, 128))
    conv_txt = lambda r: proc.apply_chat_template(
        [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": str(r["instruction"])}]},
         {"role": "assistant", "content": [{"type": "text", "text": str(r["output"])}]}],
        add_generation_prompt=False)
    hist = []
    for epoch in range(EPOCHS):
        model.train()
        for _, r in train.iterrows():
            inp = proc(text=[conv_txt(r)], images=[img], return_tensors="pt")
            inputs = {k: v.cuda() if torch.is_tensor(v) else v for k, v in inp.items()}
            inputs["labels"] = inputs["input_ids"].clone()
            loss = model(**inputs).loss
            if torch.isfinite(loss):
                opt.zero_grad(set_to_none=True)
                loss.backward()
                opt.step()
        model.eval()
        es = []
        for _, r in evals.iterrows():
            inp = proc(text=[conv_txt(r)], images=[img], return_tensors="pt")
            inputs = {k: v.cuda() if torch.is_tensor(v) else v for k, v in inp.items()}
            inputs["labels"] = inputs["input_ids"].clone()
            es.append(energy(model, inputs, img_id))
        hist.append(float(sum(es) / len(es)))
        print("  rank", rank, "epoch", epoch, "E", hist[-1], flush=True)
    return hist


def main() -> int:
    global SEED
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    SEED = a.seed
    torch.manual_seed(SEED)
    os.environ["HF_HUB_OFFLINE"] = "1"
    assert MODEL, "SmolVLM-500M not downloaded"
    from transformers import AutoModelForImageTextToText, AutoProcessor
    proc = AutoProcessor.from_pretrained(MODEL)
    model = AutoModelForImageTextToText.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="auto")
    img_id = getattr(model.config, "image_token_id", None) or getattr(model.config, "image_token_index", None)
    df = pd.read_parquet(PARQUET)
    out = {}
    for rank in (5, 6):
        # fresh base each rank: reload the LoRA-free weights
        m = AutoModelForImageTextToText.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="auto")
        hist = run_rank(rank, proc, m, df, img_id)
        out["r%d" % rank] = {"E": hist, "delta_E": hist[-1] - hist[0]}
        print("rank", rank, "dE", hist[-1] - hist[0], flush=True)
        del m
        torch.cuda.empty_cache()
    json.dump({"meta": {"script": "tools/_p1568_smolvlm_run.py", "seed": SEED, "model": "SmolVLM-500M-Instruct",
                        "num_samples": NUM_SAMPLES, "epochs": EPOCHS, "lr": LR}, "runs": out},
              open(OUT.replace(".json", "_s%d.json" % SEED), "w", encoding="utf-8"), indent=1)
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
