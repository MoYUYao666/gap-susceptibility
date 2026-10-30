# -*- coding: utf-8 -*-
r"""Record the Paper A corrections and the scoped impact on P3.

    python tools/_p800_record_edits.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📝 2026-10-15 18:30 —— 两稿修订：**Paper A 已改并编译通过；P3 核心主张确认不受影响，无需改**
>
> ### 一、✅ Paper A 已改（`tools/_p797`，2 处，最小必要改动）
>
> **改动 1 —— 补上 COCO 检索证据**（`sections/empirical.tex` 的 "Retrieval protocol" 段）
>
> 原文已诚实排除 COCO 检索列（*"their recorded accuracies are at chance: $R@1 = 1/5000$ … we do
> not treat their retrieval column as evidence about retrieval"*）。修订后在该段末追加实测：
>
> > *"That deficiency is repairable, and we repaired it: with the training and evaluation splits
> > disjoint, a unique-image gallery, and all five captions per image retained, the same three
> > adaptation positions over $10{,}000$ COCO training and $3{,}000$ evaluation images give
> > $R@1 = 0.579$ frozen, $0.607 \\pm 0.002$ for text-only and $0.624 \\pm 0.001$ for both-position,
> > over three seeds. Adaptation is therefore measurably useful on MS-COCO, but on retrieval it does
> > not reproduce the text-only advantage the alignment columns show: both-position is the higher
> > of the two."*
>
> **⇒ 这把论文此前**主动放弃**的 COCO 检索列变成了**正面证据**，并如实说明它**不支持** text-only 优势。
>
> **改动 2 —— 方法披露**（同段末追加"第四点 caution"）
>
> > 说明低秩适配 wrapper **只冻结了它替换的那几个投影**，其余塔参数仍在训练：
> > adapter 占 $196{,}608$ / $145{,}170{,}177$（**0.14%**）⇒ **那些 run 是"整塔微调 + 小适配器"，不是低秩适配**，
> > **其 rank 消融不能读作 rank 效应**；并声明**严格冻结（只训练适配器矩阵）的列不受影响**，
> > 且已用冻结基座重跑仅适配器的配置（$196{,}608$ / $491{,}520$ 可训练参数），**复现了相同的检索排序**。
>
> **编译**：**64 页 / 0 错误** ✅（原 63 页，新增两段）
>
> ### 二、✅ P3 核心主张**不受影响**（**无需修改**）
>
> | 稿件 | LoRA 实现 | 是否冻结基座 |
> |---|---|---|
> | **P3**（`paper3/scripts/run_training.py`、`run_training_qwen.py`）| **`from peft import LoraConfig, get_peft_model`**（HuggingFace 官方库）| ✅ **官方库正确冻结** |
> | **Paper A**（`src/lora.py`）| **自写 `apply_lora_to_model`** | 🔴 **不冻结**（缺陷） |
>
> **⇒ P3 的 LLaVA / Qwen rank 实验（`r_c \\in [5,6]`、15 个 rank 单调增长、Spearman）走的是官方 `peft`**，
> **不受此缺陷影响**。P3 里只有 `outputs/route_c/d/e` 那 **16 个 CLIP run** 受影响，
> 而它们**不是 P3 rank 主张的来源**。
>
> **⚠️ P3 的 R1 已投出，PDF 无法更改。**源码层面无需改动；若日后进入下一轮，可补一句方法说明。
>
> ### 三、📋 受影响范围最终认定（`tools/_p793`、`_p799`）
>
> | 归属 | run 数 | 是否影响该稿结论 |
> |---|---|---|
> | **Paper A**（`flickr30k` 29、`theory` 21、`coco` 7、`blip2` 5、`siglip` 5、`vitl` 2）| **69** | 🔴 **影响**（rank 消融与 LoRA 命名）|
> | **P3 + Paper A 共用**（`theory/v1_trajectory` 46）| **46** | 🟡 多为 ODE 拟合（gap 轨迹），**非 rank 消融** |
> | **P3**（`route_c/d/e` 16）| **16** | 🟡 非核心主张来源 |
> | **合计** | **131** | |
>
> ### 四、⏳ 仍在进行
>
> 1. **Paper A 的 rank 消融重跑**：需用冻结基座重跑 `r ∈ {1,...,64}` 才能让 rank 主张重新成立
>    （当前仅在 $r=8$ 上验证了"真 LoRA 可用"）；
> 2. **`flickr30k` 29 个 run** 的同类重跑（Paper A 的 ODE 拟合基于它们）；
> 3. **发布库同步**（`publish_clean`）—— `src/lora.py` 与 `src/trainer.py` 的修复需推上去，
>    **待操作者确认**。
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
    if "P3 核心主张确认不受影响" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("P3 核心主张确认不受影响", "get_peft_model", "0.14%", "64 页", "第四点 caution"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
