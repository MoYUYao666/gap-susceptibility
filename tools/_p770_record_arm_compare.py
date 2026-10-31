# -*- coding: utf-8 -*-
r"""Record the arm comparison: full fine-tuning works on COCO, LoRA does not.

    python tools/_p770_record_arm_compare.py --apply"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📊 2026-10-15 09:00 —— 对比结论：**COCO 上全量微调正常、LoRA 灾难性失败**（同一脚本、同数据、同预算）**
>
> ### 一、受控对比（`tools/_p767_arm_compare.py`）
>
> **条件完全相同**：COCO train2014 **2,000 唯一图** / **6 epoch** / batch 64 / seed 42 / 修正协议 / **500 图 gallery**（val2014，与训练不交）。
>
> | arm | lr | train loss | val loss | R@1 | **i2t R@1** | **t2i R@1** |
> |---|---|---|---|---|---|---|
> | **冻结基线** | — | — | — | — | **0.4755** | **0.2857** |
> | **`full_ft`（全量微调，1.51 亿参数）** | 1e-5 | **0.80 → 0.10** | 1.41 → 1.65 | 0.552 | **0.7180** ↑ | 0.3859 |
> | **`lora` rank 8 text-only** | 1e-4 | 3.87 → 1.11 | 3.69 → **7.99** ↑↑ | 0.016 | **0.0240** ↓ | 0.0080 |
>
> ### 二、结论
>
> 1. **COCO 训练通路本身没问题** —— 全量微调正常收敛（train 0.80→0.10），**并把 i2t 检索从冻结的 0.4755 提升到 0.7180**（+51%），val loss 基本平稳（1.41→1.65）；
> 2. **LoRA 是灾难性过拟合**：val loss **3.69 → 7.99**（翻倍多），检索掉到 **0.024**（比冻结低 20 倍）；
> 3. **⇒ 不是"COCO 数据不可学"，是 LoRA 这条路径在 COCO 上失效。**
>
> ### 三、⚠️ 一处必须记录的口径差异（避免日后误读）
>
> 学习率扫描（`_p765`，**4 epoch**）给出 LoRA R@1 = **0.0070**；受控对比（`_p767`，**6 epoch**）给出 **0.0160**。
> **两者都是实测，但 epoch 数不同 ⇒ 只有同脚本内的比较是受控的。** 此处照实并列，不做取舍。
>
> ### 四、对 Paper A 的含义
>
> | 稿件内容 | 判定 |
> |---|---|
> | "COCO R@1 < 0.001（near-random）" | 🔴 **不是模型或数据性质**：冻结 CLIP 就有 0.4755，全量微调能到 0.7180 |
> | "LoRA 在 COCO 上的 cross-dataset validation" | 🔴 **该配置下 LoRA 未学会任务**（检索低于冻结 20 倍） |
> | 审稿人 R1-W4 的怀疑 | ✅ **成立**：*"the retrieval protocol ... should first be carefully verified"* |
>
> ### 五、进行中
>
> `tools/_p769_lora_fixes.py`：测三种 LoRA 修正（**更小步长 1e-5** / **关掉 dropout 0.1** / **加大 rank 到 64**），
> 以判定 LoRA 失效是步长、正则还是容量问题。**结果出来后再决定能否跑 10,000 图规模。**
>
> **⚠️ 诚实标注**：本轮仍未产出可写进稿件的正面数字；产出的是**对现有 COCO 结果的否证 + 一个可用的训练配置（全量微调）**。
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
    if "COCO 上全量微调正常、LoRA 灾难性失败" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("COCO 上全量微调正常、LoRA 灾难性失败", "0.7180", "0.0240", "7.99",
              "只有同脚本内的比较是受控的"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
