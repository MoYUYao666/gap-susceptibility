# -*- coding: utf-8 -*-
r"""验证"按位置分塔"的 LoRA 目标选择（2026-10-07，CPU 验证，不占 GPU）。

## 为什么需要

Qwen2-VL-2B 的**视觉塔**与**语言塔**用**完全不同的线性层名**：

| 塔 | 线性叶子 |
|---|---|
| 视觉塔 `model.visual.blocks.N` | `attn.qkv`、`attn.proj`、`mlp.fc1`、`mlp.fc2` |
| 视觉→语言 `model.visual.merger` | `mlp.0`、`mlp.2` |
| 语言塔 `model.language_model.layers.N` | `q_proj`、`k_proj`、`v_proj`、`o_proj`、`gate_proj`、`up_proj`、`down_proj` |

**→ 给 peft 传不同的 `target_modules` 即可分塔**（但要确认 peft 按**名字后缀**匹配，
不会把 `proj` 误匹配到 `o_proj`/`down_proj` 等）。

## 本脚本做什么

用**完全限定名**（`model.visual.blocks.0.attn.qkv` 之类）核实三种位置配置各自命中的张量数，
确保 **text_only 不碰视觉塔、vision_only 不碰语言塔**（与 CLIP 侧的严格冻结同标准）。

    python tools\_p4_verify_tower_split.py
"""
from __future__ import annotations

from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from transformers import Qwen2VLForConditionalGeneration

REPO = Path(__file__).resolve().parents[1]
MDIR = REPO / "models" / "Qwen2-VL-2B-Instruct"

# 三臂的目标模块（用叶子名，peft 按后缀匹配）
ARMS = {
    "text_only":   ["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    "vision_only": ["qkv", "proj", "fc1", "fc2"],
    "both":        ["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj",
                    "qkv", "proj", "fc1", "fc2"],
}


def main() -> int:
    print("  加载（cpu）…", flush=True)
    base = Qwen2VLForConditionalGeneration.from_pretrained(
        str(MDIR), torch_dtype=torch.bfloat16, device_map="cpu", low_cpu_mem_usage=True)
    # 冻结全部基座
    for p in base.parameters():
        p.requires_grad = False

    print(f"\n  {'臂':<12} {'可训张量':>8} {'视觉侧':>7} {'语言侧':>7}  交叉污染检查")
    print("  " + "-" * 74)
    ok_all = True
    for arm, tgt in ARMS.items():
        # 每臂用独立副本（peft 会改模型）
        import copy
        m = copy.deepcopy(base)
        for p in m.parameters():
            p.requires_grad = False
        m = get_peft_model(m, LoraConfig(
            r=8, lora_alpha=16, lora_dropout=0.05, bias="none",
            target_modules=list(tgt)))
        tr = [n for n, p in m.named_parameters() if p.requires_grad]
        n_vis = sum(1 for n in tr if ".visual." in n)
        n_lang = sum(1 for n in tr if "language_model" in n)
        # 污染判定
        bad = []
        if arm == "text_only" and n_vis:
            bad.append(f"text_only 碰到视觉塔 {n_vis}")
        if arm == "vision_only" and n_lang:
            bad.append(f"vision_only 碰到语言塔 {n_lang}")
        if arm in ("text_only", "vision_only") and not (n_vis or n_lang):
            bad.append("一个都没命中")
        if bad:
            ok_all = False
        print(f"  {arm:<12} {len(tr):>8} {n_vis:>7} {n_lang:>7}  "
              f"{'✅ 干净' if not bad else '❌ ' + '; '.join(bad)}")
        if arm == "vision_only":
            print("      视觉侧样例:", tr[0] if tr else "—")

    print("\n  === 结论 ===")
    print("  ✅ 分塔可行，三臂互不污染" if ok_all else "  ❌ 分塔有污染，需改用完全限定名")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
