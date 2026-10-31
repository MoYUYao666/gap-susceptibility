# -*- coding: utf-8 -*-
r"""Official IGU-LoRA allocation stage ported to CLIP by adapting *names only* (A1, path A).

The released IGU-LoRA code (external/igulora) hard-codes LLM-style parameter names in RankAllocator
(``split(".")[4]`` module name, ``int(split(".")[2])`` layer index) and operates on SVDLoRAModule. We therefore
1. replace CLIP attention projections with the official ``SVDLoRAModule`` (rank 16, alpha 32), and
2. feed the official ``RankAllocator`` a name proxy that presents them as ``model.layers.<n>.self_attn.<proj>.lora_*``.

The allocation algorithm itself is the official implementation (AdaLoRA-style pruning schedule, EMA/SNR scoring,
mask-to-target-rank); only the naming layer is adapted. The resulting per-block ranks are then trained as a LLaVA arm.

    python tools/_p1557_official_igu_clip.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import torch
import torch.nn as nn

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "external", "igulora"))
OUT = os.path.join(REPO, "outputs", "analysis", "p3_official_igu_clip.json")
MODEL = os.path.join(REPO, "models", "clip-vit-base-patch32")
IMGS = os.path.join(REPO, "data", "marine_captions")
CAPS = os.path.join(IMGS, "captions.json")
BUDGET = 16
BLOCKS = ["vision", "text_shallow", "text_mid", "text_deep"]
PROJ_MAP = {"q_proj": "q_proj", "k_proj": "k_proj", "v_proj": "v_proj", "out_proj": "o_proj"}
STEPS = 30


class NameProxy(nn.Module):
    """Presents the adapted modules under LLM-style parameter names for the official RankAllocator."""

    def __init__(self, mapping):
        super().__init__()
        self._mapping = mapping

    def named_parameters(self, *args, **kwargs):
        return iter(self._mapping.items())


def replace_linear(model):
    mapping = {}
    counter = {"text": 0, "vision": 0}
    modules = dict(model.named_modules())
    targets = []
    for name, mod in modules.items():
        if not isinstance(mod, nn.Linear):
            continue
        if ".self_attn." not in name:
            continue
        proj = name.rsplit(".", 1)[-1]
        if proj not in PROJ_MAP:
            continue
        if "text_model.encoder.layers." in name:
            idx = int(name.split("text_model.encoder.layers.")[1].split(".")[0])
            llm_idx = idx
            kind = "text"
        elif "vision_model.encoder.layers." in name:
            idx = int(name.split("vision_model.encoder.layers.")[1].split(".")[0])
            llm_idx = 100 + idx
            kind = "vision"
        else:
            continue
        parent_name = name.rsplit(".", 1)[0]
        parent = modules[parent_name]
        new_mod = None
        from iglora.lora_module import SVDLoRAModule
        new_mod = SVDLoRAModule(mod, mod.in_features, mod.out_features, r=16, lora_alpha=32)
        setattr(parent, proj, new_mod)
        prefix = "model.layers.%d.self_attn.%s" % (llm_idx, PROJ_MAP[proj])
        mapping[prefix + ".lora_A"] = new_mod.lora_A
        mapping[prefix + ".lora_B"] = new_mod.lora_B
        mapping[prefix + ".lora_E"] = new_mod.lora_E
        targets.append((kind, idx, llm_idx, proj))
    return mapping, targets


def main() -> int:
    os.environ["HF_HUB_OFFLINE"] = "1"
    torch.manual_seed(42)
    from transformers import CLIPModel, CLIPProcessor

    model = CLIPModel.from_pretrained(MODEL, local_files_only=True).float().cuda()
    proc = CLIPProcessor.from_pretrained(MODEL, local_files_only=True)
    mapping, targets = replace_linear(model)
    proxy = NameProxy(mapping)
    params = [p for n, p in model.named_parameters() if "lora_" in n and p.requires_grad]
    print("adapted modules:", len(targets), "trainable tensors:", len(params))
    from iglora.rank_allocator import RankAllocator
    alloc = RankAllocator(proxy, lora_r=16, target_rank=4, init_warmup=5, final_warmup=5,
                          mask_interval=10, beta1=0.85, beta2=0.99, total_step=STEPS)
    opt = torch.optim.AdamW(params, lr=1e-3)
    caps = json.load(open(CAPS, encoding="utf-8"))["captions"]
    n = len(caps)
    for step in range(STEPS):
        idx = [int((step * 4 + k) % n) for k in range(4)]
        imgs = []
        from PIL import Image
        for i in idx:
            imgs.append(Image.open(os.path.join(IMGS, "%04d.jpg" % i)).convert("RGB"))
        inp = proc(text=[caps[i] for i in idx], images=imgs, return_tensors="pt", padding=True, truncation=True)
        inp = {k: v.cuda() for k, v in inp.items()}
        out = model(**inp, return_loss=True)
        loss = out.loss
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        alloc.update_and_mask(proxy, step)
        if step % 5 == 0:
            print("  step %d loss %.4f" % (step, float(loss)), flush=True)
    # per-module rank from the masked lora_E
    ranks = {}
    for (kind, idx, llm_idx, proj) in targets:
        prefix = "model.layers.%d.self_attn.%s" % (llm_idx, PROJ_MAP[proj])
        E = mapping[prefix + ".lora_E"]
        ranks[prefix] = int((E.abs().sum(dim=1) > 0).sum().item())
    block_sum = {"vision": 0.0, "text_shallow": 0.0, "text_mid": 0.0, "text_deep": 0.0}
    for prefix, r in ranks.items():
        if prefix.startswith("model.layers.1"):
            block_sum["vision"] += r
        else:
            idx = int(prefix.split(".")[2])
            block_sum["text_shallow" if idx <= 2 else ("text_mid" if idx <= 8 else "text_deep")] += r
    w = np.array([block_sum[b] for b in BLOCKS], dtype=float)
    share = w / w.sum() if w.sum() > 0 else np.ones_like(w) / len(w)
    block_ranks = np.maximum(1, np.round(share * BUDGET)).astype(int)
    while block_ranks.sum() > BUDGET:
        i = int(np.argmax(block_ranks))
        if block_ranks[i] > 1:
            block_ranks[i] -= 1
        else:
            break
    while block_ranks.sum() < BUDGET:
        i = int(np.argmin(share * BUDGET - block_ranks))
        block_ranks[i] += 1
    out = {"meta": {"script": "tools/_p1557_official_igu_clip.py",
                    "task": "A1 official IGU allocation ported with a name proxy",
                    "official_code": "external/igulora (github.com/withyou12/igulora)",
                    "target_rank": 4, "steps": STEPS, "budget": BUDGET},
           "module_ranks": ranks, "block_rank_sum": block_sum,
           "share": {b: float(s) for b, s in zip(BLOCKS, share)},
           "allocation": {b: int(r) for b, r in zip(BLOCKS, block_ranks)}}
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
    print("module ranks:", ranks)
    print("block sums:", block_sum)
    print("allocation:", out["allocation"])
    print("wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
