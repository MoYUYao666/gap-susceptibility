# -*- coding: utf-8 -*-
r"""Matched-gap experiment: is top-1 a function of the modality gap?

The paper's proposition is that zero-shot accuracy depends on the ordering of class-relative similarities, while the
modality gap is a first-moment statistic; therefore the gap cannot be a sufficient statistic. The sharpest empirical
demonstration is a matched-gap comparison: find configurations from *different perturbation families* that share the same
centroid gap and compare their top-1.

Three families are swept on one frozen model and one benchmark:
  T  translation along the gap direction ("gap surgery", lambda grid)
  P  class contraction toward each image's own class prototype (alpha grid)
  N  isotropic Gaussian noise on the image embeddings (sigma grid, several seeds)

For every point we record (CG, top-1, tau-top5). Matched-gap pairs are then found by nearest CG across families.

Frozen forward passes only -- no training.

    python tools/_p1209_matched_gap_families.py [--apply] [--benchmark imagenet5k|dtd|food101]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import random

import numpy as np
import torch
import torch.nn.functional as F

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(REPO, "outputs", "analysis")
TEMPLATE = "a photo of a {}"
N = 5000
LAMBDAS = [-2, -1, -0.5, -0.25, 0.25, 0.5, 1, 2, 4]
ALPHAS = [0.1, 0.25, 0.5]
SIGMAS = [0.01, 0.02, 0.05, 0.1, 0.2]
NOISE_SEEDS = [0, 1, 2]


def kendall_topk(base_np, cur_np, idx5):
    from scipy import stats
    taus = []
    for i in range(len(base_np)):
        r1 = base_np[i][idx5[i]]
        r2 = cur_np[i][idx5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    return float(np.mean(taus)) if taus else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--benchmark", default="imagenet5k")
    a = ap.parse_args()

    torch.manual_seed(0)
    np.random.seed(42)
    random.seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import CLIPModel, CLIPProcessor
    mid = "openai/clip-vit-base-patch32"
    try:
        model = CLIPModel.from_pretrained(mid, local_files_only=True).to(device).eval()
        proc = CLIPProcessor.from_pretrained(mid, local_files_only=True)
    except Exception:
        local = os.path.join(REPO, "models", "clip-vit-base-patch32")
        model = CLIPModel.from_pretrained(local, local_files_only=True).to(device).eval()
        proc = CLIPProcessor.from_pretrained(local, local_files_only=True)

    # ---- benchmark images
    from datasets import Dataset
    if a.benchmark == "imagenet5k":
        parq = sorted(glob.glob(os.path.join(REPO, "data", "imagenet_hf", "*.parquet")))
        ds = Dataset.from_parquet(parq)
        names = [n.split(",")[0].strip() for n in ds.features["label"].names]
        # the parquet carries a placeholder class at index 1000; A1 scores top-1 over the 1000 real classes
        if len(names) == 1001:
            names = names[:1000]
        rs = np.random.RandomState(42)
        idx = rs.choice(len(ds), size=min(N, len(ds)), replace=False)
        sub = ds.select(idx.tolist())
        labels = np.asarray(sub["label"])
        pil = [im.convert("RGB") for im in sub["image"]]
    else:
        raise SystemExit("only imagenet5k is wired for this experiment")

    print(f"  images={len(pil)} classes={len(names)} device={device}", flush=True)

    feats = []
    with torch.no_grad():
        for i in range(0, len(pil), 64):
            inp = proc(images=pil[i:i + 64], return_tensors="pt").to(device)
            v = model.vision_model(**inp)
            pooled = v[1] if isinstance(v, tuple) else v.pooler_output
            feats.append(F.normalize(model.visual_projection(pooled), dim=-1))
    base = torch.cat(feats)

    texts = [TEMPLATE.format(c.replace("_", " ")) for c in names]
    tf = []
    with torch.no_grad():
        for i in range(0, len(texts), 256):
            ti = proc(text=[str(t) for t in texts[i:i + 256]], return_tensors="pt", padding=True).to(device)
            o = model.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            tf.append(F.normalize(model.text_projection(pooled), dim=-1))
    tf = torch.cat(tf)
    if tf.shape[0] > len(names):
        tf = tf[:len(names)]

    mu_i, mu_t = base.mean(0), tf.mean(0)
    gap_vec = mu_t - mu_i
    gap_norm = float(gap_vec.norm().item())
    d_hat = gap_vec / gap_norm
    base_np = (base @ tf.T).float().cpu().numpy()
    idx5 = np.argsort(-base_np, axis=1)[:, :5]
    frozen_cg = gap_norm
    frozen_top1 = float((base_np.argmax(1) == labels).mean() * 100)
    print(f"  frozen: CG={frozen_cg:.4f} top1={frozen_top1:.2f}", flush=True)

    def measure(x, tag):
        mu = x.mean(0)
        cg = float((mu_t - mu).norm().item())
        sn = (x @ tf.T).float().cpu().numpy()
        top1 = float((sn.argmax(1) == labels).mean() * 100)
        tau = kendall_topk(base_np, sn, idx5)
        return {"family": tag[0], "param": tag[1], "CG": cg, "top1": top1, "tau": tau}

    # class centroids in image space (for family P: contract toward own class prototype)
    cls_ids = sorted(set(labels.tolist()))
    class_text = {int(c): int(np.argmax((tf @ base_np[labels == c].mean(0).__class__(tf.new_tensor(
        (base[labels == c].mean(0) @ tf.T).cpu().numpy()))).item())) for c in []}  # placeholder, unused

    rows = [measure(base, ("frozen", 0.0))]

    # family T: translation along the gap direction
    for lam in LAMBDAS:
        x = F.normalize(base + lam * gap_norm * d_hat, dim=-1)
        rows.append(measure(x, ("T", lam)))
        print(f"   T lam={lam:>5}: " + str(rows[-1]), flush=True)

    # family P: contract toward own class centroid (computed in image space, then renormalised)
    from scipy import stats as _st
    for alpha in ALPHAS:
        cents = torch.stack([base[labels == c].mean(0) for c in cls_ids])
        cents = F.normalize(cents, dim=-1)
        lab_map = {c: i for i, c in enumerate(cls_ids)}
        c_own = cents[torch.tensor([lab_map[int(x)] for x in labels], device=device)]
        x = F.normalize((1 - alpha) * base + alpha * c_own, dim=-1)
        rows.append(measure(x, ("P", alpha)))
        print(f"   P a={alpha:>5}: " + str(rows[-1]), flush=True)

    # family N: isotropic Gaussian noise
    d = base.shape[1]
    for sigma in SIGMAS:
        for s in NOISE_SEEDS:
            g = torch.Generator(device=device).manual_seed(1000 + s)
            eps = torch.randn(base.shape, generator=g, device=device) / np.sqrt(d)
            x = F.normalize(base + sigma * eps, dim=-1)
            rows.append(measure(x, ("N", sigma)))
    for sigma in SIGMAS:
        sub = [r for r in rows if r["family"] == "N" and abs(r["param"] - sigma) < 1e-12]
        print(f"   N s={sigma:>5}: CG={np.mean([r['CG'] for r in sub]):.4f} "
              f"top1={np.mean([r['top1'] for r in sub]):.2f} (n={len(sub)} seeds)", flush=True)

    # ---- matched-gap analysis: compare families at the same CG
    def nearest(fam, target, tol=0.02):
        cand = [r for r in rows if r["family"] == fam and abs(r["CG"] - target) <= tol]
        return cand

    def best_pair(tol):
        best = None
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                r, r2 = rows[i], rows[j]
                if abs(r["CG"] - r2["CG"]) > tol:
                    continue
                spread = abs(r["top1"] - r2["top1"])
                if best is None or spread > best["spread"]:
                    best = {"tol": tol, "dCG": abs(r["CG"] - r2["CG"]), "CG": r["CG"],
                            "a": {k: r[k] for k in ("family", "param", "CG", "top1")},
                            "b": {k: r2[k] for k in ("family", "param", "CG", "top1")},
                            "spread": spread}
        return best

    best = best_pair(0.03)
    best05 = best_pair(0.05)
    print("\n  === largest top-1 spread at matched CG ===")
    for b in (best, best05):
        print("  ", json.dumps(b, ensure_ascii=False) if b else "  none")

    payload = {"benchmark": a.benchmark, "model": mid, "n_images": len(pil), "n_classes": len(names),
               "frozen": {"CG": frozen_cg, "top1": frozen_top1},
               "rows": rows, "max_matched_gap_spread_tol003": best,
               "max_matched_gap_spread_tol005": best05,
               "definition": "CG = || mean(text emb) - mean(perturbed image emb) || on L2-normalised embeddings"}
    if a.apply:
        os.makedirs(OUTDIR, exist_ok=True)
        p = os.path.join(OUTDIR, "a1_matched_gap_families.json")
        io.open(p, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("\n  wrote", os.path.relpath(p, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
