# -*- coding: utf-8 -*-
r"""Larger-scale real fine-tuning campaign, with margin mass measured at every checkpoint.

Trains CLIP ViT-B/32 with LoRA on a local classification dataset and after every epoch evaluates the *transfer* task on a
fixed 5,000-image ImageNet-5k holdout, recording top-1, centroid gap, margin mass M(0.01)/M(0.02), and tau_5 against the
frozen top-5 sets. Two intervention variants are run:
    text : LoRA restricted to the text tower (target regex matches text_model only)
    both : LoRA on the text and vision towers
Each variant is run for several seeds and four epochs, so the campaign yields many real checkpoints with both a gap and an
accuracy measurement, and per-epoch margins for testing the margin mass as a monitor.

Outputs (incremental, merge-safe):
    outputs/analysis/a1_campaign.json          per-checkpoint metrics
    outputs/analysis/a1_campaign_correct.npz   per-checkpoint per-image correctness on the holdout

    python tools/_p1319_realfinetune_campaign.py --apply
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
OUT = os.path.join(REPO, "outputs", "analysis", "a1_campaign.json")
CORR = os.path.join(REPO, "outputs", "analysis", "a1_campaign_correct.npz")
N_EVAL = 5000
EPS = [0.01, 0.02]
TARGET_TEXT = r"text_model.*\.(q_proj|k_proj|v_proj)$"
TARGET_BOTH = r"(text_model|vision_model).*\.(q_proj|k_proj|v_proj)$"


def load_train_dataset(spec: str, n_train: int):
    from PIL import Image
    if spec == "dtd":
        root = os.path.join(REPO, "data", "dtd", "dtd", "images")
        tpl = "a photo of a {} texture"
    elif spec == "food101":
        root = os.path.join(REPO, "data", "food-101", "images")
        tpl = "a photo of {}, a type of food"
    elif spec == "inat_wild":
        root = os.path.join(REPO, "data", "inat_wild")
        tpl = "a photo of a {}"
    else:
        raise SystemExit("unsupported dataset " + spec)
    classes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and not d.startswith("."))
    paths, labels = [], []
    for ci, c in enumerate(classes):
        for f in sorted(os.listdir(os.path.join(root, c))):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                paths.append(os.path.join(root, c, f))
                labels.append(ci)
    rs = np.random.RandomState(42)
    sel = rs.choice(len(paths), size=min(n_train, len(paths)), replace=False)
    pil, ys = [], []
    for i in sel:
        try:
            pil.append(Image.open(paths[i]).convert("RGB"))
            ys.append(labels[i])
        except Exception:
            continue
    names = [c.replace("_", " ") for c in classes]
    return pil, np.asarray(ys), names, tpl


def load_eval():
    from datasets import Dataset
    parq = sorted(glob.glob(os.path.join(REPO, "data", "imagenet_hf", "*.parquet")))
    ds = Dataset.from_parquet(parq)
    names = [x.split(",")[0].strip() for x in ds.features["label"].names]
    if len(names) == 1001:
        names = names[:1000]
    rs = np.random.RandomState(42)
    idx = rs.choice(len(ds), size=min(N_EVAL, len(ds)), replace=False)
    sub = ds.select(idx.tolist())
    labels = np.asarray(sub["label"])
    pil = [im.convert("RGB") for im in sub["image"]]
    return pil, labels, ["a photo of a " + c.replace("_", " ") for c in names]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["dtd", "food101", "inat_wild"])
    ap.add_argument("--towers", nargs="+", default=["text", "both"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--n-train", type=int, default=2000)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        a.datasets, a.towers, a.seeds, a.epochs, a.n_train = a.datasets[:1], a.towers, a.seeds[:1], 1, 64

    from peft import LoraConfig, get_peft_model
    from transformers import CLIPModel, CLIPProcessor
    device = "cuda" if torch.cuda.is_available() else "cpu"
    local = os.path.join(REPO, "models", "clip-vit-base-patch32")
    base_model = CLIPModel.from_pretrained(local, local_files_only=True).to(device).eval()
    proc = CLIPProcessor.from_pretrained(local, local_files_only=True)

    def image_emb(model, pil, batch=32):
        out = []
        with torch.no_grad():
            for i in range(0, len(pil), batch):
                inp = proc(images=pil[i:i + batch], return_tensors="pt").to(device)
                v = model.vision_model(**inp)
                pooled = v[1] if isinstance(v, tuple) else v.pooler_output
                out.append(F.normalize(model.visual_projection(pooled).float(), dim=-1))
        return torch.cat(out)

    def text_emb(model, texts):
        out = []
        with torch.no_grad():
            for i in range(0, len(texts), 128):
                ti = proc(text=texts[i:i + 128], return_tensors="pt", padding=True).to(device)
                o = model.text_model(**ti)
                pooled = o[1] if isinstance(o, tuple) else o.pooler_output
                out.append(F.normalize(model.text_projection(pooled).float(), dim=-1))
        return torch.cat(out)

    eval_pil, eval_labels, eval_texts = load_eval()
    eval_img_frozen = image_emb(base_model, eval_pil)
    eval_txt_frozen = text_emb(base_model, eval_texts)
    frozen_scores = (eval_img_frozen @ eval_txt_frozen.T).float().cpu().numpy()
    top5 = np.argsort(-frozen_scores, axis=1)[:, :5]
    n_eval = len(eval_labels)
    from scipy import stats as st
    print(f"  eval set: {n_eval} images, {len(eval_texts)} classes", flush=True)

    payload = {"benchmark": "imagenet5k", "n_eval": n_eval, "n_classes": len(eval_texts),
               "protocol": "LoRA fine-tuning on a local dataset; transfer evaluated on the frozen ImageNet-5k holdout; "
                           "text variant = text tower only, both variant = text and vision towers",
               "runs": {}}
    corr = {}
    if os.path.exists(OUT):
        try:
            payload["runs"] = json.load(io.open(OUT, encoding="utf-8")).get("runs", {})
        except Exception:
            pass
    if os.path.exists(CORR):
        try:
            corr = dict(np.load(CORR))
        except Exception:
            corr = {}

    for spec in a.datasets:
        tr_pil, tr_y, cls_names, tpl = load_train_dataset(spec, a.n_train)
        tr_texts = [tpl.format(c) for c in cls_names]
        train_img_frozen = image_emb(base_model, tr_pil)
        print(f"  [{spec}] train images={len(tr_pil)} classes={len(cls_names)}", flush=True)
        for tower in a.towers:
            for seed in a.seeds:
                key = f"{spec}|{tower}|seed{seed}"
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
                n_lora = len(params)
                opt = torch.optim.AdamW(params, lr=1e-3 if tower == "text" else 5e-4)
                rng = np.random.RandomState(seed)
                ckpts = []
                print(f"  [{key}] LoRA tensors={n_lora}", flush=True)
                for ep in range(1, a.epochs + 1):
                    model.train()
                    order = rng.permutation(len(tr_pil))
                    tot, nb = 0.0, 0
                    for i in range(0, len(order), a.batch):
                        sel = order[i:i + a.batch]
                        ti = proc(text=tr_texts, return_tensors="pt", padding=True).to(device)
                        o = model.text_model(**ti)
                        pooled = o[1] if isinstance(o, tuple) else o.pooler_output
                        te = F.normalize(model.text_projection(pooled).float(), dim=-1)   # [C, d]
                        lab = torch.tensor(tr_y[sel], device=device)
                        if tower == "text":
                            ie = train_img_frozen[sel]
                        else:
                            inp = proc(images=[tr_pil[j] for j in sel], return_tensors="pt").to(device)
                            v = model.vision_model(**inp)
                            pooled_v = v[1] if isinstance(v, tuple) else v.pooler_output
                            ie = F.normalize(model.visual_projection(pooled_v).float(), dim=-1)
                        logits = ie @ te.T                                                 # [B, C]
                        loss = F.cross_entropy(logits, lab)
                        opt.zero_grad()
                        loss.backward()
                        opt.step()
                        tot += float(loss.item())
                        nb += 1
                    model.eval()
                    ev_img = eval_img_frozen if tower == "text" else image_emb(model, eval_pil)
                    ev_txt = text_emb(model, eval_texts)
                    sn = (ev_img @ ev_txt.T).float().cpu().numpy()
                    pred = sn.argmax(1)
                    correct = (pred == eval_labels)
                    top1 = float(correct.mean() * 100)
                    rows = np.arange(n_eval)
                    true_s = sn[rows, eval_labels]
                    s = sn.copy()
                    s[rows, eval_labels] = -1e9
                    margin = true_s - s.max(1)
                    mu_i = ev_img.mean(0)
                    mu_t = ev_txt.mean(0)
                    cg = float((mu_t - mu_i).norm().item())
                    taus = []
                    for i in range(n_eval):
                        r1 = frozen_scores[i, top5[i]]
                        r2 = sn[i, top5[i]]
                        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                            continue
                        t, _ = st.kendalltau(r1, r2)
                        if np.isfinite(t):
                            taus.append(t)
                    entry = {"epoch": ep, "train_loss": tot / max(nb, 1), "top1": top1, "CG": cg,
                             "tau5": float(np.mean(taus)) if taus else None}
                    for e in EPS:
                        entry["mass_%g" % e] = float((margin <= 2 * e).mean())
                    ckpts.append(entry)
                    corr[f"{key}|ep{ep}"] = correct.astype(np.uint8)
                    print(f"   [{key}] ep{ep} top1={top1:.2f} CG={cg:.4f} tau={entry['tau5']:.3f} "
                          f"M01={entry['mass_0.01']:.3f}", flush=True)
                payload["runs"][key] = {"dataset": spec, "tower": tower, "seed": seed,
                                        "n_train": len(tr_pil), "n_classes": len(cls_names),
                                        "checkpoints": ckpts}
                if a.apply:
                    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(payload, indent=1))
                    np.savez_compressed(CORR, **corr)
                    print("   saved", flush=True)
    if a.apply:
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
