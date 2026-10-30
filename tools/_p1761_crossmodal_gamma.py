# -*- coding: utf-8 -*-
r"""Workstream B (generality): measure gap susceptibility on non-image-text contrastive pairs.

Purpose: the paper's characterisation was fitted on image-text CLIP-family backbones. This script measures the same
quantities on audio-text (LAION-CLAP) and, as a control, on an image-text backbone, so the manuscript can say whether
the mechanism is cross-modal or image-text specific.

What is computed, per backbone and per paired batch:
  E            alignment energy proxy: mean squared distance between the two towers' L2-normalised embeddings
  DG           distribution gap: mean squared distance of the paired embeddings
  grad_m       ||d DG / d theta_m|| for each tower m (one backward pass, no training)
  gamma_m      grad_m * cos(phi_m), where phi_m is the angle between the tower gradient and the full gradient
Writes outputs/analysis/paperA_crossmodal_gamma.json (English keys).

Modes:
  --plan    print exactly what would be downloaded and computed; no model load, no GPU
  --run     execute (requires weights and paired data on disk)
"""
from __future__ import annotations

import argparse
import io
import json
import os

BACKBONES = {
    "clap": {
        "repo": "laion/clap-htsat-unfused",
        "kind": "audio-text",
        "towers": {"audio": "audio_model", "text": "text_model"},
    },
    "clip-control": {
        "repo": "openai/clip-vit-base-patch32",
        "kind": "image-text",
        "towers": {"vision": "vision_model", "text": "text_model"},
    },
}
DATA = {
    "clap": {"dataset": "sanchit-gandhi/clotho-audio-captions", "pairs": 512},
    "clip-control": {"dataset": "nlphuji/flickr30k", "pairs": 512},
}
OUT = "outputs/analysis/paperA_crossmodal_gamma.json"


def plan(backbone: str) -> dict:
    cfg = BACKBONES[backbone]
    d = DATA[backbone]
    return {
        "backbone": backbone,
        "repo": cfg["repo"],
        "modality_pair": cfg["kind"],
        "towers": list(cfg["towers"]),
        "data": d,
        "steps": [
            "download %s through the first working mirror" % cfg["repo"],
            "download %s pairs from %s" % (d["pairs"], d["dataset"]),
            "build one paired batch, compute E and DG",
            "one backward pass of DG, record ||grad_tower|| per tower",
            "compute gamma per tower and the induced ordering",
            "write %s" % OUT,
        ],
        "writes": [OUT],
        "note": "no optimizer step anywhere: measurement only",
    }


def run(backbone: str, pairs: int) -> dict:
    import numpy as np
    import torch
    from transformers import AutoModel, AutoProcessor

    cfg = BACKBONES[backbone]
    model = AutoModel.from_pretrained(cfg["repo"], trust_remote_code=True)
    proc = AutoProcessor.from_pretrained(cfg["repo"], trust_remote_code=True)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)

    # The paired batch is supplied by the caller through a cached .pt file, so this script never silently invents data.
    batch_path = os.path.join("outputs", "_crossmodal_batch_%s.pt" % backbone)
    if not os.path.isfile(batch_path):
        raise SystemExit("missing paired batch: %s (build it first with the dataset-specific loader)" % batch_path)
    batch = torch.load(batch_path, map_location="cpu")
    a, b = batch["a"], batch["b"]

    towers = cfg["towers"]
    grads = {}
    for name, attr in towers.items():
        sub = getattr(model, attr, None)
        if sub is None:
            raise SystemExit("tower %s not found on the model" % attr)
        grads[name] = [p for p in sub.parameters() if p.requires_grad or True]

    # tower outputs through the model's own forward is backbone specific; use the projection heads when available
    with torch.enable_grad():
        emb_a = model.get_audio_features(**a) if hasattr(model, "get_audio_features") else None
        emb_b = model.get_text_features(**b) if hasattr(model, "get_text_features") else None
        if emb_a is None or emb_b is None:
            raise SystemExit("this backbone exposes no get_*_features helper; adapt the script")
        emb_a = emb_a / emb_a.norm(dim=-1, keepdim=True)
        emb_b = emb_b / emb_b.norm(dim=-1, keepdim=True)
        dg = ((emb_a - emb_b) ** 2).mean()
        norm = {}
        for name in towers:
            ps = [p for p in (getattr(model, towers[name]).parameters()) if p.requires_grad]
            if not ps:
                for p in getattr(model, towers[name]).parameters():
                    p.requires_grad_(True)
                ps = [p for p in getattr(model, towers[name]).parameters() if p.requires_grad]
            g = torch.autograd.grad(dg, ps, retain_graph=True, allow_unused=True)
            norm[name] = float(torch.sqrt(sum((x ** 2).sum() for x in g if x is not None)))
            for p in getattr(model, towers[name]).parameters():
                p.requires_grad_(False)

    total = float(np.sqrt(sum(v ** 2 for v in norm.values()))) or 1.0
    gamma = {k: v / total for k, v in norm.items()}
    res = {"backbone": backbone, "modality_pair": cfg["kind"], "pairs": int(pairs),
           "E_proxy_dg": float(dg), "grad_norm": norm, "gamma_relative": gamma,
           "ordering_by_gamma": sorted(gamma, key=lambda k: -gamma[k])}
    os.makedirs("outputs/analysis", exist_ok=True)
    io.open(OUT if backbone == "clip-control" else OUT.replace(".json", "_%s.json" % backbone),
            "w", encoding="utf-8", newline="").write(json.dumps(res, indent=2))
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", default="clap", choices=sorted(BACKBONES))
    ap.add_argument("--mode", default="plan", choices=["plan", "run"])
    ap.add_argument("--pairs", type=int, default=512)
    a = ap.parse_args()
    info = plan(a.backbone) if a.mode == "plan" else run(a.backbone, a.pairs)
    print(json.dumps(info, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
