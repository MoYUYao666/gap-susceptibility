# -*- coding: utf-8 -*-
r"""End-to-end check of the corrected retrieval metric through the real dataloader.

Runs frozen CLIP over a COCO val subset built by src.dataset.create_dataloaders, in two passes:
  - max_samples = n, so each image contributes exactly one caption row (unambiguous)
  - max_samples = 5n, so each image contributes about five rows (the case that broke the old metric)

Compares the corrected metric against the old diagonal computation on identical embeddings, which
is the evidence needed to say whether the COCO numbers in the paper were a measurement artefact.

    python tools/_p753_e2e_metric_check.py --n 400 --apply
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "e2e_metric_check.json"
sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F
    from transformers import CLIPModel, CLIPProcessor
    from src.dataset import create_dataloaders

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_id = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_id).to(device).eval()
    proc = CLIPProcessor.from_pretrained(model_id)

    results = {}
    for label, ms in (("one caption per image", a.n), ("five captions per image", a.n * 5)):
        _, val_loader, _ = create_dataloaders(
            dataset_name="coco", data_dir=str(REPO), batch_size=64, max_samples=ms,
            pre_tokenize=False, num_workers=0, image_size=224,
        )
        t0 = time.time()
        img_e, txt_e, owners = [], [], []
        with torch.no_grad():
            for batch in val_loader:
                inp = proc(text=batch["caption"], return_tensors="pt", padding=True,
                           truncation=True, max_length=77)
                out = model(pixel_values=batch["image"].to(device),
                            input_ids=inp["input_ids"].to(device),
                            attention_mask=inp["attention_mask"].to(device))
                img_e.append(F.normalize(out.image_embeds, p=2, dim=-1).cpu())
                txt_e.append(F.normalize(out.text_embeds, p=2, dim=-1).cpu())
                owners.extend([str(x) for x in batch["image_path"]])
        I = torch.cat(img_e)
        T = torch.cat(txt_e)
        dt = time.time() - t0
        n_img = len(set(owners))
        n_cap = len(owners)

        # old protocol: diagonal over the flattened rows
        N = min(I.shape[0], T.shape[0])
        S = I[:N] @ T[:N].T
        old = {}
        for k in (1, 5, 10):
            top = S.topk(k, dim=1).indices
            old[k] = (top == torch.arange(N).unsqueeze(1)).any(dim=1).float().mean().item()

        # corrected protocol
        order, first = [], {}
        for j, key in enumerate(owners):
            if key not in first:
                first[key] = j
                order.append(key)
        Iu = I[[first[k] for k in order]]
        oi = {k: i for i, k in enumerate(order)}
        col = torch.tensor([oi[k] for k in owners])
        new = {}
        S2 = Iu @ T.T
        for k in (1, 5, 10):
            top = S2.topk(k, dim=1).indices
            hit = (col[top] == torch.arange(Iu.shape[0]).unsqueeze(1)).any(dim=1)
            new[k] = hit.float().mean().item()

        results[label] = {"rows": n_cap, "unique_images": n_img, "seconds": round(dt, 1),
                          "old": {f"R@{k}": round(v, 4) for k, v in old.items()},
                          "corrected": {f"R@{k}": round(v, 4) for k, v in new.items()}}
        print("=" * 100)
        print(f"{label}   (rows={n_cap}, unique images={n_img}, {dt:.1f}s)")
        print("=" * 100)
        for k in (1, 5, 10):
            print(f"  R@{k}:  old diagonal = {old[k]:.4f}   corrected = {new[k]:.4f}")
        print()

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
