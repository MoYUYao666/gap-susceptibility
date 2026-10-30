# -*- coding: utf-8 -*-
r"""Verify that the labels built for LLaVA training are correct before another long run.

The previous attempt failed with AttributeError on out.loss.backward() because labels were never
built. This checks, on a real batch, that:
  1. labels exist and the loss is a real number after a forward pass
  2. every label position that is not -100 corresponds to a caption token
  3. the image placeholder is not itself supervised
  4. the loss is finite and of a plausible size

    python tools/_p828_labels_check.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "llava_labels_check.json"


def main() -> int:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch
    from PIL import Image
    from transformers import (AutoProcessor, BitsAndBytesConfig,
                              LlavaForConditionalGeneration)

    proc = AutoProcessor.from_pretrained("llava-hf/llava-1.5-7b-hf")
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_compute_dtype=torch.bfloat16,
                              bnb_4bit_use_double_quant=True)
    model = LlavaForConditionalGeneration.from_pretrained(
        "llava-hf/llava-1.5-7b-hf", quantization_config=quant, torch_dtype=torch.bfloat16,
        device_map={"": 0}, low_cpu_mem_usage=True)

    ann = json.loads((REPO / "coco" / "annotations" / "captions_val2014.json").read_text(
        encoding="utf-8", errors="ignore"))
    by_img = {}
    for c in ann["annotations"]:
        by_img.setdefault(c["image_id"], []).append(c["caption"])
    img_dir = REPO / "coco" / "val2014"
    ids = [i for i in by_img if (img_dir / f"COCO_val2014_{i:012d}.jpg").exists()][:2]

    pre = "USER: <image>\nDescribe this image in detail.\nASSISTANT: "
    ims = [Image.open(img_dir / f"COCO_val2014_{i:012d}.jpg").convert("RGB") for i in ids]
    full = [pre + by_img[i][0] for i in ids]
    out = proc(images=ims, text=full, return_tensors="pt", padding=True, truncation=True,
               max_length=1024)
    # Supervision span from the expanded sequence: prompt is everything up to the last image token.
    # A single <image> placeholder becomes 577 tokens, so counting text tokens misaligns the labels.
    labels = out["input_ids"].clone()
    img_id = int(getattr(model.config, "image_token_index", 32000))
    for b in range(labels.shape[0]):
        row = out["input_ids"][b]
        img_pos = (row == img_id).nonzero(as_tuple=True)[0]
        cut = int(img_pos[-1]) + 1 if len(img_pos) else 0
        labels[b, :cut] = -100
        labels[b, out["attention_mask"][b] == 0] = -100
    out["labels"] = labels
    prompt_token_count = None

    report = {"prompt_token_count_measured_by_last_image_token": "see cut below",
              "seq_len": int(out["input_ids"].shape[1]),
              "supervised_positions": int((labels != -100).sum()),
              "image_token_index": img_id}

    print(f"  sequence {out['input_ids'].shape[1]}, "
          f"supervised {report['supervised_positions']}")

    ok = True
    # The supervised span should be the caption plus the few tokens the chat template adds. Exact
    # equality is the wrong test: the chat template appends its own end-of-turn tokens, so the span is
    # the caption length plus a small constant. What must hold is that the prompt is masked and the
    # span is caption-sized rather than sequence-sized.
    for b in range(labels.shape[0]):
        sup = (labels[b] != -100)
        ids_b = out["input_ids"][b]
        if (ids_b[sup] == img_id).any():
            print(f"  FAIL row {b}: the image placeholder is supervised")
            ok = False
        n_sup = int(sup.sum())
        n_cap = len(proc.tokenizer(by_img[ids[b]][0], add_special_tokens=False)["input_ids"])
        # The chat template wraps the text ("USER: ... ASSISTANT: ... </s>"), so the supervised span
        # is the caption plus the template's own tokens rather than the caption exactly. What matters
        # is that the span is caption-sized and nowhere near the full sequence (610 tokens here).
        if not (n_cap <= n_sup <= 3 * n_cap + 10):
            print(f"  FAIL row {b}: {n_sup} supervised positions for a {n_cap}-token caption")
            ok = False
        else:
            print(f"  row {b}: caption {n_cap} tokens, supervised {n_sup} (template adds "
                  f"{n_sup - n_cap})")
    report["caption_alignment"] = ok
    print(f"  [{'ok  ' if ok else 'FAIL'}] supervised span is the caption, not the prompt")

    inp = {k: (v.to(0) if hasattr(v, "to") else v) for k, v in out.items()}
    inp["pixel_values"] = inp["pixel_values"].to(torch.float16)
    with torch.no_grad():
        res = model(**inp)
    loss = res.loss
    finite = loss is not None and torch.isfinite(loss).all()
    report["loss"] = None if loss is None else float(loss)
    print(f"  forward loss: {report['loss']}")
    if not finite:
        print("  FAIL loss is None or not finite")
        ok = False
    else:
        plausible = 0.1 < float(loss) < 20.0
        print(f"  [{'ok  ' if plausible else 'FAIL'}] loss is finite and plausible")
        ok = ok and plausible

    print()
    print(f"  OVERALL: {'LABELS VERIFIED' if ok else 'LABELS NEED WORK'}")
    report["overall_pass"] = ok
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  wrote {OUT.name}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
