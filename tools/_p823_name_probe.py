# -*- coding: utf-8 -*-
r"""List LLaVA's linear layer names, in whatever prefix form they actually use.

The previous attempt assumed the names start with "vision_model"/"language_model" and failed on an
empty list, so this records the real prefixes and the first names of each group, writing the result
to JSON so the answer survives the shell's encoding.

    python tools/_p823_name_probe.py
"""
from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "llava_names.json"


def main() -> int:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch
    from transformers import BitsAndBytesConfig, LlavaForConditionalGeneration

    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_compute_dtype=torch.bfloat16,
                              bnb_4bit_use_double_quant=True)
    model = LlavaForConditionalGeneration.from_pretrained(
        "llava-hf/llava-1.5-7b-hf", quantization_config=quant, torch_dtype=torch.bfloat16,
        device_map={"": 0}, low_cpu_mem_usage=True)

    names = [n for n, m in model.named_modules() if isinstance(m, torch.nn.Linear)]
    prefixes = Counter(".".join(n.split(".")[:2]) for n in names)
    payload = {"n_linear": len(names),
               "prefixes": dict(prefixes.most_common(20)),
               "first_10": names[:10],
               "last_10": names[-10:]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  {len(names)} linear layers; wrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
