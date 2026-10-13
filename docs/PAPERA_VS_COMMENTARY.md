# Paper A 与 PRL 综述（Commentary）的区别 —— 与重叠风险

> 生成：2026-10-07 ｜ 依据：`paper_review_prl/main_prl.tex`（288 行，在审 `PRLETTERS-D-26-02402`）
> 与 `paper合/`（Paper A，49 页，候选投 CVIU/ESWA）**逐项实测对比**
> 脚本：`tools/_compare_review_vs_paperA.py`

---

## 一、结论先说

**两篇是"主张"与"证据"的关系，不是重复。**

| | **PRL 综述（Commentary）** | **Paper A（`paper合/`）** |
|---|---|---|
| **体裁** | **批判性综述**（critical review） | **原创研究论文** |
| **篇幅** | 约 **5,081 词**（288 行源文件） | **49 页** / 约 **11,254 词** / **44 条引用** |
| **材料来源** | **已发表文献**（"drawn from published work rather than a systematic sample"） | **自己的 383 个实验**（5 架构、3 种 PEFT 方法、2 个检索数据集） |
| **做什么** | **论证领域把问题问错了** | **测量该问题并给出理论** |
| **核心命题** | 领域把**两个正交决策混为一谈**：<br>① **where** 自适应容量放在哪<br>② **how** 固定预算如何在模块间分配 | ① **Distribution Gap 比 Centroid Gap 更能预测检索退化**（r=−0.71 vs −0.59）<br>② **Gap Susceptibility** 由梯度流导出<br>③ 一阶 ODE 预测间隙轨迹（mean R²=0.986）<br>④ 严格冻结对照：**CLIP 上 text-only 优、SigLIP 上反转** |
| **产出物** | **报告清单**（reporting checklist，§4） | **设计准则**：选最小有效秩；text-only 的"保护性"是**架构属性而非通则** |
| **是否引自己的实验** | ❌ 否（只引外部文献） | ❌ 否（未引该综述） |

---

## 二、主题交集实测（**用词频说话**）

在综述全文里检索 Paper A 的核心词汇：

| Paper A 的核心词 | 在综述中出现次数 |
|---|---|
| **`modality gap`** | **0** |
| `retrieval` | **0** |
| `centroid` | **0** |
| `Distribution Gap` | **0** |
| **`gradient flow`** | **0** |
| `alignment` | 2 |
| `gap`（泛指） | 1 |

**→ Paper A 的研究对象（模态间隙的演化、其梯度流理论）在综述里"根本不出现"。**

---

## 三、⚠️ 但有一处**实质重叠**，必须在投稿时处理

综述 `main_prl.tex:159` 的**第一条 robust 结论**写着：

> *"Three conclusions appear robust. First, **site dominates allocation in the small-data regime**: with a small task
> corpus, **which site is trainable matters more than how a budget is divided within it**, because a small corpus
> gives little signal with which to estimate an importance score"* （引 zhang2023adalora、wang2024loraga、zanella2024cliplora）

**而 Paper A 摘要写着**：

> *"**which part of the model is adapted matters more than how its adapters are configured**"*

**→ 这是同一个命题。**

| | 综述 | Paper A |
|---|---|---|
| **命题** | site dominates allocation（小数据） | 位置比配置更重要 |
| **依据** | **文献归纳**（引 3 篇他人工作） | **自己的 204 个归档实验** + 理论推导 |
| **性质** | "**看起来稳健**"（appear robust） | **直接测量** |

**这不是抄袭或重复——是同一结论的两种独立来源。** 但**两篇互不引用**，构成一个**必须处理的风险**：

> 若两篇都发表，**同一位作者**在两处主张**同一命题**而**互不引用**——
> 审稿人一旦发现，第一反应是"自我重复"或"发表切分"（salami slicing）。

---

## 四、⚠️⚠️ 第二个风险：**同出版商**

| 稿件 | 出版商 | 状态 |
|---|---|---|
| PRL 综述 `PRLETTERS-D-26-02402` | **Elsevier**（Pattern Recognition Letters） | **Under Review** |
| Paper A → **CVIU / ESWA** | **Elsevier** | 待投 |

**→ 这是同一个出版商下的两篇**。虽**不同刊**，但 Elsevier 的投稿声明要求
"**not under consideration for publication elsewhere**"，
且**编辑部能看到作者在同出版商下的在审稿件**。

**加上 Paper A 与 P1（`PR-D-26-10149`，Pattern Recognition 在审）的关系**，
同一作者在 Elsevier 旗下将同时有**三个**在审/将投的相关稿件：

| 稿件 | 刊 | 关系 |
|---|---|---|
| P1 | Pattern Recognition（Elsevier） | Paper A 的**前身**（P1+P2 合并） |
| 综述 | PRL（Elsevier） | 与 Paper A **共享一条命题** |
| **Paper A** | CVIU/ESWA（Elsevier） | —— |

---

## 五、建议（按优先级）

### ① **两篇互相引用**（最要紧，且对双方都有利）

| 方向 | 理由 |
|---|---|
| **综述 → Paper A** | 综述第一条 robust 结论目前**只有文献归纳**。加上"并由直接实验证实（Paper A）"**会更强**——把"appear robust"升级为"confirmed by controlled experiment" |
| **Paper A → 综述** | Paper A 的"位置 > 配置"目前是**自己的新发现**；引用综述可把它定位为"**独立文献调查也支持这一命题**"→ **削弱"孤证"质疑，反而增强可信度** |

**两份稿件都还在审/未投，改动成本低。这是少见的"引用对方能同时提高两边"的情形。**

### ② 投稿信（cover letter）**主动披露**

Paper A 投 CVIU/ESWA 时，在封面信中说明：
- 与该综述的**关系**（综述问"框架对不对"，Paper A 给"直接测量 + 理论"）；
- 与该综述的**区别**（见本文档 §二：核心词汇零交集）；
- 与 **P1** 的关系（Paper A 是 P1+P2 的合并扩展，P1 在 Pattern Recognition 在审）——
  **这一条原本就要披露**（`docs/PAPERA_VENUE_OPTIONS.md` 已记录：同刊不违规、但需披露）。

### ③ 若期刊要求声明"相关稿件"，**如实列出**上表三行

---

## 六、局限

- "重叠"判断基于**命题层面**（综述 §3 首条 vs Paper A 摘要），**未做逐句文本比对**；
- 综述为在审稿件，**不应据本文档改动其内容**——若要加交叉引用，需按各刊修订规则处理；
- 词频统计为**词汇层面**，只能证明"某词未出现"，**不能证明"该主题未被讨论"**。

---

## 七、`site dominates allocation` 的处理（2026-10-07，操作者决定"综述不改"）

### 问题

| | 综述（`-02402`，在审） | Paper A |
|---|---|---|
| 表述 | §3 首条 robust 结论：*"**site dominates allocation** … which site is trainable matters more than how a budget is divided within it"* | 摘要：*"**which part of the model is adapted matters more than how its adapters are configured**"* |
| 依据 | 文献归纳（引 3 篇） | 自己的 **204 个实验** |
| 互引 | ❌ 未引 Paper A | ❌ 未引综述 |

**同一命题、两处主张、互不引用** → 有被读成自我重复的风险。

### 决定与做法

**操作者：综述不改**（在审期间不动）。故**只在 Paper A 侧解决**。

**不引用在审综述**（在审稿件引用不当），改为**引用综述所依据的 3 篇已发表文献**：

| key | 书目（**取自综述，非记忆**） |
|---|---|
| `zhang2023adalora` | Zhang, Q., Chen, M., Bukharin, A., Karampatziakis, N. (2023). *AdaLoRA: Adaptive Budget Allocation for Parameter-Efficient Fine-Tuning.* ICLR |
| `wang2024loraga` | Wang, S., Yu, L., Li, J. (2024). *LoRA-GA: Low-Rank Adaptation with Gradient Approximation.* NeurIPS |
| `zanella2024cliplora` | Zanella, M., Ben Ayed, I. (2024). *Low-Rank Few-Shot Adaptation of Vision-Language Models.* CVPRW |

**新增一节 `Placement Against Prior Work`**（置于 Design Patterns 之前），要点：

1. **承认文献基础**：单骨干场景前人已论证"位置比预算分配更重要"；
2. **指出其边界**：那些报告**只在一个骨干、一个语料**上测量 → **未确立排序的普适性**；
3. **把贡献锐化**：我们把排序当作**待检验假设**，在 **7 个骨干**上用统一协议（优化器只见适配器矩阵）测量；
4. **给出机制**：测量显示排序**由 patch size 决定**，非视觉-语言适配的通用属性；理论节给出产生它的机制。

**→ 好处**：既**承认文献**（避免"不看文献"与自我重复），又**保住贡献**（直接测量 + 边界 + 机制）。

### 实测结果（编译后）

| 项 | 值 |
|---|---|
| bib 条目 | **44 → 47** |
| cites | **47 = bib 47**（缺失 0、未使用 0） |
| NC / Springer | **49 页 / 37 页**，0 错误，0 未定义引用 |
| 页越界（像素法） | **无** |
| 三条引用渲染 | ✅ 作者-年份格式（`Zhang et al. (2023); Wang et al. (2024); Zanella and Ben Ayed (2024)`） |
| 参考文献表 | ✅ 三条均在（CLIP-LoRA 那条标题首字母小写，属正常大小写转换） |

脚本：`tools/_pa_add_site_dominates_refs.py`（幂等、带断言）
