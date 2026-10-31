# -*- coding: utf-8 -*-
r"""Locate the tensor that is actually uint8 when the vision tower runs.

pixel_values comes back from the processor already normalised as float32 (range about -0.0065 to
0.0084), so the earlier "/ 255" was wrong and the Byte tensor causing the GELU failure must be
something else. This runs the real forward path used by the experiment and prints the dtype of every
tensor, then narrows down which argument the tower rejects.

    python tools/_p825_forward_probe.py
"""
from __future__ import annotations

import json
import os
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "llava_forward.json"


def main() -> int:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch
    from PIL import Image
    from transformers import (AutoProcessor, BitsAndBytesConfig,
                              LlavaForConditionalGeneration)

    proc = AutoProcessor.from_pretrained("llava-hf/llava-1.5-7b-hf")
    img_dir = REPO / "coco" / "val2014"
    ann = json.loads((REPO / "coco" / "annotations" / "captions_val2014.json").read_text(
        encoding="utf-8", errors="ignore"))
    iid = ann["annotations"][0]["image_id"]
    cap = ann["annotations"][0]["caption"]
    im = Image.open(img_dir / f"COCO_val2014_{iid:012d}.jpg").convert("RGB")
    raw = proc(images=[im], text=["USER: <image>\nDescribe this image.\nASSISTANT: " + cap],
               return_tensors="pt", padding=True)

    report = {"processor_dtypes": {k: str(v.dtype) for k, v in raw.items()}}
    print("  processor dtypes:", report["processor_dtypes"])

    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_compute_dtype=torch.bfloat16,
                              bnb_4bit_use_double_quant=True)
    model = LlavaForConditionalGeneration.from_pretrained(
        "llava-hf/llava-1.5-7b-hf", quantization_config=quant, torch_dtype=torch.bfloat16,
        device_map={"": 0}, low_cpu_mem_usage=True)
    inner = model.model
    vision = inner.vision_tower
    print(f"  vision tower class: {type(vision).__name__}")
    print(f"  tower dtype: {next(vision.parameters()).dtype}")

    pv = raw["pixel_values"].to(0)
    print(f"  passing pixel_values dtype {pv.dtype} range [{pv.min():.4f}, {pv.max():.4f}]")
    # 1. the tower on its own
    try:
        with torch.no_grad():
            out = vision(pv.to(torch.bfloat16), output_hidden_states=False)
        print(f"  vision tower alone: OK, output {tuple(out.last_hidden_state.shape)} "
              f"dtype {out.last_hidden_state.dtype}")
        report["tower_alone"] = "ok"
    except Exception as exc:
        print(f"  vision tower alone FAILED: {type(exc).__name__}: {str(exc)[:150]}")
        report["tower_alone"] = f"{type(exc).__name__}: {exc}"
        report["trace"] = traceback.format_exc()[-900:]

    # 2. the whole model forward
    try:
        with torch.no_grad():
            out = model(**{k: (v.to(0) if hasattr(v, "to") else v) for k, v in raw.items()})
        print(f"  full model forward: OK, logits {tuple(out.logits.shape)}")
        report["full_forward"] = "ok"
    except Exception as exc:
        print(f"  full model forward FAILED: {type(exc).__name__}: {str(exc)[:150]}")
        report["full_forward"] = f"{type(exc).__name__}: {exc}"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
