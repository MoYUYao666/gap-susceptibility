# -*- coding: utf-8 -*-
r"""落账：`+0.079` 张冠李戴的完整证据链（PR R1.1/R3.1 的真错）（2026-10-12）。

## 证据链

| 环节 | 内容 |
|---|---|
| 论文原句 | *"Full fine-tuning increases CG by 24\% …, while text-only LoRA **limits** CG increase to **$+0.079$** and zero-shot degradation to 0.6 percentage points."* |
| `+0.079` 的归档出处 | `outputs/master_results.json` → 记录 `experiment = d1_alpha64_text_r8`，`path = route_d\\d1_alpha64_text_r8`，`cg_delta = 0.079171`，**`R1 = 0.389`** |
| 该配置是什么 | **Route D（α=64）**；`lora_rank=8`，`n_trainable_params=145170177` |
| 为何是错 | 这句话的主语是"**text-only LoRA 限制 CG 增长、零样本只掉 0.6 点**"——但 0.389 的 R@1 **恰是审稿人点名的差结果**；把它的 CG∆ 挂到"好结论"上 |
| 正确候选 | `tab:position` Flickr30k text-only = **−0.064**（R@1=0.627）；`strict_control_summary.json` 5-seed = **−0.0465 ± 0.0027** |
| `24%` 出处 | `outputs/imagenet_zs_rerun/full_ft_s123/centroid_gap.json`（`cg_delta=0.2609`）与 `full_ft_s999`（`0.2672`） |
| `0.6` pp 出处 | 冻结 ImageNet top-1 59.3 → text-only 58.66 = 0.64 pp |

**这正是 PR 三位审稿人共同指出的"numerical inconsistencies"的一个实例。**

    python tools\_docs_0p079_finding.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴 2026-10-12 —— 查明 `paper合` 里 `+0.079` 的**张冠李戴**（PR R1.1/R3.1 的真错，证据链完整）**
>
> ### 背景
>
> 操作者要求**把 PR 对 P1 的全部意见在 `paper合` 上逐条改到全做完**。
> 清点 20 条意见时，AE 的头号指控是 *severe numerical inconsistencies*；
> R1.1 给出具体例子（`+0.079` 符号翻转），R3.1 再提（摘要/结论 +0.079 vs 表格 −0.064）。
>
> ### 查证结果：**不是"符号翻转"，是"张冠李戴"**
>
> **论文原句**（`paper合/sections/empirical.tex`）：
> > *"Full fine-tuning increases CG by $24\\%$ and collapses zero-shot accuracy to near-chance
> > levels (mean $2.6\\%$ over 3 retrained seeds), while text-only LoRA **limits** CG increase
> > to $+0.079$ and zero-shot degradation to $0.6$ percentage points."*
>
> **`+0.079` 的唯一归档出处**（全库搜索后）：
> ```
> outputs/master_results.json
>   experiment          : d1_alpha64_text_r8
>   path                : route_d\\d1_alpha64_text_r8
>   lora_rank           : 8
>   n_trainable_params  : 145170177
>   cg_delta            : 0.079171      ← 就是它
>   R1                  : 0.389         ← 审稿人点名的差结果
> ```
>
> **为何是错**：这句话的主语是"**text-only LoRA 限制 CG 增长、零样本仅退化 0.6 点**"，
> 却取了 **Route D（α=64）那一行的 CG∆** —— 而那一行的 **R@1 只有 0.389**，
> 正是审稿人 R1.1 引用来说明"同样叫 text-only 却符号相反"的证据。
> **用一个差配置的有利数字去支撑一个关于好配置的结论。**
>
> ### 正确的替换候选（都有源）
>
> | 候选 | 值 | 出处 |
> |---|---|---|
> | PEFT 约定的 Flickr30k text-only | **−0.064**（R@1 = 0.627） | `paper合/sections/empirical.tex` 的 `tab:position`；行级对应 `outputs/analysis/dg_r1_reproducible.json:rows` 的 `flickr30k/rq2_text_only`（CG 0.8184→0.7548，Δ=−0.0635） |
> | 严格冻结 5-seed text-only | **−0.0465 ± 0.0027** | `outputs/analysis/strict_control_summary.json:configs.text_only.cg_delta_mean` |
>
> ### 同句另两个数字（已核，有源）
>
> | 数字 | 出处 |
> |---|---|
> | `24%`（full-FT 的 CG 增幅） | `outputs/imagenet_zs_rerun/full_ft_s123/centroid_gap.json`（`cg_delta=0.2609`）、`full_ft_s999`（`0.2672`） |
> | `0.6` pp（text-only 的零样本退化） | 冻结 59.3 → text-only 58.66（`paper_a1/main.tex` 同口径）＝ 0.64 pp |
>
> ### 工具
>
> `tools/_p252_r31_verdict.py`（判定 +0.079 vs −0.064）、`_p253_trace_0p079.py`（全库追踪）、
> `_p254_master_record.py`（定位 master_results 记录）、`_p255_sentence_numbers.py`（同句数字）。
>
> **状态**：证据已固化；**改稿由 Lead 在有其他工作面结果后统一合成**（避免与并行工作面冲突）。
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "张冠李戴" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("张冠李戴", "d1_alpha64_text_r8", "0.079171", "0.389", "−0.064", "−0.0465"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
