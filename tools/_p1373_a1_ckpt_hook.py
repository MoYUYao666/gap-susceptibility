# -*- coding: utf-8 -*-
r"""A1: monitoring run with a per-epoch checkpoint hook.

Re-runs the DTD interior-optimum trajectory (one backbone, one seed, ten epochs) and saves the LoRA adapter state after
every epoch under outputs/a1_monitor_ckpt/dtd_seed42/. This closes the "no per-epoch checkpoints were archived" gap and
makes the monitoring history reproducible without retraining.

Output: outputs/analysis/a1_monitor_ckpt.json
Checkpoints: outputs/a1_monitor_ckpt/dtd_seed42/ep{k}.pt

    conda run -n pytorch python tools/_p1373_a1_ckpt_hook.py --apply
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
OUT = "outputs/analysis/a1_monitor_ckpt.json"
CKPT = "outputs/a1_monitor_ckpt/dtd_seed42"
ROOT = "data/dtd/dtd/images"
TEMPLATE = "a photo of a {} texture"
SEED = 42
EPOCHS = 10


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from PIL import Image
    from peft import LoraConfig, get_peft_model
    from transformers import CLIPModel, CLIPProcessor
    bdir = "models/clip-vit-base-patch32"
    base = CLIPModel.from_pretrained(bdir, local_files_only=True).to(device).eval()
    proc = CLIPProcessor.from_pretrained(bdir, local_files_only=True)
    classes = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d)))
    rs = np.random.RandomState(0)
    tr_pil, tr_y, te_pil, te_y = [], [], [], []
    for ci, c in enumerate(classes):
        files = sorted(f for f in os.listdir(os.path.join(ROOT, c)) if f.lower().endswith((".jpg", ".jpeg", ".png")))
        rs.shuffle(files)
        for f in files[:40]:
            tr_pil.append(Image.open(os.path.join(ROOT, c, f)).convert("RGB"))
            tr_y.append(ci)
        for f in files[40:55]:
            te_pil.append(Image.open(os.path.join(ROOT, c, f)).convert("RGB"))
            te_y.append(ci)
    texts = [TEMPLATE.format(c.replace("_", " ")) for c in classes]
    tr_y, te_y = np.array(tr_y), np.array(te_y)

    def img_emb(pil):
        out = []
        with torch.no_grad():
            for i in range(0, len(pil), 32):
                inp = proc(images=pil[i:i + 32], return_tensors="pt").to(device)
                v = base.vision_model(**inp)
                pooled = v[1] if isinstance(v, tuple) else v.pooler_output
                out.append(F.normalize(base.visual_projection(pooled).float(), dim=-1))
        return torch.cat(out)

    tr_img, te_img = img_emb(tr_pil), img_emb(te_pil)
    model = CLIPModel.from_pretrained(bdir, local_files_only=True).to(device)
    model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0, bias="none",
                                             target_modules=r"text_model.*\.(q_proj|k_proj|v_proj)$"))
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=1e-3)
    rng = np.random.RandomState(SEED)
    os.makedirs(CKPT, exist_ok=True)
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
        state = {k: v.detach().cpu() for k, v in model.state_dict().items() if "lora" in k}
        torch.save({"epoch": ep, "state": state}, os.path.join(CKPT, "ep%d.pt" % ep))
        rows.append({"epoch": ep, "top1": top1, "CG": cg, "mass_0.01": float((margin <= 0.02).mean()),
                     "ckpt": os.path.join(CKPT, "ep%d.pt" % ep)})
        print(f"  ep{ep} top1={top1:.2f} CG={cg:.4f} M01={rows[-1]['mass_0.01']:.3f}", flush=True)
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"protocol": "CLIP B/32 text-tower LoRA, DTD 47 classes, 40/15 split, seed 42, 10 epochs, per-epoch LoRA states saved",
             "checkpoint_dir": CKPT, "rows": rows}, indent=1))
        print("  wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
