# -*- coding: utf-8 -*-
r"""A23-P0-1 (the real thing): margin-mass certificate on the adapted marine encoders.

Uses the locally available BioCLIP base and OceanCLIP weights (open_clip ViT-B-16) on the same 67-class marine
subset and the same gap-surgery protocol as `tools/clip_ocean_gap_surgery.py`, and adds the margin mass
M(eps) = P(margin <= 2 eps) at eps in {0.02, 0.05, 0.1}. Reports (a) the correlation of CG and M with top-1 across
the surgery family, and (b) the transfer of an M-threshold fitted on one encoder to the other.

Output: outputs/analysis/a23_certificate_adapted.json

    conda run -n pytorch python tools/_p1352_a23_certificate_adapted.py --apply
    (or: D:\Anaconda\envs\pytorch\python.exe tools/_p1352_a23_certificate_adapted.py --apply)
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
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import open_clip
from datasets import load_dataset

LAMBDAS = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0]
EPS = [0.02, 0.05, 0.1]
OUT = "outputs/analysis/a23_certificate_adapted.json"


def load_subset():
    sub = json.load(io.open("outputs/ocean_subset.json", encoding="utf-8"))
    files = sorted(os.path.join("data/rare-species/data", f) for f in os.listdir("data/rare-species/data"))
    ds = load_dataset("parquet", data_files=files, split="train")
    idx = sub["subset_idx"]
    labels = []
    sci_of_row = {}
    for i in idx:
        sci_of_row[i] = ds[i]["sciName"]
        labels.append(ds[i]["sciName"])
    return ds, idx, labels, sub["classes"]


def images_of(ds, idx, batch=32):
    out = []
    for j in idx:
        b = ds[j]["file_name"]
        if isinstance(b, dict):
            im = Image.open(io.BytesIO(b["bytes"])) if b.get("bytes") else Image.open(b["path"])
        else:
            im = b
        out.append(im.convert("RGB"))
    return out


def build_model(tag):
    if tag == "bioclip":
        m, _, pre = open_clip.create_model_and_transforms(
            "ViT-B-16", pretrained="models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin", device="cuda")
    else:
        ck = torch.load("models/oceanclip-0.15b/oceanclip-bio/epoch_50.pt", map_location="cpu")
        m, _, pre = open_clip.create_model_and_transforms(
            "ViT-B-16", pretrained="models/oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin", device="cuda")
        m.load_state_dict(ck["state_dict"], strict=False)
    m.eval()
    return m, pre


def encode(m, pre, tag, imgs, texts):
    tok = open_clip.get_tokenizer("ViT-B-16")
    with torch.no_grad():
        tf = F.normalize(m.encode_text(tok(texts).to("cuda")), dim=-1)
        feats = []
        for i in range(0, len(imgs), 32):
            xs = torch.stack([pre(im) for im in imgs[i:i + 32]]).to("cuda")
            feats.append(F.normalize(m.encode_image(xs), dim=-1))
    return torch.cat(feats), tf


def metrics(n, ifeat, tfeat, labels, mu_i, mu_t):
    sn = (ifeat @ tfeat.T).float().cpu().numpy()
    pred = sn.argmax(1)
    top1 = float((pred == labels).mean() * 100)
    r = np.arange(len(labels))
    true_s = sn[r, labels]
    s = sn.copy()
    s[r, labels] = -1e9
    margin = true_s - s.max(1)
    cg = float((mu_t - ifeat.mean(0)).norm().item())
    row = {"lambda": n, "top1": top1, "CG": cg}
    for e in EPS:
        row["mass_%g" % e] = float((margin <= 2 * e).mean())
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ds, idx, sci_labels, classes = load_subset()
    labels = np.array([classes.index(s) for s in sci_labels])
    imgs = images_of(ds, idx)
    texts = ["a photo of a " + c for c in classes]
    print(f"  subset: {len(imgs)} images, {len(classes)} classes", flush=True)

    payload = {"protocol": "gap surgery on the 67-class marine subset; image-side translations, plus text-side at lambda=1",
               "eps": EPS, "lambdas": LAMBDAS, "n_images": len(imgs), "n_classes": len(classes), "models": {}}
    from scipy import stats as st
    embeddings = {}
    for tag in ("bioclip", "oceanclip"):
        m, pre = build_model(tag)
        ifeat, tfeat = encode(m, pre, tag, imgs, texts)
        mu_i, mu_t = ifeat.mean(0), tfeat.mean(0)
        d = mu_t - mu_i
        gn = float(d.norm().item())
        d_hat = d / gn
        rows = []
        for lam in LAMBDAS:
            x = F.normalize(ifeat + lam * gn * d_hat, dim=-1)
            rows.append(metrics(lam, x, tfeat, labels, mu_i, mu_t))
        # text-side surgery at lambda = 1 (mirrors the archive)
        tx = F.normalize(tfeat - 1.0 * gn * d_hat, dim=-1)
        rows.append(metrics("text1.0", ifeat, tx, labels, mu_i, mu_t))
        img_rows = [r for r in rows if isinstance(r["lambda"], (int, float))]
        top = np.array([r["top1"] for r in img_rows])
        cg = np.array([r["CG"] for r in img_rows])
        m05 = np.array([r["mass_0.05"] for r in img_rows])
        payload["models"][tag] = {
            "rows": rows,
            "r_CG": float(st.pearsonr(cg, top)[0]),
            "r_M005": float(st.pearsonr(m05, top)[0]) if np.std(m05) > 0 else None,
        }
        embeddings[tag] = {"mass": m05, "top": top}
        print(f"  [{tag}] top1 {top.min():.1f}-{top.max():.1f} | r(CG)={payload['models'][tag]['r_CG']:+.2f} "
              f"r(M0.05)={payload['models'][tag]['r_M005']}", flush=True)
        del m
        torch.cuda.empty_cache()

    # threshold transfer between the two adapted encoders
    def ba(pred, truth):
        tp = np.sum(pred & truth)
        tn = np.sum(~pred & ~truth)
        fp = np.sum(pred & ~truth)
        fn = np.sum(~pred & truth)
        return float(0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1)))

    transfer = {}
    for fit_tag in ("bioclip", "oceanclip"):
        m = embeddings[fit_tag]["mass"]
        h = embeddings[fit_tag]["top"] <= float(np.median(embeddings[fit_tag]["top"]))
        best = None
        for thr in np.linspace(m.min(), m.max(), 201):
            sc = ba(m <= thr, h)
            if best is None or sc > best[1]:
                best = (float(thr), float(sc))
        for test_tag in ("bioclip", "oceanclip"):
            if test_tag == fit_tag:
                continue
            mt = embeddings[test_tag]["mass"]
            ht = embeddings[test_tag]["top"] <= float(np.median(embeddings[test_tag]["top"]))
            transfer[f"{fit_tag}->{test_tag}"] = {"threshold": best[0], "fit_BA": best[1],
                                                  "test_BA": ba(mt <= best[0], ht)}
    payload["threshold_transfer"] = transfer
    print("  transfer:", json.dumps(transfer))
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("  wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
