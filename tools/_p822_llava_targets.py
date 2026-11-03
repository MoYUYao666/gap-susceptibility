# -*- coding: utf-8 -*-
r"""Find the correct way to address the two towers in LLaVA-1.5-7B for PEFT.

PEFT matches a target list entry with `key.endswith("." + entry)` and only treats the field as a
regular expression when it is a single string. The two towers share the leaf names q_proj, k_proj and
v_proj, so leaf names cannot separate them; this enumerates the full qualified module names and tests
the three ways of addressing them, then records which one isolates the towers.

    python tools/_p822_llava_targets.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "llava_targets.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

    import torch
    from transformers import BitsAndBytesConfig, LlavaForConditionalGeneration
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_compute_dtype=torch.bfloat16,
                              bnb_4bit_use_double_quant=True)
    model = LlavaForConditionalGeneration.from_pretrained(
        "llava-hf/llava-1.5-7b-hf", quantization_config=quant, torch_dtype=torch.bfloat16,
        device_map={"": 0}, low_cpu_mem_usage=True)

    linear = [(n, m) for n, m in model.named_modules() if isinstance(m, torch.nn.Linear)]
    vis = [n for n, _ in linear if n.startswith("vision_model")]
    txt = [n for n, _ in linear if n.startswith("language_model")]
    proj = [n for n, _ in linear if "multi_modal_projector" in n]
    print("=" * 100)
    print("1. qualified linear module names")
    print("=" * 100)
    print(f"  vision_model           {len(vis):>4} linear layers, e.g. {vis[0]}")
    print(f"  language_model         {len(txt):>4} linear layers, e.g. {txt[0]}")
    print(f"  multi_modal_projector  {len(proj):>4} linear layers: {proj}")

    def tower(n):
        if n.startswith("vision_model"):
            return "vision"
        if "multi_modal_projector" in n:
            return "projector"
        if n.startswith("language_model"):
            return "text"
        return "other"

    def probe(label, targets):
        m = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
        try:
            cfg = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0, bias="none",
                             task_type="CAUSAL_LM", target_modules=targets)
            pm = get_peft_model(m, cfg)
        except Exception as exc:
            print(f"  {label:<44} REJECTED: {type(exc).__name__}: {str(exc)[:90]}")
            return None
        tr = [(n, p.numel()) for n, p in pm.named_parameters() if p.requires_grad]
        by = Counter()
        for n, c in tr:
            by[tower(n)] += c
        total = sum(c for _, c in tr)
        print(f"  {label:<44} trainable {total:>12,}  tensors {len(tr):>4}  "
              f"by tower {dict(by)}")
        del pm
        torch.cuda.empty_cache()
        return {"label": label, "n_trainable": total, "n_tensors": len(tr),
                "by_tower": dict(by)}

    print()
    print("=" * 100)
    print("2. how each addressing mode behaves (vision_only arm as the test case)")
    print("=" * 100)
    # the candidate set of vision-side qualified names, minus the projector
    vis_only_names = sorted(vis)
    vis_proj_names = sorted(vis + proj)
    text_names = sorted(txt)
    results = []
    for label, targets in (
        ("leaf names {'q_proj','fc1',...}", ["q_proj", "k_proj", "v_proj", "out_proj", "fc1", "fc2"]),
        ("vision qualified names, no projector", vis_only_names),
        ("vision qualified names + projector", vis_proj_names),
        ("text qualified names", text_names),
    ):
        r = probe(label, targets)
        if r:
            results.append(r)

    print()
    print("=" * 100)
    print("3. verdict")
    print("=" * 100)
    isolators = {}
    for r in results:
        bt = r["by_tower"]
        side = "vision" if "vision" in r["label"] else ("text" if "text" in r["label"] else "leaf")
        if side == "vision":
            clean = bt.get("text", 0) == 0 and bt.get("vision", 0) > 0
            isolators[r["label"]] = {"isolates_vision": clean, "by_tower": bt}
            print(f"  {r['label']:<44} isolates vision: {clean}")
        elif side == "text":
            clean = bt.get("vision", 0) == 0 and bt.get("text", 0) > 0
            isolators[r["label"]] = {"isolates_text": clean, "by_tower": bt}
            print(f"  {r['label']:<44} isolates text:   {clean}")
        else:
            print(f"  {r['label']:<44} leaf names cannot separate the towers "
                  f"(vision {bt.get('vision', 0):,} / text {bt.get('text', 0):,})")

    payload = {"vision_names": vis, "text_names": txt, "projector_names": proj,
               "probes": results, "isolation": isolators}
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
