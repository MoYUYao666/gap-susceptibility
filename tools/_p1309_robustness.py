# -*- coding: utf-8 -*-
r"""Robustness checks for the appendix.

1. Trajectory correlations: for every archived per-epoch trajectory, Pearson of CG vs top-1 and of tau_5 vs top-1
   (the margin mass is not archived per checkpoint, so it is reported as unavailable there).
2. Binomial interval for the widest real-checkpoint pair, treating each top-1 number as a proportion over 5,000 images.
3. Half-sample stability: repeat the matched-gap sweep on two disjoint halves of the 5,000-image sample and report the
   widest spread at |dCG| <= 0.03 in each half (embeddings computed once, then split).

Outputs: outputs/analysis/a1_robustness.json
    python tools/_p1309_robustness.py [--apply]
"""
from __future__ import annotations

import argparse
import collections
import glob
import io
import json
import os

import numpy as np
import torch
import torch.nn.functional as F

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a1_robustness.json")
LAMBDAS = [-2, -1, -0.5, -0.25, 0.25, 0.5, 1, 2, 4]
ALPHAS = [0.1, 0.25, 0.5]
SIGMAS = [0.01, 0.02, 0.05, 0.1]
N = 5000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    out = {}

    # ---- 1. trajectory correlations (full per-epoch archive: a1_tau_trajectory.json)
    tr = json.load(io.open(os.path.join(REPO, "outputs", "a1_tau_trajectory.json"), encoding="utf-8"))
    cg_r, tau_r = [], []
    for name in ("text_only", "both"):
        rows = tr.get(name) or []
        if len(rows) < 3:
            continue
        top1 = np.array([r["top1"] for r in rows], dtype=float)
        cg = np.array([r["CG"] for r in rows], dtype=float)
        tau = np.array([r["tau"] for r in rows], dtype=float)
        if np.std(cg) > 1e-9:
            cg_r.append(float(np.corrcoef(cg, top1)[0, 1]))
        if np.std(tau) > 1e-9:
            tau_r.append(float(np.corrcoef(tau, top1)[0, 1]))
    out["trajectories"] = {"n": len(cg_r),
                           "cg_top1_pearson_mean": float(np.mean(cg_r)) if cg_r else None,
                           "tau_top1_pearson_mean": float(np.mean(tau_r)) if tau_r else None,
                           "margin_mass": "not archived per checkpoint"}
    print("  trajectory correlations: CG", round(float(np.mean(cg_r)), 3) if cg_r else None,
          "| tau", round(float(np.mean(tau_r)), 3) if tau_r else None)

    # ---- 2. binomial interval for the widest real pair
    rp = json.load(io.open(os.path.join(REPO, "outputs/analysis/a1_real_checkpoint_pairs.json"), encoding="utf-8"))
    p = rp["pairs"][0]
    n_eval = 5000
    p1, p2 = p["a"]["top1_5k"] / 100.0, p["b"]["top1_5k"] / 100.0
    se = np.sqrt(p1 * (1 - p1) / n_eval + p2 * (1 - p2) / n_eval) * 100
    diff = p1 * 100 - p2 * 100
    z = diff / se
    out["real_pair_binomial"] = {"top1_a": p["a"]["top1_5k"], "top1_b": p["b"]["top1_5k"],
                                 "difference": float(diff), "se": float(se),
                                 "ci95": [float(diff - 1.96 * se), float(diff + 1.96 * se)],
                                 "z": float(z), "n": n_eval}
    print("  binomial: diff %.2f se %.2f CI [%.2f, %.2f] z %.1f" % (diff, se, diff - 1.96 * se, diff + 1.96 * se, z))

    # ---- 3. half-sample stability
    torch.manual_seed(0)
    np.random.seed(42)
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
    rs = np.random.RandomState(42)
    idx = rs.choice(len(ds), size=min(N, len(ds)), replace=False)
    sub = ds.select(idx.tolist())
    labels = np.asarray(sub["label"])
    pil = [im.convert("RGB") for im in sub["image"]]
    texts = ["a photo of a " + c.replace("_", " ") for c in names]
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
        for i in range(0, len(texts), 256):
            ti = proc(text=texts[i:i + 256], return_tensors="pt", padding=True).to(device)
            o = model.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            tf.append(F.normalize(model.text_projection(pooled), dim=-1))
    tf = torch.cat(tf)[:len(names)]
    mu_i, mu_t = base.mean(0), tf.mean(0)
    gv = mu_t - mu_i
    gn = float(gv.norm().item())
    d_hat = gv / gn

    halves = {"first": np.arange(0, len(pil), 2), "second": np.arange(1, len(pil), 2)}
    res = {}
    for name, sel in halves.items():
        b = base[sel]
        lab = labels[sel]
        rows = []
        def meas(x, fam, param):
            cg = float((mu_t - x.mean(0)).norm().item())
            sn = (x @ tf.T).float().cpu().numpy()
            rows.append({"family": fam, "param": param, "CG": cg,
                         "top1": float((sn.argmax(1) == lab).mean() * 100)})
        meas(b, "frozen", 0.0)
        for lam in LAMBDAS:
            meas(F.normalize(b + lam * gn * d_hat, dim=-1), "T", lam)
        cls = sorted(set(lab.tolist()))
        cents = F.normalize(torch.stack([b[lab == c].mean(0) for c in cls]), dim=-1)
        lm = {c: i for i, c in enumerate(cls)}
        c_own = cents[torch.tensor([lm[int(x)] for x in lab], device=device)]
        for alpha in ALPHAS:
            meas(F.normalize((1 - alpha) * b + alpha * c_own, dim=-1), "P", alpha)
        dd = b.shape[1]
        for sigma in SIGMAS:
            g = torch.Generator(device=device).manual_seed(1000)
            eps = torch.randn(b.shape, generator=g, device=device) / np.sqrt(dd)
            meas(F.normalize(b + sigma * eps, dim=-1), "N", sigma)
        best = None
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                if abs(rows[i]["CG"] - rows[j]["CG"]) > 0.03:
                    continue
                sp = abs(rows[i]["top1"] - rows[j]["top1"])
                if best is None or sp > best:
                    best = sp
        res[name] = {"n_images": len(sel), "widest_spread_at_0.03": best}
        print(f"  half {name}: n={len(sel)} widest spread@0.03 = {best:.1f}")
    res["full_sample_reference"] = 32.7  # sparse grid, same lambdas as the halves
    out["half_sample"] = res

    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
