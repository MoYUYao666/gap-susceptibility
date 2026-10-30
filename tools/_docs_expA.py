# -*- coding: utf-8 -*-
r"""落档：E-A 留出检验的结果与结论（2026-10-12）。

## 结果（全部出自论文自己的归档，逐条可复核）

| 检验 | τ | CG | 出处 |
|---|---|---|---|
| 池化（n=9，50k） | **+0.85** | −0.267 | `a1_h_seed_summary.json:cross_checkpoint_correlations` |
| 池化（n=3，50k） | **+1.00** | −0.50 | 同上（seed42_only） |
| 池化（n=6） | +0.886 / +0.829 | −0.371 / −0.314 | 同上 |
| **组内（coco）** | **−0.50** | **+1.00** | `within_dataset_rank_check` |
| **组内（dtd）** | **+1.00** | +0.50 | 同上 |
| **组内（food101）** | **−0.50** | +0.50 | 同上 |
| 组内 Fisher 均值（我算，τ） | **−0.268** | +0.975 | `outputs/analysis/a1_expA_within.json` |

**→ 池化与组内方向相反 = Simpson 悖论。**

    python tools\_docs_expA.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴🔴 2026-10-12 —— 对抗性审查后执行操作者选的 C：E-A 留出检验出结果（**推翻性**）**
>
> ### 背景
>
> 操作者要求对 A1 做"审稿人视角"对抗性审查。派了 3 个独立审稿人（significance / method /
> positioning），报告落在 `docs/A1_ADVERSARIAL_{SIGNIFICANCE,METHOD,POSITIONING}.md`。
> **method 那份给出 2 条 FATAL**，操作者选 **C**（修 5 条硬伤 + 补两个实验）。
>
> ### E-A：留出检查点检验 + rival baseline（`tools/_p208`、`_p209`、`_p210`、`_p211`）
>
> **数据**：`outputs/a1_h_offset.json:checkpoints`（13 个检查点）；
> **交叉验证**：`outputs/a1_h_seed_summary.json:within_dataset_rank_check`（论文自己的归档）
>
> **结果（池化 vs 组内）**：
>
> | 检验 | τ | CG | 出处 |
> |---|---|---|---|
> | 池化（n=9，top1_50k） | **+0.850** | **−0.267** | `cross_checkpoint_correlations:seed42_plus_new_seeds_all` |
> | 池化（n=3） | **+1.000** | −0.500 | `:seed42_only` |
> | 池化（n=6，seed42+43） | +0.886 | −0.371 | `:seed42_and_43` |
> | 池化（n=6，seed43+44） | +0.829 | −0.029 | `:seeds43_44_only` |
> | **组内 coco** | **−0.50** | **+1.00** | `within_dataset_rank_check:coco` |
> | **组内 dtd** | **+1.00** | +0.50 | `:dtd` |
> | **组内 food101** | **−0.50** | +0.50 | `:food101` |
> | 组内 Fisher 均值（独立重算） | **−0.268** | +0.975 | `outputs/analysis/a1_expA_within.json` |
>
> ### 判定
>
> **池化相关的方向与组内相反 → 典型 Simpson 悖论。**
> τ 的池化强相关（+0.85～+1.00）由**数据集间难度差异**产生，
> 它**不能排序同一数据集内的检查点**；而论文所否定的 **CG 组内一致为正（+0.5～+1.0）**。
>
> **留一数据集（LODO）留出 R²**（`tools/_p208`）：τ 平均 **−98.05**（常数基线 −9.36），
> **0/4 折优于常数**。*注*：该检验的测试折指标值落在训练值域之外（组内 τ 跨度仅 0.0005，
> 组间 0.2）→ 外推 R² 会爆炸；**故以"组内相关"为主判据，LODO 仅作辅证**。
>
> ### 影响
>
> **这直接冲击论文的核心主张**（"order preservation governs zero-shot accuracy"）。
> 论文 `main.tex:471` 附近已自曝"`tau` orders datasets, not individual runs"——
> **那句话是对的，而它推翻了标题与摘要的主张**。
>
> ### 状态
>
> - ✅ E-A 已跑完、已归档、已交叉验证（我的计算与论文归档逐位一致）
> - ⏳ E-B（监控决策闭环）待跑
> - ⏳ 5 条硬伤的写作修正待做
> - 🔴 **标题/摘要/主张需要根本性重新定位**（不再是"τ 是监控器"）
>
> **证据文件**：`outputs/analysis/a1_expA_full.json`、`a1_expA_within.json`、
> `a1_within_crosscheck.json`、`a1_expA_conclusion.json`
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "E-A 留出检验出结果" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("Simpson 悖论", "−0.268", "+0.850", "within_dataset_rank_check",
              "E-A 留出检验出结果"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
