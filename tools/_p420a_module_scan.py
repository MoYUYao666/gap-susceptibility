# -*- coding: utf-8 -*-
r"""task-9 步骤 1a：列出 Qwen2-VL-2B 上 `qkv/proj/fc1/fc2` 究竟命中了哪些模块类型。

为什么要这一步：`peft` 的 `target_modules` 是**子串匹配全限定名**，vision 侧的 `proj`
同时会命中 patch-embed 的 `Conv3d`（`...visual.patch_embed.proj`）。盲目标注会让
"每 rank 成本"的记账混入卷积核——所以先把命中清单打出来，再决定纳入哪些。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
MDIR = REPO / "models" / "Qwen2-VL-2B-Instruct"

if __name__ == "__main__":
    import torch
    from transformers import Qwen2VLForConditionalGeneration
    from peft import LoraConfig, get_peft_model

    m = Qwen2VLForConditionalGeneration.from_pretrained(
        str(MDIR), torch_dtype=torch.bfloat16, low_cpu_mem_usage=True)
    cfg = m.config
    print("LLM layers:", cfg.text_config.num_hidden_layers,
          "d_model:", cfg.text_config.hidden_size)
    vc = cfg.vision_config
    print("vision depth:", vc.depth, "hidden:", vc.hidden_size,
          "embed_dim:", vc.embed_dim, "patch:", getattr(vc, "patch_size", None),
          "spatial_merge:", getattr(vc, "spatial_merge_size", None))

    targets = ["q_proj", "k_proj", "v_proj", "o_proj",
               "gate_proj", "up_proj", "down_proj",
               "qkv", "proj", "fc1", "fc2"]
    # 不加载 peft，直接用子串匹配列出会被命中的 Linear/Conv 模块
    hits = []
    for name, mod in m.named_modules():
        if not isinstance(mod, torch.nn.Linear):
            continue
        leaf = name.split(".")[-1]
        if any(t == leaf for t in targets):
            hits.append((name, mod.in_features, mod.out_features))

    print(f"\n命中 Linear 模块 {len(hits)} 个；按 (叶子名, in, out) 归类：")
    from collections import Counter
    c = Counter((n.split(".")[-1], i, o) for n, i, o in hits)
    for (leaf, i, o), k in sorted(c.items(), key=lambda x: (x[0][1], x[0][2])):
        print(f"  {leaf:<10} in={i:<6} out={o:<6} count={k}")

    print("\n视觉塔命中前缀样例：")
    seen = set()
    for n, i, o in hits:
        if ".visual." in n:
            key = n.split(".")[-1]
            if key in seen:
                continue
            seen.add(key)
            print(f"  {n}  ({i} -> {o})")

    print("\nConv3d 命中（会被 target_modules 误伤）：")
    for name, mod in m.named_modules():
        if isinstance(mod, torch.nn.Conv3d):
            leaf = name.split(".")[-1]
            if leaf in targets:
                print(f"  {name}  weight={tuple(mod.weight.shape)}")

    # 逐层号列表，用于分块
    lay = sorted({int(n.split(".")[n.split(".").index("layers") + 1])
                  for n, _ in m.named_parameters() if ".layers." in n and "language_model" in n})
    print("\nLLM 层号范围:", (min(lay), max(lay)) if lay else None, "n=", len(lay))
