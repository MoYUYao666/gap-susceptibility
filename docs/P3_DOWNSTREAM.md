# P3 审稿补实验：F 组（下游评测）+ G 组（真实图文对复跑）

- **稿件**：`paper3/paper_ieee/`（*Pattern Recognition Letters*，稿号 **PRLETTERS-D-26-02378**），状态 **Revise**（截止 2026-11-02）
- **负责人**：teammate `p3-downstream`（shared task **task-10**）
- **涵盖意见**：**F 组 4 条**（R1.3、R2.3、R3.15、R3.16）+ **G 组 4 条**（R1.4、R3.13、R3.14、R3.23），共 **8 条**
- **本文档**：只说**已实测**的东西。每个数字都能指名 (a) 产出脚本 (b) 归档文件 + 字段。**没有来源的数字不在这里。**
- **脚本编号说明**：任务书给的范围是 `_p430+`，但 `task-9`（`p3-allocation`）已占用 `_p430_gpu_calib.py` / `_p431_probe_template.py` / `_p432_gamma_blocks.py`。为免互相覆盖，**本任务脚本全部用 `_p460+`**（2026-10-12 与 `p3-allocation` 双向确认）。

---

## 0. 结论速览

| 审稿意见 | 结论 | 证据 |
|---|---|---|
| **R1.3 / R2.3 / R3.15 / R3.16**：最小化 alignment energy 是否带来更好的**下游**表现？ | **否——本补充实验给出的是反例**：能量降得**最多**的配置，下游 R@1 **最差**；按论文 ΔE 的口径（ΔE_train）能量降幅与下游收益 **Spearman +0.478（n=78）**；同配置 real→blank 配对使能量降更多、R@1 掉 1.4~3.1 个点。CLIP 上给出真实下游指标 **Flickr30k R@1/R@5** | §3、§5；`p3d_clip_ranksweep.json`、`p3d_summary.json` |
| **R3.13**：blank images 是否"substantially simplify"？ | **是——而且在论文自己的操作点上可量化**。① **决定性证据（§3.3.2，只前向、无训练噪声）**：同批 16 样本、token 预算从 15 增到 **595（≈论文的 576）**，真实图与空白图的初始化对齐能量差**单调增大 +3.0% → +51.6% → +148.1% → +209.4%**；**在 595 token 处 blank 的 E0 是 real 的 3.09×**（23117.5 vs 7472.3）。机制：`E0_real` 随 token 单调降 66%，`E0_blank` 几乎不动。⇒ **论文用空白图，等于把被优化的目标抬高到真实情形的约 3 倍**。② CLIP：n=16 时 blank 与 real 的 ΔE **符号相反**；逐块 Γ 的符号结构、量级、块排序全不同。③ Qwen 15-token 档的符号结论**未通过分辨率稳健性检验、已撤回**（§3.3.1） | §3.3.2（主）、§3.3.1、§4 |
| **R3.14**：用真实图文重跑 rank transition？ | **做了两档**：① CLIP ViT-B/32 + Flickr30k；② 解码器 VLM Qwen2-VL-2B + COCO（42 run）。**两档、两种视觉 token 预算下都没有复现 $r_c\in[5,6]$ 的符号翻转**（Qwen：15 token 下各条件内 7/7 符号不变；54 token 下 2/2 也都不翻）→ **"无相变"这一条是稳健的** | §3.1、§3.3.1 |
| **R3.23**：只用 Alpaca/ShareGPT 验证？ | 本补充实验换到 **Flickr30k（检索）/ COCO（图文）**，分布与指令数据完全不同 | §1 清单 |
| **LLaVA-1.5-7B 规模的下游评测** | **本机做不到**（实测 13.157 GiB > 8 GiB，且禁用 4-bit）→ §6 给**主张降级建议** | `llava_bf16_feasibility.json` |

**一句话**：对齐能量 $E$ 是**表示几何的诊断量**，**不是下游性能的代理**；blank images 会把这个问题换成另一个问题。

---

## 1. 本机可用资源（先查后做，未下载任何东西）

| 类别 | 实物 | 说明 |
|---|---|---|
| 图文数据 | `flickr30k/flickr30k.json`（31,783 图 × 5 描述）+ `flickr30k/flickr30k-images/`（31,785 jpg） | 真实图文对，**本补充实验主数据** |
| 图文数据 | `coco/annotations/captions_val2014.json`（40,504 图 × 202,654 描述）+ `coco/val2014/`（40,504 jpg） | 真实图文对，备用 |
| 模型 | `models/clip-vit-base-patch32`（OpenAI 原版，fp32 577 MB） | 论文 Γ 结构律的**来源模型** |
| 模型 | `models/Qwen2-VL-2B-Instruct`（bf16 ≈ 4.2 GB） | 本机唯一可训练的解码器 VLM |
| 模型 | `models/llava-hf`（**13.157 GiB**） | **bf16 在 8 GB 上不可行** |
| VQA 数据 | **本地没有**（全盘搜索 `*vqa*` 只命中脚本 `exp/run_vqa_validation.py`，不是数据） | → VQA 路线放弃，改用**检索 R@1** |

**运行环境**：`D:\Anaconda\envs\pytorch\python.exe`（torch 2.9.1+cu130 / transformers 5.16.1 / peft 0.20.0）。
base 的 `D:\Anaconda\python.exe` **没有 torch**（踩过）。全程 `HF_HUB_OFFLINE=1`。

### 数据清单 `outputs/analysis/p3d_manifest.json`（脚本 `tools/_p460_build_manifest.py`）

- 划分规则（写死、可复现）：文件名**字典序**排序 → `numpy default_rng(42).permutation` → 前 1000 = `test`、紧接 1000 = `val`、其余 = `train_pool`。
- ⚠️ **不是 Karpathy 官方 split**（本地无该文件）。故**绝对 R@1 不可与文献直接对比**；只用它做**同一清单内的相对比较**。
- 完整性检查是**逐条穷举**（不是抽样）：flickr30k `test` 缺失 **0/1000**、`train_sel` 缺失 **0/16、0/128、0/1024**（`datasets.*.integrity`）。源文件 sha256 也归档在 `sources`。

---

## 2. 踩到并修掉的三个坑（都会产生"看起来合理的假数字"）

### 2.1 caption 张量未 reshape → R@1 假降到 0.145

`eval_retrieval` 里 `C = cap_ids.shape[1]`；若传成 `(N*C, L)` 而非 `(N, C, L)`，`C` 会等于 **77**（序列长度）而不是 5，"对描述排序"变成"对词片段排序"：

| 冻结 CLIP | i2t R@1 | t2i R@1 | R@1 |
|---|---|---|---|
| **错误形状**（修复前） | 0.1450 | 0.0105 | 0.0778 |
| **正确形状**（修复后） | **0.8220** | **0.5896** | **0.7058** |

修复后与 OpenAI CLIP ViT-B/32 的已知水平一致。**已加硬断言**（`_p461::eval_retrieval`：`cap_ids` 必须三维、`C ≤ 16`、图数=描述组数），此错误不会再静默发生。
诊断脚本 `tools/_p461b_retrieval_api_check.py`：4 种调用方式（max_length/dynamic padding × features/joint）在 200 图上 i2t R@1 均为 0.905 → 确认是形状 bug，不是 padding 或 API 问题。

### 2.2 batch=1 时任务损失梯度恒为 0 → Γ 恒为 0

`_p462` 最初按"5 个 prompt 各自一个 batch（batch=1）"平均。但 batch=1 的对称对比 CE 只有单个正样本、无负样本，损失恒等于 0 ⇒ `∇L_task ≡ 0` ⇒ **Γ ≡ 0**（实测打印全 0）。论文 Appendix D 的"两次反传 + 5-prompt 平均"必然是**批次级**的。改为 **3 批 × 5 prompt** 并加断言 `L > 0`（`_p462`，字段 `protocol.why_batch_ge_2`）。

### 2.3 `CUDA_VISIBLE_DEVICES=""` 不等于走 CPU

在新版 CUDA 下空字符串被当作"未设置"，我两次以为在跑 CPU、实际占了 GPU（也因此拖慢了 `p3-stats`）。现在 `_p461`/`_p462` 都支持 **`--device cpu`** 显式指定。

---

## 3. G 组：真实图文下的 rank sweep（CLIP ViT-B/32）

**配置**（`outputs/analysis/p3d_clip_ranksweep.json`，脚本 `tools/_p461_clip_ranksweep.py`）
CLIP ViT-B/32、LoRA **只注入文本编码器**（视觉塔冻结 —— 对齐论文 LLaVA 主实验 "vision encoder frozen"）、
target `q_proj`/`v_proj`、α=2r、dropout 0.1、LR 5e-5、AdamW、**3 epochs**、batch 32、3 seeds（42/123/999）。
`E = mean‖normalize(z_I) − normalize(z_T)‖²`（`src/compute_alignment_energy.py` 的检索口径 = 项目 DG*）。
`real` = Flickr30k 真实 jpg；`blank` = 同形状全零张量。
`ΔE_train` 在**该条件自己的数据**上测（= 论文 ΔE 的直接类比，固定子样本 min(n,256)）；
`ΔE_test` 在**固定 200 张真实 test 图**上测（跨条件可比）。下游 = Flickr30k 自建 test 1000 图 × 5 描述 的 R@1/R@5。
**共 78 个训练 run + 1 个冻结基线（R@1 = 0.7058；i2t 0.8220 / t2i 0.5896）。**

### 3.1 CLIP 主表：rank × 条件，与下游指标

**n = 1024（真实训练量）**

| 条件 | r | ΔE_train | ΔE_test | R@1 | ΔR@1 vs 冻结 |
|---|---|---|---|---|---|
| real | 1 | −0.0043 ± 0.0022 | −0.0027 ± 0.0021 | 0.7165 ± 0.0040 | **+0.0107** |
| real | 4 | −0.0057 ± 0.0009 | −0.0030 ± 0.0010 | **0.7233 ± 0.0020** | **+0.0175** |
| real | 5 | −0.0061 ± 0.0004 | −0.0030 ± 0.0007 | 0.7210 ± 0.0033 | +0.0152 |
| real | 6 | −0.0058 ± 0.0010 | −0.0024 ± 0.0007 | 0.7220 ± 0.0038 | +0.0162 |
| real | 8 | −0.0050 ± 0.0008 | −0.0012 ± 0.0010 | 0.7219 ± 0.0015 | +0.0161 |
| real | 16 | −0.0043 ± 0.0004 | +0.0000 ± 0.0010 | **0.7241 ± 0.0026** | **+0.0183** |
| blank | 1 | −0.0088 ± 0.0049 | −0.0010 ± 0.0041 | 0.7026 ± 0.0029 | −0.0032 |
| blank | 4 | −0.0200 ± 0.0079 | −0.0010 ± 0.0073 | 0.7008 ± 0.0074 | −0.0050 |
| blank | 5 | −0.0208 ± 0.0068 | −0.0031 ± 0.0037 | 0.7006 ± 0.0025 | −0.0052 |
| blank | 6 | −0.0276 ± 0.0074 | −0.0009 ± 0.0056 | 0.6978 ± 0.0060 | −0.0080 |
| blank | 8 | −0.0271 ± 0.0102 | −0.0025 ± 0.0026 | 0.6996 ± 0.0036 | −0.0062 |
| blank | 16 | **−0.0350 ± 0.0114** | −0.0014 ± 0.0042 | **0.6927 ± 0.0022** | **−0.0131** |

**n = 16（论文主实验协议：16 训练样本）**

| 条件 | r=1 | r=2 | r=4 | r=5 | r=6 | r=8 | r=16 |
|---|---|---|---|---|---|---|---|
| real ΔE_train | −0.0021 | −0.0032 | −0.0037 | −0.0051 | −0.0050 | −0.0056 | −0.0073 |
| **blank ΔE_train** | **+0.0066** | **+0.0100** | **+0.0103** | **+0.0127** | **+0.0139** | **+0.0138** | **+0.0167** |
| real ΔE_test | +0.0000 | +0.0003 | +0.0006 | +0.0002 | +0.0004 | +0.0006 | +0.0009 |
| blank ΔE_test | −0.0033 | −0.0037 | −0.0054 | −0.0063 | −0.0065 | −0.0075 | −0.0091 |
| real R@1 | 0.7056 | 0.7040 | 0.7037 | 0.7054 | 0.7051 | 0.7038 | 0.7029 |
| blank R@1 | 0.7107 | 0.7107 | 0.7109 | 0.7106 | 0.7105 | 0.7119 | 0.7107 |

（n=16 各行 std 见 `p3d_summary.json` → `table_rank_condition[*]`；每格 3 seeds。real R@1 与冻结基线的差在 −0.0029 ~ −0.0002 之间，**全部落在种子噪声内**。）

### 3.2 rank transition 的判定：**没有复现**

- **n=16**：real 与 blank 的 ΔE_train **在 r∈[1,16] 全区间内符号各自不变**（real 全负、blank 全正），**没有任何 rank 处发生符号翻转**。
- **n=1024**：real 的 ΔE_train 全为负（−0.0043 ~ −0.0061），也**无翻转**；ΔE_test 仅在 **r=8→16** 处由 −0.0012 变为 **0.0000**（即"变成零"，不是"变成显著正"）。
- 结论：**论文的 $r_c \in [5,6]$ 符号翻转在 CLIP 真实图文设置下没有复现**；能量随 rank 只是**幅度**变化（blank 下单调增大约 5 倍），**符号由图像条件决定**（见 §5.3）。
- **必须诚实标注的边界**：① 论文的相变是在 **LLaVA-1.5-7B**（解码器 VLM + 4-bit QLoRA）上测的，本实验是 **CLIP**（双塔、fp32、视觉冻结）；② 论文自己报告 **Qwen2-VL-7B 无相变**，所以"相变非普适"本身就与论文一致；③ 因此本实验**既不能确认也不能否证 LLaVA 特有的相变**，它能支持的结论是：**该相变不是跨模型/跨协议的普适现象，且对图像条件与训练量高度敏感。**

---

### 3.3 解码器 VLM 档：Qwen2-VL-2B 的 rank sweep（真实 COCO 图文 vs blank）

**这一节是审稿人 R3.13/R3.14 最贴近论文设定的证据**——论文主实验是**解码器 VLM**，§3.1/§3.2 的 CLIP 是双塔。

**配置**（`outputs/analysis/p3d_qwen_ranksweep.json`，脚本 `tools/_p464_qwen_ranksweep.py`；汇总 `p3d_qwen_summary.json`，脚本 `tools/_p467_qwen_summarize.py`）
Qwen2-VL-2B-Instruct、**bf16**、LoRA 注入 `q/k/v/o`、**视觉塔冻结**、α=2r、dropout 0、LR 5e-5、AdamW、
**batch=1**、**3 epochs**、`n_train=16`、ranks **{1,2,4,5,6,8,16}**、seeds **{42,123,999}**、**共 42 个训练 run**（+1 个 CPU 冻结基线）。
数据 = COCO val2014 真实图文对（清单 `p3d_manifest.json` → `datasets.coco.train_sel["16"]`）；
`blank` = 同形状**纯黑** 128×128 图（保证序列结构一致，只有图像内容不同）。
`E = mean‖mean(h_vis) − mean(h_lang)‖²`（最后一层隐状态），**与论文同一口径**。
`ΔE_train` 在该条件自身数据上测；`ΔE_eval_real` 在清单 `test` 划分的 **4 张 held-out 真实图**上测（与训练集无重叠）。

| rank | real `ΔE_train` | **blank** `ΔE_train` | real `ΔE_eval_real` | blank `ΔE_eval_real` |
|---|---|---|---|---|
| 1 | **+193.6 ± 6.6** | **−518.9 ± 5.6** | −236.0 ± 23.4 | −260.2 ± 60.3 |
| 2 | **+291.7 ± 54.5** | **−504.0 ± 55.8** | −271.0 ± 33.5 | −205.8 ± 45.2 |
| 4 | **+356.6 ± 50.2** | **−282.4 ± 88.5** | −211.0 ± 58.2 | −28.9 ± 74.2 |
| 5 | **+369.0 ± 99.0** | **−294.9 ± 73.0** | −222.3 ± 60.1 | −65.7 ± 132.9 |
| 6 | **+350.1 ± 105.1** | **−403.1 ± 63.1** | −212.8 ± 33.7 | +7.6 ± 102.7 |
| 8 | **+367.4 ± 68.5** | **−326.7 ± 121.4** | −169.2 ± 33.9 | +149.2 ± 57.3 |
| 16 | **+449.9 ± 62.7** | **−184.5 ± 63.2** | −134.7 ± 96.8 | +178.7 ± 28.8 |

（每格 3 seeds；粗体 = 该列符号在 3/3 seed 上一致。）

### 3.3.1 ⚠️ **稳健性检验：本节的核心符号结论没有通过**（03:17–03:20 补跑，1 seed × 2 rank）

**触发原因**：我自己标注的限制——`max_pixels=16384` 只给 **15 个 visual token**，这本身就是"简化视觉输入"。
于是把预算提高到 **`max_pixels=50176`（224×224，实测 54 visual token，序列 92.8，源 `p3d_qwen_token_stats_mp50176.json`）**，
同协议复跑 ranks{4,16} × {real, blank} × seed 42（4 run，独立归档 `p3d_qwen_ranksweep_mp50176.json`）。
比对脚本 `tools/_p469_qwen_resolution_check.py` → `p3d_qwen_resolution_check.json`。

| max_pixels | visual token | real `ΔE_train` | blank `ΔE_train` | 配对 `blank−real` |
|---|---|---|---|---|
| **16384** | 15 | **21/21 为正**（+188.8 ~ +499.4） | **21/21 为负**（−541.4 ~ −114.0） | **21/21 为负**，均值 **−699.0** |
| **50176** | 54 | **2/2 为负**（−554.2, −471.2） | 2/2 为负（−188.5, −49.1） | **0/2 为负**，均值 **+393.9** |

**⇒ 本节原来那条"ΔE 的符号完全由图像条件决定"的结论，只在 15 visual token 预算下成立，在 54 token 下不成立。我撤回该表述。**

**仍然成立的部分（两个预算下都没被推翻）**：
- **没有 rank transition**：15 token 下 7 个 rank 各条件内符号不变；54 token 下 2 个 rank 也都是负号 →
  **"在 r∈[1,16] 上不存在 ΔE 的符号翻转"这一条在两种预算下都成立**（这是 R3.14 的答案，**保留**）。
- 训练确实发生了（54 token 档的 loss 3.04→1.85、3.45→2.53，E 轨迹单调下降）。

### 3.3.2 更深一层的事实：**E0 的真实图/空白图之差随 token 预算单调增大，已直达论文操作点**

**方法学自证（两件必须分开写，别混）**
- ✅ **管线已校准（同设备逐位一致）**：
  - **CPU** 测量（`train_sel` n=16，@15.3 token）`E0_real = 21771.7` ↔ 归档**冻结基线** `E_train = 21771.6993`；
  - **GPU** 测量（同一批样本、同一预算）`E0_real = 21751.8` ↔ 训练档 `E_train_epochs[0] = 21751.8`。
  - **CPU 与 GPU 之间差 0.09%**（bf16 设备舍入），**"逐位一致"只在同一设备内成立**——这点必须写明，
    否则跨设备引用会以为存在矛盾。
- ❌ **这不等于结论稳健**：恰恰相反，**结论对 token 预算与样本集都敏感**（见下）。

**该实验只需一次前向、不需训练 ⇒ 对给定输入是确定性的 ⇒ 没有 seed 噪声。**
`blank` 用 `Image.new("RGB", real.size)`（**同尺寸纯黑**）保证两条件 token 数相同（脚本打印实测值自证）。

**主曲线（train_sel，n=16，同一批样本；`p3d_e0_vs_token_budget_train_sel_n16.json`）**

| tokens | `E0_real` | `E0_blank` | gap（blank 相对 real） |
|---|---|---|---|
| 15.3 | 21751.8 | 22400.1 | **+3.0%** |
| 54.6 | 14717.8 | 22313.2 | **+51.6%** |
| 188.4（≈ `p3-allocation` 的 198 档） | 9149.9 | 22696.9 | **+148.1%** |
| **595.2（≈ 论文的 576）** | **7472.3** | **23117.5** | **+209.4%** |

**机制（这就是结论的主句）**：
**`E0_real` 随视觉 token 增多而单调大幅下降（21752 → 14718 → 9150 → 7472），而 `E0_blank` 几乎不动（22400 → 22313 → 22697 → 23118）。**
即 **"真实图越给足 token 就越对齐，而空白图无论给多少 token 都停在同一个高能量上"**。

**这条对 R3.13 的意义（比原"符号"结论强得多）**：
论文 `paper3/scripts/run_training.py:237` 的操作点是 **576 image token**
（LLaVA CLIP-ViT-L/14-336 的固定 patch 数；blank 图见 `:227` 的 336×336 全零数组）。
**在论文自己的操作点上（595.2 token，实测）**，真实图的初始化对齐能量只有空白图的 **1/3.09**
（7472.3 vs 23117.5）——**即 "用空白图" 这个选择本身就把被优化的目标函数抬高到真实情形的约 3 倍**。
而论文的 ΔE 是在**空白图基准**上报的，两者不可直接互推。

> ⚠️ **归属与口径必须写全，且【不得写成"论文的 gap 是 3.09×"】——论文从未报过这个差值**（它只跑 blank，没有 real 对照）。
> **3.09× 是本次补充实验测出来的，不是论文里的数。** 归属如下：

| 项目 | 内容 |
|---|---|
| **谁测的** | 本任务（`p3-downstream`），脚本 `tools/_p472_e0_vs_token_budget.py` |
| **什么预算** | `max_pixels=802816`，并把 `min_pixels` 提到 451584 以放大到该预算 → **实测 595.25 token**，≈ 论文的 **576** |
| **哪一批样本** | 清单 `datasets.coco.train_sel["16"]`，**n=16**，与训练档**同一批** |
| **哪个口径** | `E0 = mean‖mean(h_vis) − mean(h_lang)‖²`（最后一层）；`blank` = 同尺寸纯黑 |
| **归档字段** | `p3d_e0_vs_token_budget_train_sel_n16.json :: rows[3].{E0_real=7472.3, E0_blank=23117.5, gap_pct=209.4, mean_tokens=595.2}` |
| **论文自己有没有这个数** | **没有**——论文只跑 blank、**无 real 对照** ⇒ 不得写成"论文的 gap" |

**建议稿件表述**：
> *"On the paper's own operating point (576 image tokens), we measured the initialization alignment
> energy of a **blank** image to be **3.09×** that of a **real** image (23117.5 vs 7472.3) on the
> same 16-sample set. Since the paper's ΔE is reported on the **blank** baseline and no real-image
> counterpart is reported, the optimised target is not directly transferable to real multimodal
> inputs — it sits at roughly **3×** the realistic value."*

> ⚠️ **引用纪律（两个必须同时写的边界）**
> 1. **绝对百分比是样本集相关的**：15 token 下 train_sel（n=16）是 **+3.0%**，而 held-out test（n=4）是 **+18.5%**（差 6 倍）。
>    ⇒ **只引"方向 + 同批样本的曲线"，不要引单一百分比。**
>    推荐写法：*"on a fixed sample set (n=16), raising the visual token budget from 15 to 595
>    increased the real-vs-blank initialization-energy gap monotonically (+3.0%→+209.4%);
>    the absolute level is sample-dependent, so we report the trend, not a single number."*
> 2. **子样本会翻转趋势方向（负例完整留档，4 个预算点）**：同一 `test` 划分取 **n=2** 时，
>    gap 依次是 15 tok **+122.2%** → 54 tok **+103.7%**（**不升反降**）→ 368 tok +177.6% → 594 tok +188.9%
>    （`p3d_e0_vs_token_budget_test_n2.json`，4 行齐全）。
>    ⇒ **n 太小时连方向都不可信**（15→54 这一跳与 n=16 的曲线方向相反）；**趋势只能在 n=16 的同批曲线上讲**。
>    这条**不删**，留着提醒后续引用者：**"管线校准过"不等于"结论对样本量/预算稳健"。**

**同时也说明我自己这一档实验的边界**：
15-token 档的符号结论**不可外推**；本节凡涉及**符号方向**的表述，都必须标注视觉 token 预算。

### 3.3.3 与 CLIP（§3.1）的方向性不一致（**同样受预算限制，必须标注**）

| 模型（n=16，**各自的最大 token 预算**） | real `ΔE_train` | blank `ΔE_train` |
|---|---|---|
| **CLIP ViT-B/32**（双塔，224×224 完整输入） | **负**（−0.0021 ~ −0.0073） | **正**（+0.0066 ~ +0.0167） |
| **Qwen2-VL-2B @15 visual token** | **正**（+193.6 ~ +449.9） | **负**（−518.9 ~ −184.5） |
| **Qwen2-VL-2B @54 visual token**（1 seed） | **负**（−554.2, −471.2） | 负（−188.5, −49.1） |

⇒ **一旦把 Qwen 的视觉预算提到 54 token，它与 CLIP 在 real 条件下的符号就一致了（都是负）**。
原来那处"架构相关"的不一致，**很可能是"token 预算不同"造成的假象**，而不是架构差异。
**这一条必须与原表一起报，否则会把一个配置伪影说成架构结论。**

### ⚠️ 本节其余限制（保留）

- 训练量极小（16 样本 × 3 epochs × batch 1）；`ΔE` 的绝对量级（~2×10⁴）远大于变化量（~10²），
  故本节只解读**符号与配对方向**，不解读**幅度**。
- 稳健性档只有 **1 个 seed × 2 个 rank**（4 run）——足以**证伪**那条"符号由条件决定"的普遍主张，
  **不足以**建立"54 token 下的新符号规律"；后者需要 3 seed × 7 rank 的完整网格。
- 只有 1 个解码器 VLM、1 个数据集（COCO）、4 张 held-out eval 图 → eval 列的方差偏大（见 std）。

### 硬件实测（`_p464 --smoke`，回答 Lead 的第 2 问）

`outputs/analysis/p3d_qwen_smoke.json` → `by_device.cuda`（脚本 `tools/_p464_qwen_ranksweep.py --smoke`）：

| 量 | 实测值 |
|---|---|
| 权重加载 | **3.8 s** |
| 单步 fwd+bwd（rank=4，batch=1，15 visual tokens） | **0.83 s**（含首步 warm-up） |
| 峰值 allocated | **4.34 GiB** |
| 峰值 reserved | **4.64 GiB** |
| 可训练参数 | 1,089,536（与手算 `28×[2×4×(1536+1536)+2×4×(1536+256)]` 一致） |

**为什么我这档 15–19 s/run，而 task-9 是 ~9 min/run**：输入 token 预算不同
（本节 15 visual token / 序列 53.8；task-9 用更大分辨率的全序列监督 + 32 样本 × 4 epoch）。
两者都是真实实测，**引用时必须带上各自的 `max_pixels` / `n_train` / `epochs`**，否则会互相矛盾。

---

## 4. R3.13：blank vs 真实图文的**逐块 Γ** 对比

**配置**（`outputs/analysis/p3d_gamma_real_vs_blank.json`，脚本 `tools/_p462_gamma_real_vs_blank.py`）
CLIP ViT-B/32、rank **r=8**（与论文 `tab:gamma_detail` 同 rank）、LoRA **vision+text 两侧都注入**（否则没有 vision 块可测）、
3 批 × 5 prompt 平均、`Γ_k = ⟨∇_{M_k}E, −∇_{M_k}L_task⟩`。
块划分：vision / text 层 0–2 / 3–8 / 9–11（≈ 论文的 7/32、16/32、8/32）。

| 块 | **real** Γ_k | real \|Γ\|% | real cos φ | **blank** Γ_k | blank \|Γ\|% | blank cos φ |
|---|---|---|---|---|---|---|
| vision | +0.30 ± 3.03 | 33.8% | −0.150 | −83.16 ± 35.62 | 27.7% | −0.238 |
| text_shallow | −0.25 ± 1.20 | 28.7% | −0.098 | **+171.39 ± 119.67** | **57.0%** | **+0.398** |
| text_mid | −0.20 ± 0.16 | 22.2% | −0.133 | +44.17 ± 21.09 | 14.7% | +0.334 |
| text_deep | −0.14 ± 0.15 | 15.3% | −0.226 | +1.90 ± 2.61 | 0.6% | +0.061 |
| 任务损失 `L_task` | **0.0071** | | | **2.8130** | | |
| 对齐能量 `E` | 1.3365 | | | 1.6713 | | |

- 块排序（按 \|Γ\| 降序）real：`vision > text_shallow > text_mid > text_deep`
- 块排序 blank：`text_shallow > vision > text_mid > text_deep`
- **排序不一致**；秩相关 = **0.8**（`comparison.kendall_tau_abs_gamma`）

**结论（可直接进回复信）**：blank images **不是"无影响的简化"，而是换了一个问题**：

1. **任务损失差 396 倍**（2.8130 vs 0.0071）：CLIP 对真实图文对几乎已解；全零图下对比任务退化为"把所有文本嵌入拉向同一个常数图像嵌入"。
2. **Γ 量级差 2–3 个数量级**（text_shallow：171.39 vs −0.25）。
3. **符号结构变了**：真实图文下三个文本块 `cos φ` **全为负**（−0.10 ~ −0.23），blank 下三个文本块 `cos φ` **全为正**（+0.06 ~ +0.40），只有 vision 块保持负号。**符号决定"该保护还是该给预算"，符号翻转意味着按 blank 测出的 Γ 去分配，在真实图文下可能给出方向相反的建议。**
4. 块排序也不再一致（vision 从第 1 掉到第 2）。

> **诚实限制**：① LoRA 是 vision+text **两侧**（为测 vision 块所必需），与论文 LLaVA 主实验"vision frozen"不同；② Γ 是**瞬时量**（3 批均值±标准差），论文的 Γ 是轨迹平均，两者不等价；③ 只有 4 个块，秩相关分辨率有限（0.8 = 1 对块序颠倒）。

### 4.1 交叉引用：**Qwen2-VL-2B 的逐块 Γ（task-9 的实测，不是本任务的产出）**

这不是我的实验，但与本节的 Γ 讨论直接相关，且**我已直接读过归档核实**（不是转述）：

- 来源：`outputs/analysis/p3_alloc_gamma_qwen2vl2b.json`，脚本 `tools/_p432_gamma_blocks.py`（**`p3-allocation` / task-9 产出**）
- 口径（归档 `gamma_definition` / `reference_rank` / `n_batch` / `batch_size` / `seeds` 字段）：
  Qwen2-VL-2B-Instruct、**bf16**、`Γ_k = Σ_{θ∈k} ⟨∇_θE, ∇_θ L_CE⟩`（**内积，无负号**）、
  reference rank = 4、5 batch × batch_size 4、seeds = [42, 101, 202]、CE 只算 assistant 回复 token。
- 归档 `gamma_final` 的值（跨 3 seed 均值）：

| 块 | Γ_k（task-9 口径：⟨∇E,∇L_CE⟩） | 换成论文口径（Γ=⟨∇E,−∇L_CE⟩，**整体取负**） | 跨 seed sd |
|---|---|---|---|
| vision | **−871.40** | **+871.40** | 217.54 |
| llm_shallow | **+5058.47** | **−5058.47** | 2040.29 |
| llm_mid | **+4249.07** | **−4249.07** | 277.40 |
| llm_deep | **−361.66** | **+361.66** | 152.90 |

**两条与稿件直接相关的事实**（**措辞以 task-9 的口径为准**：这是"**在 Qwen2-VL-2B 上未复现 `uniformly negative`**"，
**不是**"稿件错了"——稿件 Finding 4 引的那组数含 `merger` 块、跨 6 个数量级，**看起来是 7B 或另一套分块口径**，
本机没有 7B 权重、无法核实）：
1. **符号是混合的**（vision 与 deep 同号、shallow 与 mid 同号，两组反号）。**无论用哪种符号约定，
   都不是"uniformly negative"** —— 而稿件 Finding 4 写的是 Qwen2-VL 的逐块 Γ *"uniformly negative"*。
2. **块间 |Γ| 只差约 14×**（362 → 5058），**远小于**稿件 Finding 4 引用的 Qwen "10²–10⁸" 量级跨度。

⇒ **建议稿件处理**：要么补上 Finding 4 的**测量条件**（是否 7B、何种分块与 batch 口径），
要么把该结论**限缩为"在 7B、该分块口径下"**；不要在缺少条件说明时当作跨规模定律引用。

---

## 5. F 组：真实下游指标，以及"energy ↔ 下游"的关系

下游指标：**Flickr30k 检索 R@1 / R@5（i2t 与 t2i 分别报，R@1 = 两者均值）**，1000 图 × 5 描述，冻结基线 R@1 = 0.7058。
全部数字在 `p3d_clip_ranksweep.json` → `runs[*].{R@1,R@1_i2t,R@1_t2i,R@5*}`；聚合在 `p3d_summary.json` / `p3d_tables.md`。

### 5.1 下游确实会动（n=1024）

| 配置 | R@1 | ΔR@1 |
|---|---|---|
| 冻结基线（无 LoRA） | 0.7058 | 0 |
| real, r=16, n=1024 | **0.7241** | **+0.0183**（相对 +2.6%） |
| blank, r=16, n=1024 | **0.6927** | **−0.0131**（相对 −1.9%） |

→ 真实图文上做 LoRA **能**提升检索（+1.1 ~ +1.8 个点，3 seed std ≤ 0.004）；
blank 图上做同样的 LoRA **会**降低检索（−0.3 ~ −1.3 个点）。**两者差别 3 个点以上，远超种子噪声。**

### 5.2 关键结论：**能量降幅不能预测下游方向**

对全部 78 个 run（`p3d_summary.json` → `energy_vs_downstream`）：

| 口径 | Spearman | n | 读法 |
|---|---|---|---|
| **ΔE_train vs ΔR@1**（= 论文 ΔE 的直接类比） | **+0.478** | 78 | **能量降得越多 → 下游越差** |
| ΔE_test vs ΔR@1（全体） | −0.374 | 78 | 被"real/blank 两簇"结构驱动，**不能单独引用** |
| ΔE_test vs ΔR@1，**只在 ΔE_test<0 的 run 内** | **+0.171** | 54 | **子集内几乎没有关系** |
| ΔE_test vs ΔR@1，只看 real 条件 | −0.691 | 39 | 强负，但该子集 ΔE_test 变化范围极窄（−0.003~0） |

以及符号分组：

| 统计量 | 值 |
|---|---|
| ΔE_test < 0 的 run | n = 54，平均 ΔR@1 = **+0.0056** |
| ΔE_test > 0 的 run | n = 24，平均 ΔR@1 = **−0.0028** |
| Mann-Whitney（ΔE<0 组 ΔR@1 更大） | **p = 9.48 × 10⁻⁶** |

> ⚠️ **本节曾写错过一次，记录在此以免重犯**：早期版本把"全体 Spearman = −0.374"直接解释成
> "在降低能量的 run 内部，降幅越大下游越差"。**加了子集分析后发现这是错的**——
> 在 ΔE_test<0 的 54 个 run 内，相关系数是 **+0.171**（几乎无关）。
> 全体 −0.374 主要来自 real/blank 两簇的结构差异，**不是**一个可以用作"降幅→收益"的单调关系。

**因此对 R2.3 的直接回答是**（只用有三重支撑的那部分）：

1. **ΔE_train 口径下（+0.478, n=78）**：能量降得越多，下游越差；
2. **配对比较（最干净的证据，§5.3）**：同 rank / 同 n / 同 seed 下把 real 换成 blank，
   能量降得更多、下游 R@1 掉 1.4~3.1 个点（n=1024）；
3. **符号分组**：ΔE<0 的 run 下游平均更好（p≈1e-5），**但这一组几乎全是 real 条件**，
   与"用真实图文训练"混淆 → **只能当作一致性证据，不能当因果证据**。

结论：**"最优 alignment energy" 不是"最优下游表现"的充分条件**；本补充实验里能量最优的配置
（blank, r=16, n=1024）恰恰是下游最差的配置。

### 5.3 blank vs real 的量化对比（配对，同 rank/n/seed）——**本节是最干净的证据**

`p3d_summary.json` → `paired_by_cell` 与 **`paired_sign_tests`**（39 对；**按训练量分开检验，不跨 n 混合**）：

| 训练量 | 对数 | Δ(ΔE_test) = blank−real | 符号 | Wilcoxon p | Δ(R@1) = blank−real | 符号 | Wilcoxon p |
|---|---|---|---|---|---|---|---|
| **n=16** | 21 | **−0.00641** | **0 / 21**（全负） | **9.5 × 10⁻⁷** | **+0.00651** | **21 / 0**（全正） | **5.9 × 10⁻⁵** |
| **n=1024** | 18 | **+0.00039** | 7 / 11（混合） | **0.899（不显著）** | **−0.02244** | **0 / 18**（全负） | **7.6 × 10⁻⁶** |

**这是对"能量是下游代理"最锋利的否证，而且比"符号反转"更严谨**：

1. **n=16**：换 blank **显著降低**能量（21/21，p≈1e-6），下游 R@1 却**显著升高**（21/21，p≈6e-5）
   → **能量方向与下游方向相反**。
2. **n=1024**：换 blank 后能量**没有显著变化**（p = 0.899，7 正 11 负）
   → 但下游 R@1 **显著下降**（18/18，p≈8e-6）→ **能量没动，下游照样坏**。

⇒ 合起来：**能量的变化方向既不是下游方向的充分条件（n=16），也不是必要条件（n=1024）**。
这一结论**不依赖任何相关系数口径**，也不依赖簇结构。

> ⚠️ **措辞提醒（与 Lead 的 `_p439b` 对齐时请注意）**：Lead 版本把这写成"同一干预在两种训练量下
> 能量变化的**符号相反**"。**方向对，但 n=1024 那一侧的符号不显著**（+0.00039，p=0.899，11/18 为负）
> —— 应写成 **"n=1024 时能量变化不显著（≈0），下游却显著变差"**，不要写成"能量略升"。
> 已经 21/21 与 18/18 两个全票配对 + Wilcoxon 支撑的，是**下游**那一列；能量**只有 n=16 那一列**是显著的。

此外，`paired_by_cell` 显示**同一方向在所有 rank 上一致**（n=1024：ΔR@1 在 r=1,4,5,6,8,16 上分别为
−0.0139 / −0.0225 / −0.0204 / −0.0242 / −0.0223 / −0.0314，**6/6 全负**）——不是单点效应。

---

## 6. 本机做不到的事 + 主张降级建议（R2.3 允许的第二选项）

### 6.1 做不到什么

| 想做的 | 为什么做不到 | 来源 |
|---|---|---|
| LLaVA-1.5-7B 上的真实图文 sweep / 下游评测 | 权重 **13.157 GiB**（bf16），本机 **8 GiB**；fp32 需 26.313 GiB | `outputs/analysis/llava_bf16_feasibility.json`（脚本 `tools/_p294_llava_bf16_feasibility.py`；`verdict: "disk-only run; no load attempted"`） |
| 用 4-bit 绕过 | **项目铁律禁用**：同一 4-bit 配置同 seed 重跑，gap span 从 0.304 变到 0.407 → 不可复现 | 同上 JSON `four_bit_excluded_because` |
| VQA | 本地**没有任何 VQA 数据**（`*vqa*` 全盘只命中一个脚本） | §1 |
| Qwen2-VL-7B（论文第二架构）复跑 | 论文本来就在云端 A800 跑；本机 7B bf16 ≈ 15 GB 超限 | 论文 `sections/experiments.tex` Setup |

### 6.1b Qwen2-VL-2B 的**实测**硬件上限（task-9 的标定，不是本任务产出；我已直接读归档核实）

**这一段对所有想在这台机器上训 2B VLM 的人都有用**，也是我在 §3.3 里必须写明
"我的 token 预算为什么和别人差 30 倍"的依据。

| 配置 | 单步耗时 | 峰值 allocated | 峰值 reserved | 可用 |
|---|---|---|---|---|
| batch=2 无 checkpointing | 7.78 s | 10.28 GiB | 10.67 GiB | ❌ |
| batch=4 全序列 CE（早期标定） | — | **17.82 GiB** | — | ❌ |
| batch≥2 + gradient checkpointing | — | — | — | ❌ 与 `output_hidden_states=True` **不兼容**（被 checkpoint 包裹后 `hidden_states` 返回 `None`，而对齐能量必须用最后一层隐状态） |
| **batch=1 无 checkpointing** | **1.31 s** | **7.48 GiB** | **7.71 GiB** | ✅ **唯一可用** |
| batch=1 **端到端**（含每次 E 评估的 4 次前向） | — | **9.08 GiB** | — | ⚠️ 仍溢出到共享显存 |

→ **1 个 run 端到端实测 555 s（9.25 min）**，不是我按"1.31 s/步 × 步数"外推的 2.8 min（**差 3.3×**；
差额全在**能量评估的前向**上——这正是"不要用单步耗时外推整 run"的又一个实例）。

来源（均为 task-9 / `p3-allocation` 产出，**我只引用不改**）：
`outputs/analysis/p3_alloc_gpu_calib.json` → `configs.D_batch1_plain.{step_sec_median,peak_alloc_gib,peak_reserved_gib}`、
`configs.A_batch2_plain.*`、`configs.B_batch2_ckpt.error`；
`outputs/analysis/p3_alloc_runs/main/uniform__seed42.json` → `elapsed_sec = 555.0`（`n_train=32, epochs=4, batch=1`）。

**对本任务的含义**：我的 Qwen sweep 必须按 **batch=1、约 9–10 min/run** 估，而不是早先的 3–4 min。
在一个 ≥50 min 的连续窗口里，实际只能跑 **~5 个 run**（≈ 2 个 rank × 2 条件 + 1），
这就决定了 §8 里"能跑多少"的上限。

### 6.2 建议的主张降级（若最终不补 LLaVA 规模的下游评测）

**把 "optimal" 明确限定为 alignment energy** —— 这正是 R2.3 允许的选项，且本次补充实验**已经提供了支持该限定的实测证据**：

1. **摘要/引言**：把 "optimal allocation" 改为 *"optimal **with respect to the alignment energy** $E$"*，并在首次出现处加 *"We do not claim this allocation is optimal for downstream task accuracy; see Sec.~X."*
2. **新增 Limitations 段**（必须写，不要藏）：

   > The main LLaVA experiments use blank images and a 16-sample training set to isolate representation geometry. We show that this choice is **not** neutral. On CLIP ViT-B/32 with real Flickr30k image–text pairs, the blank-image condition **flips the sign of $\Delta E$** at $n{=}16$ ($+0.0167$ for blank vs.\ $-0.0073$ for real at $r{=}16$), changes the per-block task loss by a factor of $396$ and the per-block $|\Gamma_k|$ by two to three orders of magnitude, and **flips the sign of $\cos\phi_k$ for all three text blocks**. Consequently, $\Gamma$ predictions are reported as statements about **alignment energy**, and their transfer to downstream accuracy is **not claimed**: in our supplementary sweep ($n{=}78$) the training-condition energy change is *positively* associated with the downstream gain ($\Delta E_{\mathrm{train}}$ vs.\ $\Delta$R@1: Spearman $+0.478$), i.e.\ **larger energy reductions correspond to worse retrieval**; the largest reduction ($\Delta E_{\mathrm{train}}=-0.0350$, blank, $r{=}16$, $n{=}1024$) coincides with the **worst** retrieval score ($\Delta$R@1 $=-0.0131$). The cleanest evidence is the paired comparison at $n{=}1024$: replacing real images by blank images reduces the energy further while **lowering** R@1 by $1.4$–$3.1$ points. (The held-out-energy correlation, Spearman $-0.374$, is dominated by the real/blank cluster structure and is *not* monotone within the energy-decreasing subset, $+0.171$, $n{=}54$.)
3. **把"能量"与"下游"解耦**：正文写 *"alignment energy is a diagnostic of representation geometry, not a proxy for downstream accuracy; in our supplementary retrieval study the two are not monotonically related."*
4. **$r_c\in[5,6]$ 加限定**：说明该临界秩是在 blank-image、16 样本、4-bit QLoRA 的 LLaVA 设置下测得；并明说该符号翻转在 CLIP 的真实图文复跑中**未出现**，与论文自报的 Qwen2-VL "无相变" 一致 → 该阈值是**设置特异**的，不是跨模型定律。

### 6.3 若要正面回应 R1.3/R3.16，最省成本的一条路

论文需要**一个**下游指标。本补充实验证明**可以用 CLIP + 检索**做：单 run 25–34 s（n=1024），3 seed 一组 ~1.5 min。
**建议在稿件里加一小节"Downstream sanity check"**，只报 §5.1 的两行（real 提升 / blank 退化）+ §5.2 的 Spearman，
并明确写"这不是 LLaVA 规模的下游评测，而是对 energy 作为下游代理的**否证性检验**（falsification test）"。

---

## 7. 溯源表（脚本 ↔ 归档 ↔ 字段）

### 7.0 来源纪律（2026-10-13 加固，流程规则：**不要把聚合产物当来源**）

**聚合文件若会被后续调用重写，它的字段路径就会静默失效/改值。** 本任务按此分两类：

| 类别 | 文件 | 性质 | 引用方式 |
|---|---|---|---|
| **来源（只增不改）** | `p3d_clip_ranksweep.json`、`p3d_qwen_ranksweep.json`、`p3d_qwen_ranksweep_mp50176.json` | 每条 run **自带超参**（`lr/epochs/batch/dropout/min_pixels/max_pixels`），续跑只**追加**、不覆盖已有 run | ✅ **引用请落到 `runs[*]`，并带 `split`/`n`** |
| **来源（确定性单次）** | `p3d_e0_vs_token_budget_{split}_n{n}.json` | 只前向、无训练 ⇒ E0 确定；**行级带 `device`**，换设备重跑会被守卫拒绝（CPU/GPU 差 0.09%） | ✅ 引用 `rows[*]`，带 `split`/`n`/`device` |
| **派生聚合（会被重写）** | `p3d_summary.json`、`p3d_qwen_summary.json`、`p3d_tables.md`、`p3d_fig_ranksweep.png`、`p3d_qwen_resolution_check.json`、`p3d_qwen_summary.json` | 每次运行**重算**；源归档若被追加 run，其数字会变 | ⚠️ 只作导航；**引用数字请回落到上面两类**，并用 `source_fingerprint.sha256` 锁定当时口径 |

**两条新增的机器保证**（`_p474` 回填 + 门禁 `_p466` 断言，现 **91/91**）：
1. **每条 run 自带超参**，且 `train_spec` 写入归档；`_p461`/`_p464` 续跑时若**共有核心键**与此前归档不一致 → **硬失败**（拒绝静默重写 `protocol` 误标旧 run）。
   - **两个方向都实测过**：不同预算指向同一归档 → `exit 1` + 明确列出差异键；**8 个共有核心键全同** → 打印 `来源校验通过（比对 8 个共有超参键）` 并正常续跑（`exit 0`）。
   - 实现上**只比对共有核心键**（`lr/epochs/batch/lora_targets/lora_alpha/dtype/min_pixels/max_pixels`），**不做整体相等**——
     最初写成整体比较，会把"参数完全相同、只是 spec 键集不同的合法续跑"也拒掉（**实测踩到并修**）。
2. **派生聚合带 `source_fingerprint`**（源文件 sha256 + 条数）与 `derived_note`；门禁逐条核对指纹与实际文件**逐位一致**。

**其余同源风险与处置**：
- `_p472` 的 rows **按 `max_pixels` 覆盖式合并** ⇒ 换设备重跑会让旧行被静默替换（CPU↔GPU 的 bf16 E0 差 **0.09%**，实测 21771.7 vs 21751.8）。
  ⇒ 已加**行级 `device`** + **设备一致性守卫**（混设备直接 `raise SystemExit`）。
- 早期一个**无 `split/n` 后缀**的重复归档已由 `tools/_p473_dedupe_legacy.py` **逐行比对确认被覆盖后**删除（不是凭文件名删）。

### 7.1 明细

| 归档文件 | 产出脚本 | 关键字段 |
|---|---|---|
| `outputs/analysis/p3d_manifest.json` | `tools/_p460_build_manifest.py` | `datasets.flickr30k.test[*]`、`datasets.*.train_sel[str(n)]`、`datasets.*.integrity`、`sources.*.sha256` |
| `outputs/analysis/p3d_clip_ranksweep.json` | `tools/_p461_clip_ranksweep.py` | `runs[*].{rank,arm,condition,n_train,seed,device,dE_train,dE_test,E_test_0,E_test_final,E_train_epochs,E_test_epochs,loss_epochs,R@1,R@1_i2t,R@1_t2i,R@5,R@5_i2t,R@5_t2i,n_peft_params,seconds}`、`protocol` |
| `outputs/analysis/p3d_summary.json` | `tools/_p463_summarize.py` | `table_rank_condition[*]`、`sign_flip.{dE_train,dE_test}.*`、`paired_blank_vs_real[*]`、`paired_by_cell[*]`、`energy_vs_downstream.*` |
| `outputs/analysis/p3d_tables.md` | `tools/_p463_summarize.py` | 人读版表格 |
| `outputs/analysis/p3d_fig_ranksweep.png` | `tools/_p463_summarize.py` | ΔE–rank / R@1–rank / ΔE–ΔR@1 三联图 |
| `outputs/analysis/p3d_gamma_real_vs_blank.json` | `tools/_p462_gamma_real_vs_blank.py` | `conditions.{real,blank}.blocks.{块}.{gamma,gamma_std,norm_gE,norm_gL,cos,pct_abs_gamma}`、`comparison.*`、`per_batch` |
| `outputs/analysis/p3d_qwen_ranksweep.json` | `tools/_p464_qwen_ranksweep.py` | `runs[*].{rank,condition,n_train,seed,device,E_train_epochs,E_eval_real_epochs,loss_epochs,dE_train,dE_eval_real,n_peft_params,seconds,sec_per_sample}`（**43 条 = 1 CPU 冻结基线 + 42 CUDA 训练 run**） |
| `outputs/analysis/p3d_qwen_summary.json` | `tools/_p467_qwen_summarize.py` | `table[*]`（rank × 条件，含 `dE_train`/`dE_eval_real` 的 mean±std）、`paired_blank_vs_real[*]`（21 对） |
| `outputs/analysis/p3d_qwen_smoke.json` | `tools/_p464_qwen_ranksweep.py --smoke` | `by_device.{cpu,cuda}.{load_seconds,step_seconds,peak_allocated_GiB,peak_reserved_GiB,loss,n_peft_params}` |
| `outputs/analysis/p3d_qwen_token_stats.json` | `tools/_p468_qwen_token_stats.py` | `rows[*].{n_visual_tokens,seq_len,grid}`、`mean_visual_tokens`=15.0、`mean_seq_len`=53.8 |
| `outputs/analysis/p3d_qwen_ranksweep_mp50176.json` | `tools/_p464_qwen_ranksweep.py --max-pixels 50176` | 4 条 run（独立归档；`runs[*].{max_pixels,dE_train,dE_eval_real,E_train_epochs,loss_epochs}`） |
| `outputs/analysis/p3d_qwen_token_stats_mp50176.json` | `tools/_p468_qwen_token_stats.py 50176` | `mean_visual_tokens`=54.0、`mean_seq_len`=92.8 |
| `outputs/analysis/p3d_qwen_resolution_check.json` | `tools/_p469_qwen_resolution_check.py` | `sign_summary.{16384,50176}.{real,blank}`、`pattern_holds.*`、`paired.*`、`conclusion` |
| （编码校验） | `tools/_p471_check_encoding.py` | 逐字节验证 11 个 `p3d_*.json` 为严格 UTF-8（11/11 通过） |
| `outputs/analysis/p3d_e0_vs_token_budget_train_sel_n16.json` | `tools/_p472_e0_vs_token_budget.py` | **主曲线**（4 个预算点）：`rows[*].{max_pixels,min_pixels,mean_tokens,tokens_match,E0_real,E0_blank,gap_pct}` + `paper_operating_point_tokens`/`paper_source` |
| `outputs/analysis/p3d_e0_vs_token_budget_test_n4.json` | 同上 | held-out test n=4，2 点（**样本集相关性的证据**） |
| `outputs/analysis/p3d_e0_vs_token_budget_test_n2.json` | 同上 | **负例**：n=2 时趋势方向翻转（+122.2%→+103.7%） |
| `outputs/analysis/llava_bf16_feasibility.json` | `tools/_p294_llava_bf16_feasibility.py` | `disk.total_GiB`=13.157、`four_bit_excluded_because`（**他人脚本，只引用不改**） |

辅助工具：`tools/_p461b_retrieval_api_check.py`（检索管线诊断）、`tools/_p465_show_runs.py`（逐 run 打印）。
运行日志：`outputs/analysis/_p461_sweep.log`、`_p461_sweep_n1024.log`、`_p461_sweep_n16.log`、`_p461b_n1000.log`。

**重跑方式**（幂等、增量落盘、可中断续跑）：

```
python tools\_p460_build_manifest.py --apply
python tools\_p461_clip_ranksweep.py --baseline --fresh --device cuda
python tools\_p461_clip_ranksweep.py --sizes 1024 --ranks 4,5,6,1,16,8 --conditions real,blank --seeds 42,123,999 --device cuda
python tools\_p461_clip_ranksweep.py --sizes 16 --ranks 6,8,16,4,5,1,2 --conditions real,blank --seeds 42,123,999 --device cuda
python tools\_p462_gamma_real_vs_blank.py --apply --device cpu
python tools\_p463_summarize.py --apply
python tools\_p466_verify_report.py          # 门禁：报告里每条关键主张对着归档断言
```

**Qwen2-VL-2B 档（§8 第 4 条，需 ≥50 min 连续 GPU 窗口；按 §6.1b 实测 ~9–10 min/run）**：

```
python tools\_p464_qwen_ranksweep.py --check-only --ranks 4 --device cpu   # 不占卡，验注入路径
python tools\_p464_qwen_ranksweep.py --smoke --device cuda --ranks 4        # 1 步 fwd+bwd，报显存
python tools\_p464_qwen_ranksweep.py --ranks 4,16 --conditions real,blank \
    --n-train 16 --seeds 42,123 --device cuda                              # 主体
python tools\_p467_qwen_summarize.py --apply
```

（循环次序为 `rank → seed → condition`，**被时间截断时已完成的仍是 real/blank 成对单元**。）

---

## 8. 没做成的事（明确列出）

1. **LLaVA-1.5-7B 规模的真实图文复跑 / 下游评测：没做成。** 硬约束（13.157 GiB > 8 GiB，且禁用 4-bit）。这是 R2.3 里"add a small downstream evaluation"的**最强版本**，本机无法交付 → 用 §6.2 的主张降级 + CLIP 的否证性检验替代。
2. **VQA：没做成**，本地无任何 VQA 标注数据，且未下载（遵守"不要下载"）。
3. **captioning 指标（BLEU/CIDEr/ROUGE）：没做成**，环境里没有 `nltk` / `pycocoevalcap` / `sacrebleu` / `rouge_score`（实测 `ModuleNotFoundError`），未安装。下游指标改用**检索 R@1/R@5**（同样是 R3.16 点名的任务族）。
4. ~~**Qwen2-VL-2B 的 rank sweep：没跑成。**~~ → **已在 02:39–02:56 跑成，见 §3.3**（42 个训练 run、7 个 rank × 2 条件 × 3 seed，全部 CUDA）。
   跑成前的准备与踩坑记录保留如下（它们解释了为什么"按理论估时长"会错 3–20 倍）：
   - `_p464 --check-only`（不占卡）：验证 LoRA 注入路径 —— rank=4 时 **224** 个可训练张量 / **1,089,536** 参数，
     rank=16 时 **224** / **4,358,144**，`patch_embed` / `visual` **零污染**；
     参数量可手算复核 `28×[2r×(1536+1536) + 2r×(1536+256)]` = 1,089,536（r=4），与回读**完全一致**。
   - `_p464 --smoke`（GPU）：峰值 allocated **4.34 GiB** / reserved **4.64 GiB**、单步 **0.83 s**。
   - **已排除两个坑**：① 全序列 CE 会物化 `(B,L,V)`（task-9 实测 batch 4 峰值 **17.82 GiB**）→ 改为只对
     assistant 回复 token 且只切 `logits[:, :-1]`；② peft 子串匹配会误伤 `visual.patch_embed.proj`（Conv3d）
     → 用 `exclude_modules` + `named_parameters()` 回读断言。
   - **已补**：`max_pixels=50176`（224×224，54 visual token）下复跑 ranks{4,16}×{real,blank}×seed42（4 run，
     独立归档 `p3d_qwen_ranksweep_mp50176.json`）→ **原符号结论被证伪，已在 §3.3.1 撤回**。
   - **仍然没做**：**54 token 预算下的完整网格**（3 seed × 7 rank ≈ 25 min GPU）。
     现有 4 个 run **足以证伪**旧主张，**不足以**建立新规律。命令：`_p464 --max-pixels 50176 --ranks 1,2,4,5,6,8,16 --seeds 42,123,999`。
5. **`both` 臂（vision+text 双塔 LoRA）的 rank sweep：没跑**（次要对照臂，`_p461 --arms both` 可直接续跑，需约 6 run × 4 rank）。
6. **n=128 这一档没跑**：只跑了 n=16（论文协议）与 n=1024（有实际训练量）。n=128 的单元可由 `--sizes 128` 直接补齐（脚本支持续跑）。
7. **`E_train` 是固定子样本（min(n,256)）而非全量**（n=1024 时全量能量评测太贵），已在 `protocol.E_train_note` 写明。
8. **CLIP 不是 LLaVA**：本补充实验的模型与论文主实验不同（双塔 vs 解码器 + 4-bit QLoRA）。§3.2 已写明这**既不能确认也不能否证** LLaVA 特有的相变；能支持的是"非普适 + 对图像条件/训练量敏感"。
