# A1 数字溯源与备战验证（备战项 1 + 3）

**对象**：`paper_a1/`（PRL / Pattern Recognition Letters, PRLETTERS-D-26-01941），状态 Decision in Process（2026-09-11）。
**目的**：把摘要/正文的关键数字逐一定位到归档 JSON；并把"τ 是否只是描述性/同义反复"这一最可能的审稿质疑用**独立复算**回答。
**新脚本**：`tools/clip_a1_tau_holdout.py` → `outputs/a1_tau_holdout.json`（可重复运行）。

## 1. 摘要关键数字逐条溯源（全部命中 ✓）

| 摘要表述 | 论文值 | 复算值 | 来源 |
|---|---|---|---|
| 手术使 CG 缩小而 top-1 崩塌 | CG 0.82 → 0.01；top-1 59.3% → 32.0% | 冻结基线 CG **0.8154**、top-1 **59.26%**；λ=+1 平移后 CG **0.0117**、top-1 **32.01%** | `a1_tau_trajectory.json`(frozen) + `a1_full_results.json`(clip/T, λ=1.0) |
| 真实微调可"增大鸿沟但不掉零样本" | CGΔ = +0.114，ImageNet 保持 59.7% | 初始质心距 **0.8188** → 末态 **0.9326**（**+0.1138**）；ImageNet-50k top-1（both_r8）**59.67%** | `outputs/imagenet_zs/both_r8/results.json`；`imagenet1k_zs_50k_plain.json::results_plain.both_r8` |
| 34 个扰动条件 | 34 | **26 + 8 = 34**（26：base 1 + 平移 T 7 + 正交 O 5 + 质心混合 C 3 + 噪声 G 4 + 子空间 L 4 + 自身类质心 P 2，见 `clip_a1_baseline_metrics.py` 逐行枚举；+8：openclip 4 + siglip 4） | `a1_baseline_metrics.json(n_conditions=26)`、`a1_crossmodel_results.json(8)` |
| 三个模型族 | 3 | clip / openclip / siglip | `a1_full_results.json`、`a1_crossmodel_results.json` |
| 五个真实检查点 | 5 | `a1_multiseed.json::n_seeds = 5`（每 seed 全 26 条件） | `a1_multiseed.json` |
| top-1 由 τ 支配、与 gap 量无关 | τ 强相关、CG 不相关 | 26 条件下 Spearman：**τ = 0.9262（p=1.2e-11）**、CG = −0.0821（p=0.69）、CKA 0.755、mean-cos 0.872；5 seed 汇总：**τ = 0.917 ± 0.006**、CG = −0.131 ± 0.028 | `a1_baseline_metrics.json::metric_correlations`、`a1_multiseed.json::aggregate` |

## 2. 独立复算：理论预测 τ（回应"theory is just a fit"）

`a1_margins.json` 的 `predicted_tau_exact` 由冻结模型的 margin/偏置统计（m, σ_m, σ_b）给出，**不使用实测 τ**；逐 λ 与实测对比（本次独立复算）：

| 对比 | n | Pearson r | 最大绝对误差 | 是否同一数组 |
|---|---|---|---|---|
| predicted_tau_exact vs measured_tau_5k | 9 | **1.0000** | **0.0019** | 否（非自我复制） |
| predicted_tau_exact vs measured_tau_50k | 3 | 1.0000 | 0.0011 | 否 |
| predicted_tau_gauss vs measured_tau_5k | 9 | 0.9865 | 0.1695 | 否 |

→ 与 `revision_additions.tex` 已有的 Q3 答复（"逐点误差 < 0.002"）**一致且经独立复算确认**；同时说明高斯近似版误差大一个量级（回复信里应明确用的是 exact 版）。

## 3. 新增证据：跨模型族泛化（留一模型，本次新算）

把 28 个带 (CG, τ, top1) 的条件（clip 20 + openclip 4 + siglip 4）放在一起，用**留一模型**评估两种预测子（在其余模型上拟合线性 top1 ~ x，预测留出模型）：

| 留出模型 | τ 预测子 R² / MAE | CG 预测子 R² / MAE |
|---|---|---|
| clip | **0.371** / 12.63 | −1.520 / 24.35 |
| openclip | −0.273 / 12.15 | −1.125 / 13.66 |
| siglip | **0.378** / 10.91 | −1.452 / 25.50 |
| 汇总（Spearman） | **τ = 0.927（p=1.4e-12）** | CG = −0.251（p=0.20，n.s.） |

**结论**：跨出训练族时，τ 是唯一还能保持预测力的量（R²>0 的两个族、整体秩相关 0.93），而 CG 一律比"取均值"更差（R²<0）。这条正是回应"τ 只是描述性/同义反复"的最直接反证——**若 τ 是 top-1 的另一种写法，它不可能在没见过的模型族上还给出正 R² 而 CG 崩塌**。
**诚实边界**：R² 仅 ~0.37 说明**族间截距/斜率不同**（校准差异），因此正文/回复信不宜把 τ 说成"跨族可直接换算 top-1"，而应强调**单调性与排序**（Spearman）而非绝对数值映射。

## 4. 仍需在返修时注意的两点

1. **59.7% 的口径**：`both_r8` 的 ImageNet-50k top-1 在 plain 模板下为 **59.67%**，synset 模板下为 60.18%——回复信中固定写 plain 模板口径，避免审稿人复算时对不上。
2. **条件计数口径**：如果审稿人问"34 个条件"如何构成，按 §1 的 26+8 说明（26 的构成已在代码里逐行枚举），不要只说"34"。
