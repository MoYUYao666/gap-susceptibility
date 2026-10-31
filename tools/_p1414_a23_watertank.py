# -*- coding: utf-8 -*-
r"""A23: second acoustic corpus - water-tank sonar (11 classes, 395 test images).

Runs the same gap-surgery family with the two adapted marine encoders on the converted water-tank sonar images and records
top-1, centroid gap, order preservation tau and margin mass, so the acoustic-domain claim can be checked on a second,
in-domain-labelled corpus rather than only on NKSID.

Output: outputs/analysis/a23_watertank_domain.json

    conda run -n pytorch python tools/_p1414_a23_watertank.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
os.environ["HF_HUB_OFFLINE"] = "1"
import open_clip
from scipy import stats as st

ROOT = "outputs/analysis/watertank96_png/test"
META = "outputs/analysis/watertank96_meta.json"
OUT = "outputs/analysis/a23_watertank_domain.json"
LAMBDAS = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0]


def load_images():
    meta = json.load(io.open(META, encoding="utf-8"))
    classes = meta["classes"]
    pil, labels = [], []
    for ci, name in enumerate(classes):
        d = os.path.join(ROOT, name)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            pil.append(Image.open(os.path.join(d, f)).convert("RGB"))
            labels.append(ci)
    return pil, np.array(labels), classes


def build_model(tag):
    if tag == "bioclip":
        m, _, pre = open_clip.create_model_and_transforms(
            "ViT-B-16", pretrained="models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin", device="cuda")
    else:
        ck = torch.load("models/oceanclip-0.15b/oceanclip-bio/epoch_50.pt", map_location="cpu")
        m, _, pre = open_clip.create_model_and_transforms(
            "ViT-B-16", pretrained="models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin", device="cuda")
        m.load_state_dict(ck["state_dict"], strict=False)
    return m.eval(), pre


def kendall(a, b):
    num = den = 0.0
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            s1 = np.sign(a[i] - a[j])
            s2 = np.sign(b[i] - b[j])
            num += s1 * s2
            den += abs(s1 * s2)
    return num / den if den else 1.0


def encode(m, pre, imgs, texts):
    tok = open_clip.get_tokenizer("ViT-B-16")
    with torch.no_grad():
        tf = F.normalize(m.encode_text(tok(texts).to("cuda")), dim=-1)
        feats = []
        for i in range(0, len(imgs), 32):
            xs = torch.stack([pre(im) for im in imgs[i:i + 32]]).to("cuda")
            feats.append(F.normalize(m.encode_image(xs), dim=-1))
    return torch.cat(feats), tf


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    imgs, labels, classes = load_images()
    texts = ["a photo of a " + c.replace("-", " ") for c in classes]
    print(f"  water-tank test images: {len(imgs)}, classes: {len(classes)}", flush=True)
    payload = {"source": META, "n_test": len(imgs), "classes": classes, "models": {}}
    for tag in ("bioclip", "oceanclip"):
        m, pre = build_model(tag)
        ifeat, tfeat = encode(m, pre, imgs, texts)
        mu_i, mu_t = ifeat.mean(0), tfeat.mean(0)
        d = mu_t - mu_i
        gn = float(d.norm().item())
        dh = d / gn
        base_scores = (F.normalize(ifeat, dim=-1) @ tfeat.T).float().cpu().numpy()
        rows = []
        for lam in LAMBDAS:
            x = F.normalize(ifeat + lam * gn * dh, dim=-1)
            sn = (x @ tfeat.T).float().cpu().numpy()
            top1 = float((sn.argmax(1) == labels).mean() * 100)
            cg = float((tfeat.mean(0) - x.mean(0)).norm().item())
            taus = []
            for i in range(len(labels)):
                top5 = np.argsort(-base_scores[i])[:5]
                taus.append(kendall(base_scores[i][top5], sn[i][top5]))
            r = np.arange(len(labels))
            ts = sn[r, labels]
            s2 = sn.copy()
            s2[r, labels] = -1e9
            margin = ts - s2.max(1)
            rows.append({"lambda": lam, "top1": top1, "CG": cg, "tau": float(np.mean(taus)),
                         "mass_0.05": float((margin <= 0.10).mean())})
        top = np.array([r["top1"] for r in rows])
        cg = np.array([r["CG"] for r in rows])
        tau = np.array([r["tau"] for r in rows])
        payload["models"][tag] = {"rows": rows,
                                  "r_CG": float(st.pearsonr(cg, top)[0]),
                                  "r_tau": float(st.pearsonr(tau, top)[0]),
                                  "top1_range": [float(top.min()), float(top.max())]}
        print(f"  [{tag}] top1 {top.min():.1f}-{top.max():.1f} | r(CG)={payload['models'][tag]['r_CG']:+.2f} "
              f"r(tau)={payload['models'][tag]['r_tau']:+.2f}", flush=True)
        del m
        torch.cuda.empty_cache()
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("  wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
