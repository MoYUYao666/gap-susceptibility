# -*- coding: utf-8 -*-
r"""Block-allocation baselines in the spirit of HALoRA, IGU-LoRA and ShapLoRA, with trained arms (R1 R2.4/R3.9).

Protocol
--------
A probe LLaVA adapter (r=8, one epoch) is trained; on it three block-level rules are computed:
  * HALoRA-style      : budget split between vision and LLM proportional to trainable-parameter mass, then across the
                        LLM depth blocks proportional to layer counts (8/16/8);
  * IGU-LoRA-style    : integrated gradients of the task loss along the linear path from the zero adapter to the probe
                        adapter, summed per block;
  * ShapLoRA-style    : exact Shapley values over the four blocks of the linearised loss reduction (16 subset
                        evaluations with block-zeroing);
each rule gives ranks summing to 16, then one trained arm per rule (three epochs, blank-image protocol).

Modes
-----
    python tools/_p1514_p3_baseline_rules.py --probe-smoke
    python tools/_p1514_p3_baseline_rules.py --probe-full
    python tools/_p1514_p3_baseline_rules.py --arms
"""
from __future__ import annotations

import argparse
import io
import itertools
import json
import math
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "p3_baseline_rules.json")
PROBE = os.path.join(REPO, "outputs", "p3_probe_adapter")
MODEL = os.path.join(REPO, "models", "llava-hf")
PARQUET = os.path.join(REPO, "paper3", "train-instr-00000.parquet")
TRAIN = os.path.join(REPO, "paper3", "scripts", "run_training.py")
BUDGET = 16
# block -> (LoRA parameter-name predicate, layer count in the LLM depth split)
BLOCKS = ["vision", "text_shallow", "text_mid", "text_deep"]


def block_of(name: str) -> str:
    if "vision_tower" in name:
        return "vision"
    if "language_model" in name:
        i = name.find("layers.")
        if i < 0:
            return "llm_other"
        idx = int(name[i + 7:].split(".")[0])
        return "text_shallow" if idx <= 7 else ("text_mid" if idx <= 23 else "text_deep")
    return "llm_other"


def train_probe(samples: int, epochs: int) -> None:
    subprocess.run([sys.executable, TRAIN, "--rank", "8", "--seed", "42", "--epochs", str(epochs),
                    "--num-samples", str(samples), "--save-adapter-dir", PROBE], check=False)


def load_probe():
    from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration
    from peft import PeftModel
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                               bnb_4bit_use_double_quant=True)
    processor = AutoProcessor.from_pretrained(MODEL)
    base = LlavaForConditionalGeneration.from_pretrained(MODEL, quantization_config=quant, device_map="auto")
    model = PeftModel.from_pretrained(base, PROBE, is_trainable=True)
    model.eval()
    return processor, model


def batch(processor, row):
    from PIL import Image
    img = Image.new("RGB", (336, 336), (128, 128, 128))
    text = f"USER: {row['instruction']}" + (f"\n{row['input']}" if row.get("input") else "") + f"\nASSISTANT: {row['output']}"
    conv = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": str(row["instruction"])}]},
            {"role": "assistant", "content": [{"type": "text", "text": str(row["output"])}]}]
    prompt = processor.apply_chat_template(conv, add_generation_prompt=False)
    inp = processor(text=prompt, images=img, return_tensors="pt")
    inp["labels"] = inp["input_ids"].clone()
    return {k: v.cuda() if torch.is_tensor(v) else v for k, v in inp.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe-smoke", action="store_true")
    ap.add_argument("--probe-full", action="store_true")
    ap.add_argument("--arms", action="store_true")
    args = ap.parse_args()
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    os.environ["HF_HUB_OFFLINE"] = "1"
    if args.arms:
        alloc = json.load(io.open(OUT, encoding="utf-8"))["allocation"]
        results = {}
        for name, ranks in alloc.items():
            out = subprocess.run([sys.executable, TRAIN, "--rank", "1", "--rank-vision", str(ranks["vision"]),
                                  "--rank-shallow", str(ranks["text_shallow"]), "--rank-mid", str(ranks["text_mid"]),
                                  "--rank-deep", str(ranks["text_deep"]), "--seed", "42", "--epochs", "3",
                                  "--num-samples", "20"], capture_output=True, text=True, encoding="utf-8",
                                 errors="replace")
            m = [ln for ln in (out.stdout or "").splitlines() if "Change:" in ln]
            results[name] = {"ranks": ranks, "delta_line": m[-1] if m else None}
            print(name, ranks, m[-1] if m else "no result", flush=True)
        json.dump(results, io.open(os.path.join(REPO, "outputs", "analysis", "p3_baseline_arms.json"), "w",
                                   encoding="utf-8"), indent=1)
        return 0
    samples, epochs = (8, 1) if args.probe_smoke else (20, 3)
    if not os.path.exists(os.path.join(PROBE, "adapter_config.json")):
        train_probe(samples, epochs)
    if not os.path.exists(os.path.join(PROBE, "adapter_config.json")):
        print("probe adapter missing")
        return 1
    processor, model = load_probe()
    df = pd.read_parquet(PARQUET).head(samples)
    b = batch(processor, df.iloc[0])
    params = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    theta = {n: p.detach().clone() for n, p in params}
    groups = {k: [] for k in BLOCKS}
    for n, p in params:
        groups.setdefault(block_of(n), []).append((n, p))
    # parameter mass (HALoRA-style)
    mass = {k: sum(int(np.prod(p.shape)) for _, p in v) for k, v in groups.items() if k in BLOCKS}
    total = sum(mass.values())
    w = {k: mass[k] / total for k in mass}
    # split LLM mass between vision and LLM: vision share vs LLM share
    vis_share = w["vision"]
    llm_depth = {"text_shallow": 8, "text_mid": 16, "text_deep": 8}
    llm_total = sum(llm_depth.values())
    halora = {"vision": max(1, int(round(vis_share * BUDGET)))}
    rest = BUDGET - halora["vision"]
    halora.update({k: max(1, int(round(rest * v / llm_total))) for k, v in llm_depth.items()})
    while sum(halora.values()) != BUDGET:
        k = max(halora, key=lambda x: halora[x])
        if sum(halora.values()) > BUDGET and halora[k] > 1:
            halora[k] -= 1
        elif sum(halora.values()) < BUDGET:
            halora[k] += 1
        else:
            break
    # IGU-style: integrated gradients along zero -> probe path
    ig = {k: 0.0 for k in BLOCKS}
    alphas = [0.0, 0.25, 0.5, 0.75, 1.0]
    for alpha in alphas:
        for n, p in params:
            p.data.copy_(alpha * theta[n])
        model.zero_grad(set_to_none=True)
        out = model(**b)
        out.loss.backward()
        for n, p in params:
            k = block_of(n)
            if k in ig and p.grad is not None:
                ig[k] += float((p.grad.detach().float() * theta[n].float()).sum()) / len(alphas)
        model.zero_grad(set_to_none=True)
    for n, p in params:
        p.data.copy_(theta[n])
    # ShapLoRA-style: exact Shapley over blocks with block-zeroing (linearised loss reduction)
    base_loss = float(model(**b).loss.item())
    vals = {}
    for r in range(len(BLOCKS) + 1):
        for keep in itertools.combinations(BLOCKS, r):
            for n, p in params:
                k = block_of(n)
                if k in BLOCKS and k not in keep:
                    p.data.zero_()
            with torch.no_grad():
                vals[keep] = float(model(**b).loss.item())
            for n, p in params:
                p.data.copy_(theta[n])
    shap = {}
    for k in BLOCKS:
        s = 0.0
        for keep in vals:
            if k in keep:
                continue
            k2 = tuple(sorted(keep + (k,), key=BLOCKS.index))
            wgt = math.factorial(len(keep)) * math.factorial(len(BLOCKS) - len(keep) - 1) / math.factorial(len(BLOCKS))
            s += wgt * (vals[keep] - vals[k2])  # loss reduction when adding k
        shap[k] = s

    def alloc_from(weights):
        keys = list(BLOCKS)
        wv = np.array([max(weights[k], 1e-9) for k in keys])
        share = wv / wv.sum()
        ranks = np.maximum(1, np.round(share * BUDGET)).astype(int)
        while ranks.sum() > BUDGET:
            i = int(np.argmax(ranks))
            if ranks[i] > 1:
                ranks[i] -= 1
            else:
                break
        while ranks.sum() < BUDGET:
            i = int(np.argmin(share * BUDGET - ranks))
            ranks[i] += 1
        return {k: int(v) for k, v in zip(keys, ranks)}

    out = {"meta": {"script": "tools/_p1514_p3_baseline_rules.py", "budget": BUDGET,
                    "probe": {"samples": samples, "epochs": epochs},
                    "note": "block-level reimplementations in the spirit of HALoRA / IGU-LoRA / ShapLoRA; not the "
                            "official implementations"},
           "mass": mass, "halora": halora,
           "igu_raw": ig, "igu_weights": {k: abs(v) for k, v in ig.items()},
           "shapley": shap, "shapley_weights": {k: abs(v) for k, v in shap.items()},
           "allocation": {"halora": halora,
                          "igu": alloc_from({k: abs(v) for k, v in ig.items()}),
                          "shap": alloc_from({k: abs(v) for k, v in shap.items()})}}
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("HALoRA", halora)
    print("IG weights", {k: round(abs(v), 3) for k, v in ig.items()})
    print("Shapley", {k: round(abs(v), 3) for k, v in shap.items()})
    print("allocation", out["allocation"])
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
