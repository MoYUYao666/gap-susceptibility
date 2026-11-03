# -*- coding: utf-8 -*-
r"""给实验 ④ 加 **bf16（原量化）** 支持：**预计算输入张量**消除处理器瓶颈（2026-10-08）。

## 实测根因

| 配置 | `vision_only` 速度 |
|---|---|
| bf16 + **每批调处理器** | **>27 min 未完成 1 个 epoch** |
| 4-bit + 每批调处理器 | 5.4 min / 3 epoch |
| **bf16 + 预计算** | **单步 0.47s（batch 2）→ 200 步 ≈ 94 s/epoch**（`tools/_p51` 实测） |

**慢的不是模型，是我的数据管线**：`pooled_features` 每批都调
`apply_chat_template` + 处理器，**对同一批图像反复预处理**。

## 修法

1. 加 `precompute_inputs(proc, batches)`：**一次性**算好全部输入张量；
2. **在 arms 循环内、`build()` 之后**调用它（`proc` 那时才存在）；
3. 训练与评估循环都用缓存。

    python tools\_p52_qwen_precompute2.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p47_qwen_train.py"

PF_OLD = '''def pooled_features(model, proc, images, captions, device, proj_i, proj_t):
    """返回 (I, T)：两塔最后一层隐状态的均值池化 → 固定投影 → L2 归一化。"""
    import torch
    import torch.nn.functional as F
'''

PF_NEW = '''def precompute_inputs(proc, batches):
    """**一次性**算好全部批次的输入张量 → 消除每批调处理器的瓶颈。

    实测（`tools/_p51_diag_qwen_bf16.py`）：bf16 下 forward+backward 只要 **0.47s（batch 2）**，
    但每批重跑处理器会让 `vision_only` **>27 min 跑不完 1 个 epoch**。
    **瓶颈在数据管线，不在模型。**
    """
    cache = []
    for b in batches:
        content = [[{"type": "image"}, {"type": "text", "text": str(c)}] for c in b["caption"]]
        texts = [proc.apply_chat_template([{"role": "user", "content": c}],
                                         tokenize=False, add_generation_prompt=True)
                 for c in content]
        inp = proc(text=texts, images=[im for im in b["image"]],
                   return_tensors="pt", padding=True)
        cache.append(dict(inp))
    return cache


def pooled_features(model, proc, images, captions, device, proj_i, proj_t, cached=None):
    """返回 (I, T)：两塔最后一层隐状态的均值池化 → 固定投影 → L2 归一化。

    `cached` 非空时**直接用预计算张量**（不再调处理器）——训练循环始终传它。
    """
    import torch
    import torch.nn.functional as F

    if cached is not None:
        inp = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in cached.items()}
        out = model(**inp, output_hidden_states=True)
        hid = out.hidden_states[-1]
        mask = inp["attention_mask"].unsqueeze(-1).to(hid.dtype)
        T = (hid * mask).sum(1) / mask.sum(1).clamp(min=1)
        tok = inp["input_ids"]
        vis_mask = ((tok >= 151652) & (tok <= 151656)).unsqueeze(-1).to(hid.dtype)
        n_vis = vis_mask.sum(1)
        I = (hid * vis_mask).sum(1) / n_vis.clamp(min=1) if float(n_vis.min()) > 0 else T
        return (F.normalize(proj_i(I.float()), p=2, dim=-1),
                F.normalize(proj_t(T.float()), p=2, dim=-1))
'''

# 在 build() 之后插入预计算
ANCHOR = '''        params = [p for p in model.parameters() if p.requires_grad]'''
INSERT = '''        # **预计算输入**（处理器只调一次）→ 训练与评估都复用
        if "_cache" not in dir():
            pass
        _t0 = time.time()
        CACHE = precompute_inputs(proc, batches)
        print(f"     预计算 {len(CACHE)} 批（{time.time()-_t0:.1f}s）", flush=True)

        params = [p for p in model.parameters() if p.requires_grad]'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "precompute_inputs" in t:
        print("  已改，跳过")
        return 0
    if t.count(PF_OLD) != 1:
        print(f"  ❌ pooled_features 锚点命中 {t.count(PF_OLD)}")
        return 1
    if t.count(ANCHOR) != 1:
        print(f"  ❌ params 锚点命中 {t.count(ANCHOR)}")
        return 1
    t = t.replace(PF_OLD, PF_NEW, 1)
    t = t.replace(ANCHOR, INSERT, 1)
    # 训练循环用缓存
    old_tr = '''                I, T = pooled_features(model, proc, imgs, b["caption"], device, proj_i, proj_t)'''
    assert t.count(old_tr) == 1, "训练调用锚点未命中"
    t = t.replace(old_tr, '''                I, T = pooled_features(model, proc, imgs, b["caption"], device,
                                       proj_i, proj_t, cached=CACHE[bi])''', 1)
    # 评估循环用缓存
    old_ev = '''                for b in batches:
                    i_, t_ = pooled_features(model, proc, [im for im in b["image"]],
                                             b["caption"], device, proj_i, proj_t)'''
    assert t.count(old_ev) == 1, "评估调用锚点未命中"
    t = t.replace(old_ev, '''                for _bi, b in enumerate(batches):
                    i_, t_ = pooled_features(model, proc, [im for im in b["image"]],
                                             b["caption"], device, proj_i, proj_t,
                                             cached=CACHE[_bi])''', 1)
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "def precompute_inputs" in t2 and "cached=CACHE[bi]" in t2 and "cached=CACHE[_bi]" in t2
    print("  ✅ 已加：预计算输入（处理器一次性）+ 训练/评估均用缓存")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
