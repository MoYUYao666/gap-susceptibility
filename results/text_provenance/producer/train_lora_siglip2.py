# -*- coding: utf-8 -*-
"""LoRA adaptation of SigLIP (2) for the A3 backbone-family check.

Same protocol as train_lora_provenance.py: five provenance arms, same images, same seed, two epochs, adapters only on
the requested tower(s), learnable logit scale, evaluation with one caption per image. The only change is the backbone
family (SigLIP base, 375M parameters, HuggingFace weights) instead of RemoteCLIP ViT-B/32.

Usage
  python train_lora_siglip2.py --corpus corpora/rsicd/subset1000_human.jsonl \
      --images-root data/rsicd --site both --seed 0 --epochs 2 --batch 16 \
      --out-prefix runs/siglip2_1000/human_subset1000_s0
"""
import argparse
import io
import json
import os
import random
import time

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
DEFAULT_MODEL = os.path.join(os.path.dirname(ROOT), "local_runs", "ms_models", "models",
                             "google--siglip2-base-patch16-224", "snapshots", "master")


def as_tensor(out):
    if torch.is_tensor(out):
        return out
    if hasattr(out, "pooler_output"):
        return out.pooler_output
    if hasattr(out, "image_embeds"):
        return out.image_embeds
    return out[0]


def build_model(model_dir, site, device):
    from transformers import AutoProcessor, SiglipModel
    from peft import LoraConfig, get_peft_model

    processor = AutoProcessor.from_pretrained(model_dir)
    model = SiglipModel.from_pretrained(model_dir, dtype=torch.float32)
    for p in model.parameters():
        p.requires_grad_(False)

    names = []
    for name, module in model.named_modules():
        if not isinstance(module, torch.nn.Linear):
            continue
        if module.out_features < 2:
            continue
        if site in ("vision", "both") and name.startswith("vision_model"):
            names.append(name)
        if site in ("text", "both") and name.startswith("text_model"):
            names.append(name)
    if not names:
        raise SystemExit("no linear modules matched site %r" % site)
    model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05, bias="none",
                                             target_modules=names))
    model.trainable_logit_scale = torch.nn.Parameter(torch.tensor(np.log(1 / 0.07), dtype=torch.float32,
                                                                  device=device))
    return model.to(device), processor, names


class Corpus(torch.utils.data.Dataset):
    def __init__(self, rows, images_root, processor, cache=None):
        self.rows = rows
        self.images_root = images_root
        self.processor = processor
        self.cache = cache if cache is not None else {}

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        r = self.rows[idx]
        pixel = self.cache.get(r["image_path"])
        if pixel is None:
            with Image.open(os.path.join(self.images_root, r["image_path"])) as im:
                pixel = self.processor(images=im.convert("RGB"), return_tensors="pt")["pixel_values"][0]
            self.cache[r["image_path"]] = pixel
        tok = self.processor(text=[r["text"]], padding="max_length", truncation=True, return_tensors="pt",
                             max_length=64)
        ids = tok["input_ids"][0]
        mask = tok["attention_mask"][0] if "attention_mask" in tok else torch.ones_like(ids)
        return idx, pixel, ids, mask


def build_cache(rows, images_root, processor):
    cache = {}
    t0 = time.time()
    for i, rel in enumerate(sorted({r["image_path"] for r in rows})):
        with Image.open(os.path.join(images_root, rel)) as im:
            cache[rel] = processor(images=im.convert("RGB"), return_tensors="pt")["pixel_values"][0]
        if (i + 1) % 500 == 0:
            print("  cached %d images (%.1f min)" % (i + 1, (time.time() - t0) / 60), flush=True)
    print("  image cache: %d images in %.1f min" % (len(cache), (time.time() - t0) / 60), flush=True)
    return cache


def retrieval_metrics(image_emb, text_emb):
    image_emb = F.normalize(image_emb, dim=-1)
    text_emb = F.normalize(text_emb, dim=-1)
    logits = image_emb @ text_emb.t()
    n = logits.shape[0]
    labels = torch.arange(n, device=logits.device)
    out = {}
    for k in (1, 5, 10):
        if k > n:
            continue
        out["R@%d_i2t" % k] = round((logits.topk(k, dim=1).indices == labels[:, None]).any(dim=1).float().mean().item(), 4)
        out["R@%d_t2i" % k] = round((logits.t().topk(k, dim=1).indices == labels[:, None]).any(dim=1).float().mean().item(), 4)
    return out


def diagnostics(image_emb, text_emb):
    image_emb = F.normalize(image_emb, dim=-1)
    text_emb = F.normalize(text_emb, dim=-1)
    gap = (image_emb.mean(0) - text_emb.mean(0)).norm().item()
    align = (image_emb - text_emb).pow(2).sum(dim=-1).mean().item()

    def uniform(x):
        d = torch.pdist(x, p=2)
        return torch.log(torch.exp(-2.0 * d.pow(2)).mean()).item()

    return {"modality_gap": round(gap, 4), "alignment": round(align, 4),
            "uniformity_image": round(uniform(image_emb), 4), "uniformity_text": round(uniform(text_emb), 4)}


@torch.no_grad()
def evaluate(model, rows, images_root, processor, device, batch=32, max_eval=1024, cache=None):
    model.eval()
    seen, deduped = set(), []
    for r in rows:
        if r["image_id"] in seen:
            continue
        seen.add(r["image_id"])
        deduped.append(r)
    rows = deduped[:max_eval]
    img_embs, txt_embs = [], []
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        pixels = []
        for r in chunk:
            pixel = cache.get(r["image_path"]) if cache is not None else None
            if pixel is None:
                with Image.open(os.path.join(images_root, r["image_path"])) as im:
                    pixel = processor(images=im.convert("RGB"), return_tensors="pt")["pixel_values"][0]
            pixels.append(pixel)
        toks = processor(text=[r["text"] for r in chunk], padding="max_length", truncation=True,
                         return_tensors="pt", max_length=64)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            ie = as_tensor(model.get_image_features(pixel_values=torch.stack(pixels).to(device)))
            te = as_tensor(model.get_text_features(input_ids=toks["input_ids"].to(device)))
        img_embs.append(F.normalize(ie.float(), dim=-1))
        txt_embs.append(F.normalize(te.float(), dim=-1))
    image_all, text_all = torch.cat(img_embs), torch.cat(txt_embs)
    metrics = retrieval_metrics(image_all, text_all)
    metrics.update(diagnostics(image_all, text_all))
    return metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--images-root", required=True)
    ap.add_argument("--model-dir", default=DEFAULT_MODEL)
    ap.add_argument("--site", default="both", choices=["vision", "text", "both"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--max-pairs", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out-prefix", required=True)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    def resolve(p):
        if os.path.isabs(p):
            return p
        return p if os.path.exists(p) else os.path.join(REPO, p)

    corpus = resolve(args.corpus)
    images_root = resolve(args.images_root)
    rows_all = [json.loads(l) for l in io.open(corpus, encoding="utf-8") if l.strip()]
    by_split = {}
    for r in rows_all:
        by_split.setdefault(r.get("split", ""), []).append(r)
    rows = by_split.get("train") or rows_all
    eval_rows = by_split.get("test") or by_split.get("val")
    if not eval_rows:
        import zlib
        eval_rows = [r for r in rows if zlib.crc32(r["image_id"].encode()) % 5 == 0]
        rows = [r for r in rows if zlib.crc32(r["image_id"].encode()) % 5 != 0]
    if args.max_pairs:
        rows = rows[:args.max_pairs]
    print("corpus %s | rows %d | site %s | seed %d" % (os.path.basename(args.corpus), len(rows), args.site, args.seed),
          flush=True)

    torch.cuda.reset_peak_memory_stats()
    model, processor, targets = build_model(args.model_dir, args.site, device)
    print("adapter modules: %d | example: %s" % (len(targets), targets[0]), flush=True)
    cache = build_cache(rows, images_root, processor)
    ds = Corpus(rows, images_root, processor, cache)
    loader = torch.utils.data.DataLoader(ds, batch_size=args.batch, shuffle=True, num_workers=0,
                                        drop_last=True)
    optim = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=2e-4, weight_decay=0.01)
    scaler = torch.amp.GradScaler("cuda", enabled=False)
    t0 = time.time()
    for epoch in range(args.epochs):
        model.train()
        for step, (idx, pixel, ids, mask) in enumerate(loader):
            pixel, ids, mask = pixel.to(device), ids.to(device), mask.to(device)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                ie = as_tensor(model.get_image_features(pixel_values=pixel))
                te = as_tensor(model.get_text_features(input_ids=ids))
                ie = F.normalize(ie.float(), dim=-1)
                te = F.normalize(te.float(), dim=-1)
                logit_scale = model.trainable_logit_scale.exp().clamp(max=100)
                logits = logit_scale * ie @ te.t()
                labels = torch.arange(logits.shape[0], device=device)
                loss = 0.5 * (F.cross_entropy(logits, labels) + F.cross_entropy(logits.t(), labels))
            optim.zero_grad(set_to_none=True)
            loss.backward()
            optim.step()
            if (step + 1) % 10 == 0:
                print("  epoch %d step %d/%d loss %.4f" % (epoch, step + 1, len(loader), loss.item()), flush=True)
    metrics = evaluate(model, eval_rows, images_root, processor, device, cache=cache)
    peak = torch.cuda.max_memory_allocated() / 1e9
    results = {
        "corpus": corpus, "images_root": images_root, "site": args.site, "seed": args.seed,
        "epochs": args.epochs, "batch": args.batch, "rows": len(rows), "m_backbone": "siglip2-base-patch16-224",
        "lora_targets": targets, "wall_seconds": round(time.time() - t0, 1), "peak_vram_gb": round(peak, 2),
        "metrics": metrics, "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }
    out = args.out_prefix + ".json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    io.open(out, "w", encoding="utf-8", newline="").write(json.dumps(results, indent=1))
    print("wrote", out, "| R@1_i2t", metrics.get("R@1_i2t"), "| gap", metrics.get("modality_gap"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
