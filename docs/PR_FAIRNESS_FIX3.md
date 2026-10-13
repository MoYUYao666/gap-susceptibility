# PR R1.6 收尾（二）— 全量微调 7 档学习率 × 2–3 seed：形状、塌缩区、与归档的分叉

**任务**：`task-7`（causal-hardener）· **日期**：2026-10-12 ·
**主交付件**：本文 + `outputs/analysis/pr_fullft_lr_sweep_full.json`（19 次全量微调 /
7 个 lr / 每点 2–3 seed / 0 有效失败）＋ 渲染表 `outputs/analysis/pr_fullft_tables.md`（T1–T7）

---

## 0. 结论速览

**7 档 lr 完整网格**（冻结基线 zero-shot **59.91 %**、CG **0.8157**；sd 一律为**样本 sd（ddof=1）**）：

| lr | n seed | zero-shot top-1 % (mean ± sd) | **ΔCG** (mean ± sd) | R@1 (mean ± sd) | 区域 |
|---|---|---|---|---|---|
| 1e-07 | 2 | 60.52 ± 0.02 | **−0.0058 ± 0.0004** | 0.1760 ± 0.0014 | functional |
| 3e-07 | 2 | 61.07 ± 0.01 | **−0.0069 ± 0.0012** | 0.1782 ± 0.0060 | functional |
| 1e-06 | 3 | 60.87 ± 0.21 | **−0.0016 ± 0.0052** | 0.1808 ± 0.0028 | functional |
| 1e-05 | 3 | 52.18 ± 1.03 | **+0.1860 ± 0.0047** | 0.1700 ± 0.0022 | functional |
| 3e-05 | 3 | 29.72 ± 1.50 | **+0.2531 ± 0.0029** | 0.1508 ± 0.0047 | functional |
| 1e-04 | 3 | 2.63 ± 2.17 | **+0.4416 ± 0.3077** | 0.0448 ± 0.0364 | **塌缩区** |
| 3e-04 | 3 | 0.10 ± 0.03 | **+0.1545 ± 0.8551** | 0.0010 ± 0.0000 | **塌缩区** |

（字段：`pr_fullft_lr_sweep_full.json :: analysis.per_lr.<lr>.{n_seeds,zero_shot_top1_pct_mean,
zero_shot_top1_pct_sd,dCG_mean,dCG_sd,R@1_mean,R@1_sd}`；逐 run `:: runs[*].final`；渲染表 T3/T7。）

**三条问题的答案**

| 问题 | 答案 |
|---|---|
| **A. ΔCG 扩大是否在某个 lr 以下消失/反向？形状？** | **是**：lr ≤ 1e-6 时 ΔCG **全部为负**（−0.0069…−0.0016，缺口不扩大、甚至略缩），zero-shot **≥ 冻结值**（60.5–61.1 %）。符号在 **1e-6 与 1e-5 之间翻转**，此后 **1e-6 → 1e-5 → 3e-5 单调上升**（−0.0016 → +0.1860 → +0.2531）。再往上不是"饱和"而是**塌缩区**（1e-4 起 zero-shot ≤ 4 %，3e-4 时嵌入退化为常数点，CG/DG 失去意义）。形状 = **平台（略负）→ 陡升 → 塌缩**。**存在一处内部极小值**：3e-7 的 −0.0069 低于两侧（1e-7 的 −0.0058、1e-6 的 −0.0016），但只低 0.0011（≈1.6–2.4× 审计的 ΔCG 抽样噪声 sd），且 1e-6 自身 seed sd = 0.0052 ⇒ **不据此宣称最优 lr**（逐点检查见 T7）。 |
| **B. 高 lr 补 seed：发散每次都发生吗？** | **每次**。1e-4 三个 seed zero-shot = **0.14 / 4.15 / 3.59 %**（全部损失 ≥93 %，但**深度是混沌的**，ΔCG +0.7969/+0.2600/+0.2679，sd 0.31）；3e-4 三个 seed = **0.08 / 0.08 / 0.13 %**，且出现**两种不同的退化几何**（见 §4）。 |
| **C. 与 2026-08 归档的分叉** | **可量化、但成因未定**：逐 epoch 曲线**从第 1 个 epoch 就分叉**（排除"后期浮点漂移"），但**最终指标高度一致**（seed 123：zero-shot 4.15 vs 归档 4.12，ΔCG +0.2600 vs +0.2609；seed 999：3.59 vs 3.39，ΔCG +0.2679 vs +0.2672）；**seed 42 是唯一明显分叉的**（ΔCG +0.797 vs +0.665）。归档不存 torch/cuDNN 版本、也不存数据指纹 ⇒ **成因判"未定"**。 |

---

## 1. 协议与"确实在做全量微调"的证明

协议与 task-5 完全一致（评测函数直接 import `tools/_p263_fullft_lr_sweep.py`）：
Flickr30k captions [0, 2000)、batch 64、fp16、**10 epoch**、AdamW(wd 0.01)、cosine（按 step）、
grad clip 1.0；评测 = ImageNet-1K 前 **14,288** 张单模板 zero-shot + Flickr30k [2000,3000) 的
CG/DG（`src/gap_metrics.GapTracker`）与 R@1（1000 对）；冻结基线沿用 task-5 的同一测量
（`frozen.zero_shot.top1_pct = 59.91`、`frozen.gap_retrieval.CG = 0.8157`）。

每次运行都断言 `all(p.requires_grad)` 且 `n_trainable_params == n_total_params == 151,277,313`
（`runs[*].{n_trainable_params,n_total_params,all_parameters_requires_grad}`）——
即"参数量大 ≠ 全量微调"那个坑没有重演；19 次运行全部满足。

### 1.1 ΔCG 的**口径**（Lead 要求写明）

- **基准**：`ΔCG = r["final"]["CG"] − frozen["gap_retrieval"]["CG"]`，其中冻结 CG = **0.8157**，
  来自 `pr_fullft_lr_sweep_full.json :: frozen.gap_retrieval.CG`（task-5 在本协议同一 1000 对上实测）。
  **不是**用归档 `centroid_gap.json :: cg_delta` 字段。Lead 的复算也用 0.8157 ⇒ **基准口径两边一致**，
  数值差异不是基准造成的。
- **sd**：本文件所有 sd 均为**样本 sd（ddof=1）**。Lead 表里的两个 sd 与本文不同，原因有两条，
  且都能逐位对上：
  1. **ddof**：1e-4 三个点（+0.7969 / +0.2600 / +0.2679）——ddof=1 得 **0.3077**，
     ddof=0 得 0.3077×√(2/3) = **0.2512**，与 Lead 的 0.2512 逐位一致。
  2. **n 不同**：Lead 的 3e-4 sd = **0.8077** 是当时**只有 2 个 seed**（+0.8001 / −0.8153）的
     ddof=0 值（1.1422×√(1/2)）；本次最终表里 3e-4 已有 **3 个 seed**（+0.8001 / −0.8153 / +0.4786），
     ddof=1 得 **0.8551**、ddof=0 得 0.6982。
  * n=2 的两行（1e-7、3e-7）两侧差异纯为 √2：0.0004 ↔ 0.0003、0.0012 ↔ 0.0008。
- 结论：**两种 sd 都对，但必须唯一可指认**。本文一律 ddof=1；要与 ddof=0 对照就乘 √((n−1)/n)，
  并且**必须同时写明 n**（3e-4 的 Lead 值与本文值的差别一半来自 n=2→3）。

### 1.2 噪声纪律（引审计成员的独立测量，本报告不重复该测量）

`outputs/analysis/dinov2_hetero/gallery_noise/results_corrected.json`
（脚本 `tools/_p366_gallery_noise_fix.py`）四个臂 × 独立 draws：

| 臂（字段路径 `corrected.<arm>.*`） | `delta_CG_protocol_independent_draws.sd` | `R1_final.sd` |
|---|---|---|
| `clip_b32_text_only` | 0.00070 | 0.00777 |
| `clip_b32_both` | 0.00045 | 0.00550 |
| `clip_b32_vision_only` | 0.00054 | 0.00612 |
| `dinov2_het_text_only_seed42` | 0.00027 | 0.00445 |

⇒ **ΔCG 的差异（0.02–0.80）远大于抽样噪声**，照常解读；**R@1 差异 < 0.007 一律不解读**
（本表内 1e-7 的 0.1760 与 3e-7 的 0.1782 相差 0.0022、1e-6 的 0.1808 与 3e-7 相差 0.0026 —— 均不解读）。

---

## 2. A：形状（平台 → 陡升 → 塌缩区）

渲染表 T7（`pr_fullft_tables.md`）逐条读法：

1. **平台（lr ≤ 1e-6）**：三点 ΔCG 全为负，|ΔCG| ≤ **0.0069**；zero-shot 60.52–61.07 %，
   **全部 ≥ 冻结 59.91 %**。即在此区间"全量微调不扩大缺口"，甚至把缺口略微收窄、把 zero-shot 略微抬高。
2. **平台本身不是严格有序**：逐点序列为 −0.0058（1e-7）→ −0.0069（3e-7）→ −0.0016（1e-6）；
   中间那点低于两侧，因此**存在一处内部极小值**——量化与判读见第 5 条（不再写成"无极小值"，
   那类全称否定必须先逐点穷举）。
3. **翻转点**：最后一个仍为负的是 **1e-6**，第一个转正的是 **1e-5** ⇒ 阈值落在 (1e-6, 1e-5)。
4. **陡升且单调**（1e-6 起）：−0.0016 → **+0.1860**（1e-5）→ **+0.2531**（3e-5），
   后两点 sd 仅 0.0047/0.0029 ⇒ 上升是真实的、可复现的。
5. **存在一处内部极小值 —— 逐点检查过，不是断言**：3e-7（−0.0069）**低于两侧**
   （1e-7 的 −0.0058、1e-6 的 −0.0016）。但两个间隔分别只有 **0.0011** 与 0.0053：前者
   ≈1.6–2.4× 审计的 ΔCG 抽样噪声 sd，后者与 1e-6 自身的 seed sd（0.0052）同量级
   ⇒ **该凹陷在噪声量级内，不能据此宣称"最优学习率"**。
   （T7 由 `tools/_p264_fullft_tables.py` 逐点枚举并写入
   `pr_fullft_verdict.json :: shape.interior_minima_functional_regime`；本文件不再出现任何
   "无极小值"之类的全称否定——那类断言必须先穷举。）

---

## 3. B：高 lr 补 seed —— 发散是否每次都发生

| lr | seed 42 | seed 123 | seed 999 | ΔCG 逐 seed |
|---|---|---|---|---|
| 3e-05 | 31.44 % | 29.04 % | 28.69 % | +0.2498 / +0.2542 / +0.2553 |
| 1e-04 | **0.14 %** | **4.15 %** | **3.59 %** | +0.7969 / +0.2600 / +0.2679 |
| 3e-04 | **0.08 %** | **0.08 %** | **0.13 %** | +0.8001 / **−0.8153** / +0.4786 |

（字段：`runs[*].final.{zero_shot_imagenet1k_top1_pct,CG}`，ΔCG 按 §1.1 口径计算。）

- **3e-5 三点极紧**（sd 1.50 pp / ΔCG sd 0.0029）⇒ 该点可作为"中等 lr 的参考水平"。
- **1e-4：发散每次都发生**（三次全部 ≥93 % 的 zero-shot 损失），但**深度混沌**：seed 42 几乎完全
  崩（0.14 %，ΔCG +0.80），seed 123/999 只崩到 3.6–4.2 %（ΔCG +0.26/+0.27）。**sd 0.31 因此
  不代表"不确定度"，而代表"两个不同的塌缩结局"** —— 单 seed 的 +0.80 不能当作该 lr 的代表值。
- **3e-4：全部崩到 0.08–0.13 %**，且出现**两种退化几何**（见 §4）。

---

## 4. 塌缩区：CG/DG 在该区不再度量模态缺口

| 运行 | zero-shot | **CG** | DG | train loss（末） | val loss（末） | 判读 |
|---|---|---|---|---|---|---|
| 3e-4 / seed 42 | 0.08 % | **1.6158** | 1.6158 | n/a（轨迹记录丢失） | n/a | 图像/文本各自塌成常数点，但两点相距 1.62 |
| 3e-4 / seed 123 | 0.08 % | **0.0004** | 0.0008 | **4.1602**（≈ ln 64 = 4.1589） | 4.1295 | 两模态塌到**同一个**常数点（CG≈DG≈0），训练停在均匀解 |
| 3e-4 / seed 999 | 0.13 % | 1.2942 | 1.2951 | 3.7131 | 4.3827 | 又一种退化几何：训练损失能压到 ln 64 之下（拟合小批次），验证损失反而升到 4.38 |

（字段：`runs[*].final.{CG,DG,zero_shot_imagenet1k_top1_pct}`、`runs[*].history.train_loss[-1]`、
`runs[*].history.val_loss[-1]`；seed 42 的轨迹记录在 task-5 的 resume 缺陷中丢失，其 loss 一栏因此留空，
只有终值来自 `pr_fullft_ckpt_reeval.json` 的复评。ln 64 = 4.1589 是 batch 64 下"均匀预测"的 InfoNCE 值。）

⇒ **这是本任务相对 task-5 结论的唯一实质修正**：3e-4 不是"+0.80 的饱和平台"，而是**退化区**；
在该区 CG 可以 ≈0（两模态重合，seed 123）也可以 ≈1.3–1.6（两模态分离但各自退化，seed 42/999），
三者的 zero-shot 都≈随机，**ΔCG 的 seed 间 spread（±0.86）大于任何效应**，因此删除
"≥3e-5 饱和"的表述是正确的。注：**seed 123 那种 CG≈0 绝不是"缺口消失/对齐变好"**
——它伴随 train loss 停在 ln 64 与 zero-shot 0.08 %（`runs[*].history`）。

---

## 5. C：与 2026-08 归档的分叉（量化 + seed 特异性 + 成因未定）

分析脚本 `tools/_p297_divergence_compare.py` → `outputs/analysis/pr_fullft_divergence.json`。

### 5.1 逐 epoch 分叉（本轮首次量化）
- **两个可比 seed（123、999）的验证损失曲线从第 1 个 epoch 就分叉**（
  `per_seed.<seed>.first_divergence_val_loss.epoch = 1`），第 1 个 epoch 的 train loss 差 0.040（seed 999）。
  ⇒ **不能用"后期浮点漂移"解释**：两条曲线一开始就在不同的轨迹上（数据顺序/增强抽样不同，
  或库版本不同）。
- 分叉后 val loss 的最大绝对差：seed 123 = **0.45**、seed 999 = **0.43**
  （`per_seed.<seed>.val_loss_max_abs_diff_after_divergence`）。

### 5.2 但最终指标高度一致（seed 特异性）
| seed | 本次 zero-shot | 归档 zero-shot | Δ | 本次 ΔCG | 归档 ΔCG | Δ |
|---|---|---|---|---|---|---|
| 123 | 4.15 % | 4.12 % | 0.03 pp | +0.2600 | +0.2609 | 0.0009 |
| 999 | 3.59 % | 3.39 % | 0.20 pp | +0.2679 | +0.2672 | 0.0007 |
| 42 | 0.14 % | 0.13 % | 0.01 pp | +0.797 | +0.665 | **0.132** |

（本次字段：`pr_fullft_lr_sweep_full.json :: runs[*].final`；归档字段：
`outputs/imagenet_zs_rerun/full_ft{,_s123,_s999}/results.json :: {zero_shot_imagenet1k.synset_single_template,final_R1}`、
`centroid_gap.json :: {cg_delta,frozen_centroid_gap}`；比对表
`pr_fullft_divergence.json :: verdict.final_metric_agreement_with_archive`。）

⇒ **环境/流程本身是可复现的**（两个 seed 的最终指标与归档差 ≤0.2 pp / ≤0.0009），
**分叉只出现在完全塌缩的 seed 42 上**（ΔCG 差 0.132，占该点值的 17 %）。

### 5.3 成因：**未定**
- **检索范围先说清**（避免又一次未穷举的全称否定）。实际检索：
  ① **文件名**：`outputs/` 全目录递归，按 `env|version|meta|fingerprint` 匹配 → **0 个命中**；
  ② **内容**：全量微调归档的 **13 个 JSON**（`outputs/imagenet_zs_rerun/**/*.json` +
  `outputs/imagenet_zs/**/*.json`）按关键词 `torch|cudnn|version|fingerprint|transformers`
  检索 → **0 个命中**。
  该批 `results.json` 只写超参（dataset/epochs/lr/weight_decay/scheduler/seed/amp/grad_clip），
  且**不含数据指纹**（`clip_fullft_rerun.py` 未记录切片哈希）。
  ⇒ 结论限定在这个范围内：**在这 13 个归档 JSON 里没有可供比对的环境/版本信息**。
- **本次环境仅记为本次信息**：torch **2.9.1+cu130**、CUDA available、RTX 4060 Laptop 8 GB
  （`pr_fullft_divergence.json :: verdict.statement` 已注明"不能假定归档运行也是这个环境"）；
- 因此**不能**断言"版本漂移"，也**不能**断言"数据顺序变了"：判 **undetermined**。

---

## 6. Adapter `up.bias`：实现疏漏，不是方法属性

（`tools/_p296_adapter_init_check.py` → `outputs/analysis/pr_adapter_init_check.json`）

| 状态 | zero-shot | CG | DG | R@1 |
|---|---|---|---|---|
| 出厂实现（`up.bias` 非零） | **0.15 %** | 1.2065 | 1.2120 | 0.0015 |
| 内存中把 `up.bias` 置零 | **59.91 %** | **0.8155** | 0.8633 | 0.1585 |

（冻结参照：59.91 % / CG 0.8157 / R@1 0.1555 ⇒ 置零后**逐项回到冻结模型**。）
`up.weight` 全零、`up.bias` 未初始化：mean|b| = 0.063、max|b| = 0.125 = `nn.Linear` 默认均匀分布
的界 1/√64（`bias_stats.*`）。

**判断（与 `discussion.tex` 的 Eleventh limitation 一致）**：
① 代码零初始化 `up.weight` 的目的显然是**近恒等初始化**，却漏了 `up.bias` ⇒ **实现疏漏**；
② 同仓库更晚的实现 `tools/clip_peft_gamma_ordering.py`（2026-09-13，主路径 `src/peft_methods.py`
为 2026-06-19）**已显式** `nn.init.zeros_(self.up.bias)` ⇒ 旁证"零 bias 才是本意"；
③ 因此论文旧约定（`delta_old`，从**注入后**状态量起）得到的 Adapter 数字**不可与 LoRA 比较**
（task-6 已量化：统一口径下 adapter_both 在任何 lr 都是正 ΔCG）；
④ **不主张**"Adapter 方法本身有缺陷"——本检查只说明本仓库这份实现不是恒等初始化。

---

## 7. 事件记录：3 次 `AcceleratorError` 是否影响结果

- 第一次尝试中，`lr=1e-4 seed999` 在 epoch 4 触发
  `AcceleratorError: CUDA error: unknown error`（异步上下文损坏），随后 `3e-4 seed123`、`3e-4 seed999`
  在同一进程内**立即失败**（同错误）；脚本把三条记为 `error` 记录后结束。
- **重试（新进程）后三个 cell 全部跑完并落盘**：1e-4/999 = 3.59 %（ΔCG +0.2679）、
  3e-4/123 = 0.08 %（CG 0.0004）、3e-4/999 = 0.13 %（ΔCG +0.4786）。
- **结论：不影响任何结果**。合并文件 `pr_fullft_lr_sweep_full.json` 只含非失败运行
  （`_p265` 以 `not r.get("error")` 过滤），失败记录仅留在 `pr_fullft_lr_sweep_ext.json`（第 17–22 条）
  作为过程记录；同错误在 task-2 的扩展运行中也出现过一次（那次也是重试后 0 失败）。
- 全程**未出现 OOM**（full-FT batch 64 fp16 峰值 3,787 MB，
  `pr_fullft_feasibility.json :: configurations[b64_fp16].peak_allocated_mb`）。

---

## 8. 溯源表

| 文档中的数字 | 归档文件 | 字段 |
|---|---|---|
| 7 档 lr 的 n / zero-shot / ΔCG / R@1（mean ± sd） | `outputs/analysis/pr_fullft_lr_sweep_full.json` | `analysis.per_lr.<lr>.*` |
| 逐 run 终值（含 3e-4 的 CG 0.0004 等） | 同上 | `runs[*].final.*` |
| 逐 epoch 轨迹（含 train loss 停在 ln 64 附近） | 同上 | `runs[*].history.{train_loss,val_loss,R@1_mean}` |
| 冻结基线 59.91 % / 0.8157 | 同上 | `frozen.*` |
| 形状判读（平台/翻转点/单调性/塌缩区） | `outputs/analysis/pr_fullft_tables.md` T7 + `pr_fullft_verdict.json` | `shape.*` |
| 与归档的逐 epoch 分叉、最终一致性、verdict | `outputs/analysis/pr_fullft_divergence.json` | `per_seed.<seed>.{first_divergence_val_loss,val_loss_max_abs_diff_after_divergence,final_agreement}`、`verdict.*` |
| 归档 4.12 %/+0.2609、3.39 %/+0.2672 | `outputs/imagenet_zs_rerun/full_ft_s{123,999}/` | `results.json :: {zero_shot_imagenet1k.synset_single_template}`、`centroid_gap.json :: cg_delta` |
| 画廊抽样噪声 sd | `outputs/analysis/dinov2_hetero/gallery_noise/results_corrected.json`（脚本 `tools/_p366_gallery_noise_fix.py`，审计成员独立测得） | `corrected.<arm>.{delta_CG_protocol_independent_draws.sd,R1_final.sd}` |
| Adapter 注入/置零后的几何 | `outputs/analysis/pr_adapter_init_check.json` | `as_shipped.*`、`up_bias_zeroed.*`、`bias_stats.*`、`verdict.*` |
| 可行性（峰值显存、单步耗时） | `outputs/analysis/pr_fullft_feasibility.json` | `configurations[*].*` |
| 本次环境 torch 2.9.1+cu130 | `pr_fullft_divergence.json` | `verdict.statement`（并见 §5.3 说明） |

**本次新建/改动的文件**

| 文件 | 说明 |
|---|---|
| `tools/_p295_fullft_extend.py` | A/B/C 三段的驱动（`--apply/--include-c/--only-c`，幂等 `--resume`） |
| `tools/_p296_adapter_init_check.py` | Adapter 注入损坏的根因定位（不改 `src/`，仅内存置零） |
| `tools/_p297_divergence_compare.py` | 与归档的逐 epoch/终值对照 + verdict |
| `tools/_p265_fullft_reeval.py`（改） | 增量复核（按权重 sha1 复用）+ `--prefer-recorded`（新 run 不再重复评测，省 GPU） |
| `tools/_p264_fullft_tables.py`（改） | 新增 T7 形状表（平台/翻转点/单调性/塌缩区自动判定） |
| `tools/_p263_fullft_lr_sweep.py`（改） | 汇总打印对"只有复评记录"的 run 不再 KeyError |
| `outputs/analysis/pr_fullft_lr_sweep_ext.json` | 扩展网格的原始记录（含 3 条 CUDA 失败记录，保留为过程记录） |
| `outputs/analysis/pr_fullft_lr_sweep_full.json` | **合并后的完整网格（19 run / 7 lr）** ← 本报告引用 |
| `outputs/analysis/pr_fullft_tables.md` / `pr_fullft_verdict.json` | T1–T7 表与机器可读结论 |
| `outputs/analysis/pr_fullft_divergence.json` | C 项全部证据 |
| `outputs/analysis/pr_adapter_init_check.json` | Adapter 根因证据 |
| `outputs/analysis/_p263_ext_backup_13runs.json` | 暂停时点的备份（过程记录） |
| `outputs/analysis/pr_fullft_sweep/<lr>_seed<s>/model_state_last.pt` | 19 个全量微调权重（各 605 MB） |

**复现命令**（单进程串行；task-8 并行时实测 per-epoch 从 47–65 s 退化到 148–254 s、单次 zero-shot
评测 80 s → 819 s，故**必须独占**）
```powershell
$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'
python tools\_p295_fullft_extend.py --apply                 # A(4 run) + B(6 run)
python tools\_p295_fullft_extend.py --apply --only-c        # 可选：C 的复跑（本次未跑，见 §9.3）
python tools\_p265_fullft_reeval.py --apply --reuse-raw --prefer-recorded --sweep outputs/analysis/pr_fullft_lr_sweep_ext.json
python tools\_p264_fullft_tables.py --apply --sweep outputs/analysis/pr_fullft_lr_sweep_full.json
python tools\_p297_divergence_compare.py --apply
python tools\_p296_adapter_init_check.py --apply
```

---

## 9. 限制

1. **3e-4 只有 2 个"可用几何"的 seed + 1 个第三种（0.4786）**：三点已经显示该区退化几何不唯一，
   但"共有几种退化结局"无法从 3 个 seed 判定；本报告只声明"CG/DG 在该区不可解释"。
2. **1e-4 的 sd 不应当作不确定度**：三次运行给出两个不同的塌缩深度（≈0.14 % 与 ≈3.6–4.2 %），
   均值 2.63 % 与 sd 2.17 只是这两簇的混合，任何"1e-4 的 ΔCG = 0.44 ± 0.31"的写法都应附带
   "由两种结局混合、非单峰"。**逐 seed 值必须与均值同时报告**。
3. **C 项未做"本次会话内的重跑"**：`_p295 --include-c` 的 1e-4/seed42 复跑因 GPU 让位给 task-8 而
   **未执行**（`pr_fullft_divergence.json :: verdict.within_session_reproduction_run_executed = false`），
   所以"同会话内可复现性"没有直接证据；不过 seed 123/999 与归档的终值一致（§5.2）已经说明环境
   本身可复现。**版本漂移假设仍未定**（归档无版本记录）。
4. **数据指纹缺失**：`clip_fullft_rerun.py` 与本次 `_p263` 都未记录训练/验证切片的文件哈希，
   因此"数据顺序/内容是否变化"无法核对——这正是 §5.3 判"未定"的原因之一，也是今后应补的记录项。
5. **R@1 差异 < 0.007 不解读**（§1.2）；本表中的 R@1 只作一致性辅证（该 val 切片每图 5 条 caption，
   对角口径上限 ≈0.2）。
6. **并行期（与 task-8 共用 GPU 约 1.5 h）只影响耗时、不影响数值**：实测 per-epoch 从 47–65 s
   退化到 148–254 s、单次 zero-shot 评测从 80 s 到 819 s（`runs[*].history.epoch_seconds` 可查）；
   无 OOM。该期间的 3 次运行（3e-5/123、3e-5/999、1e-4/123）数值与同 lr 的其它 seed 一致
   （3e-5 三点 31.44/29.04/28.69 %），且同 lr/seed 的重跑在 task-5 已验证逐位一致
   （`pr_fullft_lr_sweep_full.json` 中 1e-5/1e-6 各 3 seed 来自两次独立训练，数值相同）。
   最后 6 次运行在**独占** GPU 下完成。
