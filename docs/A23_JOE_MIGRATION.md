# A23 → IEEE JOE：Guide 硬性要求与迁移成本（实测）

> 记录日期：2026-09-24
> 依据：JOE 官方 Guide for Authors（`https://ieeeoes.org/publication/ieee-joe/guide-for-authors-ieee-joe/`，页面标注 updated 07 April 2026），本地全文提取件 `outputs/_joe_guide.txt`（150 行，供复核）
> 收件人确认：主编 **Karl von Ellenrieder**（`docs/A23_JOE_INQUIRY.md:4`）
> 投稿门户：**PaperCept** `https://controls.papercept.net/journals/joe`（不是 ScholarOne）

---

## 一、Guide 原文条款（决定性三条）

| # | 条款 | 原文 | 对我方的影响 |
|---|---|---|---|
| 1 | **篇幅** | "The length should be appropriate to the topic, **there is no specific limit**." | ✅ **OE 的"≤40 双倍行距页"顾虑作废**。66 页稿无需压缩 |
| 2 | **审稿格式** | "double-spaced in a single column, with 12 pt. font. Page and line numbers are required (note: line numbering should NOT reset to '1' at the top of each page)" | 需切到 IEEE 审稿排版：单栏 + 双倍行距 + 连续行号 |
| 3 | **拒稿史披露** | "If a manuscript was previously reviewed and rejected by any other publication, authors **must disclose this history at the time of submission**. Authors must provide **copies of the earlier decision letter** as well as **a response detailing how the Journal submission has addressed the decision letter issues**." | ⚠️ **强制**。A23 的 OE 桌面拒稿必须披露，且须附决定信副本 + 回应 |

### 其他已核实条款

- 摘要 **150–250 词**，"Over-length abstracts will be returned for editing"。现稿约 195 词 → **无需改动**。
- 需 **3–5 个 subject keywords**（`main.tex:35-37` 已有 `\begin{keyword}` 块）。
- **参考文献新增硬要求**："the JOE now requires that each online source in the bibliography include a **resolvable DOI link** where available, and if a DOI is not available, a stable locator such as an archival URL." → 29 条手工 `\bibitem` 需逐条补 DOI。
- 终稿阶段：双栏单倍行距 + 图表内嵌；`\usepackage{lineno}` 类行号；模板取自 `https://template-selector.ieee.org/secure/templateSelector/format?publicationTypeId=1&titleId=17&articleId=3`。
- 利益冲突声明：接受后仅允许改参考文献，不得新增文献（IEEE PSPB 8.2.1）。

> ⚠️ 本地提取的 Guide 正文里**没有** Technical Communication 的定义段落。该定义在 **JOE 的 Description 页**（`https://beacon.ieeeoes.org/publications/ieee-journal-of-oceanic-engineering/`，本地提取件 `outputs/_joe_desc.txt`），原文如下：
>
> - **Peer-reviewed Journal Article**："well-rounded treatments of a problem area describing an original contribution to ocean science and technology. These articles may also represent **comprehensive contributions of a theoretical or analytical nature**."
> - **Technical Communication**："a **concise and focused** study or analysis. Literature and technology reviews, system performance and tradeoff studies, innovative applications of existing technology, are all valid technical communication contributions."
>
> 判据因此是**论述的体量与完备度**（well-rounded / comprehensive ↔ concise and focused），不是"哪个更像工程"。**结论：投 Article**，理由见第六节。

---

## 二、迁移成本（用实测计数，不用估）

`paper_a2/main.tex`：901 行，`\documentclass[review,authoryear]{elsarticle}`（`:1`），`\journal{Ocean Engineering}`（`:13`）。

| 项 | 实测计数 | 工作量 | 风险 |
|---|---|---|---|
| `frontmatter` 环境 | 2（起止各一） | 小：改写为 IEEEtran `\author` 块 | 低 |
| `\affiliation[` | 1 | 小 | 低 |
| `\journal{` | 1 | 小：删除 | 无 |
| `\citet` / `\citep` | **34** | 中：改 `\cite`；**且作者-年份作主语的句子需改写**（"Wan (2026) showed" → "Wan et al. [12] showed"），非纯 sed | **中** |
| `\cite{`（纯数字式，已是） | 0 | — | — |
| `\bibitem`（**手工文献表**） | **29** | **大**：author-year → IEEE 数字式，按首次引用排序，并**逐条补 DOI / 稳定 URL** | **中高** |
| `\bibliography{}`（BibTeX） | 0 | 说明无 .bib 可自动换样式，全靠手改 | — |
| `figure*` / `table*`（双栏浮动） | 0 | 无 | 无 |
| `highlights` / `graphicalabstract` | 0 | 无 | 无 |

**结论：模板切换本身是小的（preamble + frontmatter，约 1 小时）；真正的工作量在 29 条文献表的 IEEE 化与 DOI 补全，以及 34 处引用命令的语义改写。** 这是一次"排版 + 文献"返工，不是内容重写；正文论证、数字、图表、声明章节均不动。

**格式副作用**：单栏 + 双倍行距会把 66 页（双栏单倍）拉到约 90–110 页。因**无篇幅上限**，合规；但送审 PDF 偏厚，属观感问题而非规则问题。

---

## 三、与旧清单的差异（`docs/A23_VENUE_DECISION.md` 第四节）

| §4 原条目 | 现状 |
|---|---|
| 篇幅"新刊政策未知，须重新核" | ✅ **已核：无上限**，该顾虑关闭 |
| 摘要"新刊上限若更严需再压" | ✅ **已核：150–250 词**，195 词合规，无需改动 |
| 刊名 / "Fit with the journal" 段 / OE 专属 in-scope 句 | ✅ 封面信已重写（2026-09-24），相关句已替换为 JOE 的 field-of-interest 表述 |
| 参考文献 DOI | ⚠️ **新增项**（Guide 新规），29 条需补 |
| 正文、图、结果、声明、highlights、abstract 文件 | 不变（`\journal{}` 一行除外） |

---

## 四、披露口径的更正（重要）

`docs/A23_JOE_INQUIRY.md:42` 原写：

> 不提 Ocean Engineering 桌面拒稿（与 JOE 无关）。若被直接问是否投过别处/被拒过，如实回答……

**该口径作废。** 它写于 2026-09-16/18，当时**尚未读 JOE Guide**。Guide 第 3 条要求**投稿时即须披露**，并把"直接问"变成投稿动作本身。因此：

- 新版 `paper_a2/cover_letter.tex` 已加入 **"Prior submission history (disclosure)"** 段，主动点名 `OE-D-26-11643`、2026-09-16 提交、**2026-09-18** 决定（Executive Editor Yan Wei），并给出回应。
  - ⚠️ **日期更正**：此前多处（含本文件旧稿、`A23_JOE_INQUIRY.md` 旧备注）写"当日桌面拒稿"。**错误。** 以决定信原文为准：`Submit Date: Sep 16, 2026`，邮件日期 `2026年9月18日 星期五 15:54:45 中国标准时间` → **9-16 提交，9-18 决定，隔两日**。证据：`outputs/_oe_decision.txt`（由操作者提供的 PDF 提取）。
- 回应内容**只写可核实的事实**：桌面决定**无审稿意见、无技术异议**（见 `A23_VENUE_DECISION.md:17`），scope 顾虑由 JOE 的 field of interest 与 EIC 回信直接化解。
- **未写任何尚未执行的改动**（例如格式迁移、`\journal{}` 改名），因为这些还没做。
- 这**不算"补充说明"而是必须项**：隐瞒已被拒稿史属 Guide 列明的 ethics 问题。

---

## 五、待操作者提供/决定

1. ~~**OE 决定信副本**（Guide 强制附交）~~
   ✅ **已完成 2026-09-24**：操作者提供 `C:\Users\hongr\Desktop\Editor Decision - Reject - Pre-Review (Out of Scope).pdf`，已装入 `SUBMISSION/A23_JOE/supplementary/A23_OE-D-26-11643_decision_letter.pdf`（106.1 KB），并在 `outputs/_oe_decision.txt` 留文本提取件作证据。附件包三项**已齐**。
2. **TC vs Peer-Reviewed Article** → ✅ **已判定：Article**，见第六节。
3. **是否做格式迁移** → ✅ **已于 2026-09-24 完成**，见第七节。**本文件已无待办事项。**

---

## 六、TC 还是 Article：以 JOE 官方定义判定 → **Article**

### 判据来自 JOE 自己的定义（非推测）

| | 原文 | 关键词 |
|---|---|---|
| **Journal Article** | "well-rounded treatments of a problem area describing an original contribution… may also represent **comprehensive** contributions of a theoretical or analytical nature" | well-rounded / comprehensive |
| **Technical Communication** | "a **concise and focused** study or analysis. Literature and technology reviews, system performance and tradeoff studies, innovative applications of existing technology…" | **concise and focused** |

即：这是**论述体量与完备度**的区分，**不是**"哪个更像工程"。主编回信里"TC = 技术开发/工程集成"是宽松概述，官方定义才是准绳。

### 为什么是 Article

1. **体量对不上 TC 的定义。** 本篇 66 页、5 个感知域、4 台声学仪器、完整理论附录（界 + 算子 + 每图像形式）、外加工程规程。这是 JOE 所谓 "well-rounded / comprehensive" 的教科书案例，而 TC 的定义是 "concise and focused"。**把 66 页压成 TC 不是换栏目，是换论文。**
2. **理论贡献在 Article 里被明文许可。** 定义里 "comprehensive contributions of a theoretical or analytical nature" 一句正是本篇的核心（序保持预测器、top-1 界、方向分解算子）。若投 TC，反而要把理论砍掉。
3. **TC 的诱人之处是个陷阱。** TC 明确接纳 "system performance and tradeoff studies"，看起来贴合本篇的"监测阈值 + 适配决策表"。但那是本篇的**收尾章节**，不是全文；用 TC 投等于用一个章节去代表一篇论文。
4. **框架风险已被 EIC 回信消掉。** TC 唯一潜在好处是"往工程靠、避 scope 风险"。但 EIC 已书面确认 generally in scope —— 这个对冲不再必要。反之，**为对冲而把方法学研究包装成工程集成，正是 OE 那次栽跟头的同一类错误**（当时是主题词命中就当作贡献类型命中）。同一个错犯两次代价更大。
5. **TC 并不更"快"也不更"松"。** EIC 明确 TC "same rigor"；审稿严格度相同，收益仅剩篇幅更短，而本篇**无篇幅上限**（第一节），这个收益本身就消失了。

### 什么情况下才该改投 TC

只有当你愿意**换一篇论文**：砍掉理论附录、砍掉跨域矩阵与四台仪器的复现，只留"面向从业者的监测与适配规程"这一个 focused study。那会是一篇合法的 TC，但会丢掉本篇最不可替代的部分（跨模态可迁移性证据 + 理论界）。**不建议。**

---

## 七、格式迁移：已完成（2026-09-24）

**产物**：`paper_a2/main_ieee.tex`（940 行）+ `main_ieee.pdf`（**64 页 / 0 错误 / 0 undefined / 0 未解析引用 / Overfull>20pt 为 0**）。
elsarticle 原稿 `main.tex` **保留不动**（66 页，仍可编译），迁移不破坏任何既有产物。
生成脚本：`tools/_a23_make_ieee.py`（可重跑，幂等，含条目数守恒断言）。

### 审稿排版：不是照抄模板，是量出来的

| JOE 要求 | 做法 | 实测证据 |
|---|---|---|
| 单栏 | `onecolumn` | 最宽文本行 104 字符（双栏通常 50–60） |
| 12 pt | `12pt` | 编译日志确认正文 12pt 字体 |
| **双倍行距** | `\setstretch{2.0}` | **27.74 pt ÷ 13.92 pt（IEEEtran 12pt unity baselineskip）= 1.99×** |
| 页码 + 行号，且行号不得每页重置 | `lineno` + `\linenumbers` | 第 3 页 41–64、第 4 页 65–88 —— **连续，不重置** |
| 去除页眉页脚文字 | `draftclsnofoot` | 全文大写 `DRAFT` **0** 次；日期戳 **0** 次 |

测法：`tools/_a23_linegap_ruler.py` 用**行号标记本身**的垂直间距量行距（每个行号对应一个排版行，故间距即精确基线间距），并换算成 unity baselineskip 的倍数。

### ⚠️ 三个坑：照抄 IEEE 模板会中招，且肉眼难发现

1. **IEEEtran 的 `draftcls` 自带 `\baselinestretch{1.5}`**（`IEEEtran.cls:951`）→ 默认行距已是 **20.80 pt = 1.49×**，即"一倍半"。看起来"挺松的"，但**不是双倍**。
2. **setspace 的 `\doublespacing` 其实是 `\setstretch{1.667}`** → 只到 **22.95 pt = 1.65×**。这是最危险的一条：**按最常规的写法（`\usepackage{setspace}` + `\doublespacing`）交出去，稿子并不满足 JOE 的双倍行距要求**，而页数与观感都在"像是双倍"的范围内，肉眼与常规检查都不会报警。必须显式 `\setstretch{2.0}`。
   - 佐证：页数从 55（1.65×）到 64（2.0×），**只差 9 页**，不足以引起怀疑。
3. **`draftcls` 在每页页脚压上日期与 "DRAFT"**，而 JOE Guide 明写 "remove text in the document header" → 必须用 `draftclsnofoot`。

### 引用与文献

- `\citep{}` → `\cite{}`：**33 处**（IEEE 数字式天然落在名词短语后、句号前，无需改写句子）。
- 唯一一处 `\citet`（`main.tex:821`，位于括号内）若直接转换成数字式会变成**双层括号**，已改写为 `\ldots debris release \cite{mvaldenegro2024}`。
- 5 个 `\input` 扩展文件（ext_partI–V）**与 elsarticle 共享**，其中 `ext_partIII_dynamics.tex:65` 有一处 `\citep`。处理方式是加**兼容层** `\providecommand{\citep}[1]{\cite{#1}}`，**不为迁移 fork 共享文件**（fork 会让两版永久分叉）。
- 文献表按**首次引用顺序**重排 29 条，去掉 author-year 标签，改 IEEE 数字式。

### DOI 审计：新增 7 条，全部经 Crossref 命中 + 解析验证

| key | DOI | 验证方式 |
|---|---|---|
| liang2022 | `10.52202/068431-1280` | Crossref 标题精确命中（NeurIPS 35, 2022）；解析 200 |
| yamaguchi2025 | `10.1109/CVPR52734.2025.00402` | Crossref 精确命中；解析至 IEEE 落地页 |
| sofer2025 | `10.21437/Interspeech.2025-1664` | Crossref 精确命中；解析 200 |
| wortsman2022 | `10.1109/CVPR52688.2022.00780` | Crossref 精确命中；解析至 IEEE 落地页 |
| marinegpt2023 | `10.48550/arXiv.2310.13596` | 解析 200 → arxiv.org/abs/2310.13596 |
| yi2025 | `10.48550/arXiv.2510.03268` | 解析 200 |
| sonarsurvey2025 | `10.48550/arXiv.2510.03353` | 解析 200 |

结果：**17 条带 `doi:`，12 条带稳定 URL**（`[Online]`/`\url`）。

**以下 6 条确无 DOI 可用**（Crossref 无记录，不是遗漏）：`levi2025`、`mistretta2025`、`grassucci2026`（ICLR/ICML 经 PMLR/OpenReview，不注册 DOI）、`chowers2026`（CVPR 2026 尚未索引）、`biderman2024`（TMLR 无 DOI）、`radford2021`（ICML/PMLR 无 DOI）。按 Guide 的 "where available" 以会议名+年份著录。
**未臆造任何一条 DOI** —— 查询与解析原始输出留档在 `outputs/_a23_doi_candidates.txt` 与 `outputs/_a23_doi_verify.txt`。

### 顺带修掉一处内容性假陈述

正文原写 "**Within this journal** the trajectory is already visible"，并引 `christensen2026`（maritime situational awareness）与 `maione2026`（agentic AI for marine condition monitoring）—— **这两篇都是 Ocean Engineering 上的论文**。投 JOE 后该句为**假**。已改为刊物中性的 "Within the marine engineering literature"，并在 `main.tex` / `main_ieee.tex` / `main_zh.tex` **三处同步**（中文镜像原文更露骨：写作"本刊（\textit{Ocean Engineering}）"，同改）。

> 注：封面信里指向 JOE 的那句引用（Aubard et al. 2025, `10.1109/JOE.2025.3531933`）**是真 JOE 论文**，无需改动。

### 合规核对（全部实测）

| 项 | 状态 |
|---|---|
| 摘要 194 词（要求 150–250） | ✅ |
| 关键词 | 由 **7 个裁到 5 个**（要求 3–5，原稿超限）——裁掉 `direction-resolved operator`、`underwater perception` |
| 篇幅 | 无上限，64 页合规 |
| 参考文献 DOI | 17 条 DOI + 12 条稳定 URL，无臆造 |
| `\journal{}` | 随前言替换已消失 |

---

## 八、提交完成（2026-09-21 系统时间）

| 项 | 值 |
|---|---|
| **稿号** | **`26-0663`** |
| 版本 | 1 |
| 类型 | **Research Article** |
| 状态 | **Received** |
| 门户 | PaperCept `https://controls.papercept.net/journals/joe` |

> 系统显示 September 21, 2026，而本地文件时间戳为 9-22（中国标准时间）：系统按美区时间，两者一致，**不是传错版本**。

**实传三个文件**（均在限额内）：

| 槽位 | 文件 | 大小 / 页数 | 限额 |
|---|---|---|---|
| Manuscript | `paper_a2/main_ieee.pdf` | 1,221 KB / 64 | ≤5 MB |
| Cover Letter | `paper_a2/cover_letter.pdf` | 126 KB / 3 | ≤2 MB |
| Supplementary Material for Reviewers | `SUBMISSION/A23_JOE/supplementary/SUPPLEMENTARY_FOR_REVIEWERS.pdf` | 1,040 KB / 43 | ≤2 MB（单文件） |
| Multimedia Supplement | （留空） | — | 仅收 mpg/mpeg/mp4 |

### 提交时踩过的两个坑（供下次复用）

1. **LaTeX 源包的主文件必须叫 `root.tex`**（或与 zip 同名）。原命名为 `main.tex` 被门户拒绝：
   > "This zip file contains several tex files but none that is named root.tex or A23_latex_source.tex"
   
   已改名为 `root.tex`；实测解压后 `pdflatex root.tex` 两遍 → 64 页 / 1,250,435 bytes，与 `main_ieee.pdf` **字节数一致**。
2. **附件槽只收单个 ≤2 MB 的 PDF**，而原附件包是三份共 3.5 MB / 85 页。装得下的恰是两项硬要求：Guide 强制的决定信（106 KB）+ EIC 明确要求的 A1（769 KB）。P1（2,646 KB）装不下，改为索引页 + 封面信双处写明"索要即提供"，**未静默丢弃**。

### 提交前修正的两处合规问题

1. **AI 披露位置**：原在独立的 `Declaration of generative AI…` 段（Elsevier 惯例），而门户勾选框要求 "in the **Acknowledgment** section"。已在 IEEE 版迁入致谢并补 "generative AI tools" 字样（见第七节）；elsarticle 母本保持不动。
2. **"Previously submitted as" 字段**：填 `OE-D-26-11643`（跨刊拒稿的真实编号），**不能填 "Not applicable"**——否则与本稿封面信已主动披露的拒稿史自相矛盾。

### 尚未答复的字段（提交时已填，留档核对）

- `Previously presented` → `Not Applicable`（全库检索无会议宣读记录）
- `Previously submitted as` → `OE-D-26-11643`
- `Human and animal research disclosure` → `No`（全部为公开影像数据集，无人类受试者、无动物实验）

