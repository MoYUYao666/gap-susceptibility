# -*- coding: utf-8 -*-
r"""Score frozen CLIP across gallery sizes with the caption cap switched off.

The cap is what made the metric collapse: 40,000 caption rows cannot cover a 27,000-image gallery at
five captions each, so a large part of the gallery lost every caption and became unreachable. With the
cap raised above the caption count, recall should fall smoothly as the gallery grows and must stay in
the range CLIP actually achieves on MS-COCO.

    python tools/_p844_uncapped.py --apply
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
OUT = REPO / "outputs" / "analysis" / "uncapped_gallery.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    from transformers import CLIPModel, CLIPProcessor
    import _p754_coco_scaleup as fl

    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device).eval()

    report = {"cap": 300000, "gallery": []}
    print("=" * 100)
    print("frozen CLIP, caption cap raised above the caption count (no truncation)")
    print("=" * 100)
    print(f"  {'gallery':>8} {'captions':>9} {'R@1':>8} {'R@5':>8} {'R@10':>8} {'i2t R@1':>9} "
          f"{'t2i R@1':>9}")
    for n_img in (1000, 3000, 10000, 27000):
        loader = fl.subset_loader("val", n_img, 32, False, first=False, workers=4)
        met = fl.evaluate(model, loader, device, max_caption_rows=300000, processor=proc)
        report["gallery"].append({k: met[k] for k in ("n_unique_images", "n_captions", "R@1",
                                                      "R@5", "R@10", "R@1_i2t", "R@1_t2i")})
        print(f"  {met['n_unique_images']:>8} {met['n_captions']:>9} {met['R@1']:>8.4f} "
              f"{met['R@5']:>8.4f} {met['R@10']:>8.4f} {met['R@1_i2t']:>9.4f} "
              f"{met['R@1_t2i']:>9.4f}")
        del loader
        torch.cuda.empty_cache()

    print()
    print("=" * 100)
    print("verdict")
    print("=" * 100)
    g = report["gallery"]
    mono = all(g[i]["R@1"] >= g[i + 1]["R@1"] for i in range(len(g) - 1))
    plausible = all(0.05 <= x["R@1"] <= 0.75 for x in g)
    print(f"  R@1 falls as the gallery grows: {mono}")
    print(f"  every value in a range CLIP can reach on MS-COCO: {plausible}")
    print()
    print("  reference points: CLIP ViT-B/32 scores about 0.54 i2t R@1 on the 5k-image COCO benchmark;")
    print("  a larger gallery lowers the ceiling, so a smooth decline is the expected behaviour")
    report["monotone"] = mono
    report["plausible"] = plausible
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
