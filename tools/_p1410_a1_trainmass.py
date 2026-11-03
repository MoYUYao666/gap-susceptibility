# -*- coding: utf-8 -*-
r"""A1: epoch selection with the training-split margin mass (large, label-rich sample) versus the held-out mass.

On small held-out splits the held-out mass is too coarse/noisy; the training split has many more labelled pairs. This script
re-runs the monitoring protocol (CLIP B/32, text-tower LoRA, 10 epochs) on four domains and records both the held-out and
the training margin mass after every epoch.

Output: outputs/analysis/a1_monitor_trainmass.json

    conda run -n pytorch python tools/_p1410_a1_trainmass.py --apply
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
OUT = "outputs/analysis/a1_monitor_trainmass.json"
DATASETS = {
    "dtd": ("data/dtd/dtd/images", "a photo of a {} texture", 40, 15),
    "food101": ("data/food-101/images", "a photo of {}, a type of food", 40, 12),
    "fathomnet8": ("data/fathomnet8", "a photo of a {}", 25, 10),
    "inat_wild": ("data/inat_wild", "a photo of a {}", 6, 3),
}
SEED = 42
EPOCHS = 10
EPS = [0.01, 0.02]


def load_split(root, tpl, n_train, n_test):
    from PIL import Image
    classes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and not d.startswith("."))
    rs = np.random.RandomState(0)
    tr, ty, te, ey = [], [], [], []
    for c in classes:
        files = sorted(f for f in os.listdir(os.path.join(root, c)) if f.lower().endswith((".jpg", ".jpeg", ".png")))
        if len(files) < n_train + n_test:
            continue
        rs.shuffle(files)
        for f in files[:n_train]:
            tr.append(Image.open(os.path.join(root, c, f)).convert("RGB"))
            ty.append(c)
        for f in files[n_train:n_train + n_test]:
            te.append(Image.open(os.path.join(root, c, f)).convert("RGB"))
            ey.append(c)
    keep = sorted(set(ty) | set(ey))
    remap = {c: i for i, c in enumerate(keep)}
    return tr, np.array([remap[c] for c in ty]), te, np.array([remap[c] for c in ey]), [tpl.format(c.replace("_", " ")) for c in keep]


def margin_stats(scores, labels):
    r = np.arange(len(labels))
    ts = scores[r, labels]
    s2 = scores.copy()
    s2[r, labels] = -1e9
    margin = ts - s2.max(1)
    out = {}
    for e in EPS:
        out["mass_%g" % e] = float((margin <= 2 * e).mean())
    out["top1"] = float((scores.argmax(1) == labels).mean() * 100)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(SEED)
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

    payload = {"protocol": "CLIP B/32, text-tower LoRA, seed 42, 10 epochs; held-out vs training margin mass",
               "runs": {}}
    for ds, (root, tpl, ntr, nte) in DATASETS.items():
        tr_pil, tr_y, te_pil, te_y, texts = load_split(root, tpl, ntr, nte)
        tr_img, te_img = img_emb(tr_pil), img_emb(te_pil)
        print(f"  [{ds}] train {len(tr_img)} test {len(te_img)} classes {len(texts)}", flush=True)
        model = CLIPModel.from_pretrained(bdir, local_files_only=True).to(device)
        model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0, bias="none",
                                                 target_modules=r"text_model.*\.(q_proj|k_proj|v_proj)$"))
        opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-3)
        rng = np.random.RandomState(SEED)
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
            eval_scores = (te_img @ te.T).float().cpu().numpy()
            train_scores = (tr_img @ te.T).float().cpu().numpy()
            ev = margin_stats(eval_scores, te_y)
            tv = margin_stats(train_scores, tr_y)
            row = {"epoch": ep,
                   "eval_top1": ev["top1"], "eval_mass_0.01": ev["mass_0.01"],
                   "train_top1": tv["top1"], "train_mass_0.01": tv["mass_0.01"],
                   "eval_CG": float((te_img.mean(0) - te.mean(0)).norm().item())}
            rows.append(row)
            print(f"   ep{ep} eval_top1={ev['top1']:.1f} evalM={ev['mass_0.01']:.3f} "
                  f"train_top1={tv['top1']:.1f} trainM={tv['mass_0.01']:.3f}", flush=True)
        payload["runs"][ds] = rows
        if a.apply:
            io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        del model
        torch.cuda.empty_cache()
        del tr_img, te_img
    if a.apply:
        print("  wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
