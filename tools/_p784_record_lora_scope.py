# -*- coding: utf-8 -*-
r"""Record the LoRA-scope defect and its consequences.

    python tools/_p784_record_lora_scope.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴🔴 2026-10-15 15:00 —— 重大发现：所有标注 "LoRA rank r" 的实验**实际训练了整个文本塔**，LoRA 只占 0.135%**
>
> ### 一、我怎么发现的
>
> 追查"t2i 0.31 vs i2t 0.93 不对称"这项局限时，发现**我自己的 `evaluate()` 有重复计数 bug**（i2t 报出 R@1 = **2.0317 > 1**，不可能）。
> 修 bug 后想用 checkpoint 重评，结果 `load_state_dict` **0 个张量匹配** ⇒ 一路查到 checkpoint 只存 `lora_state_dict` ⇒ 再查到**可训练参数是 145,170,177（95.84%）**。
>
> ### 二、🔴 缺陷：LoRA 注入**不冻结基座**
>
> `src/lora.py`：
> - `apply_lora_to_model()` **只注入 LoRA 层，不冻结任何基座权重**；
> - `LoRALinear.__init__()` 里 `self.original.weight.requires_grad_(False)` **只冻结被包装的那一层**（即 `q_proj`/`v_proj` 的**原权重**）。
>
> **⇒ 只加 LoRA 的 24 个 q/v 投影被冻结，文本塔其余参数全部保持可训练。**
>
> **实测（`tools/_p783`）**：
>
> | 项 | 值 |
> |---|---|
> | 模型总参数 | **151,473,921** |
> | 可训练张量 | **398** |
> | ├ LoRA 张量 | **48**（**196,608** 参数） |
> | └ 普通塔张量 | **350**（**144,973,569** 参数） |
> | **LoRA 占可训练参数比** | **0.1354%** |
>
> **可训练的"塔"参数实例**：`text_model.embeddings.token_embedding.weight`、
> `text_model.embeddings.position_embedding.weight`、`text_model.encoder.layers.*.layer_norm{1,2}.*`、
> `text_model.encoder.layers.*.mlp.fc1.*`、`text_model.encoder.layers.*.self_attn.k_proj/out_proj.*`
> —— **都不是 LoRA 参数**。
>
> ### 三、🔴 影响范围：**档案里的 LoRA 结果全部受此影响**
>
> | 证据 | 值 |
> |---|---|
> | 档案 `outputs/theory/coco/coco_text_r8/seed42` 的 `n_trainable_params` | **145,170,177** |
> | 本轮 scale-up `text_only` 配置的可训练参数 | **145,170,177**（同值）|
> | 纯 rank-8 LoRA（文本塔）应为 | **196,608** |
>
> **⇒ 档案与本次实验里所有 "LoRA r=8" 的 run，实际训练的都是整个文本塔（`apply_to_text=True` 会解冻全塔）。**
>
> **这意味着**：
> 1. **"LoRA rank 8/16/…" 的 rank 消融，测的不是 LoRA 秩** —— 因为 144.97M 个全塔参数在主导优化；
> 2. **`alpha`/`target_modules` 的作用被稀释**（只有 q/v 的原权重被冻结，其余塔权重照常更新）；
> 3. **Paper A / P3 里所有以"LoRA"为名义的结论，其实是"文本塔（或双塔）全量微调"的结论**；
> 4. **"full_ft" 与 "LoRA" 的对比，实质是"全模型微调 vs 文本塔微调"**，而非"全量 vs 低秩"。
>
> ### 四、🔴 附带缺陷：checkpoint 不完整
>
> `best_checkpoint.pt` 只存 `lora_state_dict`（24 模块 / 48 张量），**144,973,569 个可训练塔参数未保存**
> ⇒ **微调后的模型无法从 checkpoint 复现**。
> （已确认 LoRA 张量确实被训练过：12/12 检查项与初始值不同。）
>
> ### 五、🔴 我自己的失误：`evaluate()` 的重复计数 bug
>
> | 实现 | i2t R@1 |
> |---|---|
> | **loop + topk（正确）** | **0.4203** |
> | plain argmax（正确，与 loop 一致） | **0.4203** |
> | **我的分块实现（错）** | **2.0317** ← **R@1 > 1，铁证** |
>
> **根因**：分块版把"该图的某条 caption 命中"按 **caption 行**累加（`hits += ...`），
> 同一张图的 5 条 caption 各命中一次就计 5 次，再除以图数 ⇒ **重复计数**。已改为按图**去重**（`hit |=`）并加 `assert 0 <= R@1 <= 1`。
> **⇒ 先前上报的 `i2t 0.9157 / 0.9293` 等数字全部作废**；正确值见下。
>
> ### 六、✅ 修正后的规模跑数字（冻结基线，3,000 图 gallery，逐例循环验证）
>
> | 口径 | R@1 | R@5 | R@10 |
> |---|---|---|---|
> | **i2t** | **0.4203** | 0.6867 | 0.7870 |
> | **t2i** | **0.2431** | 0.4668 | 0.5736 |
>
> **⇒ 两者都在 CLIP ViT-B/32 的合理范围内，"不对称问题"不存在**（原本的不对称是那个 bug 造成的）。
>
> ### 七、下一步（**必须做，否则规模跑无意义**）
>
> 1. **修 `apply_lora_to_model` 使其真正冻结基座**（或在 `_setup_lora` 里显式冻结除 LoRA 外的全部参数）；
> 2. **重跑**受影响的关键配置，使 "LoRA" 名副其实；
> 3. **修 checkpoint 保存**（保存完整可训练状态，而非只存 LoRA）；
> 4. 重评并重写受影响的结论。
>
> **⚠️ 在此之前，本轮与档案里所有 "LoRA" 数字都只能标注为"文本塔/双塔全量微调"。**
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "所有标注 \"LoRA rank r\" 的实验" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("LoRA rank r", "144,973,569", "0.1354%", "2.0317", "0.4203", "名副其实"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
