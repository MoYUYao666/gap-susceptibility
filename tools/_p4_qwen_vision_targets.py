# -*- coding: utf-8 -*-
r"""查 Qwen2-VL-2B **视觉塔**里可做 LoRA 的线性层名（2026-10-07）。

实验 ④ 要做"位置"对照，必须有**视觉侧**可训目标。上一版显示
`q_proj/k_proj/v_proj/o_proj/gate/up/down` 在视觉塔**一个都没有**，
故需找出视觉塔 block 内的 Linear 名称。

    python tools\_p4_qwen_vision_targets.py
"""
from __future__ import annotations

import collections
from pathlib import Path

import torch
import torch.nn as nn

REPO = Path(__file__).resolve().parents[1]
MDIR = REPO / "models" / "Qwen2-VL-2B-Instruct"


def main() -> int:
    from transformers import Qwen2VLForConditionalGeneration

    print("  加载（cpu, 只为取名）…", flush=True)
    m = Qwen2VLForConditionalGeneration.from_pretrained(
        str(MDIR), torch_dtype=torch.bfloat16, device_map="cpu", low_cpu_mem_usage=True)

    print("\n  === 视觉塔 block 0 的结构（Linear 层名）===")
    vis = getattr(getattr(m, "model"), "visual", None)
    if vis is None:
        print("    ⚠ 未找到 model.visual")
        return 1
    blk0 = vis.blocks[0]
    for n, mod in blk0.named_modules():
        if isinstance(mod, nn.Linear):
            print(f"    {n:<46} {tuple(mod.weight.shape)}")
    if hasattr(vis, "merger"):
        print("\n  === merger（视觉→语言投影）===")
        for n, mod in vis.merger.named_modules():
            if isinstance(mod, nn.Linear):
                print(f"    merger.{n:<40} {tuple(mod.weight.shape)}")

    # 全塔的 Linear 叶子名统计（去掉 block 索引）
    leaves = collections.Counter()
    for n, mod in vis.named_modules():
        if isinstance(mod, nn.Linear):
            import re
            key = re.sub(r"\.\d+\.", ".N.", n)
            leaves[key] += 1
    print("\n  === 视觉塔全部 Linear 叶子（计数）===")
    for k, v in sorted(leaves.items()):
        print(f"    {k:<50} ×{v}")

    # 投影器 / 语言塔对照
    print("\n  === 可做 LoRA 的候选名（供 peft target_modules）===")
    cands = sorted({k.rsplit(".", 1)[-1] for k in leaves})
    print("    视觉塔叶子名:", cands)
    lang_leaves = collections.Counter()
    for n, mod in m.named_modules():
        if isinstance(mod, nn.Linear) and "language_model" in n:
            lang_leaves[n.rsplit(".", 1)[-1]] += 1
    print("    语言塔叶子名:", sorted(lang_leaves))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
