# PR 统计加固报告 — DG–R@1 关系的伪重复与组间混杂

**任务**：`task-1`（PR R1.2 / R2.2 / R3.2）
**执行者**：teammate `stats-hardener`
**日期**：2026-10-12
**脚本**：`tools/_p260_pr_stats_hardening.py`（幂等，两次连跑输出 SHA256 一致）
**命令**：`python tools\_p260_pr_stats_hardening.py`
**环境**：`D:\Anaconda\envs\pytorch\python.exe`（Python 3.12.14 / numpy 2.5.2 / scipy 1.18.1）
**产物**：
`outputs/analysis/pr_stats_hardened.json`（汇总）、
`pr_stats_within_group.json`、`pr_stats_mixed_effects.json`、
`pr_stats_cluster_bootstrap.json`、`pr_stats_holdout.json`

**未改动**：任何 `paper合/*.tex`（Lead 负责合成）；未改动 `outputs/` 下任何实验归档。

---

## 0. 结论（TL;DR）

三位审稿人的批评**部分成立、且可量化**，但**不是全部成立**——需要分开说：

| 审稿人指控 | 实测判定 |
|---|---|
| 把非独立实验当独立观测（伪重复） | ✅ **成立且严重**。按 dataset×backbone 聚类，bootstrap CI 宽度是朴素的 **5.27 倍**（上界从 −0.640 抬到 **−0.076**）；CR1 标准误是 OLS 的 **4.03 倍**；估计设计效应 ≈23 → **有效样本量 ≈ 9**，而非 204 |
| 组间混杂（between-group confounding） | ⚠️ **存在，但不是唯一来源**。Mundlak 分解：组内斜率 **−1.0706（p=0.026）** ≈ 组间斜率 **−1.0093（p=0.0349）** → 汇合相关**不是**纯组间假象 |
| 偏相关控制 CG 不足 | ✅ 成立。控制 CG 只处理**指标共线**，完全不处理**行间非独立性**（本报告处理的是后者） |
| r=−0.714 是"跨模型族稳定"的量 | ❌ **不成立**。204 行中 **192 行（94.1%）是 CLIP ViT-B/32**；SigLIP 单独看**符号相反**（r=+0.8083, n=5） |
| DG→R@1 是"预测"关系 | ❌ **不成立**。留出整个 dataset×backbone 单元后样本外 R² **0.2363**（对 6 折中位数 0.2266），而样本内 R² 是 0.5101 |

**判决：应写 association（关联），不得写 predictive（预测）。**

---

## 1. 数据与溯源

### 1.1 数据来源链（逐行可复核）

```
outputs/**/results.json
  :: final_gap.distribution_gap      → DG
  :: final_gap.centroid_gap          → CG
  :: final_task_metrics.R@1          → R@1
        ↓  tools/p1_dg_r1_recompute.py（规则：每条含上述三个有限值的实验目录一行；
           路径含 figures/comparison/strict_freeze/smoke/_void/old/backup 者排除）
outputs/analysis/dg_r1_reproducible.json :: rows[*]  {path, dg_final, cg_final, r1, dg_init, cg_init}
        ↓  tools/_p260_pr_stats_hardening.py（本报告）
outputs/analysis/pr_stats_{hardened,within_group,mixed_effects,cluster_bootstrap,holdout}.json
```

**独立重推校验（脚本内断言）**：204 行**逐行**重读其 `results.json`，比对
`(distribution_gap, centroid_gap, R@1)` 三元组，**逐位精确相等（0 处不符）**。
→ 字段：`pr_stats_hardened.json :: provenance.recheck`。

**复现值**：`pr_stats_hardened.json :: within_group` 与脚本断言确认
**r = −0.7142, n = 204**，与稿件现值一致（脚本中断言 `|r+0.7142| < 5e-4`）。
→ 字段：`pr_stats_hardened.json :: verdict.pooled_r`。

### 1.2 分组标签从哪来 —— **归档里没有这些字段**（审稿人必问）

**`results.json` 只有 9–10 个键**，实测枚举：`experiment`、`lora_rank`、
`final_train_loss`、`final_val_loss`、`best_val_loss`、`final_gap`、`initial_gap`、
`final_task_metrics`、`n_trainable_params`（+ 少数 17 个文件多一个 `test_metrics`）。
**没有 `dataset`、没有 `model`、没有 `config`。**

因此 dataset / model 标签是**推导**的，每条推导的出处写入
`pr_stats_hardened.json :: label_evidence`，规则分四档：

| 档位 | 含义 |
|---|---|
| `runner_literal` | 某个 runner 脚本**字面声明** `dataset=...`，且其输出目录**正是**该目录 |
| `arg_default` | runner 取 `--dataset` 参数，用其 **argparse 默认值** |
| `doc_xref` | 归档稿件/文档把该目录与某数据集**并列** |
| `disputed` | 仓库自带脚本专门去查该目录的数据集身份，**未定论** |

**推导表**（`label_evidence` 的展开；`family` = `path` 第一段）:

| family | n | dataset | model | 档位 | 出处 |
|---|---|---|---|---|---|
| `flickr30k` | 29 | flickr30k | CLIP ViT-B/32 | arg_default | `experiments/main.py:436`；`src/config.py:120` |
| `flickr30k_seeds` | 20 | flickr30k | CLIP ViT-B/32 | runner_literal | `experiments/seed_experiments.py:44`（`dataset="flickr30k"`）、`:36`（`OUTPUT_DIR="./outputs/flickr30k_seeds"`） |
| `coco` | 7 | coco | CLIP ViT-B/32 | runner_literal | `experiments/coco_experiments.py:64`（`dataset_name="coco"`）；`:32-39` 的 7 个配置名与归档 7 个目录**逐一对应** |
| `phase1` | 7 | flickr30k | CLIP ViT-B/32 | runner_literal | `experiments/phase1_experiments.py:13`（`DATA="flickr30k"`）、`:11`（`OUTPUT_DIR=outputs/phase1`） |
| `blip2` | 5 | flickr30k | BLIP | arg_default | `experiments/blip2_experiments.py:415`（`--dataset` 默认 `flickr30k`）、`:414`（`--outputs_dir` 默认 `./outputs/blip2`） |
| `siglip` | 5 | flickr30k | SigLIP | arg_default | `experiments/siglip_experiments.py:382`（默认 `flickr30k`）、`:238`（`clip_model=SIGLIP_MODEL`）、`:381` |
| `route_c` | 8 | flickr30k | CLIP ViT-B/32 | doc_xref | `paper/sections/supplementary.tex:96`「Route C/D/E …… 16 experiments」（8+5+3 与归档计数一致） |
| `route_d` | 5 | flickr30k | CLIP ViT-B/32 | doc_xref | 同上；`paper/sections/discussion.tex:18` 把 Route D 与「rank-8 on Flickr30k」并列 |
| `route_e` | 3 | flickr30k | CLIP ViT-B/32 | doc_xref | `paper/sections/experiments.tex:187`「Route E DG-ES proof-of-concept (**Flickr30k**)」 |
| `theory/v1_trajectory` | 46 | flickr30k | CLIP ViT-B/32 | runner_literal | `experiments/theory/v1_rank_sweep.py:121`；docstring `Output: outputs/theory/v1_trajectory/` |
| `theory/adapter` | 30 | flickr30k | CLIP ViT-B/32 | runner_literal | `experiments/theory/adapter_sweep.py:79`；docstring |
| `theory/beta_pilot` | 9 | flickr30k | CLIP ViT-B/32 | runner_literal | `experiments/theory/beta_pilot.py:178`；docstring |
| `theory/epoch1` | 14 | flickr30k | CLIP ViT-B/32 | runner_literal | `experiments/theory/epoch1_gamma.py:71`、`OUTPUT_DIR` |
| `theory/verify_accum` | 2 | flickr30k | CLIP ViT-B/32 | runner_literal | `experiments/theory/verify_accum.py:64`、`OUTPUT_DIR` |
| `theory/coco` | 9 | coco | CLIP ViT-B/32 | runner_literal | `experiments/theory/coco_validation.py:54`（`dataset="coco"`）；docstring「3 configs × 3 seeds = 9 runs」与归档 9 行一致 |
| `vitl` | 2 | **UNDOCUMENTED** | ViT-L | doc_xref | `experiments/` 下**找不到**写 `outputs/vitl` 的 runner；归档只在稿件里出现「ViT-L」行 |
| `imagenet_zs` | 3 | **DISPUTED** | CLIP ViT-B/32 | disputed | `tools/clip_zs_check.py`、`tools/clip_tinyimagenet_check.py` 专门用于查该目录是 ImageNet / TinyImageNet / CIFAR-100；`HANDOFF.md` 记「CIFAR Top-1 硬编码且数据夹名 imagenet_zs（身份存疑）」 |

**未归类行数（如实报告，不硬塞）：5 行** = `UNDOCUMENTED`（vitl, 2 行）+ `DISPUTED`（imagenet_zs, 3 行）。
这 5 行**排除**在 within-dataset / within-model / 设计单元分析之外，但仍参与汇合与 `family` 分析。
→ 字段：`pr_stats_hardened.json :: label_evidence`、`pr_stats_within_group.json :: by_dataset`。

**`family`（第一段路径名）是唯一**完全按归档字面**的分组**，故作为主分组。
`config` = 路径去掉尾部 `/seed<N>`（即"设计单元"），如
`theory/v1_trajectory/v1_both_r8/seed42` → `theory/v1_trajectory/v1_both_r8`。**此定义纯字符串操作，无需推断**。

### 1.3 设计单元（dataset | model）实际分布 —— 混杂的直接证据

| 单元 | n | 占比 | 档位 |
|---|---|---|---|
| flickr30k \| CLIP ViT-B/32 | **173** | **84.8 %** | arg_default |
| coco \| CLIP ViT-B/32 | 16 | 7.8 % | runner_literal |
| flickr30k \| BLIP | 5 | 2.5 % | arg_default |
| flickr30k \| SigLIP | 5 | 2.5 % | arg_default |
| DISPUTED \| CLIP ViT-B/32 | 3 | 1.5 % | disputed |
| UNDOCUMENTED \| ViT-L | 2 | 1.0 % | doc_xref |

→ 字段：`pr_stats_hardened.json :: label_evidence`、`verdict.largest_cell_share = 0.848`。

---

## 2. 结果

> 以下每个数字都可从 `outputs/analysis/pr_stats_*.json` 的**指名字段**读出；
> 全部由 `tools/_p260_pr_stats_hardening.py` 单次运行产出（幂等，两次连跑 SHA256 一致）。

### 2.1 汇合 vs 组内相关（三位审稿人点名要求）

| 量 | n | r | p | 95% CI（Fisher，**按独立观测算，仅供对照**） |
|---|---|---|---|---|
| **汇合（稿件现值）** | 204 | **−0.7142** | 3.93e−33 | [−0.7755, −0.6396] |
| 组内汇聚（族内，11 组） | — | **−0.5506** | <1e−16 | — |
| 组内汇聚（设计单元内，5 单元） | — | −0.7310 | <1e−16 | — |
| 组内汇聚（数据集内，3 组） | — | −0.7512 | <1e−16 | — |
| 组内汇聚（模型内，3 组） | — | −0.7073 | <1e−16 | — |

→ 字段：`pr_stats_hardened.json :: verdict.pooled_r`；
`pr_stats_within_group.json :: pooled_within_family / pooled_within_design_cell / pooled_within_dataset / pooled_within_model`。

**逐数据集 / 逐模型**（审稿人明确要求）：

| 分组 | n | r | p | 95% CI |
|---|---|---|---|---|
| dataset = flickr30k | 183 | **−0.7809** | <1e−39 | [−0.8317, −0.7170] |
| dataset = coco | 16 | **−0.5984** | 0.01434 | [−0.8438, −0.1459] |
| dataset = DISPUTED | 3 | −0.2523 | 0.8376 | *n<4，不作推断* |
| dataset = UNDOCUMENTED | 2 | — | — | *n=2，不可算* |
| model = **CLIP ViT-B/32** | **192** | **−0.7476** | <1e−34 | [−0.8040, −0.6777] |
| model = BLIP | 5 | −0.9765 | 0.0043 | [−0.9985, −0.6809] |
| model = **SigLIP** | 5 | **+0.8083** | 0.0978 | [−0.2578, 0.9868] |
| model = ViT-L | 2 | — | — | *n=2，不可算* |

→ 字段：`pr_stats_within_group.json :: by_dataset / by_model`。

**逐实验族**（12 组，归档字面分组）——**出现符号反转**：

| family | n | r | | family | n | r |
|---|---|---|---|---|---|---|
| `route_c` | 8 | **−0.9861** | | `coco` | 7 | **+0.8510** |
| `blip2` | 5 | **−0.9765** | | `route_d` | 5 | **+0.9793** |
| `phase1` | 7 | **−0.9218** | | `route_e` | 3 | **+0.9835** |
| `theory` | 110 | −0.6339 | | `siglip` | 5 | **+0.8083** |
| `flickr30k_seeds` | 20 | −0.6305 | | `imagenet_zs` | 3 | −0.2523 |
| `flickr30k` | 29 | −0.4641 | | `vitl` | 2 | — |

→ 字段：`pr_stats_within_group.json :: by_family`。

**同一数据集内的聚合效应**（coco 是最干净的例证）：
dataset = coco **整体 r = −0.5984**，但其内部 `coco` 族 **r = +0.8510（n=7）**、
`theory/coco` 族 **r = −0.3589（n=9）**。
即：把两个符号相反的子族池化后，得到的 −0.5984 **既不描述任何一个子族**。
→ 字段：`pr_stats_within_group.json :: by_family_within_dataset.coco`。

### 2.2 混合效应模型

**`statsmodels` 在本环境不可用** —— 实测：
`import statsmodels` → `ModuleNotFoundError: No module named 'statsmodels'`
（`sklearn` 同样缺失；`numpy`/`scipy`/`pandas` 可用）。
→ 字段：`pr_stats_mixed_effects.json :: statsmodels_available = false`、`note_statsmodels`。

因此本脚本**自带交叉随机截距 REML 估计器**（`reml_crossed`），并对**已知方差成分的模拟数据**做了自检：

- 自检设定：n=400，三层交叉随机截距（levels = 8 / 5 / 40），真值 τ = [0.50, 0.40, 0.30]，σ=1
- 斜率复原 **−1.193**（真值 −1.2）✅
- τ 复原 **[0.213, 0.300, 0.274]**，比值 **[0.426, 0.751, 0.912]**，总和比 **0.656**
- ⚠️ **层数少的因子成分被明显低估**（8 层那一层只复原到 0.43×）→ **单个方差成分只能当量级看**
→ 字段：`pr_stats_mixed_effects.json :: self_test_reml`。

**模型族**（全部为 `R@1 ~ DG + 随机截距`，REML）：

| 模型 | 随机截距 | β_DG | SE | z | p (Wald) | ICC（各层） | ICC 合计 |
|---|---|---|---|---|---|---|---|
| M1 | (1\|config) | −1.0112 | 0.0774 | −13.065 | 5.2e−39 | [0.8873] | 0.8873 |
| M2 | (1\|family)+(1\|config) | −0.9429 | 0.1017 | −9.268 | 1.9e−20 | [0.3110, 0.5938] | 0.9048 |
| M3 | (1\|dataset)+(1\|model) | −1.0475 | 0.0679 | −15.422 | 1.2e−53 | [0.6419, 0.1044] | 0.7463 |
| **M4（任务指定）** | **(1\|dataset)+(1\|model)+(1\|config)** | **−0.9526** | **0.0790** | **−12.053** | **1.88e−33** | **[dataset 0.6027, model 0.0634, config 0.2787]** | **0.9449** |
| M5 | + (1\|family) | −0.9057 | 0.0878 | −10.318 | 5.8e−25 | [0.6598, 0.0000, 0.1032, 0.1902] | 0.9532 |

> **⚠️ 引用注意（给 Lead）**：任务书指定的模型是 **M4**（dataset + model + config）：
> **β_DG = −0.9526 ± 0.0790，z = −12.05，p = 1.88e−33，ICC_随机 = 0.9449**
> （分层 ICC：dataset 0.6027 / model 0.0634 / config 0.2787 / 残差 0.0551）。
> 先前 Lead 引用的 **−1.0112 ± 0.0774（z=−13.07）、ICC=0.8873 是 M1**（只含 config），不是任务指定的模型。两者都列在此表中，请按 M4 引用。

→ 字段：`pr_stats_mixed_effects.json :: M1_… / M4_random_intercepts_dataset_model_config`。
M4 方差成分：τ = [0.0404, 0.0043, 0.0187]，σ²_残差 = 0.0037；截距 1.3947。

**注意 M5 中 model 的 ICC 被压到 0.0000** —— dataset 与 model 高度共线
（每个 dataset 几乎只配一个 backbone），两层无法分别识别。这也是**混杂的又一证据**。

**聚类稳健标准误（不依赖任何分布假设的兜底口径）**，OLS 斜率均为 −1.0484：

| 聚类单元 | 簇数 | SE_OLS | **SE_CR1** | 膨胀倍数 | p（t，df=G−1） |
|---|---|---|---|---|---|
| **dataset × model** | **6** | 0.0723 | **0.2911** | **4.03×** | **0.01553** |
| family | 12 | 0.0723 | 0.2175 | 3.01× | 0.000536 |
| config | 125 | 0.0723 | 0.1149 | 1.59× | 1.6e−15 |

→ 字段：`pr_stats_mixed_effects.json :: cluster_robust_OLS`。
（CR1 修正 = `G/(G−1)·(n−1)/(n−k)`。）

**混合模型对子集的稳健性**（M4 形式重拟合）：

| 子集 | n | β_DG | SE | ICC_随机 |
|---|---|---|---|---|
| 去掉未定论标签的 5 行 | 199 | −0.9568 | 0.0807 | 0.9542 |
| 去掉 Route C/D/E 16 行 | 188 | −0.9812 | 0.0759 | 0.9444 |
| 只留 n≥10 的设计单元 | 189 | −1.2181 | 0.0952 | 1.0000 |

→ 字段：`pr_stats_mixed_effects.json :: sensitivity_subsets`。
**β 的符号与量级在所有子集下不变** —— 混合效应对标签选择不敏感。

### 2.3 聚类 bootstrap vs 朴素 bootstrap（10000 次重抽，seed = 20261012）

| 重抽方案 | 簇数 | r 均值 | 95% CI | CI 宽度 | 相对朴素 | frac(r ≥ 0) |
|---|---|---|---|---|---|---|
| **朴素（按行重抽）** | 204 | −0.7161 | [−0.7870, −0.6404] | 0.1466 | 1.00× | 0.00000 |
| 聚类（family） | 12 | −0.7385 | [−0.8871, −0.6152] | 0.2719 | **1.85×** | 0.00000 |
| **聚类（dataset × model）** | **6** | −0.6378 | **[−0.8484, −0.0760]** | **0.7724** | **5.27×** | **0.01240** |
| 聚类（config） | 125 | −0.7160 | [−0.8195, −0.5989] | 0.2206 | 1.50× | 0.00000 |

→ 字段：`pr_stats_cluster_bootstrap.json`（`naive_row_bootstrap` / `clustered_by_family` /
`clustered_by_design_cell` / `clustered_by_config` / `widening_*`）。

**关键读法**：
- 朴素 CI 与稿件引用的 Fisher CI [−0.776, −0.640] 几乎一致 → 稿件那张 CI 是**按 204 个独立观测**算的。
- 按 dataset×model 聚类后，**上界从 −0.640 抬到 −0.076**，1.24 % 的重抽样本给出 r ≥ 0 —— 即**勉强**不跨 0。
- 簇数只有 **6** 个，bootstrap 本身在这么少的簇下也不稳，故**以 CR1 标准误（p=0.0155）作为主口径**，bootstrap 作为佐证。

### 2.4 留出验证（样本外 R²）

做法：留出一整组（family 或设计单元），**只用训练折**拟合 `R@1 ~ DG` 的 OLS 斜率，
在留出折上预测，基准 = **训练折 R@1 均值**（常数基线）；SSE 跨折汇总。

| 方案 | 折数 | **汇总样本外 R²** | 折中位 R² | 优于常数基线的折占比 |
|---|---|---|---|---|
| 样本内（对照） | — | **0.5101** | — | — |
| 留一 family | 12 | +0.4488 | +0.3961 | 67% |
| **留一设计单元（dataset × model）** | **6** | **+0.2363** | **+0.2266** | **67%** |
| 留一 config | 125 | +0.4961 | +0.5251 | 69% |

→ 字段：`pr_stats_holdout.json :: in_sample / leave_one_family_out / leave_one_design_cell_out / leave_one_config_out`。

**逐折明细（留一设计单元）**：

| 留出单元 | n_test | 训练斜率 | 样本外 R² |
|---|---|---|---|
| flickr30k \| CLIP ViT-B/32 | 173 | −0.2703 | +0.2671 |
| coco \| CLIP ViT-B/32 | 16 | −1.0503 | +0.1861 |
| flickr30k \| BLIP | 5 | −1.3480 | **−0.7683** |
| flickr30k \| SigLIP | 5 | −1.0649 | **−94.826** |
| DISPUTED \| CLIP ViT-B/32 | 3 | −1.0467 | +0.4319 |
| UNDOCUMENTED \| ViT-L | 2 | −1.0353 | +0.9011 |

→ 字段：`pr_stats_holdout.json :: leave_one_design_cell_out.folds`。

**必须诚实说明的两点**：
1. **汇总样本外 R² 被单折主导**：留出 SigLIP 单元时，常数基线本身已拟合得极好
   （分母 SS 极小），而斜率预测错向，R² 被打到 −94.8。因此**必须并读折中位（0.2266）与"优于基线的折占比（4/6）"**。
2. **留出主导单元（flickr30k|CLIP, 173 行）时，训练集只剩 31 行**，学到的斜率是 −0.2703，
   与全样本的 −1.0484 相差近 4 倍 → **在只有 6 个单元的总体里，"留一"近乎"换一个总体"**。

### 2.5 Mundlak 组内/组间分解（混杂的判定性检验）

把 `DG` 拆成「组内离差」+「组均值」，同时入回归，聚类稳健标准误按同一分组：

| 分组 | 簇数 | **组内 β** | p（t, G−1） | **组间 β** | p |
|---|---|---|---|---|---|
| **dataset × model** | 6 | **−1.0706** | **0.0260** | **−1.0093** | 0.0349 |
| family | 12 | −0.9781 | 0.00943 | −1.0937 | 0.000485 |
| config | 125 | −1.5306 | 0.151 | −1.0459 | 1.97e−15 |
| config（仅 n≥2 的 35 组 / 114 行） | 35 | −1.5306 | 0.164 | −1.3694 | 6.06e−13 |

→ 字段：`pr_stats_hardened.json :: mundlak_within_between`。

**读法**：若关系纯属组间假象，组内斜率应 ≈ 0。实测**组内斜率 −1.0706 与组间斜率 −1.0093 几乎相等**
→ **DG–R@1 关系在组内同样成立，不是纯组间假象**。这一条**为稿件辩护**，应如实写进回复信。
（config 层因为 125 个组里多为单行、组内离差为 0，该层信息量低，p=0.151 不作结论。）

### 2.6 设计效应与有效样本量

`DE = 1 + (平均簇大小 − 1) × ICC`（ICC 取自 M4/M2 的方差成分）：

| 聚类单元 | 簇数 | 平均簇大小 | ICC | **设计效应 DE** | **有效样本量** |
|---|---|---|---|---|---|
| **dataset × model** | **6** | 34.0 | 0.6661 | **22.98** | **8.88**（≈9） |
| family | 12 | 17.0 | 0.3110 | 5.98 | **34.14**（≈34） |

→ 字段：`pr_stats_hardened.json :: design_effect`。

> ⚠️ **此表的 ICC 由只有 4 层的因子估出**（dataset 4 层、model 4 层），
> 而 2.2 节的自检显示层数少时方差成分可低估到 0.43×
> → **DE=23 / 有效 n≈9 应作为"量级"陈述，不宜当成精确值**。
> 更稳的模型无关口径是 2.2 的 CR1 膨胀（**4.03×**）与 2.3 的 CI 膨胀（**5.27×**）。

### 2.7 敏感性：剔除异质配置后关系反而更强

| 子集 | n | r | 95% CI | R² |
|---|---|---|---|---|
| S1 全部 204 行（稿件现值） | 204 | −0.7142 | [−0.7755, −0.6396] | 0.5101 |
| S2 剔除 Route D（5 行） | 199 | −0.7186 | [−0.7797, −0.6439] | 0.5164 |
| S3 剔除 Route C/D/E（16 行） | 188 | **−0.7368** | [−0.7959, −0.6636] | 0.5428 |
| S4 只留 n≥10 的设计单元 | 189 | **−0.7497** | [−0.8062, −0.6797] | 0.5620 |
| S5 剔除未定论标签的 5 行 | 199 | −0.7066 | [−0.7700, −0.6293] | 0.4992 |

→ 字段：`pr_stats_hardened.json :: sensitivity`。

**结论**：Lead 点名的 `route_d/d1_alpha64_text_r8`（CGΔ=+0.0792, R@1=0.389, n_trainable 与标准配置不同）
**并不驱动** −0.7142 —— 剔掉它 r 从 −0.7142 变 −0.7186；剔掉整个 Route C/D/E 反而到 −0.7368。
所以「−0.714 是 Route D 拉出来的」这一猜测**不成立**；
但 route_d 的**组内符号反转（+0.9793）**仍然说明池化掩盖了真实的组间异质性。

---

## 3. SigLIP 方向反转的诚实标注（Lead 点名）

- **数字**：model = SigLIP，**r = +0.8083，n = 5，p = 0.0978，95% CI [−0.2578, 0.9868]**。
- **对照**：同一批数据里 CLIP ViT-B/32 是 **−0.7476（n=192）**，BLIP 是 **−0.9765（n=5）**。
- **这说明了什么**：这是**方向反转**。
- **这不能说明什么**：n=5、**CI 跨 0**（p=0.098），**不足以断言 SigLIP 上 DG 与 R@1 正相关**。
  任何"在 SigLIP 上间隙越大检索越好"的写法都是**过度解读**。
- **但它足以推翻一件事**：汇合值 **r = −0.7142 不是"跨模型族稳定"的量**。
  再加上 **204 行里 192 行（94.1%）是 CLIP ViT-B/32** ——
  **汇合相关基本由单一模型族决定**，把它写成"跨骨干成立"没有依据。
- 同类反转还有：`coco` 族 +0.8510、`route_d` +0.9793、`route_e` +0.9835。
  这四者的 n 都在 3–8 之间，**单看都不可推断**，但**四个独立小样本一致地朝相反方向**，
  共同支持"池化掩盖组间异质性"这一结论。

→ 字段：`pr_stats_within_group.json :: by_model`、`by_family`。

---

## 4. 判决：association 还是 predictive

**结论：应写 association（关联），不得写 predictive（预测）。**

**支持"关联仍成立"的证据（3 条）**：
1. 聚类稳健斜率 −1.0484，CR1 标准误 0.2911（6 簇），**p = 0.0155** —— 仍显著；
2. family 聚类 bootstrap 95% CI **[−0.887, −0.615]** 不跨 0，1 万次重抽 0 次 ≥ 0；
3. **Mundlak 组内斜率 −1.0706（p=0.026）≈ 组间斜率 −1.0093（p=0.035）** → 不是纯组间假象。

**支持"不得写 predictive"的证据（4 条）**：
1. **样本外 R² 腰斩**：留出整个 dataset×backbone 单元后 **0.2363**（折中位 0.2266），
   而样本内 R² 是 **0.5101** —— 一半的解释力来自"认出这是哪个单元"；
2. **2/6 单元比常数基线更差**（BLIP −0.7683、SigLIP −94.826）；
3. **符号不稳定**：SigLIP、`coco`、`route_d`、`route_e` 四个子群 r 为正；
4. **"n=204"是虚的**：CR1 把 SE 抬 4.03 倍，聚类 bootstrap 把 CI 抬 5.27 倍，
   设计效应估计 ≈23 → 有效样本量 ≈9。

**具体给稿件的三条建议**：
1. 把 `r = −0.714` 的语境从 **"predicts"** 改为 **"is associated with"**，
   并且**必须同时给出聚类后的区间**（[−0.848, −0.076] 或 CR1 的 p=0.0155），不得只给 n=204 的 Fisher CI；
2. **不得**再出现"across 204 experiments"这类把行数当独立样本数的措辞 ——
   改为"across 204 archived runs drawn from 6 dataset × backbone cells"；
3. `discussion.tex:18` 的 "strong negative correlation"（r=−0.714/−0.594）
   建议补一句限定：该相关主要由 CLIP ViT-B/32 单元（192/204 行）贡献。

---

## 5. 可直接写进 limitation 的一句话

**英文（建议直接采用）**：

> Although the DG–R@1 association remains significant once the nesting of runs is taken into
> account (cluster-robust slope −1.05 with a CR1 standard error of 0.29 under dataset × backbone
> clustering, *p* = 0.016; family-clustered bootstrap 95% CI [−0.887, −0.615]), the 204 archived
> runs are not 204 independent observations: 173 of them (84.8 %) fall in a single dataset ×
> backbone cell and 192 (94.1 %) share one backbone, so the design effect is ≈ 23 and the
> effective sample size is ≈ 9. The reported correlation should therefore be read as a robust
> association within this archive rather than as a precise estimate that transfers to new
> backbones or datasets.

**中文对照**：DG–R@1 关联在计入实验的嵌套结构后仍显著（dataset×backbone 聚类下稳健斜率 −1.05，
CR1 标准误 0.29，p = 0.016；family 聚类 bootstrap 95% CI [−0.887, −0.615]），
但 204 次归档运行并非 204 个独立观测：其中 173 次（84.8 %）落在同一个 dataset×backbone 单元内、
192 次（94.1 %）共享同一骨干，故设计效应约 23、有效样本量约 9。
因此报告的相关性应被读作**本归档内的稳健关联**，而非可迁移到新骨干或新数据集的精确估计。

*（所有数字出处：`pr_stats_hardened.json :: verdict.cr1_beta_DG / cr1_se_design_cell /
cr1_p_design_cell_t5 / clustered_ci_family / design_effect.* / verdict.largest_cell_share`；
`by_model` 的 192/204 见 `pr_stats_within_group.json :: by_model."CLIP ViT-B/32".n`。）*

---

## 6. 数字→出处总表

| 数字 | 脚本 | 归档文件 | 字段 |
|---|---|---|---|
| r = −0.7142, n = 204 | `tools/_p260_pr_stats_hardening.py` | `outputs/analysis/pr_stats_hardened.json` | `verdict.pooled_r` |
| −0.5506 / −0.7310（组内汇聚） | 同上 | `outputs/analysis/pr_stats_within_group.json` | `pooled_within_family.r_within` / `pooled_within_design_cell.r_within` |
| flickr30k −0.7809 / coco −0.5984 | 同上 | `pr_stats_within_group.json` | `by_dataset.flickr30k.r` / `by_dataset.coco.r` |
| CLIP −0.7476 / BLIP −0.9765 / SigLIP +0.8083 | 同上 | `pr_stats_within_group.json` | `by_model.*` |
| 12 族逐族 r | 同上 | `pr_stats_within_group.json` | `by_family.*` |
| β_DG = −0.9526 ± 0.0790（M4） | 同上 | `pr_stats_mixed_effects.json` | `M4_random_intercepts_dataset_model_config.beta_DG / .se_DG` |
| ICC 0.9449（分层 0.6027/0.0634/0.2787） | 同上 | `pr_stats_mixed_effects.json` | `M4_….icc_total_random` / `.icc.levels` |
| M1 β=−1.0112±0.0774, ICC=0.8873 | 同上 | `pr_stats_mixed_effects.json` | `M1_random_intercept_config.*` |
| CR1 SE 0.2911, 4.03×, p=0.0155 | 同上 | `pr_stats_mixed_effects.json` | `cluster_robust_OLS.by_design_cell.*` |
| REML 自检（斜率 −1.193, τ 比值） | 同上 | `pr_stats_mixed_effects.json` | `self_test_reml.*` |
| bootstrap CI [−0.848,−0.076] / 5.27× | 同上 | `pr_stats_cluster_bootstrap.json` | `clustered_by_design_cell.ci95` / `widening_design_cell_vs_naive` |
| bootstrap CI [−0.887,−0.615] / 1.85× | 同上 | `pr_stats_cluster_bootstrap.json` | `clustered_by_family.ci95` / `widening_family_vs_naive` |
| frac(r≥0)=0.0124（6 簇） | 同上 | `pr_stats_cluster_bootstrap.json` | `clustered_by_design_cell.frac_r_ge_0` |
| 样本外 R² 0.2363 / 折中位 0.2266 | 同上 | `pr_stats_holdout.json` | `leave_one_design_cell_out.r2_oos_pooled` / `.r2_oos_median_fold` |
| 逐折 R²（含 SigLIP −94.826） | 同上 | `pr_stats_holdout.json` | `leave_one_design_cell_out.folds[*].r2_oos` |
| Mundlak 组内 −1.0706 / 组间 −1.0093 | 同上 | `pr_stats_hardened.json` | `mundlak_within_between[0].*` |
| 设计效应 22.98 / 有效 n 8.88 | 同上 | `pr_stats_hardened.json` | `design_effect.design_cell.*` |
| 敏感性 S2–S5 | 同上 | `pr_stats_hardened.json` | `sensitivity.*` |
| 标签推导与出处 | — | `pr_stats_hardened.json` | `label_evidence.*`（含 `tier` 与 `evidence` 字符串） |

**产物指纹（SHA256 前 16 位，2026-10-12 最终一次运行）**：

| 文件 | SHA256[:16] | bytes |
|---|---|---|
| `outputs/analysis/pr_stats_hardened.json` | `A62B2E7C12533C75` | 89239 |
| `outputs/analysis/pr_stats_within_group.json` | `68863FBD340FB713` | 27680 |
| `outputs/analysis/pr_stats_mixed_effects.json` | `6E76DA8AAC39A17B` | 6627 |
| `outputs/analysis/pr_stats_cluster_bootstrap.json` | `7451878AFD1C9346` | 1725 |
| `outputs/analysis/pr_stats_holdout.json` | `983E91F2BF6EF61B` | 40244 |
| `tools/_p260_pr_stats_hardening.py` | `2C9314463ADEEFE4` | — |

复核命令：`python tools\_p260_pr_stats_hardening.py`（两次连跑输出哈希一致，已实测）。

---

## 7. 未解决 / 归档缺失（如实报告，未用近似数顶替）

1. **`results.json` 不记录 dataset / model / config** —— 这是本次分析最大的结构性缺口。
   分组标签全部靠 `experiments/` 的 runner 配置与稿件交叉引用**推导**（档位见 §1.2）。
   **建议**：今后每次 run 把 `dataset` / `clip_model` / 位置 / rank / alpha 一并写进 `results.json`，
   否则任何"分组统计"都无法自证。这是审稿人 R1.2 的**根因修复**。
2. **`vitl` 族（2 行）无 runner 脚本可考** → dataset 记为 `UNDOCUMENTED`，未纳入数据集/模型分析。
   归档里找不到写 `outputs/vitl` 的脚本。
3. **`imagenet_zs` 族（3 行）数据集身份存疑** —— 仓库自带 `tools/clip_zs_check.py`、
   `tools/clip_tinyimagenet_check.py` 正是为查此问题而存在，说明**当时未定论**。
   本报告记为 `DISPUTED` 并排除；**未**替你填成 ImageNet。
4. **`outputs/theory/v1_coco/` 有聚合 JSON（81 行）但没有 `results.json`** → 不在这 204 行内，
   ★ 因此 COCO 侧只有 16 行（`coco` 7 + `theory/coco` 9）。
   即**跨数据集对照的 COCO 臂明显比 Flickr30k 臂薄**（16 vs 183），这本身是一个限制。
5. **设计单元只有 6 个** → 任何以设计单元为簇的推断（CR1、bootstrap、留一）都建立在 6 个单元上，
   区间宽且不稳。这是**数据本身的限制，不是估计方法的问题**，无法通过换统计方法消除。
6. `statsmodels` / `sklearn` 未安装 → 未能用 `MixedLM` / `GEE` 交叉验证自写的 REML。
   已用**已知真值的模拟自检**替代（斜率精确复原、方差成分量级复原），但**不是**第三方实现互证。
   若需第三方互证，可 `conda install -n pytorch statsmodels` 后重跑（本脚本不依赖它，无需改动）。

---

## 附：本报告遵守的项目纪律自检

- ✅ **每个数字都有出处**：(a) 产出脚本 `tools/_p260_pr_stats_hardening.py`，
  (b) 归档文件 + JSON 字段路径，全部列入 §6 总表。
- ✅ **无来源的数字已删除**：未使用任何近似、推断或"应该是这个量级"的数值；
  无法归类的 5 行**如实报为 UNDOCUMENTED / DISPUTED**，未硬塞进任何分组。
- ✅ **脚本而非内联**：全部逻辑在 `tools/_p260_pr_stats_hardening.py`，幂等（两次连跑哈希一致），
  含 8 处断言（n=204、路径唯一、逐行重读逐位相等、复现 −0.7142、聚类 CI 必须比朴素宽、
  S1 必须等于汇合 r、混合斜率不得偏离 OLS 过远、REML 自检）。
- ✅ **未改任何 `paper合/*.tex`**；未改动任何实验归档；写入范围仅
  `tools/`、`outputs/analysis/`、`docs/PR_STATS_FIX.md`。
- ⚠️ **未更新** `HANDOFF.md` / `文件地图.md` —— 这两份不在本任务写入范围内，
  按阶段收尾规则需由 Lead 追加本条目（2026-10-12，`task-1`）。
