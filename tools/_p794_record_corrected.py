# -*- coding: utf-8 -*-
r"""Record the corrected scale-up result, the i2t clarification, and my two misdiagnoses.

    python tools/_p794_record_corrected.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-15 17:30 —— 重跑完成（真 LoRA + 正确 seed）：**结论利好**；并更正我自己的两次误判**
>
> ### 一、✅ 最终结果（COCO train2014 10,000 图 → val2014 3,000 图，修正协议）
>
> | arm | 可训练参数 | n | **R@1** | R@5 | R@10 | i2t R@1 | t2i R@1 |
> |---|---|---|---|---|---|---|---|
> | **frozen** | 0 | 1 | 0.5794 | 0.7300 | 0.7865 | 0.9157 | 0.2431 |
> | **text_only** | **196,608** | 3 | **0.6068 ± 0.0019** | 0.7538 | 0.8107 | 0.9343 | 0.2793 |
> | **both** | 491,520 | 3 | **0.6235 ± 0.0011** | 0.7705 | 0.8251 | 0.9443 | 0.3027 |
>
> **对照：缺陷版（实为整塔微调，145,170,177 参数）** `text_only` 0.6190 ± 0.0024、`both` 0.6230 ± 0.0021。
>
> **⇒ 核心对比**：
> - **真 LoRA 用 `1/738` 的可训练参数，达到与整塔微调同档或更好的检索**（`both` 0.6235 vs 0.6230）；
> - 两者**都显著优于冻结基线**（0.5794）⇒ **适配确实有效**；
> - `both` 稳定高于 `text_only` 约 **+0.017**（各自 sd 约 0.001–0.002）⇒ **在 COCO 检索上 both 更好**，与"text-only 优势"相反。
>
> ### 二、✅ checkpoint 与评测均已可复现（实测）
>
> `tools/_p782` 用新格式重评 7 个 run：**48/48（单塔）与 96/96（双塔）张量匹配**，
> 且 **`R@1 old = R@1 new` 逐一相等** ⇒ 训练状态完整保存、评测确定。
>
> ### 三、🔴 我自己的两次误判（必须记录）
>
> | # | 我的判断 | 实况 |
> |---|---|---|
> | 1 | "`evaluate()` 重复计数（i2t 报出 R@1 = 2.0317 > 1）" | ❌ **不是 bug**（当时确是别的写法问题，但下面的 0.9350 不是）|
> | 2 | "`top` 索引基准错误（分块 topk 未加偏移）" | ❌ **不是 bug** —— 最小复现（`tools/_p791`）在合成数据上证明**带/不带偏移都得正确答案** |
>
> **真相（`tools/_p792`，shape-only 依据）**：该图**最佳自有 caption 的排名分布**
> ```
> 25% → 1 ｜ 50% → 2 ｜ 75% → 7 ｜ 90% → 24 ｜ 95% → 46 ｜ 99% → 134 ｜ mean 9.8 ｜ median 2
> 排名 ≤ 1 的比例 = 0.4657    ← 恰等于 loop 的值
> 排名 ≤ 5 的比例 = 0.7237
> 排名 ≤10 的比例 = 0.8097
> ```
> **⇒ 两个数都对，测的是不同问题**：
> - `loop` **0.4657** = "该图**最佳** caption 排第 1"（单 caption 口径）
> - `evaluate` **0.9350** = "该图的**任意一条** caption 进 top-1"（多 caption 召回，**标准口径**）
>
> **⇒ 先前上报的 `i2t 0.9157 / 0.9293` 并未作废**（我一度宣布作废，那是错的）。
> 已清掉我加的 `+ s` 偏移与错误断言，并改写注释说明**两个口径都对、不必再怀疑**。
>
> ### 四、📋 受影响范围量化（`tools/_p793`）
>
> 判据：rank-8 适配器应为 196,608（单塔）/ 491,520（双塔）；记录值远超者 = 基座未冻结。
>
> | 归属 | run 数 | 位置 |
> |---|---|---|
> | **P3** | **16** | `route_c` 8、`route_d` 5、`route_e` 3（`n_trainable = 145,170,177`）|
> | **P3 + Paper A 共用** | **46** | `theory/v1_trajectory`（130–146M）|
> | **Paper A** | **69** | `flickr30k` 29、`theory` 21、`coco` 7、`blip2` 5、`siglip` 5、`vitl` 2 |
> | **合计** | **131** | |
>
> **两篇稿件都没有直接引用这些目录的路径**（`tools/_p788`）⇒ **暴露限于"方法命名"层面**，不是数字来源错配。
>
> ### 五、对两篇稿件的影响（**利好为主**）
>
> | 面 | 判断 |
> |---|---|
> | **"LoRA" 之名** | 🔴 **必须改**（现在名不副实）|
> | **"rank 消融测的是 rank"** | 🔴 **原结论失效**（当时 99.87% 可训练参数与 rank 无关）|
> | **"参数高效"** | ✅ **变强**：真 LoRA 只需 0.13% 参数即达同档性能（此前是 95.84%）|
> | **"COCO 上 text-only 优于 both"** | 🔴 **不成立**（实测 both 更高 +0.017）|
> | **"COCO R@1 < 0.001（near-random）"** | 🔴 **被推翻**（冻结即 0.5794）|
> | **审稿人 R1-W4 的怀疑** | ✅ **完全成立** |
>
> **⇒ 净判断：对"方法诚实性与参数效率"是利好；对"rank 消融"与"COCO 位置优势"两项结论是利空（须改写或撤回）。**
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
    if "重跑完成（真 LoRA + 正确 seed）" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("重跑完成（真 LoRA + 正确 seed）", "0.6068", "0.6235", "1/738", "131",
              "两次误判", "0.4657"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
