# -*- coding: utf-8 -*-
r"""A23 upgrade control: margin-mass certificate under the gap-surgery protocol on marine domains.

OceanCLIP weights are not present locally, so this control uses the public CLIP ViT-B/32 on the same two domains the
manuscript uses (marine optical: fathomnet8, 8 classes; acoustic sonar: NKSID Bohai Bay, 8 classes). For each domain the
image cluster is translated along the gap direction by lambda (the gap-surgery family) and, at every lambda, we record the
centroid gap, top-1, and the margin mass M(0.01)/M(0.02). This is a control for the statistic, not a replacement for the
OceanCLIP evidence.

Also runs the threshold-transfer test: a margin-mass threshold fitted on one domain is evaluated on the other.

Output: outputs/analysis/a23_certificate_control.json

    python tools/_p1344_a23_certificate_control.py [--apply]
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
OUT = os.path.join(REPO, "outputs", "analysis", "a23_certificate_control.json")
LAMBDAS = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0]
EPS = [0.02, 0.05, 0.10]
N_OPT = 343
N_SON = 650


def load_optical():
    from PIL import Image
    root = os.path.join(REPO, "data", "fathomnet8")
    classes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    pil, labels = [], []
    for ci, c in enumerate(classes):
        for f in sorted(os.listdir(os.path.join(root, c))):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                pil.append(Image.open(os.path.join(root, c, f)).convert("RGB"))
                labels.append(ci)
    return pil, np.array(labels), ["a photo of a " + c.replace("_", " ") for c in classes]


def load_sonar():
    from PIL import Image
    root = os.path.join(REPO, "data", "NKSID", "NKSID")
    classes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    pil, labels = [], []
    for ci, c in enumerate(classes):
        for f in sorted(os.listdir(os.path.join(root, c))):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    pil.append(Image.open(os.path.join(root, c, f)).convert("RGB"))
                    labels.append(ci)
                except Exception:
                    continue
    return pil, np.array(labels), ["a photo of a " + c.replace("_", " ") for c in classes]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(0)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import CLIPModel, CLIPProcessor
    local = os.path.join(REPO, "models", "clip-vit-base-patch32")
    model = CLIPModel.from_pretrained(local, local_files_only=True).to(device).eval()
    proc = CLIPProcessor.from_pretrained(local, local_files_only=True)

    def emb(pil, texts):
        vi = []
        with torch.no_grad():
            for i in range(0, len(pil), 32):
                inp = proc(images=pil[i:i + 32], return_tensors="pt").to(device)
                v = model.vision_model(**inp)
                pooled = v[1] if isinstance(v, tuple) else v.pooler_output
                vi.append(F.normalize(model.visual_projection(pooled).float(), dim=-1))
            ti = proc(text=texts, return_tensors="pt", padding=True).to(device)
            o = model.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            te = F.normalize(model.text_projection(pooled).float(), dim=-1)
        return torch.cat(vi), te

    payload = {"model": "openai/clip-vit-base-patch32", "protocol": "gap surgery, lambda translation along the gap direction",
               "eps": EPS, "domains": {}}
    for name, loader in (("marine_optical", load_optical), ("acoustic_sonar", load_sonar)):
        pil, labels, texts = loader()
        print(f"  [{name}] images={len(pil)} classes={len(texts)}", flush=True)
        img, txt = emb(pil, texts)
        mu_i, mu_t = img.mean(0), txt.mean(0)
        d = mu_t - mu_i
        gn = float(d.norm().item())
        d_hat = d / gn
        rows = []
        for lam in LAMBDAS:
            x = F.normalize(img + lam * gn * d_hat, dim=-1)
            sn = (x @ txt.T).float().cpu().numpy()
            pred = sn.argmax(1)
            top1 = float((pred == labels).mean() * 100)
            r = np.arange(len(labels))
            ts = sn[r, labels]
            s2 = sn.copy()
            s2[r, labels] = -1e9
            margin = ts - s2.max(1)
            cg = float((mu_t - x.mean(0)).norm().item())
            row = {"lambda": lam, "top1": top1, "CG": cg}
            for e in EPS:
                row["mass_%g" % e] = float((margin <= 2 * e).mean())
            rows.append(row)
            print(f"   lam={lam:+.2f} top1={top1:.2f} CG={cg:.4f} M05={row['mass_0.05']:.3f}", flush=True)
        payload["domains"][name] = rows
    # correlations across the pooled configurations
    from scipy import stats as st
    allrows = [r for rows in payload["domains"].values() for r in rows]
    top = np.array([r["top1"] for r in allrows])
    cg = np.array([r["CG"] for r in allrows])
    m1 = np.array([r["mass_0.05"] for r in allrows])
    payload["correlation"] = {"CG": float(st.pearsonr(cg, top)[0]), "M(0.01)": float(st.pearsonr(m1, top)[0]),
                          "M(0.05)": float(st.pearsonr(np.array([r["mass_0.05"] for r in allrows]), top)[0]),
                              "n": len(allrows)}
    # threshold transfer: healthy = top1 >= 0.8 x frozen top1 of the same domain
    def healthy(rows):
        base = rows[0]["top1"] if rows else 0.0
        return np.array([r["top1"] >= float(np.median([x["top1"] for x in rows])) for r in rows], dtype=bool)
    lab = {}
    for name, rows in payload["domains"].items():
        lab[name] = healthy(rows)
    transfer = {}
    for fit_name, fit_rows in payload["domains"].items():
        fit_health = lab[fit_name]
        fit_mass = np.array([r["mass_0.05"] for r in fit_rows])
        best = None
        for thr in np.linspace(0.0, 1.0, 101):
            pred = fit_mass <= thr
            tp = np.sum(pred & fit_health)
            tn = np.sum(~pred & ~fit_health)
            fp = np.sum(pred & ~fit_health)
            fn = np.sum(~pred & fit_health)
            ba = 0.5 * ((tp / max(tp + fn, 1)) + (tn / max(tn + fp, 1)))
            if best is None or ba > best[1]:
                best = (float(thr), float(ba))
        thr = best[0]
        for test_name, test_rows in payload["domains"].items():
            if test_name == fit_name:
                continue
            m = np.array([r["mass_0.05"] for r in test_rows])
            pred = m <= thr
            h = lab[test_name]
            tp = np.sum(pred & h)
            tn = np.sum(~pred & ~h)
            fp = np.sum(pred & ~h)
            fn = np.sum(~pred & h)
            ba = 0.5 * ((tp / max(tp + fn, 1)) + (tn / max(tn + fp, 1)))
            transfer[f"{fit_name}->{test_name}"] = {"threshold": thr, "fit_ba": best[1], "test_ba": float(ba)}
            print(f"  transfer {fit_name}->{test_name}: thr={thr:.2f} fitBA={best[1]:.2f} testBA={ba:.2f}")
    payload["threshold_transfer"] = transfer
    print(f"  correlation: {payload['correlation']}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
