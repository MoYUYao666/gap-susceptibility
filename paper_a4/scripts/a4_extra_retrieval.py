# -*- coding: utf-8 -*-
"""A4 retrieval-domain PEFT block: LoRA adaptation on COCO-5K and Flickr30K captions."""
from __future__ import annotations
import argparse, gc, glob, io, json, os, sys, time
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "paper_a4", "scripts"))
from a4_features import build_items
from a4_controlled_peft import BACKBONES, encode_images, encode_texts, gap_stats

SPLIT_SEED = 2026


def l2(x):
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(n, 1e-12)


def metrics_caption(img, txt):
    img, txt = l2(img), l2(txt)
    n = len(img); s = img @ txt.T; d = np.diag(s)
    ri = (s > d[:, None]).sum(1) + 1
    rt = (s.T > d[None, :]).sum(0) + 1
    out = {"R1_i2t": float((ri <= 1).mean() * 100), "R1_t2i": float((rt <= 1).mean() * 100),
           "R5_i2t": float((ri <= 5).mean() * 100), "R5_t2i": float((rt <= 5).mean() * 100)}
    out.update(gap_stats(img, txt))
    return out


def transform_caption(img, txt, mode, seed=0):
    img, txt = l2(img.copy()), l2(txt.copy())
    if mode == "original": return img, txt
    if mode == "mean_center": return l2(img - img.mean(0)), l2(txt - txt.mean(0))
    mu_i, mu_t = img.mean(0), txt.mean(0)
    d = mu_i - mu_t if mode == "gap_project" else np.random.RandomState(seed).normal(size=img.shape[1])
    d = d / max(np.linalg.norm(d), 1e-12)
    return l2(img - np.outer(img @ d, d)), l2(txt - np.outer(txt @ d, d))


def load_caption(spec, limit=0):
    from PIL import Image
    items = build_items(spec)
    if limit: items = items[:limit]
    rng = np.random.RandomState(SPLIT_SEED); idx = rng.permutation(len(items))
    k = int(round(len(idx) * 0.7)); tr = idx[:k]; te = idx[k:]
    tr_pil = [Image.open(items[i][0]).convert("RGB") for i in tr]
    tr_txt = [items[i][1] for i in tr]
    te_pil = [Image.open(items[i][0]).convert("RGB") for i in te]
    te_txt = [items[i][1] for i in te]
    return tr_pil, tr_txt, te_pil, te_txt


def run_one(backbone, dataset, seed, epochs, outdir, limit=0):
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import CLIPModel, CLIPProcessor
    key = f"{backbone}__{dataset}__r16__s{seed}"
    path = os.path.join(outdir, key + ".json")
    if os.path.exists(path): print("SKIP", key, flush=True); return
    local = os.path.join(REPO, BACKBONES[backbone]); device = "cuda"
    torch.manual_seed(seed); np.random.seed(seed); torch.cuda.empty_cache()
    proc = CLIPProcessor.from_pretrained(local, local_files_only=True)
    cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
                     target_modules=r"(text_model|vision_model).*\.(q_proj|k_proj|v_proj)$")
    model = get_peft_model(CLIPModel.from_pretrained(local, local_files_only=True), cfg).to(device)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=5e-4)
    tr_pil, tr_txt, te_pil, te_txt = load_caption(dataset, limit)
    steps = max(1, len(tr_pil) // 32)
    payload = {"run": {"backbone": backbone, "dataset": dataset, "rank": 16, "seed": seed, "method": "lora",
                       "tower": "both", "n_train": len(tr_pil), "n_test": len(te_pil), "epochs": epochs,
                       "split_seed": SPLIT_SEED, "task": "caption_retrieval"}, "epochs": []}
    rng = np.random.RandomState(seed)
    for ep in range(1, epochs + 1):
        model.train(); losses = []
        for _ in range(steps):
            sel = rng.choice(len(tr_pil), size=min(32, len(tr_pil)), replace=False)
            ii = proc(images=[tr_pil[i] for i in sel], return_tensors="pt").to(device)
            ti = proc(text=[tr_txt[i] for i in sel], return_tensors="pt", padding=True, truncation=True, max_length=77).to(device)
            out = model(pixel_values=ii["pixel_values"], input_ids=ti["input_ids"], attention_mask=ti["attention_mask"], return_loss=True)
            loss = out.loss; opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0); opt.step(); losses.append(float(loss.item()))
        model.eval()
        img = encode_images(model, proc, te_pil, device); txt = encode_texts(model, proc, te_txt, device)
        rec = {"epoch": ep, "train_loss": float(np.mean(losses)), "conditions": {}}
        for mode in ("original", "mean_center", "gap_project", "random_project"):
            a, b = transform_caption(img, txt, mode, seed=seed); rec["conditions"][mode] = metrics_caption(a, b)
        payload["epochs"].append(rec)
        os.makedirs(outdir, exist_ok=True); json.dump(payload, io.open(path, "w", encoding="utf-8"), indent=1)
        print("DONE", key, "ep", ep, "loss %.3f" % np.mean(losses), "R1i2t %.1f" % rec["conditions"]["original"]["R1_i2t"], flush=True)
    del model; gc.collect(); torch.cuda.empty_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbones", default="clip-b32,clip-b16")
    ap.add_argument("--datasets", default="coco5k,flickr30k")
    ap.add_argument("--seeds", default="42,43")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--outdir", default=os.path.join(REPO, "outputs", "a4", "extra", "retrieval"))
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        a.backbones, a.datasets, a.seeds, a.epochs = "clip-b32", "coco5k", "42", 1
        a.outdir = os.path.join(REPO, "outputs", "a4", "extra", "smoke_retrieval")
    for bb in a.backbones.split(","):
        for ds in a.datasets.split(","):
            for sd in [int(x) for x in a.seeds.split(",") if x]:
                run_one(bb, ds, sd, a.epochs, a.outdir, 100 if a.smoke else 0)
    files = sorted(glob.glob(os.path.join(a.outdir, "*.json")))
    runs = [json.load(io.open(f, encoding="utf-8")) for f in files if os.path.basename(f) != "summary.json"]
    if runs:
        json.dump({"n_runs": len(runs), "runs": runs}, io.open(os.path.join(a.outdir, "summary.json"), "w", encoding="utf-8"), indent=1)
        print("SUMMARY", len(runs), flush=True)


if __name__ == "__main__":
    main()
