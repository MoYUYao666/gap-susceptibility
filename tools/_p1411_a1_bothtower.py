# -*- coding: utf-8 -*-
r"""A1: repeat the interior-optimum monitoring protocol with LoRA on both towers.

The earlier validation adapted only the text tower. Here both towers are adapted (rank 8), so the image embeddings change
after every epoch and must be recomputed; this checks that the monitoring result is not a text-tower artefact.

Output: outputs/analysis/a1_monitor_bothtower.json

    conda run -n pytorch python tools/_p1411_a1_bothtower.py --apply
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
OUT = "outputs/analysis/a1_monitor_bothtower.json"
DATASETS = {"dtd": ("data/dtd/dtd/images", "a photo of a {} texture", 40, 15),
            "food101": ("data/food-101/images", "a photo of {}, a type of food", 40, 12)}
SEED = 42
EPOCHS = 10


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
    texts = [tpl.format(c.replace("_", " ")) for c in keep]
    return tr, np.array([remap[c] for c in ty]), te, np.array([remap[c] for c in ey]), texts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(SEED)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from peft import LoraConfig, get_peft_model
    from transformers import CLIPModel, CLIPProcessor
    bdir = "models/clip-vit-base-patch32"
    proc = CLIPProcessor.from_pretrained(bdir, local_files_only=True)
    payload = {"protocol": "CLIP B/32, LoRA on both towers, seed 42, 10 epochs", "runs": {}}
    for ds, (root, tpl, ntr, nte) in DATASETS.items():
        tr_pil, tr_y, te_pil, te_y, texts = load_split(root, tpl, ntr, nte)
        print(f"  [{ds}] train {len(tr_pil)} test {len(te_pil)} classes {len(texts)}", flush=True)
        model = CLIPModel.from_pretrained(bdir, local_files_only=True).to(device)
        model = get_peft_model(model, LoraConfig(
            r=8, lora_alpha=16, lora_dropout=0.0, bias="none",
            target_modules=r"(text_model|vision_model).*\.(q_proj|k_proj|v_proj)$"))
        opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-3)
        rng = np.random.RandomState(SEED)
        rows = []

        def embeds(pil):
            feats = []
            with torch.no_grad():
                for i in range(0, len(pil), 32):
                    inp = proc(images=pil[i:i + 32], return_tensors="pt").to(device)
                    v = model.vision_model(**inp)
                    pooled = v[1] if isinstance(v, tuple) else v.pooler_output
                    feats.append(F.normalize(model.visual_projection(pooled).float(), dim=-1))
            return torch.cat(feats)

        for ep in range(1, EPOCHS + 1):
            model.train()
            tr_img = embeds(tr_pil)
            te_img = embeds(te_pil)
            order = rng.permutation(len(tr_pil))
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
            tr_img = embeds(tr_pil)
            te_img = embeds(te_pil)
            with torch.no_grad():
                ti = proc(text=texts, return_tensors="pt", padding=True).to(device)
                o = model.text_model(**ti)
                pooled = o[1] if isinstance(o, tuple) else o.pooler_output
                te = F.normalize(model.text_projection(pooled).float(), dim=-1)
            sn = (te_img @ te.T).float().cpu().numpy()
            r = np.arange(len(te_y))
            ts = sn[r, te_y]
            s2 = sn.copy()
            s2[r, te_y] = -1e9
            margin = ts - s2.max(1)
            row = {"epoch": ep, "top1": float((sn.argmax(1) == te_y).mean() * 100),
                   "mass_0.01": float((margin <= 0.02).mean()),
                   "CG": float((te_img.mean(0) - te.mean(0)).norm().item())}
            rows.append(row)
            print(f"   ep{ep} top1={row['top1']:.1f} M={row['mass_0.01']:.3f} CG={row['CG']:.3f}", flush=True)
        payload["runs"][ds] = rows
        if a.apply:
            io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        del model
        torch.cuda.empty_cache()
    if a.apply:
        print("  wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
