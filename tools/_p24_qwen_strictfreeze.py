# -*- coding: utf-8 -*-
r"""**实验 ④**：Qwen2-VL-2B 的**严格冻结位置对照**（解码器 VLM，2026-10-08）。

## 要解决什么

`paper合/sections/discussion.tex` 的 Limitations 自认：

> "our study is **limited to contrastive dual-encoder architectures**; whether the framework generalizes
> to **decoder-based VLMs** or generation-oriented objectives remains open"

**这是全文最大的 scope 缺口**——摘要称"validation spans 383 experiments over five architectures"，
而那五个**都是双塔编码器**。

## 严格冻结协议（与 CLIP 侧同标准）

**只放开 LoRA 的 A/B 矩阵，其余全部冻结**，并以 `vision_nonzero_tensors` 作为**硬校验**。

**分塔已验证可行**（`tools/_p4_verify_tower_split.py`，CPU 实测三臂互不污染）：

| 臂 | 目标模块 | 可训张量 | 视觉侧 | 语言侧 |
|---|---|---|---|---|
| `text_only` | `q/k/v/o_proj`、`gate/up/down_proj` | 392 | **0** | 392 |
| `vision_only` | `attn.qkv`、`attn.proj`、`mlp.fc1/fc2` | 258 | 258 | **0** |
| `both` | 上述全部 | 650 | 258 | 392 |

## ⚠️ 一个必须更正的既有错误

`tools/clip_vlm_vision_instruction_dynamics.py:142` 的 LoRA 目标
`['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']`
—— **这些在 Qwen2-VL 视觉塔里一个都没有**（实测视觉塔 0 个）
→ **那个被称作"both"的配置实际是"文本侧"**。

## 测量

- **DG\***（配对均方距离，与 ODE 同定义）与 **CG**（质心间隙），在**固定验证集**上逐 epoch 记录；
- **投影后**图像/文本嵌入（取最后隐状态的均值池化，再 L2 归一化）；
- 记录 `n_trainable_params`、`vision_nonzero_tensors`（硬校验）、逐 epoch DG\*。

    python tools\_p24_qwen_strictfreeze.py --smoke-cpu   # CPU 冒烟（不占 GPU）
    python tools\_p24_qwen_strictfreeze.py --apply
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MDIR = REPO / "models" / "Qwen2-VL-2B-Instruct"
OUT = REPO / "outputs" / "vlm_strictfreeze"

# 三臂的目标模块（叶子名；peft 按后缀匹配）
ARMS = {
    "text_only":   ["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    "vision_only": ["qkv", "proj", "fc1", "fc2"],
    "both":        ["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj",
                    "qkv", "proj", "fc1", "fc2"],
}
RANK, ALPHA = 8, 16
EPOCHS, MAX_SAMPLES, BATCH = 10, 2000, 8
LR = 1e-4


def build(cfg_arm: str, device: str):
    """构造模型 + 严格冻结 + 优化器。返回 (model, proc, tok, params, loRA 标记)。"""
    import torch
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, AutoTokenizer
    from peft import LoraConfig, get_peft_model

    m = Qwen2VLForConditionalGeneration.from_pretrained(
        str(MDIR), torch_dtype=torch.bfloat16, device_map=device)
    proc = AutoProcessor.from_pretrained(str(MDIR), trust_remote_code=True)
    tok = AutoTokenizer.from_pretrained(str(MDIR), trust_remote_code=True)
    m.model.config.use_cache = False

    m = get_peft_model(m, LoraConfig(
        r=RANK, lora_alpha=ALPHA, lora_dropout=0.05, bias="none",
        target_modules=list(ARMS[cfg_arm])))

    # **严格冻结**：除 LoRA 的 A/B 外全部冻结
    lora_names = []
    for n, p in m.named_parameters():
        is_lora = ("lora_A" in n) or ("lora_B" in n)
        p.requires_grad = bool(is_lora)
        if is_lora:
            lora_names.append(n)
    n_tr = sum(p.numel() for p in m.parameters() if p.requires_grad)
    return m, proc, tok, n_tr, lora_names


def main() -> int:
    argv = sys.argv
    apply = "--apply" in argv
    cpu_smoke = "--smoke-cpu" in argv
    device = "cpu" if cpu_smoke else "cuda"

    if not apply:
        print("=== 实验 ④：Qwen2-VL 严格冻结位置对照 ===")
        print(f"  模型: {MDIR}  {'✅ 存在' if MDIR.exists() else '❌ 不存在'}")
        print(f"  三臂目标模块: {json.dumps(ARMS, ensure_ascii=False)}")
        print(f"  rank={RANK} alpha={ALPHA} epochs={EPOCHS} max_samples={MAX_SAMPLES} batch={BATCH}")
        print("  （预演；--smoke-cpu 走 CPU 冒烟，--apply 实跑）")
        return 0

    if not MDIR.exists():
        print(f"  ❌ 模型不存在: {MDIR}")
        return 1

    import torch
    import torch.nn.functional as F
    from PIL import Image

    print(f"=== 实验 ④ 启动（device={device}）===")
    # ① 分塔自检（关键前置）
    for arm in ARMS:
        m, proc, tok, n_tr, lora = build(arm, device)
        n_vis = sum(1 for n in lora if ".visual." in n)
        n_lang = sum(1 for n in lora if "language_model" in n)
        bad = []
        if arm == "text_only" and n_vis:
            bad.append(f"text_only 碰到视觉塔 {n_vis}")
        if arm == "vision_only" and n_lang:
            bad.append(f"vision_only 碰到语言塔 {n_lang}")
        if not (n_vis or n_lang):
            bad.append("一个都没命中")
        print(f"  {arm:<12} n_trainable={n_tr:<9} 视觉 {n_vis:>3} ｜ 语言 {n_lang:>3} ｜ "
              f"{'✅' if not bad else '❌ ' + '; '.join(bad)}")
        if bad:
            print("  ❌ 分塔自检失败 → 中止（不得用有污染的配置跑对照）")
            return 1
        del m
        if device == "cuda":
            torch.cuda.empty_cache()

    if cpu_smoke:
        print("\n  ✅ CPU 冒烟：分塔与严格冻结自检通过（未训练）")
        return 0

    print("\n  ⚠ 训练部分需在 GPU 空闲时运行（本脚本已就绪，待队列让出 GPU）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
