# -*- coding: utf-8 -*-
r"""A23: how large must the evaluation set be for the order-preservation diagnostic?

Recomputes the marine-subset embeddings once, then repeats the gap-surgery measurement on stratified evaluation subsets of
n in {32, 64, 128, 256, all} images and records how the tau-accuracy and gap-accuracy relations behave.

Output: outputs/analysis/a23_neval_sensitivity.json

    conda run -n pytorch python tools/_p1415_a23_neval.py --apply
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
from datasets import load_dataset
from scipy import stats as st

OUT = "outputs/analysis/a23_neval_sensitivity.json"
LAMBDAS = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0]
NS = [67, 134, 268, 536, None]  # 1/2/4/8 stratified images per class on the 67-class set


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sub = json.load(io.open("outputs/ocean_subset.json", encoding="utf-8"))
    files = sorted(os.path.join("data/rare-species/data", f) for f in os.listdir("data/rare-species/data"))
    ds = load_dataset("parquet", data_files=files, split="train")
    idx = sub["subset_idx"]
    classes = sub["classes"]
    labels = np.array([classes.index(ds[i]["sciName"]) for i in idx])
    pil = []
    for i in idx:
        b = ds[i]["file_name"]
        im = Image.open(io.BytesIO(b["bytes"])) if isinstance(b, dict) and b.get("bytes") else (
            Image.open(b["path"]) if isinstance(b, dict) else b)
        pil.append(im.convert("RGB"))
    texts = ["a photo of a " + c for c in classes]
    payload = {"n_classes": len(classes), "n_total": len(pil), "lambdas": LAMBDAS, "models": {}}
    rs = np.random.RandomState(42)
    # stratified subsample indices by class
    by_class = collections.defaultdict(list)
    for i, y in enumerate(labels):
        by_class[int(y)].append(i)
    for tag in ("bioclip", "oceanclip"):
        m, pre = build_model(tag)
        tok = open_clip.get_tokenizer("ViT-B-16")
        with torch.no_grad():
            tfeat = F.normalize(m.encode_text(tok(texts).to("cuda")), dim=-1)
            feats = []
            for i in range(0, len(pil), 32):
                xs = torch.stack([pre(im) for im in pil[i:i + 32]]).to("cuda")
                feats.append(F.normalize(m.encode_image(xs), dim=-1))
        ifeat = torch.cat(feats)
        mu_i, mu_t = ifeat.mean(0), tfeat.mean(0)
        d = mu_t - mu_i
        gn = float(d.norm().item())
        dh = d / gn
        base_scores = (F.normalize(ifeat, dim=-1) @ tfeat.T).float().cpu().numpy()
        result = {}
        for n in NS:
            if n is None:
                sel = np.arange(len(labels))
            else:
                per = max(1, n // len(classes))
                sel = []
                for ci in sorted(by_class):
                    v = by_class[ci]
                    pick = rs.choice(len(v), min(per, len(v)), replace=False)
                    sel.extend(v[j] for j in pick)
                sel = np.array(sel)
            img_sel = ifeat[sel]
            lab_sel = labels[sel]
            top, cg, tau = [], [], []
            for lam in LAMBDAS:
                x = F.normalize(img_sel + lam * gn * dh, dim=-1)
                sn = (x @ tfeat.T).float().cpu().numpy()
                top.append(float((sn.argmax(1) == lab_sel).mean() * 100))
                cg.append(float((tfeat.mean(0) - x.mean(0)).norm().item()))
                taus = []
                for i in range(len(lab_sel)):
                    top5 = np.argsort(-base_scores[sel[i]])[:5]
                    taus.append(kendall(base_scores[sel[i]][top5], sn[i][top5]))
                tau.append(float(np.mean(taus)))
            result[str(n)] = {"n_eval": int(len(sel)),
                              "r_tau": float(st.pearsonr(tau, top)[0]),
                              "r_CG": float(st.pearsonr(cg, top)[0]),
                              "top1_range": [float(min(top)), float(max(top))]}
        payload["models"][tag] = result
        print(f"  [{tag}]", {k: round(v["r_tau"], 2) for k, v in result.items()}, flush=True)
        del m
        torch.cuda.empty_cache()
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("  wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
