# 待跑实验设计（2026-10-07）

> 来源：操作者指示"所有能补的实验都补上"。
> **硬约束**：本机 **RTX 4060 Laptop 8 GB**，实测**只能容纳一个实验**
>（`nvidia-smi`：7812/8188 MiB、利用率 100%）→ **必须串行**。

---

## 实验 ③：patch-16 骨干 + 多 rank 对照

### 要解决什么

论文的核心经验规律（`empirical.tex` Design Patterns）：

> "across all seven strict-freezing configurations measured, every patch-32 backbone has the text-only arm at
> the smallest gap change and every patch-16 backbone has the both-position arm there, **without exception**"

**问题**：7 个配置**全部在 rank-4 下测量**，且 **patch-16 组只有 1 个骨干**（BioCLIP，领域模型）
→ 审稿人会说"这不是 patch size 规律，是 B/16 与 BioCLIP 的个体差异"。

### 设计

| 维度 | 现有 | 需补 |
|---|---|---|
| **patch-16 骨干数** | **1**（BioCLIP） | **+1**（CLIP B/16，本地已有 `models/clip-vit-base-patch16`） |
| **rank 覆盖** | 仅 **r=4** | **r ∈ {4, 16, 64}**（验证规律不依赖 rank） |
| **方差分解** | 无 | 报告**模型身份 vs patch size** 的方差占比 |

**协议**：沿用 `experiments/strict_freeze_control.py`（全冻 + 仅放开 LoRA A/B，
`vision_nonzero_tensors` 作为硬校验）。

**成本**：CLIP B/16 的 LoRA 训练，每配置约 **10–20 min**（本地实测）；
3 rank × 3 site × 1 骨干 ≈ 9 run ≈ **2–3 h**。

**须先做**：确认 `models/clip-vit-base-patch16` 是否已在本地（**当前未见，需下载 ~600 MB**）。

---

## 实验 ④：解码器 VLM 对照（Qwen2-VL-2B）

### 要解决什么

`discussion.tex` Limitations 自认：

> "our study is **limited to contrastive dual-encoder architectures**; whether the framework generalizes to
> **decoder-based VLMs** or generation-oriented objectives remains open"

**这是全文最大的 scope 缺口**——摘要声称"validation spans 383 experiments over five architectures"，
而那五个**都是双塔编码器**。

### ✅ 分塔已验证可行（本日前置工作）

Qwen2-VL-2B 的两塔用**完全不同的线性层名**：

| 塔 | 线性叶子 | 数量 |
|---|---|---|
| 视觉塔 `model.visual.blocks.N` | `attn.qkv`、`attn.proj`、`mlp.fc1`、`mlp.fc2` | 32 块 × 4 |
| 视觉→语言 `model.visual.merger` | `mlp.0`、`mlp.2` | 2 |
| 语言塔 `model.language_model.layers.N` | `q_proj`、`k_proj`、`v_proj`、`o_proj`、`gate_proj`、`up_proj`、`down_proj` | 28 层 × 7 |

**实测三臂互不污染**（`tools/_p4_verify_tower_split.py`，CPU 验证）：

| 臂 | 可训张量 | 视觉侧 | 语言侧 | 判定 |
|---|---|---|---|---|
| `text_only` | 392 | **0** | 392 | ✅ 干净 |
| `vision_only` | 258 | 258 | **0** | ✅ 干净 |
| `both` | 650 | 258 | 392 | ✅ 干净 |

**⚠️ 关键更正**：既有 Qwen2-VL 运行的 LoRA 目标
（`clip_vlm_vision_instruction_dynamics.py:142`）为 `q_proj/k_proj/v_proj/o_proj/gate/up/down`
—— **这些在视觉塔里一个都没有** → **那个配置实际是"文本侧"**，不是"both"。
**该脚本的注释/命名需更正。**

### 设计

三臂（text-only / vision-only / both），同 rank=8、α=16；
**测量**：投影后图像/文本嵌入的 DG\*、CG、以及 R@1（对比检索）。
**参数量不匹配是协议允许的**：CLIP 侧三臂本就不同（196,608 / 491,520 / 294,912），如实报告即可。

**成本**：Qwen2-VL-2B 4-bit/bf16 LoRA，每 run 约 **45–90 min**（本地实测 8 GB 可跑）；
3 臂 × 1 seed ≈ **3–4 h**（若 3 seed 则 ×3）。

---

## 实验 ⑥：第二组数据集（非自然图像）

### 要解决什么

ODE 与严格冻结结论**只在 Flickr30k / MS-COCO**（皆自然图像、皆检索）上验证。
审稿人会问"换个域还成立吗"。

### 设计

用**已在本地**的非自然图像数据（`data/dtd`：纹理，47 类；`data/food-101`：食物，101 类）
做**同一协议的 DG\* 轨迹**，或直接做零样本（论文已有 DTD/Food101 的零样本结果，`fig12`）。

**选项 A（推荐，省 GPU）**：把已有的 DTD/Food101 零样本结果与严格冻结对照**合并分析**
——检验"gap 变化小的臂是否零样本保持得更好"，**纯分析，零 GPU**。

**选项 B（需 GPU）**：在 DTD（纹理，与自然图像差异大）上重跑 rank sweep 的 DG\* 轨迹。

**成本**：A ≈ **1 h（零 GPU）**；B ≈ 2–3 h（GPU）。

---

## 执行顺序（**GPU 串行**）

| 序 | 实验 | 状态 | 预估 |
|---|---|---|---|
| 1 | 逐 epoch 梯度 → α（both 臂） | ⏳ **运行中** | ~1 h |
| 2 | 实验 ⑥ 选项 A（**零 GPU**） | 可**并行**做 | ~1 h |
| 3 | 实验 ③（CLIP B/16，需先确认模型在本地） | 排队 | 2–3 h |
| 4 | 实验 ④（Qwen2-VL 三臂） | 排队 | 3–4 h |
