# -*- coding: utf-8 -*-
r"""落账：PR 统计加固完成（task-1）+ 更正 Lead 的引用错误（2026-10-12）。

## 同时记录一个"谁更正了谁"

Lead 最初引用的是 **M1**（β=−1.0112, ICC=0.8873），但任务书指定的是
**R@1 ~ DG + (1|dataset) + (1|model) + (1|config) = M4**。
统计面主动更正了 Lead。**这里如实记录该更正**（项目要求不粉饰）。

    python tools\_docs_pr_stats.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📊 2026-10-12 —— PR R1.2/R2.2/R3.2 统计加固完成（task-1）；统计面更正了 Lead 的一处引用错误**
>
> ### 交付件
>
> `docs/PR_STATS_FIX.md`（475 行）｜`tools/_p260_pr_stats_hardening.py`（分析，幂等）｜
> `tools/_p261_verify_pr_stats_report.py`（**验证门禁：253 条主张逐条指名 JSON 文件+字段**，
> 且要求数字出现在**其自身上下文附近**——**不是**全库模糊搜索，避免本项目曾出现的"假门禁"）
> ｜归档 `outputs/analysis/pr_stats_{hardened,within_group,mixed_effects,cluster_bootstrap,holdout}.json`
>
> ### 数据基础
>
> `outputs/analysis/dg_r1_reproducible.json :: rows[*]`（**n=204**，由 `tools/p1_dg_r1_recompute.py`
> 从 `outputs/**/results.json` 的 `final_gap.distribution_gap` 与 `final_task_metrics.R@1` 重算）。
> 统计面**重读了全部 204 个底层文件，逐位吻合（0 处不符）**。
>
> ### ⚠️ 更正：Lead 引错了模型（统计面主动指出）
>
> | 模型 | 随机截距 | β_DG | SE | z | ICC |
> |---|---|---|---|---|---|
> | **M4（任务指定）** | dataset+model+config | **−0.9526** | **0.0790** | −12.05 | **0.9449** |
> | M1（Lead 误引） | config | −1.0112 | 0.0774 | −13.07 | 0.8873 |
>
> M4 的 ICC 分层：dataset **0.6027** / model 0.0634 / config 0.2787 / 残差 0.0551。
> M5（再加 family）把 model 层压到 **0.0000** → 说明 **dataset 与 model 高度共线**。
>
> ### 核心结果
>
> | 量 | 值 | 字段 |
> |---|---|---|
> | 朴素池化 r（论文现值） | **−0.7142**（n=204，p=3.9e−33） | `verdict.pooled_r` |
> | **组内汇聚 r（族内 / 设计单元内）** | **−0.5506 / −0.7310** | `verdict.within_family_r` / `within_cell_r` |
> | 逐数据集 | flickr30k **−0.7809**(n=183) ｜ coco **−0.5984**(n=16) | `within_dataset` |
> | 逐模型 | CLIP **−0.7476**(n=192) ｜ BLIP **−0.9765**(n=5) ｜ **SigLIP +0.8083**(n=5) | `within_model` |
> | **Mundlak 组内 β** | **−1.0706**（p = **0.026**） | `mundlak_within_beta` |
> | **Mundlak 组间 β** | **−1.0093**（p = 0.035） | `mundlak_between_beta` |
> | 聚类 bootstrap（6 簇） | **[−0.848, −0.076]**，宽 = 朴素 **5.27×** | `clustered_ci_cell` |
> | 聚类 bootstrap（12 簇） | [−0.887, −0.615]，宽 = 1.85× | `clustered_ci_family` |
> | **CR1 稳健 SE（6 簇）** | 0.0723 → **0.2911（4.03×）**，p(t₅) = **0.0155** | `cluster_robust_OLS` |
> | 有效样本量（cell / family） | **8.88 / 34.14** | `effective_n_cell` / `effective_n_family` |
> | 留出 R²（cell / family） | **0.2363 / 0.4488**（样本内 0.5101） | `oos_r2_cell` / `oos_r2_family` |
>
> ### 三个对稿件**有利**的发现（须写进回复信）
>
> 1. **不是纯组间假象**：Mundlak 组内 β（−1.0706）≈ 组间 β（−1.0093）→ 关系在组内同样成立。
> 2. **经聚类后仍显著**：CR1 p = 0.0155；family 聚类 1 万次重抽 **0 次** r ≥ 0。
> 3. **`route_d` 不是驱动因素**：剔掉 `d1` 后 r = −0.7186；剔掉整个 Route C/D/E 后
>    r = **−0.7368（更强）**。→ **Lead 先前"`route_d` 污染了 −0.714"的猜测不成立。**
>
> ### 必须如实写进 limitation 的两件事
>
> - **204 行不是 204 个独立观测**：173 行（84.8%）落在单一 dataset×backbone 单元，
>   **192 行（94.1%）共享同一骨干**（CLIP ViT-B/32）→ **有效 n ≈ 9（量级）**。
> - **4 个子群符号翻转**：SigLIP **+0.8083**（n=5, p=0.098, CI 跨 0）、`coco` 族 +0.8510、
>   `route_d` +0.9793、`route_e` +0.9835。单看都不可推断，但**四个独立小样本一致反向**。
>
> ### 判决
>
> **association，不是 predictive。** 建议：① "predicts" → "is associated with" 且必给聚类区间；
> ② 删 "across 204 experiments"，改 "204 archived runs drawn from 6 dataset × backbone cells"；
> ③ `discussion.tex:18` 的 "strong negative correlation" 补限定（192/204 来自 CLIP B/32）。
>
> ### 两个坦白（统计面自己写的）
>
> 1. **`statsmodels` 未安装** → 自写交叉随机截距 REML，并用**已知真值的模拟**自检
>    （斜率复原 −1.193 vs 真值 −1.2；τ 比值 [0.43, 0.75, 0.91]）。**不是第三方实现互证。**
> 2. **层数少的方差成分被低估**（8 层那层只复原到 0.43×）→ **DE=23 / 有效 n≈9 只能当量级**，
>    主口径用 CR1 的 **4.03×** 与 CI 的 **5.27×**。
>
> ### 分组标签的来源（稿里会被问）
>
> `results.json` **只有 9–10 个键，没有 `dataset`/`model`/`config` 字段** → 标签全部**推导**，
> 分四档 `runner_literal` / `arg_default` / `doc_xref` / `disputed`，每族逐条给出脚本行号
> （如 `seed_experiments.py:44`、`coco_experiments.py:64`、`experiments.tex:187`）。
> **5 行无法归类**（`vitl` 2 行 UNDOCUMENTED、`imagenet_zs` 3 行 DISPUTED——
> 仓库自带 `clip_zs_check.py`/`clip_tinyimagenet_check.py` 说明当时未定论），
> **已排除出分组分析并如实报告，未硬塞**。
>
> **待 Lead 做**：`HANDOFF.md`、`文件地图.md` 的本阶段条目（统计面写入范围外）。
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "PR R1.2/R2.2/R3.2 统计加固完成" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("PR R1.2/R2.2/R3.2 统计加固完成", "−0.9526", "0.9449", "−1.0706",
              "0.2911", "8.88", "SigLIP +0.8083", "Lead 引错了模型",
              "route_d` 不是驱动因素"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
