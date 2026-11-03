# -*- coding: utf-8 -*-
r"""Out-of-benchmark test of the one-constant closed-form law.

Calibration on ImageNet-5k gave a single constant k = 0.550 that repairs the Gaussian branch of the first-order law
(MAE 0.115 -> 0.017). A constant fitted on one benchmark proves nothing until it is frozen and applied elsewhere, so this
script replays the frozen-model margin extraction on four unrelated benchmarks -- DTD (47 texture classes), Food-101 (101
food classes), iNat-wild (48 species) and the BioCLIP rare-species benchmark (50 species) -- using the benchmark's own
gap direction ('self' variant, which needs no Flickr30k) and predicts the whole tau(lambda) curve with k held at 0.550.

It also fits k separately on each benchmark to see whether the constant is universal or family-specific.

No training: frozen CLIP ViT-B/32 forward passes only.

    python tools/_p1207_crossbenchmark_closed_form.py [--apply] [--only dtd,food101]
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a1_crossbenchmark_closed_form.json")
K_IMAGENET = 0.550


def load_e3():
    path = os.path.join(REPO, "tools", "a1_rr_e3_benchmarks.py")
    spec = importlib.util.spec_from_file_location("e3bench", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", default=None)
    a = ap.parse_args()

    e3 = load_e3()
    torch.manual_seed(0)
    from transformers import CLIPModel, CLIPProcessor
    model_id = "openai/clip-vit-base-patch32"
    try:
        model = CLIPModel.from_pretrained(model_id, local_files_only=True).cuda().eval()
        processor = CLIPProcessor.from_pretrained(model_id, local_files_only=True)
    except Exception:
        model = CLIPModel.from_pretrained(os.path.join(REPO, "models", "clip-vit-base-patch32"),
                                          local_files_only=True).cuda().eval()
        processor = CLIPProcessor.from_pretrained(os.path.join(REPO, "models", "clip-vit-base-patch32"),
                                                  local_files_only=True)

    keys = a.only.split(",") if a.only else list(e3.LOADERS)
    out = {"meta": {"script": os.path.basename(__file__), "model": model_id + " (frozen)",
                    "k_frozen_from_imagenet": K_IMAGENET,
                    "gap_variant": "self (mean class-name text emb - mean benchmark image emb)",
                    "lambda_grid": e3.GRID, "topk": e3.TOPK}, "benchmarks": {}}
    # merge, do not overwrite: the benchmarks are usually run in separate invocations
    if os.path.exists(OUT):
        try:
            prev = json.load(io.open(OUT, encoding="utf-8"))
            out["benchmarks"] = prev.get("benchmarks", {})
            print(f"  merging into existing archive with {len(out['benchmarks'])} benchmarks", flush=True)
        except Exception:
            pass

    for key in keys:
        t0 = time.time()
        print(f"\n==================== {key} ====================", flush=True)
        names, sources, labels, meta = e3.LOADERS[key]()
        print(f"  loaded {len(sources)} images, {len(names)} classes", flush=True)
        base = e3.embed_images(model, processor, sources)
        tf = e3.embed_texts(model, processor, [e3.TEMPLATE.format(c.replace("_", " ")) for c in names])
        gap_vec = tf.mean(0) - base.mean(0)
        gap_norm = float(gap_vec.norm().item())
        d_hat = gap_vec / gap_norm
        m = (d_hat @ tf.T).cpu().numpy()
        base_np = (base @ tf.T).float().cpu().numpy()
        idx5 = np.argsort(-base_np, axis=1)[:, :e3.TOPK]
        n = len(base_np)
        sigma_m = float(np.std(m - m.mean()))
        sigma_b = float(np.sqrt(2.0) * sigma_m)

        # pairwise margins and bias differences inside each image's top-k set
        d_list, b_list = [], []
        for i in range(n):
            k5 = idx5[i]
            s5 = base_np[i][k5]
            for x in range(len(k5)):
                for y in range(x + 1, len(k5)):
                    d_list.append(float(s5[x] - s5[y]))
                    b_list.append(float(m[k5[y]] - m[k5[x]]))
        d_pairs = np.asarray(d_list, float)
        b_pairs = np.asarray(b_list, float)

        rows, fit_rows = [], []
        for lam in e3.GRID:
            shifted = F.normalize(base + lam * gap_norm * d_hat, dim=-1)
            Sl = (shifted @ tf.T).float().cpu().numpy()
            top1 = float((Sl.argmax(1) == labels).mean() * 100)
            tau, _ = e3.kendall_topk(base_np, Sl, idx5)

            def predict(k):
                sb = max(k * sigma_b, 1e-9)
                u = d_pairs / (abs(lam) * gap_norm * sb + 1e-12)
                return float(1.0 - 2.0 * np.mean(stats.norm.sf(u)))

            p = predict(K_IMAGENET)
            rows.append({"lambda": lam, "top1": top1, "tau_measured": tau,
                         "tau_pred_k055": p, "abs_err": abs(p - tau)})
            fit_rows.append((lam, tau))
            print(f"   lam={lam:>5.2f} top1={top1:6.2f} tau={tau:.4f} pred(k=.55)={p:.4f} err={abs(p-tau):.4f}",
                  flush=True)

        mae = float(np.mean([r["abs_err"] for r in rows]))
        r = float(stats.pearsonr([r["tau_pred_k055"] for r in rows],
                                 [r["tau_measured"] for r in rows])[0])
        # per-benchmark best k, for comparison only
        grid = np.linspace(0.3, 1.6, 66)
        best = (1e9, None)
        for k in grid:
            sb = max(k * sigma_b, 1e-9)
            sse = 0.0
            for lam, tm in fit_rows:
                u = d_pairs / (abs(lam) * gap_norm * sb + 1e-12)
                pr = float(1.0 - 2.0 * np.mean(stats.norm.sf(u)))
                sse += (pr - tm) ** 2
            if sse < best[0]:
                best = (sse, float(k))
        print(f"  ==> MAE(k=0.550)={mae:.4f}  r={r:.4f}  | per-benchmark best k={best[1]:.3f}", flush=True)
        out["benchmarks"][key] = {"n_images": n, "n_classes": len(names), "gap_norm": gap_norm,
                                  "sigma_m": sigma_m, "sigma_b": sigma_b,
                                  "mae_k055": mae, "pearson_r_k055": r,
                                  "k_best_this_benchmark": best[1],
                                  "surgery": rows}
        del base, tf
        torch.cuda.empty_cache()
        print(f"  elapsed {time.time()-t0:.1f}s", flush=True)

    if a.apply:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("\n  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
