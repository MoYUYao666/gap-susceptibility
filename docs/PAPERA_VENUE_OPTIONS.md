# Paper A 换刊评估（A-1）—— 依据、两处更正、与未完成项

> 生成：2026-10-06 ｜ 规则来源：`docs/REVIEW_VENUE_DECISION.md`、`docs/OA_FUNDING_ROUTES.md`
> 状态：**依据已核实 / 对比表未完成（阻塞项见文末）**

---

## 一、触发原因

`paper合/`（Paper A = P1+P2）原目标 **Neurocomputing**，但 **A1（`paper_a1/`）正在该刊在审**
（`NEUCOM-D-26-20952`，With Editor，2026-09-16 投）。此前我把这称为"**同刊冲突**"。
**核对官方指南后，此判断过重，应予更正。**

---

## 二、⚠️ 更正 ①：同刊发表**不是明文禁止**

### 指南原文（`期刊指南/_guide_neurocomputing.txt`）

指南"Co-submission of related data, methods or protocols"一节的原文是：

> "You are encouraged to publish a **description of your research data, m[ethods or protocols]** …"

→ 这是 **Elsevier 的 Data/MethodsX 配套机制**：把数据或方法说明作为**配套短文一并投**。
**与"同一期刊投两篇研究论文"毫无关系。**

### 真正的限制是哪一条

指南的投稿声明写的是：

> "The article is **not under consideration for publication elsewhere**."

→ 约束的是**该稿件自身**不得重复投出，**并不禁止同一作者在同一期刊有多篇相关稿件**。

### 更正后的结论

| 原判断 | 更正后 |
|---|---|
| "同刊冲突"，属**违规风险** | **不违规**，只需**如实披露**；真正的变量是**编辑的主观判断** |

（披露位置是**投稿系统的声明项**，不是正文，故不影响稿件内容。）

---

## 三、⚠️ 更正 ②：稿件声明**并无缺失**（我先前的判断错误）

我曾据 `paper合/sections/*.tex` 的 grep 结果，报告"缺少 CRediT / Competing interests /
Funding / 生成式 AI 声明"。

**实际这五节都在 `paper合/main_nc.tex:80–104`，且内容完整**：

| 节 | 行 | 内容要点 |
|---|---|---|
| Data availability | 80–86 | 所有结果 JSON 与分析脚本已归档于项目仓库（当前私有，发表后公开，可向审稿人提供）；无受限数据 |
| Funding | 88–90 | 未获任何专项资助 |
| Declaration of competing interests | 92–94 | 无已知竞争性利益 |
| CRediT authorship contribution statement | 96–98 | Hongrui Wan：Conceptualization, Methodology, Formal analysis, Investigation, Software, Validation, Visualization, Writing – original draft, Writing – review and editing |
| Declaration of generative AI … | 100–104 | 使用 Claude (Anthropic) 与 DeepSeek V4 起草/修订文本与代码，作者已复核并承担全部责任 |

**→ 是我的检索方法错误（只 grep 了 `sections/`，漏了主文件），不是稿件缺陷。**
**更正已落账。**

---

## 四、换刊的**硬约束**（有据）

### ① 免 APC 覆盖刊（硬约束：不付费）

取自 `docs/OA_FUNDING_ROUTES.md`，**三重独立证据**：
Southampton 官方页（"*most Elsevier hybrid journals*"）
+ **SciFree API 逐刊实测** `payment = Included in Publisher Agreement`
+ 操作者截图（三刊 `Included / CC BY / Hybrid`）。

**① 确定覆盖（£0）的 Elsevier hybrid**：

| 期刊 | 备注 |
|---|---|
| Neurocomputing | A1 在审；P1 曾被桌面拒 |
| Pattern Recognition | P1 在审（`PR-D-26-10149`） |
| Pattern Recognition Letters | P3 与 Commentary 在审 |
| **Image and Vision Computing** | 已存指南 `_guide_ivc.txt` |
| **Computer Vision and Image Understanding** | — |
| Neural Networks | P1 曾被桌面拒 |
| **Expert Systems with Applications** | 无拒稿史（见下方更正） |
| **Information Fusion** | Survey 类别主用于综述 |
| **Knowledge-Based Systems** | — |

（注：**IEEE 明确不在任何 Southampton 协议内**——IEEE 金色 OA 需自付 US$2,645。）

### ② 叠加"已拒稿史"（`文件地图.md`）

| 刊 | 与本题的关系 |
|---|---|
| **Neural Networks** | ⚠️ P1 **曾被桌面拒** |
| **Neurocomputing** | ⚠️ P1 **曾被桌面拒**；且 **A1 在此刊在审** |
| **Pattern Recognition** | P1 **正在此刊在审** |
| Pattern Recognition Letters | P3 与 Commentary 在审；且 **letters 刊篇幅不匹配 49 页** |
| **KBS / ESWA / IVC / CVIU / Information Fusion** | ✅ **无拒稿史** |

### ③ 结论：候选 = **5 个**

**KBS、ESWA、IVC、CVIU、Information Fusion**
（既免 APC、又未拒过本线工作）

**另一条更正**：`REVIEW_VENUE_DECISION.md` 已澄清——**操作者从未向 ESWA 投过任何稿件**
（那篇综述投的是 **EAAI**）。故 **ESWA 的同刊风险不存在**。

---

## 五、⚠️ **本阶段未完成**（诚实标注，不填空）

**我未能产出符合本项目标准的换刊对比表。**

**本项目规则**（`docs/REVIEW_VENUE_DECISION.md`）要求：
> ① 官方 Guide **存本地** ② 逐条对照并**写出出处行号** ③ 报告审稿速度**必须标注来源**

**本次取证遇到的阻塞**：

| 来源 | 结果 |
|---|---|
| ScienceDirect 官方 Journal Insights 页 | **HTTP 403** |
| journalmetrics.org | **HTTP 429** |
| LetPub | 页面零散、口径不一（KBS 一条 7.8 个月、另一条 2.8 个月） |

**→ 无可引用的官方数据**。按规则**不得用第三方数字填空**，故**对比表的
"审稿周期 / 篇幅上限 / 评审方式 / 文章类别"四列留空**。

### 完成 A-1 所需

**候选刊的 Guide for authors PDF**（操作者提供，或允许抓取）。
现有存档 4 份：Neurocomputing、PRL、IVC、OE（`期刊指南/`）。

**优先需要的 3 份**：**KBS**、**ESWA**、**CVIU**（IVC 已有）。

---

## 六、决策的**真正分岔**（不依赖外部数据也能判断）

| 选项 | 前提 | 代价 |
|---|---|---|
| **A. 等 P1 决定后投 Neurocomputing** | P1（`PR-D-26-10149`，Required Reviews Completed）出结果 | 等待时间不可控；且需披露与 A1 的关系 |
| **B. 直接投 Neurocomputing + 披露** | 编辑器不介意同刊相关稿 | 需在封面信说明与 A1 的区别；仍有被编辑判为重叠的可能 |
| **C. 投 5 个候选中之一** | 需先完成 Guide 对照 | 需重排格式、重写封面信；审稿周期未知 |

**建议**：**先做 C 的 Guide 取证**（拿到 PDF 即可 1–2 小时产出对比表），
再在 A / B / C 之间决定——**因为 C 的成本是"可预算的"，而 A 的等待是"不可控的"**。
