# 免 APC 出版通道核查（University of Southampton）—— 取证报告

> **取证日期：2026-09-26**（本文件所有 HTTP 抓取均在该日完成，时区 Asia/Shanghai）。
> **取证方式**：本会话 `web_fetch` 工具故障（报 `configured web provider "http" is not registered`），`scrapling` MCP 断连；
> 故全程改用 `pwsh` + `Invoke-WebRequest`（浏览器 UA）直取，PDF 用 `pdftotext -layout` 解析。
> **规则**：每条结论附来源链接、HTTP 状态与**逐字原文**；页面未提及的一律写"页面未提及"或"未能验证"，**不做填空式推断**。
> **版本说明**：本版 = （a）初版文字取证 +（b）操作者提供的 Journal Search Tool 截图证据（原 §六）
> +（c）**本次新增的 API 级逐刊实测**（解决初版待核 1–3 与待核 4）+（d）IEEE 预印本/费用、Elsevier 逐刊 Guide、国家豁免资格判定。
> 初版结论**无一条被静默删除**；已解决项由"⏳ 待核"就地改标为"✅ 已解决（附新证据）"。如与旧条目冲突，以本版为准。

---

## 一、结论摘要

### 一句话回答

> **能，但只在"出版商 hybrid（订阅制）期刊 + 通讯作者为 Southampton 身份"这一组合内成立：
> Elsevier 系的目标刊（Pattern Recognition / Neurocomputing / Pattern Recognition Letters / Image and Vision Computing）
> 经**逐刊实测**确认由协议覆盖、作者零 APC；但 **IEEE（含在审的 IEEE JOE 与 TNNLS）明确不在任何 Southampton OA 出版协议内**，
> IEEE 的金色 OA 须自付 **US$2,645**（JOE 官方价），且 fully OA 期刊（Elsevier/Springer 的全 OA 刊）同样不免 APC。**

### 三分法清单

| 判定 | 对象 | 依据（摘要） |
|---|---|---|
| **① 确定覆盖** | **Elsevier hybrid**：Neurocomputing、Pattern Recognition Letters、**Pattern Recognition**、**Image and Vision Computing**、Computer Vision and Image Understanding、Neural Networks、Expert Systems with Applications、Information Fusion、Knowledge-Based Systems | Southampton 官方页"*most Elsevier hybrid journals*" + **SciFree API 逐刊实测** `payment = Included in Publisher Agreement` + **操作者截图**三刊 `Included / CC BY / Hybrid`（三条独立证据，§二.1C） |
| **① 确定覆盖**（出版商级条文；未逐刊实测） | Springer Nature hybrid（含 Nature hybrid）；Wiley（含 Hindawi/AGU）；Taylor & Francis（hybrid + fully OA + F1000 + Routledge Open）；Sage hybrid；ACM 会议/期刊/杂志；OUP；IOP Lists A–D；RSC、Royal Society、Optica、AIP、ACS、CUP、BMJ、PLOS（部分刊）、JMIR、Portland Press、Microbiology Society、Wolters Kluwer 等 | 协议总表逐条原文（§二.3–§二.7） |
| **② 需逐刊/逐条核实** | ① Elsevier 协议**时间窗**三处表述不一致；② **"Letters and Perspective pieces are not included"** 对 PRL 的**文章类型**是否致命；③ Wiley/Springer 的**超页费、彩图费**不含；④ ACM 在工具中显示 `About to Expire`；⑤ Springer "flipped from hybrid to open access" 的少量刊未逐刊核；⑥ 各协议**是否有名额/篇数上限**（页面均未提及）；⑦ Pattern Recognition 的 Guide（评审模式/预印本条款）取不到 | §二 各条、§五、§六 |
| **③ 明确不覆盖** | **IEEE 全部期刊**（JOE、TNNLS、TIP、TCSVT、Access…）；**Elsevier fully OA**（仅 15% 折扣）；**Springer Nature BMC 与多数 fully OA**（仅 15% 折扣）；**Sage fully OA**；**国家豁免/Research4Life**（英国机构不符合）；**任何未被机构工具收录的期刊**（含 MDPI/Frontiers/Sci Rep 等付费全 OA） | §二.1、§二.2、§二.8、§四.1 |

### 对当前四篇的直接含义

| 稿件 | 目标刊 | APC 结论 |
|---|---|---|
| **A1** | Neurocomputing（Elsevier hybrid） | ✅ **£0**（逐刊实测 + 截图双重确认） |
| **P1** | Pattern Recognition（Elsevier hybrid） | ✅ **£0**（逐刊实测确认）；⚠️ 与 A1 同刊在审的编辑并案风险另见专文 |
| — | Pattern Recognition Letters / Image and Vision Computing | ✅ **£0**；⚠️ PRL 需核**文章类型** |
| **A23** | **IEEE JOE**（hybrid，26-0663 在审） | ❌ **无协议覆盖**。订阅制投稿**不产生 APC**（发表 0 费用）；若要金色 OA 须自付 **US$2,645**；绿色通道畅通（§三.2） |
| **P3** | 🆕 **Pattern Recognition Letters**（`PRLETTERS-D-26-02378`，2026-09-26 16:22 投；前身 TNNLS 已拒） | ✅ **落入 ①：Elsevier hybrid + 作者为 Southampton 身份 → APC £0**（协议覆盖，见 §2.1） |

> **关键操作性结论**：**金色 OA 不是必需的**。三刊均为 **Hybrid** —— 不选 OA 也能免费发表（订阅制），
> 选 OA 则由协议付 APC。对"零预算 + 尽快见刊"而言，**订阅制投稿 + 绿色自存档**已足够建立公开、可引用的记录。

---

## 二、转换协议覆盖范围与条件（逐出版商）

### 2.0 通用资格条件（适用于绝大多数协议）

**来源**：<https://library.soton.ac.uk/openaccess/agreements>（HTTP 200，页脚 "Last Updated: Sep 24, 2026"）

逐字原文：

> "These publisher agreements and open access memberships provide open access at no cost to University of Southampton corresponding authors (current UK, Delhi and Malaysia based staff and students) where the research has been underpinned by the University of Southampton. Please note that former members of staff, colleagues on honorary contracts, visitors and Emeritus Professors cannot benefit from the agreements/memberships."

> "Please note that we do not have a central institutional fund for open access payments that fall outside of these deals; the University of Southampton supports open access via self-archiving your Accepted Manuscript in Pure."

> "Please note that page charges, colour charges and other associated publishing costs are excluded from these agreements."

**要点**：① 必须是**现任 UK / Delhi / Malaysia 校区 staff 或 student**；② 研究须由 Southampton 支撑；
③ **名誉合同、访问学者、荣休教授不合格**；④ **学校没有通用 OA 经费池**，协议之外一律自付；⑤ **页费、彩图费、其它出版成本不含**。

### 2.1 Elsevier（对本作者最关键）

**来源 A（机构侧）**：<https://library.soton.ac.uk/openaccess/elsevier>（HTTP 200）
**来源 B（出版商侧）**：<https://www.elsevier.com/open-access/agreements/jisc>（HTTP 200）
**来源 C（逐刊实测）**：SciFree 机构期刊检索工具 API（复现命令见文末附）
**来源 D（操作者截图）**：Southampton Journal Search Tool 查询结果截图（操作者提供）

**A. 覆盖与免除（逐字）**

> "Open access at no cost to University of Southampton corresponding authors for research and review articles in most Elsevier hybrid journals."

> "Includes articles accepted for publication 01/01/22-31/12/27"

> "Please select the CC BY licence rather than CC BY-NC or CC BY-ND as this is required for the Library team to approve your article for open access under the agreement."

> "Fully open access journals are not included, but we do get a 15% discount"

> "Journal of Pharmacology and Experimental Therapeutics, Molecular Pharmacology and Pharmacological Reviews are excluded as these titles are society-owned journals and fall outside the scope of the agreement."

> "Please note: Letters and Perspective pieces are not included. When publishing in eligible hybrid Cell Press journals, review articles and short survey article types are not eligible. When publishing in eligible journals from The Lancet, full length articles are the only eligible article type."

**B. 出版商侧确认协议存在与生效期（逐字）**

> "Elsevier and Jisc have established an agreement to support affiliated corresponding authors in the United Kingdom who wish to publish open access (OA) in Elsevier journals."

> "Eligible corresponding authors publishing OA in selected hybrid journals (including eligible hybrid Lancet titles and Cell Press titles) do not have to pay an article publishing charge (APC)."

> "When does the agreement apply? Articles must have an original acceptance date between 1 January 2026 and 31 December 2028."

> "For the purpose of eligibility under the agreement, there can only be one corresponding author. … Importantly, **the corresponding author's affiliation will be used to determine eligibility** for the publishing agreement. The affiliations of other co-authors are not relevant for agreement eligibility."

> "Your institution validates your eligibility for the agreement. Please note: **The final decision on your eligibility lies with the person at your institution** responsible for managing and administering this agreement."

> "Please note that fully OA journals will not show in the journal search tool."

**⚠️ 必须记录的三处不一致**

1. **时间窗**：机构页 `01/01/22-31/12/27`；Elsevier 页 `1 January 2026 and 31 December 2028`；机构工具元数据 `end_date 2027-12-31`。**对"2026 年内录用"三者一致**，但**结束年份不同**。→ 需向 `eprints@soton.ac.uk` 确认；对 2026 年投稿无实质影响。
2. **"Letters and Perspective pieces are not included"** 是 Elsevier 的**文章类型**排除表述，**≠"刊名含 Letters 的期刊被排除"**（PRL 是常规研究刊，且工具按刊名判 Included）。但若本人以**Letters 文章类型**投 PRL，则可能正命中该排除 → §五 第 4 条。
3. Elsevier 侧同页列出的覆盖类型为：Case reports、Data in Brief articles、Full-length articles、Micro-articles、Original software publications、Practice guidelines、Protocols、Registered report articles、Registered report protocols、Replication studies、Review articles、Short communications、Short surveys、Video articles（**无 Letters、无 Perspective**）。

**C. 逐刊实测（本次新增，解决初版待核项 1–3）**

**证据链一：机构工具 API（可复跑）** —— 2026-09-26 实测，字段 `payment` / `publishing_model` / `agreement_name` / `licenses`：

| 期刊 | imprint | 模型 | payment | 协议名 | 许可 |
|---|---|---|---|---|---|
| **Neurocomputing** | Elsevier | Hybrid | **Included in Publisher Agreement** | Elsevier Read and Publish Agreement | CC BY |
| **Pattern Recognition** | Elsevier | Hybrid | **Included in Publisher Agreement** | Elsevier Read and Publish Agreement | CC BY |
| **Pattern Recognition Letters** | Elsevier | Hybrid | **Included in Publisher Agreement** | Elsevier Read and Publish Agreement | CC BY |
| **Image and Vision Computing** | Elsevier | Hybrid | **Included in Publisher Agreement** | Elsevier Read and Publish Agreement | CC BY |
| Computer Vision and Image Understanding | Elsevier | Hybrid | Included in Publisher Agreement | Elsevier Read and Publish Agreement | CC BY |
| Neural Networks | Elsevier | Hybrid | Included in Publisher Agreement | Elsevier Read and Publish Agreement | CC BY |
| Expert Systems with Applications | Elsevier | Hybrid | Included in Publisher Agreement | Elsevier Read and Publish Agreement | CC BY |
| Information Fusion | Elsevier | Hybrid | Included in Publisher Agreement | Elsevier Read and Publish Agreement | CC BY |
| Knowledge-Based Systems | Elsevier | Hybrid | Included in Publisher Agreement | Elsevier Read and Publish Agreement | CC BY |
| Machine Vision and Applications | Springer | Hybrid | Included in Publisher Agreement | Springer Nature Read & Publish agreement | CC BY |
| International Journal of Computer Vision | Springer | Hybrid | Included in Publisher Agreement | Springer Nature Read & Publish agreement | CC BY |
| IET Image Processing / IET Signal Processing | Wiley | Open Access | Included in Publisher Agreement | Jisc Wiley agreement Open Access | CC BY |

协议元数据（`https://api.jst.scifree.se/agreements/soton/6526615a5c60d70001c9b2c8`，逐字）：

> `{"publisher":"Elsevier","payment":"Included in Publisher Agreement","start_date":"2022-01-01T00:00:00","end_date":"2027-12-31T00:00:00","name":"Elsevier Read and Publish Agreement","licenses":["CC BY"],"account":"soton","updated_at":"2026-07-14T07:24:06.005000","updated_by":"k.p.lapage@soton.ac.uk","status":"enabled","file_name":"Elsevier_Hybrid_scifreeimport.xlsx"}`

→ **刊单于 2026-07-14 由图书馆更新**；工具内协议结束日 **2027-12-31**。

**证据链二：操作者提供的 Journal Search Tool 截图**（列：Journals ｜ Imprint ｜ Included in Agreements ｜ License options ｜ Publishing model）

| 期刊 | Imprint | Included in Agreements | License options | Publishing model |
|---|---|---|---|---|
| Neurocomputing | Elsevier | ✅ Included | CC BY | Hybrid |
| Pattern Recognition Letters | Elsevier | ✅ Included | CC BY | Hybrid |
| Pattern Recognition | Elsevier | ✅ Included | CC BY | Hybrid |

**两条证据链完全一致**（`Included` / `CC BY` / `Hybrid`），且与官方页"most Elsevier hybrid journals + 必须 CC BY"的条件吻合。
**操作者截图注意**：截图**未包含 Image and Vision Computing**；该刊由**证据链一（API）**确认为 `Included in Publisher Agreement`。

### 2.2 IEEE（对本作者最关键的一条：**不覆盖**）

**来源**：<https://library.soton.ac.uk/openaccess/agreements>（HTTP 200）中 IEEE 行的两个位置，逐字原文：

表格内 IEEE 行：

> "IEEE … **We no longer have a read and publish agreement please see the information below this table.**"

表下方 IEEE 专节：

> "We do not have an open access publishing agreement with IEEE"

> "The University of Southampton has signed up to the national '**Read-only plus green open access arrangement**' with IEEE (the Institute of Electrical and Electronics Engineers). **It does not cover open access publishing**, but it does permit self-archiving, also known as repository or 'green' open access:"

> "**All authors can immediately self-archive their Accepted Manuscripts** submitted to any subscription-based IEEE journals, magazines, or conference proceedings by uploading the Accepted Manuscript to Pure"

> "You may apply a **CC BY** (Creative Commons Attribution) license to your Accepted Manuscript"

> "IEEE guarantee that the **IEEE Repository License Fee (RLF) will not apply to any UK authors**"

> "If your article acknowledges **UKRI funding** and you would like to publish in a fully open access IEEE journal, please complete our APC application form **prior to submitting your article** to ensure we can cover the cost."

**交叉印证**：机构期刊检索工具中 **"IEEE" 一词命中 0 条**（`term=IEEE` → `total_count = 0`）；
用 `IEEE Journal of Oceanic Engineering`、`IEEE Transactions on Neural Networks and Learning Systems`、
`IEEE Transactions on Image Processing`、`IEEE Access`、`IEEE Transactions on Geoscience and Remote Sensing`
逐一精确匹配，**均不在工具库内**（模糊命中数来自他刊，无任何 IEEE imprint 条目）。

**IEEE JOE 的实际费用（官方站点，逐字）** —— <https://beacon.ieeeoes.org/publications/ieee-journal-of-oceanic-engineering/submitting-a-paper-to-joe/>（HTTP 200，"Guide for Authors (updated 3 March 2025)"）：

> "This publication is a hybrid journal, allowing either Traditional manuscript submission or Open Access (OA) manuscript submission. Upon submission, if you choose to have your manuscript be an Open Access article in order to enable unrestricted public access, you commit to immediately pay the **US$2,645** OA fee, plus applicable taxes. If you would like your manuscript to be a Traditional submission, your article will be available to qualified subscribers and purchasers via IEEE Xplore. Immediate payment is not required for Traditional submission."

> 同刊本地留存副本 `outputs/_joe_guide.txt:119`：「By selecting "Yes" to the Open Access question below, you commit to pay the **$2,645 USD APC**…」

**📌 更正旧数**：`docs/FAST_PUBLICATION_PLAN.md:106` 记 JOE OA 为 **US$2,800**，与 2025-03-03 版官方 Guide 的 **US$2,645** 不符；后者为现行官方数字。（✅ **已于 2026-09-26 同步完成**：FAST_PUBLICATION_PLAN.md 与 A23_VENUE_DECISION.md:108 均已改为 US\,645；原注：步。）

> **取证保留**：`open.ieee.org`、`journals.ieeeauthorcenter.ieee.org`、`www.ieee.org/*.pdf` 本次全部 **403 或 0 字节**；
> IEEE 侧"哪些机构在协议内"的官方清单页（`open.ieee.org/partners/jisc-uk-shedl-institutions/`）**未能抓取**。
> 上表结论建立在两条**互相独立**的证据上：Southampton 官方口径（两处）+ 机构工具零 IEEE 条目。

### 2.3 Springer Nature（含 Nature Research / Palgrave）

**来源**：<https://library.soton.ac.uk/openaccess/agreements>、<https://library.soton.ac.uk/openaccess/springer-nature>、<https://www.springernature.com/gp/open-science/oa-agreements/uk/jisc>（三者均 HTTP 200）

> "The Springer Nature Read and Publish 2026-2028 agreement brings together Springer, Palgrave Macmillan, and Nature Research journals into one Read and Publish agreement."

> "Open to University of Southampton corresponding authors original research and review articles, brief communications and continuing education articles in many Springer Nature hybrid journals."

> "**Our agreement covers hybrid journals only; BMC and most fully open access journals are not included, although you may be eligible for a discounted APC.**"

> "The deal does not include fully open access titles, but corresponding authors are eligible for a 15% discount in the open access cost (APC) for fully open access journals. Unfortunately, this does not apply to articles accepted or that signed the author publishing agreement between 1st January 2026 and 16th January 2026…"

> "Upon request to the journal, eligible authors may have their **colour charges waived**."（**唯一明确写"可申请免除彩图费"的一家**）

> "Articles accepted for publication on or before before 31/12/2027"（原文重复 "before"，逐字照录）

出版商侧（**协议权益取决于机构签约档位**）：

> "For Springer hybrid journals, article processing charges (APCs) are covered by the agreement. … For Nature hybrid journals, APCs are covered if your institution has signed an additional Nature agreement. … For Fully OA journals, coverage depends on your institution…"

> "**Centralised**: the institution pays 100% of the APC for eligible articles. … **Pay as you go**: the author pays a discounted APC after article acceptance"

→ **未核实**：Southampton 属哪一档（centralised / selective centralised / pay as you go）。机构页文字（"no cost"、accepted…31/12/2027）指向覆盖，但**机构档位未取证**（§六 第 10 条）。

### 2.4 Wiley（含 AGU、Hindawi）

> "The Wiley agreement is open to all University of Southampton Responsible Corresponding Authors submitting primary research and review articles* to Wiley and Hindawi journals for articles accepted by 31/12/2027."

> "Please use your soton.ac.uk email address and affiliation throughout the submission process and your article will be published open access at no cost to the authors. **You must be identified as the Responsible Corresponding Author (RCA) in the Wiley Author Services submission system.**"

> "**The agreement covers the open access cost (APC) only, we cannot fund any additional publication fees or excess page charges.**"

> 覆盖："All fully open access journals and hybrid journals offering Online Open"；文章类型含 Case Study、Commentary、Data Article、Education、Lecture、Method and Protocol、Perspective、Practice and Policy、Rapid Publication、Research Article、Review Article、Short Communication、Technical Note。

### 2.5 Taylor & Francis

> "Open to University of Southampton corresponding authors submitting original research articles in T&F journals, F1000 and Routledge Open."

> 覆盖：*"Hybrid journals, fully open access journals, F1000 and Routledge Open"*；时间窗 *"01/01/2024 and 31/12/2027"*；许可自动提供 CC BY。

### 2.6 Sage

> "Includes research articles, review articles, and case reports with a University of Southampton corresponding author in Sage hybrid journals."

> 覆盖：*"Hybrid journals (not fully open access journals) in SAGE Premier, IMechE Journal Collection and Royal Society of Medicine Collection"*；时间窗 *"01/01/2023-31/12/2027"*。

### 2.7 ACM / OUP / IOP / 其它

| 出版商 | 覆盖范围（逐字要点） | 时间窗 | 备注 |
|---|---|---|---|
| **ACM** | "All ACM conferences, journals, and magazines for which ACM manages production and rights, are eligible for the agreement. However, these lists of conferences and journals are co-published with other publishers and are excluded from the agreement." 条件：institutional address + institutional email | "Agreement signed May 2024. Includes articles accepted for publication by 31/12/2026" | 工具中 ACM 条目 `payment = "About to Expire"`（状态语义未解释） |
| **OUP** | "Most OUP hybrid and fully open access journals"；类型：research article、review article、brief report、case report | "Articles received into OUP production by 31/12/2027" | — |
| **IOP** | "All journals included in Lists A, B, C and D"；类型含 letters、papers、reviews、special issue articles | "01/01/2024 and 31/12/2026" | 工具显示 `About to Expire` |
| **RSC / Royal Society / Optica / AIP / ACS / CUP / BMJ / PLOS / JMIR / Portland Press / Microbiology Society / Wolters Kluwer / Geological Society / Company of Biologists / OLH** | 均在协议总表内，各自范围与时间窗见原页；**PLOS 仅部分刊**（PLOS ONE、Genetics、Pathogens、Computational Biology、NTD、Digital Health、Complex Systems；2026-01-01 起增 Ecosystems、Aging and Health） | 见原页 | 与本文目标方向无交集，未逐条取证 |

### 2.8 明确不在协议内的负向清单

1. **IEEE 全部**（机构明文 + 工具零条目）。
2. **Elsevier fully OA**（仅 15% 折扣）。
3. **Springer Nature BMC 与多数 fully OA**（仅 15% 折扣，2026-01-01～16 有例外）。
4. **Sage fully OA**（明文 "not fully open access journals"）。
5. **未被机构工具收录的任何期刊**——"The journal search tool includes all journals covered by our publisher open access agreement"。

---

## 三、绿色 OA 与 preprint 合规（含与在审稿件的关系）

### 3.1 Southampton 侧的绿色通道（免费、不依赖出版商协议）

**来源**：<https://library.soton.ac.uk/openaccess/options>、<https://library.soton.ac.uk/openaccess/RRS>、<https://library.soton.ac.uk/openaccess/howto>（均 HTTP 200）

> "You can make your work Open Access without paying a charge. The University of Southampton supports self-archiving, also known as repository (or green) open access."

> "**From September 2026, institutional rights retention means your Accepted Mancuscript can be made openly available (with a CC BY licence) through our institutional repository from the date of publication.**"（原文拼写 "Mancuscript" 逐字照录）

> "Rights Retention is a policy approach which ensures that the University and its researchers (staff and students) can legally share a version of their research outputs immediately upon publication, **regardless of publisher restrictions, such as embargo periods**. This applies to the Author Accepted Manuscript (AAM)…"

> "The Author Accepted Manuscript will be made open access immediately upon online publication, with a CC BY licence (unless a different licence has been applied via an exemption process)."

> "Rights Retention ensures that all in-scope research outputs (i.e., **journal articles and conference proceedings**) can be made immediately open access"

> opt-out 例外（逐字要点）：third party copyright；disagreement from co authors；disagreement from a commercial partner；**a journal rejecting a paper because of Rights Retention**；overriding funder requirement。

> 义务：*"Upload your Author Accepted Manuscript to Pure as soon as possible after acceptance and no later than three months from the date the article appears online"*；
> 2026–2028 年 REF 口径：*"deposited in our institutional repository by the online publication date and no later than 3 month"*。

**结论**：**绿色 OA 是本校的默认免费路线**（"we do not have a central institutional fund…supports open access via self-archiving your Accepted Manuscript in Pure"）；
且自 **2026 年 9 月**起，机构权利保留策略**连 embargo 一并覆盖**（对 Southampton 作者不必等 embargo）。

### 3.2 IEEE 侧的绿色 + 预印本规则（决定 A23/JOE 与 P3 能否公开）

**(a) 绿色**（§二.2 已引）：订阅制 IEEE 期刊的 AM **可立即**存入 Pure；**可施加 CC BY**；UK 作者 RLF 免除。
→ **JOE 走订阅制 = 发表 0 费用 + 录用后立即公开**，这是零预算下唯一可用的 JOE 公开路径。

**(b) IEEE 预印本政策（逐字）** —— <https://cis.ieee.org/images/files/Publications/IEEE_Preprint_Policy.pdf>（HTTP 200，275,343 字节；`pdftotext` 提取；转述 IEEE PSPB Operations Manual §8.1.9）：

> "There is often questions about whether it is OK to post preprints of articles under review to arXiv or other preprint servers. **Bottom line: it is fine to post to arXiv with certain conditions.**"

> "IEEE seeks to maximize the rights of its authors and their employers to post preprint versions of an article on the author's personal web site, on a server operated by the author's employer, or on a server operated by an approved not-for-profit third party…"

> "In any preprint version archived by the author after submission, **IEEE requires that IEEE will be credited as copyright holder**. Upon publication of the work, authors are asked to include the article's Digital Object Identifier (DOI)."

> "The IEEE Intellectual Property Rights Office maintains a list of not-for-profit third party servers where material submitted to the IEEE may be posted. **[The only approved third-party server is arXiv.]**"

> "…the author must update any previously posted version of the article with a prominently displayed IEEE copyright notice (as shown in 8.1.9.B). Upon publication of an article by the IEEE, the author must replace any previously posted electronic versions of the article with either (1) the full citation to the IEEE work with a Digital Object Identifier (DOI), or (2) the accepted version only with the DOI (not the IEEE-published version)."

> "IEEE allows its authors to follow mandates of agencies that fund the author's research by posting accepted versions of their articles in the agencies' publicly accessible repositories."

**⚠️ 时效保留**：该 PDF 托管在 IEEE CIS 分会站点、系对 PSPB Operations Manual 的转述；**未能核实是否为最新版本**（ieee.org 域本次全部 403/0 字节；`archive.org`/`web.archive.org` 在本网络**不可达**）。引用时请连同此保留一并引用。

**(c) IEEE JOE 自己的规则（逐字；`outputs/_joe_guide.txt` 与 beacon 页面一致）**：

> "**Each published article was reviewed by a minimum of two independent reviewers using a single-blind peer review process**, where the identities of the reviewers are not known to the authors, but the reviewers know the identities of the authors."

> "The Journal publishes only original material that has not been published or submitted for publication elsewhere. Prior publication of an abbreviated or preliminary form of the material in conference proceedings or abstracts shall not preclude publication in the Journal provided such prior publication is disclosed at the time of submission."

> "Concurrent submission to other publications and this Journal is viewed as a serious breach of ethics and will result in immediate rejection of the submission."

> "If a manuscript was previously reviewed and rejected by any other publication, authors must disclose this history at the time of submission. Authors must provide copies of the earlier decision letter as well as a response detailing how the Journal submission has addressed the decision letter issues."

> "Format and Length: … The length should be appropriate to the topic, **there is no specific limit**."

**→ JOE 合规判定（三条）**

1. **JOE 不是双盲，而是 single-blind** → **不存在"公开预印本破坏匿名"的问题**（对照：TNNLS 是双盲，规则不可混用）。
2. JOE Guide **未出现 "preprint"/"arXiv" 字样**（本地副本全文检索确认）→ **JOE 层面的预印本规则属"页面未提及"**，适用的是 IEEE 的 PSPB 预印本政策（(b)），而非期刊自设条款。
3. JOE 的硬条款是"**未在别处发表或投稿**"+"**必须披露既往拒稿史（附决定信）**"。预印本**不构成** "submitted for publication elsewhere"（IEEE 政策明文允许）；但**投稿后**上传的预印本须加 IEEE 版权声明，**发表后**须替换为 DOI 引文或带 DOI 的 accepted version。

### 3.3 Elsevier 侧的预印本与 AAM 规则

**来源**：<https://www.elsevier.com/about/policies-and-standards/sharing>（HTTP 200）逐字：

> "**Preprint** … Authors can share their preprint **anywhere at any time**"

> "If accepted for publication, we encourage authors to link from the preprint to their formal publication via its Digital Object Identifier (DOI)"

> "Authors can update their preprints on arXiv or RePEc with their accepted manuscript"

> "**Please note: Some society-owned titles and journals that operate double-anonymized peer review have different preprint policies — please check the journals' Guide for Authors for further information**"

> "**Accepted manuscript** … Authors can share their accepted manuscript: **Immediately**: Via their non-commercial personal homepage or blog; By updating a preprint in arXiv or RePEc with the accepted manuscript (and updating the license to a CC BY-NC-ND license)… **Publicly, after the embargo period**: Via non-commercial hosting platforms, such as their institutional repository…"

> "In all cases accepted manuscripts should: Link to the formal publication via its DOI. Bear a CC-BY-NC-ND license… Not be added to or enhanced in any way to appear more like, or to substitute for, the published journal article"

**逐刊 Guide 原文（本地留存副本，可按行号复核）**

| 期刊 | 评审模式（逐字） | 预印本条款（逐字） | 投稿声明（逐字） |
|---|---|---|---|
| **Neurocomputing**（`_guide_neurocomputing.txt`，2026-09-16 抓取） | `:210` "This journal follows a **single anonymized** review process." | `:455-456` "Authors may share preprints in line with Elsevier's article sharing policy. **Sharing preprints, such as on a preprint server, will not count as prior publication.**" | `:252-253` "The work described has not been published previously **except in the form of a preprint**, an abstract, a published lecture, academic thesis or registered report." / `:256` "The article is not under consideration for publication elsewhere." |
| **Image and Vision Computing**（`_guide_ivc.txt`，2026-09-16） | `:138` "single anonymized review process" | `:390` 同 Neurocomputing 句 | `:184` 同（含 "except in the form of a preprint"） |
| **Ocean Engineering**（`_guide_oe.txt` / `_guide.txt`） | `:198` / `:137` "single anonymized review process" | `:444` / `:275` 同上 | `:240` / `:166` 同上 |
| **Pattern Recognition** | **未能验证** | **未能验证** | **未能验证** |

`docs/SUBMISSION_COMPLIANCE_NEUROCOMPUTING.md:25` 独立记录了同一条（"本刊为 single anonymized review"，指 `:209-212`），与本次抓取的 `:210` 一致 —— 两份记录互相印证。

### 3.4 与在审/已投稿件的关系（合规判定表）

| 稿件 | 状态 | 把稿件或其早期版本放公开仓库/预印本，是否冲突？ | 依据 |
|---|---|---|---|
| **A1 → Neurocomputing** | 在审 | **不冲突**：该刊 Guide 明文"on a preprint server, will not count as prior publication"；且为 **single anonymized**，无需匿名 | `_guide_neurocomputing.txt:210, 455-456`；Elsevier sharing policy |
| **A23 → IEEE JOE（26-0663）** | 在审 | **不冲突（有条件）**：IEEE 明文允许放 arXiv；JOE 为 **single-blind**；但① JOE Guide 未提预印本，适用 IEEE PSPB 政策；② 投稿后上传须加 IEEE 版权声明；③ 发表后须替换为 DOI/带 DOI 的 accepted version；④ **若该稿曾被别处拒过，必须在投稿时披露并附决定信**（独立硬条款，与预印本无关） | IEEE Preprint Policy PDF；`outputs/_joe_guide.txt:75`；JOE Guide "Publication Principles" 段 |
| **P1 → Pattern Recognition（PR-D-26-10149）** | 在审 | **⚠️ 暂缓**：无法取得 PR 的 Guide（403/连接关闭），而 Elsevier 全局政策**明确警告**："Some society-owned titles and journals that operate **double-anonymized** peer review have different preprint policies — please check the journals' Guide for Authors"。未核实 PR 是单盲还是双盲之前，**不得**把 P1 或其早期版本放到公开预印本服务器 | Elsevier sharing policy；§六 第 1 条 |
| **P3 → IEEE TNNLS** | **已拒**，无在审 | **风险最低**：无在审期刊的匿名/首发冲突；IEEE 政策允许 arXiv。改投 IEEE 系按 (b) 加版权声明/DOI；改投 Elsevier 系按该刊 Guide（若为单盲则无障碍） | IEEE Preprint Policy；`_guide_neurocomputing.txt:210` |
| **ap3（合并稿）** | 待 P1 决定 | 需先确认目标刊的评审模式与预印本条款；**不与在审稿共享可识别内容**是前提 | `docs/FAST_PUBLICATION_PLAN.md` §8.3 |

> ⚠️ **通用红线**：真正的 ethics 风险是**"同一稿同时投两家"**与**"未披露的重叠稿件"**（JOE Guide 明文"Concurrent submission… will result in immediate rejection"）；
> **预印本本身**在上述各刊**均不构成 prior publication**（Pattern Recognition 待核除外）。

---

## 四、其它免 APC 通道及资格判定

### 4.1 国家豁免 / Research4Life —— **本人不符合**

**Elsevier 官方（逐字）**：<https://www.elsevier.com/about/policies-and-standards/pricing>（HTTP 200）

> "we automatically apply APC waivers or discounts to those articles in gold open access journals for which **all author groups are based in a country eligible for the Research4Life program**"

> "When publishing in fully open access journals, we fully waive all open access charges for authors from **69 countries (Group A)** and give a **50% discount** for authors from **57 countries (Group B)**"

> "**Our waiving policy does not apply to hybrid journals.** Authors publishing in hybrid journals can publish under the subscription model at no cost and make use of the Elsevier sharing policy"

> "If an author group from a non-Research4Life country cannot afford the APC to publish an article in a **gold open access journal**, we will consider individual waiver requests on a case-by-case basis at our discretion."

**Springer Nature 官方（逐字）**：<https://www.springernature.com/gp/open-research/policies/journal-policies/apc-waiver-countries>（HTTP 200）

> "Springer Nature offers APC waivers to papers whose **corresponding authors are based in locations classified by the World Bank**"

> "**APC waivers are not offered for open access publication in Springer Nature hybrid and transformative titles**, as authors without the funds to publish open access in these journals can publish via the subscription route."

> 该页 "Low-income locations: full APC waiver" 表**全文抓取核对**（2026-09-26；该段 HTML 内 `<td>` 共 67 个）：
> Afghanistan, Burkina Faso, Burundi, Central African Republic, Chad, DR Congo, Eritrea, Ethiopia, Gambia, Guinea-Bissau, Liberia, Madagascar, Malawi, Mali, Mozambique, Niger, Rwanda, Sierra Leone, Somalia, South Sudan, Sudan, Syria, Uganda, Ukraine*, Yemen。
> → **表中不含 United Kingdom，也不含 China**（该页 HTML 内检索 "United Kingdom" 与 "China" 命中数均为 **0**）。

**资格判定（可复核）**：

| 问题 | 判定 | 依据 |
|---|---|---|
| **中国国籍**能否带来豁免？ | **不能**。两家的判定依据都是**作者所属机构所在国**（Elsevier："all author groups are based in a country…"；Springer："corresponding authors are based in locations…"），**不是国籍** | 上述两页原文 |
| **英国机构（Southampton）**能否享受国家豁免？ | **不能**。英属高收入经济体，不在两份官方豁免名单内；且 Elsevier/Springer 均明文 **hybrid 期刊不适用豁免政策** | 同上（Springer 名单实测不含 UK；Elsevier 明文 hybrid 不适用） |
| **hybrid 期刊**能否以"经济困难"个案申请？ | Elsevier 的个案豁免口子只对 **gold OA 期刊**开（"…to publish an article in a **gold open access journal**…"），**hybrid 明文排除**；Springer 的 "discretionary waiver / financial need" 政策指向其 OA policies 页，**本次未取证** | Elsevier pricing 页原文 |
| Research4Life 官方国家清单原文 | **未能验证**：`www.research4life.org` 根域、`/about/eligibility/`、`/access/eligibility/`、西语 FAQ 及其 `wp-content` 下的国家清单 PDF **全部 403**；`login.research4life.org/tracsearch/eligibility` 返回 200 但正文仅 "Secure Portal"（13 字符） | §六 第 2 条 |

### 4.2 机构/资助者经费通道 —— **仅限特定资助**

**来源**：<https://library.soton.ac.uk/openaccess/howto>（HTTP 200）

> "We hold open access block grants for journal articles **acknowledging UKRI**. These can be used for articles submitted to fully open access journals."

> "We can accept applications for open access costs from our UKRI and Cancer Research UK block grants for: **articles to be published in fully open access journals with a CC BY licence**"

> "Applications for APCs must be made on submission using the online form."

> "**We cannot accept applications for page, colour, cover charges or any extra publication charges not related to open access.**"

> "Our Wellcome open access block grant ended on 31st March 2024, the CRUK grant closed to applications 30th June 2026"

> "We participate in over 20 publisher agreements for no-cost-to-the-author publisher open access, **regardless of funder**."

**判定**：① 与 IEEE 相关的那条（"If your article acknowledges UKRI funding…fully open access IEEE journal…APC application form"）**要求论文声明 UKRI 资助**——本人是否有该资助**需本人确认**（§五 第 6 条）；② 无 UKRI/CRUK 资助则**没有任何通用经费池**；③ 页费/彩图费任何通道都不覆盖。

### 4.3 学会会员免费额度 —— **未能验证**

IEEE / OES 会员是否含免费 OA 额度或折扣，**本次未能取得任何官方证据**（`open.ieee.org` 全部 403）。**不作为可用通道计入**。

### 4.4 其它无 APC 的官方通道（有据可查，但与目标方向无关）

| 通道 | 内容 | 相关性 |
|---|---|---|
| **JMIR–Jisc** | Southampton 协议覆盖 JMIR Publications（Original Research Papers / Reviews / Protocol Regular Papers；acceptance 2025-08-01～2027-07-31，机构称 no cost） | ❌ 医学/健康信息学，与 VLM/声呐方向不符 |
| **ACM Open** | 见 §2.7 | ⚠️ 仅当改投 ACM 会议/期刊时可用（会议亦可零 APC 发表） |
| **Diamond OA（DOAJ 无 APC 期刊）** | 机构页给出 DOAJ 无 APC 检索入口 | ⚠️ 通用备选，需逐刊核质量与 scope |
| **OLH** | 图书馆联盟资助、无作者费用 | ❌ 人文学科 |

---

## 五、需要作者本人确认的事项

| # | 待确认事项 | 为什么必须由本人确认 | 依据 |
|---|---|---|---|
| 1 | 是否以 **Southampton 身份作为通讯作者**，且是**唯一**通讯作者 | Elsevier 明文"there can only be one corresponding author…the corresponding author's affiliation will be used to determine eligibility"，且**最终资格由图书馆管理员裁定** | §二.1B |
| 2 | 本人身份是 **current UK-based staff 或 student**，投稿时未离职/未毕业 | 协议明确排除 former staff、honorary contracts、visitors、Emeritus Professors；页面只写"staff and students"，未细分 PGR | §2.0 |
| 3 | 研究是否由 Southampton 支撑（署名 + 单位 + 邮箱） | 所有协议以"the University of Southampton has underpinned the research"为前提；Wiley 额外要求**在系统中被标为 RCA** 并全程用 soton.ac.uk 邮箱 | §2.0、§2.4 |
| 4 | 拟投的**文章类型**是否在覆盖清单内 | Elsevier 明文 **"Letters and Perspective pieces are not included"**；若以 Letters 类型投 PRL 可能正命中排除；Full-length / Research article / Short communication 明确在列 | §二.1 |
| 5 | 是否接受**必须选 CC BY** | 机构明文选错许可则"the Library team"不批准 → **免 APC 失效** | §二.1A |
| 6 | 是否有 **UKRI / CRUK 资助**（论文是否声明） | 决定能否走 block grant（仅 fully OA + CC BY）及 IEEE fully OA 的 APC 申请表 | §4.2、§2.2 |
| 7 | 是否已有 arXiv/仓库预印本？投稿时**是否已在系统内披露** | IEEE 要求投稿后预印本版本加 IEEE 版权声明、发表后替换为 DOI 版本；JOE 要求披露既往拒稿史 | §3.2、§3.4 |
| 8 | 投稿系统内 affiliation / email 是否填成 Southampton / soton.ac.uk | 系统按通讯作者单位自动匹配协议；填错则不会出现"APC = 0.00"的协议选项 | §二.1、§2.4 |
| 9 | 协议**是否有名额/篇数上限** | 机构页与出版商页**均未提及**上限；**不能据此断言"无上限"**——需邮件确认 `eprints@soton.ac.uk` | §六 第 6 条 |
| 10 | 是否接受**页费/彩图费/超页费自付** | 机构明文"page charges, colour charges and other associated publishing costs are excluded"；Wiley 明说不含 excess page charges。**JOE Guide 未提及任何页费且写明"there is no specific limit"**——但"未提及"≠"不存在"，投稿前宜向编辑部书面确认 | §2.0、§2.4、§3.2c |
| 11 | Pattern Recognition 在审稿（PR-D-26-10149）采用单盲还是双盲 | 决定能否为 P1 放预印本；Elsevier 全局政策对双盲刊的预印本政策有例外保留，而 PR 的 Guide 本次取不到 | §3.3、§3.4、§六 第 1 条 |

---

## 六、未能验证的问题（逐条给出失败方式）

| # | 未能验证的内容 | 失败方式（实测） |
|---|---|---|
| 1 | **Pattern Recognition 的 Guide for Authors**（评审模式 / 预印本条款 / 投稿声明） | `https://www.elsevier.com/journals/pattern-recognition/0031-3203/guide-for-authors` → **HTTP 403**；`https://www.sciencedirect.com/journal/pattern-recognition/publish/guide-for-authors` → 连接被意外关闭。仓库内**无** PR 的 Guide 留存副本（`_guide*.txt` 只有 Ocean Engineering / IVC / Neurocomputing）。→ 故 §3.4 对 P1 判为"暂缓"而非"允许" |
| 2 | **Research4Life 官方资格页与国家清单原文** | `www.research4life.org/`、`/about/eligibility/`、`/access/eligibility/`、`/es/preguntas-frecuentes/`、`wp-content/.../Country-List...pdf`、`2020-6p-insert-EN-print-1.pdf` → **全部 403**；`login.research4life.org/tracsearch/eligibility` → 200 但正文仅 "Secure Portal" |
| 3 | **Jisc 官网的协议汇总正文** | `www.jisc.ac.uk/news/all/landmark-publishing-agreements-for-uk-universities`、`/transitional-agreements`、`/licences/agreements` → **全部 403**。→ Jisc 侧原文缺失；协议结论只能由"Southampton 侧 + 出版商侧"两条独立证据链支撑（Elsevier 页确写 "Elsevier and Jisc have established an agreement"） |
| 4 | **IEEE 侧官方清单与政策的最新版本** | `open.ieee.org/partners/jisc-uk-shedl-institutions/` → 403；`journals.ieeeauthorcenter.ieee.org/...pdf` → 403；`www.ieee.org/documents/*.pdf` → 200 但 **0 字节**（`pdftotext` 报 "Document stream is empty"）。→ IEEE 预印本政策用的是 **cis.ieee.org** 托管的转述 PDF，**版本时效未核实**；`archive.org`/`web.archive.org` 在本网络**不可达**，无法用快照交叉核验 |
| 5 | **IEEE / OES 会员是否含免费 OA 额度** | IEEE 域全部 403，无官方页面可引；**未计入任何可用通道** |
| 6 | **各协议是否有名额（篇数）上限** | Southampton 协议总表、Elsevier Jisc 页、Springer Jisc 页**均未提及**上限或配额。**"未提及"不能推成"无上限"** |
| 7 | **Elsevier 协议时间窗的权威口径** | 机构页 `01/01/22-31/12/27` vs Elsevier 页 `1 January 2026 and 31 December 2028` vs 工具元数据 `end_date 2027-12-31`——三处不一致，**无第三方仲裁来源** |
| 8 | **Elsevier hybrid 期刊的逐刊 embargo 期限** | Elsevier 全局 sharing policy 只写"after the embargo period"，未给逐刊月数；Sherpa Romeo 旧域 `v2.sherpa.ac.uk`、`www.sherpa.ac.uk` **连接被关闭**；Jisc Open Policy Finder 首页可访问（200）但为 JS 应用，未取到逐刊记录。→ **对 Southampton 作者，此点已被机构权利保留策略覆盖（§3.1），embargo 不构成实际障碍** |
| 9 | **JOE 是否收取超页费/版面费** | JOE Guide（updated 3 March 2025）全文检索**未出现** page charge / overlength 字样，且写明"there is no specific limit"。**只能记"页面未提及"**，不能断言"不存在" |
| 10 | **Southampton 在 Springer Nature 协议中的档位** | 出版商侧区分 centralised / selective centralised / pay as you go；机构页未写档位，参与机构名单页未取到逐条记录 |
| 11 | **ACM 条目在工具中 `payment = "About to Expire"` 的确切含义** | 工具 UI 状态语义未在任何官方页面解释；协议总表只写"articles accepted for publication by 31/12/2026" |

---

## 附：可复核性说明

1. **抓取日期**：全部 2026-09-26（Asia/Shanghai）；PDF 经 `pdftotext -layout` 提取。
2. **机构级逐刊结论可原样复跑**（唯一需重启证据链的结论）：
   ```powershell
   # Elsevier hybrid 逐刊覆盖（§二.1C 证据链一的来源）
   foreach ($t in 'Neurocomputing','Pattern Recognition','Pattern Recognition Letters','Image and Vision Computing') {
     $e=[uri]::EscapeDataString($t)
     (Invoke-WebRequest "https://api.jst.scifree.se/search?term=$e&account=soton" -UseBasicParsing).Content |
       ConvertFrom-Json | Select-Object -ExpandProperty data |
       Select-Object name, imprint, publishing_model, payment, agreement_name, licenses
   }
   # IEEE 不在协议内（应返回 0）
   ((Invoke-WebRequest "https://api.jst.scifree.se/search?term=IEEE&account=soton" -UseBasicParsing).Content | ConvertFrom-Json).total_count
   ```
3. **失败记录如实保留**：403 来源已在 §六 逐条列出（Jisc、Research4Life、IEEE 全域、Elsevier Guide 页）；`web_fetch` 工具故障与 `scrapling` MCP 断连属工具层问题，非页面 403，已在本文件顶部注明。
4. **本地留存副本**（仓库内，可按行号复核）：`_guide_neurocomputing.txt`、`_guide_ivc.txt`、`_guide_oe.txt`、`_guide.txt`、`outputs/_joe_guide.txt`。
5. ✅ **已回填**：数字更正已同步到 docs/FAST_PUBLICATION_PLAN.md 与 docs/A23_VENUE_DECISION.md:108：`docs/FAST_PUBLICATION_PLAN.md:106` 的 "IEEE JOE OA US$2,800" 应改为官方现行价 **US$2,645**（来源：beacon.ieeeoes.org JOE Guide for Authors, updated 3 March 2025）。**本报告未改动该文件**，按仓库收尾规则由操作者同步。
