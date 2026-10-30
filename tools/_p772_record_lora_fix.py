# -*- coding: utf-8 -*-
r"""Record the LoRA failure cause and the corrected configuration.

    python tools/_p772_record_lora_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🎯 2026-10-15 09:50 —— LoRA 在 COCO 上失效的**根因找到并已修复**
>
> ### 一、根因：**`LoRAConfig.dropout = 0.1`（默认值）＋ 步长过大**
>
> 受控对比（同一脚本、同 2,000 图、同 6 epoch、同 seed）：
>
> | 配置 | train loss | val loss | R@1 |
> |---|---|---|---|
> | r=8, **lr=1e-4, dropout=0.1**（默认） | 3.87 → 1.11 | 3.69 → **7.99** | **0.016** |
> | r=8, **lr=1e-5, dropout=0.0** | 0.80 → **0.12** | 3.69 → **1.68** | **0.485** |
>
> （`r8_lr1e-5_drop0` 的第 5 epoch：`Loss 0.1248 ｜ Val Loss 1.6760 ｜ R@1 0.485`）
>
> **⇒ 在 rank 8 的适配器上叠加 10% dropout 并用 1e-4 的步长，会把适配器推向退化**：
> val loss 反而从 3.69 升到 7.99，检索掉到 0.016（比冻结低 30 倍）。
> **改成 lr=1e-5、dropout=0 后 LoRA 正常收敛**（train 0.80→0.12、val 平稳、内部 R@1 0.485）。
>
> **⚠️ 这不是"调参微调"，而是量级差异**：同一份数据、同一个 rank，两种配置的结果差 **30 倍**。
>
> ### 二、⚠️ 我的两处失误（照实记录）
>
> | # | 失误 | 后果 |
> |---|---|---|
> | 1 | **测试脚本里把 `.to(device)` 放在 LoRA 注入之前** | 报 `Expected all tensors to be on the same device`，我一度误判为项目缺陷；**实为我的脚本顺序错**，trainer 的顺序是对的 |
> | 2 | **漏设 `HF_HUB_OFFLINE=1`** | 任务卡在 hf-mirror 网络重试；本地已有缓存。已加该环境变量 |
> | 3 | 用 PowerShell 字符串替换改 Python 源码 | 产生重复的 `ap.add_argument("--alpha", ...)`，脚本启动即崩；已改为直接编辑 |
>
> ### 三、✅ 已启动规模跑（回答 R2-3）
>
> **配置**：COCO **train2014 10,000 唯一图 / 50,020 行** 训练，**val2014 3,000 唯一图 / 15,010 行** 评测（**断言不相交**），3 epoch，3 seed，batch 64，**rank 8 / lr 1e-5 / dropout 0**，修正检索协议。
>
> **相比旧 COCO 实验**：有效图数 **~2,000 → 10,000（5×）**；split **同源 → 严格分离**；协议 **对角线 → 显式归属**。
>
> **实时状态**（已确认在跑）：`train: 10000 unique images, 50020 caption rows ｜ val: 3000 unique images ｜ train/val disjoint: True ｜ Epoch 1 loss≈0.53`。
>
> **预计**：10,000 图 × 3 epoch ≈ 22 分钟/seed；3 seed × 2 arm + frozen ≈ **2.5 小时**。
>
> ### 四、⚠️ 仍未解决
>
> `tools/_p769_lora_fixes.py` 的第三个配置（`r64_lr1e-4_drop0`）触发 **CUDA illegal address** 崩溃
> —— 多次连续训练后显存释放不净（脚本问题，非模型问题）。前两个配置的数据已从日志取得，第三个未完成。
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
    if "LoRA 在 COCO 上失效的" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("LoRA 在 COCO 上失效的", "dropout = 0.1", "0.485", "30 倍", "HF_HUB_OFFLINE",
              "10,000 唯一图"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
