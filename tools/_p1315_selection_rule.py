# -*- coding: utf-8 -*-
r"""Item 4: margin mass as a selection rule.

Candidate sets:
  (a) the 17 synthetic configurations of the showdown archive (classification), where selecting by min M(eps) can be
      compared with selecting by min CG and with the labelled oracle;
  (b) five backbones x ten prompt templates: for each backbone, a practitioner must choose a template without labels.
      We compute per-template margins and top-1, then compare four rules: oracle, min M(0.01), min M(0.02), and the
      default (first template), reporting the selected top-1 and the regret against the oracle.

Outputs: outputs/analysis/a1_selection_rule.json
    python tools/_p1315_selection_rule.py [--apply]
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
OUT = os.path.join(REPO, "outputs", "analysis", "a1_selection_rule.json")
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

    out = {"eps": EPS, "selection": {}}

    # ---- (a) synthetic configurations from the showdown archive
    sd = json.load(io.open(os.path.join(REPO, "outputs/analysis/a1_statistic_showdown.json"), encoding="utf-8"))
    rows = sd["scenarios"]["classification"]
    top1 = np.array([r["top1"] for r in rows])
    cg = np.array([r["CG"] for r in rows])
    m1 = np.array([r["mass_0.01"] for r in rows])
    o = int(np.argmax(top1))
    rules_a = {"oracle": o, "min_CG": int(np.argmin(cg)), "min_M(0.01)": int(np.argmin(m1))}
    out["selection"]["synthetic_configs"] = {
        "n": len(rows),
        "oracle_top1": float(top1[o]),
        "rules": {k: {"index": int(i), "top1": float(top1[i]), "regret": float(top1[o] - top1[i])}
                  for k, i in rules_a.items()},
    }
    print("  synthetic configs:", {k: round(float(top1[i]), 1) for k, i in rules_a.items()})

    # ---- (b) prompt-template selection on five backbones
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
    out["selection"]["templates"] = {}
    for tag, rel in MODELS.items():
        if not os.path.isdir(os.path.join(REPO, rel)):
            continue
        model = AutoModel.from_pretrained(os.path.join(REPO, rel), local_files_only=True).to(device).eval()
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
        base = torch.cat(feats)
        per = []
        for t_i, tpl in enumerate(TEMPLATES):
            texts = [tpl.format(c.replace("_", " ")) for c in names]
            tf = []
            with torch.no_grad():
                for i in range(0, len(texts), 128):
                    kw = dict(padding="max_length", truncation=True, max_length=64) if is_siglip else dict(padding=True)
                    ti = proc(text=texts[i:i + 128], return_tensors="pt", **kw).to(device)
                    o2 = model.text_model(**ti)
                    pooled = o2[1] if isinstance(o2, tuple) else o2.pooler_output
                    tf.append(F.normalize((model.text_projection(pooled) if has_tproj else pooled).float(), dim=-1))
            tf = torch.cat(tf)[:len(names)]
            sn = (base @ tf.T).float().cpu().numpy()
            pred = sn.argmax(1)
            true_s = sn[np.arange(len(pred)), labels]
            s = sn.copy()
            s[np.arange(len(pred)), labels] = -1e9
            margin = true_s - s.max(1)
            entry = {"template": tpl, "top1": float((pred == labels).mean() * 100)}
            for e in EPS:
                entry["mass_%g" % e] = float((margin <= 2 * e).mean())
            per.append(entry)
        tops = np.array([p["top1"] for p in per])
        o = int(np.argmax(tops))
        rules = {"oracle": o, "default_template": 0}
        for e in EPS:
            key = "mass_%g" % e
            vals = np.array([p[key] for p in per])
            if np.std(vals) > 1e-12:
                rules["min_%s" % key] = int(np.argmin(vals))
        ranked = [p["mass_0.01"] for p in per]
        from scipy import stats as st
        rho = float(st.spearmanr(ranked, tops)[0]) if len(set(ranked)) > 1 else None
        out["selection"]["templates"][tag] = {
            "rows": per, "oracle_top1": float(tops[o]), "spearman_mass_top1": rho,
            "rules": {k: {"index": int(i), "top1": float(tops[i]), "regret": float(tops[o] - tops[i])}
                      for k, i in rules.items()},
        }
        print(f"  [{tag}] oracle {tops[o]:.1f} | " +
              " ".join(f"{k}={tops[i]:.1f}" for k, i in rules.items()) + f" | rho={rho}")
        if a.apply:
            io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
    if a.apply:
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
