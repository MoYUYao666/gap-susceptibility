# -*- coding: utf-8 -*-
r"""Realistic text-side intervention: change only the prompt template and watch the gap move while accuracy stays.

Proposition 1 of the manuscript says a common translation of the text embeddings preserves every row ordering (hence
top-1 and tau) while moving the centroid gap arbitrarily. Prompt engineering is the one intervention that does exactly
that in practice: it changes the text embeddings, not the images. This script measures it.

For each backbone it computes, on the same 5,000 ImageNet-5k images:
  * image embeddings once;
  * text embeddings per template (ten standard CLIP prompts);
  * per template: centroid gap, zero-shot top-1, tau with k = 5 and k = 10 (Kendall against the reference template's
    top-k sets), and full-ranking Spearman;
  * a bootstrap over images for the top-1 confidence interval of each template.

Deliverables feed item 1 (realistic non-sufficiency) and item 4 (how small k must be) of the novelty plan.

    python tools/_p1263_prompt_template_control.py [--backbones clip32 clip16 openclip siglip vitl] [--apply]
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
OUT = os.path.join(REPO, "outputs", "analysis", "a1_prompt_template_gap.json")
N = 5000

TEMPLATES = [
    "a photo of a {}.",
    "a photo of the {}.",
    "a bad photo of a {}.",
    "a cropped photo of a {}.",
    "a close-up photo of a {}.",
    "a bright photo of a {}.",
    "a photo of one {}.",
    "a pixelated photo of a {}.",
    "an image of a {}.",
    "{}",
]
REFERENCE = 0

BACKBONES = {
    "clip32": "models/clip-vit-base-patch32",
    "clip16": "models/clip-vit-base-patch16",
    "openclip": "models/openclip",
    "siglip": "models/siglip-base-patch16-224",
    "vitl": "models/clip-vit-large-patch14",
}


def load_images():
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
    return pil, labels, names


def embed_image(model, proc, pil, device, batch=64):
    has_vproj = hasattr(model, "visual_projection")
    feats = []
    with torch.no_grad():
        for i in range(0, len(pil), batch):
            inp = proc(images=pil[i:i + batch], return_tensors="pt").to(device)
            v = model.vision_model(**inp)
            pooled = v[1] if isinstance(v, tuple) else v.pooler_output
            emb = model.visual_projection(pooled) if has_vproj else pooled
            feats.append(F.normalize(emb.float(), dim=-1))
    return torch.cat(feats)


def embed_text(model, proc, texts, device):
    has_tproj = hasattr(model, "text_projection")
    is_siglip = type(model).__name__.lower().startswith("siglip")
    feats = []
    with torch.no_grad():
        for i in range(0, len(texts), 128):
            kw = dict(padding="max_length", truncation=True, max_length=64) if is_siglip else dict(padding=True)
            ti = proc(text=texts[i:i + 128], return_tensors="pt", **kw).to(device)
            o = model.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            emb = model.text_projection(pooled) if has_tproj else pooled
            feats.append(F.normalize(emb.float(), dim=-1))
    return torch.cat(feats)[:len(texts)]


def kendall_topk(base_np, cur_np, k):
    from scipy import stats
    idx = np.argsort(-base_np, axis=1)[:, :k]
    taus = []
    for i in range(len(base_np)):
        r1, r2 = base_np[i][idx[i]], cur_np[i][idx[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    return float(np.mean(taus)) if taus else None


def spearman_full(base_np, cur_np, n_rows=2000):
    from scipy import stats
    rs = []
    for i in range(min(n_rows, len(base_np))):
        r1, r2 = base_np[i], cur_np[i]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        r, _ = stats.spearmanr(r1, r2)
        if np.isfinite(r):
            rs.append(r)
    return float(np.mean(rs)) if rs else None


def bootstrap_top1(correct: np.ndarray, n_boot=500, seed=0):
    rs = np.random.RandomState(seed)
    means = [correct[rs.randint(0, len(correct), len(correct))].mean() for _ in range(n_boot)]
    return [float(np.percentile(means, 2.5) * 100), float(np.percentile(means, 97.5) * 100)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbones", nargs="+", default=["clip32", "openclip", "siglip", "vitl"])
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    torch.manual_seed(0)
    np.random.seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import AutoModel, AutoProcessor

    pil, labels, names = load_images()
    print(f"  images={len(pil)} classes={len(names)} device={device}", flush=True)

    payload = {"benchmark": "imagenet5k", "n_images": len(pil), "n_classes": len(names),
               "templates": TEMPLATES, "reference_template": TEMPLATES[REFERENCE], "models": {}}
    if os.path.exists(OUT):
        try:
            payload["models"] = json.load(io.open(OUT, encoding="utf-8")).get("models", {})
        except Exception:
            pass

    for tag in a.backbones:
        local = os.path.join(REPO, BACKBONES.get(tag, ""))
        if not BACKBONES.get(tag) or not os.path.isdir(local):
            print(f"  {tag}: missing {local}", flush=True)
            continue
        if tag in payload["models"]:
            print(f"  {tag}: already archived, skipping", flush=True)
            continue
        try:
            model = AutoModel.from_pretrained(local, local_files_only=True).to(device).eval()
            proc = AutoProcessor.from_pretrained(local, local_files_only=True)
        except Exception as e:
            print(f"  {tag}: load failed {type(e).__name__}: {str(e)[:160]}", flush=True)
            continue
        img = embed_image(model, proc, pil, device)
        rows = []
        base_np = None
        for t_i, tpl in enumerate(TEMPLATES):
            texts = [tpl.format(c.replace("_", " ")) for c in names]
            tf = embed_text(model, proc, texts, device)
            mu_i, mu_t = img.mean(0), tf.mean(0)
            cg = float((mu_t - mu_i).norm().item())
            sn = (img @ tf.T).float().cpu().numpy()
            correct = (sn.argmax(1) == labels)
            top1 = float(correct.mean() * 100)
            if t_i == REFERENCE:
                base_np = sn
                row = {"template": tpl, "CG": cg, "top1": top1, "tau5": 1.0, "tau10": 1.0,
                       "spearman_full": 1.0, "top1_ci95": bootstrap_top1(correct)}
            else:
                row = {"template": tpl, "CG": cg, "top1": top1,
                       "tau5": kendall_topk(base_np, sn, 5),
                       "tau10": kendall_topk(base_np, sn, 10),
                       "spearman_full": spearman_full(base_np, sn),
                       "top1_ci95": bootstrap_top1(correct)}
            rows.append(row)
            print(f"   [{tag}] {tpl[:28]:<30} CG={cg:.4f} top1={top1:.2f} tau5={row['tau5']:.3f} "
                  f"tau10={row['tau10']:.3f}", flush=True)
        cgs = np.array([r["CG"] for r in rows])
        t1 = np.array([r["top1"] for r in rows])
        i_min, i_max = int(np.argmin(cgs)), int(np.argmax(cgs))
        payload["models"][tag] = {
            "rows": rows,
            "cg_range": [float(cgs.min()), float(cgs.max())],
            "cg_spread": float(cgs.max() - cgs.min()),
            "top1_at_min_cg": float(t1[i_min]),
            "top1_at_max_cg": float(t1[i_max]),
            "top1_spread": float(abs(t1[i_min] - t1[i_max])),
            "top1_min": float(t1.min()), "top1_max": float(t1.max()),
            "n_templates": len(rows),
        }
        print(f"  [{tag}] CG spread={cgs.max()-cgs.min():.4f} | top-1 spread={abs(t1[i_min]-t1[i_max]):.2f} "
              f"| all top-1 range={t1.max()-t1.min():.2f}", flush=True)
        if a.apply:
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
            print("  wrote", os.path.relpath(OUT, REPO), flush=True)

    if not a.apply:
        print("  (dry run)")
        return 0
    print("  done:", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
