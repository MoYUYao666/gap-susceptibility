# 每周文献检索 · 2026-10-19（覆盖全部 6 篇稿件）

**检索方式**：17 条检索式（`web_search` + arXiv API `export.arxiv.org` + Crossref/arXiv MCP），逐条核对 arXiv abs 页或 DOI；
**已投稿件一律不改**，发现只记入"下轮修回动作"。
**核对基准**：Paper A bib 52 条、P3 bib 21 条、P1 bib 45 条、A1 内嵌 thebibliography 56 条。

---

## 1. A1（`paper_a1/`）｜Pattern Analysis and Applications 已投（Submission received；技术检查中）

**⚠️ 本周最重要发现：出现一篇与本稿主张高度重叠的工作。**

| 候选 | ① 是什么 | ② 与本稿关系 | ③ 行动 |
|---|---|---|---|
| **Sharma & Saxena, 2026**<br>[*One Geometry, Different Outcomes: Readout-Dependent Effects of the Modality Gap in Vision-Language Models*](https://arxiv.org/abs/2609.36101)（arXiv:2609.36101，9 页）| 在 CLIP/SigLIP 上发现图像–文本均值分离 94.4–99.9% 的平方范数由**单一主方向**承载（秩一）；把相似度分解为三种 readout 角色：零样本分类里"固定 gap 偏移"等价于**加性类别偏置**、标准检索里投影掉 gap 方向会引入**乘性排序畸变**、混合模态检索里 gap 方向按模态排序。据此解释"改 gap 有时提升、有时破坏" | **重叠/挑战（最接近）**：同样主张"gap 修改的效果取决于任务与 readout"，A1 的"任务敏感谱"（centroid < zero-shot < retrieval）与其结论方向一致。**本稿仍独有**：定理级充分性（一阶矩统计量不可能充分）、margin 质量下界与证书、670 对真实匹配、5 骨干加密扫描 | **A1 修回必须**：加引用 + 一段区分（几何秩一解释 vs 统计充分性/证书；其无下界、无监控规则） |
| Yaras, Chen, Wang & Qu, 2024<br>[arXiv:2412.07909](https://arxiv.org/abs/2412.07909) | 用**梯度流**刻画 gap 的产生：错配数据对 + 可学习温度是主因；温度调度/模态交换可缓解，缩 gap 提升检索 | 背景/支持：为"gap 是训练动力学产物、不是健康指标"提供机理；Paper A 已引，**A1 未引** | A1 修回可加 1 句机理引用 |
| 检索 `"order preservation" AND "zero-shot"` | arXiv 全库仅 1 条无关命中（曝光校正）| **支持**：未发现"用保序性替代绝对量"的同类度量 → A1 的 τ/保序叙事仍为首创 | 记录，不改稿 |

## 2. Paper A（`paper合/`）｜Neurocomputing 已投（`NEUCOM-D-26-23760`）

| 候选 | ① 是什么 | ② 关系 | ③ 行动 |
|---|---|---|---|
| Sharma & Saxena, 2026（同上）| 见上 | 已在 bib（`sharma2026readout`）✅ | 修回可在"任务依赖"处引一句 |
| Yaras et al., 2024 | 见上 | 已在 bib（`yaras2026explaining`）✅ | 无 |
| **Role, Meyer & Amblard, 2026**<br>[*Quantifying and reducing the modality gap in both contrastive and generative multimodal VLMs*](https://doi.org/10.1007/s13735-026-00423-w)（IJMI 15(4)，DOI 已核）| "Fill the Gap" 的**期刊正式版**：量化并缩小对比式与生成式 VLM 的 gap | 与"gap 可量化/可缩小"直接相关；bib 现只有 arXiv 预印本 `2505.03703` | **修回把该条升级为期刊版**（有 DOI/卷期，符合"引用可核实"规则）|
| Hu et al., 2026<br>[*Visual Branch is What You Need for CLIP-based Class-Incremental Learning*](https://arxiv.org/abs/2609.37888) | 指出 CLIP 文本分类器因 gap 偏离视觉分布，改用纯视觉分支 + 核化增量最小二乘更优 | 支持本稿"文本侧与 gap 耦合、text 分支并非天然更优"的论点 | 修回可选引用（讨论段）|
| Zhou?/He et al., 2026<br>[*Dual-Mode Low-Rank Learner with Bridge-Prototype Ensemble*](https://arxiv.org/abs/2609.36759) | CLIP 增量学习：双模式低秩 + 视觉原型–文本嵌入测地桥，补偿文本决策边界的 gap 局限 | 背景（低秩 + gap 补偿） | 可选 |
| 检索 `adapter placement / adaptation site / frozen backbone LoRA` | 未发现新的"位置效应"竞争工作 | **支持**：Paper A 的位置效应主张仍独有 | 记录 |

## 3. P3（`paper3/paper_ieee/`）｜PRL `PRLETTERS-D-26-02378R1` 在审（deadline **2026-11-02**）

**rank allocation 方向本周新增多篇，直接压 P3 的"零样本、免搜索分配"卖点。**

| 候选 | ① 是什么 | ② 关系 | ③ 行动 |
|---|---|---|---|
| **Gao & Tan, 2026**<br>[*Statistical Inference for Rank Allocation in Low-Rank Adaptation*](https://arxiv.org/abs/2607.20205)（arXiv:2607.20205，77 页）| 把 LoRA rank 分配写成**假设检验**：每个分量一个检验统计量、p 值决定保留/剪枝；给出优化器轨迹的中心极限定理（含 AdamW），StatLoRA 在 GLUE/生成/QA 上对比 AdaLoRA/IGU-LoRA | **竞争**：同为"有理论依据的 rank 分配"，但其需估计/校准，非零样本 | **P3 修回必引 + 区分**（P3：由梯度几何先验直接给出，无搜索/无校准集）|
| He & Fan, 2026<br>[*LoRA-GA²: Multi-step Gradient Adaptive Alignment*](https://arxiv.org/abs/2608.19800) | 用多步梯度探测 + 谱重要性做 rank 分配与初始化，GLUE/GSM8K/HumanEval 超基线 | 竞争（梯度驱动分配） | 引用区分 |
| **Zhang, Liu & Cheng, 2026**<br>[*IFCLoRA: Topology-Aware Rank Allocation*](https://arxiv.org/abs/2607.22251) | **训练前、一次性**：用冻结模型干预追踪构造交互图，取信息流中心性 + 局部梯度敏感度，做零搜索 rank 分配与保函数初始化 | **最接近**：同样"预训练后、微调前分配"，且明确"无需搜索" | **P3 修回必引 + 重点区分**（P3 的分配规则来自梯度几何的解析式与临界 rank，而非图拓扑评分）|
| Xie et al., 2026<br>[*Automatic Rank Allocation ... via ℓp Regularization*](https://arxiv.org/abs/2609.28998) | ℓp 正则实现隐式阈值化 rank 选择 | 背景 | 可选 |
| 检索 `alignment energy / critical rank / phase transition` | 未发现同一"对齐能量–临界 rank"现象的工作 | **支持**：P3 的理论点仍独有 | 记录 |

## 4. A23（`paper_a2/`）｜IEEE JOE `26-0663` 在审

| 候选 | ① 是什么 | ② 关系 | ③ 行动 |
|---|---|---|---|
| Kim et al., 2026<br>[*Cross-Modal Knowledge Distillation for Acoustic Pedestrian Detection*](https://arxiv.org/abs/2609.31785) | 视频教师蒸馏音频学生，讨论"音频–视频 gap"下选择性监督的收益与局限 | 弱相关背景（跨模态 gap 但非声呐/非对比对齐）| 记录 |
| Do & Kim, 2026 / 侧扫声呐配准类 | SAR–EO、侧扫声呐几何配准 | 声呐几何配准，非语义对齐 | 记录 |
| 检索 `sonar image-text contrastive alignment` | **未发现**"声呐图像–文本对比对齐"竞争工作 | **支持**：A23 的跨模态诊断仍为空档 | 记录 |

## 5. P1（`paper/`，已拒）与 6. ap3（归档）

无新发现；沿用 Paper A 的竞争面结论。

---

## 四句总评

1. **竞争最激烈的是 A1**：Sharma & Saxena (2026) 从"秩一几何 + readout 角色"解释 gap 修改的任务依赖性，与本稿"任务敏感谱"重叠——但它没有充分性定理、下界与证书，A1 修回时必须引用并区分。
2. **各稿最脆弱主张**：A1"gap 非充分统计量 + margin 证书"未被挑战；Paper A"位置效应"仍独有；**P3"训练前零搜索分配"被 IFCLoRA / StatLoRA 逼近**；A23 声呐对齐仍无竞争。
3. **最紧急一篇是 P3**：deadline 2026-11-02，且需在修回中补引至少 3 篇 rank-allocation 工作并写清"解析式 vs 搜索/校准"的差异。
4. **动作清单**：① A1 修回加 Sharma/Yaras 引用 + 区分段；② Paper A 修回把 Amblard 条升级为 IJMI 期刊版，可选加 CIL 两条；③ P3 修回必引 StatLoRA / IFCLoRA / LoRA-GA²；④ A23 与 P1 仅记录，**所有已投稿件本轮不动**。
