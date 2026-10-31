# -*- coding: utf-8 -*-
r"""落账：实验 ④ 脚本就绪 + CPU 冒烟通过（2026-10-08 08:10）。

    python tools\_docs_vlm_ready.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-08 08:10 —— 实验 ④（解码器 VLM 对照）脚本就绪，CPU 冒烟通过**
>
> ### 这条要解决论文自认的最大 scope 缺口
>
> `discussion.tex` Limitations 原文：
> > "our study is **limited to contrastive dual-encoder architectures**; whether the framework
> > generalizes to **decoder-based VLMs** or generation-oriented objectives remains open"
>
> 而摘要称验证跨"five architectures" —— **那五个都是双塔编码器**。
>
> ### 脚本与冒烟结果
>
> **脚本**：`tools/_p24_qwen_strictfreeze.py`（严格冻结，仅放开 LoRA A/B）
> **CPU 冒烟**：`--apply --smoke-cpu`（**只用 CPU，不影响 GPU 队列**）
>
> | 臂 | n_trainable | 视觉侧 | 语言侧 | 判定 |
> |---|---|---|---|---|
> | `text_only` | 9,232,384 | **0** | 392 | ✅ |
> | `vision_only` | 5,262,528 | 258 | **0** | ✅ |
> | `both` | 14,494,912 | 258 | 392 | ✅ |
>
> **分塔靠"叶子名不同"实现**（视觉塔 `attn.qkv`/`attn.proj`/`mlp.fc1|fc2`；
> 语言塔 `q/k/v/o_proj`/`gate|up|down_proj`），peft 按后缀匹配 → **三臂互不污染**（已断言）。
>
> ### ⚠️ 顺带确认的既有错误（**须改 A2 论文**）
>
> `tools/clip_vlm_vision_instruction_dynamics.py:142` 的 LoRA 目标
> `['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']`
> —— **这些在 Qwen2-VL 视觉塔里一个都没有** → **那个被称作 "both" 的配置实际是"文本侧"**。
>
> ### 训练成本（待 GPU）
>
> Qwen2-VL-2B，rank 8，2000 样本，batch 8，10 epoch —— **8 GB 可跑**（4-bit 或 bf16 需实测）。
> 三臂合计估计 **3–4 h**。
>
> ### 队列位置
>
> **排在 COCO 补跑之后**（COCO 已在跑 36 h，打断会浪费；④ 可续跑且不阻塞中心论断）。
> **优先级说明**：④ 补的是 **scope**（审稿人会问），A 与同秩对照补的是**中心论断的正确性** → 后者优先。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "实验 ④（解码器 VLM 对照）脚本就绪" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("解码器 VLM 对照", "9,232,384", "5,262,528", "14,494,912", "视觉塔里一个都没有"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
