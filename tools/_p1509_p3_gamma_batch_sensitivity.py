# -*- coding: utf-8 -*-
r"""Reference-batch sensitivity of the per-block Gamma statistic (R1 comment R3.4).

Reuses the protocol of tools/_p462_gamma_real_vs_blank.py (CLIP ViT-B/32, LoRA on both towers, rank 8) and varies
the reference batch: size n in {2,4,8,16} and three disjoint compositions per size. Reports per-block Gamma,
the ordering, and the allocation ranks under the exponential rule.

    python tools/_p1509_p3_gamma_batch_sensitivity.py
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import sys

os.environ.setdefault("HF_HUB_OFFLINE", "1")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "src"))

OUT = os.path.join(REPO, "outputs", "analysis", "p3_gamma_batch_sensitivity.json")
MODEL = os.path.join(REPO, "models", "clip-vit-base-patch32")
IMGS = os.path.join(REPO, "data", "marine_captions")
CAPS = os.path.join(REPO, "data", "marine_captions", "captions.json")
RANK = 8
SIZES = [2, 4, 8, 16]
N_DRAWS = 3


def load_p462():
    spec = importlib.util.spec_from_file_location("p462", os.path.join(REPO, "tools", "_p462_gamma_real_vs_blank.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    import torch
    from PIL import Image
    from transformers import CLIPModel, CLIPProcessor
    from src.lora import apply_lora_to_model
    p462 = load_p462()
    torch.manual_seed(42)
    model = CLIPModel.from_pretrained(MODEL, local_files_only=True)
    for p in model.parameters():
        p.requires_grad = False
    model, layers, n_peft = apply_lora_to_model(model, rank=RANK, alpha=RANK * 2.0, dropout=0.0,
                                               target_modules=["q_proj", "v_proj"],
                                               apply_to_vision=True, apply_to_text=True)
    model = model.float().eval()
    proc = CLIPProcessor.from_pretrained(MODEL, local_files_only=True)
    caps = json.load(io.open(CAPS, encoding="utf-8"))["captions"]
    pool = []
    for i in range(32):
        img = Image.open(os.path.join(IMGS, f"{i:04d}.jpg")).convert("RGB")
        px = proc(images=img, return_tensors="pt")["pixel_values"][0]
        e = proc.tokenizer(text=caps[i], return_tensors="pt", padding="max_length", truncation=True,
                           max_length=77)
        pool.append((px, e["input_ids"][0], e["attention_mask"][0]))
    results = {"meta": {"script": "tools/_p1509_p3_gamma_batch_sensitivity.py", "task": "R3.4 reference-batch sensitivity",
                        "model": "CLIP ViT-B/32 + LoRA r=8", "sizes": SIZES, "n_draws": N_DRAWS},
               "conditions": []}
    for n in SIZES:
        draws = []
        for d in range(min(N_DRAWS, len(pool) // n)):
            idx = list(range(d * n, d * n + n))
            px = torch.stack([pool[i][0] for i in idx])
            ids = torch.stack([pool[i][1] for i in idx])
            am = torch.stack([pool[i][2] for i in idx])
            g = p462.measure(model, px, ids, am, "cpu")
            draws.append({b: v["gamma"] for b, v in g.items()})
        blocks = list(draws[0])
        mean = {b: sum(dd[b] for dd in draws) / len(draws) for b in blocks}
        sd = {b: (sum((dd[b] - mean[b]) ** 2 for dd in draws) / max(len(draws) - 1, 1)) ** 0.5 for b in blocks}
        absg = {b: abs(mean[b]) for b in blocks}
        order = sorted(blocks, key=lambda b: absg[b], reverse=True)
        # allocation ranks with the exponential rule, budget 16, beta = 1/mean(abs Gamma)
        total = sum(absg.values()) or 1.0
        ranks = {}
        budget = 16
        w = {b: absg[b] / total for b in blocks}
        raw = {b: max(1, int(round(w[b] * budget))) for b in blocks}
        while sum(raw.values()) != budget:
            if sum(raw.values()) < budget:
                b = max(blocks, key=lambda x: w[x] * budget - raw[x])
                raw[b] += 1
            else:
                b = max(blocks, key=lambda x: raw[x])
                if raw[b] > 1:
                    raw[b] -= 1
                else:
                    break
        ranks = raw
        results["conditions"].append({"n": n, "draw": d, "gamma": mean, "gamma_sd": sd, "abs_order": order,
                                      "ranks": ranks})
        print(f"  n={n} d={d} order={order} ranks={ranks} sd={ {k: round(v,3) for k,v in sd.items()} }", flush=True)
    # summary: CV per block across all conditions
    blocks = list(results["conditions"][0]["gamma"])
    summary = {}
    for b in blocks:
        vals = [c["gamma"][b] for c in results["conditions"]]
        m = sum(vals) / len(vals)
        sd = (sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5
        summary[b] = {"mean": m, "sd": sd, "cv": sd / abs(m) if m else None,
                      "min": min(vals), "max": max(vals)}
    results["summary"] = summary
    json.dump(results, open(OUT, "w", encoding="utf-8"), indent=1)
    print("summary:", {k: round(v["cv"], 3) if v["cv"] else None for k, v in summary.items()})
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
