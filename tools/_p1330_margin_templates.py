# -*- coding: utf-8 -*-
r"""P0-2: is the margin-mass certificate robust to the text side?

For five backbones and ten prompt templates on the fixed ImageNet-5k holdout, compute top-1, the centroid gap, and the
margin mass M(0.01)/M(0.02). The comparison with the earlier prompt-template archive (which stored CG and tau) shows
whether the certificate moves less than the first-moment statistic when only the template changes.

Memory discipline: one backbone is loaded at a time; embeddings are released before the next backbone; the image set is a
5,000-image subset.

Output: outputs/analysis/a1_margin_templates.json

    python tools/_p1330_margin_templates.py [--apply]
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
OUT = os.path.join(REPO, "outputs", "analysis", "a1_margin_templates.json")
TEMPLATES = [
    "a photo of a {}.", "a photo of the {}.", "a bad photo of a {}.", "a cropped photo of a {}.",
    "a close-up photo of a {}.", "a bright photo of a {}.", "a photo of one {}.", "a pixelated photo of a {}.",
    "an image of a {}.", "{}",
]
MODELS = {"clip32": "models/clip-vit-base-patch32", "clip16": "models/clip-vit-base-patch16",
          "openclip": "models/openclip", "siglip": "models/siglip-base-patch16-224",
          "vitl": "models/clip-vit-large-patch14"}
EPS = [0.01, 0.02]
N = 5000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(0)
    np.random.seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import AutoModel, AutoProcessor
    from datasets import Dataset

    parq = sorted(glob.glob(os.path.join(REPO, "data", "imagenet_hf", "*.parquet")))
    ds = Dataset.from_parquet(parq)
    names = [x.split(",")[0].strip() for x in ds.features["label"].names]
    if len(names) == 1001:
        names = names[:1000]
    rs = np.random.RandomState(42)
    idx = rs.choice(len(ds), size=min(N, len(ds)), replace=False)
    sub = ds.select(idx.tolist())
    labels = np.asarray(sub["label"])
    pil = [im.convert("RGB") for im in sub["image"]]
    print(f"  eval images={len(pil)} classes={len(names)}", flush=True)

    payload = {"benchmark": "imagenet5k", "n_images": len(pil), "templates": TEMPLATES,
               "eps": EPS, "models": {}}
    if os.path.exists(OUT):
        try:
            payload["models"] = json.load(io.open(OUT, encoding="utf-8")).get("models", {})
        except Exception:
            pass

    for tag, rel in MODELS.items():
        if not os.path.isdir(os.path.join(REPO, rel)):
            print(f"  {tag}: missing", flush=True)
            continue
        if tag in payload["models"]:
            print(f"  {tag}: archived", flush=True)
            continue
        model = AutoModel.from_pretrained(os.path.join(REPO, rel), local_files_only=True)
        model = model.to(device).eval()
        proc = AutoProcessor.from_pretrained(os.path.join(REPO, rel), local_files_only=True)
        has_vproj, has_tproj = hasattr(model, "visual_projection"), hasattr(model, "text_projection")
        is_siglip = type(model).__name__.lower().startswith("siglip")
        feats = []
        with torch.no_grad():
            for i in range(0, len(pil), 32):
                inp = proc(images=pil[i:i + 32], return_tensors="pt").to(device)
                v = model.vision_model(**inp)
                pooled = v[1] if isinstance(v, tuple) else v.pooler_output
                feats.append(F.normalize((model.visual_projection(pooled) if has_vproj else pooled).float(), dim=-1))
        img = torch.cat(feats)
        rows = []
        for t_i, tpl in enumerate(TEMPLATES):
            texts = [tpl.format(c.replace("_", " ")) for c in names]
            tf = []
            with torch.no_grad():
                for i in range(0, len(texts), 128):
                    kw = dict(padding="max_length", truncation=True, max_length=64) if is_siglip else dict(padding=True)
                    ti = proc(text=texts[i:i + 128], return_tensors="pt", **kw).to(device)
                    o = model.text_model(**ti)
                    pooled = o[1] if isinstance(o, tuple) else o.pooler_output
                    tf.append(F.normalize((model.text_projection(pooled) if has_tproj else pooled).float(), dim=-1))
            tf = torch.cat(tf)[:len(names)]
            sn = (img @ tf.T).float().cpu().numpy()
            pred = sn.argmax(1)
            top1 = float((pred == labels).mean() * 100)
            rows_ = np.arange(len(labels))
            true_s = sn[rows_, labels]
            s = sn.copy()
            s[rows_, labels] = -1e9
            margin = true_s - s.max(1)
            mu_i, mu_t = img.mean(0), tf.mean(0)
            entry = {"template": tpl, "top1": top1, "CG": float((mu_t - mu_i).norm().item())}
            for e in EPS:
                entry["mass_%g" % e] = float((margin <= 2 * e).mean())
            rows.append(entry)
            print(f"   [{tag}] t{t_i} top1={top1:.2f} CG={entry['CG']:.4f} M01={entry['mass_0.01']:.3f}", flush=True)
        payload["models"][tag] = {"rows": rows}
        if a.apply:
            io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        del model, img, feats
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(f"  [{tag}] done and released", flush=True)
    if a.apply:
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
