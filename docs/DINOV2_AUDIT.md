# DINOv2 异质组合实验 —— 独立审计报告

- **审计对象**：`tools/_p293_dinov2_hetero_strict.py` 及其产物 `outputs/analysis/dinov2_hetero/**`
  （DINOv2-base 视觉塔 + CLIP ViT-B/32 文本塔 + 拟合头，严格冻结三臂实验，用于回应 PR 审稿人 R2.3）
- **审计人**：dinov2-auditor（独立成员，非该实验作者）
- **日期**：2026-10-12
- **审计时状态**：`text_only/seed42` 已完成并归档；`both/seed42` 正在训练；`vision_only/seed42` 未开始
- **纪律**：本文每个数字都注明 (a) 产出脚本/命令 (b) 归档文件+字段。凡我未能查清的一律写"**未定**"。

---

## 0. 核心结论（摘要）

1. **给出审计前提的那条判断，我不同意，并且有硬证据反驳**：论文 `tab:position_strict` 里**并非**"所有 ΔCG 都在 ±0.10 内"——同一张表已有 **BioCLIP B/16** 行
   ΔCG = text_only **−0.3671** / both **−0.4515** / vision_only **−0.2927**（3 seeds，r=4）。
   因此 **−0.3913 与论文自己的表同量级（1.07×）**，"量级本身反常/否证论文"的写法**不能成立**。
   （来源：`outputs/strict_freeze_bioclip/results_partial.json::summary.r4_*`；表内文字 `paper合/sections/empirical.tex:85`）
2. **那个"−0.39 可能来自归一化错配"的怀疑，我用对照实验排除了**：同一冻结权重下把 DINOv2 换成它自己的 ImageNet 统计量（含官方 256→crop224 几何），frozen CG 只从 0.6769 变到 0.6785（+0.24%），成对 ΔCG 从 −0.3915 变到 −0.3892（≤0.0025）。**归档的 −0.3913 可被独立复现到 0.0002~0.0004**。（`tools/_p357_dinov2_norm_probe.py` → `norm_probe/results.json`）
   ⇒ 这个实验的**数字本身是可靠的**；它的问题不在"算错了"，而在"**不可与论文并列**"。
3. **这个实验目前还不能支撑任何"适配位置排序"结论**：三臂只完成 1 臂、1 seed、1 次评测抽样；
   且它与论文各行**不可比项有 4 条**（异质配对、视觉塔归一化错配、**损失温度差 7 倍**、初始检索对齐差约 2 倍）。
   它能支撑的最强命题是"**在论文自己的 BioCLIP 那一类（初始对齐差的非原生配对）里，再添一个同量级实例**"。
4. **顺带查出 4 个独立于本次实验本身的问题**（前三个影响全项目、含论文）：
   - **评测画廊继承 train transform**（随机翻转+颜色抖动）→ 本项目每个 CG/DG/R@1 都是随机抽样。**已量化**：**ΔCG 的抽样 sd 仅 0.0003~0.0007**（噪声只占论文 ΔCG 臂间间隔的 1.5%~3%，**不影响 ΔCG 排序**），但 **R@1 的抽样 sd 达 0.0045~0.0078、极差 0.014~0.025**。见 §3.3/§3.5。
   - **单 run R@1 复现不出（最重要的一条）**：用**论文自己的 loader + 自己的指标函数**、加载归档 checkpoint 重复评测，`vision_only/seed42` 只能得到 **0.679±0.003**，而归档记的是 **0.7000**；同一 checkpoint 的 epoch-9 权重也记 0.694 而我测 0.679。⇒ 归档里"每个 seed 的 R@1"是单次随机抽样，**run 级偏移可达 ~0.02**；这正与 R1.1/R3.1"数字对不上"同量级。**成因未定**（不是 seed、不是权重、不是指标代码）。见 §3.6。
   - **损失温度不一致**：本地 CLIP 权重的 `logit_scale = ln(100)`（τ=0.01，已用**全文件 SHA256** 证实与上游 HF 缓存逐字节相同），而 DINOv2 脚本硬编码 `ln(1/0.07)`（τ=0.07）并自称"CLIP 的值"——**错**。见 §2.7。
   - `tools/_p293_dinov2_hetero_strict.py` 未提交改动里曾把**已训好的 LoRA 清零**导致新字段恒为 0.0（Lead 已修，我已复核修复；见 §2.5）。

---

## 1. 事实基础（我这一轮亲自核实的一手事实）

| # | 事实 | 证据（脚本 / 文件 / 字段 / 命令） |
|---|---|---|
| F1 | `text_only/seed42`：CG 0.67676→0.28550，DG 0.75090→0.30465，ΔCG=−0.3912654，ΔDG=−0.4462488，R@1=0.3540 | `outputs/analysis/dinov2_hetero/fitted/text_only/seed42/results.json` :: `CG_initial/CG_final/delta_CG/delta_DG/R@1` |
| F2 | 同 run 的 CG 逐 epoch 单调下降、无跳变 | 同上目录 `gap_history.json::centroid_gap` = 0.6768→0.4778→0.4147→0.3677→0.3349→0.3129→0.3049→0.2914→0.2891→0.2859→0.2855 |
| F3 | frozen 基线（同头、同画廊定义）：CG 0.67688、DG 0.75099、R@1 0.28900 | `outputs/analysis/dinov2_hetero/fitted/frozen/results.json` |
| F4 | 头 = 768→512→512 两层 MLP，**656,384** 参数，在 train captions [5000,10000) 上拟合 10 epoch（AdamW lr 1e-4），拟合后 val R@1 = **0.2820**，耗时 3440.8 s | `outputs/analysis/dinov2_hetero/heads/fitted.pt::meta.{n_head_params,tuning_split,val_R@1_after_fitting,fit_seconds}`；`logs/head_fit.log:49` |
| F5 | 头的拟合用的是 **train split 的增强变换**（翻转+抖动） | `tools/_p293_dinov2_hetero_strict.py:216-217`（`split="train"`）；`src/dataset.py:75` |
| F6 | DINOv2 `text_only` 臂的 checkpoint 是**第 10 epoch** 的模型：`epoch=10`、24 层 LoRA，且该臂的 `last_checkpoint.pt` 与 `best_checkpoint.pt` **逐位相同**（该 run 的 val loss 最后一次改善就发生在 epoch 10）。**注意**：三个 CLIP 臂不是这样——它们的 `best` 是 **epoch 9**（val loss 最小）、`last` 是 epoch 10，两者权重不同 | `tools/_p357a_ckpt_probe.py` → `norm_probe/ckpt_probe.json::last_equals_best=true`；`tools/_p368_checkpoint_epochs.py` → `checkpoint_epochs.json::clip_strict_freeze.*.best_checkpoint.pt.epoch=9` |
| F7 | 被杀的 `text_only/seed123` 只跑到 **epoch 3**（train_losses 仅 3 项）→ **不是可用的第二个 seed**，其 checkpoint 不能当 n=2 用 | `outputs/analysis/dinov2_hetero/fitted/text_only/seed123/best_checkpoint.pt::epoch=3`（`_p357a`）；日志 `logs/fitted_text_only_seed123.log` 尾部为 `Epoch 4: 62%` |
| F8 | 严格冻结的不变量成立：`n_trainable=196,608`，`n_trainable_vision_side=0`，闭式校验通过 | `results.json::n_trainable_params/n_trainable_vision_side`；`tools/_p293_dinov2_hetero_strict.py:356-365`（assert） |
| F9 | 视觉塔输入用 **CLIP** mean/std，不是 DINOv2 的 ImageNet 统计量 | `src/dataset.py:19-20,23-38`（唯一 transform 入口）；`models/dinov2-base/preprocessor_config.json::{image_mean,image_std}`；实验自己也记了这个字段 `results.json::image_normalisation` |
| F10 | DINOv2 的**几何** 224 并不越界：官方 preprocessor 就是 shortest_edge 256 → center crop 224 | `models/dinov2-base/preprocessor_config.json::{size,crop_size,do_center_crop,resample}` |
| F11 | **评测画廊用的是 train 变换**：`create_dataloaders` 对 `split="train"` 的 dataset 对象做 `random_split`，val/test 是它的 `Subset` → 继承翻转+抖动。实测同一 index 连读两次 `max|Δ|` = **0.1501**（rev-2 归档值；rev-1 曾测得 0.2851，两次是同一定义下的不同随机抽法，量级一致且均 ≫0） | 我的 `tools/_p357_dinov2_norm_probe.py`（rev-2）→ `norm_probe/results.json::protocol_facts.same_index_two_reads_max_abs_diff=0.1501`、`same_index_two_reads_differ=true`；rev-1 的 0.2851 见 `logs/p357_norm_probe.log`；独立复现（另一成员）`outputs/analysis/transform_chain.json::val_chain_has_train_transform=true, max_abs_diff_overall=3.827` |
| F12 | 论文严格冻结对照的 frozen 参考**没有记 CG/DG/R@1** | `outputs/strict_freeze/frozen/results.json` 仅 6 个键（`effective_rank_final`、`backbone_delta` 等）；`experiments/strict_freeze_control.py:312-339`；我读出的键列表见 `outputs/analysis/dinov2_hetero/protocol_facts.json::facts.paper_frozen_reference` |
| F13 | 论文 CLIP B/32 严格冻结三臂（5 seeds）：ΔCG −0.0465±0.0030 / −0.0258±0.0035 / +0.0106±0.0044；R@1 0.6238/0.6932/0.6800；初始 CG ≈ **0.8183** | `outputs/strict_freeze/{text_only,both,vision_only}/seed*/results.json`；汇总 `outputs/analysis/dinov2_hetero/clip_baseline_check.json::rows`；单 run 初始 CG 见 `outputs/strict_freeze/text_only/seed42/results.json::initial_gap.centroid_gap=0.81833` |
| F14 | BioCLIP B/16 严格冻结（3 seeds，r=4）：ΔCG −0.3671±0.0104 / −0.4515±0.0149 / −0.2927±0.0022，初始 CG ≈1.79 | `outputs/strict_freeze_bioclip/results_partial.json::summary.r4_*` 与 `records[]` |
| F15 | LoRA 更新量（与论文同公式 √Σ‖s·A@B‖²）：CLIP B/32 text 侧 **5.4416**；DINOv2 异质 text 侧 **8.3371**（1.53×）。CLIP both: vis 6.2320/text 4.3484；vision_only: vis 6.9014 | 我写的 `tools/_p365_lora_update_norms.py` → `outputs/analysis/dinov2_hetero/lora_update_norms.json`；CLIP 侧原值出自 `experiments/strict_freeze_control.py:210-217` 写下的 `outputs/strict_freeze/*/seed42/results.json::lora_update_norm` |
| F16 | **损失温度不一致**：本地 `models/clip-vit-base-patch32/pytorch_model.bin::logit_scale = 4.605170` = ln(100)（τ=0.01），且与 HF 缓存 `models--openai--clip-vit-base-patch32` 的 snapshot **全文件 SHA256 相同**（`A6308213…576F`，大小同为 605,247,071 字节）；DINOv2 脚本硬编码 2.659260 = ln(1/0.07)（τ=0.07） | `tools/_p363_logit_scale_provenance.py`、`tools/_p364_pristine_clip_provenance.py` → `outputs/analysis/dinov2_hetero/{logit_scale_provenance.json,pristine_clip_provenance.json}`；脚本常量 `tools/_p293_dinov2_hetero_strict.py:107-108` |
| F17 | 实验脚本与归档 JSON **不同版本**：seed42 的 `results.json` 没有 `lora_update_norm_frobenius/backbone_delta_note` 字段，而工作区脚本会写这两个字段 | `git diff HEAD -- tools/_p293_dinov2_hetero_strict.py`（新增 23 行）；`results.json` 字段清单 |
| F18 | 三臂参数预算与论文 CLIP 同臂**完全相同**（text 196,608 / vision 294,912 / both 491,520） | 我的 `tools/_p361_protocol_facts.py` → `protocol_facts.json::facts.trainable_params_*` |
| F19 | **评测抽样噪声实测**（CLIP B/32 seed42，各 12 次新抽样）：ΔCG 均值±sd = −0.0445±0.0007 / −0.0253±0.0005 / +0.0110±0.0005（与归档 −0.0443/−0.0253/+0.0108 一致到 0.0003）；R@1_final = 0.6204±0.0078 / 0.6949±0.0055 / 0.6782±0.0061 | `tools/_p360_gallery_noise.py` + `tools/_p366_gallery_noise_fix.py` → `outputs/analysis/dinov2_hetero/gallery_noise/results_corrected.json` |
| F20 | 用**论文自身 loader + 指标函数**复评归档 checkpoint：text_only 0.6198、both 0.6925、**vision_only 0.6790**（归档分别为 0.6180/0.6890/**0.7000**） | `tools/_p369_reproduce_clip_arm_r1.py` → `paper_path_r1.json` |
| F21 | `vision_only/seed42` 的 `best_checkpoint.pt` 是 **epoch 9**（val loss 最小 0.3997）、`last_checkpoint.pt` 是 **epoch 10**，二者权重不同；两套权重各自新抽样都为 ≈0.679，而归档该 epoch 记 0.694/0.700 | `tools/_p370_vision_only_checkpoint_identity.py` → `vision_only_ckpt_identity.json` |
| F22 | 论文 strict-freeze 各 run 的 `R@1_i2t ≠ R@1_t2i`（30 格里仅 1 格相等）⇒ DINOv2 归档里 `R@1_i2t == R@1_t2i == 0.3540` 逐位相同属**巧合**，非结构性 | 归档遍历（`outputs/strict_freeze*/**/results.json::final_task_metrics`） |
| F23 | 温度确实进入训练：`src/trainer.py:419` `logit_scale = self.model.logit_scale.exp()` 参与 InfoNCE logits | `src/trainer.py:419-428` |

---

## 2. 逐项判定表（A.1–C.6）

判定用语：**成立** / **不成立** / **部分成立** / **未定**（并给出原因）。

### A.1 图像归一化错配（视觉塔收到分布外输入）

| 项 | 内容 |
|---|---|
| 事实 | F9 + F10：**几何 224 不越界**（是 DINOv2 官方配置），**但均值/方差是 CLIP 的**，DINOv2 要的是 ImageNet 统计量。所以"分布外"只在 mean/std 这一维成立。 |
| 对照实验 | `tools/_p357_dinov2_norm_probe.py`（CPU，只测不训）：同一冻结权重（DINOv2+CLIP 文本+归档头）跑 4 条图像流水线：`clip_clean`（CLIP 统计量，确定画廊）/`imagenet_clean`（仅换 ImageNet 统计量）/`dinov2_native`（shortest-edge 256→center-crop 224 + ImageNet 统计量，即官方预处理）/`clip_aug_r*`（协议实际用的增强流水线）。 |
| 结果 | 见 **§3.1**（表 T1）。 |
| 判定 | **A.1 不成立（不足以解释 −0.39）**：错配客观存在且被实验自己记录，但**实测影响可忽略**——CG 只变 +0.0016（+0.24%），ΔCG 只变 ≤0.0025（= 效应量的 0.6%），R@1 的变化落在抽样波动内。见 §3.1/§3.2。**注意**：即使如此，"归档头是在 CLIP 统计量的特征上拟合的"这一点仍然成立，因此要断言"在正确统计量下**重新拟合头**后结论不变"仍需 GPU 训练（本轮**未做**，标 **未定**）；但"归一化错配吃掉了 −0.39 的相当部分"这一具体假设已被排除。 |

### A.2 拟合头的作用

| 项 | 内容 |
|---|---|
| 事实 | F4：头是用 **656,384** 个可训练参数在不相交切分上以 InfoNCE 拟合的（比任何一臂的 LoRA 都大：196,608~491,520）。F8 决定头在训练/评测全程冻结且各臂完全相同（`backbone_delta.head.nonzero_tensors=0`）。 |
| 头拟合时的水平 | F4：拟合结束时 val R@1 = **0.2820**；frozen 归档 = **0.2890**（F3）。**同一个头、同一画廊定义，两次评测差 0.0070** —— 这不是头在变，而是 F11 的抽样差异。 |
| ΔCG 是否"主要在文本侧" | **是，而且可以证明**：严格冻结 + `n_trainable_vision_side=0` ⇒ 图像嵌入在适配前后**逐位不变**（同一次评测抽样内）。所以 −0.3913 的**全部**来自文本嵌入变化。这一点与论文 CLIP 的 text_only 臂同构，不是本实验的缺陷。 |
| 配对复测 | 用归档 checkpoint 在同一批图像上重测（冻结 vs 适配），见 §3.2 表 T2（`_p357` → `norm_probe/results.json::adapted`）。 |
| 未证 | **随机头对照（`--head random`）未跑**：因此"这个 ΔCG 反映的是适配位置，而不是'头提供了可被文本侧轻易压小的对齐'"**未定**。这是我对本实验最担心的单点。 |

### A.3 单 seed / 无离散度

| 项 | 内容 |
|---|---|
| 已有种子数 | **1**（`text_only/seed42` 完整 10 epoch）；seed123 只到 epoch 3（F7）⇒ 不能算 n=2。 |
| 第一手离散度证据 | 两个 seed 在**匹配 epoch** 上的 CG（不同 seed = 不同 LoRA 初始化 + 不同评测抽样，二者混在一起）：epoch1 0.4778 vs 0.4817；epoch2 0.4147 vs 0.4243；epoch3 0.3677 vs 0.3804。差值 0.004~0.013。来源：`fitted/text_only/seed42/gap_history.json` 与 `fitted/text_only/seed123/best_checkpoint.pt::gap_history`（经 `_p357a`）。 |
| 是否噪声 | 轨迹**平滑单调**（F2），且 10 epoch 累计 −0.391、单 epoch 最大降幅 0.199（第 1 epoch）——**不像随机跳变**。 |
| 抽样噪声量化 | 见 **§3.3**（N 次重复评测分布 + 成对 bootstrap）。 |
| 判定 | **A.3 部分成立（已量化）**：n=1 仍是硬伤，但"−0.39 是抽样噪声"这一假设被排除——ΔCG 的抽样 sd 只有 **0.0002~0.0004**（§3.3），成对 bootstrap 区间 [−0.3979,−0.3805] 也把归档值包在里面（§3.4）；轨迹平滑单调（F2）。真正不能由 n=1 支撑的是**三臂排序**（需要另两臂 + 噪声带）。 |

### B.4 与论文 `tab:position_strict` 的协议可比性

逐项对比（左=论文 `experiments/strict_freeze_control.py`，右=本实验 `tools/_p293_dinov2_hetero_strict.py`）：

| 项 | 论文 CLIP B/32 | 本实验 | 可比 |
|---|---|---|---|
| 数据集 / 样本数 | Flickr30k，`max_samples=5000`（`data_dir="."`） | 同 | ✅ |
| epoch / batch / rank / α / lr / wd / scheduler | 10 / 128 / 8 / 16 / 1e-4 / 0.01 / cosine（TrainConfig 默认） | 同（同用 TrainConfig 默认） | ✅ |
| LoRA 目标模块 | 默认 `["q_proj","v_proj"]`（CLIP 视觉+文本） | 文本 `["q_proj","v_proj"]`；视觉 `["query","value"]`（DINOv2 自己的命名） | ✅ 同类（q/v），命名随架构 |
| 严格冻结不变量 | 可训参数全部为 LoRA A/B | 同（并带闭式断言） | ✅ |
| 可训参数量 | 196,608 / 491,520 / 294,912 | 同（text_only 已核对 196,608） | ✅ |
| 评测画廊 | 500 对（0.1×5000，`random_split` 后），**带随机增强** | 同 | ✅（同一缺陷，F11） |
| ΔCG 定义 | 同 run 内 `final_gap−initial_gap` | 同 | ✅ |
| **seeds** | **5**（42/123/456/789/1024） | **1**（42） | ❌ |
| **模型** | 原生对比式双塔（CLIP B/32） | **异质配对**：DINOv2-base + CLIP 文本 + 拟合头 | ❌ |
| **视觉塔归一化** | CLIP 统计量（=本身份） | CLIP 统计量（≠视觉塔本身份，F9） | ❌ |
| **损失温度** | `logit_scale` 冻结于 **4.6052**（τ=0.01，来自本地权重） | 硬编码 **2.6593**（τ=0.07） | ❌（F16） |
| 初始对齐（R@1） | 严格冻结臂 0.62~0.69 | frozen 0.289（F3） | ❌（差约 2 倍，非"同一 regime"） |
| frozen 基线记录 | 只有 effective rank + backbone_delta，**无 CG/DG/R@1**（F12） | 有 CG/DG/R@1（F3） | ⚠️ 本实验更完整 |

**判定：B.4 不成立（不可比）**——样本/epoch/batch/rank/α/评测规模这些"可对齐项"确实对齐了，但有 4 条结构性不可比项（异质配对、归一化、损失温度、初始对齐水平）。**任何把 −0.3913 与 −0.0465 直接并列比较的写法都站不住**。

### B.5 `backbone_delta` 全 0 的解释是否成立；缺 `lora_update_norm` 是否影响结论

| 项 | 内容 |
|---|---|
| 队友的解释 | "严格冻结下参考权重确实没变，真正被训的是不在参考 state_dict 里的 LoRA A/B 矩阵" |
| 我的核实 | **解释正确**。机制：`ref = build_model(...)` 是**不含 LoRA** 的新模型；比较循环 `for name,p in model.named_parameters()` 只处理 `key in ref_sd` 的项（`tools/_p293_dinov2_hetero_strict.py:406-414`），而 `lora_A/lora_B` 的键在任何参考 `state_dict` 里都不存在 → 被 `continue` 跳过；`.original.` 名字归一化让包装后的原权重正确对上参考键。于是**全 0 恰好是"冻结成功"的验证**，而不是"没有适配"。 |
| 该字段是否有用 | **有用但很弱**：它只能证伪"原权重被改动"，不能给出适配幅度。作为冻结验证它与论文同款（`experiments/strict_freeze_control.py:182-206`）。 |
| 缺 `lora_update_norm` 是否影响结论 | **影响"为什么 −0.39 这么大"的解释，不影响 −0.39 本身**。我已从 checkpoint 恢复该值（F15）：DINOv2 异质 text 侧 8.3371 vs 论文 CLIP text 侧 5.4416（同公式、同 rank/α/层数/宽度/数据）⇒ **文本塔被推得比论文里远 1.53×**。这是"异质配对被推得更多"的**独立量化证据**，值得写进报告。 |
| 另发现（已修） | 未提交改动里曾有一段 `for w in lora_layers.values(): w.lora_A.data.zero_(); w.lora_B.data.zero_()`——它清零的是**已训好的** `model`（`ref` 没有 LoRA），导致紧随其后计算的 `lora_update_norm_frobenius/lora_update_max_abs` **恒为 0.0**。Lead 已让上游删除并加注释；我已复核工作区（两行已不存在，注释说明原因）。**影响面**：`both/seed42` 进程在 16:50 启动、加载的是**修复前**代码 ⇒ 它的 `results.json` 里这两个字段仍会是 0.0，**不得当作发现**；真值可从其 checkpoint 用 `tools/_p365_lora_update_norms.py` 恢复。`vision_only` 由新子进程启动，会带上修复。 |
| 更正我先前给出的一个数 | 我在给 Lead 的中间汇报里写过"20.0524 总范数 / per-layer 均值 0.8355"——那是 **24 层逐层范数之和**这一种聚合；与论文/本实验同公式的可比值是 **8.3371**。比较时用 8.3371。 |

### C.6 结论能否成立

| 项 | 内容 |
|---|---|
| 观察 | text_only 同时 ΔCG↓(−0.3913)、ΔDG↓(−0.4462)、R@1↑(0.2890→0.3540)；论文 CLIP B/32 严格冻结里 text_only 是 ΔCG 最小**但** R@1 最低的臂（0.6238 vs both 0.6932）。 |
| 能否用"异质组合本身"解释 | **能，而且我认为这就是主因**，有三条独立证据：(1) 初始 R@1 0.289 只有论文 CLIP 臂（0.62~0.69）的 47%，即文本空间与（头投影后的）图像空间几乎没对齐，文本侧适配有巨大的"可压空间"；(2) 文本塔被推得比论文远 1.53×（F15）；(3) 论文自己的 BioCLIP 行——同样是"初始对齐差/非原生配对"——给出同量级 ΔCG（F14）。三者一致指向"**ΔCG 的量级由初始对齐水平与配对方式决定，而不是由适配位置决定**"。 |
| 论文的"分组规则"能否套用到本实验 | **有一个概念漏洞必须指出**：论文的规则是"**双塔联合对比预训练** → text_only 最小；否则 → both 最小"（`paper合/sections/empirical.tex:179`）。本实验的两塔**分别来自不同预训练**（视觉自监督、文本对比式），**"该模型的预训练目标"没有定义** ⇒ 无论三臂跑出什么顺序，都不能用它来"确认/否证"论文的分组。这一点必须在报告里写明，否则等于用一个规则未定义的样本去检验该规则。 |
| 结论表述建议 | 见 **§4**。 |

### 2.7 补充发现（超出 A/B/C 清单，但比本实验本身更重要）

**（1）损失温度不一致（F16/F23）** —— 判 **成立（缺陷）**
- 本地 `models/clip-vit-base-patch32/pytorch_model.bin` 的 `logit_scale = 4.605170 = ln(100)` ⇒ **τ = 0.01**；
  全文件 SHA256 `A6308213…576F` 与 HF 缓存 `models--openai--clip-vit-base-patch32/snapshots/3d74acf9…/pytorch_model.bin`
  **完全相同** ⇒ 这是上游原件的真实值（`config.json::logit_scale_init_value = 2.6592` 与权重不符，属该 HF 件自身的历史）。
- 本实验脚本硬编码 `LOGIT_SCALE_INIT = 2.659260036932778`（τ = 0.07）并冻结，注释称其为 "CLIP logit scale init" ⇒ **对该权重是错的**。
- `src/trainer.py:419` 训练损失直接用 `logit_scale.exp()` ⇒ **论文各臂在 exp=100 的尺度下训练，本实验在 exp=14.29 下训练（7×）**。严格冻结下它不可训，所以差异是起点性的、不会随训练收敛掉。
- 影响：**不影响 ΔCG 的定义、不影响本实验三臂之间的横向比较**；但**足以否定"把 −0.3913 与论文 CLIP 行并列"**。
- 出处：`tools/_p363_logit_scale_provenance.py`、`tools/_p364_pristine_clip_provenance.py` → `logit_scale_provenance.json`、`pristine_clip_provenance.json`。

**（2）单 run R@1 不可从自身 checkpoint 复现（F19–F21）** —— 判 **成立（缺陷，成因未定）**，详见 §3.6。

**（3）归档 frozen 基线无 CG/DG/R@1（F12）** —— 判 **成立（归档缺口）**
`outputs/strict_freeze/frozen/results.json` 只有 6 个键；`experiments/strict_freeze_control.py:312-339` 不计算 CG/DG/R@1；
`outputs/flickr30k/baseline_frozen/results.json::final_task_metrics = null`。⇒ 论文中任何"冻结模型 R@1"的说法在归档里**没有来源**。

---

## 3. 量化结果（全部已落盘）

### 3.1 T1 —— frozen 基线在四种图像流水线下的 CG/DG/R@1 ✅ 已填

**来源**：脚本 `tools/_p357_dinov2_norm_probe.py`（rev-2）→ 归档
`outputs/analysis/dinov2_hetero/norm_probe/results.json::frozen`（+`::protocol_facts`）。
同一冻结权重（DINOv2+CLIP 文本+归档 `heads/fitted.pt`）、同一 500 对画廊
（`protocol_facts.val_indices_sha1_16 = d69098c0074eca13`，`n_pairs=500`）、同一文本嵌入。

| 流水线 | 归一化 | 几何 | CG | DG | R@1 | R@1 (i2t/t2i) |
|---|---|---|---|---|---|---|
| `clip_clean` | CLIP mean/std | Resize 224 | **0.6769** | 0.7512 | **0.2740** | 0.2880 / 0.2600 |
| `imagenet_clean` | ImageNet | Resize 224 | 0.6768 | 0.7510 | 0.2780 | 0.2900 / 0.2660 |
| `dinov2_native` | ImageNet | 256→crop224（官方） | **0.6785** | 0.7521 | **0.2720** | 0.3020 / 0.2420 |
| `clip_aug_r0` | CLIP | Resize224+翻转+抖动（协议实际） | 0.6767 | 0.7508 | 0.2800 | 0.2840 / 0.2760 |
| （归档 `fitted/frozen/results.json`） | CLIP | 协议实际 | 0.67688 | 0.75099 | 0.28900 | — |

**结论（A.1 定性）**：归一化错配**真实存在，但对报告量的影响可忽略**：
- CG：`dinov2_native − clip_clean` = **+0.0016 ± 0.0008**（成对 bootstrap，95% [+0.0001, +0.0032]，`::paired_boot_dinov2native_minus_clipclean`）→ 相对 0.6769 是 **+0.24%**；只换 mean/std（`imagenet_clean`）时 CG 差 **−0.0001**。
- R@1：0.2720（官方流水线）~0.2800（增强抽样），全部落在**同一抽样波动区间**内（§3.3），即"换归一化"与"换一次抽样"不可区分。
- ⇒ **"frozen 基线被归一化错配弄坏、因而 gap 更容易被压小"这一假设不成立**（见 §3.2 的成对复测：ΔCG 在四种流水线下都在 −0.3892~−0.3917）。
- 附带修正一个说法：`image_size=224` **不是**越界（DINOv2 官方 preprocessor 就是 256→crop224，F10）；越界的只有 mean/std。

### 3.2 T2 —— 归档 text_only 的成对复测（同一批图像，冻结 vs 适配）✅ 已填

**来源**：`tools/_p357_dinov2_norm_probe.py`（rev-2）→ `norm_probe/results.json::adapted`；
LoRA 来自 `fitted/text_only/seed42/last_checkpoint.pt`（`checkpoint_epoch=10`，24 层，逐层键集合与注入层断言相等）。

| 图像流水线 | CG_frozen | CG_adapted | **ΔCG（成对）** | ΔDG（成对） | R@1 冻结→适配 |
|---|---|---|---|---|---|
| `clip_clean` | 0.6769 | 0.2854 | **−0.3915** | −0.4464 | 0.2740 → **0.3540** |
| `dinov2_native` | 0.6785 | 0.2893 | −0.3892 | −0.4444 | 0.2720 → 0.3440 |
| `imagenet_clean` | 0.6768 | 0.2850 | −0.3917 | −0.4466 | 0.2780 → 0.3610 |
| `clip_aug_r0` | 0.6767 | 0.2856 | −0.3910 | −0.4459 | 0.2800 → 0.3570 |
| **归档 `results.json`** | 0.67676 | 0.28550 | **−0.39127** | −0.44625 | 0.28900 → **0.35400** |

**结论**：
1. 归档的 −0.3913 **可被独立复现到 0.0002~0.0004**（−0.3915 / −0.3892 / −0.3917 / −0.3910）。R@1 的**适配后**值 0.3540 也被**逐位复现**（`clip_clean` 行）。
2. 归一化对照下 ΔCG 的变化量 ≤0.0025，而它与归档的偏差 ≤0.0004 ⇒ **−0.39 不是归一化产物**。
3. **A.2 的"ΔCG 全部来自文本侧"是构造性事实**：适配前后图像嵌入逐位相同（严格冻结 + `n_trainable_vision_side=0`），所以 ΔCG 只能来自文本嵌入。这不是缺陷，与论文 text_only 臂同构。
4. 一个**未定**的小观察：归档 `results.json` 里 `R@1_i2t = R@1_t2i = 0.3540`（逐位相同），而我这次独立抽样得到 `0.3620 / 0.3460`（均值同为 0.3540，见 `::adapted.clip_clean.adapted`）。均值复现，两个子指标不相等 ⇒ 归档那次的 i2t/t2i 相等更可能是**同一次抽样的巧合**（两个计数都=177/500），不是结构性性质。对论文比较所用均值**无影响**，标 **未定**。

### 3.3 T3 —— 评测抽样噪声（N=12 次重复评测同一 checkpoint）✅ CLIP 三臂已填

**来源**：脚本 `tools/_p360_gallery_noise.py` → `gallery_noise/results.json`；缺陷修正与协议口径重算
`tools/_p366_gallery_noise_fix.py` → `gallery_noise/results_corrected.json`。
每次重复 = 同一画廊的新一次增强抽样（逐项固定 seed），文本侧固定（tokens 确定）⇒ 变化只来自图像侧，与协议一致。
**协议口径**：真实 run 在 epoch 0 测 initial、epoch 10 测 final，是**两次独立抽样**，故主列为"独立 draw"口径
（`delta_CG_protocol_independent_draws`）；同 draw 配对口径另列。

| 模型 / 臂（各 12 次新抽样） | **ΔCG 均值 ± sd（独立 draw）** | ΔCG sd（同 draw） | **R@1_final 均值 ± sd（极差）** | 归档 ΔCG | 归档 R@1 |
|---|---|---|---|---|---|
| CLIP B/32 **text_only** seed42 | **−0.0445 ± 0.00070** | 0.00019 | **0.6204 ± 0.0078**（0.0250） | −0.0443 | 0.6180 |
| CLIP B/32 **both** seed42 | **−0.0253 ± 0.00045** | 0.00041 | **0.6949 ± 0.0055**（0.0170） | −0.0253 | 0.6890 |
| CLIP B/32 **vision_only** seed42 | **+0.0110 ± 0.00054** | 0.00039 | **0.6782 ± 0.0061**（0.0210） | +0.0108 | **0.7000** ⚠️ |
| DINOv2 异质 **text_only** seed42 | **−0.3911 ± 0.00027** | 0.00027 | **0.3588 ± 0.0045**（0.0140） | −0.3913 | 0.3540 |

（DINOv2 行的 init 取自 `norm_probe/results.json::frozen.clip_aug_r0`，原因见 `_p366` 说明：rev-1 在算 T_init 时已把适配后的文本 LoRA 载入，故该臂自身的 init 通道无效；末态值全部有效。）

**关键结果**：
- **四个臂的 ΔCG 均值都与归档一致到 0.0002~0.0003**（−0.0445 vs −0.0443；−0.0253 vs −0.0253；+0.0110 vs +0.0108；**−0.3911 vs −0.3913**）⇒ 归档 ΔCG **可复现**，我的管线与协议等价。
- **ΔCG 的抽样 sd 只有 0.0003~0.0007**（协议口径），即 **±0.002 就已经是 3σ**。
- **R@1 的抽样 sd 是 0.0045~0.0078，极差 0.014~0.025**（≈ 7~12 对 / 500），比 ΔCG 大一个数量级还多。
- ⚠️ **`vision_only` 的归档 R@1（0.7000）复现不出**（我的 0.6782±0.0061，用论文自身代码路径 0.6790）——见 §3.6，这条比 DINOv2 那三臂更重要。

### 3.4 T4 —— 成对 bootstrap（500 对画廊的抽样不确定性）✅ 已填

**来源**：`norm_probe/results.json::bootstrap_CG_frozen` / `::paired_boot_*`（rev-2，n_boot=2000，seed 12345/999）

| 量 | 点估计（bootstrap 均值） | sd | 95% 区间 |
|---|---|---|---|
| CG（frozen，`clip_clean`） | 0.6786 | 0.00404 | [0.6706, 0.6863] |
| CG（frozen，`dinov2_native`） | 0.6802 | 0.00418 | [0.6720, 0.6882] |
| `dinov2_native − clip_clean`（frozen，成对） | +0.00161 | 0.00078 | [+0.0001, +0.0032] |
| **text_only ΔCG（`clip_clean`，成对）** | **−0.3892** | **0.00448** | **[−0.3979, −0.3805]** |
| text_only ΔCG（`dinov2_native`，成对） | −0.3869 | 0.00455 | [−0.3958, −0.3781] |

（归档 −0.39127 落在 `clip_clean` 的 95% 区间内；两个归一化下的 ΔCG 区间高度重叠 ⇒ 归一化不构成解释。）

### 3.5 折算到论文量级：抽样噪声 vs 臂间间隔 ⭐ Lead 的核心问题

论文一格的比较量是**5-seed 均值**，因此"单次评测 sd"要折算成 `sd/√5` 再与臂间间隔比。

| 量 | 论文臂间间隔 | 单次评测 sd（本次实测） | 5-seed 均值的 sd | 判定 |
|---|---|---|---|---|
| **ΔCG**（CLIP B/32） | text_only vs both = **0.0207**；both vs vision_only = **0.0364**（来源 `clip_baseline_check.json::rows`） | **0.00045~0.00070** | **0.0002~0.0003** | 噪声 = 间隔的 **1.5%~3%** ⇒ **低一到两个数量级，不能动摇 ΔCG 排序** |
| **R@1**（CLIP B/32） | text_only vs both = **0.069**；both vs vision_only = **0.013** | **0.0055~0.0078** | 0.0025~0.0035 | 0.069 的间隔 → 单 run **8.8~12.5σ**、5-seed **20~28σ**，**稳**；**0.013 的间隔 → 单 run 仅 1.7~2.4σ、5-seed 3.7~5.2σ；若改用论文自己归档的 seed-sd（0.0146/0.0117）只有约 1.5σ ⇒ 边缘结论，不应被当作硬结论** |
| **R@1 单格复现差异**（论文 vs 归档 5-seed 均值） | 观测 |Δ| = 0.0006~0.0064（6/12 格，来源 `r1_discrepancies.json`） | — | 两套独立评测的 5-seed 均值之差 sd ≈ 0.006·√2/√5 ≈ **0.004** | **6 格中 5 格的差异（0.0006–0.0022）落在 ~0.5σ 内 ⇒ 画廊随机性足以解释**；§3.6 又给出单 run 层面的直接机制（归档单 run R@1 可偏离同权重新抽样 0.005~0.021）。**但最大那格 0.0064 不是噪声**——它是 OpenCLIP r4 text_only，`r1_provenance.json::conclusion` 已查明该行 R@1 来自 **rank-8** 树而 ΔCG 来自 **rank-4** 树（**provenance 混用**，需改稿而非改口径） |


**回答 Lead 的三个问题**：
1. **分布**：见 §3.3（四臂 × 12 次新抽样的均值、sd、极差）。**ΔCG 的抽样 sd = 0.0003~0.0007；R@1 的抽样 sd = 0.0045~0.0078（极差 0.014~0.025）**。
2. **是否同量级**：**ΔCG 不同量级**（噪声 sd 0.0007 对臂间间隔 0.021/0.036 ⇒ 噪声只占 2%~3%，低 1~2 个数量级 ⇒ **论文 ΔCG 列稳健**）；**R@1 在"单 run 层面同量级"**（sd ≈ 0.006 vs 最小臂间间隔 0.013 ⇒ 单 run 只有 ~2σ；5-seed 均值口径 ~4.8σ；若改用论文自己归档的 seed-sd 0.0146/0.0117 则只有 ~1.5σ）。⇒ **"text_only 检索最差"（间隔 0.069）稳**；**"both 检索优于 vision_only"（0.013）属边缘，建议不再强调**；**R@1 单格的第 3 位小数级复现差异可由本噪声解释**（§3.6 给出机制与量级）。
3. **修复**：见 §8。**不要**为这件事改评测管线再重跑全表（会与归档全面失配）；优先"对具体主张做 K 次重复评测 + 报 sd"。

### 3.6 T6 —— 新发现：论文归档里的**单 run R@1 不可从其自身 checkpoint 复现**（本报告最重要的一条）

**来源**：`tools/_p369_reproduce_clip_arm_r1.py` → `outputs/analysis/dinov2_hetero/paper_path_r1.json`；
`tools/_p370_vision_only_checkpoint_identity.py` → `.../vision_only_ckpt_identity.json`。
方法：用**论文自己的 loader**（`src.dataset.create_dataloaders`，num_workers=4、batch128、含随机增强画廊）
+ **论文自己的指标函数**（`src.trainer.GapAwareTrainer._compute_retrieval_metrics`，未改一行）
+ 归档 checkpoint，重复评测。

| 臂（seed42） | checkpoint epoch | 用论文自身代码路径的 3–4 次新抽样 | 归档 `final_task_metrics.R@1` | 差 |
|---|---|---|---|---|
| text_only | 10 | 0.6260 / 0.6050 / 0.6270 / 0.6210（均值 0.6198） | 0.6180 | +0.002 |
| both | 10 | 0.6940 / 0.6950 / 0.6890 / 0.6920（均值 0.6925） | 0.6890 | +0.004 |
| **vision_only** | 10 | 0.6820 / 0.6750 / 0.6810 / 0.6780（均值 0.6790） | **0.7000** | **−0.021** |
| vision_only（epoch 9 的 `best_checkpoint.pt`） | 9 | 0.6800 / 0.6770 / 0.6790（均值 0.6787） | 0.6940（该 epoch 记录值） | **−0.015** |

三条独立路径（我的 `_p360` 管线 12 次抽样均值 0.6782 ± 0.0061、论文自身路径 4 次 0.6790、epoch-9 权重 3 次 0.6787）
**一致给出 ≈0.679**，而归档对同一权重记的是 0.694（epoch 9）/ 0.700（epoch 10）。差异**集中在 t2i 半边**
（归档 0.690/0.710；我的新抽样 i2t 0.680~0.688、t2i 0.666~0.684），i2t 基本吻合而 t2i 系统性偏低。

**结论与含义**：
- 这不是我的管线问题（用了论文自己的 loader 与指标函数），也**不是 seed 或权重问题**（`best_equals_last_weights=false`，两个 epoch 的权重都被正确地分别复现）。
- 同一 arm 的其余 4 个 seed 归档值为 0.6790/0.6720/0.6780/0.6710（5-seed 均值 0.6800），与我的新抽样 0.679 **高度吻合** ⇒ **被记录的那个 0.7000 是这组里最高的单次抽样**。
- ⇒ **归档里"每个 seed 的 R@1"是单次随机画廊抽样，其 run 级偏移可达 ~0.02**；而 **5-seed 均值更稳**（本例 0.6800 vs 新抽样 0.679）。
- **对 PR 回复的直接价值**：R1.1/R3.1 的"数字对不上"**至少部分可归因于这个机制**（配合 §3.5）：单 run R@1 的评测噪声 ±0.006~0.008（极差 0.021），5-seed 均值层面的差异量级 ~0.005，与论文 6 个 R@1 格观测到的 0.0006~0.0064 差异**同量级**。
- **未定**：为什么 `vision_only` 会出现 +0.015~+0.021 的**系统性**（两个 epoch 都偏高）偏移，我**没能查清**——不是 seed、不是权重（已核对 epoch）、不是指标代码（用的是论文自身的）。剩余的候选解释（该 run 的抽样恰好偏"易"、或某个我未识别的评测期差异）我无法在归档上区分。**这一条我明确标为未定，不得写成已定论。**


---

## 4. "该实验的结论应如何表述"（我的建议，含必须标注的限制）

### 4.1 可以写（有来源、不过度）

> **一句式**：在严格冻结下，一个**异质配对**（DINOv2-base 视觉塔 + CLIP ViT-B/32 文本塔 + 在不相交切分上拟合后冻结的投影头）的文本侧适配臂把 Centroid Gap 从 0.6769 降到 0.2855（ΔCG = −0.3913，1 seed，500 对画廊），R@1 由 0.2890 升到 0.3540。
> **可复现性**：该 ΔCG 由审计用归档 checkpoint 在**独立抽样**上复现到 **0.0002~0.0004**（−0.3915/−0.3892/−0.3917/−0.3910 四种图像流水线；`norm_probe/results.json::adapted`）；适配后 R@1 = 0.3540 **逐位复现**。抽样/画廊噪声量级为 sd(ΔCG) ≈ 0.0003、sd(R@1) ≈ 0.008（§3.3）。
> **定位**：这是本论文对照在**非原生对比式配对**上的第一个实例；其 ΔCG 量级与表中已有的 BioCLIP B/16 行（−0.3671/−0.4515/−0.2927）一致，因此**不构成对论文量级结论的反例**。

### 4.2 必须同时标注的限制（缺一不可）

1. **不是原生模型**：没有"DINOv2 双塔"这种东西；对齐由拟合头提供，该头有 656,384 个可训练参数（比适配器本身大），且**随机头对照尚未跑**。
2. **n=1 seed**（评测抽样噪声已量化并很小，但训练 seed 的离散度未测）；论文各行是 5-seed 均值。
3. **视觉塔收到 CLIP 均值/方差**（DINOv2 要 ImageNet 统计量）⇒ 这一条**已做对照并被证明影响可忽略**（frozen CG 只差 +0.0016，ΔCG 只差 ≤0.0025；§3.1/§3.2）。**仍应主动披露**，因为 `results.json::image_normalisation` 字段本身就写着这句话，审稿人会看到；披露时请一并给出上述对照数字。
4. **损失温度不同**：论文 CLIP 行 τ=0.01（本地权重 `logit_scale=ln 100`，全文件 SHA256 与上游一致），本实验 τ=0.07 ⇒ **不可与论文 ΔCG 逐格并列**（`src/trainer.py:419` 训练损失直接用它）。
5. **初始对齐水平不同**：frozen R@1 = 0.289 vs 论文 CLIP 臂 0.62~0.69（论文骨干的 frozen R@1 本次首测为 **0.5770**，500 对画廊 draw 0，`gallery_noise/results.json`）。
6. **不得用于检验论文的分组规则**：该规则定义在"双塔联合预训练的对比式 vs 其他"之上，异质配对没有单一"预训练目标"（见 §2 C.6）。

### 4.3 明确不要写（我建议 Lead 拦下这些表述）

- ❌"−0.39 是论文里所有 ΔCG 的 4~37 倍，因此论文的适配位置结论有问题"——**前提错误**（BioCLIP 行 −0.3671/−0.4515/−0.2927）。
- ❌"在 DINOv2 上 text_only 仍然最保对齐/顺序反转，支持/否证论文"——三臂未跑完，且规则未定义。
- ❌"frozen 基线 CG 0.6769 与论文 CLIP 的 0.8183 可比"——配对与归一化都不同（可以并列展示，但不能据此下"更对齐/更差"的结论）。
- ❌"text_only 提升了 R@1，所以 gap 下降是好事"——论文的反例正是"gap 最小者检索最差"；本实验里二者同向，需要解释为"初始对齐差 ⇒ 向图像云移动同时改善两者"，**不能反过来当作一般结论**。

---

## 5. 我认为最可能被审稿人挑战的点（按风险排序）

1. **"你测的是你的头，不是 DINOv2。"** 头在 5000 条 caption 上以 InfoNCE 训练，参数量（656,384）比适配器（196,608~491,520）还大；缺随机头对照 ⇒ **无法排除"头提供了可被文本侧压小的对齐"**。这是本实验**最脆弱的一点**。建议：跑 `--head random`（3 臂 × ~4~5 h GPU），或在正文明确写 "head-fitted only, random-head control not run"。
2. **"那 −0.39 是不是你自己把基线的归一化弄坏了？"** 这一条**我已经用对照实验答了**（§3.1/§3.2：影响 ≤0.0025 = 效应量的 0.6%），**主动写进回复信即可把这条攻击变成加分项**（"我们检查并量化了这个风险"）。只能攻击的残余部分是"没有在正确统计量下重新拟合头"，如实标注即可。
3. **"n=1、且评测画廊是随机的。"** 现在有量化答案（§3.3/§3.5）：**ΔCG 的抽样 sd 只有 0.0002~0.0004**（远小于论文臂间间隔 0.021~0.036），**R@1 的 sd 0.005~0.008**（与论文最小的 R@1 臂间间隔 0.013 同量级）。如实报告反而说明作者查得比审稿人深。
4. **"损失温度都不一样，凭什么并列？"** 这是本轮新发现，必须主动披露——**主动说 > 被审稿人抓到**。诚实的化解办法：不把 −0.3913 与论文 CLIP 行逐格比，只与 BioCLIP 行做"量级同类"的陈述。
5. **"BioCLIP 那行本来就是例外，你只是又加了一个例外。"** 最难答。诚实答法：R2.3 要的是"更广模型覆盖"，本实验提供的正是**又一类**（自监督视觉塔）覆盖，并量化了"这类模型的 ΔCG 由初始对齐水平主导"（初始 R@1 0.289 vs 论文骨干 0.577，且文本塔更新量 8.3371 vs 5.4416）；**不宣称**论文分组规则在非对比式骨干上得到验证。
6. **"gap 降了检索反而升了，说明 CG 不是有意义的指标。"** 需要用"初始对齐差 ⇒ 向图像云移动同时改善两者"解释方向反转，并明确这是该 regime 的性质，不是普遍规律。
7. **（内部必须先处理，审稿人一定会问）"你们所有数字都是随机画廊的单次抽样？"** 现在有完整答案（§3.3/§3.5/§3.6）：**ΔCG 稳健**（抽样 sd 0.0005~0.0007，三个臂的新抽样均值与归档一致到 0.0003）；**R@1 不稳健**（sd 0.0055~0.0078，且 `vision_only/seed42` 归档的 0.7000 用论文自身代码路径只能测到 0.679）。⇒ 建议在回复信里**主动交代**：(a) 评测画廊带随机增强这一事实；(b) 我们实测的噪声带；(c) **ΔCG 列不受影响**；(d) R@1 列以 5-seed 均值报告并给误差，不依赖 <0.02 的 R@1 差异；(e) OpenCLIP 行 R@1 的 0.0064 差异**另有原因**（provenance 混用，需改稿）。

---

## 6. 我没能查清的（明确未定）

0. **`vision_only/seed42` 归档 R@1 系统性偏高 ~0.015~0.021 的成因**（§3.6）：已排除 seed、checkpoint 权重（epoch 9/10 两套都复现）、指标代码（用的是论文自身的 `_compute_retrieval_metrics`）、差分两半（i2t 吻合、t2i 偏低）。剩余候选（该 run 抽样恰好偏易 / 某个未识别的评测期差异）**无法在归档上区分 ⇒ 未定**。
1. **随机头对照**（`--head random`）未跑 ⇒ 头的作用**未定**。
2. **在 DINOv2 正确归一化下重新拟合头后的 frozen 基线与 ΔCG** ⇒ 需要 GPU 训练（头拟合 57 min + 3 臂），本轮 **未做**；我用"同头换统计量"（§3.1/§3.2）作代理并证明影响很小，但"重新拟合后完全不变"**未定**。
3. **头无关的 ridge 探针未完成**：`tools/_p357_dinov2_norm_probe.py` rev-1 的 `ridge_probe` 因我自己的索引越界 bug（调参切分 [5000,10000) 超出 `max_samples=5000` 截断后的数据集）崩溃，rev-2 已移除该模块 ⇒ **"是头还是视觉特征本身限制了对齐"未定**。
4. **`vision_only` / DINOv2 异质的 12 次抽样分布**：审计交稿时仍在跑（`gallery_noise/results.json` 已含 CLIP 三臂）。
5. **`both/seed42` 与 `vision_only/seed42` 两臂**未完成 ⇒ 三臂排序、以及"是否复现 BioCLIP 的 both 最小"**未定**。
6. **`both/seed42` 的 `lora_update_norm*` 字段**：该进程 16:49:54 启动，而修复版脚本 mtime = **17:01:54** ⇒ 它加载的是修复前代码，字段会是 **0.0**，**不得当作发现**；真值需从它的 checkpoint 用 `tools/_p365_lora_update_norms.py` 恢复（审计交稿时它还在训练，**未定**）。
7. **论文 R@1 列那 3 个 CLIP 格（0.0006~0.0012）的确切来源**：画廊随机性在量级上足以解释（预期 |Δ| ≈ 0.005），但"到底是重评过 checkpoint 还是手抄错一位"**未定**——归档里没有产生该列的脚本记录。
8. **DINOv2 在 518 分辨率下的结果**未测（官方 preprocessor 是 224，故不是必须）；"分辨率不影响结论"**未定**。
9. 归档 `text_only/seed42` 里 `R@1_i2t == R@1_t2i == 0.3540` 逐位相同，而我独立抽样得 0.3620/0.3460（均值相同）⇒ 我判断为**同一次抽样的巧合**，但**未定**（无法重放原抽样）。


---

## 8. 最小修复方案（Lead 问：是否只需在评测画廊上关掉随机变换？先不改代码）

**根因**：`src/dataset.py:401-425`。`kwargs["split"]="train"` 只构造了**一个** dataset 对象，`val_dataset`/`test_dataset`
在 L422 被 `random_split(train_dataset, ...)` 的结果**整体覆盖**，于是 val/test 是**同一个带增强 transform 的对象的 Subset**。

**最小修复（6 行，不动标注解析、不动训练集增强）**：

```python
# src/dataset.py  替换 L416-425 的 flickr30k 分支
if dataset_name == "flickr30k":
    from torch.utils.data import random_split, Subset
    det = cls(data_root, split="val", image_size=image_size,      # 确定性 transform
              max_samples=max_samples, pre_tokenize=pre_tokenize)  # 同一份 flickr30k.json
    n = len(train_dataset)
    n_train, n_val = int(0.8 * n), int(0.1 * n)
    tr, va, te = random_split(train_dataset,
                              [n_train, n_val, n - n_train - n_val],
                              generator=torch.Generator().manual_seed(42))
    train_dataset = tr                       # 训练集保留增强（正确做法）
    val_dataset   = Subset(det, list(va.indices))
    test_dataset  = Subset(det, list(te.indices))
```

- 我已验证两个对象在**相同 index 上是同一张图**（`_p357` 里的断言：`ds_train.samples[i]["image"] == ds_clean.samples[i]["image"]` 对 500 个 val index 全部成立），所以画廊内容不变，只是不再随机抖动。
- **必须注意的代价**：这会让**所有已归档数字（含论文全部 CG/DG/R@1）与今后数字不再同口径**。因此**不能静默改**。
  建议加开关 `eval_transform="augmented"|"deterministic"`（默认保持 `augmented` 以便复现已发表结果），并在文档里把两种口径分别命名。
- **对本次投稿/回复更稳的做法（零代码改动、且是审稿人要的东西）**：保持现有管线，对**被质疑的具体主张**做 **K 次重复评测并报 mean ± sd**（就是本报告 §3.3 的做法）。
  这样既不与归档冲突，又把"结论是否超出抽样噪声"讲清楚。
- **建议执行顺序**：① 用 §3.3 的 sd 判断哪些结论超出噪声 → ② 只对超出不足的结论做 K 次重评 → ③ 今后新实验用上面的开关 + 确定性画廊 → ④ 在 limitation 里明确"2026-10-12 之前的数字为单次抽样口径"。

---

## 9. 探针状态与本报告的更新方式

| 脚本 | 内容 | 状态 | 产物 |
|---|---|---|---|
| `tools/_p357_dinov2_norm_probe.py`（rev-2） | 归一化对照 / 成对复测 / 成对 bootstrap | ✅ 完成（669.7 s，CPU 4 线程） | `norm_probe/results.json`、`head_embeds.pt`、`text_embeds.pt` |
| `tools/_p360_gallery_noise.py` + `_p366_gallery_noise_fix.py` | 四臂 × 12 次重复评测分布 | ✅ 完成（49.5 min，CPU 6 线程） | `gallery_noise/results.json`、`results_corrected.json` |
| `tools/_p369_reproduce_clip_arm_r1.py` | 用论文自身 loader + 指标复评归档 checkpoint | ✅ 完成 | `paper_path_r1.json` |
| `tools/_p370_vision_only_checkpoint_identity.py` | epoch 9/10 权重身份与 R@1 | ✅ 完成 | `vision_only_ckpt_identity.json` |
| `_p357a/_p361/…/_p368`（8 个） | checkpoint 探针、协议事实、CLIP API、logit_scale、权重来源、LoRA 范数、R@1 差异清单、checkpoint epoch | ✅ 完成 | 见 §1 各条引用 |

**数字纪律（本报告自检）**：① 每个数字都指向脚本 + 归档文件 + 字段；② 我自己脚本的两处缺陷
（rev-1 bootstrap 未做 L2 归一化；rev-1 的 init 通道把已适配 LoRA 计入）都在代码与归档里**留痕并更正**，
被更正前的字段明确标为 invalid（`_p357` 的 `revision` 字段、`_p366` 的 `raw_rev1_dCG_is_invalid_for_this_arm`）；
③ 凡未查清的一律进 §6 标 **未定**。

**本轮未做**：`--head random` 对照（需 GPU）；正确归一化下**重新拟合头**（需 GPU）；头无关的 ridge 探针（脚本 bug，已弃并说明）；DINOv2 518 分辨率对照；`both`/`vision_only` 两臂的实验本体（审计时仍在 GPU 上跑，见 §6）。

