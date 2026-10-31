# -*- coding: utf-8 -*-
r"""Retrieval-side replication (novelty item D): does the same failure appear on image-to-caption retrieval?

The manuscript's claim is about zero-shot classification, but the gap is also used to monitor retrieval. This script runs
the matched-gap protocol on an image-caption set (536 marine images with one caption each, local):

  families   T  translation along the gap direction (lambda grid)
             P  contraction toward each image's own caption embedding (the retrieval analogue of class contraction)
             N  isotropic Gaussian noise (sigma grid, seeds)
  measures   CG, image->text R@1 and R@5, tau on the frozen top-5 caption sets

Output reports, for every configuration, whether the same dissociation appears: matched gaps with different R@1, and
whether tau tracks R@1 better than CG does.

    python tools/_p1273_retrieval_evidence.py [--apply]
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
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a1_retrieval_evidence.json")
LAMBDAS = [-2, -1, -0.5, -0.25, 0.25, 0.5, 1, 2, 4]
ALPHAS = [0.1, 0.25, 0.5]
SIGMAS = [0.01, 0.02, 0.05, 0.1]
NOISE_SEEDS = [0, 1]


def load_pairs():
    root = os.path.join(REPO, "data", "marine_captions")
    imgs = sorted(glob.glob(os.path.join(root, "*.jpg")))
    caps = json.load(io.open(os.path.join(root, "captions.json"), encoding="utf-8"))["captions"]
    n = min(len(imgs), len(caps))
    pil = [Image.open(p).convert("RGB") for p in imgs[:n]]
    return pil, [str(c) for c in caps[:n]]


def kendall_topk(base_np, cur_np, k):
    from scipy import stats
    idx = np.argsort(-base_np, axis=1)[:, :k]
    taus = []
    for i in range(len(base_np)):
        r1, r2 = base_np[i][idx[i]], cur_np[i][idx[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    return float(np.mean(taus)) if taus else None


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

    pil, caps = load_pairs()
    print(f"  pairs={len(pil)} device={device}", flush=True)
    feats = []
    with torch.no_grad():
        for i in range(0, len(pil), 64):
            inp = proc(images=pil[i:i + 64], return_tensors="pt").to(device)
            v = model.vision_model(**inp)
            pooled = v[1] if isinstance(v, tuple) else v.pooler_output
            feats.append(F.normalize(model.visual_projection(pooled), dim=-1))
    base = torch.cat(feats)
    tf = []
    with torch.no_grad():
        for i in range(0, len(caps), 128):
            ti = proc(text=caps[i:i + 128], return_tensors="pt", padding="max_length", truncation=True,
                      max_length=64).to(device)
            o = model.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            tf.append(F.normalize(model.text_projection(pooled), dim=-1))
    tf = torch.cat(tf)[:len(caps)]

    mu_i, mu_t = base.mean(0), tf.mean(0)
    gap_vec = mu_t - mu_i
    gap_norm = float(gap_vec.norm().item())
    d_hat = gap_vec / gap_norm
    base_np = (base @ tf.T).float().cpu().numpy()
    n = len(base_np)
    target = np.arange(n)  # the diagonal is the paired caption

    def measure(x, tag):
        cg = float((mu_t - x.mean(0)).norm().item())
        sn = (x @ tf.T).float().cpu().numpy()
        ranks = np.argsort(-sn, axis=1)
        r1 = float((ranks[:, 0] == target).mean() * 100)
        r5 = float((ranks[:, :5] == target[:, None]).any(1).mean() * 100)
        tau = kendall_topk(base_np, sn, 5) if tag != ("frozen", 0.0) else 1.0
        return {"family": tag[0], "param": tag[1], "CG": cg, "R1": r1, "R5": r5, "tau": tau}

    rows = [measure(base, ("frozen", 0.0))]
    print(f"  frozen: CG={rows[0]['CG']:.4f} R@1={rows[0]['R1']:.2f} R@5={rows[0]['R5']:.2f}", flush=True)
    for lam in LAMBDAS:
        rows.append(measure(F.normalize(base + lam * gap_norm * d_hat, dim=-1), ("T", lam)))
        print(f"   T lam={lam:>5}: CG={rows[-1]['CG']:.4f} R@1={rows[-1]['R1']:.2f} tau={rows[-1]['tau']:.3f}", flush=True)
    for alpha in ALPHAS:
        x = F.normalize((1 - alpha) * base + alpha * tf[:len(base)], dim=-1)
        rows.append(measure(x, ("P", alpha)))
        print(f"   P a={alpha:>5}: CG={rows[-1]['CG']:.4f} R@1={rows[-1]['R1']:.2f} tau={rows[-1]['tau']:.3f}", flush=True)
    d = base.shape[1]
    for sigma in SIGMAS:
        for s in NOISE_SEEDS:
            g = torch.Generator(device=device).manual_seed(1000 + s)
            eps = torch.randn(base.shape, generator=g, device=device) / np.sqrt(d)
            rows.append(measure(F.normalize(base + sigma * eps, dim=-1), ("N", sigma)))
    for sigma in SIGMAS:
        sub = [r for r in rows if r["family"] == "N" and abs(r["param"] - sigma) < 1e-12]
        print(f"   N s={sigma:>5}: CG={np.mean([r['CG'] for r in sub]):.4f} R@1={np.mean([r['R1'] for r in sub]):.2f}", flush=True)

    def best_pair(tol):
        best = None
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                if abs(rows[i]["CG"] - rows[j]["CG"]) > tol:
                    continue
                spread = abs(rows[i]["R1"] - rows[j]["R1"])
                if best is None or spread > best["spread"]:
                    best = {"tol": tol, "dCG": abs(rows[i]["CG"] - rows[j]["CG"]), "CG": rows[i]["CG"],
                            "a": {k: rows[i][k] for k in ("family", "param", "CG", "R1", "R5")},
                            "b": {k: rows[j][k] for k in ("family", "param", "CG", "R1", "R5")},
                            "spread": spread}
        return best

    from scipy import stats as st
    tau_vals = [r["tau"] for r in rows if r["tau"] is not None]
    r1_vals = [r["R1"] for r in rows if r["tau"] is not None]
    cg_vals = [r["CG"] for r in rows if r["tau"] is not None]
    corr_tau = float(st.pearsonr(tau_vals, r1_vals)[0]) if len(set(r1_vals)) > 1 else None
    corr_cg = float(st.pearsonr(cg_vals, r1_vals)[0]) if len(set(r1_vals)) > 1 else None
    corr_gap_r1 = corr_cg

    payload = {"benchmark": "marine_captions", "n_pairs": n, "model": "openai/clip-vit-base-patch32",
               "frozen": {"CG": rows[0]["CG"], "R1": rows[0]["R1"], "R5": rows[0]["R5"]},
               "rows": rows, "widest_matched_pair_tol003": best_pair(0.03),
               "widest_matched_pair_tol005": best_pair(0.05),
               "correlation": {"tau_vs_R1": corr_tau, "CG_vs_R1": corr_gap_r1},
               "note": "one caption per image; R@5 over 536 candidates; frozen rows carry tau=1 by construction"}
    print("\n  matched pair tol003:", json.dumps(payload["widest_matched_pair_tol003"], ensure_ascii=False)[:300])
    print("  matched pair tol005:", json.dumps(payload["widest_matched_pair_tol005"], ensure_ascii=False)[:300])
    print(f"  corr tau~R1 = {corr_tau:.3f} | corr CG~R1 = {corr_gap_r1:.3f}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
