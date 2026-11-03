# -*- coding: utf-8 -*-
r"""Time one forward pass of LLaVA-1.5-7B in 4-bit, to size the experiment honestly.

The adaptation-site run needs two measurement passes over the evaluation set per arm, each of which is
one forward pass per batch. Knowing the per-forward cost turns the arm count into a predictable wall
clock instead of a guess.

    python tools/_p833_forward_timing.py
"""
from __future__ import annotations

import json
import os
import statistics as st
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "llava_forward_timing.json"


def main() -> int:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch
    from PIL import Image
    from transformers import (AutoProcessor, BitsAndBytesConfig,
                              LlavaForConditionalGeneration)

    if not torch.cuda.is_available():
        print("  no CUDA device")
        return 1

    proc = AutoProcessor.from_pretrained("llava-hf/llava-1.5-7b-hf")
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_compute_dtype=torch.bfloat16,
                              bnb_4bit_use_double_quant=True)
    model = LlavaForConditionalGeneration.from_pretrained(
        "llava-hf/llava-1.5-7b-hf", quantization_config=quant, torch_dtype=torch.bfloat16,
        device_map={"": 0}, low_cpu_mem_usage=True)
    model.eval()

    ann = json.loads((REPO / "coco" / "annotations" / "captions_val2014.json").read_text(
        encoding="utf-8", errors="ignore"))
    by_img = {}
    for c in ann["annotations"]:
        by_img.setdefault(c["image_id"], []).append(c["caption"])
    img_dir = REPO / "coco" / "val2014"
    ids = [i for i in by_img if (img_dir / f"COCO_val2014_{i:012d}.jpg").exists()][:16]

    pre = "USER: <image>\nDescribe this image in detail.\nASSISTANT: "
    report = {}
    print("=" * 100)
    print("forward-only cost by batch size")
    print("=" * 100)
    for bs in (1, 2, 4, 8):
        chunk = ids[:bs]
        ims = [Image.open(img_dir / f"COCO_val2014_{i:012d}.jpg").convert("RGB") for i in chunk]
        prompts = [pre + by_img[i][0] for i in chunk]
        inp = proc(images=ims, text=prompts, return_tensors="pt", padding=True, truncation=False)
        if inp["pixel_values"].dtype == torch.uint8:
            inp["pixel_values"] = inp["pixel_values"].to(torch.float32) / 255.0
        inp = {k: (v.to(0) if hasattr(v, "to") else v) for k, v in inp.items()}
        inp["pixel_values"] = inp["pixel_values"].to(torch.float16)
        ts = []
        try:
            for _ in range(3):
                torch.cuda.synchronize()
                t0 = time.time()
                with torch.no_grad():
                    model(**inp)
                torch.cuda.synchronize()
                ts.append(time.time() - t0)
        except torch.cuda.OutOfMemoryError:
            print(f"  batch {bs}: out of memory")
            torch.cuda.empty_cache()
            continue
        sec = st.median(ts)
        per_item = sec / bs
        print(f"  batch {bs:>2}: {sec:6.2f} s/forward  ({per_item:5.2f} s per item)  "
              f"seq {inp['input_ids'].shape[1]}")
        report[str(bs)] = {"seconds": sec, "per_item": per_item,
                           "seq_len": int(inp["input_ids"].shape[1])}
        del inp
        torch.cuda.empty_cache()

    print()
    print("=" * 100)
    print("implications for the adaptation-site run")
    print("=" * 100)
    best = min(report.items(), key=lambda kv: kv[1]["per_item"]) if report else None
    if best:
        bs, v = best
        print(f"  fastest measured: batch {bs} at {v['per_item']:.2f} s per item")
        for n_eval in (40, 75, 150):
            print(f"  measuring {n_eval * 2} items per arm (before + after) "
                  f"= {n_eval * 2 * v['per_item'] / 60:.1f} min per arm")
        print()
        print("  The labels check and the frozen arm confirm the pipeline works; the constraint is")
        print("  arithmetic, so the evaluation set is the knob that sets the wall clock.")
        report["note"] = ("evaluation-set size drives the wall clock; per-arm cost is two passes "
                          "over the evaluation set")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
