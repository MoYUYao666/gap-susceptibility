# -*- coding: utf-8 -*-
r"""More benchmarks and bootstrap intervals for the matched-gap control (novelty items 5 and 6).

Item 5: repeat the frozen-CLIP matched-gap protocol on two further local benchmarks, iNaturalist-wild (50 species
folder tree) and the rare-species parquet release (classes from the common names, at least five images each).

Item 6: every matched-gap spread is a difference of two top-1 numbers measured on the same images, so it is cheap to
bootstrap. For the flagship ImageNet-5k pair and for each new benchmark's widest pair this script reports a 95 %
interval over 500 image-level resamples, plus the interval of the class-contraction gain.

Only frozen forward passes; no training, no downloads.

Input : data/imagenet_hf, data/inat_wild, data/rare-species
Output: outputs/analysis/a1_more_benchmarks.json

    python tools/_p1264_more_benchmarks.py --benchmarks imagenet5k inat_wild rare_species --apply
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
OUT = os.path.join(REPO, "outputs", "analysis", "a1_more_benchmarks.json")

LAMBDAS = [-2, -1, -0.5, -0.25, 0.25, 0.5, 1, 2, 4]
ALPHAS = [0.1, 0.25, 0.5]
SIGMAS = [0.01, 0.02, 0.05, 0.1, 0.2]
NOISE_SEEDS = [0, 1]
N = 5000


def load_benchmark(spec, n):
    if spec == "imagenet5k":
        from datasets import Dataset
        parq = sorted(glob.glob(os.path.join(REPO, "data", "imagenet_hf", "*.parquet")))
        ds = Dataset.from_parquet(parq)
        names = [x.split(",")[0].strip() for x in ds.features["label"].names]
        if len(names) == 1001:
            names = names[:1000]
        rs = np.random.RandomState(42)
        idx = rs.choice(len(ds), size=min(n, len(ds)), replace=False)
        sub = ds.select(idx.tolist())
        return [im.convert("RGB") for im in sub["image"]], np.asarray(sub["label"]), names, "a photo of a {}"
    if spec == "inat_wild":
        root = os.path.join(REPO, "data", "inat_wild")
        classes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and not d.startswith("."))
        names = [c.replace("_", " ") for c in classes]
        paths, labels = [], []
        for ci, c in enumerate(classes):
            for f in sorted(os.listdir(os.path.join(root, c))):
                if f.lower().endswith((".jpg", ".jpeg", ".png")):
                    paths.append(os.path.join(root, c, f))
                    labels.append(ci)
        rs = np.random.RandomState(42)
        idx = rs.choice(len(paths), size=min(n, len(paths)), replace=False)
        return [Image.open(paths[i]).convert("RGB") for i in idx], np.asarray([labels[i] for i in idx]), names, \
            "a photo of a {}"
    if spec == "rare_species":
        from datasets import load_dataset
        fs = sorted(glob.glob(os.path.join(REPO, "data", "rare-species", "data", "*.parquet")))
        ds = load_dataset("parquet", data_files=fs, split="train")
        counts = {}
        for c in ds["common"]:
            counts[c] = counts.get(c, 0) + 1
        keep = {c for c, k in counts.items() if k >= 5 and c and c != "None"}
        names = sorted(keep)
        name_to_i = {c: i for i, c in enumerate(names)}
        rows = [(i, name_to_i[c]) for i, c in enumerate(ds["common"]) if c in keep]
        rs = np.random.RandomState(42)
        sel = rs.choice(len(rows), size=min(n, len(rows)), replace=False)
        rows = [rows[i] for i in sel]
        pil = [ds[i]["file_name"].convert("RGB") for i, _ in rows]
        return pil, np.asarray([lab for _, lab in rows]), names, "a photo of a {}"
    raise SystemExit("unsupported benchmark " + spec)


def bootstrap_ci(correct_a, correct_b, n_boot=500, seed=0):
    """95 % interval of mean(a) - mean(b) over image-level resamples."""
    rs = np.random.RandomState(seed)
    n = len(correct_a)
    diffs = []
    for _ in range(n_boot):
        idx = rs.randint(0, n, n)
        diffs.append(float(100 * (correct_a[idx].mean() - correct_b[idx].mean())))
    return [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]


def run(spec, model, proc, device, tag):
    pil, labels, names, template = load_benchmark(spec, N)
    print(f"  [{spec}] images={len(pil)} classes={len(names)}", flush=True)
    has_vproj, has_tproj = hasattr(model, "visual_projection"), hasattr(model, "text_projection")
    feats = []
    with torch.no_grad():
        for i in range(0, len(pil), 64):
            inp = proc(images=pil[i:i + 64], return_tensors="pt").to(device)
            v = model.vision_model(**inp)
            pooled = v[1] if isinstance(v, tuple) else v.pooler_output
            feats.append(F.normalize((model.visual_projection(pooled) if has_vproj else pooled).float(), dim=-1))
    base = torch.cat(feats)
    texts = [template.format(c) for c in names]
    tf = []
    with torch.no_grad():
        for i in range(0, len(texts), 256):
            ti = proc(text=texts[i:i + 256], return_tensors="pt", padding=True).to(device)
            o = model.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            tf.append(F.normalize((model.text_projection(pooled) if has_tproj else pooled).float(), dim=-1))
    tf = torch.cat(tf)[:len(names)]

    mu_i, mu_t = base.mean(0), tf.mean(0)
    gap_vec = mu_t - mu_i
    gap_norm = float(gap_vec.norm().item())
    d_hat = gap_vec / gap_norm
    base_np = (base @ tf.T).float().cpu().numpy()
    frozen_correct = (base_np.argmax(1) == labels)
    frozen = {"CG": gap_norm, "top1": float(frozen_correct.mean() * 100)}
    print(f"  [{spec}] frozen CG={gap_norm:.4f} top1={frozen['top1']:.2f}", flush=True)

    pts = {}
    def measure(x, key):
        cg = float((mu_t - x.mean(0)).norm().item())
        sn = (x @ tf.T).float().cpu().numpy()
        correct = (sn.argmax(1) == labels)
        pts[key] = {"CG": cg, "top1": float(correct.mean() * 100), "correct": correct}
        return pts[key]
    measure(base, ("frozen", 0.0))
    for lam in LAMBDAS:
        measure(F.normalize(base + lam * gap_norm * d_hat, dim=-1), ("T", lam))
    cls_ids = sorted(set(labels.tolist()))
    cents = F.normalize(torch.stack([base[labels == c].mean(0) for c in cls_ids]), dim=-1)
    lab_map = {c: i for i, c in enumerate(cls_ids)}
    c_own = cents[torch.tensor([lab_map[int(x)] for x in labels], device=device)]
    for alpha in ALPHAS:
        measure(F.normalize((1 - alpha) * base + alpha * c_own, dim=-1), ("P", alpha))
    d = base.shape[1]
    for sigma in SIGMAS:
        for s in NOISE_SEEDS:
            g = torch.Generator(device=device).manual_seed(1000 + s)
            eps = torch.randn(base.shape, generator=g, device=device) / np.sqrt(d)
            measure(F.normalize(base + sigma * eps, dim=-1), ("N", sigma))

    rows = [{"family": k[0], "param": k[1], "CG": v["CG"], "top1": v["top1"]} for k, v in pts.items()]
    best = None
    for ka, va in pts.items():
        for kb, vb in pts.items():
            if ka >= kb:
                continue
            if abs(va["CG"] - vb["CG"]) > 0.03:
                continue
            spread = abs(va["top1"] - vb["top1"])
            if best is None or spread > best["spread"]:
                best = {"spread": spread, "dCG": abs(va["CG"] - vb["CG"]),
                        "a": {"family": ka[0], "param": ka[1], "CG": va["CG"], "top1": va["top1"]},
                        "b": {"family": kb[0], "param": kb[1], "CG": vb["CG"], "top1": vb["top1"]},
                        "ci95": bootstrap_ci(va["correct"], vb["correct"])}
    p_best = max((v["top1"] for k, v in pts.items() if k[0] == "P"), default=None)
    if p_best is not None:
        keys = [k for k in pts if k[0] == "P"]
        best_p = max(keys, key=lambda k: pts[k]["top1"])
        contraction = {"top1_gain": pts[best_p]["top1"] - frozen["top1"],
                       "CG_change": pts[best_p]["CG"] - frozen["CG"],
                       "ci95": bootstrap_ci(pts[best_p]["correct"], frozen_correct)}
    else:
        contraction = None
    print(f"  [{spec}] matched spread={best['spread']:.1f} CI={best['ci95']} dCG={best['dCG']:.3f}; "
          f"contraction={contraction['top1_gain']:.1f} pts CI={contraction['ci95']}", flush=True)
    return {"benchmark": spec, "n_images": len(pil), "n_classes": len(names), "template": template,
            "frozen": frozen, "rows": rows, "widest_matched_pair": best, "contraction": contraction}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmarks", nargs="+", default=["imagenet5k", "inat_wild", "rare_species"])
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(0)
    np.random.seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import CLIPModel, CLIPProcessor
    mid = "openai/clip-vit-base-patch32"
    for cand in (os.path.join(REPO, "models", "clip-vit-base-patch32"), mid):
        try:
            model = CLIPModel.from_pretrained(cand, local_files_only=True).to(device).eval()
            proc = CLIPProcessor.from_pretrained(cand, local_files_only=True)
            break
        except Exception:
            model = None
    assert model is not None
    payload = {"model": mid, "benchmarks": {}}
    if os.path.exists(OUT):
        try:
            payload["benchmarks"] = json.load(io.open(OUT, encoding="utf-8")).get("benchmarks", {})
        except Exception:
            pass
    for spec in a.benchmarks:
        payload["benchmarks"][spec] = run(spec, model, proc, device, spec)
        if a.apply:
            io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
            print("  wrote", os.path.relpath(OUT, REPO), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
