# -*- coding: utf-8 -*-
r"""落账：CLIP B/16 是 patch-size 规律的**反例**（2026-10-08 07:50）。

    python tools\_docs_b16_counterexample.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴🔴 2026-10-08 07:50 —— CLIP B/16 是 patch-size 规律的**反例**（本阶段最重要的结果）**
>
> ### 先说好消息：**论文现有表格 100% 可复现**
>
> 按唯一原则逐项复算 `tab:position_strict` 的 **12 个数字**（脚本 `tools/_verify_position_table2.py`）：
> **复算失败 0 项 ｜ 违反规律 0 个**。论文没编造。
>
> | 骨干 | patch | Text-only | Both | Vision-only | 最保护 | 复现 |
> |---|---|---|---|---|---|---|
> | CLIP B/32 (WIT) | 32 | **−0.0465** | −0.0258 | +0.0106 | text_only | ✅ n=5 |
> | OpenCLIP B/32 (LAION) | 32 | **+0.0694** | +0.0881 | +0.0925 | text_only | ✅ n=5 |
> | SigLIP B/16 | 16 | +0.0664 | **−0.0114** | +0.0522 | both | ✅ n=5 |
> | BioCLIP B/16 | 16 | −0.3671 | **−0.4515** | −0.2927 | both | ✅ n=3 |
>
> ⚠️ **证据强度须区分**：前三个是**逐 run 可复算**；
> **BioCLIP 只有汇总**（`outputs/strict_freeze_bioclip/results_partial.json:summary`，
> 注明"操作者于 2026-10-06 要求停止，rank 4 已完成、rank 8 未完成"，
> 由 `tools/_exp3_bioclip_harvest.py` **从运行日志解析落盘**）→ **无逐 run `results.json`**。
>
> ### 🔴 坏消息：**新增的 CLIP B/16 违反规律**
>
> **CLIP B/16（rank 4，5000 样本，严格冻结，实测）**：
>
> | 臂 | CGΔ | R@1 |
> |---|---|---|
> | **text_only** | **−0.0190** | 0.642 |
> | both | +0.0150 | 0.696 |
> | vision_only | *(运行中)* | |
>
> **→ 最保护臂 = `text_only`，而论文规律要求 patch-16 骨干应为 `both`。**
>
> ### 为什么这条特别关键
>
> 论文自认：*"domain shift alone could account for its ordering; and with two backbones per patch size
> the two are not separated."* —— **CLIP B/16 正是那个能把 patch size 与模型身份分开的对照**：
> **同族（CLIP）、同预训练目标（WIT）、仅 patch size 不同（32→16）**。
>
> **它给出的是 patch-32 的排序，不是 patch-16 的排序。**
>
> ### 可能的解释（须先验证，不得直接采信）
>
> | 假说 | 验证方式 |
> |---|---|
> | **H1：规律是 BioCLIP/SigLIP 的个体特征** | 已有证据支持：两个 patch-16 骨干恰好都是**非 WIT 预训练**（SigLIP 为 sigmoid 目标，BioCLIP 为生物域） |
> | **H2：需对照 CLIP B/32 在完全相同协议下的排序** | ✅ 已有：CLIP B/32（r8, 5 seed）= text_only 最保护 —— **但 r8 vs 我 r4 不同秩** |
> | **H3：我给的是 rank 4，论文 patch-16 组是 rank 4，但 CLIP B/32 组是 rank 8** | **须补 CLIP B/32 的 rank 4** 才能同秩对照 |
>
> **→ 最干净的下一步：补 `CLIP B/32 @ rank 4`**（成本 ~35 min/臂），
> 与 CLIP B/16 @ rank 4 **同秩对照**，才能判定"排序由 patch size 决定"还是"由预训练目标决定"。
>
> ### 待办
>
> 1. 等 ③b `vision_only` 完成 → 补齐该行；
> 2. **补 CLIP B/32 @ rank 4**（同秩对照）；
> 3. 依结果**修改论文**：若 CLIP B/16 结论稳固，`empirical.tex` 的规律必须**收窄为
>    "在 WIT 预训练的 CLIP 系内，patch-32 → text-only、patch-16 → ?"** 或**改为按预训练目标分组**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "CLIP B/16 是 patch-size 规律" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("复算失败 0 项", "CLIP B/16 违反规律", "同秩对照", "results_partial.json"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
