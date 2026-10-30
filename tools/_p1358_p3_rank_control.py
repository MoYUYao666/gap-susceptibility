# -*- coding: utf-8 -*-
r"""P3 supplementary control: local LoRA rank sensitivity in a CLIP model.

The main text reports a critical rank for LLaVA-1.5-7B under the blank-image protocol and retracts the claim that it is a
model property. This control asks the cheaper analogue question on a local CLIP model: does increasing the LoRA rank
inflate the centroid gap or degrade held-out accuracy in the same direction?

Protocol: CLIP ViT-B/32 with LoRA on the text tower (rank 4/8/16/32/64), DTD 47 classes with a per-class held-out split,
six epochs, two seeds. Reported per rank/seed: best and last held-out top-1, centroid gap at the first and last epoch,
and the relationship between rank and gap.

Output: outputs/analysis/p3_rank_local_control.json

    conda run -n pytorch python tools/_p1358_p3_rank_control.py --apply
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
OUT = "outputs/analysis/p3_rank_local_control.json"
RANKS = [4, 8, 16, 32, 64]
SEEDS = [42, 43]
EPOCHS = 6
ROOT = "data/dtd/dtd/images"
TEMPLATE = "a photo of a {} texture"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(0)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from PIL import Image
    from peft import LoraConfig, get_peft_model
    from transformers import CLIPModel, CLIPProcessor
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
    tr_y = np.array(tr_y)
    te_y = np.array(te_y)
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

    tr_img = img_emb(tr_pil)
    te_img = img_emb(te_pil)
    print(f"  train {len(tr_img)} test {len(te_img)} classes {len(texts)}", flush=True)
    payload = {"protocol": "CLIP B/32, LoRA on text tower, DTD 47 classes, 6 epochs", "ranks": RANKS,
               "seeds": SEEDS, "runs": {}}
    for rank in RANKS:
        for seed in SEEDS:
            key = f"r{rank}|seed{seed}"
            torch.manual_seed(seed)
            np.random.seed(seed)
            model = CLIPModel.from_pretrained(bdir, local_files_only=True).to(device)
            cfg = LoraConfig(r=rank, lora_alpha=2 * rank, lora_dropout=0.0, bias="none",
                             target_modules=r"text_model.*\.(q_proj|k_proj|v_proj)$")
            model = get_peft_model(model, cfg)
            params = [p for p in model.parameters() if p.requires_grad]
            opt = torch.optim.AdamW(params, lr=1e-3)
            rng = np.random.RandomState(seed)
            n_par = sum(p.numel() for p in params)
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
                    logits = tr_img[sel] @ te.T
                    loss = F.cross_entropy(logits, torch.tensor(tr_y[sel], device=device))
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
                cg = float((te_img.mean(0) - te.mean(0)).norm().item())
                rows.append({"epoch": ep, "top1": top1, "CG": cg})
            payload["runs"][key] = {"rank": rank, "seed": seed, "n_param": n_par, "rows": rows}
            print(f"   [{key}] n_param={n_par} top1={[round(r['top1'],1) for r in rows]} "
                  f"CG={[round(r['CG'],3) for r in rows]}", flush=True)
            del model
            torch.cuda.empty_cache()
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
        print("  wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
