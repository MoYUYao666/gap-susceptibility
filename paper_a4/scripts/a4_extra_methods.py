# -*- coding: utf-8 -*-
"""A4 extra controlled experiments: AdaLoRA/DoRA, SigLIP, retrieval adaptation, rank sensitivity."""
from __future__ import annotations
import argparse, gc, glob, io, json, os, sys, time
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "paper_a4", "scripts"))
from a4_controlled_peft import (BACKBONES, TOWER_TARGETS, load_dataset, metrics_for, transform,
                               encode_images, encode_texts)

SPLIT_SEED = 2026


def get_model(backbone, method, rank, tower, steps):
    from peft import LoraConfig, AdaLoraConfig, get_peft_model
    from transformers import CLIPModel
    local = os.path.join(REPO, BACKBONES[backbone])
    base = CLIPModel.from_pretrained(local, local_files_only=True)
    target = TOWER_TARGETS[tower]
    if method == "lora":
        cfg = LoraConfig(r=rank, lora_alpha=2 * rank, lora_dropout=0.05, bias="none", target_modules=target)
    elif method == "dora":
        cfg = LoraConfig(r=rank, lora_alpha=2 * rank, lora_dropout=0.05, bias="none", target_modules=target, use_dora=True)
    elif method == "adalora":
        cfg = AdaLoraConfig(r=rank, lora_alpha=2 * rank, lora_dropout=0.05, bias="none", target_modules=target,
                            total_step=max(1, steps), init_r=rank)
    else:
        raise ValueError(method)
    return get_peft_model(base, cfg)


def run_method(backbone, dataset, method, rank, seed, epochs, outdir):
    import torch
    from transformers import CLIPProcessor
    key = f"{backbone}__{dataset}__r{rank}__s{seed}__{method}"
    path = os.path.join(outdir, key + ".json")
    if os.path.exists(path): print("SKIP", key, flush=True); return
    local = os.path.join(REPO, BACKBONES[backbone]); device = "cuda"
    torch.manual_seed(seed); np.random.seed(seed); torch.cuda.empty_cache()
    proc = CLIPProcessor.from_pretrained(local, local_files_only=True)
    train_pil, train_y, test_pil, test_y, classes, tpl = load_dataset(dataset)
    texts = [tpl.format(c.replace("_", " ")) for c in classes]
    by_class = {c: [i for i, y in enumerate(train_y) if y == c] for c in range(len(classes))}
    valid = [c for c in range(len(classes)) if by_class[c]]
    n_classes = min(16, len(valid)); steps = max(1, len(train_pil) // n_classes) * epochs
    model = get_model(backbone, method, rank, "both", steps).to(device)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=5e-4)
    steps_ep = max(1, len(train_pil) // n_classes)
    rng = np.random.RandomState(seed)
    payload = {"run": {"backbone": backbone, "dataset": dataset, "rank": rank, "seed": seed, "epochs": epochs,
                       "method": method, "tower": "both", "n_train": len(train_pil), "n_test": len(test_pil),
                       "n_classes": len(classes), "split_seed": SPLIT_SEED, "trainable_tensors": len(params)},
               "epochs": []}
    for ep in range(1, epochs + 1):
        model.train(); losses = []
        for _ in range(steps_ep):
            cs = rng.choice(valid, size=n_classes, replace=False)
            sel = [int(rng.choice(by_class[int(c)])) for c in cs]
            imgs = [train_pil[i] for i in sel]; btexts = [texts[int(c)] for c in cs]
            ii = proc(images=imgs, return_tensors="pt").to(device)
            ti = proc(text=btexts, return_tensors="pt", padding=True, truncation=True, max_length=77).to(device)
            out = model(pixel_values=ii["pixel_values"], input_ids=ti["input_ids"],
                        attention_mask=ti["attention_mask"], return_loss=True)
            loss = out.loss; opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0); opt.step(); losses.append(float(loss.item()))
        model.eval()
        img = encode_images(model, proc, test_pil, device); txt = encode_texts(model, proc, texts, device)
        rec = {"epoch": ep, "train_loss": float(np.mean(losses)), "conditions": {}}
        for mode in ("original", "mean_center", "gap_project", "random_project"):
            a, b = transform(img, txt, mode, seed=seed); rec["conditions"][mode] = metrics_for(a, b, test_y)
        payload["epochs"].append(rec)
        os.makedirs(outdir, exist_ok=True); json.dump(payload, io.open(path, "w", encoding="utf-8"), indent=1)
        print("DONE", key, "ep", ep, "loss %.3f" % np.mean(losses), "CG %.3f" % rec["conditions"]["original"]["CG"], flush=True)
    del model; gc.collect(); torch.cuda.empty_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbones", default="clip-b32,clip-b16")
    ap.add_argument("--datasets", default="dtd,inat,nksid")
    ap.add_argument("--methods", default="adalora,dora")
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--seeds", default="42,43")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--outdir", default=os.path.join(REPO, "outputs", "a4", "extra", "methods"))
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        a.backbones, a.datasets, a.methods, a.seeds, a.epochs = "clip-b32", "dtd", "adalora,dora", "42", 1
        a.outdir = os.path.join(REPO, "outputs", "a4", "extra", "smoke")
    for bb in [x for x in a.backbones.split(",") if x]:
        for ds in [x for x in a.datasets.split(",") if x]:
            for m in [x for x in a.methods.split(",") if x]:
                for sd in [int(x) for x in a.seeds.split(",") if x]:
                    run_method(bb, ds, m, a.rank, sd, a.epochs, a.outdir)
    # merge this directory
    files = sorted(glob.glob(os.path.join(a.outdir, "*.json")))
    runs = [json.load(io.open(f, encoding="utf-8")) for f in files if os.path.basename(f) != "summary.json"]
    if runs:
        json.dump({"n_runs": len(runs), "runs": runs}, io.open(os.path.join(a.outdir, "summary.json"), "w", encoding="utf-8"), indent=1)
        print("SUMMARY", a.outdir, len(runs), flush=True)


if __name__ == "__main__":
    main()
