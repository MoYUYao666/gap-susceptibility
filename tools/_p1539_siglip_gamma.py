# -*- coding: utf-8 -*-
r"""Gamma computed on a non-CLIP source model (SigLIP) and the resulting allocation (D2).

    python tools/_p1539_siglip_gamma.py
"""
from __future__ import annotations

import json
import os

import numpy as np
import torch
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "p3_siglip_gamma.json")
MODEL = os.path.join(REPO, "models", "siglip-base-patch16-224")
IMGS = os.path.join(REPO, "data", "marine_captions")
CAPS = os.path.join(IMGS, "captions.json")
BUDGET = 16
BLOCKS = ["vision", "text_shallow", "text_mid", "text_deep"]


def block_of(name: str) -> str:
    if "vision_model" in name:
        return "vision"
    if "text_model.encoder.layers." in name:
        idx = int(name.split("text_model.encoder.layers.")[1].split(".")[0])
        return "text_shallow" if idx <= 3 else ("text_mid" if idx <= 7 else "text_deep")
    return "other"


def main() -> int:
    os.environ["HF_HUB_OFFLINE"] = "1"
    torch.manual_seed(42)
    from transformers import SiglipModel, SiglipProcessor

    model = SiglipModel.from_pretrained(MODEL, local_files_only=True).float().cuda()
    model.eval()
    proc = SiglipProcessor.from_pretrained(MODEL, local_files_only=True)
    caps = json.load(open(CAPS, encoding="utf-8"))["captions"]
    blocks = {}
    for n, p in model.named_parameters():
        b = block_of(n)
        if b in BLOCKS:
            blocks.setdefault(b, []).append((n, p))
    gamma = {b: 0.0 for b in BLOCKS}
    nb = 0
    for bi in range(3):
        idxs = list(range(bi * 4, bi * 4 + 4))
        imgs = [Image.open(os.path.join(IMGS, f"{i:04d}.jpg")).convert("RGB") for i in idxs]
        texts = [caps[i] for i in idxs]
        inp = proc(text=texts, images=imgs, return_tensors="pt", padding=True, truncation=True)
        inp = {k: v.cuda() for k, v in inp.items()}
        model.zero_grad(set_to_none=True)
        out = model(**inp)
        I = torch.nn.functional.normalize(out.image_embeds, dim=-1)
        T = torch.nn.functional.normalize(out.text_embeds, dim=-1)
        E = ((I - T) ** 2).sum(-1).mean()
        logits = out.logits_per_image
        lab = torch.arange(len(idxs), device=logits.device)
        L = (torch.nn.functional.cross_entropy(logits, lab) +
             torch.nn.functional.cross_entropy(logits.T, lab)) / 2
        E.backward(retain_graph=True)
        gE = {n: p.grad.detach().float().clone() for n, p in model.named_parameters() if p.grad is not None}
        model.zero_grad(set_to_none=True)
        L.backward()
        for b, plist in blocks.items():
            s = 0.0
            for n, p in plist:
                if p.grad is not None and n in gE:
                    s += float(-(gE[n] * p.grad.detach().float()).sum())
            gamma[b] += s
        nb += 1
        model.zero_grad(set_to_none=True)
    gamma = {b: v / nb for b, v in gamma.items()}
    absg = {b: abs(v) for b, v in gamma.items()}
    share = np.array([absg[b] for b in BLOCKS])
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
    out = {"meta": {"script": "tools/_p1539_siglip_gamma.py", "task": "D2 non-CLIP source (SigLIP)",
                    "budget": BUDGET},
           "gamma": gamma, "abs": absg, "share": {b: float(s) for b, s in zip(BLOCKS, share)},
           "allocation": {b: int(r) for b, r in zip(BLOCKS, ranks)}}
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
    print("gamma:", {k: round(v, 4) for k, v in gamma.items()})
    print("allocation:", out["allocation"])
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
