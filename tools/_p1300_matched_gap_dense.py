# -*- coding: utf-8 -*-
r"""Dense lambda grid, five backbones, one uniform matched-gap tolerance.

The headline matched-gap claim currently rests on three CLIP-family backbones at |dCG| <= 0.03 and on OpenCLIP/SigLIP
only at looser tolerances (0.066 and 0.197) because their swept points are sparse. This script re-sweeps every backbone on
a dense grid so all five can be quoted at the same tolerance. Image embeddings are recomputed per backbone (one forward
pass over 5,000 images); the families and the matching analysis are unchanged.

Output: outputs/analysis/a1_matched_gap_dense.json

    python tools/_p1300_matched_gap_dense.py [--backbones clip32 clip16 openclip siglip vitl] [--apply]
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
OUT = os.path.join(REPO, "outputs", "analysis", "a1_matched_gap_dense.json")
LAMBDAS = [-2, -1.5, -1, -0.75, -0.5, -0.4, -0.3, -0.25, -0.15, 0.15, 0.25, 0.3, 0.4, 0.5, 0.75, 1, 1.5, 2, 4]
ALPHAS = [0.1, 0.2, 0.3, 0.4, 0.5]
SIGMAS = [0.01, 0.02, 0.05, 0.1]
N = 5000
MODELS = {
    "clip32": "models/clip-vit-base-patch32",
    "clip16": "models/clip-vit-base-patch16",
    "openclip": "models/openclip",
    "siglip": "models/siglip-base-patch16-224",
    "vitl": "models/clip-vit-large-patch14",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbones", nargs="+", default=list(MODELS))
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(0)
    np.random.seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import AutoModel, AutoProcessor
    from datasets import Dataset

    parq = sorted(glob.glob(os.path.join(REPO, "data", "imagenet_hf", "*.parquet")))
    ds = Dataset.from_parquet(parq)
    names = [x.split(",")[0].strip() for x in ds.features["label"].names]
    if len(names) == 1001:
        names = names[:1000]
    rs = np.random.RandomState(42)
    idx = rs.choice(len(ds), size=min(N, len(ds)), replace=False)
    sub = ds.select(idx.tolist())
    labels = np.asarray(sub["label"])
    pil = [im.convert("RGB") for im in sub["image"]]
    print(f"  images={len(pil)} classes={len(names)} device={device}", flush=True)

    payload = {"benchmark": "imagenet5k", "n_images": len(pil), "n_classes": len(names),
               "lambdas": LAMBDAS, "models": {}}
    if os.path.exists(OUT):
        try:
            payload["models"] = json.load(io.open(OUT, encoding="utf-8")).get("models", {})
        except Exception:
            pass

    texts = ["a photo of a " + c.replace("_", " ") for c in names]
    for tag in a.backbones:
        rel = MODELS.get(tag)
        if not rel or not os.path.isdir(os.path.join(REPO, rel)):
            print(f"  {tag}: missing", flush=True)
            continue
        if tag in payload["models"]:
            print(f"  {tag}: archived", flush=True)
            continue
        model = AutoModel.from_pretrained(os.path.join(REPO, rel), local_files_only=True).to(device).eval()
        proc = AutoProcessor.from_pretrained(os.path.join(REPO, rel), local_files_only=True)
        has_vproj, has_tproj = hasattr(model, "visual_projection"), hasattr(model, "text_projection")
        is_siglip = type(model).__name__.lower().startswith("siglip")
        feats = []
        with torch.no_grad():
            for i in range(0, len(pil), 32):
                inp = proc(images=pil[i:i + 32], return_tensors="pt").to(device)
                v = model.vision_model(**inp)
                pooled = v[1] if isinstance(v, tuple) else v.pooler_output
                feats.append(F.normalize((model.visual_projection(pooled) if has_vproj else pooled).float(), dim=-1))
        base = torch.cat(feats)
        tf = []
        with torch.no_grad():
            for i in range(0, len(texts), 128):
                kw = dict(padding="max_length", truncation=True, max_length=64) if is_siglip else dict(padding=True)
                ti = proc(text=texts[i:i + 128], return_tensors="pt", **kw).to(device)
                o = model.text_model(**ti)
                pooled = o[1] if isinstance(o, tuple) else o.pooler_output
                tf.append(F.normalize((model.text_projection(pooled) if has_tproj else pooled).float(), dim=-1))
        tf = torch.cat(tf)[:len(names)]
        mu_i, mu_t = base.mean(0), tf.mean(0)
        gv = mu_t - mu_i
        gn = float(gv.norm().item())
        d_hat = gv / gn
        rows = []

        def measure(x, fam, param):
            cg = float((mu_t - x.mean(0)).norm().item())
            sn = (x @ tf.T).float().cpu().numpy()
            rows.append({"family": fam, "param": param, "CG": cg,
                         "top1": float((sn.argmax(1) == labels).mean() * 100)})
        measure(base, "frozen", 0.0)
        for lam in LAMBDAS:
            measure(F.normalize(base + lam * gn * d_hat, dim=-1), "T", lam)
        cls = sorted(set(labels.tolist()))
        cents = F.normalize(torch.stack([base[labels == c].mean(0) for c in cls]), dim=-1)
        lm = {c: i for i, c in enumerate(cls)}
        c_own = cents[torch.tensor([lm[int(x)] for x in labels], device=device)]
        for alpha in ALPHAS:
            measure(F.normalize((1 - alpha) * base + alpha * c_own, dim=-1), "P", alpha)
        dd = base.shape[1]
        for sigma in SIGMAS:
            g = torch.Generator(device=device).manual_seed(1000)
            eps = torch.randn(base.shape, generator=g, device=device) / np.sqrt(dd)
            measure(F.normalize(base + sigma * eps, dim=-1), "N", sigma)

        def best(tol):
            b = None
            for i in range(len(rows)):
                for j in range(i + 1, len(rows)):
                    if abs(rows[i]["CG"] - rows[j]["CG"]) > tol:
                        continue
                    sp = abs(rows[i]["top1"] - rows[j]["top1"])
                    if b is None or sp > b["spread"]:
                        b = {"tol": tol, "dCG": abs(rows[i]["CG"] - rows[j]["CG"]), "spread": sp,
                             "a": {k: rows[i][k] for k in ("family", "param", "CG", "top1")},
                             "b": {k: rows[j][k] for k in ("family", "param", "CG", "top1")}}
            return b
        entry = {"frozen": {"CG": gn, "top1": rows[0]["top1"]}, "rows": rows,
                 "matched_tol003": best(0.03), "matched_tol005": best(0.05)}
        payload["models"][tag] = entry
        print(f"  [{tag}] frozen CG={gn:.4f} top1={rows[0]['top1']:.2f} | "
              f"tol0.03 spread={entry['matched_tol003']['spread'] if entry['matched_tol003'] else 'n/a'}", flush=True)
        if a.apply:
            io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
    if a.apply:
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
