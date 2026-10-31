# -*- coding: utf-8 -*-
r"""IGU-LoRA allocation equations applied at block level (official repository inspected).

The released IGU-LoRA code (github.com/withyou12/igulora, cloned under external/igulora) implements rank allocation with
SVD-LoRA modules inside a text-LLM training pipeline; it cannot be dropped into the 4-bit LLaVA training loop directly.
This script applies the published allocation equations (Eq. 4-7 of arXiv 2603.13792) to our probe adapter:
  * integrated-gradient sensitivity of each LoRA delta-W along the zero -> current path, at alpha in {0,.25,.5,.75,1};
  * per-rank score by projecting the IG matrix onto the singular basis of delta-W;
  * block scores aggregated from module scores, then normalized to the paper's budget of 16 ranks.

    python tools/_p1530_igu_allocation.py
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "p3_igu_allocation.json")
MODEL = os.path.join(REPO, "models", "llava-hf")
ADAPTER = os.path.join(REPO, "outputs", "p3_probe_adapter")
PARQUET = os.path.join(REPO, "paper3", "train-instr-00000.parquet")
BUDGET = 16


def block_of(name: str) -> str:
    if "vision_tower" in name:
        return "vision"
    if "language_model" in name:
        i = name.find("layers.")
        idx = int(name[i + 7:].split(".")[0])
        return "text_shallow" if idx <= 7 else ("text_mid" if idx <= 23 else "text_deep")
    return "other"


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
    row = pd.read_parquet(PARQUET).iloc[0]
    img = Image.new("RGB", (336, 336), (128, 128, 128))
    conv = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": str(row["instruction"])}]},
            {"role": "assistant", "content": [{"type": "text", "text": str(row["output"])}]}]
    prompt = processor.apply_chat_template(conv, add_generation_prompt=False)
    inp = processor(text=prompt, images=img, return_tensors="pt")
    inp["labels"] = inp["input_ids"].clone()
    inp = {k: v.cuda() if torch.is_tensor(v) else v for k, v in inp.items()}
    params = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    theta = {n: p.detach().clone() for n, p in params}
    alphas = [0.0, 0.25, 0.5, 0.75, 1.0]
    grads = {n: torch.zeros_like(p) for n, p in params}
    for alpha in alphas:
        for n, p in params:
            p.data.copy_(alpha * theta[n])
        model.zero_grad(set_to_none=True)
        loss = model(**inp).loss
        loss.backward()
        for n, p in params:
            if p.grad is not None:
                grads[n] += p.grad.detach().float() / len(alphas)
        model.zero_grad(set_to_none=True)
    for n, p in params:
        p.data.copy_(theta[n])
    # group per LoRA module
    mods = {}
    for n, p in params:
        key = n.split(".lora_")[0]
        kind = "A" if ".lora_A" in n else ("B" if ".lora_B" in n else None)
        if kind is None:
            continue
        mods.setdefault(key, {})[kind] = (n, theta[n].float(), grads[n])
    block_scores = {k: 0.0 for k in ("vision", "text_shallow", "text_mid", "text_deep")}
    module_rows = []
    for key, d in mods.items():
        if "A" not in d or "B" not in d:
            continue
        nA, A, gA = d["A"]
        nB, B, gB = d["B"]
        dW = B @ A                       # out x in
        G = gB @ A + B @ gA              # gradient of loss wrt dW
        IG = dW * G                      # Eq. 4 sensitivity (first-order per unit path)
        # thin QR of the LoRA factors keeps everything in r x r space (no full SVD of dW)
        Bq, Br = torch.linalg.qr(B, mode="reduced")
        Aq, Ar = torch.linalg.qr(A.T, mode="reduced")
        M = Bq.T @ IG @ Aq               # r x r compressed sensitivity
        core = Br @ Ar.T                 # r x r core of dW
        Us, S, Vs = torch.linalg.svd(core, full_matrices=False)
        scores = torch.abs((Us.T @ M @ Vs).diagonal()).tolist()
        total = float(np.sum(scores))
        blk = block_of(nA)
        if blk in block_scores:
            block_scores[blk] += total
        module_rows.append({"module": key, "block": blk, "rank_scores": scores, "total": total,
                            "n_ranks": len(scores)})
    keys = list(block_scores)
    w = np.array([block_scores[k] for k in keys])
    # allocation: proportional to block score, min 1, exactly BUDGET
    share = w / w.sum() if w.sum() > 0 else np.ones_like(w) / len(w)
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
    out = {"meta": {"script": "tools/_p1530_igu_allocation.py",
                    "source": "IGU-LoRA equations Eq. 4-7 (arXiv 2603.13792); official repo external/igulora inspected",
                    "budget": BUDGET},
           "block_scores": block_scores, "share": {k: float(s) for k, s in zip(keys, share)},
           "allocation": {k: int(r) for k, r in zip(keys, ranks)},
           "modules": module_rows}
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
    print("block scores:", {k: round(v, 4) for k, v in block_scores.items()})
    print("allocation:", out["allocation"])
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
