# 投稿期刊 SCI 收录登记表（VENUE SCI REGISTRY）

> 规则来源：操作者 2026-10-24 原话 **"不管投哪，必须是SCI期刊，记录进规则"**
> （已写入 `AGENTS.md` / `CLAUDE.md` 的「🔴🔴 投稿目标必须是 SCI 期刊」节）。
> 本表是这条规则的**唯一登记入口**：任何投稿目标在写进方案/cover letter/对外文档之前，必须在本表有一行。

## 1. 判定标准

- **合格**：Web of Science Core Collection 的 **SCIE**（Science Citation Index Expanded）。
- **不合格**：ESCI-only、Scopus-only、无 WoS 收录、纯预印本平台。
- **预印本**（arXiv/Zenodo）：可用于占位与引用，**不算投稿目标**，不能替代期刊发表要求。
- **例外**：仅当操作者书面同意，并在本表登记"经操作者同意 + 日期 + 原话"。

## 2. 核实流程（每次投稿前执行，必须留痕）

1. 打开 **Clarivate Master Journal List**（`mjl.clarivate.com`），用刊名或 ISSN 检索；
2. 确认该刊在 **Science Citation Index Expanded** 的收录列表内（若显示 ESCI，则**不合格**）；
3. 交叉核对**出版商官网**的 "Abstracting & Indexing" / "Journal metrics" 页；
4. 第三方（LetPub、MIAR、JCR 分区表）**只能作旁证**，不能单独作为依据；
5. 在本表第 3 或第 4 节登记：`刊名 | ISSN | 出版商 | 收录=SCIE | 来源URL | 核实日期 | 核实人`；
6. 未登记 = 未核实 = **不得投稿**。

## 3. 当前五篇的投稿目标（已投/在审，历史事实）

> **✅ 2026-10-25 已按 §2 完成 MJL 复核（task-26）**：五条目标刊物全部在 Clarivate Master Journal List
> 上显示 **Web of Science Core Collection: Science Citation Index Expanded** ⇒ `收录类型` = **SCIE**。
> 逐条证据摘录、访问路由与未取得的第二来源见 `docs/venue_sci_reverification_2026-10-25.md`。
> **没有一条是 ESCI-only / Scopus-only，本轮没有任何刊物被取消资格。**

| 稿件 | 刊名 | ISSN（print / eISSN） | 出版商 | 收录类型 | 核实来源 URL（精确，MJL） | 核实日期 | 核实途径 | 稿号 / 状态 |
|---|---|---|---|---|---|---|---|---|
| Paper A（`paper合/`）| Neurocomputing | 0925-2312 / 1872-8286 | Elsevier | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0925-2312&hide_exact_match_fl=true` | **2026-10-25** | Edge CDP 代理（web-access）；MJL 为 JS 单页应用，静态 fetch 只返回标题 | `NEUCOM-D-26-23760`（With Editor）|
| A1（`paper_a1/`）| Pattern Analysis and Applications | 1433-7541 / 1433-755X | Springer | **SCIE** | `https://mjl.clarivate.com/search-results?issn=1433-7541&hide_exact_match_fl=true` | **2026-10-25** | 同上；第二来源已获：`https://link.springer.com/journal/10044`（"Abstracted and indexed in … Science Citation Index Expanded (SCIE)"）| `0a4629f0-…`（With editor）|
| P3（`paper3/paper_ieee/`）| Pattern Recognition Letters | 0167-8655 / 1872-7344 | Elsevier | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0167-8655&hide_exact_match_fl=true` | **2026-10-25** | Edge CDP 代理（web-access）| `PRLETTERS-D-26-02671`（With Editor）|
| A23（`paper_a2/`）| IEEE Journal of Oceanic Engineering | 0364-9059 / 1558-1691 | IEEE | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0364-9059&hide_exact_match_fl=true` | **2026-10-25** | Edge CDP 代理（web-access）| `26-0663` |
| Commentary（`paper_review_prl/`）| Pattern Recognition Letters | 0167-8655 / 1872-7344 | Elsevier | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0167-8655&hide_exact_match_fl=true` | **2026-10-25** | 与 P3 同一刊、同一 URL；一次核实覆盖两行 | `PRLETTERS-D-26-02402`（在审）|

### 3.1 本次核实的证据摘录（原文关键行 + 选项指标）

| 刊名 | MJL 页面关键原文 | 出版商第二来源 | 指标（**publisher-displayed，第三方 JCR/CiteScore 数据，仅记录，不用于资格判定**）|
|---|---|---|---|
| Neurocomputing | `Exact Match Found`；`Web of Science Core Collection: Science Citation Index Expanded`；`Additional Web of Science Indexes: Current Contents Engineering, Computing & Technology \| Essential Science Indicators` | ScienceDirect 期刊页（**无** Abstracting & Indexing 列表；`/about/abstracting-and-indexing` 重定向回首页）| Impact Factor **6.7**；CiteScore **10.8** |
| Pattern Analysis and Applications | `Exact Match Found`；`Web of Science Core Collection: Science Citation Index Expanded`；同上 Additional Indexes | **Springer 期刊页**：`Abstracted and indexed in … Science Citation Index Expanded (SCIE)` | Journal Impact Factor **2.6 (2025)**；5-year **2.4 (2025)** |
| Pattern Recognition Letters | `Web of Science Core Collection: Science Citation Index Expanded`；`Additional Web of Science Indexes: Current Contents Engineering, Computing & Technology \| Essential Science Indicators`（结果标题为 “Journals Relevant To 0167-8655”，1 条结果，ISSN 与刊名均匹配）| ScienceDirect 期刊页（**无** A&I 列表；journalinsights 已重定向到期刊首页）| Impact Factor **3.5**；CiteScore **7.8** |
| IEEE Journal of Oceanic Engineering | `Web of Science Core Collection: Science Citation Index Expanded`；`Additional Web of Science Indexes: Current Contents Engineering, Computing & Technology \| Essential Science Indicators`（结果标题为 “Journals Relevant To 0364-9059”，1 条结果，ISSN 与刊名均匹配）| IEEE Xplore 期刊页 / `aboutJournal.jsp`（**无** Abstracting & Indexing 列表）| Impact Factor **5.6**；CiteScore **8.6**；Eigenfactor 0.00504；AIS 1.169 |

> **说明 1**：上表五条是**已发生的投稿事实**，本轮（2026-10-25）已按 §2 用 MJL 逐条复核并留痕
> ⇒ 本表现在**构成 §2 要求的留痕**（核实人：agent `p3-stats`，task-26）。
> **下一次**投稿/改投前，仍应重新复核（MJL 收录状态可能变化）。
>
> **说明 2**：**JCR 分区（quartile）未能免费取得**（需 JCR 登录），按规则**不填**；上表 IF/CiteScore
> 只是出版页面公开展示的第三方数据，**不作为资格依据**。
>
> **说明 3**：第二来源（§2 第 3 步）只对 PAA 取得（Springer 页面明确列出 SCIE）；
> Neurocomputing / PRL / IEEE JOE 的出版商 A&I 页**不可达或不存在**（详见
> `docs/venue_sci_reverification_2026-10-25.md` §3），因此这三条的判定**仅由 §2 第 1 步的 MJL 一手来源支撑**，
> 未做第三方"循环印证"。

## 4. 备选/候选目标

### 4.1 合格候选（主流 SCIE，按契合度）

| 刊名 | ISSN | 出版商 | 适合哪篇 | 备注 |
|---|---|---|---|---|
| Pattern Recognition | 0031-3203 | Elsevier | Commentary 升级为系统综述后；P3 改投 / Paper A 转投候选 | SCIE，综述与正刊均可；**2026-10-26 MJL 已复核，见 §4.4** |
| ACM Computing Surveys | 0360-0300 | ACM | Commentary 升级为系统综述 | SCIE；[ACM 索引页](https://acm-stag.literatumonline.com/journal/csur/indexing) |
| International Journal of Computer Vision | 0920-5691 | Springer | 综述/长文 | SCIE |
| IEEE TPAMI | 0162-8828 | IEEE | 长文 | SCIE；无 Commentary 栏目 |
| Nature Machine Intelligence | 2522-5839 | Springer Nature | Commentary/Comment 栏目 | SCIE；门槛高，**待核栏目是否接受投稿型 Comment** |
| Machine Learning | 0885-6125 | Springer | 方法长文 | SCIE |
| Information Fusion | 1566-2535 | Elsevier | 多模态融合方向 / Paper A 转投候选 | SCIE；**2026-10-26 MJL 已复核，见 §4.4** |
| Knowledge-Based Systems | 0950-7051 | Elsevier | 方法/应用 / Paper A 转投候选 | SCIE；**2026-10-26 MJL 已复核，见 §4.4** |
| Neural Networks | 0893-6080 | Elsevier | 方法 | SCIE；**该刊已拒同一稿族（`NEUNET-D-26-09426`），Paper A 不得转投** |
| IEEE Transactions on Multimedia | 1520-9210 | IEEE | 多模态方法 | SCIE |

> 上表刊名与 ISSN 为登记用；**投稿前仍须按 §2 用 MJL 逐条核实**并补 `来源URL/日期`。

### 4.2 待核（未核实前不得作为目标）

| 刊名 | ISSN | 出版商 | 现状 |
|---|---|---|---|
| Patterns | 2666-3899 | Cell Press | `待核`（疑似 ESCI，需 MJL 确认；本条已写入规则文件）|

### 4.3 已剔除（不合格）

| 刊名 | ISSN | 原因 |
|---|---|---|
| Frontiers in Artificial Intelligence | 2624-8212 | ESCI/Scopus，非 SCIE |
| Frontiers in Big Data | 2624-909X | ESCI/Scopus，非 SCIE |

### 4.4 Paper A 转投候选（2026-10-26 按 §2 用 MJL 核实）

> 触发：Neurocomputing 对 Paper A 桌面拒稿（`NEUCOM-D-26-23760`，2026-10-26），Elsevier 提供 article transfer，
> 需在 **2026-11-24 23:59** 前答复；选定目标前必须按 §2 核实。本节 8 刊**全部由 Clarivate Master Journal List
> 一手结果判为 SCIE**（1 条结果、刊名/ISSN 与检索一致、`Web of Science Core Collection: Science Citation Index Expanded`）。
> 逐条证据摘录与访问路由见 `docs/venue_transfer_candidates_2026-10-26.md`。
> **核实人**：agent `p3-stats`；**核实日期**：**2026-10-26**（Asia/Shanghai）。
> **第二来源（出版商 A&I 页）**：Elsevier 的 ScienceDirect `/about/abstracting-and-indexing` 子页**已重定向到期刊首页**，
> 页面无索引数据库清单（`journalinsights.elsevier.com` 亦重定向）⇒ 8 刊均**未取得**第二来源，判定仅由 MJL 一手来源支撑；
> 与 2026-10-25 对 Neurocomputing/PRL 的结论一致（不是本次新出现的阻塞）。

| 刊名 | ISSN / eISSN | 出版商（MJL 登记）| 收录类型 | MJL 来源 URL（本次实际访问）| 核实日期 | 页数/字数限制（guide for authors，实际读到）|
|---|---|---|---|---|---|---|
| **Pattern Recognition** | 0031-3203 / 1873-5142 | Elsevier Sci Ltd | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0031-3203&hide_exact_match_fl=true` | 2026-10-26 | **20–35 页**（单栏双倍行距，含 figures/tables/references/biosketches；附录不计入；survey 可至 40 页）；<20 页建议改投 PRL |
| **Information Fusion** | 1566-2535 / 1872-6305 | Elsevier | **SCIE** | `https://mjl.clarivate.com/search-results?issn=1566-2535&hide_exact_match_fl=true` | 2026-10-26 | 原创研究 **10–35 页**（含全部内容）、**最多 50 条参考文献**；综述可至 50 页/300 refs |
| **Knowledge-Based Systems** | 0950-7051 / 1872-7409 | Elsevier | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0950-7051&hide_exact_match_fl=true` | 2026-10-26 | 原创/综述**最好 ≤20 双倍行距页**（含表图）；short communication ≤10 页 |
| **Engineering Applications of Artificial Intelligence** | 0952-1976 / 1873-6769 | Pergamon-Elsevier Science Ltd | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0952-1976&hide_exact_match_fl=true` | 2026-10-26 | **≤50 页**（硬性；超过即 desk rejection），文件 ≤100 MB |
| **Image and Vision Computing** | 0262-8856 / 1872-8138 | Elsevier | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0262-8856&hide_exact_match_fl=true` | 2026-10-26 | **正文 4500–7500 words**（Word Count 节；opinion paper ≤2 页）|
| **Computer Vision and Image Understanding** | 1077-3142 / 1090-235X | Academic Press Inc Elsevier Science | **SCIE** | `https://mjl.clarivate.com/search-results?issn=1077-3142&hide_exact_match_fl=true` | 2026-10-26 | guide 中**未见页数/字数硬限**（仅有摘要 ≤250 words 等常规项）|
| **Applied Soft Computing** | 1568-4946 / 1872-9681 | Elsevier | **SCIE** | `https://mjl.clarivate.com/search-results?issn=1568-4946&hide_exact_match_fl=true` | 2026-10-26 | technical paper **20–30 页、至多 50 页**；letter ≤3500 words（约 10 页）|
| **Expert Systems with Applications** | 0957-4174 / 1873-6793 | Pergamon-Elsevier Science Ltd | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0957-4174&hide_exact_match_fl=true` | 2026-10-26 | guide 中**未见页数/字数硬限**（仅有摘要 ≤250 words 等常规项）|

**核实途径（8 条相同）**：MJL 是 JS 单页应用，静态 `web_fetch` 只返回页面标题；本轮用 Edge CDP
（浏览器渲染后读取结果卡片：`Journals Relevant To "<ISSN>"` + 1 条结果 + `Web of Science Core Collection:
Science Citation Index Expanded`）完成 8 次检索。**第二来源（Elsevier A&I）未取得**（见上）。
**核实日期均为 2026-10-26（Asia/Shanghai）**。

**Additional Web of Science Indexes（MJL 同页，逐刊）**：8 刊均为
`Current Contents Engineering, Computing & Technology | Essential Science Indicators`；
Pattern Recognition 另含 `Biological Abstracts | BIOSIS Previews`。

**未入表/不合格**：`Neural Networks`（0893-6080）虽为 SCIE，但**同一稿族已被其拒稿**（`NEUNET-D-26-09426`），
Paper A 转投时**排除**。

### 4.5 Paper A 转投候选的资格判定

| 判定 | 刊物 |
|---|---|
| **SCIE，可作候选**（8 刊）| Pattern Recognition、Information Fusion、Knowledge-Based Systems、Engineering Applications of Artificial Intelligence、Image and Vision Computing、Computer Vision and Image Understanding、Applied Soft Computing、Expert Systems with Applications |
| **不合格/排除**（本次 8 刊之外）| Neural Networks（同一稿族已拒，流程上排除）；Frontiers 两刊（ESCI，非 SCIE，见 §4.3）；`Patterns` 仍 `待核`（本轮未核）|

### 4.6 Paper A 第二轮候选（2026-10-26 按 §2 用 MJL 核实；CVIU 因 Vitae 要求弃用后）

> 触发：CVIU 指南要求作者 **Vitae（≤100 词 bio + 护照型照片）**（`docs/cviu_guide_quotes_2026-10-26.txt`），
> 操作者决定换刊；Pattern Recognition 亦因**同稿族 P1 已投递**（`PR-D-26-10149`）而排除。
> **核实人**：agent `p3-downstream`；**核实日期**：**2026-10-26**（Asia/Shanghai）。
> **核实途径**：MJL 为 JS 单页应用，用**可见 Edge + CDP** 渲染后读取 `Exact Match Found` 结果卡片
> （4 次检索均返回 1 条结果，卡片逐字含 `Web of Science Core Collection: Science Citation Index Expanded`）。
> 详细指南摘录与可行性见 `docs/venue_second_candidates_2026-10-26.md`。

| # | 刊名 | ISSN / eISSN | 出版商（MJL 登记）| 收录类型 | MJL 来源 URL（本次实际访问）| 核实日期 | 指南关键约束（实际读到）|
|---|---|---|---|---|---|---|---|
| 1 | **Information Sciences** | 0020-0255 / 1872-6291 | Elsevier Science Inc | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0020-0255&hide_exact_match_fl=true` | 2026-10-26 | 单盲；**要 Vitae（≤100 词）+ 护照型照片**；"experimental … not longer than 40 double-spaced typed pages and 8 figures + tables; theoretical … maximum of 45 pages and 10 figures + tables"；摘要刊内 ≤200 词；关键词 1–7；highlights 鼓励（3–5，≤85 字符）；数据 **Option C** |
| 2 | **International Journal of Computer Vision** | 0920-5691 / 1573-1405 | Springer | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0920-5691&hide_exact_match_fl=true` | 2026-10-26 | 单/双盲**未明示**；无页数限制但 aims 页："Regular articles (**up to 25 journal pages**)"；摘要 150–250 词；关键词 4–6；无 highlights；**无 Vitae**；LaTeX 用 Springer 模板 **`[iicol]`**、源码+PDF、**不可用子目录**；参考文献 **APA v7**；需 Data Availability Statement + Statements and Declarations |
| 3 | **Applied Intelligence** | 0924-669X / 1573-7497 | Springer | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0924-669X&hide_exact_match_fl=true` | 2026-10-26 | 单/双盲**未明示**；**无页数/字数限制**；摘要 150–250 词；关键词 4–6；无 highlights；**无 Vitae**；LaTeX 用 Springer 模板 **`smallcondensed`**、不可用子目录；参考文献 **`sn-basic.bst`（数字式）**；需 DAS + Statements and Declarations |
| 4 | **Cognitive Computation** | 1866-9956 / 1866-9964 | Springer | **SCIE** | `https://mjl.clarivate.com/search-results?issn=1866-9956&hide_exact_match_fl=true` | 2026-10-26 | 单/双盲**未明示**；"Full-length or Regular papers can be up to **10,000 words**"；"**Manuscripts should be typed in Word**"（LaTeX 非目标格式）；**结构化摘要** 150–250（须带小标题）；关键词 3–6；无 highlights；**无 Vitae**；参考文献数字式；需 DAS + Declarations |

**Additional Web of Science Indexes（MJL 同页，逐刊）**：四刊均为
`Current Contents Engineering, Computing & Technology | Essential Science Indicators`。

**资格判定（本轮）**：
- **可作候选**：**Applied Intelligence**（推荐）、**IJCV**（冲刺）。两者均 **无 Vitae 要求**、**无页数限制**（IJCV 为 25 排版页/regular article）。
- **排除**：**Information Sciences**（Vitae + 护照照片，与 CVIU 同因；另有 40/45 页与 8/10 图表指导值需大砍）；
  **Cognitive Computation**（Word-only + ≤10,000 词 + 结构化摘要；scope 为认知/生物启发系统，与本稿不合）。

**第二来源（出版商 A&I 页）**：四刊**均未取得**（Elsevier/Springer 的 A&I 页不列索引数据库），判定仅由 MJL 一手来源支撑；与 2026-10-25/26 既有结论一致。

**未决**：Springer 三刊的**单盲/双盲**在指南中未明示，投稿前需在投稿系统/期刊页确认（若双盲需另做匿名版与独立 title page）。



## 5. 变更记录

| 日期 | 变更 | 触发 |
|---|---|---|
| 2026-10-24 | 建立本表；规则写入 `AGENTS.md`/`CLAUDE.md`；剔除 Frontiers 两刊；`Patterns` 标待核 | 操作者原话"不管投哪，必须是SCI期刊，记录进规则" |
| 2026-10-25 | **五条目标刊物全部按 §2 用 MJL 复核为 SCIE**；填 `来源URL`/`核实日期`/`核实途径`；PAA 另有 Springer 第二来源；出版商 A&I 不可达的三条如实标注；新增 §3.1 证据摘录；IF/CiteScore 标为 publisher-displayed 第三方数据、不用于资格判定 | task-26（独立审计发现 registry 全为 `待核` 后补做）|
| 2026-10-26 | **新增 §4.4/§4.5：Paper A 转投 8 个 Elsevier 候选全部按 §2 用 MJL 核实为 SCIE**（Pattern Recognition / Information Fusion / Knowledge-Based Systems / EAAI / Image and Vision Computing / CVIU / Applied Soft Computing / Expert Systems with Applications），并记录 guide-for-authors 页数/字数限制；第二来源（Elsevier A&I）不可达如实标注；Neural Networks 因同稿族已拒而排除 | Paper A 被 Neurocomputing 桌面拒稿（`NEUCOM-D-26-23760`，2026-10-26），Elsevier 转投需在 2026-11-24 前答复 |
| 2026-10-26 | **新增 §4.6：第二轮 4 个候选（Information Sciences / IJCV / Applied Intelligence / Cognitive Computation）全部按 §2 用 MJL 核实为 SCIE**（可见 Edge 读 `Exact Match Found` 卡片）；记录各项指南约束；判定 **Information Sciences 因 Vitae+照片、Cognitive Computation 因 Word-only+10k 词+结构化摘要而排除**；**推荐 Applied Intelligence**、IJCV 为冲刺。详见 `docs/venue_second_candidates_2026-10-26.md` | CVIU 指南要求作者 Vitae + 护照型照片（`docs/cviu_guide_quotes_2026-10-26.txt`），操作者"换期刊吧"；Pattern Recognition 另因同稿族 P1 已投递（`PR-D-26-10149`）排除 |

## 6. 新增投稿目标（2026-10-27）

| 稿件 | 刊名 | ISSN | 出版商 | 收录 | 核实来源 URL | 核实日期 | 核实人 |
|---|---|---|---|---|---|---|---|
| **New paper B - PENDING, blocked by the A23 overlap** | Journal of Marine Science and Engineering (JMSE) | 2077-1312 | MDPI | **SCIE** | https://www.mdpi.com/journal/jmse (page states "indexed with Scopus, SCIE (Web of Science), Ei Compendex, GeoRef, Inspec, AGRIS") | 2026-10-27 | agent（一手：出版商官网）|
| **RS-VLM survey (new)** | Remote Sensing | 2072-4292 | MDPI | **SCIE** | https://www.mdpi.com/journal/remotesensing (page states "indexed within Scopus, SCIE (Web of Science), Ei Compendex, PubAg, GeoRef, Astrophysics Data System, Inspec, dblp"; stats page: 22 days to first decision, 3 days acceptance to publication) | 2026-10-27 | agent（一手：出版商官网）|

### A3 candidate venues (new paper, 2026-10-28)

Operator constraint: no APC (subscription route only, as with A/A1/A2/P3) and SCIE mandatory.

| candidate | ISSN | publisher | indexing | APC for us | verification |
|---|---|---|---|---|---|
| **ISPRS J. Photogrammetry and Remote Sensing** | 0924-2716 | Elsevier | SCIE (publisher page + third-party corroboration; **MJL row not yet captured**) | none: publisher page states "No publication fee charged to authors" (subscription route) | 2026-10-28: ScienceDirect journal page read live (Impact Factor 12.9, CiteScore 21.0, 5-day first decision, 60-day decision after review); 2026-10-29: x-mol journal page states "SCI收录状况: Science Citation Index Expanded"; **operator approved submission on 2026-10-29 with the MJL capture still pending** (A3 package submitted/being submitted on that instruction), fallback Image and Vision Computing (SCIE verified 2026-10-26) |
| **IEEE JSTARS** | 1939-1404 | IEEE | SCIE, `待核` | none if within page limit; overlength fees to be checked | not yet verified (MJL unreachable this session) |
| **Image and Vision Computing** | 0262-8856 | Elsevier | **SCIE verified 2026-10-26** | none (subscription) | usable today |
| **Pattern Recognition** | 0031-3203 | Elsevier | **SCIE verified 2026-10-26** | none (subscription) | usable today |

Excluded: Remote Sensing (MDPI) - APC; Neurocomputing - desk rejection on Paper A; other MDPI titles.

Note recorded 2026-10-28: the Clarivate Master Journal List did not return results in this session through the
authenticated Edge profile (search page loaded, results did not render), so no new `SCIE` row was written from it.
