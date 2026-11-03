# -*- coding: utf-8 -*-
r"""A1: monitoring validation on an in-batch retrieval task.

The classification protocol is extended to retrieval: image-caption pairs from the local marine caption set (537 pairs),
with a 400/137 train/held-out split. The text tower is adapted with LoRA; after every epoch the held-out split is scored for
in-batch retrieval (R@1), the margin mass of the true caption against the best wrong caption, and the image-text centroid
gap. This checks that the certificate works on a task where the dependent variable is retrieval, not classification.

Output: outputs/analysis/a1_retrieval_monitor.json

    conda run -n pytorch python tools/_p1412_a1_retrieval_monitor.py --apply
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
OUT = "outputs/analysis/a1_retrieval_monitor.json"
ROOT = "data/marine_captions"
N_TRAIN = 400
EPOCHS = 10
SEED = 42


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    from PIL import Image
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from peft import LoraConfig, get_peft_model
    from transformers import CLIPModel, CLIPProcessor
    caps = json.load(io.open(os.path.join(ROOT, "captions.json"), encoding="utf-8"))["captions"]
    files = sorted(f for f in os.listdir(ROOT) if f.lower().endswith(".jpg"))
    assert len(files) == len(caps), (len(files), len(caps))
    imgs = [Image.open(os.path.join(ROOT, f)).convert("RGB") for f in files]
    rs = np.random.RandomState(SEED)
    perm = rs.permutation(len(files))
    tr = perm[:N_TRAIN]
    te = perm[N_TRAIN:]
    tr_imgs = [imgs[i] for i in tr]
    tr_caps = [caps[i] for i in tr]
    te_imgs = [imgs[i] for i in te]
    te_caps = [caps[i] for i in te]
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

    def txt_emb(texts):
        with torch.no_grad():
            ti = proc(text=list(texts), return_tensors="pt", padding=True).to(device)
            o = base.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            return F.normalize(base.text_projection(pooled).float(), dim=-1)

    tr_img, te_img = img_emb(tr_imgs), img_emb(te_imgs)
    frozen_tr_txt = txt_emb(tr_caps)
    model = CLIPModel.from_pretrained(bdir, local_files_only=True).to(device)
    model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0, bias="none",
                                             target_modules=r"text_model.*\.(q_proj|k_proj|v_proj)$"))
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-3)
    rng = np.random.RandomState(SEED)
    rows = []
    for ep in range(1, EPOCHS + 1):
        model.train()
        order = rng.permutation(N_TRAIN)
        for i in range(0, len(order), 32):
            sel = order[i:i + 32]
            if len(sel) < 2:
                continue
            ti = proc(text=[tr_caps[j] for j in sel], return_tensors="pt", padding=True).to(device)
            o = model.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            te = F.normalize(model.text_projection(pooled).float(), dim=-1)
            logits = tr_img[sel] @ te.T
            loss = F.cross_entropy(logits, torch.arange(len(sel), device=device))
            opt.zero_grad()
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            ti = proc(text=te_caps, return_tensors="pt", padding=True).to(device)
            o = model.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            te = F.normalize(model.text_projection(pooled).float(), dim=-1)
        sn = (te_img @ te.T).float().cpu().numpy()
        n = len(te_caps)
        r = np.arange(n)
        r1 = float((sn.argmax(1) == r).mean() * 100)
        ts = sn[r, r]
        s2 = sn.copy()
        s2[r, r] = -1e9
        margin = ts - s2.max(1)
        row = {"epoch": ep, "R@1": r1,
               "mass_0.01": float((margin <= 0.02).mean()),
               "mass_0.05": float((margin <= 0.10).mean()),
               "CG": float((te_img.mean(0) - te.mean(0)).norm().item())}
        rows.append(row)
        print(f"   ep{ep} R@1={r1:.1f} M01={row['mass_0.01']:.3f} M05={row['mass_0.05']:.3f} CG={row['CG']:.4f}", flush=True)
    payload = {"protocol": "CLIP B/32, text-tower LoRA, marine caption set, 400 train / 137 held-out pairs, 10 epochs, "
                          "in-batch retrieval", "runs": {"marine_retrieval": rows}}
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("  wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
