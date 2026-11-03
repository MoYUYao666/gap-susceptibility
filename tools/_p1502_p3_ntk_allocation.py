# -*- coding: utf-8 -*-
r"""NTK-based and gradient-energy allocation baselines for P3 (R1 comments R2.4 / R3.9).

Computes per-block Gauss-Newton (NTK-diagonal) traces on CLIP ViT-B/32 with real marine image-caption pairs, derives
rank allocations under the paper's budget rule, and compares the ordering with the archived Gamma allocation.

    python tools/_p1502_p3_ntk_allocation.py
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np
import torch
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "p3_ntk_allocation.json")
CLIP = os.path.join(REPO, "models", "clip-vit-base-patch32")
CAP = os.path.join(REPO, "data", "marine_captions", "captions.json")
IMGS = os.path.join(REPO, "data", "marine_captions")
BUDGET = 16
N_BATCH = 4
BATCH = 4


def main() -> int:
    torch.manual_seed(42)
    caps = json.load(open(CAP, encoding="utf-8"))
    seq = caps["captions"] if isinstance(caps, dict) else caps
    items = [(f"{i:04d}.jpg", seq[i]) for i in range(min(len(seq), N_BATCH * BATCH))]
    from transformers import CLIPModel, CLIPProcessor
    model = CLIPModel.from_pretrained(CLIP).eval()
    proc = CLIPProcessor.from_pretrained(CLIP)
    blocks = {"vision": [], "text_shallow": [], "text_mid": [], "text_deep": []}
    for n, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if n.startswith("vision_model"):
            blocks["vision"].append((n, p))
        elif n.startswith("text_model.encoder.layers."):
            idx = int(n.split(".")[3]) if n.split(".")[3].isdigit() else 0
            key = "text_shallow" if idx <= 2 else ("text_mid" if idx <= 8 else "text_deep")
            blocks[key].append((n, p))
    trace = {k: 0.0 for k in blocks}
    nb = 0
    for b in range(N_BATCH):
        chunk = items[b * BATCH:(b + 1) * BATCH]
        images = []
        texts = []
        for key, v in chunk:
            f = os.path.join(IMGS, key if key.endswith(".jpg") else f"{int(key):04d}.jpg")
            if not os.path.exists(f):
                cand = glob.glob(os.path.join(IMGS, "*.jpg"))
                f = cand[0]
            images.append(Image.open(f).convert("RGB"))
            texts.append(v if isinstance(v, str) else str(v))
        inp = proc(text=texts, images=images, return_tensors="pt", padding=True, truncation=True)
        model.zero_grad(set_to_none=True)
        out = model(**inp)
        logits = out.logits_per_image
        target = torch.arange(len(texts))
        loss = (torch.nn.functional.cross_entropy(logits, target) +
                torch.nn.functional.cross_entropy(logits.t(), target)) / 2
        loss.backward()
        for k, plist in blocks.items():
            s = 0.0
            for n, p in plist:
                if p.grad is not None:
                    s += float((p.grad.float() ** 2).sum())
            trace[k] += s
        nb += 1
    trace = {k: v / max(nb, 1) for k, v in trace.items()}
    # Gamma allocation from the archived CLIP measurement (r=8, real condition)
    gamma = {}
    gp = os.path.join(REPO, "outputs", "analysis", "p3d_gamma_real_vs_blank.json")
    if os.path.exists(gp):
        g = json.load(open(gp, encoding="utf-8"))
        for k in ("vision", "text_shallow", "text_mid", "text_deep"):
            try:
                gamma[k] = abs(float(g["conditions"]["real"]["blocks"][k]["gamma"]))
            except Exception:
                pass

    def alloc(weights: dict) -> dict:
        keys = list(weights)
        w = np.array([max(float(weights[k]), 1e-12) for k in keys])
        share = w / w.sum()
        ranks = np.maximum(1, np.round(share * BUDGET)).astype(int)
        # enforce exact budget by adjusting the largest remainder
        while ranks.sum() > BUDGET:
            i = int(np.argmax(ranks))
            if ranks[i] > 1:
                ranks[i] -= 1
            else:
                break
        while ranks.sum() < BUDGET:
            i = int(np.argmin(share * BUDGET - ranks))
            ranks[i] += 1
        return {k: int(r) for k, r in zip(keys, ranks)}

    report = {"meta": {"script": "tools/_p1502_p3_ntk_allocation.py", "task": "R3.9 NTK/gradient baseline",
                       "model": "CLIP ViT-B/32", "data": "marine image-caption pairs", "budget": BUDGET,
                       "n_batches": nb},
              "ntk_trace": trace, "gamma_abs": gamma,
              "allocation_ntk": alloc(trace),
              "allocation_gamma": alloc(gamma) if gamma else None,
              "allocation_uniform": alloc({k: 1.0 for k in trace})}
    json.dump(report, open(OUT, "w", encoding="utf-8"), indent=1)
    print(json.dumps(report, indent=1))
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
