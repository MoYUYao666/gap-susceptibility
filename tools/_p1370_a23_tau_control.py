# -*- coding: utf-8 -*-
r"""A23: order-preservation (tau) positive control on the adapted marine encoders.

Same gap-surgery protocol and embeddings as `_p1352`, but the per-configuration statistics now include the measured
order-preservation tau (mean over images of the Kendall correlation between the baseline top-5 class-score vector and the
surgery top-5 vector). This is the diagnostic the paper actually advocates; margin mass and the centroid gap are the
controls that failed.

Output: outputs/analysis/a23_tau_control.json

    conda run -n pytorch python tools/_p1370_a23_tau_control.py --apply
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
from datasets import load_dataset
from scipy import stats as st

LAMBDAS = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0]
EPS = [0.05, 0.1]
OUT = "outputs/analysis/a23_tau_control.json"


def load_subset():
    sub = json.load(io.open("outputs/ocean_subset.json", encoding="utf-8"))
    files = sorted(os.path.join("data/rare-species/data", f) for f in os.listdir("data/rare-species/data"))
    ds = load_dataset("parquet", data_files=files, split="train")
    idx = sub["subset_idx"]
    labels = np.array([sub["classes"].index(ds[i]["sciName"]) for i in idx])
    return ds, idx, labels, sub["classes"]


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


def kendall_vectors(a, b):
    """Kendall tau-b between two score vectors."""
    n = len(a)
    num = 0.0
    den = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            s1 = np.sign(a[i] - a[j])
            s2 = np.sign(b[i] - b[j])
            num += s1 * s2
            den += abs(s1 * s2)
    return num / den if den else 1.0


def metrics(lam, ifeat, tfeat, labels, base_scores):
    sn = (ifeat @ tfeat.T).float().cpu().numpy()
    top1 = float((sn.argmax(1) == labels).mean() * 100)
    r = np.arange(len(labels))
    ts = sn[r, labels]
    s2 = sn.copy()
    s2[r, labels] = -1e9
    margin = ts - s2.max(1)
    cg = float((tfeat.mean(0) - ifeat.mean(0)).norm().item())
    # order preservation: per image, Kendall tau of the baseline top-5 class scores vs the surgery scores
    taus = []
    for i in range(len(labels)):
        top5 = np.argsort(-base_scores[i])[:5]
        taus.append(kendall_vectors(base_scores[i][top5], sn[i][top5]))
    row = {"lambda": lam, "top1": top1, "CG": cg, "tau": float(np.mean(taus))}
    for e in EPS:
        row["mass_%g" % e] = float((margin <= 2 * e).mean())
    return row, sn


def ba(pred, truth):
    tp = np.sum(pred & truth)
    tn = np.sum(~pred & ~truth)
    fp = np.sum(pred & ~truth)
    fn = np.sum(~pred & truth)
    return float(0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ds, idx, labels, classes = load_subset()
    imgs = []
    for i in idx:
        b = ds[i]["file_name"]
        im = Image.open(io.BytesIO(b["bytes"])) if isinstance(b, dict) and b.get("bytes") else (
            Image.open(b["path"]) if isinstance(b, dict) else b)
        imgs.append(im.convert("RGB"))
    texts = ["a photo of a " + c for c in classes]
    payload = {"protocol": "same gap-surgery family as a23_certificate_adapted; tau = per-image Kendall of the baseline "
                          "top-5 scores vs the surgery top-5 scores, averaged over images",
               "n_images": len(imgs), "models": {}}
    cached = {}
    for tag in ("bioclip", "oceanclip"):
        m, pre = build_model(tag)
        ifeat, tfeat = encode(m, pre, imgs, texts)
        mu_i, mu_t = ifeat.mean(0), tfeat.mean(0)
        d = mu_t - mu_i
        gn = float(d.norm().item())
        dh = d / gn
        base, _ = metrics(0.0, F.normalize(ifeat + 0.0 * gn * dh, dim=-1), tfeat, labels,
                          (F.normalize(ifeat + 0.0 * gn * dh, dim=-1) @ tfeat.T).float().cpu().numpy())
        base_scores = (F.normalize(ifeat, dim=-1) @ tfeat.T).float().cpu().numpy()
        rows = []
        for lam in LAMBDAS:
            x = F.normalize(ifeat + lam * gn * dh, dim=-1)
            row, _ = metrics(lam, x, tfeat, labels, base_scores)
            rows.append(row)
        img_rows = [r for r in rows if r["lambda"] <= 2.0]
        top = np.array([r["top1"] for r in img_rows])
        tau = np.array([r["tau"] for r in img_rows])
        mass = np.array([r["mass_0.05"] for r in img_rows])
        cg = np.array([r["CG"] for r in img_rows])
        payload["models"][tag] = {
            "rows": rows,
            "r_tau": float(st.pearsonr(tau, top)[0]),
            "r_mass": float(st.pearsonr(mass, top)[0]),
            "r_cg": float(st.pearsonr(cg, top)[0]),
        }
        cached[tag] = {"tau": tau, "mass": mass, "top": top}
        print(f"  [{tag}] top1 {top.min():.1f}-{top.max():.1f} | r(tau)={payload['models'][tag]['r_tau']:+.2f} "
              f"r(mass)={payload['models'][tag]['r_mass']:+.2f} r(CG)={payload['models'][tag]['r_cg']:+.2f}", flush=True)
        del m
        torch.cuda.empty_cache()
    # threshold transfer between the two encoders, tau (higher is better) vs mass (lower is better)
    transfer = {}
    for stat in ("tau", "mass"):
        for fit_tag in ("bioclip", "oceanclip"):
            vals = cached[fit_tag][stat]
            h = cached[fit_tag]["top"] <= float(np.median(cached[fit_tag]["top"]))
            best = None
            for thr in np.linspace(vals.min(), vals.max(), 201):
                pred = (vals <= thr) if stat == "mass" else (vals >= thr)
                sc = ba(pred, h)
                if best is None or sc > best[1]:
                    best = (float(thr), float(sc))
            for test_tag in ("bioclip", "oceanclip"):
                if test_tag == fit_tag:
                    continue
                vt = cached[test_tag][stat]
                ht = cached[test_tag]["top"] <= float(np.median(cached[test_tag]["top"]))
                pred = (vt <= best[0]) if stat == "mass" else (vt >= best[0])
                transfer[f"{stat}|{fit_tag}->{test_tag}"] = {"fit_BA": best[1], "test_BA": ba(pred, ht)}
    payload["threshold_transfer"] = transfer
    print("  transfer:", json.dumps(transfer))
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("  wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
