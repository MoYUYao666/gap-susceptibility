# -*- coding: utf-8 -*-
r"""定位 `get_base_layer()` 返回 Conv3d 的那个 LoRA 包装模块名（5 行诊断）。"""
from __future__ import annotations
import os
import sys
from pathlib import Path
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
MDIR = REPO / "models" / "Qwen2-VL-2B-Instruct"

import torch
from transformers import Qwen2VLForConditionalGeneration
from peft import LoraConfig, get_peft_model

m = Qwen2VLForConditionalGeneration.from_pretrained(
    str(MDIR), torch_dtype=torch.bfloat16, low_cpu_mem_usage=True)
m = get_peft_model(m, LoraConfig(
    r=8, lora_alpha=16, lora_dropout=0.0, bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj",
                    "qkv", "proj", "fc1", "fc2"]))
bad = []
for name, mod in m.named_modules():
    if hasattr(mod, "lora_A"):
        base = mod.get_base_layer() if hasattr(mod, "get_base_layer") else mod
        if not isinstance(base, torch.nn.Linear):
            bad.append((name, type(base).__name__, type(mod).__name__))
print("LoRA-wrapped modules whose base is NOT nn.Linear:", len(bad))
for n, b, w in bad:
    print("   ", n, "| base:", b, "| wrapper:", w)
n_lin = sum(1 for _, mod in m.named_modules()
            if hasattr(mod, "lora_A")
            and isinstance(mod.get_base_layer() if hasattr(mod, "get_base_layer") else mod,
                           torch.nn.Linear))
print("LoRA-wrapped Linear modules:", n_lin)
