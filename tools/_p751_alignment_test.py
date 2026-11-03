# -*- coding: utf-8 -*-
r"""Measure how far the paper's COCO retrieval numbers move when the alignment is corrected.

The loader builds one sample per caption, so a run over max_samples captions covers only
max_samples/5 distinct images and repeats each image across several rows. The trainer's metric
treats row i's caption as row i's positive, which is false for every row but one per image.

This compares, on the same COCO val images and the same frozen CLIP:
  A. the loader's convention: rows are caption-samples, diagonal treated as positive
  B. row-to-own-image: a hit if any row's caption ranks its own image highest
  C. one row per image, first caption aligned: the protocol that gave R@1 = 0.573

If B is close to C and A is near zero, the paper's COCO numbers are a measurement artefact.

    python tools/_p751_alignment_test.py --n-images 1000 --apply
"""
from __future__ import annotations

import argparse
import io
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "alignment_test.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-images", type=int, default=1000)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F
    from PIL import Image
    from transformers import CLIPModel, CLIPProcessor

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_id = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_id).to(device).eval()
    proc = CLIPProcessor.from_pretrained(model_id)

    def feats(x):
        """get_image_features / get_text_features may return an output object in this version."""
        if not torch.is_tensor(x):
            for attr in ("image_embeds", "text_embeds", "pooler_output", "last_hidden_state"):
                if hasattr(x, attr):
                    return getattr(x, attr)
            raise TypeError(type(x))
        return x

    ann = json.loads((REPO / "coco" / "annotations" / "captions_val2014.json").read_text(
        encoding="utf-8", errors="ignore"))
    img_dir = REPO / "coco" / "val2014"
    by_img = defaultdict(list)
    for c in ann["annotations"]:
        by_img[c["image_id"]].append(c["caption"])
    ids = [i for i in by_img if (img_dir / f"COCO_val2014_{i:012d}.jpg").exists()]
    rng = random.Random(42)
    rng.shuffle(ids)
    ids = ids[: a.n_images]

    # replicate the loader: one row per caption, then max_samples truncation
    rows = []
    for i in ids:
        for cap in by_img[i]:
            rows.append((i, cap))
    print(f"  {len(ids)} images -> {len(rows)} caption rows (the loader would truncate here)")

    # embed images once
    img_emb = {}
    t0 = time.time()
    with torch.no_grad():
        for s in range(0, len(ids), a.batch):
            chunk = ids[s:s + a.batch]
            ims = [Image.open(img_dir / f"COCO_val2014_{i:012d}.jpg").convert("RGB") for i in chunk]
            inp = proc(images=ims, return_tensors="pt")
            inp = {k: v.to(device) for k, v in inp.items()}
            out = F.normalize(feats(model.get_image_features(**inp)), p=2, dim=-1).cpu()
            for j, i in enumerate(chunk):
                img_emb[i] = out[j]
    # embed every caption row
    txt_emb = []
    with torch.no_grad():
        for s in range(0, len(rows), a.batch):
            caps = [c for _, c in rows[s:s + a.batch]]
            inp = proc(text=caps, return_tensors="pt", padding=True, truncation=True,
                       max_length=77)
            inp = {k: v.to(device) for k, v in inp.items()}
            out = model.get_text_features(**inp)
            txt_emb.append(F.normalize(feats(out), p=2, dim=-1).cpu())
    txt = torch.cat(txt_emb)
    dt = time.time() - t0
    print(f"  embedded in {dt:.1f}s")

    I = torch.stack([img_emb[i] for i in ids])              # (n_images, d)
    row_owner = torch.tensor([ids.index(i) for i, _ in rows])  # row -> image index

    print()
    print("=" * 100)
    print("A. the loader's convention: every caption row carries its own image embedding,")
    print("   and the diagonal (row j caption vs row j image) is treated as the positive")
    print("=" * 100)
    S2 = torch.stack([img_emb[rows[j][0]] for j in range(len(rows))]) @ txt.T
    for k in (1, 5, 10):
        top = S2.topk(k, dim=1).indices
        diag = torch.arange(len(rows)).unsqueeze(1)
        print(f"  R@{k} = {(top == diag).any(dim=1).float().mean().item():.4f}")

    print()
    print("=" * 100)
    print("B. image -> its own captions: a hit if any of the image's own captions is top-k")
    print("=" * 100)
    S = I @ txt.T                                            # (n_images, n_rows)
    for k in (1, 5, 10):
        top = S.topk(k, dim=1).indices                       # top caption rows per image
        correct = 0
        for i in range(S.shape[0]):
            if any(int(row_owner[t]) == i for t in top[i]):
                correct += 1
        print(f"  R@{k} = {correct / S.shape[0]:.4f}")

    print()
    print("=" * 100)
    print("C. one row per image, first caption aligned (the clean protocol)")
    print("=" * 100)
    idxs, seen = [], set()
    for j, (i, cap) in enumerate(rows):
        if i not in seen and cap == by_img[i][0]:
            idxs.append(j)
            seen.add(i)
    S3 = I @ txt[idxs].T
    for k in (1, 5, 10):
        top = S3.topk(k, dim=1).indices
        diag = torch.arange(S3.shape[0]).unsqueeze(1)
        print(f"  R@{k} = {(top == diag).any(dim=1).float().mean().item():.4f}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"n_images": len(ids), "n_rows": len(rows),
                                   "seconds": round(dt, 1)}, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
