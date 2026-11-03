# -*- coding: utf-8 -*-
r"""H4 experiment: does templated text inflate caption-overlap scores without improving retrieval?

Design
  For each provenance arm of one dataset we train the same small caption decoder (GRU over frozen RemoteCLIP image
  features) on that arm's training text, generate captions for the test images, and score them with an in-repository
  CIDEr-Lite (TF-IDF n-gram cosine), BLEU-4 and diversity measures. The decoder and the image encoder are identical
  across arms, so any difference in scores is attributable to the supervision text.

  Reference captions for scoring are the dataset's own human captions (the standard choice), so a templated arm is
  scored against human text it was not trained on - which is exactly the inflation the hypothesis is about.

Outputs
  analysis/captioning_<dataset>.json   per-arm scores
  runs/captioning/<dataset>/<arm>.pt   decoder weights (untracked)

Usage
  python run_captioning.py --dataset rsicd --arms human,templated,segmented,metadata [--limit 20000]
"""
import argparse
import collections
import io
import json
import math
import os
import random
import re
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS = {"rsicd": "data/rsicd", "rsitmd": "data/rsitmd", "nwpu_captions": "data/nwpu_captions",
            "dior_rsvg": "data/dior_rsvg"}
ARMS = ["human", "templated", "segmented", "metadata"]


# ---------------------------------------------------------------- data and features
class CaptionDataset(Dataset):
    def __init__(self, rows, images_root, preprocess):
        self.rows = rows
        self.images_root = images_root
        self.preprocess = preprocess

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        r = self.rows[idx]
        with Image.open(os.path.join(self.images_root, r["image_path"])) as im:
            image = self.preprocess(im.convert("RGB"))
        return image, r["text"], r["image_id"]


@torch.no_grad()
def extract_features(rows, images_root, batch=64):
    import open_clip
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained=os.path.join(ROOT, "models", "RemoteCLIP-ViT-B-32.pt"), precision="fp32", device="cpu")
    model = model.cuda().eval()
    ds = CaptionDataset(rows, images_root, preprocess)
    loader = DataLoader(ds, batch_size=batch, shuffle=False, num_workers=4)
    feats, texts, ids = [], [], []
    for images, batch_texts, image_ids in loader:
        with torch.autocast("cuda", dtype=torch.bfloat16):
            f = model.encode_image(images.cuda())
        feats.append(F.normalize(f.float(), dim=-1).cpu())
        texts.extend(batch_texts)
        ids.extend(image_ids)
    return torch.cat(feats), texts, ids


# ---------------------------------------------------------------- decoder
class CaptionDecoder(nn.Module):
    def __init__(self, vocab_size, feat_dim=512, embed=256, hidden=512):
        super().__init__()
        self.proj = nn.Linear(feat_dim, hidden)
        self.embed = nn.Embedding(vocab_size, embed, padding_idx=0)
        self.gru = nn.GRU(embed, hidden, batch_first=True)
        self.out = nn.Linear(hidden, vocab_size)

    def forward(self, feats, tokens):
        h0 = self.proj(feats).unsqueeze(0)
        x = self.embed(tokens[:, :-1])
        out, _ = self.gru(x, h0)
        return self.out(out)

    @torch.no_grad()
    def generate(self, feats, tokenizer_vocab, inv_vocab, max_len=30, device="cuda"):
        h = self.proj(feats).unsqueeze(0)
        tok = torch.full((feats.shape[0], 1), tokenizer_vocab["<bos>"], device=device)
        outs = []
        state = h
        for _ in range(max_len):
            x = self.embed(tok[:, -1:])
            out, state = self.gru(x, state)
            logits = self.out(out[:, -1])
            tok = logits.argmax(-1, keepdim=True)
            outs.append(tok)
            if (tok == tokenizer_vocab["<eos>"]).all():
                break
        seq = torch.cat(outs, dim=1).cpu().tolist()
        words = []
        for row in seq:
            w = []
            for idx in row:
                if idx == tokenizer_vocab["<eos>"]:
                    break
                w.append(inv_vocab.get(idx, "<unk>"))
            words.append(" ".join(w))
        return words


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def build_vocab(texts, min_count=1):
    counter = collections.Counter()
    for t in texts:
        for w in tokenize(t):
            counter[w] += 1
    words = [w for w, c in counter.most_common() if c >= min_count]
    vocab = {"<pad>": 0, "<bos>": 1, "<eos>": 2, "<unk>": 3}
    for w in words:
        vocab[w] = len(vocab)
    inv = {i: w for w, i in vocab.items()}
    return vocab, inv


# ---------------------------------------------------------------- metrics
def cider_lite(refs, cands, n=4):
    """TF-IDF n-gram cosine with average pairwise similarity, the TF-IDF variant of CIDEr (Vedantam et al. 2015)."""
    def ngrams(text, k):
        toks = tokenize(text)
        return [tuple(toks[i:i + k]) for i in range(len(toks) - k + 1)]

    docs = {k: collections.Counter() for k in range(1, n + 1)}
    for caps in refs.values():
        for cap in caps:
            for k in range(1, n + 1):
                docs[k].update(ngrams(cap, k))
    df = {k: collections.Counter() for k in range(1, n + 1)}
    for k in range(1, n + 1):
        for g in set(docs[k]):
            df[k][g] += sum(1 for caps in refs.values() for cap in caps if g in ngrams(cap, k))
    total_docs = sum(len(caps) for caps in refs.values())
    idf = {k: {g: math.log(max(1, total_docs) / c) for g, c in df[k].items()} for k in range(1, n + 1)}

    def vec(text):
        v = {}
        for k in range(1, n + 1):
            for g in ngrams(text, k):
                v[g] = v.get(g, 0) + idf[k].get(g, 0.0)
        return v

    def cosine(a, b):
        keys = set(a) | set(b)
        num = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
        da = math.sqrt(sum(v * v for v in a.values()))
        db = math.sqrt(sum(v * v for v in b.values()))
        return num / (da * db) if da and db else 0.0

    scores = []
    for image_id, cap in cands.items():
        ref_vecs = [vec(r) for r in refs.get(image_id, [])]
        cand_vec = vec(cap)
        if not ref_vecs:
            continue
        scores.append(sum(cosine(cand_vec, r) for r in ref_vecs) / len(ref_vecs))
    return float(np.mean(scores)) if scores else 0.0


def bleu4(refs, cands):
    def ngrams(tokens, k):
        return collections.Counter(tuple(tokens[i:i + k]) for i in range(len(tokens) - k + 1))

    precisions, totals = [], []
    for image_id, cand in cands.items():
        refs_tok = [tokenize(r) for r in refs.get(image_id, [])]
        cand_tok = tokenize(cand)
        if not refs_tok:
            continue
        p = []
        for k in range(1, 5):
            c_grams = ngrams(cand_tok, k)
            max_ref = collections.Counter()
            for r in refs_tok:
                for g, c in ngrams(r, k).items():
                    max_ref[g] = max(max_ref[g], c)
            clipped = sum(min(c, max_ref[g]) for g, c in c_grams.items())
            p.append(clipped / max(1, sum(c_grams.values())))
        bp = min(1.0, math.exp(1 - sum(len(r) for r in refs_tok) / max(1, 4 * len(cand_tok))))
        precisions.append(p)
        totals.append(bp)
    if not precisions:
        return 0.0
    logs = np.mean(np.log([max(1e-9, p) for p in np.array(precisions).mean(axis=0)]))
    return float(np.mean(totals) * math.exp(logs))


def distinct_n(texts, n=4):
    grams = set()
    total = 0
    for t in texts:
        toks = tokenize(t)
        g = [tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)]
        grams.update(g)
        total += len(g)
    return len(grams) / total if total else 0.0


# ---------------------------------------------------------------- experiment
def run_arm(dataset, arm, limit, epochs=3, device="cuda"):
    images_root = os.path.join(ROOT, DATASETS[dataset])
    corpus_path = os.path.join(ROOT, "corpora", dataset, "budgets", "%s_10000_pairs.jsonl" % arm)
    if not os.path.exists(corpus_path):
        corpus_path = os.path.join(ROOT, "corpora", dataset, arm + ".jsonl")
    rows = [json.loads(l) for l in io.open(corpus_path, encoding="utf-8") if l.strip()]
    train_rows = [r for r in rows if r["split"] == "train"][:limit]
    test_rows = [r for r in rows if r["split"] == "test"][:200] or rows[-200:]

    feats, texts, ids = extract_features(train_rows, images_root)
    vocab, inv = build_vocab(texts)
    tokens = [[1] + [vocab.get(w, 3) for w in tokenize(t)] + [2] for t in texts]
    max_len = max(len(t) for t in tokens)
    padded = torch.zeros(len(tokens), max_len, dtype=torch.long)
    for i, t in enumerate(tokens):
        padded[i, :len(t)] = torch.tensor(t[:max_len])

    model = CaptionDecoder(len(vocab)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3)
    feats_dev = feats.to(device)
    for epoch in range(epochs):
        perm = torch.randperm(len(texts))
        total = 0.0
        for i in range(0, len(texts), 64):
            idx = perm[i:i + 64]
            logits = model(feats_dev[idx], padded[idx].to(device))
            targets = padded[idx, 1:].to(device)
            loss = F.cross_entropy(logits.reshape(-1, len(vocab)), targets.reshape(-1), ignore_index=0)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            total += loss.item() * len(idx)
        print("  %s epoch %d loss %.3f" % (arm, epoch, total / len(texts)), flush=True)

    # generate on test images; score against the arm's own references and against human references.
    # The first measures the within-corpus score the literature reports, the second measures whether the text
    # transfers; comparing the two is what separates "template inflation" from "a genuinely good captioner".
    refs = {}
    for r in test_rows:
        refs.setdefault(r["image_id"], []).append(r["text"])
    human_path = os.path.join(ROOT, "corpora", dataset, "budgets", "human_10000_pairs.jsonl")
    if not os.path.exists(human_path):
        human_path = os.path.join(ROOT, "corpora", dataset, "human.jsonl")
    human_rows = [json.loads(l) for l in io.open(human_path, encoding="utf-8") if l.strip()]
    human_test_ids = {r["image_id"] for r in test_rows}
    human_refs = {}
    for r in human_rows:
        if r["image_id"] in human_test_ids or len(human_refs) < 5:
            human_refs.setdefault(r["image_id"], []).append(r["text"])
    test_feats, _, test_ids = extract_features(test_rows, images_root)
    gen = model.generate(test_feats.to(device), vocab, inv)
    cands = dict(zip(test_ids, gen))
    scores = {
        "arm": arm, "dataset": dataset, "n_train": len(train_rows), "n_test": len(test_rows),
        "cider_lite": round(cider_lite(refs, cands), 4),
        "bleu4": round(bleu4(refs, cands), 4),
        "cider_vs_human": round(cider_lite(human_refs, cands), 4),
        "bleu4_vs_human": round(bleu4(human_refs, cands), 4),
        "distinct4": round(distinct_n([c for c in cands.values()]), 4),
        "template_token_share": round(template_share([c for c in cands.values()]), 4),
        "sample_captions": [cands[k] for k in list(cands)[:5]],
    }
    return scores


TEMPLATE_WORDS = {"the", "a", "an", "is", "are", "there", "in", "of", "this", "image", "remote", "sensing",
                  "scene", "located", "part", "objects", "visible", "pixel", "size", "aspect", "ratio",
                  "brightness", "mean", "classes", "and", "with", "on", "by", "at", "to", "recorded", "shows"}


def template_share(captions):
    toks = [w for c in captions for w in tokenize(c)]
    if not toks:
        return 0.0
    return sum(1 for w in toks if w in TEMPLATE_WORDS) / len(toks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="rsicd")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--limit", type=int, default=20000)
    args = ap.parse_args()
    out_dir = os.path.join(ROOT, "runs", "captioning", args.dataset)
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for arm in [a.strip() for a in args.arms.split(",") if a.strip()]:
        print("==", arm, flush=True)
        scores = run_arm(args.dataset, arm, args.limit)
        results.append(scores)
        io.open(os.path.join(out_dir, arm + ".json"), "w", encoding="utf-8", newline="").write(
            json.dumps(scores, indent=1))
    os.makedirs(os.path.join(ROOT, "analysis"), exist_ok=True)
    io.open(os.path.join(ROOT, "analysis", "captioning_%s.json" % args.dataset), "w", encoding="utf-8",
            newline="").write(json.dumps({"dataset": args.dataset, "arms": results}, indent=1))
    print(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
