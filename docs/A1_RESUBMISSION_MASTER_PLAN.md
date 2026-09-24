# A1 新稿：全部提升与修改点 + 目标期刊候选

> 背景：PRLETTERS-D-26-01941 于 2026-09-14 被 **Rejected**（R1 六条 + R2 五条）。逐条应对计划见 `A1_REVIEWER_RESPONSE_PLAN.md`。本文件是**新稿的总纲**：把"所有提升点"（已有的 8 块素材 + 新跑的补强 + 因审稿意见新增的工作）与"目标期刊"合在一起，作为写作与投稿的依据。

---

## 一、新稿必须做的 11 项修改（对应审稿意见）

| ID | 来源 | 修改内容 | 类型 |
|---|---|---|---|
| M1 | R1.1 | 把"模态差被广泛当作通用指标"的表述**改为可支撑的版本**：说明前作主要在对齐/检索语境下使用该诊断量，并明确我们否定的是"**无条件**的 gap 指标观" | 主张收窄 |
| M2 | R1.2 | **Related Work 从一段扩成正式小节**（≥1.5 页）：zero-shot robustness / 微调后表示漂移 / VLM 灾难性遗忘 / 排序稳定性 / 校准 / prompt 敏感性 / 替代相似度度量 + 与我们的区别 | 文献 |
| M3 | R1.3 + R1.4 | **正面处理"同义反复 vs 不充分"这对矛盾**：写明 τ 只在**冻结 top-5 集合**上算 Kendall、准确率是 1000 类全 argmax → 二者非同一对象；并**主动收窄**为"τ 是破坏方向上的必要代理，跨机制不充分"（把审稿人自己举的 Gaussian vs 收缩反例写进正文） | 主张收窄（核心） |
| M4 | R1.5 | 把**块 4/6/7（真实 LoRA 微调）从补充提升为正文主证据**；补种子误差棒（进行中） | 结构 + 实验 |
| M5 | R1.6 | ① 收窄"通用监控指标"措辞；② **新增跨数据集的微调检查点**（不只 Flickr30k） | 主张 + 实验 |
| M6 | R2.1 | **明写配对反转判据不是一阶近似**：`pair (i,j) 反转 ⟺ λ‖g‖(m_j−m_i) > d_ij` 对任意 λ 精确（给定冻结 margin）；一阶展开只用于文本侧讨论 | 理论澄清（可翻盘） |
| M7 | R2.2 | **top-k 消融**（k = 1,3,5,10,20,50,100）：τ–准确率相关性、λ 曲线、监测灵敏度是否随 k 稳定 | 新实验（纯评测） |
| M8 | R2.3 | **增加 zero-shot 基准 + 细粒度数据集**（本机已有 DTD / Food-101 / iNat / rare-species / marinelife16k / NKSID） | 新实验（纯评测） |
| M9 | R2.4 | 补引三篇 compositional ZSL 工作并 contextualize：Concept-Aware GCN / Semi-Negative Contrastive Subclass Discriminative / Multi-Level Contextual Prototype Modulation | 文献（易做） |
| M10 | R2.5 | **把 r=1.0 重新定位**：明说这是"闭式恒等式的自洽检查"（两侧共享同一批冻结分数），**不是独立验证**；独立证据改用跨族留出（R²=0.371/0.378、ρ=0.927）+ 新 50k 样本预测；附散点图 + 误差分布 + 适用前提 | 表述（核心） |
| M11 | R2.1 附带 | 把高斯代理的适用域写成**命题**（何时从精确退化为近似：R²=0.986、最大误差 0.170） | 理论 |

## 二、新稿的四大新增实验（回答"实验面窄"）

| ID | 实验 | 数据现状 | 状态 |
|---|---|---|---|
| E1 | **补种子**：λ_reg ∈ {0, 0.1, 0.5, 1.0} × seed {123, 456}，10 epoch，端点 τ/top-1/val | 跑到 λ=0.5；已完成 λ=0/0.1/0.5 的 seed123 与 λ=0.1 的 seed456 | ⏳ 运行中（约 2.5 h 剩余） |
| E2 | **top-k 消融**（R2.2） | 无需新数据：复用冻结分数与 τ 计算，换 k 重算 | 待跑（纯评测） |
| E3 | **多基准 zero-shot**（R2.3）：DTD / Food-101 / iNat / rare-species 等，冻结 + 平移 + 收缩三条件下的 top-1 与 τ | 图像数据本机已有；需写评测脚本 | 待跑（纯评测） |
| E4 | **跨数据集微调检查点**（R1.6）：在非 Flickr30k 数据上做 LoRA 微调，检验 τ–准确率关系是否跨数据集成立 | 数据本机已有 | 待跑（最耗算力） |

**E1 已出的数**：50k top-1 随 λ_reg 单调下降 —— λ=0: **58.05** → λ=0.1: **57.73** → λ=0.5: **56.35**（seed 123），与"训练期类别对齐损害 zero-shot"一致，且给原单种子表补上误差棒。

## 三、新稿结构建议（Elsevier 全文格式，约 14–18 页）

1. Introduction（**收窄主张**：τ 是排序保持代理，不是通用指标；gap 不是通用健康指标）
2. **Related Work**（新写，M2 的 7 支文献 + M9 三篇）
3. Theory：gap 平移下的**精确**配对反转判据（M6）+ 高斯代理的适用域命题（M11）
4. Method：τ 的定义与 **top-k 的动机与消融**（M7）+ CG/其他度量对照
5. Controlled perturbations：34 条件 × 3 模型族（原有）
6. **Real adaptation**（块 4/6/7 提上来 + E1 误差棒 + E4 跨数据集）：τ 最早侵蚀、top-1 惰性、训练期对齐剂量-响应
7. **Boundary of the metric**（M3 + M10）：τ 何时失效（收缩机制、高斯代理）、r=1.0 的正确解读、跨族留出的独立证据
8. **Multi-benchmark validation**（E3）：细粒度与非 ImageNet 基准上的复现
9. Limitations & Conclusion（**逐条对应审稿意见**，把"我们已收窄到哪里"写清）
10. Appendix：完整表格、散点图、误差分析、逐 seed 数值

## 四、目标期刊候选（中科院二/三/四区、全文格式、审稿相对快）

> ⚠️ **分区与审稿周期必须现查**：中科院分区每年 12 月左右更新，各刊"审稿周期"以 LetPub 与期刊官网的 "Review time / Submission to first decision" 为准。下表是**范围匹配度**判断（我给的排序依据是主题契合，不是承诺的速度）。

| 候选 | 分区（需核） | 契合度 | 备注 |
|---|---|---|---|
| **Image and Vision Computing**（Elsevier） | 中科院 3 区（有来源标注 3 区） | **很高**：视觉表示、评估方法 | 全文格式；Elsevier 内部转投可走 ATS |
| **Journal of Visual Communication and Image Representation**（Elsevier） | 3–4 区 | **很高**：直接对应"表示漂移"主题 | — |
| **Neurocomputing**（Elsevier） | 2 区 | 高：表示学习 + 评估 | 篇幅宽松，容得下 Related Work 扩写；与 `paper_ap3` 同刊需披露重叠 |
| **The Visual Computer**（Springer） | 3–4 区 | 高：视觉方法 | Springer 转投系统较快 |
| **Machine Vision and Applications**（Springer） | 3–4 区 | 高 | — |
| **Pattern Analysis and Applications**（Springer） | 4 区 | 中高 | — |
| **Signal, Image and Video Processing**（Springer） | 4 区 | 中 | 偏信号 |
| **Neural Computing and Applications**（Springer） | 2–3 区 | 中 | 体量大、周期波动 |
| **Multimedia Tools and Applications**（Springer） | 4 区 | 中 | 快但口碑一般 |
| **IEEE Access** | 2–3 区（近年下调） | 中 | 最快之一；部分单位不认，投稿前确认 |
| MDPI（Electronics / Applied Sciences / Sensors） | 3–4 区 | 中 | 极快（2–4 周），需 APC；分区/认可度逐年变化，谨慎 |

**核验入口（自己查最准）**：
- LetPub 期刊查询：`https://www.letpub.com.cn/index.php?page=journalapp`（搜刊名 → 看"审稿周期""中科院分区"）
- 期刊官网的 "Review time" / "Submission to first decision" 字段
- Elsevier **Article Transfer Service**：`https://www.elsevier.com/authors/journal-authors/submit-your-paper/article-transfer-service`

## 五、最快的一条路：让 PRL 把稿件**转投**（ATS）

1. PRL 的 Guide for Authors 明确写了 Article Transfer Service："your manuscript will be transferred and **independently reviewed** by the editors"。
2. 本次决定信**没有**主动提供转投 —— 但作者可以**写信向 EIC/AE 申请转投**（附一页说明：已按评审意见完成哪些实质性扩展）。
3. 优势：转投时**评审意见随稿件走**，接收刊可能直接采用，省掉一轮新审 —— 这通常比"撤稿重投新刊"快得多。
4. 建议优先申请转投到 **IVC / JVCI / Neurocomputing**（同属 Elsevier，流程内转投最顺）。

---

## 六、执行顺序（建议）

1. **今天**：M1/M2/M3/M6/M9/M10/M11 的写作（零算力，且是拒稿的核心痛点）
2. **等 E1 跑完**：补误差棒 → M4 定稿
3. **E2 + E3**（纯评测，本机一夜可跑完）→ M7/M8
4. **E4**（最耗算力，可并行于写作）
5. **定刊** → 按该刊模板重排 + 走 ATS 或直接投稿
