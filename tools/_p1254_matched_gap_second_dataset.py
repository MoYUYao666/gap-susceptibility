# -*- coding: utf-8 -*-
r"""Second-dataset replication of the matched-gap control.

The ImageNet-5k result (a1_matched_gap_families.json) shows that configurations sharing the same centroid gap can differ by
33 accuracy points. This script repeats the identical protocol on other locally available benchmarks, so the claim does
not rest on one dataset:

  families   T  translation along the gap direction (lambda grid)
             P  contraction toward each image's own class prototype (alpha grid)
             N  isotropic Gaussian noise (sigma grid, three seeds)
  statistic  CG = || mean(text emb) - mean(perturbed image emb) || on L2-normalised embeddings
             top-1 on the perturbed similarity matrix; tau on the frozen top-5 sets

Frozen forward passes only. Never overwrites the ImageNet-5k archive: output goes to
`outputs/analysis/a1_matched_gap_second_dataset.json`, keyed by benchmark.

    python tools/_p1254_matched_gap_second_dataset.py --benchmarks dtd food101 --n 5000 --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os
import random

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a1_matched_gap_second_dataset.json")

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


def load_benchmark(spec: str, n: int):
    """Return (pil images, labels, class names, template)."""
    if spec == "dtd":
        root = os.path.join(REPO, "data", "dtd", "dtd", "images")
        template = "a photo of a {} texture"
    elif spec == "food101":
        root = os.path.join(REPO, "data", "food-101", "images")
        template = "a photo of {}, a type of food"
    else:
        raise SystemExit("unsupported benchmark: " + spec)
    classes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    paths, labels = [], []
    for ci, c in enumerate(classes):
        files = sorted(f for f in os.listdir(os.path.join(root, c))
                       if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
        for f in files:
            paths.append(os.path.join(root, c, f))
            labels.append(ci)
    rs = np.random.RandomState(42)
    idx = rs.choice(len(paths), size=min(n, len(paths)), replace=False)
    pil = [Image.open(paths[i]).convert("RGB") for i in idx]
    return pil, np.asarray([labels[i] for i in idx]), classes, template


def run_benchmark(spec, n, model, proc, device, mid):
    pil, labels, names, template = load_benchmark(spec, n)
    print(f"  [{spec}] images={len(pil)} classes={len(names)} template={template!r}", flush=True)

    feats = []
    with torch.no_grad():
        for i in range(0, len(pil), 64):
            inp = proc(images=pil[i:i + 64], return_tensors="pt").to(device)
            v = model.vision_model(**inp)
            pooled = v[1] if isinstance(v, tuple) else v.pooler_output
            feats.append(F.normalize(model.visual_projection(pooled), dim=-1))
    base = torch.cat(feats)

    texts = [template.format(c.replace("_", " ")) for c in names]
    tf = []
    with torch.no_grad():
        for i in range(0, len(texts), 256):
            ti = proc(text=[str(t) for t in texts[i:i + 256]], return_tensors="pt", padding=True).to(device)
            o = model.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            tf.append(F.normalize(model.text_projection(pooled), dim=-1))
    tf = torch.cat(tf)[:len(names)]

    mu_i, mu_t = base.mean(0), tf.mean(0)
    gap_vec = mu_t - mu_i
    gap_norm = float(gap_vec.norm().item())
    d_hat = gap_vec / gap_norm

    base_np = (base @ tf.T).float().cpu().numpy()
    idx5 = np.argsort(-base_np, axis=1)[:, :5]
    frozen = {"CG": gap_norm, "top1": float((base_np.argmax(1) == labels).mean() * 100)}
    print(f"  [{spec}] frozen: CG={gap_norm:.4f} top1={frozen['top1']:.2f}", flush=True)

    def measure(x, tag):
        cg = float((mu_t - x.mean(0)).norm().item())
        sn = (x @ tf.T).float().cpu().numpy()
        top1 = float((sn.argmax(1) == labels).mean() * 100)
        return {"family": tag[0], "param": tag[1], "CG": cg, "top1": top1,
                "tau": kendall_topk(base_np, sn, idx5)}

    rows = [measure(base, ("frozen", 0.0))]
    for lam in LAMBDAS:
        rows.append(measure(F.normalize(base + lam * gap_norm * d_hat, dim=-1), ("T", lam)))
        print(f"   [{spec}] T lam={lam:>5}: CG={rows[-1]['CG']:.4f} top1={rows[-1]['top1']:.2f}", flush=True)

    cls_ids = sorted(set(labels.tolist()))
    cents = torch.stack([base[labels == c].mean(0) for c in cls_ids])
    cents = F.normalize(cents, dim=-1)
    lab_map = {c: i for i, c in enumerate(cls_ids)}
    c_own = cents[torch.tensor([lab_map[int(x)] for x in labels], device=device)]
    for alpha in ALPHAS:
        rows.append(measure(F.normalize((1 - alpha) * base + alpha * c_own, dim=-1), ("P", alpha)))
        print(f"   [{spec}] P a={alpha:>5}: CG={rows[-1]['CG']:.4f} top1={rows[-1]['top1']:.2f}", flush=True)

    d = base.shape[1]
    for sigma in SIGMAS:
        for s in NOISE_SEEDS:
            g = torch.Generator(device=device).manual_seed(1000 + s)
            eps = torch.randn(base.shape, generator=g, device=device) / np.sqrt(d)
            rows.append(measure(F.normalize(base + sigma * eps, dim=-1), ("N", sigma)))

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

    out = {"benchmark": spec, "model": mid, "n_images": len(pil), "n_classes": len(names),
           "template": template, "frozen": frozen, "rows": rows,
           "max_matched_gap_spread_tol003": best_pair(0.03),
           "max_matched_gap_spread_tol005": best_pair(0.05),
           "definition": "CG = || mean(text emb) - mean(perturbed image emb) || on L2-normalised embeddings"}
    b = out["max_matched_gap_spread_tol003"]
    print(f"  [{spec}] max top-1 spread at |dCG|<=0.03: {b['spread']:.1f} points "
          f"(dCG={b['dCG']:.3f})", flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmarks", nargs="+", default=["dtd", "food101"])
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    torch.manual_seed(0)
    np.random.seed(42)
    random.seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import CLIPModel, CLIPProcessor
    mid = "openai/clip-vit-base-patch32"
    for cand in (mid, os.path.join(REPO, "models", "clip-vit-base-patch32")):
        try:
            model = CLIPModel.from_pretrained(cand, local_files_only=True).to(device).eval()
            proc = CLIPProcessor.from_pretrained(cand, local_files_only=True)
            break
        except Exception:
            model = None
    assert model is not None, "CLIP ViT-B/32 not found locally"
    print(f"  device={device} model={mid}", flush=True)

    payload = {"model": mid, "n_images_requested": a.n, "benchmarks": {}}
    if os.path.exists(OUT):
        try:
            payload["benchmarks"].update(json.load(open(OUT, encoding="utf-8")).get("benchmarks", {}))
        except Exception:
            pass
    for spec in a.benchmarks:
        payload["benchmarks"][spec] = run_benchmark(spec, a.n, model, proc, device, mid)
        if a.apply:
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
            print("  wrote", os.path.relpath(OUT, REPO), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
