# -*- coding: utf-8 -*-
r"""Find which tensor in the LLaVA batch is still uint8.

The GELU error says a Byte tensor reaches the vision tower, so this prints the dtype of every tensor
the processor produces and of every tensor after the intended conversion, to locate the one that is
being missed.

    python tools/_p824_dtype_probe.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "llava_dtypes.json"


def main() -> int:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch
    from PIL import Image
    from transformers import AutoProcessor

    proc = AutoProcessor.from_pretrained("llava-hf/llava-1.5-7b-hf")
    img_dir = REPO / "coco" / "val2014"
    ann = json.loads((REPO / "coco" / "annotations" / "captions_val2014.json").read_text(
        encoding="utf-8", errors="ignore"))
    iid = ann["annotations"][0]["image_id"]
    cap = ann["annotations"][0]["caption"]
    im = Image.open(img_dir / f"COCO_val2014_{iid:012d}.jpg").convert("RGB")

    report = {}
    raw = proc(images=[im], text=["USER: <image>\nDescribe this image.\nASSISTANT: " + cap],
               return_tensors="pt", padding=True)
    report["processor_outputs"] = {k: str(v.dtype) for k, v in raw.items()}
    print("  processor output dtypes:")
    for k, v in raw.items():
        print(f"    {k:<20} {v.dtype}  shape {tuple(v.shape)}")

    conv = dict(raw)
    conv["pixel_values"] = conv["pixel_values"].to(torch.float32) / 255.0
    conv["pixel_values"] = conv["pixel_values"].to(torch.float16)
    report["after_conversion"] = {k: str(v.dtype) for k, v in conv.items()}
    print("  after the intended conversion:")
    for k, v in conv.items():
        print(f"    {k:<20} {v.dtype}")

    # what the tower sees
    report["pixel_values_finite"] = bool(torch.isfinite(conv["pixel_values"]).all())
    report["pixel_values_range"] = [float(conv["pixel_values"].min()),
                                    float(conv["pixel_values"].max())]
    print(f"  pixel range after conversion: {report['pixel_values_range']}")
    print(f"  all finite: {report['pixel_values_finite']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
