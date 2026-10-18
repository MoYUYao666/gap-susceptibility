# -*- coding: utf-8 -*-
r"""Numbers for the lower-bound section: the class-spread constant L, the margin mass, and real-checkpoint pairs.

L bounds how far a unit embedding perturbation can move a class score away from the row mean:
    L = max_u max_c |u . (t_c - mean_t)|  with u unit; a convenient bound is max_c ||t_c - mean_t||.
For a perturbation of size c along the class direction, the score spread is about c L, which is the eps of Proposition 5.

Also collects:
  * the margin mass M(eps) of the frozen ImageNet-5k model (archive a1_margin_mass.json);
  * real fine-tuned checkpoint pairs whose gaps agree to <= 0.01 / 0.03 (archive a1_epoch_sweep.json).

Outputs: outputs/analysis/a1_lower_bound_constants.json, outputs/analysis/a1_real_checkpoint_pairs.json

    python tools/_p1301_lower_bound_constants.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os

import numpy as np
import torch
import torch.nn.functional as F

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(REPO, "outputs", "analysis")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(0)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import CLIPModel, CLIPProcessor
    from datasets import Dataset

    local = os.path.join(REPO, "models", "clip-vit-base-patch32")
    model = CLIPModel.from_pretrained(local, local_files_only=True).to(device).eval()
    proc = CLIPProcessor.from_pretrained(local, local_files_only=True)
    parq = sorted(glob.glob(os.path.join(REPO, "data", "imagenet_hf", "*.parquet")))
    ds = Dataset.from_parquet(parq)
    names = [x.split(",")[0].strip() for x in ds.features["label"].names]
    if len(names) == 1001:
        names = names[:1000]
    texts = ["a photo of a " + c.replace("_", " ") for c in names]
    tf = []
    with torch.no_grad():
        for i in range(0, len(texts), 256):
            ti = proc(text=texts[i:i + 256], return_tensors="pt", padding=True).to(device)
            o = model.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            tf.append(F.normalize(model.text_projection(pooled), dim=-1))
    tf = torch.cat(tf)[:len(names)]
    central = tf - tf.mean(0)
    norms = central.norm(dim=1)
    L = float(norms.max().item())
    L_median = float(norms.median().item())
    print(f"  text embeddings: {len(tf)} | L=max||t_c - mean_t|| = {L:.4f} (median {L_median:.4f})")

    mass = json.load(io.open(os.path.join(AN, "a1_margin_mass.json"), encoding="utf-8"))
    frozen = next(r for r in mass["rows"] if r["family"] == "frozen")
    masses = {k: frozen[k] for k in frozen if k.startswith("mass_eps_")}

    # lower bound instantiation: a first-moment statistic can be fooled by at least mass(2cL) rows
    inst = {}
    for c in (0.028, 0.05, 0.1):
        tau = 2 * c * L
        # nearest grid point in the archive
        best_eps = min(mass["eps_grid"], key=lambda e: abs(e - tau / 2))
        key = "mass_eps_%g" % best_eps
        inst[str(c)] = {"score_spread_2cL": tau, "grid_eps": best_eps,
                        "mass": frozen.get(key), "bound_points": 100.0 * frozen.get(key, 0.0)}
        print(f"  c={c}: 2cL={tau:.4f} -> eps grid {best_eps}, margin mass {frozen.get(key):.4f} "
              f"=> lower bound {100*frozen.get(key,0):.1f} points")

    # real checkpoint pairs
    d = json.load(io.open(os.path.join(REPO, "outputs", "a1_epoch_sweep.json"), encoding="utf-8"))
    ck = [c for c in d["checkpoints"] if c.get("CG_flickr_val") is not None and c.get("top1_5k") is not None]
    pairs = []
    for i in range(len(ck)):
        for j in range(i + 1, len(ck)):
            dcg = abs(ck[i]["CG_flickr_val"] - ck[j]["CG_flickr_val"])
            if dcg <= 0.03:
                pairs.append({"dCG": dcg, "dtop1": abs(ck[i]["top1_5k"] - ck[j]["top1_5k"]),
                              "a": {k: ck[i][k] for k in ("dataset", "seed", "epoch", "CG_flickr_val", "top1_5k")},
                              "b": {k: ck[j][k] for k in ("dataset", "seed", "epoch", "CG_flickr_val", "top1_5k")}})
    pairs.sort(key=lambda p: -p["dtop1"])
    same = [p for p in pairs if p["a"]["dataset"] == p["b"]["dataset"]]
    print(f"  real checkpoint pairs at |dCG|<=0.03: {len(pairs)} (within dataset {len(same)})")
    for tol in (0.003, 0.01, 0.03):
        sub = [p for p in pairs if p["dCG"] <= tol]
        if sub:
            print(f"   tol {tol}: {len(sub)} pairs | widest {max(p['dtop1'] for p in sub):.2f} points")
    within = {}
    for ds_name in sorted({c["dataset"] for c in ck}):
        sub = [c for c in ck if c["dataset"] == ds_name]
        best = None
        for i in range(len(sub)):
            for j in range(i + 1, len(sub)):
                dcg = abs(sub[i]["CG_flickr_val"] - sub[j]["CG_flickr_val"])
                if dcg <= 0.01 and (best is None or abs(sub[i]["top1_5k"] - sub[j]["top1_5k"]) > best[0]):
                    best = (abs(sub[i]["top1_5k"] - sub[j]["top1_5k"]), dcg)
        within[ds_name] = {"n": len(sub), "widest_pair_at_0.01": best}

    payload = {"text_embedding_spread_L": L, "text_embedding_spread_L_median": L_median,
               "margin_mass_frozen": masses, "lower_bound_instances": inst,
               "real_checkpoint_pairs_tol003": pairs[:20],
               "within_dataset_widest": within}
    print(json.dumps(payload["within_dataset_widest"], indent=1)[:600])
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(os.path.join(AN, "a1_lower_bound_constants.json"), "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
    io.open(os.path.join(AN, "a1_real_checkpoint_pairs.json"), "w", encoding="utf-8", newline="").write(
        json.dumps({"pairs": pairs, "within_dataset": within, "n_checkpoints": len(ck)}, indent=1))
    print("  wrote a1_lower_bound_constants.json and a1_real_checkpoint_pairs.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
