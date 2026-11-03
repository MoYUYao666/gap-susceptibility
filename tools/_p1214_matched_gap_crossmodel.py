# -*- coding: utf-8 -*-
r"""Cross-model replication of the matched-gap control (OpenCLIP, SigLIP) on the same 5k images.

The CLIP result (two probe points with gaps agreeing to 0.03 differ by 32.7 accuracy points) is only a property of the
method if it replicates. This runs the same translation sweep and contraction family on the other two checkpoints that
are available locally, using get_image_features / get_text_features so one code path covers both architectures.

    python tools/_p1214_matched_gap_crossmodel.py [--apply]
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
OUT = os.path.join(REPO, "outputs", "analysis", "a1_matched_gap_crossmodel.json")
TEMPLATE = "a photo of a {}"
LAMBDAS = [-2, -1, -0.5, 0.25, 0.5, 1, 2, 4]
ALPHAS = [0.1, 0.25, 0.5]
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
    names = [n.split(",")[0].strip() for n in ds.features["label"].names]
    if len(names) == 1001:
        names = names[:1000]
    rs = np.random.RandomState(42)
    idx = rs.choice(len(ds), size=min(N, len(ds)), replace=False)
    sub = ds.select(idx.tolist())
    labels = np.asarray(sub["label"])
    pil = [im.convert("RGB") for im in sub["image"]]
    print(f"  images={len(pil)} classes={len(names)}", flush=True)

    out = {"benchmark": "imagenet5k", "n_images": len(pil), "n_classes": len(names), "models": {}}
    if os.path.exists(OUT):
        try:
            prev = json.load(io.open(OUT, encoding="utf-8"))
            out["models"] = prev.get("models", {})
            print(f"  merging into existing archive ({len(out['models'])} models)", flush=True)
        except Exception:
            pass
    for tag, path in (("openclip", "models/openclip"), ("siglip", "models/siglip-base-patch16-224")):
        local = os.path.join(REPO, path)
        if not os.path.isdir(local):
            print(f"  {tag}: missing {local}", flush=True)
            continue
        try:
            model = AutoModel.from_pretrained(local, local_files_only=True).to(device).eval()
            proc = AutoProcessor.from_pretrained(local, local_files_only=True)
        except Exception as e:
            print(f"  {tag}: load failed {type(e).__name__}: {str(e)[:120]}", flush=True)
            continue
        try:
            has_vproj = hasattr(model, "visual_projection")
            has_tproj = hasattr(model, "text_projection")
            feats = []
            with torch.no_grad():
                for i in range(0, len(pil), 64):
                    inp = proc(images=pil[i:i + 64], return_tensors="pt").to(device)
                    v = model.vision_model(**inp)
                    pooled = v[1] if isinstance(v, tuple) else v.pooler_output
                    emb = model.visual_projection(pooled) if has_vproj else pooled
                    feats.append(F.normalize(emb.float(), dim=-1))
            base = torch.cat(feats)
            tf = []
            with torch.no_grad():
                for i in range(0, len(names), 256):
                    kw = (dict(padding="max_length", truncation=True, max_length=64)
                          if "Siglip" in type(model).__name__ else dict(padding=True))
                    ti = proc(text=[TEMPLATE.format(c.replace("_", " ")) for c in names[i:i + 256]],
                              return_tensors="pt", **kw).to(device)
                    o = model.text_model(**ti)
                    pooled = o[1] if isinstance(o, tuple) else o.pooler_output
                    emb = model.text_projection(pooled) if has_tproj else pooled
                    tf.append(F.normalize(emb.float(), dim=-1))
            tf = torch.cat(tf)
            if tf.shape[0] > len(names):
                tf = tf[:len(names)]
        except Exception as e:
            print(f"  {tag}: inference failed {type(e).__name__}: {str(e)[:160]}", flush=True)
            continue

        mu_i, mu_t = base.mean(0), tf.mean(0)
        gap_vec = mu_t - mu_i
        gap_norm = float(gap_vec.norm().item())
        d_hat = gap_vec / gap_norm
        base_np = (base @ tf.T).float().cpu().numpy()
        frozen_top1 = float((base_np.argmax(1) == labels).mean() * 100)
        idx5 = np.argsort(-base_np, axis=1)[:, :5]
        print(f"\n  {tag}: frozen CG={gap_norm:.4f} top1={frozen_top1:.2f}", flush=True)

        def measure(x):
            cg = float((mu_t - x.mean(0)).norm().item())
            sn = (x @ tf.T).float().cpu().numpy()
            return cg, float((sn.argmax(1) == labels).mean() * 100), sn

        rows = []
        for lam in LAMBDAS:
            x = F.normalize(base + lam * gap_norm * d_hat, dim=-1)
            cg, t1, _ = measure(x)
            rows.append({"family": "T", "param": lam, "CG": cg, "top1": t1})
        cls_ids = sorted(set(labels.tolist()))
        cents = F.normalize(torch.stack([base[labels == c].mean(0) for c in cls_ids]), dim=-1)
        lab_map = {c: i for i, c in enumerate(cls_ids)}
        c_own = cents[torch.tensor([lab_map[int(z)] for z in labels], device=device)]
        for al in ALPHAS:
            x = F.normalize((1 - al) * base + al * c_own, dim=-1)
            cg, t1, _ = measure(x)
            rows.append({"family": "P", "param": al, "CG": cg, "top1": t1})
        for r in rows:
            print(f"   {r['family']} {r['param']:>5}: CG={r['CG']:.4f} top1={r['top1']:6.2f}", flush=True)

        best = None
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                if abs(rows[i]["CG"] - rows[j]["CG"]) <= 0.03:
                    sp = abs(rows[i]["top1"] - rows[j]["top1"])
                    if best is None or sp > best["spread"]:
                        best = {"dCG": abs(rows[i]["CG"] - rows[j]["CG"]),
                                "a": rows[i], "b": rows[j], "spread": sp}
        print(f"  {tag}: max matched-gap spread (|dCG|<=0.03) = {best['spread']:.1f} points", flush=True)
        out["models"][tag] = {"frozen": {"CG": gap_norm, "top1": frozen_top1},
                              "rows": rows, "max_matched_gap_spread": best}
        del model, base, tf
        torch.cuda.empty_cache()

    if a.apply and out["models"]:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("\n  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
