# -*- coding: utf-8 -*-
r"""P0-1 (proper test): a campaign with an interior optimum, so that "stop early" is not trivially optimal.

Fine-tune LoRA on 2,000 in-domain ImageNet-5k images drawn from the complement of the 5,000-image holdout, evaluate the
disjoint holdout after every epoch for six epochs. In-domain training should raise transfer accuracy before overfitting,
creating an interior optimum that lets the margin-mass stopping rule be compared with the labelled oracle in a non-trivial
way.

Output: outputs/analysis/a1_certificate_interior.json

    python tools/_p1334_interior_optimum.py [--apply]
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
OUT = os.path.join(REPO, "outputs", "analysis", "a1_certificate_interior.json")
TARGET_TEXT = r"text_model.*\.(q_proj|k_proj|v_proj)$"
TARGET_BOTH = r"(text_model|vision_model).*\.(q_proj|k_proj|v_proj)$"
EPS = [0.01, 0.02]
N_TRAIN = 2000
N_EVAL = 5000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(0)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from peft import LoraConfig, get_peft_model
    from transformers import CLIPModel, CLIPProcessor
    from datasets import Dataset

    local = os.path.join(REPO, "models", "clip-vit-base-patch32")
    base = CLIPModel.from_pretrained(local, local_files_only=True).to(device).eval()
    proc = CLIPProcessor.from_pretrained(local, local_files_only=True)
    parq = sorted(glob.glob(os.path.join(REPO, "data", "imagenet_hf", "*.parquet")))
    ds = Dataset.from_parquet(parq)
    names = [x.split(",")[0].strip() for x in ds.features["label"].names]
    if len(names) == 1001:
        names = names[:1000]
    labels_all = np.asarray(ds["label"])
    rs = np.random.RandomState(42)
    ev_idx = rs.choice(len(ds), size=N_EVAL, replace=False)
    ev_set = set(ev_idx.tolist())
    complement = np.array([i for i in range(len(ds)) if i not in ev_set])
    tr_idx = np.random.RandomState(7).choice(complement, size=N_TRAIN, replace=False)
    ev_pil = [ds[int(i)]["image"].convert("RGB") for i in ev_idx]
    ev_y = labels_all[ev_idx]
    tr_pil = [ds[int(i)]["image"].convert("RGB") for i in tr_idx]
    tr_y = labels_all[tr_idx]
    ev_texts = ["a photo of a " + c.replace("_", " ") for c in names]
    print(f"  train {len(tr_pil)} in-domain / eval {len(ev_pil)} disjoint", flush=True)

    def img_emb(model, pil, batch=32):
        out = []
        with torch.no_grad():
            for i in range(0, len(pil), batch):
                inp = proc(images=pil[i:i + batch], return_tensors="pt").to(device)
                v = model.vision_model(**inp)
                pooled = v[1] if isinstance(v, tuple) else v.pooler_output
                out.append(F.normalize(model.visual_projection(pooled).float(), dim=-1))
        return torch.cat(out)

    def txt_emb(model, texts):
        out = []
        with torch.no_grad():
            for i in range(0, len(texts), 256):
                ti = proc(text=texts[i:i + 256], return_tensors="pt", padding=True).to(device)
                o = model.text_model(**ti)
                pooled = o[1] if isinstance(o, tuple) else o.pooler_output
                out.append(F.normalize(model.text_projection(pooled).float(), dim=-1))
        return torch.cat(out)

    ev_img_frozen = img_emb(base, ev_pil)
    payload = {"protocol": "LoRA on 2000 in-domain ImageNet-5k images, disjoint 5000-image holdout, 6 epochs",
               "n_train": len(tr_pil), "n_eval": len(ev_pil), "eps": EPS, "runs": {}}
    if os.path.exists(OUT):
        try:
            payload["runs"] = json.load(io.open(OUT, encoding="utf-8")).get("runs", {})
        except Exception:
            pass

    for tower in ("text", "both"):
        for seed in (42, 43):
            key = f"{tower}|seed{seed}"
            if key in payload["runs"]:
                print(f"  {key}: archived", flush=True)
                continue
            torch.manual_seed(seed)
            np.random.seed(seed)
            model = CLIPModel.from_pretrained(local, local_files_only=True).to(device)
            cfg = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0, bias="none",
                             target_modules=TARGET_TEXT if tower == "text" else TARGET_BOTH)
            model = get_peft_model(model, cfg)
            params = [p for p in model.parameters() if p.requires_grad]
            opt = torch.optim.AdamW(params, lr=1e-3 if tower == "text" else 5e-4)
            rng = np.random.RandomState(seed)
            tr_img_frozen = img_emb(base, ev_pil[:1])  # placeholder not used
            tr_img_frozen = None
            if tower == "text":
                tr_img_frozen = img_emb(base, tr_pil)
            ck = []
            for ep in range(1, 7):
                model.train()
                order = rng.permutation(len(tr_pil))
                for i in range(0, len(order), 32):
                    sel = order[i:i + 32]
                    if len(sel) < 2:
                        continue
                    ti = proc(text=ev_texts, return_tensors="pt", padding=True).to(device)
                    o = model.text_model(**ti)
                    pooled = o[1] if isinstance(o, tuple) else o.pooler_output
                    te = F.normalize(model.text_projection(pooled).float(), dim=-1)
                    if tower == "text":
                        ie = tr_img_frozen[sel]
                    else:
                        inp = proc(images=[tr_pil[j] for j in sel], return_tensors="pt").to(device)
                        v = model.vision_model(**inp)
                        pv = v[1] if isinstance(v, tuple) else v.pooler_output
                        ie = F.normalize(model.visual_projection(pv).float(), dim=-1)
                    logits = ie @ te.T
                    lab = torch.tensor(tr_y[sel], device=device)
                    loss = F.cross_entropy(logits, lab)
                    opt.zero_grad()
                    loss.backward()
                    opt.step()
                model.eval()
                ev_img = ev_img_frozen if tower == "text" else img_emb(model, ev_pil)
                ev_txt = txt_emb(model, ev_texts)
                sn = (ev_img @ ev_txt.T).float().cpu().numpy()
                pred = sn.argmax(1)
                top1 = float((pred == ev_y).mean() * 100)
                rows = np.arange(len(ev_y))
                ts = sn[rows, ev_y]
                s2 = sn.copy()
                s2[rows, ev_y] = -1e9
                margin = ts - s2.max(1)
                cg = float((ev_img.mean(0) - ev_txt.mean(0)).norm().item())
                entry = {"epoch": ep, "top1": top1, "CG": cg}
                for e in EPS:
                    entry["mass_%g" % e] = float((margin <= 2 * e).mean())
                ck.append(entry)
                print(f"   [{key}] ep{ep} top1={top1:.2f} CG={cg:.4f} M01={entry['mass_0.01']:.3f}", flush=True)
            payload["runs"][key] = ck
            if a.apply:
                io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
            del model, params
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    if a.apply:
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
