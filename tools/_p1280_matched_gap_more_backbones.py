# -*- coding: utf-8 -*-
r"""Extend the matched-gap control to two further backbones (novelty add-on a).

The main text reports the matched-gap spread on three models (CLIP ViT-B/32, OpenCLIP, SigLIP). The prompt-template
control already covers five (adds CLIP ViT-B/16 and CLIP ViT-L/14); this script closes the gap by running the same
families (T, P, N) on the two extra backbones and recording the widest matched pair.

Output: outputs/analysis/a1_matched_gap_morebackbones.json (keyed by model, merges on re-runs)

    python tools/_p1280_matched_gap_more_backbones.py --backbones clip16 vitl --apply
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
OUT = os.path.join(REPO, "outputs", "analysis", "a1_matched_gap_morebackbones.json")
LAMBDAS = [-2, -1, -0.5, -0.25, 0.25, 0.5, 1, 2, 4]
ALPHAS = [0.1, 0.25, 0.5]
SIGMAS = [0.01, 0.02, 0.05, 0.1]
NOISE_SEEDS = [0, 1]
N = 5000
MODELS = {"clip16": "models/clip-vit-base-patch16", "vitl": "models/clip-vit-large-patch14"}


def load_data():
    from datasets import Dataset
    parq = sorted(glob.glob(os.path.join(REPO, "data", "imagenet_hf", "*.parquet")))
    ds = Dataset.from_parquet(parq)
    names = [x.split(",")[0].strip() for x in ds.features["label"].names]
    if len(names) == 1001:
        names = names[:1000]
    rs = np.random.RandomState(42)
    idx = rs.choice(len(ds), size=min(N, len(ds)), replace=False)
    sub = ds.select(idx.tolist())
    return [im.convert("RGB") for im in sub["image"]], np.asarray(sub["label"]), names


def embed(model, proc, pil, device, kind="image", texts=None, batch=32):
    out = []
    if kind == "image":
        with torch.no_grad():
            for i in range(0, len(pil), batch):
                inp = proc(images=pil[i:i + batch], return_tensors="pt").to(device)
                v = model.vision_model(**inp)
                pooled = v[1] if isinstance(v, tuple) else v.pooler_output
                emb = model.visual_projection(pooled) if hasattr(model, "visual_projection") else pooled
                out.append(F.normalize(emb.float(), dim=-1))
        return torch.cat(out)
    is_siglip = type(model).__name__.lower().startswith("siglip")
    with torch.no_grad():
        for i in range(0, len(texts), 128):
            kw = dict(padding="max_length", truncation=True, max_length=64) if is_siglip else dict(padding=True)
            ti = proc(text=texts[i:i + 128], return_tensors="pt", **kw).to(device)
            o = model.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            emb = model.text_projection(pooled) if hasattr(model, "text_projection") else pooled
            out.append(F.normalize(emb.float(), dim=-1))
    return torch.cat(out)[:len(texts)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbones", nargs="+", default=["clip16", "vitl"])
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(0)
    np.random.seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import AutoModel, AutoProcessor

    pil, labels, names = load_data()
    print(f"  images={len(pil)} classes={len(names)} device={device}", flush=True)
    payload = {"benchmark": "imagenet5k", "n_images": len(pil), "n_classes": len(names), "models": {}}
    if os.path.exists(OUT):
        try:
            payload["models"] = json.load(io.open(OUT, encoding="utf-8")).get("models", {})
        except Exception:
            pass

    for tag in a.backbones:
        rel = MODELS.get(tag)
        if not rel or not os.path.isdir(os.path.join(REPO, rel)):
            print(f"  {tag}: missing", flush=True)
            continue
        if tag in payload["models"]:
            print(f"  {tag}: already archived", flush=True)
            continue
        model = AutoModel.from_pretrained(os.path.join(REPO, rel), local_files_only=True).to(device).eval()
        proc = AutoProcessor.from_pretrained(os.path.join(REPO, rel), local_files_only=True)
        base = embed(model, proc, pil, device)
        texts = ["a photo of a " + c.replace("_", " ") for c in names]
        tf = embed(model, proc, None, device, kind="text", texts=texts)
        mu_i, mu_t = base.mean(0), tf.mean(0)
        gap_vec = mu_t - mu_i
        gap_norm = float(gap_vec.norm().item())
        d_hat = gap_vec / gap_norm
        base_np = (base @ tf.T).float().cpu().numpy()
        frozen_top1 = float((base_np.argmax(1) == labels).mean() * 100)
        print(f"  [{tag}] frozen CG={gap_norm:.4f} top1={frozen_top1:.2f}", flush=True)

        rows = []
        def measure(x, fam, param):
            cg = float((mu_t - x.mean(0)).norm().item())
            sn = (x @ tf.T).float().cpu().numpy()
            rows.append({"family": fam, "param": param, "CG": cg,
                         "top1": float((sn.argmax(1) == labels).mean() * 100)})
        measure(base, "frozen", 0.0)
        for lam in LAMBDAS:
            measure(F.normalize(base + lam * gap_norm * d_hat, dim=-1), "T", lam)
        cls_ids = sorted(set(labels.tolist()))
        cents = F.normalize(torch.stack([base[labels == c].mean(0) for c in cls_ids]), dim=-1)
        lab_map = {c: i for i, c in enumerate(cls_ids)}
        c_own = cents[torch.tensor([lab_map[int(x)] for x in labels], device=device)]
        for alpha in ALPHAS:
            measure(F.normalize((1 - alpha) * base + alpha * c_own, dim=-1), "P", alpha)
        dd = base.shape[1]
        for sigma in SIGMAS:
            for s in NOISE_SEEDS:
                g = torch.Generator(device=device).manual_seed(1000 + s)
                eps = torch.randn(base.shape, generator=g, device=device) / np.sqrt(dd)
                measure(F.normalize(base + sigma * eps, dim=-1), "N", sigma)

        best = None
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                if abs(rows[i]["CG"] - rows[j]["CG"]) > 0.03:
                    continue
                spread = abs(rows[i]["top1"] - rows[j]["top1"])
                if best is None or spread > best["spread"]:
                    best = {"dCG": abs(rows[i]["CG"] - rows[j]["CG"]), "spread": spread,
                            "a": {k: rows[i][k] for k in ("family", "param", "CG", "top1")},
                            "b": {k: rows[j][k] for k in ("family", "param", "CG", "top1")}}
        payload["models"][tag] = {"frozen": {"CG": gap_norm, "top1": frozen_top1}, "rows": rows,
                                  "max_matched_gap_spread_tol003": best}
        print(f"  [{tag}] matched spread={best['spread']:.1f} at dCG={best['dCG']:.3f}", flush=True)
        if a.apply:
            io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
            print("  wrote", os.path.relpath(OUT, REPO), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
