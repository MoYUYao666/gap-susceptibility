# -*- coding: utf-8 -*-
"""A4 non-CLIP architecture check: LoRA adaptation of SigLIP Base."""
from __future__ import annotations
import argparse, gc, glob, io, json, os, sys
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "paper_a4", "scripts"))
from a4_controlled_peft import load_dataset, metrics_for, transform
from a4_features import encode_images as _noop  # noqa: F401  (keeps path import explicit)

SPLIT_SEED = 2026


def l2(x):
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(n, 1e-12)


def enc_images(model, proc, pil, device, batch=32):
    import torch
    out = []
    with torch.no_grad():
        for i in range(0, len(pil), batch):
            inp = proc(images=pil[i:i + batch], return_tensors="pt").to(device)
            z = model.get_image_features(pixel_values=inp["pixel_values"])
            if hasattr(z, "pooler_output"): z = z.pooler_output
            elif hasattr(z, "image_embeds"): z = z.image_embeds
            out.append(torch.nn.functional.normalize(z.float(), dim=-1).cpu().numpy())
    return np.concatenate(out, 0)


def enc_texts(model, proc, texts, device, batch=64):
    import torch
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), batch):
            inp = proc(text=texts[i:i + batch], return_tensors="pt", padding="max_length", truncation=True, max_length=64).to(device)
            ids = inp["input_ids"]
            mask = inp.get("attention_mask", torch.ones_like(ids))
            z = model.get_text_features(input_ids=ids, attention_mask=mask)
            if hasattr(z, "pooler_output"): z = z.pooler_output
            elif hasattr(z, "text_embeds"): z = z.text_embeds
            out.append(torch.nn.functional.normalize(z.float(), dim=-1).cpu().numpy())
    return np.concatenate(out, 0)


def run_one(dataset, seed, epochs, outdir, limit_train=0, limit_test=0):
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModel, AutoProcessor
    key = f"siglip__{dataset}__r16__s{seed}"
    path = os.path.join(outdir, key + ".json")
    if os.path.exists(path): print("SKIP", key, flush=True); return
    local = os.path.join(REPO, "models", "siglip-base-patch16-224"); device = "cuda"
    torch.manual_seed(seed); np.random.seed(seed); torch.cuda.empty_cache()
    proc = AutoProcessor.from_pretrained(local, local_files_only=True)
    base = AutoModel.from_pretrained(local, local_files_only=True)
    cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
                     target_modules=r"(vision_model|text_model).*\.(q_proj|k_proj|v_proj)$")
    model = get_peft_model(base, cfg).to(device)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=5e-4)
    train_pil, train_y, test_pil, test_y, classes, tpl = load_dataset(dataset, limit_train, limit_test)
    texts = [tpl.format(c.replace("_", " ")) for c in classes]
    by_class = {c: [i for i, y in enumerate(train_y) if y == c] for c in range(len(classes))}
    valid = [c for c in range(len(classes)) if by_class[c]]
    n_classes = min(16, len(valid)); steps_ep = max(1, len(train_pil) // n_classes)
    payload = {"run": {"backbone": "siglip", "dataset": dataset, "rank": 16, "seed": seed, "method": "lora",
                       "tower": "both", "n_train": len(train_pil), "n_test": len(test_pil),
                       "n_classes": len(classes), "split_seed": SPLIT_SEED, "trainable_tensors": len(params)},
               "epochs": []}
    rng = np.random.RandomState(seed)
    for ep in range(1, epochs + 1):
        model.train(); losses = []
        for _ in range(steps_ep):
            cs = rng.choice(valid, size=n_classes, replace=False)
            sel = [int(rng.choice(by_class[int(c)])) for c in cs]
            imgs = [train_pil[i] for i in sel]; btexts = [texts[int(c)] for c in cs]
            ii = proc(images=imgs, return_tensors="pt").to(device)
            ti = proc(text=btexts, return_tensors="pt", padding="max_length", truncation=True, max_length=64).to(device)
            mask = ti.get("attention_mask", torch.ones_like(ti["input_ids"]))
            out = model(pixel_values=ii["pixel_values"], input_ids=ti["input_ids"], attention_mask=mask, return_loss=True)
            loss = out.loss; opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0); opt.step(); losses.append(float(loss.item()))
        model.eval()
        img = enc_images(model, proc, test_pil, device); txt = enc_texts(model, proc, texts, device)
        rec = {"epoch": ep, "train_loss": float(np.mean(losses)), "conditions": {}}
        for mode in ("original", "mean_center", "gap_project", "random_project"):
            a, b = transform(img, txt, mode, seed=seed); rec["conditions"][mode] = metrics_for(a, b, test_y)
        payload["epochs"].append(rec)
        os.makedirs(outdir, exist_ok=True); json.dump(payload, io.open(path, "w", encoding="utf-8"), indent=1)
        print("DONE", key, "ep", ep, "loss %.3f" % np.mean(losses), "CG %.3f" % rec["conditions"]["original"]["CG"], flush=True)
    del model, base; gc.collect(); torch.cuda.empty_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", default="dtd,inat,nksid")
    ap.add_argument("--seeds", default="42,43")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--outdir", default=os.path.join(REPO, "outputs", "a4", "extra", "siglip"))
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        a.datasets, a.seeds, a.epochs = "dtd", "42", 1
        a.outdir = os.path.join(REPO, "outputs", "a4", "extra", "smoke_siglip")
    for ds in [x for x in a.datasets.split(",") if x]:
        for sd in [int(x) for x in a.seeds.split(",") if x]:
            run_one(ds, sd, a.epochs, a.outdir, 120 if a.smoke else 0, 60 if a.smoke else 0)
    files = sorted(glob.glob(os.path.join(a.outdir, "*.json")))
    runs = [json.load(io.open(f, encoding="utf-8")) for f in files if os.path.basename(f) != "summary.json"]
    if runs:
        json.dump({"n_runs": len(runs), "runs": runs}, io.open(os.path.join(a.outdir, "summary.json"), "w", encoding="utf-8"), indent=1)
        print("SUMMARY", len(runs), flush=True)


if __name__ == "__main__":
    main()
