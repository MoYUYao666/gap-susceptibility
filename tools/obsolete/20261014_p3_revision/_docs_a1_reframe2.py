# -*- coding: utf-8 -*-
r"""写 A1 的**如实改写方案**（操作者选 ①②）（2026-10-12）。

## 背景

对抗性审查 + E-A 实验查明：A1 的**核心主张与自家数据冲突**。

| 论文主张 | 实况（全部来自论文归档） |
|---|---|
| "order preservation **governs** zero-shot accuracy" | 池化 τ=+0.85，但**组内** τ=−0.27（反向） |
| "τ 是监控器"（标题） | 论文自曝 *"change detector, not a health verdict"*、*"orders datasets, not individual runs"* |
| 摘要首句 "Only the second governs" | 与自家 Table 1 冲突（τ=0.615→78.6%） |
| r=1.000 "预测" | `tau_pred_exact` 与 `tau` **逐位相同** = 同义反复 |
| "gap predicts retrieval" | 自家 Spearman(CG,R@1)=−0.389 |

**新证据（`tools/_p216`）**：τ 的池化相关几乎全部由**数据集身份**承载
（Spearman(τ, 数据集均值)=+0.83；去掉数据集均值后 τ–top1 = **+0.039 ≈ 0**）。

    python tools\_docs_a1_reframe2.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "docs" / "A1_REFRAME_PLAN.md"

DOC = r"""# A1 如实改写方案（2026-10-12）

> 触发：操作者对 A1 做"审稿人视角"对抗性审查 → 3 份报告
> （`A1_ADVERSARIAL_SIGNIFICANCE.md` / `_METHOD.md` / `_POSITIONING.md`）
> → 方法学报告给出 2 条 FATAL → 操作者选 **C**（修 5 条硬伤 + 补两个实验）
> → E-A 实验结果**推翻了核心主张** → 操作者改选 **①②**（如实改写 + 补实验救 τ）

## 一、查明的事实（每条都有归档出处）

| # | 事实 | 出处 |
|---|---|---|
| 1 | τ 的池化相关 +0.85（n=9，top1_50k） | `outputs/a1_h_seed_summary.json:cross_checkpoint_correlations:seed42_plus_new_seeds_all` |
| 2 | 但**组内** τ = −0.50 / +1.00 / −0.50（coco / dtd / food101） | 同上 `:within_dataset_rank_check` |
| 3 | 论文所否定的 **CG 组内一致为正**（+1.00 / +0.50 / +0.50） | 同上 |
| 4 | 组内 Fisher 均值：τ = **−0.268**，CG = **+0.975** | `outputs/analysis/a1_expA_within.json`（`tools/_p209`） |
| 5 | τ 与**数据集身份**的 Spearman = **+0.830** | `outputs/analysis/a1_dataset_confound.json`（`tools/_p216`） |
| 6 | **去掉数据集均值后** τ–top1 = **+0.039 ≈ 0** | 同上 |
| 7 | `tau_pred_exact` 与 `tau` **逐位相同**（12/12 节点） | `outputs/a1_rr_e3_benchmarks.json`（`tools/_p204`） |
| 8 | `highlights.tex` 的 r=1.000 **未加限定** | `paper_a1/highlights.tex:14` |
| 9 | 论文自己写 *"τ orders datasets, not individual runs"* | `paper_a1/main.tex:574` |
| 10 | 论文自己写 *"a fixed τ level is a change detector, not a health verdict"* | `paper_a1/main.tex` §hardening |
| 11 | 论文自己写结论 *"not applied to rank individual runs within one dataset"* | `paper_a1/main.tex:579` |

**→ 第 9/10/11 条是对的，而它们与标题、摘要首句、以及"监控器"卖点冲突。**

## 二、改写原则

1. **标题不再承诺"监控器"**（那是论文自曝做不到的）。改为承诺**已证的东西**。
2. **摘要首句与 Table 1 一致**（"necessary, not sufficient"，不是 "only the second governs"）。
3. **把 Simpson 悖论本身写成一个发现**——这是有价值的负面结果，且数据全在手。
4. **r=1.000 在 highlights 里也降级**为"自洽检查"。
5. **"四位数"改三位**（实测最大残差 0.0019）。
6. **"gap predicts retrieval" 按自家数据修正**（Spearman(CG,R@1) = −0.389）。

## 三、待定：标题（等 `_p218` 结果）

**若组内 τ 在 n=30 上仍 ≤0** → τ 无排序力，标题只应承诺"边界刻画"：

> *The Modality Gap Is Not a Universal Health Metric: Task Dependence and Dataset Confounds
> in Cross-Modal Alignment Diagnostics*

**若组内 τ 在 n=30 上显著为正** → τ 在组内有救，标题可为：

> *Order Preservation as an Early-Warning Signal for Classification Fine-Tuning:
> Why the Modality Gap Is Not a Universal Health Metric*

**判据**：`outputs/a1_epoch_sweep.json`（`tools/_p218`，100 个检查点 + `tools/_p219` 分析）。

## 四、执行清单

| # | 动作 | 文件 | 状态 |
|---|---|---|---|
| 1 | 评测全部逐 epoch 检查点（100 个，无需训练） | `tools/_p218_eval_all_epochs.py` | 运行中 |
| 2 | 组内 n=30 重算 τ 排序力 | `tools/_p219_*` | 待做 |
| 3 | 按结果定标题 | `paper_a1/main.tex:21` | 待定 |
| 4 | 摘要首句改 "necessary, not sufficient" | `main.tex:33` | 待做 |
| 5 | "zero-overhead monitor" 改为 "signal for detecting erosion" | `main.tex:308` | 待做 |
| 6 | 写入 Simpson 悖论（数据集混杂） | 新小节 + `main.tex:579` | 待做 |
| 7 | highlights r=1.000 加限定 | `highlights.tex:14` | 待做 |
| 8 | "four decimals" → "three decimals"（0.0019） | `main.tex:33` | 待做 |
| 9 | 检索表述按自家数据修正 | `main.tex:33` | 待做 |
| 10 | 摘要/正文同步 + 重编译 + 门禁 | — | 待做 |

## 五、诚实标注

- **"①②"是操作者 2026-10-12 的选择**，不是我的推断。
- **若第 2 步结果不利，我会如实报告并建议只走 ①**（不硬撑 τ）。
- **本文件不修改任何稿件内容**，只记录方案；改动全部走 `tools/` 下的幂等脚本。
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    F.parent.mkdir(parents=True, exist_ok=True)
    io.open(F, "w", encoding="utf-8", newline="").write(DOC)
    t = io.open(F, encoding="utf-8").read()
    for k in ("Simpson", "0.268", "+0.975", "+0.830", "tau_pred_exact", "0.039"):
        assert k in t, f"断言失败：缺 {k}"
    print(f"  ✅ 已写 {F.relative_to(REPO)}（{len(t.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
