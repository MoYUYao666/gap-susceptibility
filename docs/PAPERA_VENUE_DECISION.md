# Paper A 目标刊决策（A-1）—— 5 个候选刊逐条对照

> 生成：2026-10-07 ｜ 输入：操作者提供的 5 份 **Guide for authors** PDF（桌面 → `期刊指南/`）
> 提取脚本：`tools/_venue_guide_extract.py`、`tools/_venue_guide_deep.py`、`tools/_venue_length_check.py`
> **规则**：每字段取自 Guide 原文；未提及者明确写"未提及"，**不填第三方数字**

---

## 一、候选来源与硬约束

**候选 = 同时满足两个条件者**：

1. **免 APC**（`docs/OA_FUNDING_ROUTES.md`：Southampton Jisc–Elsevier 协议**逐刊实测**覆盖 → £0）
2. **未拒过本线工作**（`文件地图.md` 拒稿史）

| 刊 | 全名 | ISSN | 免 APC | 拒稿史 |
|---|---|---|---|---|
| **ESWA** | Expert Systems with Applications | 0957-4174 | ✅ | 无 |
| **KBS** | Knowledge-Based Systems | 0950-7051 | ✅ | 无 |
| **CVIU** | Computer Vision and Image Understanding | 1077-3142 | ✅ | 无 |
| **IVC** | Image and Vision Computing | 0262-8856 | ✅ | 无 |
| **IF** | Information Fusion | 1566-2535 | ✅ | 无 |

（排除：`Neural Networks`/`Neurocomputing` = P1 曾桌面拒；`Pattern Recognition` = P1 在审；`PRL` = 在审且 letters 刊篇幅不符）

---

## 二、逐条对照（**原文引用，可复核**）

### ① 匿名方式（决定工作量）

| 刊 | 原文 | 判定 |
|---|---|---|
| **ESWA** | *"This journal follows a **double anonymized** review process"* | ⚠️ **双盲** → 须拆**题名页 + 匿名稿**两个文件 |
| **KBS** | *"This journal follows a **single anonymized** review process"* | ✅ 单盲（作者信息保留） |
| **CVIU** | *"…a **single anonymized** review process"* | ✅ 单盲 |
| **IVC** | *"…a **single anonymized** review process"* | ✅ 单盲 |
| **IF** | *"…a **single anonymized** review process"* | ✅ 单盲 |

> ESWA Guide 目录中另有独立条目 **"Double anonymized peer review"**，与上述表述一致。

### ② 篇幅规定（**决定性**）

| 刊 | 原文 | 对 11,254 词的判定 |
|---|---|---|
| **ESWA** | **未提及**篇幅上限（穷举 `page limit`/`no more than`/`not exceed`/`maximum`/`word count` 等 9 类关键词，仅命中摘要 250 词与 Highlights 85 字符） | ✅ **无需压缩** |
| **KBS** | Articles types：*"(1) Original high-quality research and review papers (**preferably no more than 20 double line spaced manuscript pages**, including tables and figures)"* | ⚠️ **"preferably"（非硬性）**，但 20 页双倍行距 ≈ 5,000 词 → **我们约 2.2 倍** |
| **CVIU** | **未提及**篇幅上限 | ✅ **无需压缩** |
| **IVC** | *"the acceptable **word count range is 4500-7500 words**"*（排除参考文献、图注、表内容、图片内可选文本、参考文献之后的章节） | ❌ **我们约 11,254 词，超上限约 50%** |
| **IF** | Research article：*"Manuscripts **must be 10–35 pages**"*；*"**Maximum 50 references**"*；且 *"Failure to comply with these formatting requirements, length limits … may result in **desk rejection**"* | ❌ **我们约 45–52 页（双倍行距）→ 超 35 页**；引用 44 条 ✅ 达标 |

### ③ 其余字段（均已达标，无差异）

| 字段 | 5 刊要求 | 我们现状 | 判定 |
|---|---|---|---|
| **摘要** | 均 *"does not exceed **250 words**"* | **244 词** | ✅ 全部达标 |
| **关键词** | 均 *"**1 to 7** keywords"* | **6 个** | ✅ 全部达标 |
| **Highlights** | KBS/ESWA = *encouraged*；IVC/CVIU/IF = *required*；均 *"3 to 5 bullet points, each a maximum of **85 characters**"* | **5 条，最长 61 字符** | ✅ 全部达标 |
| **Graphical abstract** | KBS/ESWA 未提及；CVIU/IF = *encouraged*；**IVC = required** | 无 | ⚠️ 仅 IVC 强制（但 IVC 已因字数出局） |
| **Research data** | 均 *"**Option C** instructions … apply"* → **必须**存入仓库 + 引用链接 + 否则给理由 | 稿件已写"私有仓库、发表后公开、可向审稿人提供" | ⚠️ **Option C 要求"存入仓库"，需核对措辞是否满足** |

---

## 三、结论：**2 个可行、3 个出局**

| 判定 | 刊 | 理由 |
|---|---|---|
| ❌ **出局** | **IVC** | 字数控 **4500–7500**，我们超约 50% |
| ❌ **出局** | **IF** | 页数硬上限 **10–35**，我们约 45–52；且明示超限可 **desk rejection** |
| ⚠️ **勉强** | **KBS** | "**preferably** ≤20 双倍行距页"，我们约 2.2 倍——**非硬性**，但风险实在 |
| ✅ **可行** | **ESWA** | 无篇幅上限；但**双盲** → 须拆题名页 |
| ✅ **可行** | **CVIU** | 无篇幅上限；单盲 |

### 建议顺序

| 首选 | **ESWA** | 无篇幅上限；单盲以外唯一门槛是**双盲拆分**（一次性工作）；范围"expert and intelligent systems"能容下方法类工作 |
| 次选 | **CVIU** | 无篇幅上限 + **单盲**（工作量最小）；但**范围偏视觉/图像理解**，本文是表征分析而非视觉任务，**scope 匹配度需自评** |
| 备选 | **KBS** | "preferably 20 页"风险实在，**除非压缩** |

> **⚠️ 一处须诚实标注**：**篇幅换算为估算**。三种口径给出 23 页（LaTeX 源行数）、45 页（正文词数÷250）、52 页（PDF 全文词数÷250），差异大。
> **口径 ① 明显低估**（LaTeX 一行常含多句）。**采信 ②③：约 45–52 页**。
> **最终判定须用目标刊 LaTeX 模板实排**——这仍是**未完成项**。

---

## 四、待办（按顺序）

1. **确认选刊**（ESWA 或 CVIU）——待操作者决定；
2. **若 ESWA**：制作**双盲版**（题名页与匿名稿分离，致谢与竞争利益声明只放题名页）；
3. **核对 Option C**：数据可用性措辞是否满足"存入相关仓库 + 引用链接"；
4. **用目标刊模板实排**，得出权威页数（替换本文的估算）；
5. 重写**封面信**（含与 A1 的披露，按 `docs/PAPERA_VENUE_OPTIONS.md` 结论：同刊不违规、只需披露——若选 ESWA 则**不同刊，无需披露同刊问题**）。

---

## 五、实证明查：候选刊**近年实际刊载内容**（2026-10-07 追加）

**动机**：Guide 只给"研究领域"（CVIU 列有 "Data structures and representations" 与 "Theory"），
**不能回答"该刊实际收什么"**——而这才决定 desk-reject 风险。故用 **OpenAlex API**（公开、可复核）实查。

### 四轮核查，方法逐轮修正

| 轮次 | 脚本 | 方法 | 结果 |
|---|---|---|---|
| 1 | `_venue_content_survey.py` | 关键词分类，每刊 200 篇（2024 起） | ⚠️ **假阳性严重**：`rank` 命中 "Rank Graduation Box"、`convergence` 命中 "Hiking Optimization Algorithm"、`embedding` 命中 "knowledge graph embedding"。**且 CVIU 的"表征类"样本全是视觉任务**（Video Anomaly Recognition、light-field super-resolution、RGB-D semantic segmentation）——只是**碰巧提到 embedding** |
| 2 | `_venue_topic_probe.py` | 用**本文主题词**检索 | ✅ CVIU：`parameter-efficient fine-tuning` **48**、`vision-language alignment` **28**、`LoRA` **11** → **有大量同类技术先例**。但返回标题**全是"方法应用到具体视觉任务"** |
| 3 | `_venue_analysis_probe.py` | 区分「**分析类**」vs「任务类」措辞 | ⚠️ **返回标题与检索词不对题**（如查 `understanding representation collapse` 返回 *"Escaping the big data paradigm in self-supervised representation learning"*）→ **OpenAlex 为宽泛 OR 匹配，计数被夸大** |
| 4 | 目视逐条核对返回标题 | —— | **无一篇是"分析优先"的论文** |

### 决定性观察

CVIU / ESWA / KBS **都在发 VLM + PEFT 的工作**，但形态**一致**：

> **"把方法应用到具体任务"** —— semantic segmentation、medical image segmentation、
> anomaly detection、depth human parsing、video inpainting …

**没有观察到任何一篇"以分析表征几何 / 训练动态本身为目的"的论文。**

→ 本文（**分析优先 + 理论**：383 实验、5 架构、3 种 PEFT 方法）与这 5 个刊的
**实际刊载形态不匹配**。**这是 scope 风险的真实来源，且用检索无法消除。**

### ⚠️ 核查的**局限**（诚实标注，不夸大结论）

1. OpenAlex 为**宽泛匹配**，**计数不可当作精确篇数**（已由返回标题证实不对题）；
2. 未取得**完整目录**（ScienceDirect 返回 **403**）→ 样本非全体，**不能断言"该刊从不收"**；
3. 分类规则由我编写，**已目视发现假阳性**，故**采信"返回标题"而非"计数"**；
4. 仅在英文**标题/摘要**层面检索，**未逐篇读正文**，故"是否分析优先"依标题判断，可能有偏差。

→ **结论强度：方向可信（四轮同向），但不是穷尽证明。**

### 数据落盘（可复核）

- `outputs/analysis/venue_content_survey.json`
- `outputs/analysis/venue_topic_probe.json`
- `outputs/analysis/venue_analysis_probe.json`

### 对结论的影响

**先前推荐 ESWA（首选）/ CVIU（次选），依据是 Guide 的篇幅与流程条件——那些条件仍然成立**
（ESWA/CVIU 无篇幅上限、CVIU 单盲且首轮 3.7 月、ESWA 首轮 5.4 月）。

**但本次核查表明：scope 风险对两刊同样实在，且不因换刊而消除。**

**→ 决策实为三选一**：

| 选项 | 做法 | 风险 |
|---|---|---|
| **1. 改包装 → ESWA** | 把表征分析落到**可复用的设计准则/实用指南**，命中其 *"design, development, testing, implementation … practical guidelines"* 措辞 | 需重写引言的 framing；仍可能被判非系统类 |
| **2. 改包装 → CVIU** | 把**视觉侧**结论前置，弱化文本/NLP 侧；强调 "Data structures and representations" | 需重写 framing；仍可能被判非图像理解 |
| **3. 另找 scope 真正对的刊** | 当前 5 个候选**均非"分析型"定位** | 需重新取证（且须复核免 APC 与拒稿史） |

---

## 六、选项 3：反查「这类论文实际发在哪」（2026-10-07 追加）

## 本轮方法（第 5、6 轮，逐轮修正）

| 轮 | 脚本 | 方法 | 问题 / 收获 |
|---|---|---|---|
| 5 | `_venue_reverse_lookup.py` | 全文 `search=` | ⚠️ 总命中 **3–4 万** → 松匹配，计数不可信 |
| 6 | `_venue_modality_gap_venues.py` | **`title.search=`（仅标题）** | ✅ 总量合理（99 / 352 / 257 篇），**信号干净** |

## 第 6 轮结果（标题级精确）

| 标题短语 | 总量（2023 起） | 第一梯队 |
|---|---|---|
| `modality gap` | **99 篇** | Zenodo **20**（预印本库，非期刊）｜**EAAI 3**｜IEEE RA-L 2｜IEEE TMM 2｜**ESWA 2**｜**PR 1** |
| `cross-modal alignment` | **352 篇** | **Neurocomputing 7**｜IEEE TCSVT 6｜ACM TOMM 6｜IEEE Access 5｜**KBS 5**｜**IF 5**｜**PR 4** |
| `parameter-efficient fine-tuning` | **257 篇** | **Neurocomputing 8**｜**IEEE TPAMI 6**｜**IJCV 5**｜**Neural Networks 5**｜**PR 3** |

（🆓 = 在 `docs/OA_FUNDING_ROUTES.md` 免 APC 清单内）

## 两个决定性结论

### ① 主题本身**很窄**
`modality gap` 三年仅 **99 篇**（且 **20/99 在 Zenodo 预印本库**）——**这不是一个拥挤的领域**。
好处：**没有"已被做烂"的风险**；坏处：**没有稳定的对口刊**，各刊都是零散收录。

### ② 最优 scope 的刊 ↔ **免 APC 清单，几乎不重叠**

| 主题第一梯队 | 是否免 APC | 有无障碍 |
|---|---|---|
| IEEE TPAMI / IJCV / IEEE TCSVT / IEEE TMM | ❌ **IEEE 明确不覆盖** | 自付 US$2,645（JOE 官方价） |
| Zenodo（20/99） | — | **不是期刊**（预印本库） |
| **Neurocomputing**（7 + 8 篇，两榜第一） | ✅ | ⚠️ **P1 曾桌面拒**；且 **A1 在此在审** |
| **Pattern Recognition**（4 + 3 篇） | ✅ | ⚠️ **P1 在此在审**（`PR-D-26-10149`） |
| **Neural Networks**（5 篇） | ✅ | ⚠️ **P1 曾桌面拒** |
| **KBS**（5 篇） | ✅ | ⚠️ Guide *"preferably ≤20 double line spaced pages"*（我们约 2.2 倍） |
| **Information Fusion**（5 篇） | ✅ | ⚠️ 页数硬上限 **10–35**（我们约 45–52） |
| **ESWA**（2 篇） | ✅ | ⚠️ 双盲；**scope 偏系统/应用** |
| **EAAI**（3 篇，`modality gap` 榜第二） | ❓ **未逐刊核实** | 见下 |

**→ 免 APC 且有主题先例的刊，全部带一项实质障碍**（拒稿史 / 在审冲突 / 篇幅 / 口径）。

### ③ 新发现：`Engineering Applications of AI`（EAAI）

- `modality gap` 标题级 **3 篇**，在**非预印本期刊中排第二**（仅次于若干 IEEE 刊）；
- **但**：抽看其论文形态仍是 **"方法 + 任务"**
  （*"Denoising diffusion bridge for cross-modal alignment in **3D scene understanding**"*、
  *"A universal parameter-efficient fine-tuning approach for **stereo image super-resolution**"*）
  → **与第 1–4 轮的结论一致：这些刊要"落到任务"**；
- **且 EAAI 不在** `docs/OA_FUNDING_ROUTES.md` 的"① 确定覆盖"9 刊清单里
  → 属**"② 需逐刊核实"**（它虽是 Elsevier hybrid，非 fully-OA，但**未逐刊实测**）。

## ⚠️ 本轮局限（诚实标注）

1. **样本小**：`modality gap` 三年仅 99 篇，各刊计数为个位数 → **统计噪声大**；
2. **`title.search` 仍是 OpenAlex 的匹配**，非权威目录（ScienceDirect 全程 403）；
3. **Zenodo 20/99** 说明该主题相当比例尚未正式发表 → **venue 信号本身偏弱**；
4. **未读正文**，形态判断依标题。

**→ 结论：这是"方向性"证据，足以否掉"某个免 APC 刊是天然对口"的想法，但不足以指定唯一目标刊。**
