# -*- coding: utf-8 -*-
r"""Margin mass: the statistic that *does* see what the gap cannot (novelty item b).

Proposition 5 says a top-1 prediction can change only if its margin satisfies m_i <= 2 eps_i, where eps_i bounds the
class-wise spread of the score change. This script builds the operational statistic implied by that bound - the margin
mass

    M(eps) = n^{-1} # { i : m_i <= 2 eps }

- and asks whether it tracks zero-shot accuracy across the same perturbation families where the gap fails. The margin m_i
is computed from the frozen model's similarity matrix on the evaluation images.

Outputs: outputs/analysis/a1_margin_mass.json
    families T (translation), P (class contraction), N (noise); metrics per configuration: CG, top-1, M(eps) for a grid
    of eps, and the Pearson correlation of each with top-1 across the pooled configurations.

    python tools/_p1299_margin_mass.py [--apply]
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
OUT = os.path.join(REPO, "outputs", "analysis", "a1_margin_mass.json")
LAMBDAS = [-2, -1, -0.5, -0.25, 0.25, 0.5, 1, 2, 4]
ALPHAS = [0.1, 0.25, 0.5]
SIGMAS = [0.01, 0.02, 0.05, 0.1]
EPS_GRID = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
N = 5000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(0)
    np.random.seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import CLIPModel, CLIPProcessor
    local = os.path.join(REPO, "models", "clip-vit-base-patch32")
    model = CLIPModel.from_pretrained(local, local_files_only=True).to(device).eval()
    proc = CLIPProcessor.from_pretrained(local, local_files_only=True)

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
    print(f"  images={len(pil)} classes={len(names)}", flush=True)

    feats = []
    with torch.no_grad():
        for i in range(0, len(pil), 64):
            inp = proc(images=pil[i:i + 64], return_tensors="pt").to(device)
            v = model.vision_model(**inp)
            pooled = v[1] if isinstance(v, tuple) else v.pooler_output
            feats.append(F.normalize(model.visual_projection(pooled), dim=-1))
    base = torch.cat(feats)
    texts = ["a photo of a " + c.replace("_", " ") for c in names]
    tf = []
    with torch.no_grad():
        for i in range(0, len(texts), 256):
            ti = proc(text=texts[i:i + 256], return_tensors="pt", padding=True).to(device)
            o = model.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            tf.append(F.normalize(model.text_projection(pooled), dim=-1))
    tf = torch.cat(tf)[:len(names)]
    mu_i, mu_t = base.mean(0), tf.mean(0)
    gap_vec = mu_t - mu_i
    gn = float(gap_vec.norm().item())
    d_hat = gap_vec / gn

    rows = []

    def measure(x, fam, param):
        sn = (x @ tf.T).float().cpu().numpy()
        pred = sn.argmax(1)
        top1 = float((pred == labels).mean() * 100)
        # margin: score of the true class minus the best wrong class (0 when already wrong)
        true_s = sn[np.arange(len(pred)), labels]
        s = sn.copy()
        s[np.arange(len(pred)), labels] = -1e9
        best_wrong = s.max(1)
        margin = true_s - best_wrong
        cg = float((mu_t - x.mean(0)).norm().item())
        row = {"family": fam, "param": param, "CG": cg, "top1": top1,
               "margin_median": float(np.median(margin)),
               "margin_mean": float(np.mean(margin))}
        for e in EPS_GRID:
            row["mass_eps_%g" % e] = float((margin <= 2 * e).mean())
        rows.append(row)
        print(f"   {fam}({param:>5}): CG={cg:.4f} top1={top1:.2f} med_margin={row['margin_median']:.4f}", flush=True)

    measure(base, "frozen", 0.0)
    for lam in LAMBDAS:
        measure(F.normalize(base + lam * gn * d_hat, dim=-1), "T", lam)
    cls = sorted(set(labels.tolist()))
    cents = F.normalize(torch.stack([base[labels == c].mean(0) for c in cls]), dim=-1)
    lm = {c: i for i, c in enumerate(cls)}
    c_own = cents[torch.tensor([lm[int(x)] for x in labels], device=device)]
    for alpha in ALPHAS:
        measure(F.normalize((1 - alpha) * base + alpha * c_own, dim=-1), "P", alpha)
    d = base.shape[1]
    for sigma in SIGMAS:
        g = torch.Generator(device=device).manual_seed(1000)
        eps = torch.randn(base.shape, generator=g, device=device) / np.sqrt(d)
        measure(F.normalize(base + sigma * eps, dim=-1), "N", sigma)

    from scipy import stats as st
    top1 = np.array([r["top1"] for r in rows])
    cg = np.array([r["CG"] for r in rows])
    corr = {"CG": float(st.pearsonr(cg, top1)[0])}
    for e in EPS_GRID:
        key = "mass_eps_%g" % e
        vals = np.array([r[key] for r in rows])
        corr[key] = float(st.pearsonr(vals, top1)[0])
    payload = {"benchmark": "imagenet5k", "n_images": len(pil), "model": "openai/clip-vit-base-patch32",
               "eps_grid": EPS_GRID, "rows": rows, "correlation_with_top1": corr,
               "definition": "margin = s_i(y_i) - max_{c!=y_i} s_i(c); mass(eps) = mean(1[margin <= 2 eps])"}
    print("\n  correlation with top-1 (pooled configurations):")
    for k, v in corr.items():
        print(f"   {k:<14} {v:+.3f}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
