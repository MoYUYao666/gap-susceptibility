# -*- coding: utf-8 -*-
r"""Bootstrap intervals for the DTD and Food-101 matched-gap results (finishes the uniform table).

The three benchmarks added in the appendix carry 95 % intervals; DTD and Food-101 (Section secondbench) do not. This
script re-measures those two with the same protocol and per-image correctness records, then merges the results into
outputs/analysis/a1_more_benchmarks.json under their own keys, so one archive backs the whole table.

    python tools/_p1281_ci_dtd_food101.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools"))
OUT = os.path.join(REPO, "outputs", "analysis", "a1_more_benchmarks.json")
LAMBDAS = [-2, -1, -0.5, -0.25, 0.25, 0.5, 1, 2, 4]
ALPHAS = [0.1, 0.25, 0.5]
SIGMAS = [0.01, 0.02, 0.05, 0.1]
NOISE_SEEDS = [0, 1]
N = 5000


def bootstrap(a, b, n_boot=500, seed=0):
    rs = np.random.RandomState(seed)
    n = len(a)
    d = [float(100 * (a[rs.randint(0, n, n)].mean() - b[rs.randint(0, n, n)].mean())) for _ in range(n_boot)]
    return [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(0)
    np.random.seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import CLIPModel, CLIPProcessor
    from _p1254_matched_gap_second_dataset import load_benchmark

    model = CLIPModel.from_pretrained(os.path.join(REPO, "models", "clip-vit-base-patch32"),
                                      local_files_only=True).to(device).eval()
    proc = CLIPProcessor.from_pretrained(os.path.join(REPO, "models", "clip-vit-base-patch32"),
                                         local_files_only=True)

    payload = {"model": "openai/clip-vit-base-patch32", "benchmarks": {}}
    if os.path.exists(OUT):
        payload["benchmarks"] = json.load(io.open(OUT, encoding="utf-8")).get("benchmarks", {})

    for spec in ("dtd", "food101"):
        pil, labels, names, template = load_benchmark(spec, N)
        print(f"  [{spec}] images={len(pil)} classes={len(names)}", flush=True)
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
                ti = proc(text=texts[i:i + 256], return_tensors="pt", padding=True).to(device)
                o = model.text_model(**ti)
                pooled = o[1] if isinstance(o, tuple) else o.pooler_output
                tf.append(F.normalize(model.text_projection(pooled), dim=-1))
        tf = torch.cat(tf)[:len(names)]
        mu_i, mu_t = base.mean(0), tf.mean(0)
        gap_vec = mu_t - mu_i
        gn = float(gap_vec.norm().item())
        d_hat = gap_vec / gn
        base_np = (base @ tf.T).float().cpu().numpy()
        frozen_correct = (base_np.argmax(1) == labels)
        frozen = {"CG": gn, "top1": float(frozen_correct.mean() * 100)}
        print(f"  [{spec}] frozen CG={gn:.4f} top1={frozen['top1']:.2f}", flush=True)

        pts = {}
        def measure(x, key):
            cg = float((mu_t - x.mean(0)).norm().item())
            sn = (x @ tf.T).float().cpu().numpy()
            correct = (sn.argmax(1) == labels)
            pts[key] = {"CG": cg, "top1": float(correct.mean() * 100), "correct": correct}
        measure(base, ("frozen", 0.0))
        for lam in LAMBDAS:
            measure(F.normalize(base + lam * gn * d_hat, dim=-1), ("T", lam))
        cls = sorted(set(labels.tolist()))
        cents = F.normalize(torch.stack([base[labels == c].mean(0) for c in cls]), dim=-1)
        lm = {c: i for i, c in enumerate(cls)}
        c_own = cents[torch.tensor([lm[int(x)] for x in labels], device=device)]
        for alpha in ALPHAS:
            measure(F.normalize((1 - alpha) * base + alpha * c_own, dim=-1), ("P", alpha))
        dd = base.shape[1]
        for sigma in SIGMAS:
            for s in NOISE_SEEDS:
                g = torch.Generator(device=device).manual_seed(1000 + s)
                eps = torch.randn(base.shape, generator=g, device=device) / np.sqrt(dd)
                measure(F.normalize(base + sigma * eps, dim=-1), ("N", sigma))

        rows = [{"family": k[0], "param": k[1], "CG": v["CG"], "top1": v["top1"]} for k, v in pts.items()]
        best = None
        for ka, va in pts.items():
            for kb, vb in pts.items():
                if ka >= kb or abs(va["CG"] - vb["CG"]) > 0.03:
                    continue
                sp = abs(va["top1"] - vb["top1"])
                if best is None or sp > best["spread"]:
                    best = {"spread": sp, "dCG": abs(va["CG"] - vb["CG"]),
                            "a": {"family": ka[0], "param": ka[1], "CG": va["CG"], "top1": va["top1"]},
                            "b": {"family": kb[0], "param": kb[1], "CG": vb["CG"], "top1": vb["top1"]},
                            "ci95": bootstrap(va["correct"], vb["correct"])}
        pk = max((k for k in pts if k[0] == "P"), key=lambda k: pts[k]["top1"])
        contraction = {"top1_gain": pts[pk]["top1"] - frozen["top1"],
                       "CG_change": pts[pk]["CG"] - frozen["CG"],
                       "ci95": bootstrap(pts[pk]["correct"], frozen_correct)}
        payload["benchmarks"][spec] = {"benchmark": spec, "n_images": len(pil), "n_classes": len(names),
                                       "template": template, "frozen": frozen, "rows": rows,
                                       "widest_matched_pair": best, "contraction": contraction}
        print(f"  [{spec}] spread={best['spread']:.1f} CI={[round(x,1) for x in best['ci95']]} "
              f"| contraction {contraction['top1_gain']:.1f} CI={[round(x,1) for x in contraction['ci95']]}", flush=True)
        if a.apply:
            io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
            print("  wrote", os.path.relpath(OUT, REPO), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
