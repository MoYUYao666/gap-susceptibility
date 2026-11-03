# -*- coding: utf-8 -*-
r"""A23: second acoustic corpus (UATD-derived detection crops) under the same gap-surgery protocol.

Builds a detection-crop classification set from the local UATD-derived YOLO corpus (riku1825: 11 classes), then runs the
same gap-surgery family with the two adapted marine encoders and records top-1, centroid gap, order preservation tau and
margin mass at every amplitude.

Output: outputs/analysis/a23_uatd_domain.json

    conda run -n pytorch python tools/_p1382_a23_uatd_domain.py --apply
"""
from __future__ import annotations

import argparse
import collections
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

BASE = "data/second_sonar/riku1825/Dataset"
OUT = "outputs/analysis/a23_uatd_domain.json"
LAMBDAS = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0]
CLASSES = ["mine", "can", "bottle", "drink-carton", "chain", "propeller", "tire", "hook", "valve",
           "shampoo-bottle", "standing-bottle"]
MAX_TRAIN, MAX_TEST = 25, 10


def load_crops():
    rs = np.random.RandomState(42)
    train = collections.defaultdict(list)
    test = collections.defaultdict(list)
    for split, target, cap in (("train", train, MAX_TRAIN), ("val", test, MAX_TEST), ("test", test, MAX_TEST)):
        labels = sorted(os.listdir(os.path.join(BASE, "labels", split)))
        for lf in labels:
            img_name = os.path.splitext(lf)[0] + ".jpg"
            ip = os.path.join(BASE, "images", split, img_name)
            if not os.path.exists(ip):
                for ext in (".png", ".jpeg"):
                    cand = os.path.join(BASE, "images", split, os.path.splitext(lf)[0] + ext)
                    if os.path.exists(cand):
                        ip = cand
                        break
            if not os.path.exists(ip):
                continue
            try:
                im = Image.open(ip).convert("RGB")
            except Exception:
                continue
            W, H = im.size
            for line in io.open(os.path.join(BASE, "labels", split, lf), encoding="utf-8"):
                parts = line.split()
                if len(parts) < 5:
                    continue
                ci = int(float(parts[0]))
                if ci < 0 or ci >= len(CLASSES):
                    continue
                cx, cy, w, h = map(float, parts[1:5])
                x0, y0 = max(0, int((cx - w / 2 - 0.05) * W)), max(0, int((cy - h / 2 - 0.05) * H))
                x1, y1 = min(W, int((cx + w / 2 + 0.05) * W)), min(H, int((cy + h / 2 + 0.05) * H))
                if x1 - x0 < 16 or y1 - y0 < 16:
                    continue
                dst = train if split == "train" else test
                if len(dst[ci]) < cap:
                    dst[ci].append(im.crop((x0, y0, x1, y1)).resize((224, 224)))
    return train, test


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


def encode(m, pre, imgs, texts):
    tok = open_clip.get_tokenizer("ViT-B-16")
    with torch.no_grad():
        tf = F.normalize(m.encode_text(tok(texts).to("cuda")), dim=-1)
        feats = []
        for i in range(0, len(imgs), 32):
            xs = torch.stack([pre(im) for im in imgs[i:i + 32]]).to("cuda")
            feats.append(F.normalize(m.encode_image(xs), dim=-1))
    return torch.cat(feats), tf


def kendall(a, b):
    num = den = 0.0
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            s1 = np.sign(a[i] - a[j])
            s2 = np.sign(b[i] - b[j])
            num += s1 * s2
            den += abs(s1 * s2)
    return num / den if den else 1.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    train, test = load_crops()
    train_pil, train_y = [], []
    test_pil, test_y = [], []
    for ci, items in train.items():
        for im in items:
            train_pil.append(im)
            train_y.append(ci)
    for ci, items in test.items():
        for im in items:
            test_pil.append(im)
            test_y.append(ci)
    train_y, test_y = np.array(train_y), np.array(test_y)
    texts = ["a photo of a " + c.replace("-", " ") for c in CLASSES]
    print(f"  crops: train {len(train_pil)}, test {len(test_pil)}, classes {len(CLASSES)}", flush=True)
    payload = {"protocol": "UATD-derived detection crops (riku1825, 11 classes), gap surgery as in a23_certificate_adapted",
               "n_train": len(train_pil), "n_test": len(test_pil), "classes": CLASSES, "models": {}}
    for tag in ("bioclip", "oceanclip"):
        m, pre = build_model(tag)
        ifeat, tfeat = encode(m, pre, test_pil, texts)
        mu_i, mu_t = ifeat.mean(0), tfeat.mean(0)
        d = mu_t - mu_i
        gn = float(d.norm().item())
        dh = d / gn
        base_scores = (F.normalize(ifeat, dim=-1) @ tfeat.T).float().cpu().numpy()
        rows = []
        for lam in LAMBDAS:
            x = F.normalize(ifeat + lam * gn * dh, dim=-1)
            sn = (x @ tfeat.T).float().cpu().numpy()
            top1 = float((sn.argmax(1) == test_y).mean() * 100)
            cg = float((tfeat.mean(0) - x.mean(0)).norm().item())
            taus = []
            for i in range(len(test_y)):
                top5 = np.argsort(-base_scores[i])[:5]
                taus.append(kendall(base_scores[i][top5], sn[i][top5]))
            r = np.arange(len(test_y))
            ts = sn[r, test_y]
            s2 = sn.copy()
            s2[r, test_y] = -1e9
            margin = ts - s2.max(1)
            rows.append({"lambda": lam, "top1": top1, "CG": cg, "tau": float(np.mean(taus)),
                         "mass_0.05": float((margin <= 0.1).mean())})
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
