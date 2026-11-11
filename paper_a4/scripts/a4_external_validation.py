# -*- coding: utf-8 -*-
"""A4 external validation with public vision-only CLIP LoRA adapters."""
from __future__ import annotations
import argparse, gc, glob, io, json, os, sys
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "paper_a4", "scripts"))
from a4_controlled_peft import load_dataset, metrics_for, transform
from a4_extra_retrieval import load_caption, metrics_caption, transform_caption

ADAPTERS = {
    "dtd": "clip-vit-base-patch16_dtd_lora-16",
    "sun397": "clip-vit-base-patch16_sun397_lora-16",
    "stanford-cars": "clip-vit-base-patch16_stanford-cars_lora-16",
    "eurosat": "clip-vit-base-patch16_eurosat_lora-16",
}
OUTDIR = os.path.join(REPO, "outputs", "a4", "extra", "external")


def l2(x):
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(n, 1e-12)


def env_split(vision, text_model, proc, pil, texts, device, batch=48):
    import torch
    imgs, txts = [], []
    with torch.no_grad():
        for i in range(0, len(pil), batch):
            inp = proc(images=pil[i:i + batch], return_tensors="pt").to(device)
            o = vision(pixel_values=inp["pixel_values"])
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            imgs.append(torch.nn.functional.normalize(text_model.visual_projection(pooled).float(), dim=-1).cpu().numpy())
        for i in range(0, len(texts), 64):
            inp = proc(text=texts[i:i + 64], return_tensors="pt", padding=True, truncation=True, max_length=77).to(device)
            o = text_model.text_model(input_ids=inp["input_ids"], attention_mask=inp["attention_mask"])
            pooled = o[1] if isinstance(o, tuple) else o.pooler_output
            txts.append(torch.nn.functional.normalize(text_model.text_projection(pooled).float(), dim=-1).cpu().numpy())
    return np.concatenate(imgs, 0), np.concatenate(txts, 0)


def base_caption(proc, base, pil, texts, device):
    import torch
    imgs, txts = [], []
    with torch.no_grad():
        for i in range(0, len(pil), 48):
            inp = proc(images=pil[i:i + 48], return_tensors="pt").to(device)
            z = base.get_image_features(pixel_values=inp["pixel_values"])
            if hasattr(z, "pooler_output"): z = z.pooler_output
            imgs.append(torch.nn.functional.normalize(z.float(), dim=-1).cpu().numpy())
        for i in range(0, len(texts), 64):
            inp = proc(text=texts[i:i + 64], return_tensors="pt", padding=True, truncation=True, max_length=77).to(device)
            z = base.get_text_features(input_ids=inp["input_ids"], attention_mask=inp["attention_mask"])
            if hasattr(z, "pooler_output"): z = z.pooler_output
            txts.append(torch.nn.functional.normalize(z.float(), dim=-1).cpu().numpy())
    return np.concatenate(imgs, 0), np.concatenate(txts, 0)


def eval_class(model, proc, te, te_y, classes, tpl, device):
    texts = [tpl.format(c.replace("_", " ")) for c in classes]
    if hasattr(model, "get_image_features"):
        img, txt = base_caption(proc, model, te, texts, device)
    else:
        img, txt = env_split(model["vision"], model["base"], proc, te, texts, device)
    out = {}
    for mode in ("original", "mean_center", "gap_project", "random_project"):
        a, b = transform(img, txt, mode); out[mode] = metrics_for(a, b, te_y)
    return out


def eval_caption(model, proc, te, te_txt, device):
    if hasattr(model, "get_image_features"):
        img, txt = base_caption(proc, model, te, te_txt, device)
    else:
        img, txt = env_split(model["vision"], model["base"], proc, te, te_txt, device)
    out = {}
    for mode in ("original", "mean_center", "gap_project", "random_project"):
        a, b = transform_caption(img, txt, mode); out[mode] = metrics_caption(a, b)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapters", default="dtd,sun397,stanford-cars,eurosat")
    ap.add_argument("--datasets", default="dtd,inat,nksid,coco5k,flickr30k")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    import torch
    from peft import PeftModel
    from transformers import CLIPModel, CLIPProcessor
    device = "cuda"; local = os.path.join(REPO, "models", "clip-vit-base-patch16")
    proc = CLIPProcessor.from_pretrained(local, local_files_only=True)
    for ds in [x for x in a.datasets.split(",") if x]:
        if ds in ("dtd", "inat", "nksid"):
            _, _, te, te_y, classes, tpl = load_dataset(ds); kind = "class"; te_txt = None
        else:
            te, te_txt = load_caption(ds)[2:]; kind = "caption"
        for ad in [x for x in a.adapters.split(",") if x]:
            outpath = os.path.join(OUTDIR, "%s__%s.json" % (ad, ds))
            if os.path.exists(outpath): print("SKIP", ad, ds, flush=True); continue
            b0 = CLIPModel.from_pretrained(local, local_files_only=True).to(device).eval()
            b = eval_class(b0, proc, te, te_y, classes, tpl, device) if kind == "class" else eval_caption(b0, proc, te, te_txt, device)
            b1 = CLIPModel.from_pretrained(local, local_files_only=True).to(device)
            peft_vis = PeftModel.from_pretrained(b1.vision_model, os.path.join(REPO, "models", "peft_public", ADAPTERS[ad])).to(device).eval()
            model = {"vision": peft_vis, "base": b1}
            e = eval_class(model, proc, te, te_y, classes, tpl, device) if kind == "class" else eval_caption(model, proc, te, te_txt, device)
            payload = {"adapter": ad, "dataset": ds, "kind": kind, "base": b, "adapted": e,
                       "base_model": "openai/clip-vit-base-patch16", "adapter_type": "vision-tower LoRA r16"}
            os.makedirs(OUTDIR, exist_ok=True); json.dump(payload, io.open(outpath, "w", encoding="utf-8"), indent=1)
            print("DONE", ad, ds, "CG base %.3f adapted %.3f" % (b["original"]["CG"], e["original"]["CG"]), flush=True)
            del b0, b1, peft_vis; gc.collect(); torch.cuda.empty_cache()
    files = sorted(glob.glob(os.path.join(OUTDIR, "*.json")))
    rows = [json.load(io.open(f, encoding="utf-8")) for f in files]
    json.dump({"n_cells": len(rows), "cells": rows}, io.open(os.path.join(OUTDIR, "summary.json"), "w", encoding="utf-8"), indent=1)
    print("SUMMARY", len(rows), flush=True)


if __name__ == "__main__":
    main()
