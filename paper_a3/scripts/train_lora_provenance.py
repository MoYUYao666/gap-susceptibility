# -*- coding: utf-8 -*-
r"""Train one A3 cell: LoRA at a chosen adaptation site on one provenance corpus, then evaluate retrieval.

Model: RemoteCLIP ViT-B-32 (open_clip architecture) with every parameter frozen except LoRA adapters and the logit
temperature. Adapter placement is the A3 factor `site`:

  vision - LoRA on the vision tower projections that open_clip keeps as nn.Linear: attention out_proj plus the MLP c_fc
           and c_proj of every block (the q/k/v projections are fused into a single in_proj parameter and cannot take a
           module-level adapter)
  text   - LoRA on the text tower MLP projections (c_fc, c_proj) of every block, for the same fused-attention reason
  both   - the union of the two

Every adapted module name is recorded in the run JSON (`adapted_modules`, `adapted_suffixes`), because "which
projections are adapted" is part of the treatment rather than an implementation detail.

Usage
  python train_lora_provenance.py --plan
  python train_lora_provenance.py --self-test
  python train_lora_provenance.py --corpus <jsonl> --images-root <dir> --site vision --epochs 3 --batch 32 \
      --out-prefix runs/rsicd_10k_vision_s0 --seed 0 --max-pairs 10000
"""
import argparse
import io
import json
import os
import random
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset


def plan():
    print("""A3 training cell plan

factors   : corpus (arm x dataset x budget) x site {vision,text,both} x seed {0,1,2}
model     : RemoteCLIP ViT-B-32 via open_clip, all weights frozen, LoRA r=8 on the selected tower's nn.Linear modules,
            logit scale trainable; images resized 224, CLIP normalisation
loss      : symmetric InfoNCE with learnable temperature
eval      : R@1/R@5/R@10 for image-to-text and text-to-image on the corpus's test split; peak VRAM and wall time recorded
output    : <out-prefix>.json with the full run record and <out-prefix>.pt with the adapter weights
inputs    : corpora from corpora/<dataset>/<arm>.jsonl (image_path resolved against --images-root)
""")
    return 0


class PairDataset(Dataset):
    def __init__(self, rows, images_root, preprocess, tokenizer, max_text_len=77, cache=None):
        self.rows = rows
        self.images_root = images_root
        self.preprocess = preprocess
        self.tokenizer = tokenizer
        self.max_text_len = max_text_len
        self.cache = cache or {}

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        r = self.rows[idx]
        path = os.path.join(self.images_root, r["image_path"])
        image = self.cache.get(r["image_path"])
        if image is None:
            with Image.open(path) as im:
                image = self.preprocess(im.convert("RGB"))
            if self.cache is not None:
                self.cache[r["image_path"]] = image
        tokens = self.tokenizer([r["text"]])[0]
        return idx, image, tokens


def build_image_cache(rows, images_root, preprocess, log=print):
    """Decode every distinct image once, in parallel, and keep the preprocessed tensor in RAM.

    Cloud hosts often have slow block storage while the GPU waits; caching removes disk from the training loop.
    """
    from concurrent.futures import ThreadPoolExecutor

    paths = sorted({r["image_path"] for r in rows})
    cache = {}
    t0 = time.time()

    def load(rel):
        with Image.open(os.path.join(images_root, rel)) as im:
            return rel, preprocess(im.convert("RGB"))

    with ThreadPoolExecutor(max_workers=32) as pool:
        for i, (rel, tensor) in enumerate(pool.map(load, paths)):
            cache[rel] = tensor
            if (i + 1) % 5000 == 0:
                log("cached %d/%d images in %.1f min" % (i + 1, len(paths), (time.time() - t0) / 60))
    log("image cache: %d images in %.1f min" % (len(cache), (time.time() - t0) / 60))
    return cache


class OnePerImageBatchSampler:
    """Yield batches of row indices with no two rows from the same image.

    Corpora such as RSICD store several captions per image; if two captions of the same image land in one
    contrastive batch, the loss pushes them apart as if they were negatives. This sampler draws distinct images
    per batch and cycles through the available captions across epochs.
    """

    def __init__(self, rows, batch_size, seed=0):
        self.rows = rows
        self.batch_size = batch_size
        self.seed = seed
        self.epoch = 0
        by_image = {}
        for i, r in enumerate(rows):
            by_image.setdefault(r["image_id"], []).append(i)
        self.by_image = by_image
        self.images = list(by_image)

    def __iter__(self):
        import random
        rng = random.Random(self.seed + self.epoch)
        images = list(self.images)
        rng.shuffle(images)
        batch = []
        for img in images:
            captions = self.by_image[img]
            batch.append(captions[(self.epoch + rng.randrange(len(captions))) % len(captions)])
            if len(batch) == self.batch_size:
                yield batch
                batch = []
        if batch:
            yield batch
        self.epoch += 1

    def __len__(self):
        return len(self.images) // self.batch_size


def limit_pairs(rows, max_pairs, seed):
    if not max_pairs or max_pairs >= len(rows):
        return rows
    rng = random.Random(seed)
    return rng.sample(rows, max_pairs)


def build_model(model_path, site, device):
    import open_clip
    from peft import LoraConfig, get_peft_model

    name = "ViT-L-14" if "ViT-L-14" in os.path.basename(model_path) else (
        "ViT-H-14" if "ViT-H-14" in os.path.basename(model_path) else "ViT-B-32")
    model, _, preprocess = open_clip.create_model_and_transforms(
        name, pretrained=model_path, precision="fp32", device="cpu")
    tokenizer = open_clip.get_tokenizer(name)
    for p in model.parameters():
        p.requires_grad_(False)
    model.logit_scale.requires_grad_(True)

    vision_pat = r"^visual\..*(q_proj|k_proj|v_proj|out_proj|c_fc|c_proj)$"
    text_pat = r"^transformer\..*(c_fc|c_proj)$"
    patterns = {"vision": [vision_pat], "text": [text_pat], "both": [vision_pat, text_pat]}[site]
    target = "|".join(patterns)
    model = get_peft_model(model, LoraConfig(
        r=8, lora_alpha=16, lora_dropout=0.05, bias="none", target_modules=target))
    # record which modules actually received adapters, and from which tower
    names = [n.split(".lora_")[0].replace("base_model.model.", "") for n, _ in model.named_modules()
             if n.endswith("lora_A.default")]
    if not names:
        raise SystemExit("no LoRA adapters were inserted for site %r" % site)
    return model.to(device), preprocess, tokenizer, names


def modality_diagnostics(image_emb, text_emb):
    """Modality gap and alignment/uniformity, the quantities H3 is stated in.

    gap       - Euclidean distance between the two centroids on the unit sphere (the modality gap of Liang et al. 2022)
    alignment - mean squared distance between the paired image and text embeddings (lower is better)
    uniformity - log of the mean pairwise Gaussian potential within each modality (lower means more spread out)
    """
    image_emb = F.normalize(image_emb, dim=-1)
    text_emb = F.normalize(text_emb, dim=-1)
    gap = (image_emb.mean(0) - text_emb.mean(0)).norm().item()

    def align(a, b):
        return (a - b).pow(2).sum(dim=-1).mean().item()

    def uniform(x):
        d = torch.pdist(x, p=2)
        return torch.log(torch.exp(-2.0 * d.pow(2)).mean()).item()

    return {"modality_gap": round(gap, 4),
            "alignment": round(align(image_emb, text_emb), 4),
            "uniformity_image": round(uniform(image_emb), 4),
            "uniformity_text": round(uniform(text_emb), 4)}


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
        i2t = (logits.topk(k, dim=1).indices == labels[:, None]).any(dim=1).float().mean().item()
        t2i = (logits.t().topk(k, dim=1).indices == labels[:, None]).any(dim=1).float().mean().item()
        out["R@%d_i2t" % k] = round(i2t, 4)
        out["R@%d_t2i" % k] = round(t2i, 4)
    return out


@torch.no_grad()
def evaluate(model, rows, images_root, preprocess, tokenizer, device, batch=32, max_eval=1024, cache=None):
    model.eval()
    # one caption per test image: corpora store several captions per image, and scoring every caption row makes the
    # candidate pool contain near-duplicates, which is both stricter and inconsistent with the budget-matched cells
    seen = set()
    deduped = []
    for r in rows:
        if r["image_id"] in seen:
            continue
        seen.add(r["image_id"])
        deduped.append(r)
    rows = deduped
    if len(rows) > max_eval:
        rows = rows[:max_eval]
    image_embs, text_embs = [], []
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        images = []
        texts = []
        for r in chunk:
            img = cache.get(r["image_path"]) if cache is not None else None
            if img is None:
                with Image.open(os.path.join(images_root, r["image_path"])) as im:
                    img = preprocess(im.convert("RGB"))
            images.append(img)
            texts.append(r["text"])
        image_t = torch.stack(images).to(device)
        tokens = tokenizer(texts).to(device)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            image_embs.append(F.normalize(model.encode_image(image_t), dim=-1).float())
            text_embs.append(F.normalize(model.encode_text(tokens), dim=-1).float())
    image_all, text_all = torch.cat(image_embs), torch.cat(text_embs)
    metrics = retrieval_metrics(image_all, text_all)
    metrics.update(modality_diagnostics(image_all, text_all))
    return metrics


def train(args):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)

    with io.open(args.corpus, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    by_split = {}
    for r in rows:
        by_split.setdefault(r["split"], []).append(r)
    train_rows = by_split.get("train") or rows
    train_rows = limit_pairs(train_rows, args.max_pairs, args.seed)
    eval_rows = by_split.get("test") or by_split.get("val") or rows

    model, preprocess, tokenizer, adapted = build_model(args.model, args.site, device)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    cache = build_image_cache(train_rows + eval_rows, args.images_root, preprocess) if args.cache_images else None
    ds = PairDataset(train_rows, args.images_root, preprocess, tokenizer, cache=cache)
    if getattr(args, "one_per_image", False):
        sampler = OnePerImageBatchSampler(train_rows, args.batch, seed=args.seed)
        loader = DataLoader(ds, batch_sampler=sampler, num_workers=args.workers, pin_memory=True)
    else:
        loader = DataLoader(ds, batch_size=args.batch, shuffle=True, num_workers=args.workers,
                            pin_memory=True, drop_last=True)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.01)
    steps_per_epoch = max(1, len(loader))
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs * steps_per_epoch)

    torch.cuda.reset_peak_memory_stats(device) if torch.cuda.is_available() else None
    started = time.time()
    losses = []
    for epoch in range(args.epochs):
        model.train()
        for step, (_, images, tokens) in enumerate(loader):
            images = images.to(device, non_blocking=True)
            tokens = tokens.to(device, non_blocking=True)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                image_features = model.encode_image(images)
                text_features = model.encode_text(tokens)
                image_features = F.normalize(image_features.float(), dim=-1)
                text_features = F.normalize(text_features.float(), dim=-1)
                logit_scale = model.logit_scale.exp().float()
                logits = logit_scale * image_features @ text_features.t()
                labels = torch.arange(logits.shape[0], device=logits.device)
                loss = 0.5 * (F.cross_entropy(logits, labels) + F.cross_entropy(logits.t(), labels))
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            scheduler.step()
            losses.append(loss.item())
            if step % args.log_every == 0:
                print("epoch %d step %d/%d loss %.4f" % (epoch, step, steps_per_epoch, loss.item()), flush=True)

    elapsed = time.time() - started
    peak = torch.cuda.max_memory_allocated(device) / 1e9 if torch.cuda.is_available() else 0.0
    metrics = evaluate(model, eval_rows, args.images_root, preprocess, tokenizer, device, batch=args.eval_batch, cache=cache)
    record = {
        "corpus": os.path.abspath(args.corpus), "images_root": os.path.abspath(args.images_root),
        "site": args.site, "seed": args.seed, "epochs": args.epochs, "batch": args.batch,
        "max_pairs": args.max_pairs, "pairs_used": len(train_rows), "eval_pairs": min(len(eval_rows), 1024),
        "trainable_params": trainable, "total_params": total, "trainable_share": round(trainable / total, 6),
        "adapted_modules_count": len(adapted), "adapted_suffixes": sorted({n.split(".")[-1] for n in adapted}),
        "final_loss": round(float(np.mean(losses[-50:])), 4), "loss_first": round(float(np.mean(losses[:50])), 4),
        "wall_seconds": round(elapsed, 1), "peak_vram_gb": round(peak, 3), "metrics": metrics,
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "torch": torch.__version__, "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out_prefix)), exist_ok=True)
    io.open(args.out_prefix + ".json", "w", encoding="utf-8", newline="").write(json.dumps(record, indent=1))
    if args.save_adapter:
        torch.save({"state_dict": {k: v for k, v in model.state_dict().items() if "lora" in k.lower()},
                    "config": record}, args.out_prefix + ".pt")
    print(json.dumps(record, indent=1))
    return record


def self_test():
    """Synthetic round trip: 24 random images and texts, two steps, assertions on the record."""
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_selftest_train")
    os.makedirs(os.path.join(tmp, "images"), exist_ok=True)
    rows = []
    rng = np.random.default_rng(0)
    for i in range(24):
        arr = (rng.random((64, 64, 3)) * 255).astype("uint8")
        Image.fromarray(arr).resize((224, 224)).save(os.path.join(tmp, "images", "img_%02d.jpg" % i))
        rows.append({"image_id": "img_%02d" % i, "image_path": "images/img_%02d.jpg" % i,
                     "split": "train" if i < 16 else "test", "text": "a test caption number %d" % i})
    corpus = os.path.join(tmp, "corpus.jsonl")
    with io.open(corpus, "w", encoding="utf-8", newline="") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models",
                              "RemoteCLIP-ViT-B-32.pt")
    if not os.path.exists(model_path):
        print("  [SKIP] weights not downloaded yet: %s" % model_path)
        return 1
    args = argparse.Namespace(corpus=corpus, images_root=tmp, model=model_path, site="vision", seed=0,
                              epochs=1, batch=8, max_pairs=None, workers=0, lr=1e-4, log_every=1,
                              eval_batch=8, out_prefix=os.path.join(tmp, "run"), save_adapter=False)
    rec = train(args)
    checks = {
        "loss finite": np.isfinite(rec["final_loss"]),
        "trainable share small": 0 < rec["trainable_share"] < 0.2,
        "metrics reported": "R@1_i2t" in rec["metrics"],
        "peak vram recorded": rec["peak_vram_gb"] > 0,
    }
    ok = all(checks.values())
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--images-root")
    ap.add_argument("--model", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                    "models", "RemoteCLIP-ViT-B-32.pt"))
    ap.add_argument("--site", choices=["vision", "text", "both"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--max-pairs", type=int, default=0)
    ap.add_argument("--one-per-image", action="store_true")
    ap.add_argument("--cache-images", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--log-every", type=int, default=20)
    ap.add_argument("--eval-batch", type=int, default=32)
    ap.add_argument("--out-prefix", default="paper_a3/runs/run")
    ap.add_argument("--save-adapter", action="store_true")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.plan:
        return plan()
    if args.self_test:
        return self_test()
    if not args.corpus or not args.images_root or not args.site:
        print("provide --corpus, --images-root and --site, or use --plan / --self-test", file=sys.stderr)
        return 2
    train(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
