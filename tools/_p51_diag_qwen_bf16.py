# -*- coding: utf-8 -*-
r"""诊断：Qwen2-VL 的 `vision_only` 在 **bf16（原量化）** 下能否跑，以及为何慢（2026-10-08）。

## 实测背景

| 配置 | `vision_only` 速度 |
|---|---|
| bf16，batch 4 | **>27 min 未完成 1 个 epoch**（`text_only` 为 2.4 min/epoch） |
| 4-bit，batch 4 | 5.4 min / 3 epoch |

## 假设（本脚本逐项实测）

| # | 假设 | 检验 |
|---|---|---|
| **H1** | 显存不足导致反复重试/碎片 | 测单步峰值显存 |
| **H2** | `vision_only` 时**语言塔虽冻结仍参与反传**（计算图穿过整个 LLM） | 对冻结参数设 `requires_grad=False` 并比较单步耗时 |
| **H3** | 视觉塔的 LoRA 落在 `attn.qkv` 等大矩阵上，激活量大 | 打印各目标层形状 |

## 判据（先写明）

若 **bf16 单步耗时可接受（< 2 s/step）** → 可跑原量化；
否则须换配置（更大 batch 反而更慢，故考虑**梯度检查点**或**缩小视觉 token 数**）。

    python tools\_p51_diag_qwen_bf16.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
MDIR = REPO / "models" / "Qwen2-VL-2B-Instruct"


def main() -> int:
    import torch
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    from peft import LoraConfig, get_peft_model

    print("=== H1/H3：模型与目标层形状（bf16）===")
    t0 = time.time()
    m = Qwen2VLForConditionalGeneration.from_pretrained(
        str(MDIR), torch_dtype=torch.bfloat16, device_map="cuda", low_cpu_mem_usage=True)
    proc = AutoProcessor.from_pretrained(str(MDIR), trust_remote_code=True)
    m.config.use_cache = False
    print(f"  加载耗时 {time.time()-t0:.1f}s ｜ 显存 "
          f"{torch.cuda.memory_allocated()/2**30:.2f} GB", flush=True)

    m = get_peft_model(m, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05, bias="none",
                                     target_modules=["qkv", "proj", "fc1", "fc2"]))
    for n, p in m.named_parameters():
        p.requires_grad = ("lora_A" in n) or ("lora_B" in n)
    n_vis = sum(1 for n, p in m.named_parameters() if p.requires_grad and ".visual." in n)
    print(f"  vision_only 可训张量 {n_vis} ｜ 显存 {torch.cuda.memory_allocated()/2**30:.2f} GB",
          flush=True)

    print("\n=== 视觉塔 LoRA 目标层的形状（H3）===")
    shown = 0
    for n, mod in m.named_modules():
        if n.endswith(("attn.qkv", "attn.proj", "mlp.fc1", "mlp.fc2")) and hasattr(mod, "weight"):
            print(f"    {n:<40} {tuple(mod.weight.shape)}")
            shown += 1
            if shown >= 4:
                break

    print("\n=== H2：单步耗时（前向+反向+优化），bf16，batch 1 ===")
    from PIL import Image
    import numpy as np
    img = Image.fromarray((np.random.rand(224, 224, 3) * 255).astype("uint8"))
    params = [p for p in m.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=1e-4)

    for batch in (1, 2):
        texts = [proc.apply_chat_template(
            [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": f"a photo {i}"}]}],
            tokenize=False, add_generation_prompt=True) for i in range(batch)]
        inp = proc(text=texts, images=[img] * batch, return_tensors="pt", padding=True).to("cuda")
        torch.cuda.reset_peak_memory_stats()
        try:
            t0 = time.time()
            out = m(**inp, output_hidden_states=True)
            fwd = time.time() - t0
            hid = out.hidden_states[-1]
            loss = hid.float().pow(2).mean()
            t1 = time.time()
            loss.backward()
            bwd = time.time() - t1
            opt.step(); opt.zero_grad()
            peak = torch.cuda.max_memory_allocated() / 2**30
            print(f"  batch={batch}: 前向 {fwd:.2f}s ｜ 反向 {bwd:.2f}s ｜ 合计 {fwd+bwd:.2f}s "
                  f"｜ 峰值显存 {peak:.2f} GB", flush=True)
        except torch.OutOfMemoryError as e:
            print(f"  batch={batch}: ❌ OOM（{str(e)[:60]}）", flush=True)

    print("\n=== 结论 ===")
    print("  若 batch=1 的单步合计 < 2s，且峰值 < 7 GB → bf16 可跑（200 步/epoch ≈ 数分钟）")
    print("  若 OOM 或 > 5s/步 → 须换配置（梯度检查点 / 更小视觉分辨率 / 保留 4-bit）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
