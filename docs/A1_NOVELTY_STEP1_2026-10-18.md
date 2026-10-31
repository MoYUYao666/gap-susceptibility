# A1 新颖性升级 · 第 1 步：一阶定律能否"外推预测"（2026-10-18）

> 目的：A1 摘要自认 bias-field 的 `r = 1.000` 是 **自洽、非独立验证**。本步检验：换成**只用聚合量**的闭式分支后，
> 定律能否**跨基准预测** τ(λ)。若能，A1 的新颖性从"经验观察"升级为"可预测定律"；若不能，就把它如实量化为**边界结果**。
>
> 脚本：`tools/_p1205_validate_a1_closed_form.py`、`_p1206_calibrate_a1_closed_form.py`、`_p1207_crossbenchmark_closed_form.py`
> 归档：`outputs/analysis/a1_closed_form_validation.json`、`a1_closed_form_calibration.json`、`a1_crossbenchmark_closed_form.json`

## 1. 两条预测分支的性质（ImageNet-5k，CLIP ViT-B/32）

| 分支 | 误差 MAE | Pearson r | 性质 |
|---|---|---|---|
| **逐图反转条件（exact）** | **0.0013** | 1.0000 | **近乎同义反复**：它反演的正是定义实测 τ 的同一批逐图边距 ⇒ 解释不了"独立验证" |
| **闭式高斯（Gauss）** | **0.1153** | 0.9865 | 形状对、**水平系统性偏低**（τ 平均低 0.115；top-1 平均差 16.3 点） |

- margin–bias 独立性成立（Pearson 0.066，n=50 000 对）⇒ 偏差**不是**独立性假设被破坏，而是"用单一 σ_b 代替真实边距场"。
- 因此尝试**单常数标定**：`σ_b,eff = k·√2·σ_m`，在 ImageNet 上拟合得 **k = 0.550**，
  误差 **0.1153 → 0.0171**（6.7× 降低，max 0.035）。

## 2. 关键检验：把 k 冻结在 0.550，跨四个无关基准预测

各基准用**自身 gap 方向**（`self` 变体，不需要 Flickr30k），冻结 CLIP 前向，无训练。

| 基准 | 图像数 | 类数 | **MAE(k=0.55)** | Pearson r | 该基准最优 k |
|---|---|---|---|---|---|
| rare_species（BioCLIP/IUCN） | 1 000 | 50 | **0.0789** | 0.961 | 0.640 |
| inat_wild（iNaturalist） | 718 | 48 | **0.1021** | 0.933 | 0.360 |
| DTD（纹理） | 1 880 | 47 | **0.1199** | 0.975 | 0.980 |
| Food-101（细粒度食物） | 25 250 | 101 | **0.1043** | 0.986 | 0.940 |

## 3. 结论（如实）

1. **形状可迁移**：r = 0.93–0.99，说明一阶定律的函数形式对无关基准成立；
2. **水平不可迁移**：单常数 k 需随基准在 **0.36–0.98** 间变化 ⇒ **目前还不是可预测定律**，只能算"形状正确的机制模型"；
3. λ=0 处实测与预测同为 τ=1（定义使然，会轻微抬高一致性）；|λ|≥2 时实测 τ 可为负而模型饱和在 0 以上 ⇒
   缺的是**逐对相关性结构**，不是更好的常数；
4. ⇒ **A1 的新颖性不应押在"预测定律"上**；应押在：
   - **(a) 可识别性命题**：top-1 只依赖类相对序，gap 是一阶矩量 ⇒ 非充分统计量（配合构造性反例）；
   - **(b) 本步给出的量化边界**：一阶定律跨基准保形、不保水平，缺的是边距–偏置联合结构 —— 这是有价值的新结果。

## 4. 复跑

```powershell
& 'D:\Anaconda\envs\pytorch\python.exe' tools\_p1207_crossbenchmark_closed_form.py --apply
```

注：torch 在 `D:\Anaconda\envs\pytorch`（系统 python 无 torch）；四基准数据均在本地 `data/`。

---

# 第 2 步（2026-10-18 13:05）：把"匹配 gap"实验写进 A1

> 脚本：`_p1209`（三扰族扫描）、`_p1210`（作图）、`_p1211`（小节插入）
> 归档：`outputs/analysis/a1_matched_gap_families.json`；图：`paper_a1/figures/fig5_matched_gap.{pdf,png}`

## 实验（冻结 CLIP ViT-B/32，5 000 张 ImageNet，1 000 类，各自基准 gap 方向）

| 族 | 参数 | CG | top-1 (%) |
|---|---|---|---|
| — | frozen | 0.855 | 59.1 |
| 平移 | λ=0.25 / 0.5 / 1 / 2 / 4 | 0.651 / **0.426** / 0.045 / **0.398** / 0.613 | 55.6 / 46.8 / 33.6 / **14.1** / 3.5 |
| 类收缩 | a=0.1 / 0.25 / 0.5 | 0.865 / 0.878 / 0.897 | 63.3 / 69.2 / **78.1** |
| 噪声 | σ=0.05 / 0.2（3 seeds）| 0.855 / 0.849 | 58.9 / 57.9 |

**关键结果**：
- **匹配 gap（ΔCG=0.028）：top-1 差 32.7 点**（λ=0.5 的 46.8% vs λ=2 的 14.1%）；
- 放宽到 ΔCG≤0.05：**差 52.1 点**（λ=0.25 的 55.6% vs λ=4 的 3.5%）；
- **方向可反转**：类收缩在 gap **更大**（0.855→0.897）时准确率**更高**（59.1%→78.1%）；
- 噪声族为对照：两个量都不动。

## 写入稿件

- 新增小节 **5.2 “A matched-gap control: the same gap can hide 33 accuracy points”**（`\label{sec:matchedgap}`），
  含图 `fig:matchedgap`（Figure 2）与表 `tab:matchedgap`（Table 1）；
- 摘要新增一句：*"The gap is not even a sufficient statistic for the accuracy it is often used to monitor: two
  configurations whose centroid gaps agree to 0.03 can differ by 33 accuracy points, and at 0.05 by 52."*
- 编译：**44 页**（原 42），**0 错误 / 0 未定义 / 0 Overfull**；图注与表注措辞已修正（图例移出数据区）。

## 为什么这一步对"新颖性"有效

AE 的拒稿理由是"technical novelty marginal"。本步把 A1 的核心命题从**经验观察**改成**可构造检验的非充分性陈述**，
并给出一个**尖锐、可复现、与控制实验并列**的量化反例（同 gap 差 33/52 点 + 反向族 + 对照族）。
这不是加篇幅，而是把"gap 不是通用指标"升级为"gap 非充分统计量，且我们给出构造证明"。

---

# 第 3 步（2026-10-18 13:25）：控制实验、跨模型复现、边界小节、形式命题

> 脚本 `_p1213`（随机方向）、`_p1214`（跨模型）、`_p1215`（入稿）
> 归档 `outputs/analysis/a1_random_direction_gap.json`、`a1_matched_gap_crossmodel.json`

## 1. 随机方向控制（诚实负结果）

200 个随机单位方向，各自平移以把 CG 恢复到 frozen 值（CG 匹配到 0.858±0.003，最大偏差 0.013）：
**top-1 仅 57.0–59.5%（跨度 2.5 点，mean 58.7，frozen 59.1）**；τ 跨度 0.70–0.90，与 top-1 相关 r=0.60。

⇒ **匹配 gap 的 33/52 点塌缩不是普遍现象**，只发生在**相干方向**平移（正是微调轨迹的方向）；随机扰动保 gap 时也保准确率。
这条已如实写入正文，既避免过度声称，也预先挡掉"你挑了 λ"的质疑。

## 2. 跨模型复现（OpenCLIP）

| 量 | CLIP ViT-B/32 | OpenCLIP laion2B |
|---|---|---|
| frozen CG / top-1 | 0.855 / 59.1% | 0.791 / 62.4% |
| 类收缩 a=0.5：CG / top-1 | 0.897 / 78.1%（**+19.0**）| 1.187 / 81.8%（**+19.4**）|
| 回程分支 | λ=0.5 CG 0.426/46.8 vs λ=2 CG 0.398/14.1（ΔCG 0.028 → **32.7 点**）| λ=0.5 CG 0.394/55.6 vs λ=2 CG 0.328/28.5（ΔCG 0.066 → **27.1 点**）|

**方向反转在两模型上一致（+19.0 vs +19.4）**；回程分支的反例在 OpenCLIP 上也存在（27.1 点），只是 ΔCG 略大。
**SigLIP 不采用**：本 harness 上 zero-shot 基线仅 1.86%，明显是文本塔路径损坏，不能作为科学结果。

## 3. 写入 A1 的三块新内容

1. **形式命题**（Setup 之前）：top-1 只依赖相似度的行内序；CG 是这些序的函数之外的量；|ΔCG|≤0.03 可对应 >30 点准确率差
   ⇒ 任何 CG 阈值都不可能是零样本分类的充分健康判据。并注明反例只对相干变换成立（随机方向仅 2.5 点）。
2. **随机方向控制 + 跨模型复现**（并入 5.2 节，在 Figure 2 之前）。
3. **新小节 "The first-order law keeps shape but not level across benchmarks"**（`sec:boundary`）：exact 分支 MAE 0.0013（自洽）、
   闭式 0.115、单常数 0.017 后跨四基准 MAE 0.079–0.120、最优常数 0.36–0.98 ⇒ 保形不保水平，缺的是 margin–bias **联合**结构。

## 4. 编译

A1：**45 页**（42 → 44 → 45），**0 错误 / 0 未定义 / 0 Overfull**。

---

# 第 4 步（2026-10-18 13:40）：修好 SigLIP，跨模型复现补齐到三个骨干

**根因**：SigLIP 的文本塔必须按训练时的 `max_length=64` 做 padding。用默认 `padding=True`（按最长样本）时，
pooled 输出不是训练时的那个位置 ⇒ zero-shot 基线塌到 **1.86%**（500 图探针甚至 0%）；改成
`padding="max_length", truncation=True, max_length=64` 后基线恢复 **72.8%/73.3%**。

**三骨干结果（ImageNet-5k，1000 类，冻结模型）**：

| 模型 | frozen CG / top-1 | 类收缩 a=0.5：CG / top-1 | 变化 | 回程反例（λ=0.5 vs λ=2）|
|---|---|---|---|---|
| CLIP ViT-B/32 | 0.855 / 59.1% | 0.897 / 78.1% | **+19.0** | ΔCG 0.028 → 32.7 点 |
| OpenCLIP laion2B | 0.791 / 62.4% | 1.187 / 81.8% | **+19.4** | ΔCG 0.066 → 27.1 点 |
| SigLIP base-p16-224 | 1.116 / 73.3% | 1.168 / 88.3% | **+15.0** | ΔCG 0.197 → 27.1 点 |

**结论（已写入正文 5.2 节）**：类收缩的"**gap 更大、准确率更高**"方向反转在**三个架构上都复现**（+19.0/+19.4/+15.0）；
回程分支的塌缩也在三者上出现，但 SigLIP/OpenCLIP 需要更大的 ΔCG 才显现（都是 27.1 点，ΔCG 0.197 vs 0.066）。

**⚠️ 为后续复用记录**：SigLIP 文本塔必须 `padding="max_length", max_length=64`；否则 zero-shot 基线会假性塌陷。

---

# 第 5 步（2026-10-18 13:55）：框架补齐（摘要 / 命题位置 / 第四条发现）

此前正文是增量叠加的：摘要第一句与"Only the second"失去干净指代；引言仍写"三个受控实验、三条发现"，而实际已有第四条证据线。

## 改动

| 位置 | 改动 |
|---|---|
| 摘要 | **整段重写**（约 285 词）：先给"**非充分统计量**"结论与构造（33/52 点、200 方向控制 2.5 点），再给三骨干方向反转（+19.0/+19.4/+15.0）、gap surgery 塌缩、类对齐、任务敏感谱，最后以**一阶定律的量化边界**（保形 r=0.93–0.99、常数 0.36–0.98）收尾 |
| 引言 | "three controlled experiments" → **"four"**；新增**第 (iv) 条发现**：非充分性是结构性的（命题 + 匹配 gap 控制 + 三模型复现 + 相干性控制），并明确一阶场是"有边界的机制"而非预测律 |
| 命题位置 | 从 `\input{related_work}` 之后移到**之前**（引言三条发现之后、相关工作之前），逻辑顺序正确 |

## 核验（`tools/_p1222_verify_a1_framing.py`）

```
abstract words (approx): 285
OK proposition occurrences = 1 ｜ OK abstract 'sufficient' = 1 ｜ OK finding (iv) = 1
OK proposition order: 7744 < related_work 8567 < Setup 8592
pages: 45 ｜ pdf: 'sufficient statistic' / 'four controlled experiments' / '0.36' / '0.98' 均在
```

A1 编译 **45 页**、**0 错误 / 0 未定义 / 0 Overfull**。

## 待办（选刊时处理）

摘要 285 词，多数 Elsevier 刊无硬限，但若新刊要求 ≤250 词需压缩；重排格式时按目标刊要求调整。

---

## 第 6 步（2026-10-18 17:45）：六项新颖性增强全部落地

操作者指示"1-6 都做"。A1 从 **45 页**增至 **48 页**，编译 **0 错误 / 0 未定义 / 0 Overfull**，审计 `a1_paa`
**READY / grade A（pass=61 fail=0 warn=0）**。

| 项 | 内容 | 归档/证据 |
|---|---|---|
| **1** | **Proposition 1（非充分性）**：`top1` 只依赖相似度矩阵的行序；对文本侧做公共平移 $t_c\mapsto t_c+v$ 保持全部行序（故 top-1、top-$k$、$\tau$ 全不变），而 $\mathrm{CG}=\|\bar t+v-\bar x\|$ 可取任意 $g\ge0$。附完整证明 | `main.tex` §3.1 `sec:theory` |
| **1b** | **Corollary 1（族条件信息性）**：保序族上 top-1 为常数而 CG 在区间内变动 ⇒ 阈值不可跨族迁移 | 同上 |
| **2** | **Proposition 2**：$|a(S)-a(S')|\le n^{-1}\sum_i\mathbb{1}[\arg\max\text{ 改变}]$，且 CG 差为零时该质量可最大 ⇒ 不存在 $h(0)=0$ 的界 | 同上 |
| **3** | **无标签监控协议**：六种选择规则在 10 条轨迹上评测；$\tau$-max **59.44**（相对 oracle 59.49 的 regret **0.05**、最差 0.46）、CUSUM **59.35**（0.14，LOO 标定 $h=6.0$）、patience-2 58.80（0.69）、训到末轮 57.14（2.35）；并诚实报告"首轮即最优、平凡规则并列"的限制 | `outputs/analysis/a1_monitor_protocol.json`（`_p1255`）|
| **4** | **四控制即伪证协议表**：匹配 gap / 200 随机方向 / 类收缩 / 基准扫描，各列"所伪证的假设"与实测结果 | `main.tex` §5 `tab:controls` |
| **5** | **第二数据集复现**：同一协议在 **DTD**（47 类，冻结 CG 1.019 / top-1 41.62%）与 **Food-101**（101 类，0.953 / 80.64%）上重现分离；$|\Delta\mathrm{CG}|\le0.03$ 时最大 top-1 差 **10.1 / 12.1** 点，$\le0.05$ 时 **15.1 / 42.1** 点（Food-101 的 42.1 点发生在**同一 T 族内**，$\Delta\mathrm{CG}=0.034$）；类收缩反向 +17.8 / +18.2 点而 gap 同步增大 | `outputs/analysis/a1_matched_gap_second_dataset.json`（`_p1254`）|
| **6** | **姊妹文关系段**：说明与"梯度流动力学"那条线互补、不重叠、结论不依赖之 | `main.tex` Discussion |

**数字溯源**：32.7（`a1_matched_gap_families.json::max_matched_gap_spread_tol003.spread = 32.68`）、52.1、27.1@0.066/@0.197、
2.5 点与 $r=0.60$（`a1_random_direction_gap.json::summary`）、+19.0/+19.4/+15.0（`a1_matched_gap_crossmodel.json`）；
第二数据集数字见 `a1_matched_gap_second_dataset.json`。控制表初稿曾误写 33.1（归档为 32.68），由 `_p1259` 修正。

---

## 第 7 步（2026-10-18 18:15）：第 1–7 项全部落地，A1 **51 页**

| 项 | 落地内容 | 归档 |
|---|---|---|
| **1** | **提示词模板控制**：固定 5,000 张 ImageNet-5k 图像，只换 10 个模板。CG 变动 **0.025–0.094**（最大 OpenCLIP），而 top-1 变动仅 **2.3–4.9 点**。旗舰匹配对里 **0.028** 的 gap 差伴随 **32.7 点**精度崩塌 ⇒ 一次 prompt 选择把 gap 推走 **3.4 倍**，精度却几乎不动 | `a1_prompt_template_gap.json`（5 骨干）|
| **2** | **阈值不可迁移**：各设置**冻结** gap 跨 **0.791–1.116（×1.41）**；SigLIP 冻结 gap 最大（1.116）却精度最高（73.3%）；20 次跨设置迁移的 balanced accuracy **中位 0.458**、**10/20 低于随机**、最差 **0.188** | `a1_threshold_transfer.json` |
| **3** | **Proposition 3（文本侧混杂 / 可识别性）**：文本侧变动（prompt/类名）只动 gap、不动行序 ⇒ 不报告 prompt 词表时 gap 不可归因到图像侧；附证明 | `main.tex` §3.1 |
| **4** | **τ 的 k 依赖**：每个模板同时归档 τ@5 与 τ@10（τ@10 系统性略高，见归档）| `a1_prompt_template_gap.json` |
| **5** | **再加两个基准**：iNaturalist-wild（50 物种，spread **2.6**、收缩 **+3.2**）、rare-species（398 类，spread **21.0**、收缩 **+9.9**）| `a1_more_benchmarks.json` |
| **6** | **bootstrap 区间**（500 次图像重采样）：旗舰 spread **32.7 [31.3, 33.9]**；收缩 **+19.0 [17.8, 20.2]**；新基准区间全部排除 0 | 同上 |
| **7** | **最低报告标准**（5 项清单表）：gap+序统计量、prompt/词表、匹配 gap 对照、校准设置、逐次记录 | `main.tex` Discussion `tab:standard` |

**骨干扩展**：新下载 **CLIP ViT-L/14**（ModelScope，`models/clip-vit-large-patch14`）。
实测：`hf-mirror.com` 与 `huggingface.co` 本机**超时不可达**（0 B/s），ModelScope **可达**（~10 MB/s 实测下载）
⇒ 按"以实测为准"走 ModelScope，权重直下数据盘，无本地上传。提示词控制因此覆盖 **5 个骨干**（B/32、B/16、OpenCLIP、SigLIP、L/14）。

**编译与审计**：A1 **51 页**、0 错误 / 0 未定义 / 0 Overfull；`a1_paa` **READY grade A：pass=61 fail=0 warn=0**；
PAA 包已重建（Manuscript 51 页、源码 14 文件）。

---

## 第 8 步（2026-10-18 18:40）：投稿前收尾四项，A1 **52 页**

| 项 | 内容 |
|---|---|
| **揭示函** | companion 表述由"being handled separately"改为 **"under consideration at Neurocomputing (submitted October 2026)"**（Paper A 已于 2026-10-18 投出，状态 Submitted）。注意：包构建脚本 `_p1236` 内置模板会覆盖该文件，模板本身已同步修改 |
| **自动化交接文档** | `AUTOMATION_HANDOVER.md`：Paper A 改为"已投，状态 Submitted，稿号待补"；A1 改为"已改投 PAA（SCIE），包就绪待投"；新增 2026-10-18 18:40 状态块；每周检索 prompt 的 A1 段落同步更新 |
| **Proposition 4（一阶矩统计量均不充分）** | 把非充分性从 centroid gap 推广到任意只依赖两个经验均值的统计量 $F(\bar x,\bar t)$：文本侧平移移动均值、保持行序 ⇒ 除非 $F$ 不依赖 $\bar t$，否则不可能是充分统计量；CG、归一化 gap、角 gap 及其单调变换都是实例 | 
| **附录化** | `tab:protocol`（监控规则）、`tab:morebench`（新基准+区间）、`tab:standard`（报告标准）与 Proposition 3 的证明移入附录；正文因此更短，表格与证明仍在同一 PDF 内 |

**编译**：52 页、**0 错误 / 0 未定义 / 0 Overfull**；包重建（Manuscript 52 页、latex_source 14 文件）；
审计 `a1_paa` **READY grade A：pass=61 fail=0 warn=0**。

---

## 第 9 步（2026-10-18 19:05）：剩余提升项 C/D/E/F 全部落地

| 项 | 结果 | 归档 |
|---|---|---|
| **C τ 的 k 选择** | k=10 与 k=5 对十个模板的排序几乎一致（Spearman **≥0.95**，五骨干），且 k=10 系统性低 **0.040** ⇒ 更便宜的 **k=5 是默认** | `a1_tau_k.json` |
| **D retrieval 侧证据** | 536 图–字幕对（本地 marine_captions，冻结 CLIP）：**ΔCG=0.016** 的两配置（λ=0.5 平移 vs α=0.5 收缩）**R@1 差 61.8 点**（8.96% vs 70.71%）⇒ 分离不限于分类。但 τ 在 retrieval 上**不跟踪 R@1**（r=−0.17，CG 为 −0.23）⇒ 序统计量也有任务范围，必须按目标任务重新验证（已写入正文并如实报告为负结果）| `a1_retrieval_evidence.json` |
| **E 监控不确定性** | 对 10 条轨迹做 bootstrap：τ-max regret **0.05 [0.00, 0.14]**、CUSUM **0.14 [0.00, 0.34]**、训到末轮 **2.35 [1.65, 3.12]**、τ-max 相对末轮优势 **2.30 [1.56, 3.09]** | `a1_monitor_uncertainty.json` |
| **F graphical abstract** | 四面板整页图（匹配 gap / prompt 模板 / 阈值迁移热图 / 监控 regret）：`paper_a1/figures/graphical_abstract.{pdf,png}`，并作为可选上传项 `Graphical Abstract.pdf` 进入 PAA 包 | `paper_a1/figures/`、`SUBMISSION/A1_PatternAnalysisApplications/` |

**A1 终态**：**52 页**（正文 ~47 + 附录）、0 错误 / 0 未定义 / 0 Overfull；PAA 包 6 个文件
（Manuscript 52 页、Title Page、Cover Letter、**Graphical Abstract**、latex_source.zip 14 文件、README）；
审计 `a1_paa` **READY grade A：pass=61 fail=0 warn=0**。

---

## 第 10 步（2026-10-18 19:35）：合规收尾 + 最后两项加料，A1 **53 页**

### 1. A1 claim ledger（**97/97 通过**）——顺手查出两处真错

新建 `tools/_claim_ledger_a1.py`：把 A1 引用的 97 个数字逐条绑定到「脚本 + 归档字段」并断言。首轮 85/87，暴露出两处**真实错误**：

| 错误 | 稿件原值 | 归档实测 | 处理 |
|---|---|---|---|
| DTD 冻结 gap | `1.019` | 1.01845… ⇒ 应为 **1.018**（四舍五入错） | 稿件改 3 处 |
| 逐轮 τ 与 top-1 的平均 Pearson | `0.90` | 0.9331 ⇒ 应为 **0.93** | 摘要 / 引言 / §epoch_sweep 各改 |

修正后 **97/97 全通过**；归档 `outputs/analysis/claim_ledger_a1.json`。

### 2. 数据可用性声明收窄（原先与归档不符）

原句声称"所有逐次记录与脚本均在公开仓库 + Zenodo 快照"——但快照（2026-10-13）**早于本轮全部新实验**。
现改为：快照覆盖**当时已有**的逐次记录与脚本；本轮新增分析（prompt 控制、更多基准与 retrieval 复现、监控评估）
在公开仓库中，**接收后将另立版本化快照**。标题页声明同步加注。

### 3. Proposition 5（正例判据）

给出"**何时可以相信一阶矩统计量**"：记 $arepsilon_i=\max_c|\Delta s_i(c)-ar\Delta_i|$，若某图 top-1 改变，则其 margin
$m_i\le2arepsilon_i$。故一阶矩摘要只有在其能界定 $arepsilon_i$（即干预对类别分数是**类中性**的）时才可用来认证精度。
这把批评变成可操作判据，并与 Prop 1（类中性平移）对接。

### 4. 另两个骨干 + DTD/Food-101 区间

- 匹配 gap 现覆盖 **5 个骨干**：CLIP B/32 **32.7**、**B/16 35.5**、**L/14 39.6** 点（$|\Delta\mathrm{CG}|\le0.03$），
  OpenCLIP/SigLIP 各 **27.1**（需更大 gap 差 0.066/0.197）；控制表同步改为五骨干。
- DTD / Food-101 补 **95% bootstrap 区间**：spread 10.1 [8.1, 12.0] 与 12.1 [10.7, 13.3]；收缩增益 +17.8 [15.9, 19.7] 与
  +18.2 [17.1, 19.4]；附录表补两行，iNat 行由带符号区间改为**绝对值区间**。

### 5. 公开镜像：**已准备、未推送**（按操作者要求等投稿确认）

`tools/_p1284_prepare_public_mirror.py` 把 11 个新归档 + 11 个脚本复制进 `publish_clean/` 并打印复核命令；
**脚本自身不执行 commit/push**。投稿确认后运行它，再手动 commit + `push ssh-origin main`。

**A1 终态**：**53 页**（正文 ~46 + 附录）、0/0/0；PAA 包 6 文件；审计 `a1_paa` **READY grade A：pass=61 fail=0 warn=0**；
三个台账（A1 **97/97**、主 **96/96**、Paper A **76/76**）全通过。

---

## 第 11 步（2026-10-18 20:10）：图放大 + graphical abstract 入正文，A1 **55 页**

**问题**：A1 五张图宽度为 0.55 / 0.62 / 0.55 / **0.45 / 0.48**，后两张（训练轨迹、任务敏感谱）明显偏小；
graphical abstract 此前只是包内独立 PDF，**正文里找不到**。

**处理**：

| 项 | 处理前 | 处理后 |
|---|---|---|
| Fig. 1 `fig1_lambda` | 0.55\textwidth | **0.78**（`__crop` 版） |
| Fig. 2 `fig5_matched_gap` | 0.62 | **0.92** |
| Fig. 3 `fig2_tau_top1` | 0.55 | **0.78** |
| Fig. 4 `fig3_trajectory` | **0.45** | **0.74** |
| Fig. 5 `fig4_spectrum` | **0.48** | **0.78** |
| Graphical abstract | 仅包内独立文件 | **附录 Figure A.6（第 52 页）**，宽度 0.98\textwidth |

- 新增 `paper_a1/figures/*_crop.pdf`（`pdfcrop` 裁掉图内白边），`main.tex` 改用裁剪版；
- graphical abstract 以独立小节 + `figure` 环境置于附录（`Figure A.6`），同时**仍保留**包内独立文件
  `Graphical Abstract.pdf`（门户可选上传项）；
- 编译：**55 页**、0 错误 / 0 未定义 / 0 Overfull；审计 `a1_paa` **READY/A pass=61 fail=0 warn=0**。

---

## 第 12 步（2026-10-18 20:35）：图内字体统一 Times New Roman（长期规则）

**操作者要求**：图里的字必须 Times New Roman，**以后所有生图都照此**。

- **核查**：`pdffonts` 显示 fig1–fig4 本已是 TimesNewRomanPSMT（数学 STIX），但 **fig5_matched_gap 与 graphical_abstract
  用的是 DejaVu Sans**。
- **修复**：`tools/_p1288_fix_figure_fonts.py` 给 `_p1210_figure_matched_gap.py` 与 `_p1276_graphical_abstract.py`
  插入统一样式块（serif + Times New Roman + `mathtext.fontset=stix` + `pdf.fonttype=42`），重生成并重裁边
  （`*_crop.pdf`）。
- **复验**：六张图（含裁边版）`pdffonts` 仅含 **TimesNewRomanPSMT / TimesNewRomanPS-BoldMT / STIXGeneral**，无 DejaVu。
- **规则落盘**：已写入 `AGENTS.md` 与 `CLAUDE.md`（新会话生图前必读）。

A1 编译 **55 页**、0/0/0；三台账 97/97、96/96、76/76 全过；审计 `a1_paa` READY/A。

---

## 第 13 步（2026-10-18 21:00）：字体嵌入类型统一 CID TrueType

字体族已统一 Times New Roman 后，`pdffonts` 进一步暴露：**fig1–fig4 是 Type 3 嵌入**（旧生成脚本只设字体族、
未设 `pdf.fonttype`），出版社排版会拒收。

- 给 `tools/clip_a1_figures.py`（fig1/2/4）与 `tools/clip_a1_fig4.py`（fig3）插入同款样式块
  （`pdf.fonttype=42`），重生成并重裁边（脚本 `_p1290`）。
- 复验六图（`*_crop.pdf`）：**TimesNewRomanPSMT / TimesNewRomanPS-BoldMT / STIXGeneral 全部 CID TrueType**。
- 规则文档（`AGENTS.md`、`CLAUDE.md`）追加"Type 3 不接受"的硬判据。
- A1 重编译 **55 页**、0/0/0；A1/Main/PaperA 三台账 97/97、96/96、76/76 全过；审计 `a1_paa` **READY/A**。

---

## 第 14 步（2026-10-18 21:30）：全页目视渲染检查 + 浮动排版修正，A1 **53 页**

**方法**：把 55 页全部渲染成 72 dpi 图，逐页统计墨迹覆盖率、左右/上下越界、页内最大空白与页尾空白；
再对关键页（标题页、图 2、图 5、附录表页、GA 页、参考文献末页）做 100 dpi 目视抽查。

**发现**：

| 项 | 结果 |
|---|---|
| 空白页 | **0** |
| 内容越界（左右/上边距） | **0** |
| 字体 | 六图均 CID TrueType（TimesNewRoman/STIX），正文 Times |
| **graphical abstract 被挤到独立页** | p51 留白 **331 pt**，图被推到 p52 |
| **`[H]` 强制定位造成页尾空白** | p32 300 pt、p16 261 pt、p29 243 pt、p50 224 pt |

**修正**：
1. 所有 figure/table 的 `[H]` 改为 `[t]`（顶部浮动，让正文回填）；
2. graphical abstract 宽度 0.98 → **0.84**\textwidth，使其与说明段同页；
3. 重扫：**页数 55 → 53**；页尾留白 >250 pt 的仅剩最后一页（参考文献结束，正常）；
4. 目检：图 2（p17）、图 5（p32）、GA（p51）、附录表 A.18/A.19（p49）排版正常，表列不越界、图例可读。

A1 **53 页**、0 错误 / 0 未定义 / 0 Overfull；三台账 97/97、96/96、76/76 全过；审计 `a1_paa` **READY/A**。

---

## 第 15 步（2026-10-18 22:30）：新颖性 (a) 下界 + (b) margin 质量统计量；证据两处加强，A1 **54 页**

### (a) 下界：一阶矩统计量不可能"充分"

新增 **Proposition（一阶矩统计量的下界）**：设 $A$ 为 margin 满足 $m_i\le2cL$ 的正确样本集（$L=\max_c\|t_c-\bar t\|$ 为类散布常数），
则存在**零均值**、范数 $\le c$ 的图像扰动，使 **CG 完全不变**、而 $A$ 中每一行的 top-1 翻转 ⇒ top-1 至少变化 $|A|/n$。
证明用逐行方向 $u_i=(t_{\hat y_i}-t_{y_i})/\|\cdot\|$（$A$ 内推 $+c'u_i$ 越过 margin，$A$ 外反向推且只增大 margin），
并用 $\sum w_i=0$ 保证均值不变。

**量化**：冻结 ImageNet-5k 上 $L=1.013$，margin 低于 $2\varepsilon$ 的比例为 **0.681**（$\varepsilon=0.01$）、**0.875**（$\varepsilon=0.02$）
⇒ 在匹配 gap 族的位移尺度（$\varepsilon\approx0.03$）上，**至少 87.5% 的行可被"藏起来"**，即 gap 可被构造为恒等于零而 top-1 崩塌 87.5 点；
实测家族只实现了其中一部分（稀疏 32.7、加密 50.6–62.0），与下界一致。

### (b) 正例：margin 质量 $M(\varepsilon)$

由 Prop 5（翻转要求 $m_i\le2\varepsilon_i$）直接给出可用统计量：$M(\varepsilon)=n^{-1}\#\{i:m_i\le2\varepsilon\}$。
同一批 19 个配置上：**CG 与 top-1 相关 $r=-0.154$**，而 **$M(0.01)$ 为 $r=-0.996$**、$M(0.02)$ 为 $r=-0.988$。
必须按 margin 尺度取 $\varepsilon$（$\varepsilon\ge0.05$ 时饱和），文中按曲线报告。这把论文从"只否证"变成"否证 + 给出替代量"。

### 证据加强 1：五骨干同容差

加密 λ 网格（19 个 λ × 5 个 α × 4 个 σ），$|\Delta\mathrm{CG}|\le0.03$ 下各骨干最大 spread：
**CLIP B/32 50.6**（$\Delta$CG=0.006）、**B/16 54.4**（0.004）、**OpenCLIP 48.0**（0.029）、**SigLIP 7.7**（0.029；0.05 时 46.0）、**L/14 62.0**（0.009）。
原文稀疏网格的 32.7 是保守值。

### 证据加强 2：真实 checkpoint 匹配对

11 个同时有 CG 与 top-1 的真实微调 checkpoint 中，31 对满足 $|\Delta\mathrm{CG}|\le0.03$；最宽一对
**$\Delta$CG=0.0024 而 top-1 差 6.64 点**（COCO ep1 60.14% vs DTD ep10 53.50%）；同数据集内最宽 $\Delta$CG=0.0013、差 **2.24 点**（DTD seed43/44）。
⇒ 不依赖合成扰动的同向证据。

**归档**：`a1_matched_gap_dense.json`、`a1_real_checkpoint_pairs.json`、`a1_lower_bound_constants.json`、`a1_margin_mass.json`；
**脚本** `_p1299`–`_p1304`。A1 **54 页**、0/0/0；**A1 claim ledger 112/112**；审计 `a1_paa` READY/A。

---

## 第 16 步（2026-10-18 23:30）：最后一轮全面提升 —— 主定理 + 统计量对决 + 稳健性 + 摘要重写，A1 **56 页**

### A. 一条主定理（Theorem 1，特征化）

| 部分 | 内容 | 出处 |
|---|---|---|
| (i) | top-1 只依赖行序；**任何只依赖两嵌入均值的统计量**对文本侧公共平移不变 ⇒ 不可能充分 | Prop 1 + Prop 3 |
| (ii) | 干涉的类内散布 $\le\varepsilon$ 时，仅 $m_i\le2\varepsilon$ 的行可翻转；**可翻转比例 = margin 质量 $M(\varepsilon)$** | Prop 4（margin 条件）|
| (iii) | 下界可达：存在**零均值**扰动使 CG 完全不变、top-1 变化 $M(cL)$ | Prop 5（下界）|

⇒ 一句话结论：**一阶矩只对"类中性"干涉有效；一般情形下的正确证书是 margin 质量，不是矩。**

### B. 统计量对决（Table showdown）

同一冻结模型、同一评测数据、同一批 17 个配置，两个任务域：

| 统计量 | 分类 $r$ | 检索 $r$ |
|---|---|---|
| CG | −0.154 | −0.223 |
| τ₅ | **+0.832** | **−0.143**（失效）|
| $M(0.01)$ | **−0.996** | **−0.970** |
| $M(0.02)$ | −0.988 | −0.921 |

⇒ τ 只在分类有效、检索失效；**margin 质量两域都最强**——正好补上 τ 在 retrieval 负结果的缺口。

### C. 稳健性附录

- **半样本**：2,500 图两半的匹配 gap spread = **32.7 / 32.6**（全样本 32.7）；
- **真实配对显著性**：6.64 点、SE 0.99、95% CI **[4.70, 8.58]**、$z=6.7$；
- **τ 的模板依赖**：跨 10 模板最低 0.54，而精度变化 <5 点；
- **margin 质量的尺度依赖**：$\varepsilon\ge0.05$ 饱和，按曲线报告。

### D. 摘要/引言重写（摘要 **243 词**，上限 250）

摘要从"τ 跟踪精度"改为"**证明 gap 何时不可能成为指标，并给出可用证书**"；引言把"three model families"改为**五骨干**，
并把主定理与对决表前置。台账同步更新（**127/127**）。

### E. 减长（**决定不做**）

总页数 56（含附录），PAA 无页数上限；把两张表再移入附录不改变总页数、只增加维护风险，故按计划"视页数决定"不做。

---

## 第 17 步（2026-10-19 00:20）：四项强化落地，A1 **58 页**，台账 **139/139**

| 项 | 内容 | 归档 |
|---|---|---|
| **1. 相关差异显著性（Williams 检验）** | 两统计量与同一精度向量相关 ⇒ 依赖样本；分类：CG vs $M(0.01)$ $t=7.2$（$p=4.7\times10^{-6}$）、$\tau$ vs $M$ $t=14.7$（$p=6.6\times10^{-10}$）；检索：$t=6.1$（$2.6\times10^{-5}$）、$t=7.5$（$2.8\times10^{-6}$）。CG vs $\tau$ 在分类显著（$t=-5.5$，$p=7.2\times10^{-5}$），**在检索不显著（$t=-0.3$，$p=0.75$）**——与两者在检索上都弱一致 | `a1_williams_tests.json` |
| **2. Theorem 1 的假设说明** | 明确三点：精确陈述用未归一化算式（归一化下平移只差二阶项，故实测族确实会改变精度）；零均值构造要求至少一个 $A$ 外行与足够维度（$A$ 为全集时改用逐行幅度）；$L$ 由模型自身文本嵌入**实测**（CLIP B/32：$L=1.013$），非假设 | 正文 Remark |
| **3. retrieval 版下界** | 新 Proposition：配对 margin $m_i=s_i(i)-\max_{j\ne i}s_i(j)$、配对质量 $M_R(\varepsilon)$；同一构造使 CG 不变而 R@1 变化 $M_R(cL)$。536 对冻结集上 $M_R(0.01)=0.578$、$M_R(0.02)=0.723$，与 R@1 相关 $-0.970$ | 正文 §retrieval |
| **4. $M(\varepsilon)$ 作为选择规则** | 合成 17 配置：按 **min $M(0.01)$ 选择 = 精确命中 oracle（regret 0）**，而按 min CG 选择亏 **44.4 点**；10 模板 × 5 骨干：候选间精度差 ≤2 点，min-M 与默认模板 regret 都在 1.7 点内（CLIP B/32：1.7 vs 1.0），骨干内 Spearman($M$,top-1) −0.58…−0.94 | `a1_selection_rule.json` |

**顺带修复**：p 值曾被格式化成 "0.0"（一位小数），已改为科学计数法；A1 台账的比较改为**容差式**（避免 2.6e-05 这类浮点在
小数舍入下误判），并新增 20 条断言 → **139/139**。

A1 **58 页**、0/0/0；三台账 139/139、96/96、76/76；审计 `a1_paa` READY/A。

---

## 第 18 步（2026-10-19 01:30）：真实微调 campaign + margin 质量逐 epoch 监控器，A1 **58 页**，台账 **157/157**

### 实验

`tools/_p1319_realfinetune_campaign.py`：CLIP ViT-B/32 + LoRA，**18 个真实微调 run**（3 个本地分类数据集 × 2 个干预变体
〔仅文本塔 / 两塔〕× 3 个种子 × 4 epoch），每个 epoch 在**固定 5,000 图 ImageNet-5k holdout** 上评迁移，记录
top-1、CG、$M(0.01)$、$M(0.02)$、$\tau_5$。

**结果**：72 个真实 checkpoint，CG 跨 0.464–0.768、top-1 跨 5.68–57.36%。

### 证据 1：真实微调的匹配对（不再是合成）

- $|\Delta\mathrm{CG}|\le0.03$ 的匹配对 **670 对**（$\le0.01$ 有 254 对）；
- 最宽跨 run 对：**48.5 点 @ $\Delta$CG=0.0242**（DTD/both ep3 8.9% vs Food-101/text ep1 57.4%），
  paired bootstrap 95% CI 绝对值 **[47.0, 50.0]**；
- 最宽**同 run 内**对：**19.6 点 @ $\Delta$CG=0.0125**（同数据、同种子、仅 epoch 不同），CI **[18.4, 20.9]**；
- ⇒ 真实微调的 dissociation 不小于合成（稀疏 32.7），与加密扫描（50.6）同量级。

### 证据 2：margin 质量作逐 epoch 监控器

跨 72 个 checkpoint：CG 相关 **+0.577**（符号与合成族相反！）、$\tau_5$ **+0.987**、$M(0.01)$ **−0.987**、$M(0.02)$ −0.908。

逐 run 选 epoch（18 个 run，oracle 均值 47.8%）：**min $M(0.01)$ regret 0.06 点**、$\tau$ regret 0.0、
min-CG regret **5.65**、训到最后一轮 regret **13.8**（最差 29.4）。

⇒ 证书不仅能诊断，**可以直接当早停/选型规则**；同时 CG 在两个真实族间**变号**，再次说明它不能当指标。

### 入稿

- §realpairs 增 campaign 段 + `tab:campaign`（跨 run/同 run 两组极端匹配对 + CI）；
- 对决表 `tab:showdown` 增"real fine-tuning"列，并补 CG 变号的警示句；
- 原"轨迹不可比"段替换为 campaign 逐 epoch 监控结果；
- 选择表 `tab:selection` 增 18 个真实 run 的 epoch 选择行；
- 摘要中"6.6 点真实配对"改为"72 个真实 LoRA checkpoint、最宽 48.5 点 @ 0.024"（摘要 **249 词**，≤250）。

A1 **58 页**、0/0/0；三台账 **157/157、96/96、76/76**；审计 `a1_paa` READY/A。
