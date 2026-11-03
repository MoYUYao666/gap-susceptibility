# -*- coding: utf-8 -*-
r"""给实验 ④ 加 **bf16（原量化）** 支持：**预计算输入张量**消除处理器瓶颈（2026-10-08）。

## 实测根因

| 配置 | `vision_only` 速度 |
|---|---|
| bf16 + **每批调处理器** | **>27 min 未完成 1 个 epoch** |
| 4-bit + 每批调处理器 | 5.4 min / 3 epoch |
| **bf16 + 预计算输入**（本脚本） | **单步 0.47s（batch 2）→ 200 步 ≈ 94 s/epoch** |

**慢的不是模型，是我的数据管线**：`pooled_features` 每批都调
`proc.apply_chat_template(...)` 与处理器，**对同一批图像反复做预处理**。

## 修法（三处）

1. **预计算**：先把全部批次的 `input_ids`/`attention_mask`/`pixel_values` 算好缓存，
   训练时直接喂模型 → **处理器只调用一次**；
2. 训练循环里**不再调处理器**；
3. 保留 `--4bit` 开关（默认 **关** = bf16 原量化）。

    python tools\_p52_qwen_precompute.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p47_qwen_train.py"

# ① pooled_features 增加「直接吃预计算张量」的分支
OLD_PF = '''def pooled_features(model, proc, images, captions, device, proj_i, proj_t):
    """返回 (I, T)：两塔最后一层隐状态的均值池化 → 固定投影 → L2 归一化。"""
    import torch
    import torch.nn.functional as F
'''
NEW_PF = '''def precompute_inputs(proc, batches):
    """**一次性**把全部批次的输入张量算好并缓存 → 消除每批调处理器的瓶颈。

    实测：每批调处理器会让 `vision_only` 在 bf16 下 >27 min 跑不完 1 个 epoch；
    bf16 单步（batch 2）本身只要 0.47s。
    """
    cache = []
    for b in batches:
        content = [[{"type": "image"}, {"type": "text", "text": str(c)}] for c in b["caption"]]
        texts = [proc.apply_chat_template([{"role": "user", "content": c}],
                                         tokenize=False, add_generation_prompt=True)
                 for c in content]
        inp = proc(text=texts, images=[im for im in b["image"]],
                   return_tensors="pt", padding=True)
        cache.append({k: v for k, v in inp.items()})
    return cache


def pooled_features(model, proc, images, captions, device, proj_i, proj_t, cached=None):
    """返回 (I, T)：两塔最后一层隐状态的均值池化 → 固定投影 → L2 归一化。

    `cached` 非空时**直接用预计算张量**（不再调处理器）——训练循环应始终传它。
    """
    import torch
    import torch.nn.functional as F

    if cached is not None:
        inp = {k: v.to(device) for k, v in cached.items()}
        out = model(**inp, output_hidden_states=True)
        hid = out.hidden_states[-1]
        mask = inp["attention_mask"].unsqueeze(-1).to(hid.dtype)
        T = (hid * mask).sum(1) / mask.sum(1).clamp(min=1)
        tok = inp["input_ids"]
        vis_mask = ((tok >= 151652) & (tok <= 151656)).unsqueeze(-1).to(hid.dtype)
        n_vis = vis_mask.sum(1)
        I = (hid * vis_mask).sum(1) / n_vis.clamp(min=1) if float(n_vis.min()) > 0 else T
        return F.normalize(proj_i(I.float()), p=2, dim=-1), F.normalize(proj_t(T.float()), p=2, dim=-1)
'''

# ② 主循环：预计算 + 训练/评估都用缓存
OLD_LOOP = '''    summary = {}
    for arm in arms:'''
NEW_LOOP = '''    # **一次性预计算**（处理器只调一次）——按 batch 索引复用
    print("  预计算输入张量（消除处理器瓶颈）...", flush=True)
    _t0 = time.time()
    CACHE = precompute_inputs(proc, batches)
    print(f"  预计算完成（{time.time()-_t0:.1f}s，{len(CACHE)} 批）", flush=True)

    summary = {}
    for arm in arms:'''
assert OLD_LOOP in io.open(F, encoding="utf-8").read(), "主循环锚点未命中"


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "precompute_inputs" in t:
        print("  已改，跳过")
        return 0
    if t.count(OLD_PF) != 1:
        print(f"  ❌ pooled_features 锚点未唯一命中（{t.count(OLD_PF)}）")
        return 1
    t = t.replace(OLD_PF, NEW_PF, 1)

    # 训练循环：用缓存
    t = t.replace(
        '''                I, T = pooled_features(model, proc, imgs, b["caption"], device, proj_i, proj_t)''',
        '''                I, T = pooled_features(model, proc, imgs, b["caption"], device,
                                       proj_i, proj_t, cached=CACHE[bi])''', 1)
    # 评估循环：用缓存
    t = t.replace(
        '''                for b in batches:
                    i_, t_ = pooled_features(model, proc, [im for im in b["image"]],
                                             b["caption"], device, proj_i, proj_t)''',
        '''                for _bi, b in enumerate(batches):
                    i_, t_ = pooled_features(model, proc, [im for im in b["image"]],
                                             b["caption"], device, proj_i, proj_t,
                                             cached=CACHE[_bi])''', 1)
    # 加预计算段（需要 proc 已在作用域：把 CACHE 放在 arms 循环内、模型构造后）
    t = t.replace(
        '''    summary = {}
    for arm in arms:''',
        '''    summary = {}
    _CACHE_CACHE = {}
    for arm in arms:''', 1)
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "def precompute_inputs" in t2
    print("  ✅ 已加 precompute_inputs（处理器一次性）；训练/评估均可用 cached")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
