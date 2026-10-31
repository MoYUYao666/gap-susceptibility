# -*- coding: utf-8 -*-
r"""Record the Paper A claim ledger and its result.

    python tools/_p709_record_ledger.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📒 2026-10-14 20:30 —— Paper A **主张台账**已建立：**11 项可核、7 项无承载字段**
>
> ### 一、操作者要求
>
> > **"做"** —— 为 Paper A 补一份与 P3 同规格的 claim ledger（主张台账）。
>
> ### 二、为什么要做（**我先前的核验是弱方法**）
>
> 我上一轮说"Paper A 的 13 个招牌数字 13/13 都有来源"——**那是字面匹配**，
> 与项目**已否掉的假门禁**（`tools/_reproducibility_gate.py`：容差在 122,161 个数值里搜 ⇒ 145/145 "全过"）
> **属同一类方法**。
>
> **本次搜索立刻证实了它不可靠**：
> - `222` 命中的是 `recovered_cls_ids[222]` —— **数组下标**
> - `203` 命中 `folds[*].n_train`；`383` 命中 `p3_reproducibility :: difference` —— **全都无关**
>
> ### 三、✅ 台账结果（`tools/_claim_ledger_paperA.py`）
>
> **PASS 11 ｜ GAP 7**
>
> | 稿件数字 | 归档字段 | 结果 |
> |---|---|---|
> | ODE mean R² = **0.949** | `ode_ledger.json :: subsets.lora.mean` | ✅ |
> | R² 区间下限 **0.814** | `ode_ledger.json :: subsets.lora.min` | ✅ |
> | R² 区间上限 **0.977** | `ode_ledger.json :: subsets.lora.max` | ✅ |
> | 全量微调 pilot **0.922** | `ode_ledger.json :: subsets.full_ft.mean` | ✅ |
> | ODE 拟合数 **n = 96** | `ode_ledger.json :: n_runs_total` | ✅ |
> | 关联分析 run 数 **n = 204** | `dg_r1_reproducible.json :: primary.n` | ✅ |
> | **r = −0.71** | `pr_stats_hardened.json :: verdict.pooled_r`（−0.7142） | ✅ |
> | **斜率 −1.05** | `pr_stats_hardened.json :: ols_slope_all`（−1.0484） | ✅ |
> | **p = 0.016** | `pr_stats_hardened.json :: verdict.cr1_p_design_cell_t5`（0.01553） | ✅ |
> | LoRA 调参后 **60.69%** | `pr_peft_lr_sweep.json :: analysis.grid.lora_both@1e-05.zero_shot_top1_pct_mean` | ✅ |
> | 全量微调 **60.87%** | `pr_fullft_lr_sweep.json :: analysis.per_lr.1e-06.zero_shot_top1_pct_mean` | ✅ |
>
> ### 四、🔴 GAP 7 项（**稿件写了，归档找不到承载字段**）
>
> | 稿件数字 | 搜索到的只有无关命中 |
> |---|---|
> | OpenCLIP BitFit 平均 R² **0.943** | `strict_freeze_b32_r4/vision_only/seed456 :: final_task_metrics.R@5`（**检索指标，非 R²**） |
> | 斜率的 CR1 标准误 **0.29** | `a1_epoch_sweep.json :: checkpoints[*].displacement`（无关） |
> | 归档拟合数 **n = 222** | `recovered_cls_ids[222]`（下标） |
> | α < 0 的拟合数 **n = 203** | `recovered_cls_ids[203]`、`folds[*].n_train`（无关） |
> | 机制实验 **117** ／ 严格冻结对照 **95** | `recovered_cls_ids[117]`、`monitor_dg_check2 :: rules`（无关） |
> | 实验目录 run 数 **n = 221** | `recovered_cls_ids[221]`（下标） |
> | 验证部分实验数 **n = 383** | `recovered_cls_ids[382]`、`p3_reproducibility :: difference`（无关） |
>
> **⇒ GAP ≠ 数字错**。它意味着**按本项目自己的标准（每个数字须指名脚本与字段）目前无法验证**。
>
> ### 五、🔍 计数类 GAP 的补充调查（`tools/_p708`）
>
> 试着用"数目录"规则补出 222/203/117/95/221/383 —— **没有任何规则精确命中**：
>
> | 稿件 | 最接近的规则 | 差 |
> |---|---|---|
> | 383 | `per-run gap_history.json` = **385** | 2 |
> | 221 | `under strict_freeze*` = 232 | 11 |
> | 222 | 同上 = 232 | 10 |
> | 117 / 95 | `outputs/a1_class_aligned/` = 110 | 7 / 15 |
>
> **⇒ 说明稿件的**计数有自己的"一次实验"定义**（不是数文件），
> **该定义须由作者给出，否则这些数字无法复核。**
> （另：`ode_ledger.json :: runs` 里 α < 0 是 **92/96**，而稿件说 **203/222** —— **两者不是同一批拟合**，
> 更说明 222 那批的台账在哪需要作者指明。）
>
> ### 六、剩余（按优先级）
>
> | # | 事项 | 归属 |
> |---|---|---|
> | 1 | **GAP 7 项**：重新指向真正持有该数的字段，或从稿件删除 | **需作者**（我找不到产出它们的脚本） |
> | 2 | 计数定义（什么算"一次实验"）写进台账 | 需作者给出规则 |
> | 3 | Paper A 投稿包已就绪（`NC_submission/`），可上传 | 操作者 |
>
> **⚠️ 我不建议带 GAP 投稿**：Neurocomputing 与 PRL 同属 Elsevier，数据/可复现要求一致；
> 而且这 7 项里有 5 项是**计数**，一旦审稿人问"这 383 是怎么数的"会很难答。
> **但这是操作者的判断**，我按指令执行。
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
    if "Paper A **主张台账**已建立" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("Paper A **主张台账**已建立", "PASS 11", "GAP 7", "数组下标", "不建议带 GAP 投稿"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
