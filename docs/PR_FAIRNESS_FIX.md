# PR R1.6 — 全量微调公平性：8 GB 可行性 + 学习率扫描

**任务**：`task-5`（causal-hardener）· **日期**：2026-10-12 · **交付件**：本文 + `outputs/analysis/pr_fullft_lr_sweep_full.json`（唯一数字来源）

**审稿人 R1.6 原话**：

> *"directly using the same learning rate for LoRA, Adapter, and full fine-tuning may not
> constitute a fair comparison, because full fine-tuning is typically more sensitive to the
> learning rate. In the current results, full fine-tuning on CIFAR-100 drops from 60.72% to
> 7.38% ... may also reflect optimization instability."*

---

## 0. 结论速览

| 问题 | 答案 | 证据 |
|---|---|---|
| **8 GB 能不能跑全量微调？** | **能**，但**不是现稿写的那套配置**。batch 128 / fp32 需要 **11,354 MB** 峰值分配 > 物理显存 **8,187.5 MB** → 只能走 Windows 主机内存回退，单步 **11.32 s**（batch 128 fp16 只要 1.55 s，慢 **7.3×**）。batch 64 fp16（归档全量微调配置）峰值 **3,787 MB**，单步 0.81 s | T1 |
| **是否 OOM？** | 5 个配置**全部未报 OOM**，但 `manuscript_b128_fp32` 超出物理显存 3.2 GB | T1 |
| **扫描了几个 lr？** | **5 个**：{1e-6, 1e-5, 3e-5, 1e-4, 3e-4}；1e-6 与 1e-5 各 **3 seeds**，其余各 1 seed；共 9 次全量微调，每次 10 epoch | T2 |
| **最优 lr 下"全量微调破坏对齐"还成立吗？** | **不成立（对 zero-shot 与 CG 都不成立）**。最优 lr=1e-6 时：zero-shot **60.87 ± 0.21 %**（冻结 59.91 %，**+0.96 pp**）、**ΔCG = −0.0016 ± 0.0052**（与 0 不可分辨）、R@1 **0.1808 ± 0.0028**（冻结 0.1555，**变好**） | T3 |
| **那么"破坏"从哪来？** | **来自共用的 lr=1e-4**。损伤随 lr 单调：zero-shot 60.87 → 52.18 → 31.44 → 0.14 → 0.08 %；ΔCG −0.002 → +0.186 → +0.250 → +0.797 → +0.800 | T3 |
| **现稿句子的两个数字可靠吗？** | "zero-shot → 2.6 %（3 seeds）"可复现（我 lr=1e-4 得 0.14 %，归档重跑 0.13/4.12/3.39 %）；**但"+24 % CG"来自另一次运行**（原始 full-FT：`outputs/imagenet_zs/full_ft/results.json`，ΔCG +0.1887 = +23.1 %，且那次**没有崩**：R@1 0.647、val loss 0.53），而 lr=1e-4 的实测是 +81.5 %（重跑）/+97.7 %（本扫描）。一句话里拼了两次不同设置的运行 | T5 + §5 |

---

## 1. 可行性探测（实测，非推断）

`tools/_p262_fullft_feasibility.py`：**每个配置独立子进程**（一次 OOM 不会污染下一个配置的分配器），
每个配置跑 **3 个真实优化步**（前向+反向+AdamW），记录峰值显存、单步耗时与失败原文。
全量微调的**代码级证明**：每个配置都断言 `all(p.requires_grad)` 且
`n_trainable_params == n_total_params == 151,277,313`（父进程再对子进程 JSON 复核一次）。

| 配置 | batch | 精度 | 结果 | 峰值分配 MB | 是否装进物理显存 | 单步 s |
|---|---|---|---|---|---|---|
| 现稿配方 | 128 | fp32 | ok | **11354.2** | **否 — 主机内存回退** | 11.323 |
| | 128 | fp16 | ok | 6686.8 | 是 | 1.554 |
| | 64 | fp32 | ok | 6526.3 | 是 | 1.120 |
| 归档 full-FT 配置 | 64 | fp16 | ok | 3786.7 | 是 | 0.813 |
| | 32 | fp32 | ok | 4162.9 | 是 | 0.681 |

（字段：`outputs/analysis/pr_fullft_feasibility.json :: configurations[*].{peak_allocated_mb,peak_reserved_mb,step_seconds_mean}`；
物理显存 `:: meta.gpu_total_mb = 8187.5`。探测时桌面占用约 1.7 GB，可用 6,476 MB。）

**诚实结论**：全量微调在这台 8 GB 机器上**可行**；但现稿正文写的"所有实验 batch 128、AdamW"这一套
用于全量微调时**装不进显存**——它靠驱动把 3.2 GB 分页到系统内存才跑完，且慢 7.3×。
因此本扫描采用**归档全量微调自己的配置**（batch 64、fp16、10 epoch、2000 条 caption），
这样 lr=1e-4 那一点可与 `outputs/imagenet_zs_rerun/full_ft*` 直接对照。

---

## 2. 扫描协议与"确实在做全量微调"的证明

- 训练：Flickr30k captions [0, 2000)，batch 64，fp16 AMP，AdamW(lr, wd=0.01)，
  cosine（按 step），grad clip 1.0，**10 epoch**，num_workers=0；
  与归档 `tools/clip_fullft_rerun.py` 完全一致（`pr_fullft_lr_sweep_full.json :: meta.protocol`）。
- 评测（每次训练结束后同一套代码）：ImageNet-1K val **前 14,288 张**（= 归档 `n_images`）
  单模板 zero-shot top-1；Flickr30k captions [2000, 3000) 上的 CG、DG
  （`src/gap_metrics.GapTracker`）、R@1(i2t/t2i 均值)。
- **代码级全量微调证明**：每次运行都断言 `n_trainable == n_total`；对只靠 checkpoint 复评的三次运行，
  则断言 **state dict 的参数总数 == 全模型参数总数**（`pr_fullft_ckpt_reeval.json :: reevaluations[*].n_params_in_state_dict`）。
  这直接回应 task-2 发现的教训：`n_trainable_params = 145,170,177` 并不等于全量微调。
- 冻结基线：zero-shot **59.91 %**、CG **0.8157**、DG **0.8636**、R@1 **0.1555**
  （`pr_fullft_lr_sweep_full.json :: frozen`）。

---

## 3. 结果：损伤随学习率单调

| lr | n | zero-shot top-1 % | ΔCG | ΔDG | R@1 | 崩到 <20 % 的 seed |
|---|---|---|---|---|---|---|
| 冻结 | — | **59.91** | — | — | 0.1555 | — |
| **1e-6** | 3 | **60.87 ± 0.21** | **−0.0016 ± 0.0052** | +0.0019 ± 0.0047 | **0.1808 ± 0.0028** | 0/3 |
| 1e-5 | 3 | 52.18 ± 1.03 | +0.1860 ± 0.0047 | +0.1549 ± 0.0036 | 0.1700 ± 0.0022 | 0/3 |
| 3e-5 | 1 | 31.44 | +0.2498 | +0.2102 | 0.1455 | 0/1 |
| 1e-4 | 1 | 0.14 | +0.7969 | +0.7547 | 0.0030 | 1/1 |
| 3e-4 | 1 | 0.08 | +0.8001 | +0.7522 | 0.0010 | 1/1 |

（字段：`pr_fullft_lr_sweep_full.json :: analysis.per_lr.<lr>.{zero_shot_top1_pct_mean,zero_shot_top1_pct_sd,dCG_mean,dCG_sd,dDG_mean,dDG_sd,R@1_mean_of_runs,R@1_sd,seeds_collapsed_below_20pct}`；
逐 seed 原值 `:: runs[*].final`，逐 epoch 轨迹 `:: runs[*].history`。）

三点读数：

1. **zero-shot 的"崩溃"是学习率造成的**：1e-4/3e-4 掉到 0.14 %/0.08 %（1000 类随机 = 0.1 %）；
   而 1e-6 反而是 **60.87 ± 0.21 %，比冻结高 0.96 pp**，1e-5 仍有 52.18 ± 1.03 %。
2. **CG 的加宽对 lr 单调，且在最低 lr 消失**：+0.186（1e-5，相对 +22.1…23.1 %）→ +0.250（3e-5）
   → +0.797/+0.800（1e-4/3e-4，相对 +98 %）；1e-6 时 **−0.0016**，即"全量微调把 gap 拉大"
   在训练得动的前提下**不再成立**。
3. **域内检索反而变好**：1e-6/1e-5 的 R@1（0.181/0.170）都高于冻结 0.1555，与 CG 的走向解耦 ——
   与论文"gap 与任务指标不是同一对象"的论点一致。
   （口径提醒：本 val 切片每图 5 条 caption，对角口径的**理论上限 = 0.2**，故这组 R@1 只能读作"贴近上限"，
   不能与常规 1-caption-per-image 的 R@1 横向比较。）

**直接回答问题**：在最优 lr（1e-6，本扫描的下界）下，"全量微调破坏对齐"**不再成立**：
zero-shot 无损失（甚至 +0.96 pp）、CG 无变化（−0.002）、域内 R@1 提升。现稿那句
"increases CG by 24 % and collapses zero-shot accuracy to near-chance (2.6 %)" 描述的是
**共用 lr=1e-4** 的行为，不是全量微调本身的性质。

### 3.1 复现核对（同一权重、两条独立路径）

`tools/_p265_fullft_reeval.py` 重新加载 9 个保存的 checkpoint 并用同一协议复评：

- **zero-shot top-1 与训练时记录逐位一致**（偏差 **0.00e+00**，确定性）；
- CG/DG 偏差 ≤ **5.4e-4**、R@1 偏差 ≤ **1.15e-2** —— 这两个指标走的是
  `Flickr30kDataset(split='train')` 的**随机增强**（RandomHorizontalFlip + ColorJitter），
  其抽样噪声与权重无关（`pr_fullft_ckpt_reeval.json :: reevaluations[*].{deviation_vs_sweep_json,within_tolerance,deviation_tolerance}`，
  判定 `integrity_verdict = PASS`）。
  ⇒ 本报告的结论依据是 zero-shot 与 CG/DG；R@1 只作辅证，且自带 ~1e-2 的抽样噪声。
- 过程记录（**非归档字段**，可重跑复核）：脚本早期 resume 缺陷使 1e-5/seed42 与 1e-6/seed42
  各被独立训练了两次，两次运行的逐 epoch loss 与终值完全相同（53.20 %/CG 0.9962 与 61.02 %/CG 0.8083），
  说明该流水线在同一 lr/seed 下是确定性的。

---

## 4. 与归档全量微调的对照（T5）

| 运行 | lr | zero-shot % | ΔCG | final val loss | R@1 |
|---|---|---|---|---|---|
| 归档 seed42 | 1e-4 | 0.13 | +0.6646 | 7.877 | 0.0020 |
| 归档 seed123 | 1e-4 | 4.12 | +0.2609 | 3.103 | 0.0530 |
| 归档 seed999 | 1e-4 | 3.39 | +0.2672 | 3.090 | 0.0460 |
| **本扫描 seed42** | 1e-4 | **0.14** | +0.7969 | —（复评） | 0.0030 |

（归档字段：`outputs/imagenet_zs_rerun/full_ft*/results.json :: {zero_shot_imagenet1k.synset_single_template,final_val_loss,final_R1}`、
`centroid_gap.json :: cg_delta`。）

- lr=1e-4 的**崩溃方向完全复现**（0.14 % vs 0.13 %，逐 epoch val loss 4.13/4.13/4.13/4.33/… 与归档
  4.13/4.13/4.13/4.11/… 前 3 个 epoch 相同，第 4 个 epoch 起分岔）。
- 但 **lr=1e-4 是混沌区**：归档三个 seed 的 ΔCG 从 +0.26 到 +0.66，我复现得 +0.80，都落在同一量级但不逐位一致；
  因此"崩溃"可复现，"崩溃时的 CG 具体数值"不可复现 —— 这一点必须在正文写清楚。

---

## 5. 附带发现：现稿那句里的 "+24 % CG" 与 "2.6 % zero-shot" 来自**两次不同的运行**（建议拆开）

逐字段核对（不是推断）：

| 运行 | 归档 | ΔCG | 训练末态的其他证据 |
|---|---|---|---|
| **原始 full-FT 运行** | `outputs/imagenet_zs/full_ft/results.json`（`initial_gap.centroid_gap = 0.8185032` → `final_gap.centroid_gap = 1.0072111`，epoch 10 / step 320；`n_trainable_params = 151,277,313` 真·全量微调）；同值亦见 `outputs/master_results.json :: {cg_init 0.818503, cg_final 1.007211, cg_delta 0.188708}` | **+0.1887 = +23.1 %**（≈ 现稿 +24 %） | **没有崩**：`final_val_loss = 0.5323`、`final_task_metrics.R@1 = 0.6470` |
| **2026-08 重跑（lr = 1e-4）** | `outputs/imagenet_zs_rerun/full_ft*/results.json` | +0.6646 / +0.2609 / +0.2672 | 发散：`final_val_loss` 7.877 / 3.103 / 3.090，`final_R1` 0.0020 / 0.0530 / 0.0460；zero-shot 0.13 / 4.12 / 3.39 % → 均值 **2.55 %**（≈ 现稿 2.6 %） |
| 本扫描 lr=1e-4 seed42 | `pr_fullft_lr_sweep_full.json :: runs[*]` | +0.7969 | zero-shot 0.14 %、R@1 0.0030（崩溃方向复现） |
| 本扫描 lr=1e-5（3 seeds） | 同上 | **+0.186 ± 0.005** | zero-shot **52.18 ± 1.03 %**（gap 变大但仍健康） |

**结论**：现稿那句把**"gap 拉大但训练健康"的原始运行**（+24 %，R@1 = 0.647）与**"完全发散"的重跑**
（zero-shot 2.6 %）**拼在了同一句里**。本扫描把这两种状态分开量化：lr=1e-5 → ΔCG +0.186、zero-shot 52.18 %；
lr=1e-4 → ΔCG +0.797、zero-shot 0.14 %。

而两次运行**连评测协议都不同**：原始运行的 `R@1 = 0.647` 超过了重跑/本扫描所用指标的理论上限
（该 val 切片每张图有 5 条 caption，对角口径上限 = 1/5 = 0.2；本扫描冻结 0.1555、全量微调 0.181 都已贴近上限），
所以它的 R@1 不可能来自同一协议；同时它的 `final_val_loss = 0.5323` 也远低于重跑 7.877 与本扫描 2.1–2.35。
原始运行**未记录 lr 与评测协议**（脚本已丢失），因此今天无法被精确重建。
建议：把这句拆成两半并各自标明运行与配置，或统一改用本扫描的逐 lr 口径。

（另注：旧数字 "7.38 %" 是 legacy 常数，见 `outputs/imagenet1k_zs_synset_single.json :: paper_values.full_ft`，
仓库已有的审计文档已指出它是硬编码而非测量，本报告不引用它。）

---

## 6. 建议改法

### 6.1 可直接放进 response letter 的段落（英文）

> **Fair comparison of full fine-tuning (R1.6).** We agree, and we have measured it. Full
> fine-tuning of CLIP ViT-B/32 is far more learning-rate sensitive than the adapter methods.
> Under one fixed protocol (Flickr30k captions 0–1999, batch 64, fp16, 10 epochs, AdamW, cosine,
> three seeds at the two lowest rates), its ImageNet-1K zero-shot accuracy moves monotonically
> from **60.87 ± 0.21 %** at lr 1e-6 and **52.18 ± 1.03 %** at 1e-5 to 31.44 % at 3e-5, 0.14 % at
> 1e-4 and 0.08 % at 3e-4, against **59.91 %** frozen; the centroid gap moves from ΔCG = −0.002
> to +0.80 over the same range. The collapse we previously reported is therefore a property of
> the **shared** learning rate (1e-4), not of full fine-tuning as such: at the best rate we
> tested, full fine-tuning leaves zero-shot accuracy and the centroid gap indistinguishable from
> the frozen model (+0.72…+1.11 pp across seeds, ΔCG −0.002 ± 0.005) while *improving* in-domain
> retrieval (R@1 0.181 vs 0.156 frozen). We now report the sweep and no longer claim that full
> fine-tuning
> destroys alignment. Relatedly, the two numbers in that sentence come from different runs: the
> "+24 %" CG belongs to the original full fine-tuning run
> (`outputs/imagenet_zs/full_ft/results.json`: CG 0.8185 → 1.0072, i.e. +0.189, with final
> validation loss 0.53 and R@1 0.647 — a run that did *not* collapse), whereas the "2.6 %"
> zero-shot figure belongs to the 2026-08 rerun at lr 1e-4, which diverged (final validation
> loss 7.88, R@1 0.002). We now report the per-rate sweep instead of merging the two. Finally,
> for transparency about hardware: the manuscript's batch-128/fp32 recipe requires 11.4 GB of
> GPU memory for full fine-tuning, above the 8 GB card used here, so our full-fine-tuning runs
> use batch 64 with fp16 autocast throughout.

### 6.2 建议写进 limitation 的一句

> Full fine-tuning is far more learning-rate sensitive than the adapter methods, so our
> full-fine-tuning comparison is a comparison at one shared learning rate rather than at each
> method's optimum: over lr ∈ {1e-6 … 3e-4} its zero-shot accuracy spans 60.9 % to 0.1 % and its
> ΔCG spans −0.002 to +0.80, and the collapse we report is the behaviour of the shared rate
> (1e-4), not of full fine-tuning as such.

---

## 7. 溯源表

| 文档中的数字 | 归档文件 | 字段 |
|---|---|---|
| 峰值显存/单步耗时/是否装进显存 | `outputs/analysis/pr_fullft_feasibility.json` | `configurations[*].{peak_allocated_mb,peak_reserved_mb,step_seconds_mean,outcome}`；物理显存 `meta.gpu_total_mb` |
| `n_trainable == n_total = 151,277,313` | 同上 / `pr_fullft_lr_sweep_full.json` | `configurations[*].{n_trainable_params,n_total_params}` / `runs[*].{n_trainable_params,n_total_params}` |
| 冻结基线 59.91 % / CG 0.8157 / DG 0.8636 / R@1 0.1555 | `pr_fullft_lr_sweep_full.json` | `frozen.{zero_shot.top1_pct, gap_retrieval.CG, gap_retrieval.DG, gap_retrieval.R@1_mean}` |
| 各 lr 的 zero-shot / ΔCG / ΔDG / R@1（含 mean±sd） | 同上 | `analysis.per_lr.<lr>.*`；逐 seed `runs[*].final.*` |
| 逐 epoch train/val loss 与 R@1 | 同上 | `runs[*].history.{train_loss,val_loss,R@1_mean}`（仅训练时被记录下来的 6 次运行有轨迹；另 3 次只有复评终值，`history = null` 并在 `history_note` 里写明原因） |
| 归档 0.13/4.12/3.39 %、ΔCG +0.6646/+0.2609/+0.2672 | `outputs/imagenet_zs_rerun/full_ft{,_s123,_s999}/` | `results.json :: {zero_shot_imagenet1k.synset_single_template,final_val_loss,final_R1}`、`centroid_gap.json :: cg_delta` |
| 原始 full-FT 的 ΔCG +23.1 %（+0.1887）、R@1 0.647、val loss 0.5323 | `outputs/imagenet_zs/full_ft/results.json`（同值亦见 `outputs/master_results.json`） | `initial_gap.centroid_gap` = 0.8185032、`final_gap.centroid_gap` = 1.0072111、`final_val_loss`、`final_task_metrics.R@1`、`n_trainable_params`；`master_results.json :: cg_delta/cg_init/cg_final` |
| legacy 常数 7.38 % | `outputs/imagenet1k_zs_synset_single.json` | `paper_values.full_ft`（硬编码，非测量） |
| 复评与记录的偏差、容差 | `outputs/analysis/pr_fullft_ckpt_reeval.json` | `reevaluations[*].{deviation_vs_sweep_json,deviation_tolerance,within_tolerance}`、`integrity_verdict` |
| checkpoint 的 sha1 与字节数 | 同上 | `reevaluations[*].{weights_sha1,weights_bytes}` |

**本次新建文件**

| 文件 | 说明 |
|---|---|
| `tools/_p262_fullft_feasibility.py` | 8 GB 可行性探测（每配置独立子进程 + OOM 原文） |
| `tools/_p263_fullft_lr_sweep.py` | 全量微调 lr 扫描（`--apply/--resume/--epochs/--batch/--n-zs-eval`） |
| `tools/_p264_fullft_tables.py` | 表渲染（数字不手抄） |
| `tools/_p265_fullft_reeval.py` | checkpoint 复评 + 完整网格合并 + 与记录值的容差核对 |
| `outputs/analysis/pr_fullft_feasibility.json` | 可行性实测（5 配置） |
| `outputs/analysis/pr_fullft_lr_sweep.json` | `_p263` 直接产出（6 次带轨迹的运行，status=complete） |
| `outputs/analysis/pr_fullft_lr_sweep_full.json` | **合并后的完整网格（9 次运行 / 5 个 lr）** ← 本报告引用 |
| `outputs/analysis/pr_fullft_ckpt_reeval.json` | 9 个 checkpoint 的复评与偏差核对 |
| `outputs/analysis/pr_fullft_tables.md` / `pr_fullft_verdict.json` | T1–T5 表格与机器可读结论 |
| `outputs/analysis/pr_fullft_sweep/b64_fp16_lr*_seed*/model_state_last.pt` | 每次运行的最终权重（各 605 MB，共 9 个 = 5.4 GB；本次专门保存，避免重演"权重丢失"） |

**复现命令**（单进程串行；全程约 2 h GPU，峰值 <7 GB）
```powershell
$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'
python tools\_p262_fullft_feasibility.py --apply
python tools\_p263_fullft_lr_sweep.py --apply --lrs 1e-5,3e-5,1e-4,3e-4 --seeds 42      # 崩溃后加 --resume
python tools\_p263_fullft_lr_sweep.py --apply --lrs 1e-6 --seeds 42,123,999 --resume
python tools\_p263_fullft_lr_sweep.py --apply --lrs 1e-5 --seeds 42,123,999 --resume
python tools\_p265_fullft_reeval.py --apply                 # 复评+合并（约 15 min）
python tools\_p264_fullft_tables.py --apply --sweep outputs/analysis/pr_fullft_lr_sweep_full.json
```

---

## 8. 限制（必须与结论一起写）

1. **最优 lr 落在网格边界**（1e-6）：更低的学习率未测，因此不能声称 1e-6 是"最优"，只能说
   "在本扫描的最低 lr 上，损伤已不可分辨"。趋势单调 ⇒ 更低 lr 只会更接近（或超过）冻结表现。
2. **3e-5 / 1e-4 / 3e-4 各只有 1 个 seed**（1e-6、1e-5 各 3 个）。归档在 1e-4 有 3 seeds
   （0.13/4.12/3.39 %），可见该区间 seed 方差很大；本报告在高 lr 端只作"方向性"结论。
3. **只扫了全量微调的 lr**：LoRA/Adapter 仍用现稿的 lr=1e-4，因此"每种方法各自调参后再比"
   这一更强的公平性要求**尚未满足**（若 PEFT 在 1e-4 上已接近其最优，则不对称性对全量微调不利，
   而不是对 PEFT 有利）。
4. **协议规模**：1 个模型、2000 条 caption、10 epoch、batch 64 fp16，与归档全量微调一致，
   但与现稿正文写的 batch 128 不一致（原因见 §1）。
5. **R@1 带增强抽样噪声**（~1e-2），CG/DG 带 ~1e-4 噪声；zero-shot 是确定性的。
6. **本机 GPU 小时成本**：全部实验约 2 小时串行（含复评），未与其它任务并发。
