# -*- coding: utf-8 -*-
r"""P1-6 retrieval fine-tuning + P2-11 cross-domain campaign.

Part A (P1-6): LoRA fine-tuning on the 536 marine image-caption pairs (400 train / 136 held-out test), two variants
(text tower only, both towers), three epochs, three seeds. After every epoch the held-out set is evaluated for image->caption
R@1, caption->image R@1, centroid gap, and the paired margin mass M_R(0.01)/M_R(0.02). This supplies real fine-tuned
retrieval evidence (the earlier retrieval archive used synthetic perturbations only).

Part B (P2-11): the same campaign protocol on fathomnet8 (8 marine classes, 344 images), evaluating transfer back to the
ImageNet-5k holdout; tests whether the certificate behaves across domains.

Outputs:
    outputs/analysis/a1_retrieval_realfinetune.json
    outputs/analysis/a1_campaign_crossdomain.json

    python tools/_p1332_retrieval_and_crossdomain.py [--apply]
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
AN = os.path.join(REPO, "outputs", "analysis")
OUT_A = os.path.join(AN, "a1_retrieval_realfinetune.json")
OUT_B = os.path.join(AN, "a1_campaign_crossdomain.json")
TARGET_TEXT = r"text_model.*\.(q_proj|k_proj|v_proj)$"
TARGET_BOTH = r"(text_model|vision_model).*\.(q_proj|k_proj|v_proj)$"
EPS = [0.01, 0.02]


def img_emb(model, proc, pil, device, batch=32):
    out = []
    with torch.no_grad():
        for i in range(0, len(pil), batch):
            inp = proc(images=pil[i:i + batch], return_tensors="pt").to(device)
            v = model.vision_model(**inp)
            pooled = v[1] if isinstance(v, tuple) else v.pooler_output
            out.append(F.normalize(model.visual_projection(pooled).float(), dim=-1))
    return torch.cat(out)


def txt_emb(model, proc, texts, device):
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), 128):
            ti = proc(text=texts[i:i + 128], return_tensors="pt", padding=True).to(device)
            o = model.text_model(**ti)
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            out.append(F.normalize(model.text_projection(pooled).float(), dim=-1))
    return torch.cat(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    torch.manual_seed(0)
    np.random.seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from peft import LoraConfig, get_peft_model
    from transformers import CLIPModel, CLIPProcessor
    from datasets import Dataset
    from scipy import stats as st
    from PIL import Image

    local = os.path.join(REPO, "models", "clip-vit-base-patch32")
    base = CLIPModel.from_pretrained(local, local_files_only=True).to(device).eval()
    proc = CLIPProcessor.from_pretrained(local, local_files_only=True)

    # ---- ImageNet-5k holdout (same subset as the campaign)
    parq = sorted(glob.glob(os.path.join(REPO, "data", "imagenet_hf", "*.parquet")))
    ds = Dataset.from_parquet(parq)
    names = [x.split(",")[0].strip() for x in ds.features["label"].names]
    if len(names) == 1001:
        names = names[:1000]
    rs = np.random.RandomState(42)
    idx = rs.choice(len(ds), size=5000, replace=False)
    sub = ds.select(idx.tolist())
    ev_labels = np.asarray(sub["label"])
    ev_pil = [im.convert("RGB") for im in sub["image"]]
    ev_texts = ["a photo of a " + c.replace("_", " ") for c in names]
    ev_img_frozen = img_emb(base, proc, ev_pil, device)
    ev_txt_frozen = txt_emb(base, proc, ev_texts, device)
    print("  ImageNet-5k eval ready", flush=True)

    # ================================================== Part A: retrieval
    root = os.path.join(REPO, "data", "marine_captions")
    imgs = sorted(glob.glob(os.path.join(root, "*.jpg")))
    caps = json.load(io.open(os.path.join(root, "captions.json"), encoding="utf-8"))["captions"]
    n = min(len(imgs), len(caps))
    pil = [Image.open(imgs[i]).convert("RGB") for i in range(n)]
    texts = [str(caps[i]) for i in range(n)]
    perm = np.random.RandomState(7).permutation(n)
    tr_idx, te_idx = perm[:400], perm[400:]
    tr_pil = [pil[i] for i in tr_idx]
    tr_txt = [texts[i] for i in tr_idx]
    te_pil = [pil[i] for i in te_idx]
    te_txt = [texts[i] for i in te_idx]
    print(f"  retrieval: train {len(tr_pil)} / test {len(te_pil)}", flush=True)

    def retrieval_metrics(model):
        ie = img_emb(model, proc, te_pil, device)
        te = txt_emb(model, proc, te_txt, device)
        s = (ie @ te.T).float().cpu().numpy()
        i2t = float((s.argmax(1) == np.arange(len(te_pil))).mean() * 100)
        t2i = float((s.argmax(0) == np.arange(len(te_pil))).mean() * 100)
        rows = np.arange(len(te_pil))
        paired = s[rows, rows]
        s2 = s.copy()
        s2[rows, rows] = -1e9
        margin = paired - s2.max(1)
        cg = float((ie.mean(0) - te.mean(0)).norm().item())
        out = {"R@1_i2t": i2t, "R@1_t2i": t2i, "CG": cg}
        for e in EPS:
            out["massR_%g" % e] = float((margin <= 2 * e).mean())
        return out

    ret_payload = {"protocol": "LoRA on 400 marine pairs, held-out 136 pairs; R@1 both directions",
                   "n_train": len(tr_pil), "n_test": len(te_pil), "eps": EPS, "runs": {}}
    frozen_m = retrieval_metrics(base)
    ret_payload["frozen"] = frozen_m
    print(f"  retrieval frozen: {frozen_m}", flush=True)
    for tower in ("text", "both"):
        for seed in (42, 43, 44):
            key = f"{tower}|seed{seed}"
            torch.manual_seed(seed)
            np.random.seed(seed)
            model = CLIPModel.from_pretrained(local, local_files_only=True).to(device)
            cfg = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0, bias="none",
                             target_modules=TARGET_TEXT if tower == "text" else TARGET_BOTH)
            model = get_peft_model(model, cfg)
            params = [p for p in model.parameters() if p.requires_grad]
            opt = torch.optim.AdamW(params, lr=1e-3 if tower == "text" else 5e-4)
            rng = np.random.RandomState(seed)
            ck = []
            tr_img_frozen = img_emb(base, proc, tr_pil, device) if tower == "text" else None
            for ep in range(1, 4):
                model.train()
                order = rng.permutation(len(tr_pil))
                for i in range(0, len(order), 32):
                    sel = order[i:i + 32]
                    if len(sel) < 2:
                        continue
                    ti = proc(text=[tr_txt[j] for j in sel], return_tensors="pt", padding=True).to(device)
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
                    lab = torch.arange(len(sel), device=device)
                    loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
                    opt.zero_grad()
                    loss.backward()
                    opt.step()
                model.eval()
                mtr = retrieval_metrics(model)
                mtr["epoch"] = ep
                ck.append(mtr)
                print(f"   [{key}] ep{ep} R@1_i2t={mtr['R@1_i2t']:.1f} CG={mtr['CG']:.3f} "
                      f"MR01={mtr['massR_0.01']:.3f}", flush=True)
            ret_payload["runs"][key] = ck
            if a.apply:
                io.open(OUT_A, "w", encoding="utf-8", newline="").write(json.dumps(ret_payload, indent=1))
            del model, params
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    if a.apply:
        print("  wrote", os.path.relpath(OUT_A, REPO))

    # ================================================== Part B: cross-domain
    cross = {"protocol": "LoRA on fathomnet8 (8 marine classes, 344 images), transfer to the ImageNet-5k holdout",
             "n_train": None, "runs": {}}
    froot = os.path.join(REPO, "data", "fathomnet8")
    classes = sorted(d for d in os.listdir(froot) if os.path.isdir(os.path.join(froot, d)))
    paths, labels = [], []
    for ci, c in enumerate(classes):
        for f in sorted(os.listdir(os.path.join(froot, c))):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                paths.append(os.path.join(froot, c, f))
                labels.append(ci)
    f_pil, f_y = [], []
    for p, y in zip(paths, labels):
        try:
            f_pil.append(Image.open(p).convert("RGB"))
            f_y.append(y)
        except Exception:
            continue
    f_texts = ["a photo of a " + c.replace("_", " ") for c in classes]
    cross["n_train"] = len(f_pil)
    cross["classes"] = classes
    print(f"  cross-domain: {len(f_pil)} images, {len(classes)} classes", flush=True)
    from scipy import stats as st  # noqa: F811
    for tower in ("text", "both"):
        for seed in (42, 43):
            key = f"fathomnet|{tower}|seed{seed}"
            torch.manual_seed(seed)
            np.random.seed(seed)
            model = CLIPModel.from_pretrained(local, local_files_only=True).to(device)
            cfg = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0, bias="none",
                             target_modules=TARGET_TEXT if tower == "text" else TARGET_BOTH)
            model = get_peft_model(model, cfg)
            params = [p for p in model.parameters() if p.requires_grad]
            opt = torch.optim.AdamW(params, lr=1e-3 if tower == "text" else 5e-4)
            rng = np.random.RandomState(seed)
            ck = []
            for ep in range(1, 4):
                model.train()
                order = rng.permutation(len(f_pil))
                for i in range(0, len(order), 32):
                    sel = order[i:i + 32]
                    if len(sel) < 2:
                        continue
                    ti = proc(text=f_texts, return_tensors="pt", padding=True).to(device)
                    o = model.text_model(**ti)
                    pooled = o[1] if isinstance(o, tuple) else o.pooler_output
                    te = F.normalize(model.text_projection(pooled).float(), dim=-1)
                    inp = proc(images=[f_pil[j] for j in sel], return_tensors="pt").to(device)
                    v = model.vision_model(**inp)
                    pv = v[1] if isinstance(v, tuple) else v.pooler_output
                    ie = F.normalize(model.visual_projection(pv).float(), dim=-1)
                    logits = ie @ te.T
                    lab = torch.tensor([f_y[j] for j in sel], device=device)
                    loss = F.cross_entropy(logits, lab)
                    opt.zero_grad()
                    loss.backward()
                    opt.step()
                model.eval()
                ev_img = ev_img_frozen if tower == "text" else img_emb(model, proc, ev_pil, device)
                ev_txt = txt_emb(model, proc, ev_texts, device)
                sn = (ev_img @ ev_txt.T).float().cpu().numpy()
                pred = sn.argmax(1)
                top1 = float((pred == ev_labels).mean() * 100)
                rows = np.arange(len(ev_labels))
                ts = sn[rows, ev_labels]
                s2 = sn.copy()
                s2[rows, ev_labels] = -1e9
                margin = ts - s2.max(1)
                cg = float((ev_img.mean(0) - ev_txt.mean(0)).norm().item())
                entry = {"epoch": ep, "top1": top1, "CG": cg}
                for e in EPS:
                    entry["mass_%g" % e] = float((margin <= 2 * e).mean())
                ck.append(entry)
                print(f"   [{key}] ep{ep} top1={top1:.2f} CG={cg:.4f} M01={entry['mass_0.01']:.3f}", flush=True)
            cross["runs"][key] = ck
            if a.apply:
                io.open(OUT_B, "w", encoding="utf-8", newline="").write(json.dumps(cross, indent=1))
            del model, params
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    if a.apply:
        print("  wrote", os.path.relpath(OUT_B, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
