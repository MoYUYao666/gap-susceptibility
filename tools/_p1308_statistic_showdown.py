# -*- coding: utf-8 -*-
r"""Statistic showdown: CG vs tau vs margin mass, measured on the same configurations, in two task regimes.

Scenario 1 (classification): the ImageNet-5k synthetic families (translation along the gap, class contraction, noise). For
each configuration compute the centroid gap, the top-1 accuracy, tau_5 against the frozen top-5 sets, and the margin mass
M(eps) = n^-1 #{i : margin_i <= 2 eps} for eps in {0.01, 0.02}.

Scenario 2 (retrieval): the 536 image-caption pairs. Same statistics, with the margin defined against the paired caption:
m_i = s_i(pair) - max_{j != pair} s_i(j).

Outputs: outputs/analysis/a1_statistic_showdown.json
    python tools/_p1308_statistic_showdown.py [--apply]
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
OUT = os.path.join(REPO, "outputs", "analysis", "a1_statistic_showdown.json")
LAMBDAS = [-2, -1, -0.5, -0.25, 0.25, 0.5, 1, 2, 4]
ALPHAS = [0.1, 0.25, 0.5]
SIGMAS = [0.01, 0.02, 0.05, 0.1]
EPS = [0.01, 0.02]
N = 5000


def kendall_topk(base_np, cur_np, k=5):
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


def margin_stats(sn, target, n_classes):
    """margin of the target class over the best other class, per row."""
    n = len(sn)
    rows = np.arange(n)
    true_s = sn[rows, target]
    s = sn.copy()
    s[rows, target] = -1e9
    best_other = s.max(1)
    m = true_s - best_other
    return m


def collect(model, proc, imgs, texts, target, device, tag, base_ref=None):
    has_vproj = hasattr(model, "visual_projection")
    has_tproj = hasattr(model, "text_projection")
    is_siglip = type(model).__name__.lower().startswith("siglip")
    feats = []
    with torch.no_grad():
        for i in range(0, len(imgs), 64):
            inp = proc(images=imgs[i:i + 64], return_tensors="pt").to(device)
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
    tf = torch.cat(tf)[:len(texts)]
    mu_i, mu_t = base.mean(0), tf.mean(0)
    gv = mu_t - mu_i
    gn = float(gv.norm().item())
    d_hat = gv / gn
    return base, tf, mu_i, mu_t, gn, d_hat


def measure(x, tf, mu_t, target, tag, fam, param, base_np, rows):
    cg = float((mu_t - x.mean(0)).norm().item())
    sn = (x @ tf.T).float().cpu().numpy()
    top1 = float((sn.argmax(1) == target).mean() * 100)
    m = margin_stats(sn, target, tf.shape[0])
    row = {"family": fam, "param": param, "CG": cg, "top1": top1,
           "tau5": kendall_topk(base_np, sn, 5) if base_np is not None else 1.0}
    for e in EPS:
        row["mass_%g" % e] = float((m <= 2 * e).mean())
    rows.append(row)


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
    payload = {"model": "openai/clip-vit-base-patch32", "eps": EPS, "scenarios": {}}

    # ---- scenario 1: ImageNet-5k synthetic families
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
    texts = ["a photo of a " + c.replace("_", " ") for c in names]
    base, tf, mu_i, mu_t, gn, d_hat = collect(model, proc, pil, texts, labels, device, "cls")
    base_np = (base @ tf.T).float().cpu().numpy()
    rows = []
    measure(base, tf, mu_t, labels, "cls", "frozen", 0.0, None, rows)
    for lam in LAMBDAS:
        measure(F.normalize(base + lam * gn * d_hat, dim=-1), tf, mu_t, labels, "cls", "T", lam, base_np, rows)
    cls = sorted(set(labels.tolist()))
    cents = F.normalize(torch.stack([base[labels == c].mean(0) for c in cls]), dim=-1)
    lm = {c: i for i, c in enumerate(cls)}
    c_own = cents[torch.tensor([lm[int(x)] for x in labels], device=device)]
    for alpha in ALPHAS:
        measure(F.normalize((1 - alpha) * base + alpha * c_own, dim=-1), tf, mu_t, labels, "cls", "P", alpha, base_np, rows)
    dd = base.shape[1]
    for sigma in SIGMAS:
        g = torch.Generator(device=device).manual_seed(1000)
        eps = torch.randn(base.shape, generator=g, device=device) / np.sqrt(dd)
        measure(F.normalize(base + sigma * eps, dim=-1), tf, mu_t, labels, "cls", "N", sigma, base_np, rows)
    payload["scenarios"]["classification"] = rows
    print(f"  classification configs: {len(rows)}", flush=True)

    # ---- scenario 2: retrieval (536 image-caption pairs)
    root = os.path.join(REPO, "data", "marine_captions")
    imgs = sorted(glob.glob(os.path.join(root, "*.jpg")))
    caps = json.load(io.open(os.path.join(root, "captions.json"), encoding="utf-8"))["captions"]
    n2 = min(len(imgs), len(caps))
    pil2 = [Image.open(p).convert("RGB") for p in imgs[:n2]]
    texts2 = [str(c) for c in caps[:n2]]
    target2 = np.arange(n2)
    base2, tf2, mu_i2, mu_t2, gn2, d_hat2 = collect(model, proc, pil2, texts2, target2, device, "ret")
    base_np2 = (base2 @ tf2.T).float().cpu().numpy()
    rows2 = []
    measure(base2, tf2, mu_t2, target2, "ret", "frozen", 0.0, None, rows2)
    for lam in LAMBDAS:
        measure(F.normalize(base2 + lam * gn2 * d_hat2, dim=-1), tf2, mu_t2, target2, "ret", "T", lam, base_np2, rows2)
    for alpha in ALPHAS:
        measure(F.normalize((1 - alpha) * base2 + alpha * tf2[:len(base2)], dim=-1), tf2, mu_t2, target2,
                "ret", "P", alpha, base_np2, rows2)
    for sigma in SIGMAS:
        g = torch.Generator(device=device).manual_seed(1000)
        eps = torch.randn(base2.shape, generator=g, device=device) / np.sqrt(base2.shape[1])
        measure(F.normalize(base2 + sigma * eps, dim=-1), tf2, mu_t2, target2, "ret", "N", sigma, base_np2, rows2)
    payload["scenarios"]["retrieval"] = rows2
    print(f"  retrieval configs: {len(rows2)}", flush=True)

    # ---- correlations
    from scipy import stats as st
    corr = {}
    for scen, rr in payload["scenarios"].items():
        top1 = np.array([r["top1"] for r in rr])
        corr[scen] = {"CG": float(st.pearsonr(np.array([r["CG"] for r in rr]), top1)[0])}
        for key in ("tau5", "mass_0.01", "mass_0.02"):
            vals = np.array([r[key] if r[key] is not None else np.nan for r in rr])
            ok = np.isfinite(vals) & np.isfinite(top1)
            corr[scen][key] = float(st.pearsonr(vals[ok], top1[ok])[0]) if ok.sum() > 2 and np.std(vals[ok]) > 1e-12 else None
    payload["correlation_with_top1"] = corr
    print("\n  correlation with accuracy:")
    for scen, c in corr.items():
        print("   ", scen, {k: (round(v, 3) if v is not None else None) for k, v in c.items()})
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
    print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
