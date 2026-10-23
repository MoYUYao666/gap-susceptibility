# -*- coding: utf-8 -*-
r"""Empirical test of the block-additivity assumption (R3' / R1.5) on the probe adapter.

For every subset S of the four blocks, zero the LoRA B-matrices of blocks outside S and measure the alignment energy
E(S) on held-out instruction batches. The pair residual r(A,B) = E(A u B) - E(A) - E(B) + E(empty) quantifies the
violation of block additivity. Per-prompt residuals are bootstrap-resampled for a 95% CI.

    python tools/_p1534_additivity_residual.py [--n-eval 8]
"""
from __future__ import annotations

import argparse
import itertools
import json
import os

import numpy as np
import pandas as pd
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "p3_additivity_residual.json")
MODEL = os.path.join(REPO, "models", "llava-hf")
ADAPTER = os.path.join(REPO, "outputs", "p3_probe_adapter")
PARQUET = os.path.join(REPO, "paper3", "train-instr-00000.parquet")
BLOCKS = ["vision", "text_shallow", "text_mid", "text_deep"]
N_BOOT = 2000


def block_of(name: str) -> str:
    if "vision_tower" in name:
        return "vision"
    if "language_model" in name:
        i = name.find("layers.")
        idx = int(name[i + 7:].split(".")[0])
        return "text_shallow" if idx <= 7 else ("text_mid" if idx <= 23 else "text_deep")
    return "other"


def energy(model, inp):
    with torch.no_grad():
        out = model(**inp, output_hidden_states=True)
    hs = out.hidden_states[-1]
    vis = hs[:, :576, :]
    lang = hs[:, 576:, :]
    h_vis = vis.mean(dim=1)
    h_lang = lang.mean(dim=1)
    return float(((h_vis - h_lang) ** 2).sum(dim=-1).mean())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-eval", type=int, default=8)
    a = ap.parse_args()
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
    df = pd.read_parquet(PARQUET).head(a.n_eval)
    img = Image.new("RGB", (336, 336), (128, 128, 128))
    items = []
    for _, row in df.iterrows():
        conv = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": str(row["instruction"])}]},
                {"role": "assistant", "content": [{"type": "text", "text": str(row["output"])}]}]
        text = processor.apply_chat_template(conv, add_generation_prompt=False)
        inp = processor(text=text, images=img, return_tensors="pt")
        inp["labels"] = inp["input_ids"].clone()
        items.append({k: v.cuda() if torch.is_tensor(v) else v for k, v in inp.items()})
    lora_b = [(n, p) for n, p in model.named_parameters() if "lora_B" in n]
    saved = {n: p.detach().clone() for n, p in lora_b}
    energies = {}
    for r in range(len(BLOCKS) + 1):
        for keep in itertools.combinations(BLOCKS, r):
            for n, p in lora_b:
                if block_of(n) in BLOCKS and block_of(n) not in keep:
                    p.data.zero_()
            energies[keep] = [energy(model, inp) for inp in items]
            for n, p in lora_b:
                p.data.copy_(saved[n])
            print(f"  keep={keep} E={np.mean(energies[keep]):.1f}", flush=True)
    empty = np.array(energies[()])
    pairs = []
    rng = np.random.default_rng(42)
    for a_, b_ in itertools.combinations(BLOCKS, 2):
        ab = tuple(sorted((a_, b_), key=BLOCKS.index))
        resid = np.array(energies[ab]) - np.array(energies[(a_,)]) - np.array(energies[(b_,)]) + empty
        boots = [float(np.mean(rng.choice(resid, len(resid), replace=True))) for _ in range(N_BOOT)]
        scale = float(np.mean(energies[ab])) + 1e-9
        pairs.append({"A": a_, "B": b_, "E_union": float(np.mean(energies[ab])),
                      "E_A": float(np.mean(energies[(a_,)])), "E_B": float(np.mean(energies[(b_,)])),
                      "E_empty": float(np.mean(empty)), "residual": float(resid.mean()),
                      "relative": float(resid.mean() / scale),
                      "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]})
    out = {"meta": {"script": "tools/_p1534_additivity_residual.py", "task": "R3' additivity test",
                    "n_eval": a.n_eval, "adapter": "probe r=8", "n_boot": N_BOOT},
           "energies": {"+".join(k) if k else "empty": float(np.mean(v)) for k, v in energies.items()},
           "pair_residuals": pairs,
           "max_abs_relative": max(abs(p["relative"]) for p in pairs)}
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
    for p in pairs:
        print(f"  {p['A']}+{p['B']}: residual {p['residual']:+.1f} ({100*p['relative']:+.2f}%) "
              f"CI95 [{p['ci95'][0]:+.2f},{p['ci95'][1]:+.2f}]")
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
