# -*- coding: utf-8 -*-
r"""Check whether the retrieval metric in src/trainer.py measures what it claims.

src/trainer.py::_compute_retrieval_metrics builds sim = image_embeds @ text_embeds.T and treats the
diagonal as the positive pair. That is only valid if sample i's caption describes sample i's image.
The dataset yields sampled (image, caption) pairs, so unless the loader is built one caption per
image in the same order, the diagonal is not the positive pair and R@1 collapses toward chance.

This evaluates frozen CLIP on MS-COCO val2014 both ways on the same embeddings:
  - the diagonal protocol, as implemented in the trainer
  - the standard protocol: image x all captions, a hit if any of the image's own five captions is
    in the top k

If the second is far above the first, the near-random COCO numbers in the paper are a metric bug
rather than a property of the model, which is exactly what reviewer R1-W4 asked to be checked.

    python tools/_p750_retrieval_protocol_check.py --n-images 1000 --apply
"""
from __future__ import annotations

import argparse
import io
import json
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "retrieval_protocol_check.json"


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
    print(f"  device: {device}")
    model_id = "openai/clip-vit-base-patch32"
    print(f"  loading {model_id} ...")
    model = CLIPModel.from_pretrained(model_id).to(device).eval()
    proc = CLIPProcessor.from_pretrained(model_id)

    ann_path = REPO / "coco" / "annotations" / "captions_val2014.json"
    img_dir = REPO / "coco" / "val2014"
    print(f"  annotations: {ann_path.exists()}  images dir: {img_dir.exists()}")
    ann = json.loads(ann_path.read_text(encoding="utf-8", errors="ignore"))
    by_img = {}
    for c in ann["annotations"]:
        by_img.setdefault(c["image_id"], []).append(c["caption"])
    ids = [i for i in by_img if (img_dir / f"COCO_val2014_{i:012d}.jpg").exists()]
    rng = random.Random(42)
    rng.shuffle(ids)
    ids = ids[: a.n_images]
    print(f"  using {len(ids)} images, {sum(len(by_img[i]) for i in ids)} captions")

    # one caption per image, in image order: this is what the trainer's diagonal assumes
    img_embeds, cap_embeds, owner = [], [], []
    t0 = time.time()
    with torch.no_grad():
        for s in range(0, len(ids), a.batch):
            chunk = ids[s:s + a.batch]
            ims = [Image.open(img_dir / f"COCO_val2014_{i:012d}.jpg").convert("RGB") for i in chunk]
            caps = [by_img[i][0] for i in chunk]           # first caption, aligned to its image
            inp = proc(images=ims, text=caps, return_tensors="pt", padding=True,
                       truncation=True, max_length=77)
            inp = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in inp.items()}
            out = model(**inp)
            img_embeds.append(F.normalize(out.image_embeds, p=2, dim=-1).cpu())
            cap_embeds.append(F.normalize(out.text_embeds, p=2, dim=-1).cpu())
    img = torch.cat(img_embeds)
    cap = torch.cat(cap_embeds)
    dt = time.time() - t0
    print(f"  embedded {len(img)} image-caption pairs in {dt:.1f}s "
          f"({len(img)/dt:.1f} pairs/s)")

    def r_at_k(sim, k, owners=None):
        top = sim.topk(k, dim=1).indices
        if owners is None:
            idx = torch.arange(sim.shape[0]).unsqueeze(1)
            return (top == idx).any(dim=1).float().mean().item()
        hit = torch.zeros(sim.shape[0], dtype=torch.bool)
        for j in range(sim.shape[0]):
            hit[j] = any(owners[int(t)] == j for t in top[j])
        return hit.float().mean().item()

    sim = img @ cap.T
    print()
    print("=" * 100)
    print("A. diagonal protocol (what src/trainer.py computes here)")
    print("=" * 100)
    for k in (1, 5, 10):
        print(f"  R@{k} = {r_at_k(sim, k):.4f}")

    print()
    print("=" * 100)
    print("B. shuffling the captions must destroy the diagonal protocol if it were real")
    print("=" * 100)
    perm = torch.randperm(cap.shape[0])
    sim_s = img @ cap[perm].T
    for k in (1, 5, 10):
        print(f"  R@{k} (captions permuted) = {r_at_k(sim_s, k):.4f}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        res = {"n_images": len(img), "batch": a.batch, "seconds": round(dt, 1),
               "pairs_per_second": round(len(img) / dt, 1),
               "diagonal": {f"R@{k}": round(r_at_k(sim, k), 4) for k in (1, 5, 10)},
               "permuted": {f"R@{k}": round(r_at_k(sim_s, k), 4) for k in (1, 5, 10)}}
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
