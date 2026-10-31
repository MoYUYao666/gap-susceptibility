# -*- coding: utf-8 -*-
"""Diagnose the SigLIP zero-shot path: shapes, normalisation, and the effect of max-length text padding."""
import glob
import os

import numpy as np
import torch
import torch.nn.functional as F

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
device = "cuda" if torch.cuda.is_available() else "cpu"

from transformers import AutoModel, AutoProcessor
from datasets import Dataset

local = os.path.join(REPO, "models", "siglip-base-patch16-224")
model = AutoModel.from_pretrained(local, local_files_only=True).to(device).eval()
proc = AutoProcessor.from_pretrained(local, local_files_only=True)
print("  model:", type(model).__name__)
print("  logit_scale:", getattr(model, "logit_scale", None), " logit_bias:", getattr(model, "logit_bias", None))

parq = sorted(glob.glob(os.path.join(REPO, "data", "imagenet_hf", "*.parquet")))
ds = Dataset.from_parquet(parq)
names = [n.split(",")[0].strip() for n in ds.features["label"].names][:1000]
rs = np.random.RandomState(42)
idx = rs.choice(len(ds), size=500, replace=False)
sub = ds.select(idx.tolist())
labels = np.asarray(sub["label"])
pil = [im.convert("RGB") for im in sub["image"]]
texts = [f"a photo of a {c.replace('_', ' ')}" for c in names]

with torch.no_grad():
    inp = proc(images=pil, return_tensors="pt").to(device)
    v = model.vision_model(**inp)
    pooled = v[1] if isinstance(v, tuple) else v.pooler_output
    print("  vision pooled shape:", tuple(pooled.shape), "dtype", pooled.dtype)
    img = F.normalize(pooled.float(), dim=-1)

    for mode in ("longest", "max_length"):
        kw = dict(padding="max_length", truncation=True, max_length=64) if mode == "max_length" else dict(padding=True)
        ti = proc(text=texts, return_tensors="pt", **kw).to(device)
        o = model.text_model(**ti)
        tp = o[1] if isinstance(o, tuple) else o.pooler_output
        txt = F.normalize(tp.float(), dim=-1)
        S = img @ txt.T
        top1 = float((S.argmax(1).cpu().numpy() == labels).mean() * 100)
        print(f"  padding={mode:<10} text shape={tuple(tp.shape)} | top-1 on 500 = {top1:.2f}%")

    # also try the model's own feature helpers
    try:
        fi = model.get_image_features(**inp)
        ft = model.get_text_features(**ti)
        print("  get_features types:", type(fi).__name__, type(ft).__name__)
        if torch.is_tensor(fi):
            S2 = F.normalize(fi.float(), dim=-1) @ F.normalize(ft.float(), dim=-1).T
            print("  helper top-1 =", float((S2.argmax(1).cpu().numpy() == labels).mean() * 100))
    except Exception as e:
        print("  helpers failed:", type(e).__name__, str(e)[:140])
