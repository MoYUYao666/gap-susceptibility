# P3 任务 A 方案：官方 IGU-LoRA 实现 vs 块级再实现（2026-10-24 编制，仅准备，未开机、未训练）

> 交付件：`tools/_p1639_p3_official_igu.py`（`--plan` / `--run-official` / `--compare` / `--self-test`）
> 本文件回答四件事：**caveat 现在怎么写的 → 官方实现是什么 → 公平比较怎么做 → 差距小/大分别怎么写进论文**。
> 所有数字都给出**可复核来源**；未能离线核实的假设集中在第 9 节。

---

## 1. 这条 caveat 现在怎么写

`paper3/paper_ieee/supplementary/supplementary.tex`，Section **"Allocation-rule baselines"**（`\label{app:rules}`，表 `tab:rules` / `tab:rulearms`）原文：

> "Block-level reimplementations in the spirit of three published allocation rules, and one trained arm each under
> the blank-image protocol … **These are our block-level reimplementations, not the official implementations.**"

补充材料另有 Section **"Official IGU allocation stage"**（`\label{app:iguofficial}`，表 `tab:iguofficial`）报告了
官方分配器（`outputs/analysis/p3_official_igu_clip.json`）与其训练臂（`verify_r1_s42_bcexplicit_v12_s1_m2_d1.json`，ΔE **+240.5**）。

**⇒ 因此这条 caveat 的准确含义不是"拿不到官方代码"，而是"官方代码与块级规则从来没有在同一协议下比过"**：

| | 官方那一支（S39） | 块级再实现那一支（S27） |
|---|---|---|
| 分配从哪来 | CLIP 对比学习批（30 步在线剪枝，官方 `RankAllocator`+`SVDLoRAModule`） | LLaVA 探针适配器上的 zero→probe 积分梯度（`tools/_p1514_p3_baseline_rules.py`） |
| 分配结果 | 12/1/2/1（视/浅/中/深，预算 16） | 11/1/3/1 |
| 训练协议 | 20 样本、3 epoch、seed 42、base rank 1、α=16、qkvo | **相同** |
| 训练臂 ΔE | +240.5 | +333.0 |

两支的**训练协议本来就一致**（这正是可以公平比较的前提）；差异只在**分配规则本身**（研究变量）与**分配阶段的输入**（不可消除，见第 4 节）。

---

## 2. 官方实现是什么（已核实）

* **论文**：IGU-LoRA: Adaptive Rank Allocation via Integrated Gradients and Uncertainty-Aware Scoring，
  ICLR 2026（第十四届），OpenReview `MnToYQx9My`（来源：`external/igulora/README.md` 的 BibTeX）。
* **仓库**：`https://github.com/withyou12/igulora.git`
  * HEAD：`3f5ba10a6646c81c557e4669b14b072f76822085`（2026-02-26 07:45:36 +0000，"first commit"）
  * 本地 vendored 路径：`external/igulora/`；**仓库 `.gitignore:87` 忽略 `external/`**（`git ls-files external` = **0** 个文件）
    ⇒ **实例上必须自行克隆**，命令：
    ```bash
    git clone https://github.com/withyou12/igulora.git external/igulora && \
      git -C external/igulora checkout 3f5ba10a6646c81c557e4669b14b072f76822085
    ```
* **哪些是官方、哪些是本仓库的粘合层**（这条决定 caveat 能关到什么程度）：

| 组件 | 归属 | 说明 |
|---|---|---|
| `iglora/rank_allocator.py`（`RankAllocator`：EMA/SNR 打分、AdaLoRA 预算表、mask-to-target-rank） | **官方，逐字未改** | 算法本体；sha256 `6ba699eb…` |
| `iglora/lora_module.py`（`SVDLoRAModule`） | **官方，逐字未改** | 被打分的模块；sha256 `63ff9a98…` |
| 名称代理（把 CLIP attention 投影映射成 `model.layers.<n>.self_attn.<proj>.lora_*`） | 本仓库 | 官方 `RankAllocator` 硬编码 LLM 命名 |
| 四块聚合（per-module rank → vision/浅/中/深） | 本仓库 | 见第 3 节，**有一套已发表口径与一套修正口径** |
| `iglora/run_pruning_sft.py` + `script/benchmark/sst2/*.sh`（SVD-LoRA 文本 LLM 管线，Llama2-7B/SST2） | 官方，但**用不上** | 该管线不能直接嵌入 4-bit LLaVA（HANDOFF 2026-10-22 条目已记录同一结论） |

脚本把上述文件 sha256 全部**钉死**在 `tools/_p1639_p3_official_igu.py::OFFICIAL_FILES`，`--plan`/`--run-official`
逐文件核对；任何漂移都会 FAIL（不会静默用一个来路不明的"官方代码"）。

---

## 3. 编制期间发现的问题：块聚合的两套口径

已发表表格里的 "rank sum = 309 / 23 / 45 / 7" 来自 `tools/_p1557_official_igu_clip.py` 的聚合粘合层，其判据是
`prefix.startswith("model.layers.1")`。CLIP 文本塔只有 12 层，**文本层 1、10、11 的代理名同样以 `model.layers.1` 开头**
（视觉塔代理层号是 100–111），因此这三层被算进了 "vision"。

用归档的 96 个 per-module rank 重算（`tools/_p1639_p3_official_igu.py --plan` 第 [8] 节会逐项断言）：

| 口径 | vision | 浅 | 中 | 深 | 份额 v/s/m/d | 预算 16 分配 |
|---|---|---|---|---|---|---|
| **archived**（已发表 S39 / 已训练臂 +240.5） | 309 | 23 | 45 | 7 | 0.8047/0.0599/0.1172/0.0182 | **12/1/2/1** |
| **corrected**（按真实层号） | 270 | 30 | 45 | 39 | 0.7031/0.0781/0.1172/0.1016 | **11/1/2/2** |

影响与处理：

1. **已发表数字不动**（本任务是准备，不改稿、不改归档）。`--stage allocate` 一次跑出 per-module ranks，
   **同时**给出两套口径并各自断言（archived 必须复现 309/23/45/7 与 12/1/2/1）。
2. 与块级再实现 11/1/3/1 的 L1 距离：archived 口径 **2**、corrected 口径 **2**，**两套都在预声明容差 2 之内**。
   ⇒ 这个粘合层 bug 不改变"两者在同一量级"的结论，但它**改变了 deep 块的 rank 数（7→39）**，
   属于"表格里的一行数字被错误归块"，建议在下一版补充材料里作为 **已知修正** 说明（一句话即可）。
3. `--compare --official-config` 默认 `auto`：**优先用 corrected 口径的臂**（更正确、且与再实现更可比），
   两者都记录在 `allocation_sensitivity_to_the_block_mapping` 里，读者可以看到结论对口径不敏感。

---

## 4. 公平比较清单（`--plan` 第 [5] 节逐条打印）

| 条件 | 官方臂 | 块级臂 | 是否一致 |
|---|---|---|---|
| 数据 | `paper3/train-00000-of-00001-a09b74b3ef9c3b56.parquet` 前 20 行（16 train / 4 eval，空白图协议）sha256 `06391b65…` | 同 | ✅ |
| epoch | 3 | 3 | ✅ |
| 优化器 / lr / batch | AdamW / 5e-5 / 1 | 同 | ✅ |
| 秩预算 | 16 rank-layers，base rank 1，α=16，targets qkvo | 同 | ✅ |
| seed | 42, 123, 789 | 同 | ✅ |
| 基座模型 | `models/llava-hf`，4-bit nf4 double-quant，float16 计算 | 同 | ✅ |
| 评测 | `run_training.py` 的 `compute_E`，同一批 4 个留出样本，ΔE = E(3) − E(0) | 同 | ✅ |
| **分配规则** | 官方 `RankAllocator` + 名称代理 | 块级积分梯度 | **研究变量** |
| **分配阶段的输入** | CLIP 对比批（官方在线剪枝表） | 探针 LLaVA 适配器（后验 IG） | **不可消除，如实声明** |

最后一行必须写进论文：官方分配器是**在线**的 AdaLoRA 式剪枝表，不是"给定探针适配器再后验算梯度"，
所以"同一输入"在原理上做不到；能对齐的是**训练臂的每一个条件**与**预算/评测口径**。

---

## 5. 云端成本（依据实测，不是估算）

**时间**（来源：`outputs/run_*.log` 的 `Training time: 1253–1968 s`；`docs/p3_cloud_round_notes.md` 第 5 节的
`p3_rerun_*.json` elapsed_min 21.3–26.6 分钟）：

| 项 | 数量 | 单次 | 小计 |
|---|---|---|---|
| 官方分配阶段（CLIP-base，30 步 × 4 caption） | 1 | ~2–5 分钟 | ~2–5 分钟 |
| 训练臂（20 样本 / 3 epoch / batch 1，笔记本级 GPU ~21–33 分钟/次） | 6（官方 3 seed + 块级 3 seed） | ~25 分钟 | **~2.5 小时** |
| 复现校验（seed 42 与归档 +240.5 / +333.0 对比） | 含在上面 | — | — |

⇒ **总预算约 2.5–3.5 GPU 小时**（数据中心卡更快；`docs/p3_cloud_round_notes.md` 明确"比笔记本快"）。
只跑 corrected 口径 3 seed + 块级 2 个新 seed（seed 42 复用归档）时约 2 小时。

**磁盘**：不新增下载（CLIP 模型 600 MB、marine captions 159 MB、训练 shard 24 MB、`models/llava-hf` 13.2 GB 均已在库/实例上）；
每个臂归档 ~30 MB；`HF_HOME`/`MODELSCOPE_CACHE` 指向 50 GB 数据盘。

**下载源（遵循仓库"镜像优先"规则）**：本任务**不需要下载任何东西**。若实例缺 `models/clip-vit-base-patch32`
或 marine captions，用镜像取：

```bash
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/hf
python -c "from huggingface_hub import snapshot_download; print(snapshot_download('openai/clip-vit-base-patch32'))"
# 慢则先测多连接再换源；ModelScope 仓库名必须先用 HubApi() 核实
```

**依赖**：官方那两个文件只依赖 `torch`；训练走实例上已跑通的 `paper3/scripts/run_training.py`
（torch + transformers + peft + bitsandbytes + numpy + pandas + pillow）。**不需要** `accelerate`/`datasets`/`tensorboardX`
（那是官方文本 LLM 管线才要的）。pip 一律 `-i https://pypi.tuna.tsinghua.edu.cn/simple`。

---

## 6. 实例上的操作步骤（脚本自己**不下载**任何东西）

```bash
# 0) 见 §2 的 clone 命令；确认 models/llava-hf、paper3/train-*.parquet、models/clip-vit-base-patch32、
#    data/marine_captions 都在
# 1) 只打印、不执行、不写盘（可在任意机器上跑）
python tools/_p1639_p3_official_igu.py --plan
python tools/_p1639_p3_official_igu.py --run-official --stage all --dry-run

# 2) 官方分配阶段（写 outputs/analysis/p3_official_igu_run.json；不训练）
python tools/_p1639_p3_official_igu.py --run-official --stage allocate
#    —— 若分配阶段没能复现归档 per-module ranks，脚本 exit 3 并拒绝继续（不会拿漂移的结果去训练）

# 3) 训练 6 个臂（官方 corrected 口径 3 seed + 块级 3 seed；seed 42 会顺带做复现校验）
python tools/_p1639_p3_official_igu.py --run-official --stage train \
    --config official_corrected_map,reimpl_igu_style --seeds 42,123,789

# 4) 比较（写 outputs/analysis/p3_official_vs_reimpl.json；确定性，可重跑）
python tools/_p1639_p3_official_igu.py --compare
```

**写盘边界**：`--plan`/`--self-test`/`--dry-run` **什么都不写**；`--run-official` 只写
`outputs/analysis/p3_official_igu_run.json`，而 `run_training.py` 自己会写
`paper3/scripts/outputs/experiments/verify_r1_s<seed>_bcexplicit_v*.json` 与 `verify_r1_s<seed>_b1_partial.json`：
**凡已存在的同名归档，脚本先备份、跑完再还原**，并在 `runs[].archive_preserved` 里记录（seed 42 的两个已发表归档因此不会被改）。
`--compare` 只写 `outputs/analysis/p3_official_vs_reimpl.json`。

**收尾（按仓库云端规则）**：确认进程退出 → 跑 `--compare` 断言全过 → 把
`p3_official_igu_run.json` / `p3_official_vs_reimpl.json` / 新 `verify_*.json` 全部拉回本地并核对 sha256 →
`sync && (shutdown -h now || poweroff)` → 端口探测确认不可达 → 记 HANDOFF。

---

## 7. 预声明判定规则（**跑之前**就定好，避免事后挑口径）

* **臂差距**：ΔE 差的绝对值 ≤ **0.05 × E(0) = 196.05**（沿用论文自己的 5% 等价边界；E(0)=3921.0 见归档），
  且（当 seed ≥2 时）配对 bootstrap 的 TOST 在 0.05 水平上判定等价。
* **分配一致性**：四块 rank 的 L1 距离 ≤ **2**（即 16 个 rank-layer 里的 12.5%）。
* **综合判定**：
  * `small`：臂等价 **且** 分配在容差内 ⇒ 这条 caveat 可以撤掉；
  * `mixed`：只有一条成立（**当前单 seed 归档就是这一档**：ΔE 差 −92.5 在界内，但只有一个 seed ⇒ 无区间）；
  * `large`：臂差距超出 196.05，或（有区间时）区间排除等价 ⇒ caveat 保留，块级数字只能作为单独标注的臂。

统计实现与 `tools/_p1595_p3_rank_separation.py::vqa_contrast` **逐字段一致**（`--self-test` 用同一组数、
同一 RNG 种子对比 11 个字段，全等才通过）；只有一个配对 seed 时脚本**不报区间**，而是写
`unavailable_reason`（"a single paired seed carries no bootstrap interval or TOST p-value"）。

---

## 8. 替换 caveat 的句子（英文，按判定结果二选一）

**差距小（`small`，可整条撤掉 caveat，写入 S27/S39 的正文与表注）**：

> The IGU-LoRA baseline is computed with the authors' released allocator
> (github.com/withyou12/igulora, commit 3f5ba10a) rather than a block-level reimplementation: the official
> \texttt{RankAllocator} and \texttt{SVDLoRAModule} run unmodified, and only the parameter-naming interface is
> adapted. Trained under the identical protocol (same data, epochs, learning rate, rank budget, seeds and
> evaluation), the official allocator and our block-level integrated-gradient rule differ by
> \emph{<gap>} in alignment energy (95\% CI \emph{[lo, hi]}, paired by seed; pre-declared margin 196.05 =
> 5\% of $E(0)$) and by an $L_1$ distance of \emph{<l1>} rank-layers out of 16, so the allocation-rule
> comparison is reported from the official implementation.

**差距大（`large`，caveat 保留但改写为"已量化"）**：

> The IGU-LoRA baseline is computed with the authors' released allocator (github.com/withyou12/igulora,
> commit 3f5ba10a) under the identical protocol. Its trained arm differs from our block-level
> integrated-gradient rule by \emph{<gap>} in alignment energy (95\% CI \emph{[lo, hi]}, paired by seed),
> which exceeds the pre-declared margin of 196.05 (5\% of $E(0)$); the two rules therefore do not
> substitute for each other, and the block-level numbers are reported as a separate, clearly labelled arm
> rather than as the official method.

**中间态（`mixed`，当前单 seed 证据就落在这里）**：

> The official allocator (github.com/withyou12/igulora, commit 3f5ba10a) and our block-level
> reimplementation agree on the trained-arm outcome within the pre-declared 5\% margin
> (\emph{<gap>}, \emph{<n>} paired seed(s)) but disagree on the block ranks ($L_1=\emph{<l1>}$ of 16);
> the baseline is reported from the official implementation and the rank difference is stated explicitly.

三句都由 `--compare` 写进 `outputs/analysis/p3_official_vs_reimpl.json` 的 `caveat_sentences`
（`small`/`mixed`/`large`），避免手抄数字。

---

## 9. 未能离线核实 / 需要实例确认的假设

1. **实例上是否已有 `external/igulora`**：本地有（且 sha256 已钉死），但 `external/` 被 gitignore，
   **远端仓库里没有**；实例若从未克隆过就必须跑 §2 的 clone。`--run-official` 会在 import 前检查。
2. **官方分配阶段在别的 GPU/驱动上是否逐位复现归档 per-module ranks**：脚本按 `--plan`/`--stage allocate`
   实测断言；不一致时 exit 3 而不是继续（**未在实例上验证过**，因为本任务不开机）。
3. **训练臂在新机器上是否逐位复现 +240.5 / +333.0**：论文自己已记录环境敏感性（S29/S37：r=5 均值随
   cu121/cu130 栈变化），所以脚本把 seed 42 的重跑作为**复现检查**记录（`reproduction.equal`），
   **不**硬失败；跨栈的配对差距会带 `same_stack=false` 与 `stack_mix_warning`，提示不要把该区间读成同栈区间。
4. **数据中心卡的耗时**：只有笔记本级 GPU 的实测（21–33 分钟/臂），"更快"是 `docs/p3_cloud_round_notes.md`
   的既有判断，**没有 32 GB 卡上的实测数字**（本任务不允许开机）。
5. **CLIP 模型与 marine captions 的 sha256**：脚本只检查存在性，未钉哈希（它们不是本次比较的变量；
   若实例上的 CLIP 与本地不同，分配阶段可能落到不同 per-module ranks，由第 2 条的断言兜住）。
6. `paper3/scripts/run_training.py` 的**优化器步数**未归档（S28 已有同类说明），因此"训练协议一致"
   指的是命令行参数逐项一致，而不是步数被独立核对过。