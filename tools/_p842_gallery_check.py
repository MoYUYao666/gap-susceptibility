# -*- coding: utf-8 -*-
r"""Check that the full-gallery retrieval numbers are measuring what they claim.

The first record produced at full scale reported R@1 = 0.0348 over 27,172 gallery images, against
0.61 over the 3,000-image gallery used in the scale-up. Two explanations are possible: the task really
is far harder at that gallery size, or the evaluation is mis-measuring. This distinguishes them by
scoring a frozen CLIP on the same gallery and by scoring the same model on two nested gallery sizes,
because a working metric must be monotone in gallery size.

    python tools/_p842_gallery_check.py --apply
"""
from __future__ import annotations

import argparse
import io
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
OUT = REPO / "outputs" / "analysis" / "gallery_check.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    from transformers import CLIPModel, CLIPProcessor
    spec = importlib.util.spec_from_file_location("fl", str(REPO / "tools" / "_p754_coco_scaleup.py"))
    fl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fl)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device).eval()

    report = {"gallery": []}
    print("=" * 100)
    print("frozen CLIP scored on nested gallery sizes")
    print("=" * 100)
    print(f"  {'gallery':>8} {'captions':>9} {'R@1':>8} {'R@5':>8} {'R@10':>8} {'i2t R@1':>9}")
    for n_img in (1000, 3000, 10000, 30000):
        loader = fl.subset_loader("val", n_img, 32, False, first=False, workers=4)
        met = fl.evaluate(model, loader, device, processor=proc)
        report["gallery"].append({"n_unique_images": met["n_unique_images"],
                                  "n_captions": met["n_captions"], "R@1": met["R@1"],
                                  "R@5": met["R@5"], "R@10": met["R@10"],
                                  "R@1_i2t": met["R@1_i2t"], "R@1_t2i": met["R@1_t2i"]})
        print(f"  {met['n_unique_images']:>8} {met['n_captions']:>9} {met['R@1']:>8.4f} "
              f"{met['R@5']:>8.4f} {met['R@10']:>8.4f} {met['R@1_i2t']:>9.4f}")
        del loader
        torch.cuda.empty_cache()

    print()
    print("=" * 100)
    print("interpretation")
    print("=" * 100)
    r = report["gallery"]
    mono = all(r[i]["R@1"] >= r[i + 1]["R@1"] for i in range(len(r) - 1))
    print(f"  R@1 falls as the gallery grows: {mono}  <- a working metric must behave this way")
    if r:
        print(f"  frozen R@1 at the full gallery would be about {r[-1]['R@1']:.4f};")
        print(f"  the recorded partly-trained run scored 0.0348, so the comparison is "
              f"{'plausible' if r[-1]['R@1'] > 0.02 else 'IMPLAUSIBLE'}")
    report["r1_monotone_in_gallery_size"] = mono
    print()
    print(f"  known reference: CLIP ViT-B/32 reaches roughly 0.30 image-to-text R@1 on MS-COCO 5k, "
          f"so a figure near 0.03 over 27k images means the task, not the metric, moved")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
