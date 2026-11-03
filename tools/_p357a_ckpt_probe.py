# -*- coding: utf-8 -*-
r"""p357a -- read-only probe of the DINOv2-hetero checkpoints and head file.

Answers, from the archive alone (CPU only, no GPU):
  * what exactly is in best/last_checkpoint.pt (epoch, losses, lora state dict)
  * whether `last_checkpoint.pt` is the epoch-10 model or a copy of `best`
  * what `heads/fitted.pt` records about the head fit (val R@1 at fit time)

Source of every printed number is the file path printed next to it.
Writes outputs/analysis/dinov2_hetero/norm_probe/ckpt_probe.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import torch  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "norm_probe"
OUT.mkdir(parents=True, exist_ok=True)

CKPTS = [
    "outputs/analysis/dinov2_hetero/fitted/text_only/seed42/best_checkpoint.pt",
    "outputs/analysis/dinov2_hetero/fitted/text_only/seed42/last_checkpoint.pt",
    "outputs/analysis/dinov2_hetero/fitted/text_only/seed123/best_checkpoint.pt",
]
HEAD = "outputs/analysis/dinov2_hetero/heads/fitted.pt"


def main():
    rep = {"script": "tools/_p357a_ckpt_probe.py", "checkpoints": {}, "head": None}

    states = {}
    for rel in CKPTS:
        p = REPO / rel
        ck = torch.load(p, map_location="cpu", weights_only=False)
        lsd = ck.get("lora_state_dict", {})
        norms = []
        for k, v in lsd.items():
            A, B = v["A"].float(), v["B"].float()
            norms.append(float((A @ B).norm().item()))
        rec = {
            "path": rel,
            "top_keys": sorted(ck.keys()),
            "epoch": ck.get("epoch"),
            "config_name": ck.get("config_name"),
            "n_lora_layers": len(lsd),
            "lora_layer_names_sample": sorted(lsd.keys())[:3],
            "train_losses": [round(float(x), 6) for x in ck.get("train_losses", [])],
            "val_losses": [round(float(x), 6) for x in ck.get("val_losses", [])],
            "task_R1": [round(float(t.get("R@1", float("nan"))), 6)
                        for t in ck.get("task_metrics", [])],
            "gap_epochs": [g.get("epoch") for g in ck.get("gap_history", [])],
            "gap_CG": [round(float(g.get("centroid_gap")), 6)
                       for g in ck.get("gap_history", [])],
            "lora_AB_frobenius_sum_of_norms": sum(norms),
            "fingerprint_lora_first_tensor": float(
                next(iter(lsd.values()))["A"].float().sum().item()) if lsd else None,
        }
        rep["checkpoints"][rel] = rec
        states[rel] = {k: (v["A"].clone(), v["B"].clone()) for k, v in lsd.items()}

    # is last == best ?
    a = states.get(CKPTS[0], {})
    b = states.get(CKPTS[1], {})
    same = bool(a) and set(a) == set(b) and all(
        torch.equal(a[k][0], b[k][0]) and torch.equal(a[k][1], b[k][1]) for k in a)
    rep["last_equals_best"] = same

    h = torch.load(REPO / HEAD, map_location="cpu", weights_only=False)
    rep["head"] = {
        "path": HEAD,
        "top_keys": sorted(h.keys()),
        "state_dict_keys": sorted(h["state_dict"].keys()),
        "meta": h["meta"],
    }
    with open(OUT / "ckpt_probe.json", "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2, ensure_ascii=False)
    print(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
