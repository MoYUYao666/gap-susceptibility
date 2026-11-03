# -*- coding: utf-8 -*-
r"""Check whether the image and text embeddings are still aligned at large gallery sizes.

R@1 stays near 0.55 at 1,000 and 3,000 gallery images but collapses to 0.03 at 10,000, which is not
how recall degrades with gallery size. This tests the embeddings directly: for frozen CLIP, a matching
image-caption pair must score higher than a mismatched one, and the gap must not depend on how many
images the loader has walked through. If alignment holds at small sizes and breaks at large ones, the
fault is in the data path, not in the metric.

    python tools/_p843_alignment_probe.py --apply
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
OUT = REPO / "outputs" / "analysis" / "alignment_probe.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F
    from transformers import CLIPModel, CLIPProcessor

    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device).eval()

    spec = importlib.util.spec_from_file_location("fl", str(REPO / "tools" / "p754_tmp.py"))
    # load the loader helper without importing the whole scale-up script
    sys.path.insert(0, str(REPO / "tools"))
    import _p754_coco_scaleup as fl

    report = {}
    print("=" * 100)
    print("matched vs mismatched cosine similarity, by how many images the loader has seen")
    print("=" * 100)
    print(f"  {'n_images':>9} {'matched':>9} {'mismatched':>11} {'gap':>7} {'i2t@1(own)':>11}")
    for n_img in (100, 1000, 10000):
        loader = fl.subset_loader("val", n_img, 32, False, first=False, workers=4)
        imgs, txts, owners = [], [], []
        with torch.no_grad():
            for b in loader:
                out = model(pixel_values=b["image"].to(device),
                            input_ids=proc(text=b["caption"], return_tensors="pt",
                                           padding=True, truncation=True,
                                           max_length=77)["input_ids"].to(device))
                imgs.append(F.normalize(out.image_embeds, p=2, dim=-1).float().cpu())
                txts.append(F.normalize(out.text_embeds, p=2, dim=-1).float().cpu())
                owners.extend([str(x) for x in b["image_path"]])
        I = torch.cat(imgs)
        T = torch.cat(txts)
        # align by first owner order shown by the loader
        order, first = [], {}
        for j, k in enumerate(owners):
            if k not in first:
                first[k] = j
                order.append(k)
        Iu = I[[first[k] for k in order]]
        oi = {k: i for i, k in enumerate(order)}
        col = torch.tensor([oi[k] for k in owners])
        S = Iu @ T.T
        matched = S[col, torch.arange(S.shape[1])].mean().item()
        # mismatched = the mean of everything except each caption's own image
        mask = torch.ones_like(S, dtype=torch.bool)
        mask[col, torch.arange(S.shape[1])] = False
        mismatched = S[mask].mean().item()
        own_rank1 = (S.argmax(0) == col).float().mean().item()
        print(f"  {len(order):>9} {matched:>9.4f} {mismatched:>11.4f} "
              f"{matched - mismatched:>7.4f} {own_rank1:>11.4f}")
        report[str(n_img)] = {"n_gallery": len(order), "n_captions": len(owners),
                              "matched": matched, "mismatched": mismatched,
                              "gap": matched - mismatched, "own_rank1": own_rank1}
        del loader, imgs, txts, I, T, S
        torch.cuda.empty_cache()

    print()
    print("=" * 100)
    print("verdict")
    print("=" * 100)
    ok = True
    for k, v in report.items():
        good = v["matched"] > v["mismatched"] and v["gap"] > 0.05
        if not good:
            ok = False
        print(f"  n={k:>6}: matched > mismatched by {v['gap']:.4f}  "
              f"[{'ok  ' if good else 'FAIL'}]")
    print()
    print(f"  alignment holds at every size: {ok}")
    if not ok:
        print("  => the data path, not the metric, is at fault: embeddings from larger walks are "
              "misaligned")
    report["alignment_ok"] = ok
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
