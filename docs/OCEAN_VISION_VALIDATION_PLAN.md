# 海洋视觉模型 × 跨模态对齐理论：可行性探索方案

**状态（2026-08-25）**：✅ 阶段 0/1/2 全部闭环——候选定案（OceanCLIP-0.15B）、λ 手术、Theorem 1 精确验证、P1 保护性、σ_m 判别实验 2×2、健康度诊断卡全部完成；结果见 `docs/ocean_universality_report.md` + `ocean_diagnostics.md`，任务规划见 HANDOFF §八"海洋方向"。
**日期**：2026-08-25
**背景文件**：`C:\Users\hongr\Desktop\main.pdf`（综述，33 页，全文已存 `docs/main_pdf_text.txt`）
**目标**：把 Win 端核心理论（P1 / A1 / P3 / Paper A）应用到**外部海洋视觉基础模型**，先验证理论普适性，再诊断海洋模型的健康度；本轮产出为**可行性探索报告**。
**算力现状**：本地 RTX 4060 8GB（可跑 CLIP 级模型；Qwen2-VL-2B bf16 勉强）；autodl 状态待确认。

---

## 0. 综述与理论的结合点（为什么可行）

综述中与视觉/多模态直接相关的素材：

- **Wave 4 基础模型**：Lei 等 [20] 多模态 PHM 大模型（角度域重采样+tokenize）、Peng 等 [21] RotLLM（**LoRA 微调 + RAG**）、Lai 等 [22] FR-LLM（信号转文本）；
- **Wave 3 跨注意力多模态融合**：FedMSFD [75]（Transformer + **对比学习** + 跨注意力）；
- **Wave 2/4 信号→图像**：振动信号二维化 CNN、DPCNN 99.07%；
- 结论部分：时间序列基础模型 + **对比学习** [131,132] 被列为前沿方向；
- 挑战清单：**跨船泛化、可解释性、数据稀缺**（小样本）——正是 PEFT 理论最相关的三个痛点。

理论侧（Win 端）的相关性映射：

| 理论 | 核心结论 | 与海洋视觉模型的结合点 |
|---|---|---|
| **P1**（Protect, Don't Perturb）| PEFT 保护对齐；text-only 最优；full FT 摧毁零样本 | RotLLM 用 LoRA → 海洋视觉模型若用 LoRA 微调，其对齐保护性能否复现？ |
| **A1**（Gap Surgery）| τ/top-1 解耦；类偏置场一阶理论（Pearson=1.000）；文本侧/图像侧非对称；CG 无信息 | 海洋 CLIP 类模型做 λ 平移手术，看崩塌曲线/非对称性是否跨域成立 |
| **P3**（块级分配）| Theory 优先于 Random；rank/块分配敏感性；任务敏感度谱系（NCC<zero-shot<检索）| 海洋模型在检索 vs 分类任务的敏感性谱；不同 LoRA 分配策略下海洋模型的优劣 |
| **Paper A**（动态理论）| Gap Susceptibility Γ；ODE d(DG*)/dt=α−β | 海洋微调轨迹的 DG 时间演化、跨方法 β 稳定性 |

**关键新科学问题**：A1/P1 理论建立在 ImageNet-1K（1000 类）与 Flickr30k/COCO 上，其推导中含类目数相关量（m_c 分布、σ_m、0.372 均值等）。**海洋域类目数通常远小于 1000（如鱼类数百种）且类目结构异质** → "类偏置场"理论在小类目数域的成立性本身就是有价值的检验，既检验普适性又可能是新贡献点。

---

## 1. 候选模型池（联网初筛，权重可得性为主线）

| 模型 | 类型 | 权重 | 适配协议 | 优先级 |
|---|---|---|---|---|
| **OceanCLIP-0.15B**（zjunlp, HF） | CLIP 类海洋 VLM，`open_clip` 格式 | ✅ HF 直接下载 | **A1 全协议**（λ 平移/top-1/τ/CG），现有 `tools/clip_a1_*` 可移植 | ★★★ |
| **AquaticCLIP**（arXiv 2502.01785 / IEEE 11380196） | 水下 CLIP + 数据集 | 需进一步核实（GitHub/HF 待查） | A1 全协议 + 附带数据集可直接做 zero-shot 类目 | ★★★ |
| **MarineGPT**（hkust-vgd, GitHub, arXiv 2310.13596） | 海洋 VLM（LLM+图像编码器，MiniGPT-4 式） | GitHub 提供代码/权重链接需核实 | P1（LoRA 保护性）、P3（块级分配）、Paper A（微调轨迹） | ★★ |
| **通用 VLM 海洋版**（如 Qwen2-VL 20B 海洋微调版） | VLM | 需搜索（"marine finetune qwen-vl"） | P1/P3 与 A1 的 Qwen 通道（已有 `exp/qwen_gap_surgery_v3.py` 基础） | ★★ |
| **基准**：WaterBench（HF）、MARINER（ACM MM 2026，Qwen2.5-VL 7B 64.40） | 评测基准 | ✅ 数据集 | 应用诊断阶段的"健康度体检"任务集 | 辅助 |

**阶段 0 任务（第一步）**：
1. 核实 AquaticCLIP 权重与数据集可得性（GitHub 仓库、HF、许可证）；
2. 下载 OceanCLIP-0.15B 到本地 `models/`（按 CLAUDE.md 规则：本地直接用 HF，先确认大小 ~300MB，无需服务器）；
3. 梳理 OceanCLIP/AquaticCLIP 的 zero-shot 类目集（海洋域类目数、模板提示词）→ 判断 m_c 分布可行性；
4. 确认 autodl 是否可用（若不可用，本轮只做 CLIP 级模型 + 小样本协议）。

---

## 2. 两阶段路线

### 阶段 1：普适性检验（理论跨域成立？）

在 OceanCLIP-0.15B（首选）上移植 A1 协议：

1. **λ 平移手术**（图像侧/文本侧 × λ∈{−2,−1,…,4}）：CG、τ（类级排序）、top-1（zero-shot）三条曲线；
2. **判据**（与 ImageNet/CLIP 结果对照）：
   - top-1 崩塌超线性 vs 线性？τ 是否先于 top-1 下降（解耦跨域？）；
   - 文本侧破坏性 < 图像侧（非对称跨域？）；
   - 逐类位移 vs 偏置场预言 Pearson 是否仍 ≈1；
   - CG 与 top-1 是否仍解耦（CG 无信息性）；
3. **小类目数域检验**（若类目数 N<300）：m_c 分布重标定 → 上述理论量的 α 缩放；这是潜在的**新贡献**而非单纯复制；
4. **PEFT 保护性**（P1）：在海洋分类/检索数据上 LoRA vs Adapter vs BitFit vs Full FT 的"零样本保持 vs 任务性能"权衡图（可复用 `tools/clip_a1_retrain_epochwise.py` 框架，数据量按 4060 8GB 裁剪）。

### 阶段 2：应用诊断（理论当体检工具）

对每个候选海洋模型输出**健康度诊断卡**：

- 指标集合：CG、τ/top-1 耦合度、PEFT 敏感性梯度、任务敏感度谱系（NCC 质心 / zero-shot / 检索三档——对应 P3）；
- 基准对照：同协议跑 CLIP/OpenCLIP/SigLIP（权重本地已有 `models/`）→ 海洋模型相对"健康/脆弱"的定量定位；
- 对 WaterBench/MARINER 子集跑 VLM 型候选（若算力允许）→ 诊断卡第二页：多模态能力 vs 对齐健康；
- 输出：`docs/ocean_diagnostics.md` + `outputs/ocean_*.json`（全部可复现，数字来自真实 JSON——遵守 CLAUDE.md 约束）。

### 阶段 3：可行性结论与成文决策

- 汇总表：哪几条结论跨域成立 / 哪些被反例修正 / 哪些是海洋域新发现；
- 成文候选（若值得）：A2 方向《Gap Surgery in the Ocean: Cross-Modal Alignment Theory for Marine Vision-Language Models》（理论普适性 + 海洋诊断）；
- 若理论不跨域：转为"海洋模型特殊性"研究报告，仍可回馈训练建议（如 LoRA rank 选择、类目集构建）。

---

## 3. 风险与对策

| 风险 | 对策 |
|---|---|
| 海洋模型权重不可得/许可证限制 | 候选池保留 3 个以上；退路：自有 Qwen2-VL-2B + 海洋数据微调出"海洋原型" |
| 海洋类目集太小或噪声大 | 用附带数据集类目（AquaticCLIP 数据集）或合成类目；τ 类排序需要 ≥10 类，可接受最小规模 |
| zero-shot 模板缺失（海洋模型可能无标准模板） | 复用 ImageNet 模板 + 海洋域模板各 1 套，双口径报告 |
| 4060 8GB 不够大模型 | 阶段 1 只做 CLIP 级；VLM 级放 autodl 或延期 |
| 已验证理论在海洋域不成立 | 这是**有效结果**（边界条件发现），如实报告并分析原因（类目结构/预训练域差异） |

---

## 4. 交付物清单

1. `docs/OCEAN_VISION_VALIDATION_PLAN.md`（本方案，含协议映射表）
2. 阶段 0：候选池核实表（权重/许可证/类目集）→ `docs/ocean_candidates.md`
3. 阶段 1：`outputs/ocean_gap_surgery.json`（λ 扫描全量）+ `docs/ocean_universality_report.md`
4. 阶段 2：`docs/ocean_diagnostics.md`（诊断卡）
5. 阶段 3：成文可行性结论（含：是否立项 A2、目标期刊建议）

## 5. 待确认（回复后细化）

1. 综述是否为您本人的投稿稿？（影响：验证结果与综述衔接方式、是否可作为综述引用的"理论工具"章节）
2. 时间预算？（本探索 1–2 周 / 1 个月 / 随缘）
3. autodl 现在是否可用？（决定 VLM 级实验是否列入近期）
4. 成文倾向：若可行，PRL 类短文还是 KBS/海洋领域刊长文？
