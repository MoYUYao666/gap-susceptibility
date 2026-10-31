# -*- coding: utf-8 -*-
r"""A1: early-stopping baselines for the interior-optimum validation.

Adds common confidence-based signals to the monitoring comparison, so the certificate can be compared with
entropy / max-softmax / max-logit / logsumexp-energy selection, and adds a third held-out dataset (fathomnet8).

Output: outputs/analysis/a1_stopping_baselines.json

    conda run -n pytorch python tools/_p1369_a1_stopping_baselines.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os

import numpy as np
import torch
import torch.nn.functional as F

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
OUT = "outputs/analysis/a1_stopping_baselines.json"
EPS = [0.01, 0.02]
DATASETS = {
    "dtd": ("data/dtd/dtd/images", "a photo of a {} texture", 40, 15, 47),
    "food101": ("data/food-101/images", "a photo of {}, a type of food", 40, 12, 101),
    "fathomnet8": ("data/fathomnet8", "a photo of a {}", 25, 10, 7),
}
SEEDS = [42, 43]
EPOCHS = 10


def load_split(root, tpl, n_train, n_test):
    from PIL import Image
    classes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and not d.startswith("."))
    rs = np.random.RandomState(0)
    tr, ty, te, ey = [], [], [], []
    for ci, c in enumerate(classes):
        files = sorted(f for f in os.listdir(os.path.join(root, c)) if f.lower().endswith((".jpg", ".jpeg", ".png")))
        rs.shuffle(files)
        for f in files[:n_train]:
            tr.append(Image.open(os.path.join(root, c, f)).convert("RGB"))
            ty.append(ci)
        for f in files[n_train:n_train + n_test]:
            te.append(Image.open(os.path.join(root, c, f)).convert("RGB"))
            ey.append(ci)
    return tr, np.array(ty), te, np.array(ey), [tpl.format(c.replace("_", " ")) for c in classes]


def signals(sn):
    """Per-checkpoint confidence signals from the score matrix (n_eval x n_classes)."""
    z = sn - sn.max(1, keepdims=True)
    e = np.exp(z)
    p = e / e.sum(1, keepdims=True)
    return {
        "entropy": float(np.mean(-(p * np.log(p + 1e-12)).sum(1))),
        "maxsoftmax": float(np.mean(p.max(1))),
        "maxlogit": float(np.mean(sn.max(1))),
        "energy": float(np.mean(np.log(np.exp(z).sum(1)) + sn.max(1))),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(0)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from peft import LoraConfig, get_peft_model
    from transformers import CLIPModel, CLIPProcessor
    bdir = "models/clip-vit-base-patch32"
    base = CLIPModel.from_pretrained(bdir, local_files_only=True).to(device).eval()
    proc = CLIPProcessor.from_pretrained(bdir, local_files_only=True)

    def img_emb(pil):
        out = []
        with torch.no_grad():
            for i in range(0, len(pil), 32):
                inp = proc(images=pil[i:i + 32], return_tensors="pt").to(device)
                v = base.vision_model(**inp)
                pooled = v[1] if isinstance(v, tuple) else v.pooler_output
                out.append(F.normalize(base.visual_projection(pooled).float(), dim=-1))
        return torch.cat(out)

    payload = {"protocol": "CLIP B/32 text-tower LoRA, in-domain held-out, 10 epochs; baselines = entropy/maxsoftmax/maxlogit/energy",
               "eps": EPS, "runs": {}}
    for ds, (root, tpl, ntr, nte, nc) in DATASETS.items():
        tr_pil, tr_y, te_pil, te_y, texts = load_split(root, tpl, ntr, nte)
        tr_img, te_img = img_emb(tr_pil), img_emb(te_pil)
        print(f"  [{ds}] train {len(tr_img)} test {len(te_img)} classes {len(texts)}", flush=True)
        for seed in SEEDS:
            key = f"{ds}|seed{seed}"
            torch.manual_seed(seed)
            np.random.seed(seed)
            model = CLIPModel.from_pretrained(bdir, local_files_only=True).to(device)
            model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0, bias="none",
                                                     target_modules=r"text_model.*\.(q_proj|k_proj|v_proj)$"))
            params = [p for p in model.parameters() if p.requires_grad]
            opt = torch.optim.AdamW(params, lr=1e-3)
            rng = np.random.RandomState(seed)
            rows = []
            for ep in range(1, EPOCHS + 1):
                model.train()
                order = rng.permutation(len(tr_img))
                for i in range(0, len(order), 32):
                    sel = order[i:i + 32]
                    if len(sel) < 2:
                        continue
                    ti = proc(text=texts, return_tensors="pt", padding=True).to(device)
                    o = model.text_model(**ti)
                    pooled = o[1] if isinstance(o, tuple) else o.pooler_output
                    te = F.normalize(model.text_projection(pooled).float(), dim=-1)
                    loss = F.cross_entropy(tr_img[sel] @ te.T, torch.tensor(tr_y[sel], device=device))
                    opt.zero_grad()
                    loss.backward()
                    opt.step()
                model.eval()
                with torch.no_grad():
                    ti = proc(text=texts, return_tensors="pt", padding=True).to(device)
                    o = model.text_model(**ti)
                    pooled = o[1] if isinstance(o, tuple) else o.pooler_output
                    te = F.normalize(model.text_projection(pooled).float(), dim=-1)
                sn = (te_img @ te.T).float().cpu().numpy()
                top1 = float((sn.argmax(1) == te_y).mean() * 100)
                r = np.arange(len(te_y))
                ts = sn[r, te_y]
                s2 = sn.copy()
                s2[r, te_y] = -1e9
                margin = ts - s2.max(1)
                cg = float((te_img.mean(0) - te.mean(0)).norm().item())
                row = {"epoch": ep, "top1": top1, "CG": cg}
                for e in EPS:
                    row["mass_%g" % e] = float((margin <= 2 * e).mean())
                row.update(signals(sn))
                rows.append(row)
            payload["runs"][key] = rows
            print(f"   [{key}] tops={[round(r['top1'], 1) for r in rows]}", flush=True)
            if a.apply:
                io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
            del model
            torch.cuda.empty_cache()
        del tr_img, te_img
        torch.cuda.empty_cache()
    if a.apply:
        print("  wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
