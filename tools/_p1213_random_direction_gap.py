# -*- coding: utf-8 -*-
r"""Random-direction matched-gap ensemble: how wide is the accuracy range at one fixed gap?

Section 5.2 compares two hand-picked lambda points. A reviewer can object that the pair was selected. This experiment
removes the selection: 200 random unit directions in image-embedding space are each translated by the amount that
restores the centroid gap to the frozen value, and the resulting top-1 distribution is measured. If the gap were a
sufficient statistic, every member of that ensemble would sit at the frozen accuracy.

Also records, for each member, the order statistic tau (top-5 Kendall against the frozen similarities) so the text can
show that tau separates the ensemble where the gap does not.

    python tools/_p1213_random_direction_gap.py [--apply] [--directions 200] [--orthogonal]
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
from scipy import stats

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a1_random_direction_gap.json")
TEMPLATE = "a photo of a {}"
N = 5000


def kendall_topk(base_np, cur_np, idx5):
    taus = []
    for i in range(len(base_np)):
        r1 = base_np[i][idx5[i]]
        r2 = cur_np[i][idx5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    return float(np.mean(taus)) if taus else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--directions", type=int, default=200)
    ap.add_argument("--orthogonal", action="store_true", help="draw directions orthogonal to the gap direction")
    ap.add_argument("--model", default="clip-vit-base-patch32")
    a = ap.parse_args()

    torch.manual_seed(0)
    np.random.seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import CLIPModel, CLIPProcessor
    local = os.path.join(REPO, "models", a.model)
    try:
        model = CLIPModel.from_pretrained(local, local_files_only=True).to(device).eval()
        proc = CLIPProcessor.from_pretrained(local, local_files_only=True)
    except Exception:
        mid = "openai/clip-vit-base-patch32"
        model = CLIPModel.from_pretrained(mid, local_files_only=True).to(device).eval()
        proc = CLIPProcessor.from_pretrained(mid, local_files_only=True)

    from datasets import Dataset
    parq = sorted(glob.glob(os.path.join(REPO, "data", "imagenet_hf", "*.parquet")))
    ds = Dataset.from_parquet(parq)
    names = [n.split(",")[0].strip() for n in ds.features["label"].names]
    if len(names) == 1001:
        names = names[:1000]
    rs = np.random.RandomState(42)
    idx = rs.choice(len(ds), size=min(N, len(ds)), replace=False)
    sub = ds.select(idx.tolist())
    labels = np.asarray(sub["label"])
    pil = [im.convert("RGB") for im in sub["image"]]
    print(f"  images={len(pil)} classes={len(names)} model={a.model}", flush=True)

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
    frozen_top1 = float((base_np.argmax(1) == labels).mean() * 100)
    print(f"  frozen CG={gap_norm:.4f} top1={frozen_top1:.2f}", flush=True)

    D = base.shape[1]

    def cg_and_top1(x):
        cg = float((mu_t - x.mean(0)).norm().item())
        sn = (x @ tf.T).float().cpu().numpy()
        return cg, float((sn.argmax(1) == labels).mean() * 100), sn

    # scale search: translate along u by s; find the s that lands closest to the frozen CG
    scales = np.linspace(0.0, 4.0, 41)
    rows = []
    for k in range(a.directions):
        u = torch.randn(D, device=device)
        if a.orthogonal:
            u = u - (u @ d_hat) * d_hat
        u = F.normalize(u, dim=0)
        best = None
        for s in scales:
            if s == 0.0:
                continue
            x = F.normalize(base + float(s) * gap_norm * u, dim=-1)
            cg, t1, sn = cg_and_top1(x)
            err = abs(cg - gap_norm)
            if best is None or err < best[0]:
                best = (err, s, cg, t1, sn)
        err, s, cg, t1, sn = best
        tau = kendall_topk(base_np, sn, idx5)
        rows.append({"k": k, "scale": float(s), "CG": cg, "top1": t1, "tau": tau, "cg_err": err})

    t1s = np.array([r["top1"] for r in rows])
    taus = np.array([r["tau"] for r in rows])
    cgs = np.array([r["CG"] for r in rows])
    summary = {
        "n_directions": len(rows), "orthogonal": bool(a.orthogonal),
        "frozen": {"CG": gap_norm, "top1": frozen_top1},
        "CG_matched": {"mean": float(cgs.mean()), "sd": float(cgs.std()),
                       "max_abs_err": float(np.abs(cgs - gap_norm).max())},
        "top1": {"min": float(t1s.min()), "max": float(t1s.max()), "mean": float(t1s.mean()),
                 "sd": float(t1s.std()), "p05": float(np.percentile(t1s, 5)),
                 "p50": float(np.percentile(t1s, 50)), "p95": float(np.percentile(t1s, 95)),
                 "range": float(t1s.max() - t1s.min())},
        "tau": {"min": float(taus.min()), "max": float(taus.max()), "mean": float(taus.mean())},
        "corr_tau_top1": float(stats.pearsonr(taus, t1s)[0]),
        "frac_below_frozen_by_10pts": float(np.mean(t1s < frozen_top1 - 10)),
    }
    print("\n  === matched-gap ensemble ===")
    for k, v in summary.items():
        print(f"   {k}: {v}")
    print("\n  worst 5 (lowest top-1 at matched gap):")
    for r in sorted(rows, key=lambda x: x["top1"])[:5]:
        print(f"   top1={r['top1']:5.2f}  tau={r['tau']:+.3f}  CG={r['CG']:.4f}  scale={r['scale']:.3f}")

    payload = {"model": a.model, "benchmark": "imagenet5k", "n_images": len(pil),
               "n_classes": len(names), "summary": summary, "rows": rows,
               "note": ("each direction is translated by the amount that restores the centroid gap to the frozen value; "
                        "a sufficient statistic would put every member at the frozen accuracy")}
    if a.apply:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        suffix = "_orth" if a.orthogonal else ""
        p = OUT.replace(".json", suffix + ".json")
        io.open(p, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("\n  wrote", os.path.relpath(p, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
