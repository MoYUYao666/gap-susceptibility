# -*- coding: utf-8 -*-
r"""Bootstrap stability of the CLIP coupling and per-layer CLIP Gamma (C-gamma stability, D2 source-layer check).

Runs on CPU to avoid contention with training jobs.

    python tools/_p1551_clip_gamma_bootstrap.py
"""
from __future__ import annotations

import io
import json
import os

import numpy as np
import torch
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "p3_clip_gamma_bootstrap.json")
MODEL = os.path.join(REPO, "models", "clip-vit-large-patch14")
IMGS = os.path.join(REPO, "data", "marine_captions")
CAPS = os.path.join(IMGS, "captions.json")
BUDGET = 16
BLOCKS = ["vision", "text_shallow", "text_mid", "text_deep"]
N_DRAWS = 3
BATCH = 4
TEXT_LAYERS = 12


def block_of(name: str) -> str:
    if "vision_model" in name:
        return "vision"
    if "text_model.encoder.layers." in name:
        idx = int(name.split("text_model.encoder.layers.")[1].split(".")[0])
        return "text_shallow" if idx <= 3 else ("text_mid" if idx <= 7 else "text_deep")
    return "other"


def layer_of(name: str) -> str:
    if "vision_model" in name:
        return "vision"
    if "text_model.encoder.layers." in name:
        return "text_%02d" % int(name.split("text_model.encoder.layers.")[1].split(".")[0])
    return "other"


def alloc(absg):
    share = np.array([absg[b] for b in BLOCKS], dtype=float)
    share = share / share.sum()
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
    return {b: int(r) for b, r in zip(BLOCKS, ranks)}, share


def main() -> int:
    os.environ["HF_HUB_OFFLINE"] = "1"
    torch.manual_seed(42)
    from transformers import CLIPModel, CLIPProcessor

    model = CLIPModel.from_pretrained(MODEL, local_files_only=True).float()
    proc = CLIPProcessor.from_pretrained(MODEL, local_files_only=True)
    caps = json.load(open(CAPS, encoding="utf-8"))["captions"]
    n = len(caps)
    blocks = {}
    layers = {}
    for name, p in model.named_parameters():
        b = block_of(name)
        if b in BLOCKS:
            blocks.setdefault(b, []).append((name, p))
        l = layer_of(name)
        if l != "other":
            layers.setdefault(l, []).append((name, p))
    rng = np.random.default_rng(42)
    draws = []
    layer_acc = {}
    for di in range(N_DRAWS):
        idxs = rng.integers(0, n, BATCH)
        imgs = [Image.open(os.path.join(IMGS, f"{int(i):04d}.jpg")).convert("RGB") for i in idxs]
        texts = [caps[int(i)] for i in idxs]
        inp = proc(text=texts, images=imgs, return_tensors="pt", padding=True, truncation=True)
        model.zero_grad(set_to_none=True)
        out = model(**inp, return_loss=True)
        L = out.loss
        I = torch.nn.functional.normalize(out.image_embeds, dim=-1)
        T = torch.nn.functional.normalize(out.text_embeds, dim=-1)
        E = ((I - T) ** 2).sum(-1).mean()
        E.backward(retain_graph=True)
        gE = {k: v.grad.detach().float().clone() for k, v in model.named_parameters() if v.grad is not None}
        model.zero_grad(set_to_none=True)
        L.backward()
        gamma = {}
        for b, plist in blocks.items():
            gamma[b] = sum(float(-(gE[k] * v.grad.detach().float()).sum()) for k, v in plist if v.grad is not None)
        alloc_ranks, share = alloc({b: abs(v) for b, v in gamma.items()})
        draws.append({"gamma": gamma, "allocation": alloc_ranks})
        for l, plist in layers.items():
            s = sum(float(-(gE[k] * v.grad.detach().float()).sum()) for k, v in plist if v.grad is not None)
            layer_acc.setdefault(l, []).append(s)
        model.zero_grad(set_to_none=True)
        print(f"  draw {di}: gamma {({k: round(v, 2) for k, v in gamma.items()})} alloc {alloc_ranks}", flush=True)
    ranks_list = [tuple(d["allocation"][b] for b in BLOCKS) for d in draws]
    stable = len(set(ranks_list)) == 1
    layer_mean = {l: {"mean": float(np.mean(v)), "sd": float(np.std(v, ddof=1))} for l, v in sorted(layer_acc.items())}
    out = {"meta": {"script": "tools/_p1551_clip_gamma_bootstrap.py", "task": "Gamma bootstrap stability on CLIP",
                    "n_draws": N_DRAWS, "batch": BATCH},
           "draws": draws, "rank_vectors": ranks_list, "allocation_stable": stable,
           "layer_gamma": layer_mean}
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
    print("allocations:", ranks_list, "stable:", stable)
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
