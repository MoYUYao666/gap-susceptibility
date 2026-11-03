# -*- coding: utf-8 -*-
r"""查 Qwen2-VL-2B 的参数命名，为"按位置分塔"的严格冻结做准备（2026-10-07）。

实验 ④ 需要把 LoRA 分别限制在**视觉塔**与**语言塔**上，故必须先确认二者在参数名里如何区分。

    python tools\_p4_qwen_param_names.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MDIR = REPO / "models" / "Qwen2-VL-2B-Instruct"


def main() -> int:
    import torch
    from transformers import Qwen2VLForConditionalGeneration
    from peft import LoraConfig, get_peft_model

    print("  加载（仅取参数名，不做前向）…", flush=True)
    m = Qwen2VLForConditionalGeneration.from_pretrained(
        str(MDIR), torch_dtype=torch.bfloat16, device_map="cpu",
        low_cpu_mem_usage=True)
    names = [n for n, _ in m.named_parameters()]
    print(f"  参数张量总数: {len(names)}")

    vis = [n for n in names if "visual" in n.lower()]
    lang = [n for n in names if "visual" not in n.lower()]
    print(f"  含 'visual'（视觉塔）: {len(vis)}")
    print(f"  其余（语言塔）:        {len(lang)}")
    print("\n  视觉塔样例:")
    for n in vis[:5]:
        print("    " + n)
    print("\n  语言塔样例:")
    for n in lang[:5]:
        print("    " + n)

    # 关键：LoRA 目标模块在两塔里各有多少
    tgt = ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")
    print("\n  === LoRA 目标模块的分布 ===")
    for t in tgt:
        nv = sum(1 for n in vis if n.endswith(t + ".weight"))
        nl = sum(1 for n in lang if n.endswith(t + ".weight"))
        print(f"    {t:<12} 视觉塔 {nv:>3} ｜ 语言塔 {nl:>3}")

    # 用 peft 实测注入后的可训参数名（判断能否按名字分塔）
    print("\n  === peft 注入后的可训参数名（各 5 例）===")
    mm = get_peft_model(m, LoraConfig(
        r=8, lora_alpha=16, lora_dropout=0.05, bias="none",
        target_modules=list(tgt)))
    tr = [n for n, p in mm.named_parameters() if p.requires_grad]
    print(f"    可训张量 {len(tr)}")
    v_tr = [n for n in tr if "visual" in n.lower()]
    l_tr = [n for n in tr if "visual" not in n.lower()]
    print(f"    其中视觉塔 {len(v_tr)} ｜ 语言塔 {len(l_tr)}")
    for n in v_tr[:3]:
        print("      [V] " + n)
    for n in l_tr[:3]:
        print("      [L] " + n)
    print("\n  → 分塔可行" if v_tr and l_tr else "\n  ⚠ 无法按名字分塔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
