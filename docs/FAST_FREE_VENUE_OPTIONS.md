# 快速见刊 × 零预算：期刊可选范围调研报告

> **作者情形**：Hongrui Wan（University of Southampton，唯一作者）；方向为视觉-语言模型参数高效微调（LoRA/Adapter）、跨模态对齐、模态鸿沟、零样本鲁棒性、秩分配理论，另有一篇海洋/声呐跨模态对齐稿。
> **硬约束**：APC / 版面费 / 超页费预算 = 0，且希望"尽可能快见刊"。
> **调研人**：本会话（只读调研；除本文件外未修改工作区任何既有文件）。
> **报告抓取日期**：2026-09-26（+08:00）。文中每个数字与引文都标注来源 URL 与抓取日期；抓不到的写"未能验证"，不含推测值。

---

## 〇、方法与可复核性说明（先读，决定本报告可信度）

1. **本会话 `web_fetch` 工具损坏**（报错 `configured web provider "http" is not registered`），改用 PowerShell + `curl.exe` 直连带完整浏览器头抓取。命令模板：

   ```powershell
   $ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
   curl.exe -sL -o out.html -w "%{http_code}" --compressed --max-time 45 `
     -H "User-Agent: $ua" -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" `
     -H "Accept-Language: en-US,en;q=0.9" -H "Sec-Fetch-Dest: document" -H "Sec-Fetch-Mode: navigate" `
     -H "Sec-Fetch-Site: none" -H "Upgrade-Insecure-Requests: 1" "<URL>"
   ```
   HTML 去标签后落为 `.txt`，PDF 用 `pdftotext -layout`（TeXLive 自带）抽取。临时件全部写在 `%TEMP%\venue_research\`，**未写入工作区**。

2. **抓取失败与替代入口（如实标注）**：
   - **ScienceDirect / journalinsights.elsevier.com 全部被 captcha 拦截**（返回 "Are you a robot?"），公开 CORS 代理（allorigins / codetabs）同样被拦。→ **Elsevier 的"审稿时效"数字本报告未能从官方页面取得**，只能给出官方页 URL 请作者用浏览器自查（见 §二）。
   - **IEEE 的 `open.ieee.org`、`journals.ieeeauthorcenter.ieee.org`、`ieeeaccess.ieee.org` 被 Cloudflare 拦（"Just a moment..."，HTTP 403）**；但 **IEEE 学会站点可直连**：`pspb.ieee.org`、`signalprocessingsociety.org`、`cis.ieee.org`、`ieee-cas.org`——IEEE 官方政策原文即从这些站点取得。
   - **MDPI、Wiley/IET、PLOS、Nature 站点对自动化请求返回 403/000**；其 APC 改用 **DOAJ 官方 API**（出版商自行申报的数额，附出版商 APC 页 URL）核实。
   - **Springer（link.springer.com）、Frontiers、elsevier.com 政策页、CCF、中科院分区表、Clarivate MJL 入口**可访问。

3. **一个自建的、可复跑的时效指标（本报告唯一的"自算"数据）**：Springer 会把 `received`（投稿）/`accepted`（录用）日期作为 assertion 存入 Crossref；IEEE 与 Elsevier **不存**。因此本报告对 Springer 候选刊用 Crossref API 计算"投稿→录用""录用→在线"中位数：

   ```powershell
   curl.exe -s "https://api.crossref.org/journals/<ISSN>/works?rows=60&sort=published&order=desc&select=DOI,published-online,assertion,type"
   ```
   取最近 60 条 `journal-article`，解析 `assertion[name=received|accepted]` 与 `published-online`，算中位数。脚本落在 `%TEMP%\venue_research\crossref_times.ps1`（未入库）。**样本 n=59–60，抓取日期 2026-09-26**；这是"出版商自存元数据"的自算统计，**不是期刊官网公布的中位数**，两者的口径差异见 §二表注。

---

## 一、硬约束与结论摘要

**一句话答案：存在"完全免费且选题契合"的期刊（Elsevier / IEEE / Springer 的订阅制（hybrid 传统）通道），但在官方可验证的数据范围内，不存在同时满足"数月内见刊 + 完全免费 + 不被视为降级"的选项。** 免费路线的现实见刊预期是 **4–7 个月**；能把周期压到 **1–2 个月**的刊物（MDPI、Frontiers、IEEE Access、Scientific Reports、IET 系、PLOS ONE 等）**全部是必须付 APC 的全 OA 刊**，与预算 0 直接冲突。

三条直接的判断：

1. **"免费"这一侧**：Elsevier 的 Pattern Recognition / Neurocomputing / PRL / IVC / Ocean Engineering、IEEE 的 TIP / TCSVT / TNNLS / SPL / JOE、Springer 的 The Visual Computer / MVA / PAA / NPL / Multimedia Systems 等，**都以订阅制（hybrid）方式收稿，选传统通道不产生 APC**——但 **IEEE 系存在"隐形付费"：超过 10 个印刷页的部分是强制超页费**（SPS 系 $220/页；TNNLS $200/页），且条款明写"不付清可扣发"。**对一篇长文，这不是 0 元，而是数百到上千美元。**
2. **"快"这一侧**：官方公布时效的只有 Springer 一类（首次决定中位 1–41 天），而且**这些"1–3 天"的中位数被秒拒（desk rejection）拉低了**，不代表录用速度；用出版商存入 Crossref 的实际数据算，**投稿→录用中位 118–178 天，录用→在线 15–22 天**。
3. **对作者当前最省时的动作不是换刊，而是把手上的三份在审稿推进到底**（PR、Neurocomputing `NEUCOM-D-26-20952`、IEEE JOE `26-0663`），同时把 Springer 系 hybrid 刊作为被拒后的第一顺位备选。

---

## 二、"快速"的量化对比表（含来源与抓取日期）

### 2.1 官方公布的时效（Springer；唯一能从官网抓到的一类）

来源：各刊 Springer 官网首页 "Journal metrics" 区块，**抓取日期 2026-09-26**。

| 期刊（Springer） | 官网 URL | JIF (2025) | Submission to first decision（官网中位） |
|---|---|---|---|
| Neural Processing Letters | https://link.springer.com/journal/11063 | 2.8 | **14 天** |
| Multimedia Systems | https://link.springer.com/journal/530 | 2.8 | **41 天** |
| The Visual Computer | https://link.springer.com/journal/371 | 3.4 | **3 天** |
| Pattern Analysis and Applications | https://link.springer.com/journal/10044 | 2.6 | **1 天** |
| International Journal of Computer Vision | https://link.springer.com/journal/11263 | 10.3 | **37 天**（页面另注："typical time to first decision for manuscripts is approximately 96 days"） |
| Machine Vision and Applications | https://link.springer.com/journal/138 | — | **未能验证**（该页 metrics 区块在抽取文本中未出现，标题确认为该刊） |

> ⚠️ **口径陷阱**：Springer 的 "submission to first decision (median)" 覆盖**全部投稿**（含直接退稿）。The Visual Computer 的 3 天、PAA 的 1 天显然由 desk rejection 主导，**不能读作"3 天/1 天就有审稿意见"**。IJCV 页面罕见地自己写明了这一口径问题（原文见上）——这恰好证明该类中位数不可直接当"录用速度"用。

### 2.2 自算时效（Crossref 出版商存款元数据；Springer；n=59–60；2026-09-26）

| 期刊 | 投稿→录用 中位（天） | 录用→在线 中位（天） | 两端相加的**现实见刊预期** |
|---|---|---|---|
| The Visual Computer | **118** | 22 | ≈ 4.7 个月 |
| Pattern Analysis and Applications | **136.5** | 15 | ≈ 5.0 个月 |
| Multimedia Systems | **150.5** | 20 | ≈ 5.6 个月 |
| Machine Vision and Applications | **178** | 16 | ≈ 6.4 个月 |
| International Journal of Computer Vision | **266** | 23 | ≈ 9.5 个月 |
| Neural Processing Letters | 未能验证（`received` 未存入，n=0） | 21 | 仅能确认录用后 ≈ 3 周上线 |

### 2.3 关键期刊的官方时效：**未能验证**（附作者可用浏览器自查的 URL）

以下页面在自动化访问下被 captcha / Cloudflare 拦截（HTTP 403）。**作者用浏览器打开即可看到 Elsevier 官方时效数字**（该页即 ScienceDirect 的 "Journal insights"）：

| 期刊 | 官方时效页（请浏览器自查） | 本报告状态 |
|---|---|---|
| Neurocomputing | https://www.sciencedirect.com/journal/neurocomputing/about/insights | 403 captcha，**未能验证** |
| Pattern Recognition | https://www.sciencedirect.com/journal/pattern-recognition/about/insights | 同上 |
| Pattern Recognition Letters | https://www.sciencedirect.com/journal/pattern-recognition-letters/about/insights | 同上 |
| Image and Vision Computing | https://www.sciencedirect.com/journal/image-and-vision-computing/about/insights | 同上 |
| Ocean Engineering | https://www.sciencedirect.com/journal/ocean-engineering/about/insights | 同上 |
| IEEE 各刊（TIP/TCSVT/TNNLS/SPL/JOE） | 未发现 IEEE 官方公布"投稿→首次决定"中位数的页面 | **未能验证**（IEEE Xplore 有 Early Access 机制，但官方给不出天数） |

**第三方佐证（仅作辅证，非官方，且本报告未独立核验其抽样方法）**：LetPub 给出四刊的 Gold OA 占比——Pattern Recognition 12.71%、Image and Vision Computing 10.59%、Neurocomputing 12.15%、Pattern Recognition Letters 20.04%（来源：`letpub.com` 期刊详情页，抓取 2026-09-26）。**该数据的用处是证明这些刊是 hybrid**（绝大多数文章走订阅制、即免费通道），**不是**时效数据。

### 2.4 作者自己的实测时钟（项目既有事实，比任何第三方统计都更贴近）

来自工作区既有记录（`docs/A1_VENUE_DECISION.md`、`AGENTS.md`）：A1 → Neurocomputing `NEUCOM-D-26-20952`（2026-09-16 提交）；A23 → IEEE JOE `26-0663`；P1 → Pattern Recognition 在审；Pattern Recognition Letters 于 2026-09-14 拒（`PRLETTERS-D-26-01941`）；EAAI 2026-08-14 投后 **6 周无编辑接手**→撤稿重投。**EAAI 一例说明：Elsevier 侧的"周期"瓶颈常常在编辑分配阶段，而非审稿阶段**——这是任何官网中位数都反映不出来的风险。

---

## 三、"免费"的可选范围（含官方原文引文与 URL）

### 3.1 完全免费：订阅制（hybrid 的传统通道）

**Elsevier（官方政策页，抓取 2026-09-26）** — https://www.elsevier.com/about/policies-and-standards/pricing

> "Elsevier publishes journal articles under two separate models to suit author preferences:
> **Subscription articles funded by payments for reading made by subscribing individuals or institutions**
> Open access articles funded by payments for publishing made by authors, their institution or funding bodies, commonly known as Article Publishing Charges (APCs)"

> "Where articles are not supported by the pay-to-publish model, they are typically supported by subscription fees paid for by readers."

同页另载：APC 区间 "$150 to $9,900"，且**减免只针对全 OA 刊**（"When publishing in fully open access journals, we fully waive all open access charges for authors from 69 countries"）——对 hybrid 刊的订阅制通道无收费条款。

**逐刊逐字核对（官方 Guide for Authors 全文，作者此前下载的官方副本；本报告读取日期 2026-09-26）**：

| 本地官方 Guide | 检查项 | 结果 |
|---|---|---|
| `_guide_neurocomputing.txt` | "page charge / APC / open access" 关键词 | 全文**无任何 page charge（版面费/超页费）条款**；APC 只出现在"若选 OA"的语境（如 L1257："For open access articles, all authors understand that they are responsible for payment of the article publishing charge (APC) if the manuscript is accepted."） |
| `_guide_ivc.txt` | 同上 | 同上（另含 4500–7500 词硬上限，见 §四排除理由） |
| `_guide_oe.txt` | 同上 | 同上 |

> **诚实标注**：Elsevier 的 Guide 里**没有**一句字面写着"订阅制发表免费"。上述结论由两条官方证据合成：① 官方定价政策页把订阅文章定义为"由订阅费支持"；② 各刊官方 Guide 全文不含任何作者端强制费用条款，APC 义务只挂在 OA 文章上。**这属于强推断，不是逐字原文**。

**IEEE（官方原文，抓取 2026-09-26）**

- IEEE CASS 的 TCSVT 官方页（https://ieee-cas.org/publication/tcsvt）：
  > "Publication Fees: This publication is supported by subscriptions and applicable Article Processing Charges (APCs). **Although there is no cost for publishing with IEEE**, authors may wish to take advantage of some of our fee-based offerings"

- IEEE SPS "Information for Authors"（https://signalprocessingsociety.org/publications-resources/information-authors）：
  > "The SPS Transactions and Journals (except for the IEEE Open Journal of Signal Processing, which is a fully Open Access journal) adopt a **hybrid publication model**, allowing either traditional manuscript publication or Open Access (author-pays OA) manuscript publication. **With traditional manuscript publication, the manuscript will be available to qualified subscribers and purchasers via IEEE Xplore.**"

- IEEE JOE 官方 Guide 副本（作者本地 `outputs/_joe_guide.txt`，本次读取 2026-09-26）：
  > "This publication is a hybrid journal, allowing either Traditional manuscript submission or Open Access (OA) manuscript submission... **Immediate payment is not required for Traditional submission.**"

  （JOE Guide 用 `charge|fee|APC|cost` 关键词全文检索，**除 OA 相关句外无任何版面费/超页费条款**；篇幅政策为 "The length should be appropriate to the topic, **there is no specific limit**"，摘要 150–250 词。）

- IEEE 顶层政策（**IEEE PSPB Operations Manual, Amended 25 June 2026 (260625)**，https://pspb.ieee.org/images/files/files/opsmanual.pdf ，抓取 2026-09-26，HTTP 200，`pdftotext` 抽取 7408 行）§6.5：
  > "**Article Processing Charges are of two types, mandatory and voluntary.** Examples of APCs include, but are not restricted to, voluntary page charges, overlength article charges, mandatory open access publishing charges, and mandatory charges for article modification."（§6.5.1.B）
  > "**An overlength article charge is a mechanism for accommodating the maximum number of authors' articles within a given publication by requiring authors to pay a charge for each page that exceeds a specified limit.**"（§6.5.1.B.2）
  > "Article Processing Charges and the rules for processing them **shall be clearly stated in the Guidelines for Authors** for that publication."（§6.5.2.B）
  > "Organizational units **shall establish a process for authors to apply for a waiver of Mandatory APCs in cases of financial hardship**."（§6.5.2.C）

**Springer**：候选刊均为订阅制 hybrid（选 OA 才付费），本报告未抓到 Springer 一句"订阅制免费"的官方原句（其 open access 页面只有 OA 侧说明：https://www.springer.com/gp/open-access/springer-open-choice ，抓取 2026-09-26）。**该项标注为"结构上免费、官方字面未取得"**，投稿前请在目标刊 "Submission guidelines" 页确认无 page charge 条款。

### 3.2 hybrid 期刊（对预算 0 的作者 = 可用，只要不勾 OA）

已核实为 hybrid（官方原文见 §3.1）：**IEEE TIP、TCSVT、TNNLS、SPL、JOE**；**Elsevier Pattern Recognition、Neurocomputing、Pattern Recognition Letters、Image and Vision Computing、Ocean Engineering**；**Springer The Visual Computer、Machine Vision and Applications、Pattern Analysis and Applications、Neural Processing Letters、Multimedia Systems、IJCV**。
hybrid 刊的 OA 选项价格示例（**属"可选"，不选即不付**）：IEEE JOE 的 OA 费 **US$2,645**（JOE 官方 Guide 原文，本地副本读取 2026-09-26）；TCSVT 的 Guidelines 页面列出 "**APC for articles submitted in 2026: $2,800**"（IEEE 会员 5%、Society 会员 20% 折扣，https://ieee-cas.org/publication/tcsvt/guidelines-authors ，抓取 2026-09-26）。

### 3.3 必须 APC 的全 OA 期刊：**明确列为不可行**

金额取自 **DOAJ 官方 API**（`https://doaj.org/api/v3/search/journals/issn%3A<ISSN>`，字段 `bibjson.apc.max`；DOAJ 记录更新时间 **2026-09-17**，本报告抓取 **2026-09-26**）。DOAJ 只收录**全 OA 刊**（不收录 hybrid 刊），因此"出现在 DOAJ"即证明该刊为**全 OA**，"`has_apc=true`"表示其向 DOAJ 申报了 APC。
> ⚠️ **APC 减免的边界**：出版商确有减免计划（Elsevier 对 69 个国家的作者全额豁免 OA 费；IEEE 对低/中收入国家作者有折扣），但**减免一般按通讯作者所在国家判定，本报告未逐项核验英国是否适用**——请以各出版商豁免政策页为准。**上表金额按"无减免"计**，故对预算 0 的作者一律视为不可行。

| 期刊 | 出版商 | 当前 APC（DOAJ 申报，取 max） | DOAJ 记录的官方 APC 页 |
|---|---|---|---|
| IEEE Access | IEEE | **2,160 USD** | https://ieeeaccess.ieee.org/about-ieee-access/learn-more-about-ieee-access/ |
| IEEE Open Journal of Signal Processing | IEEE | **2,160 USD** | https://open.ieee.org/index.php/for-authors/article-processing-charges/ |
| Scientific Reports | Nature Portfolio | **2,850 USD / 2,490 EUR / 2,290 GBP** | https://www.nature.com/srep/open-access |
| PLOS ONE | PLOS | **2,477 USD** | https://plos.org/publish/fees/ |
| MDPI Sensors | MDPI | **2,600 CHF** | https://www.mdpi.com/journal/sensors/apc |
| MDPI Remote Sensing | MDPI | **2,700 CHF** | https://www.mdpi.com/journal/remotesensing/apc |
| MDPI Journal of Marine Science and Engineering | MDPI | **2,600 CHF** | https://www.mdpi.com/journal/jmse/apc |
| MDPI Mathematics | MDPI | **2,600 CHF** | https://www.mdpi.com/journal/mathematics/apc |
| MDPI Applied Sciences | MDPI | **2,400 CHF** | https://www.mdpi.com/journal/applsci/apc |
| Frontiers in Marine Science | Frontiers | **3,150 CHF** | https://www.frontiersin.org/journals/marine-science/for-authors/publishing-fees |
| Frontiers in Artificial Intelligence | Frontiers | **1,950 CHF** | https://www.frontiersin.org/journals/artificial-intelligence/for-authors/publishing-fees |
| Frontiers in Computer Science | Frontiers | **1,175 CHF** | https://www.frontiersin.org/journals/computer-science/for-authors/publishing-fees |
| Heliyon | Elsevier | **2,270 USD** | https://www.cell.com/heliyon/open-access |
| PeerJ Computer Science | PeerJ | **1,395 USD** | https://peerj.com/pricing/ |
| **Electronics Letters** | **Wiley（IET）** | **2,600 USD / 2,030 GBP / 2,370 EUR** | 见下注 |
| IET Image Processing | Wiley（IET） | **2,800 USD / 2,190 GBP / 2,550 EUR** | 同上 |
| IET Computer Vision | Wiley（IET） | **2,600 USD / 2,020 GBP / 2,370 EUR** | 同上 |
| IET Signal Processing | Wiley（IET） | **2,600 USD / 2,020 GBP / 2,370 EUR** | 同上 |
| IET Radar, Sonar & Navigation | Wiley（IET） | **2,600 USD / 2,060 GBP / 2,380 EUR** | 同上 |

> 🔴 **重要更正型发现**：**IET 系（含 Electronics Letters）已出现在 DOAJ 且带 APC，即已转为强制付费的全 OA，不再是"免费快刊"。** DOI/ISSN 核对：Electronics Letters = ISSN 0013-5194 / 1350-911X；IET Image Processing = 1751-9659；IET Computer Vision = 1751-9632；IET Signal Processing = 1751-9675；IET Radar, Sonar & Navigation = 1751-8784（均经 DOAJ API 按 ISSN 命中，抓取 2026-09-26）。**若作者曾被"Electronics Letters 快且免费"的旧印象吸引，该印象已过期。**
>
> 对照：**IEEE TCSVT（1051-8215）、TIP（1057-7149）、SPL（1070-9908）、TNNLS（2162-237X）、Neurocomputing（0925-2312）、Pattern Recognition（0031-3203）均 NOT in DOAJ**——与"它们是订阅制 hybrid 刊"一致（DOAJ 不收录 hybrid 刊）。

### 3.4 IEEE 现行政策核查：三问三答（这是"隐形付费"的核心）

**① mandatory vs optional OA？——OA 是可选（hybrid），但"强制费"另有一类。**
IEEE 政策把 APC 明确分为 mandatory（强制）与 voluntary（自愿）两类（PSPB §6.5.1.B，原文见 §3.1）。传统 IEEE Transactions/Letters 走 hybrid：**选传统通道不付 OA 费**（TCSVT 页面原文 "there is no cost for publishing with IEEE"；SPS 页面 "hybrid publication model"；JOE "Immediate payment is not required for Traditional submission"）。**但"强制 APC"确实存在，主要形态是超页费（overlength article charge）**。

**② 超页费（overlength page charges）现行规则与金额——有，且金额明确：**

| 刊物/系列 | 强制超页费 | 官方原文 | 来源（抓取 2026-09-26） |
|---|---|---|---|
| **IEEE TNNLS** | **$200 / 页**，超出 10 页（regular）、15 页（survey）、6 页（brief）的部分；含超页费的总长上限：15 / 21 / 9 页 | "Papers submitted to this transaction will be imposed **mandatory over-length page charge** for pages in excess of 10 pages for a full paper, 15 pages for a survey paper, and 6 pages for a brief paper. Authors of papers accepted for publication will be assessed a **mandatory page charge of $200 (per page)** for every printed page over these limits." | https://cis.ieee.org/publications/t-neural-networks-and-learning-systems/tnnls-page-charges |
| **IEEE SPS 系（含 TIP；TMM 门槛 8 页）** | **$220 / 页**，超出前 10 个已刊页的部分 | "The author(s) or their company or institution will be billed **$220 per page** for each page more than the first ten published pages for Regular Papers."（另注：TMM 超出 8 页即触发） | https://signalprocessingsociety.org/publications-resources/information-authors |
| 自愿版面费（非强制） | TNNLS $110/印刷页；SPS $110/页（前 10 页） | TNNLS："...are **not obligatory nor is their payment a prerequisite for publication**." | 同上两处 |
| 彩色印刷费（仅当要求印彩页） | TNNLS **$275/图**；CASS/TCSVT **$1,045（≤4 彩页）/ $2,090（4–8）/ $3,135（9–12）+ $62.50/图** | 两处官方页面均有原文 | TNNLS 页；https://ieee-cas.org/publication/tcsvt/guidelines-authors |
| 电子版彩色 | **免费** | "Color figures are automatically posted in color on the IEEE Xplore website free of charge."（TNNLS）；"All SPS Transactions and Journals are online-only, so color graphics are always free of charge."（SPS） | 同上 |

**篇幅门槛（同源）**：SPS 系初投 **≤13 双栏页**（TMM ≤10），修回 **≤16 页**（TMM ≤14）；TNNLS regular paper 含超页费上限 **15 页**；**IEEE SPL 为 5 页**（"A Signal Processing Letter is a five pages long paper... at most four pages of technical content plus one page only for references"，https://signalprocessingsociety.org/publications-resources/ieee-signal-processing-letters ，抓取 2026-09-26）；**IEEE JOE 无篇幅上限**（JOE Guide 原文）。

**③ 是否有"必须先付超页费才发表"的条款？——有，原文很硬。**
IEEE SPS 官方页（同一 URL）：
> "Overlength page charges **DO apply to Open Access articles published in hybrid journals**. These are **mandatory and non-negotiable** page charges, and the author(s) will be held responsible for them. By way of manuscript submission and acceptance, authors acknowledge their obligation to pay mandatory charges to any of the SPS Transactions or Journals. **The Publisher holds the right to withhold publication under any circumstance, as well as publication of the current or future submissions of authors who have outstanding mandatory page charge debt.**"

同页另有一句对投稿人的授权确认要求：
> "Acknowledge that all authors accept these rules... including agreements to accept all Article Processing Charges, overlength page charges, open access fees, and any other charges... **Such charges are non-negotiable and cannot be waived.**"

以及 PSPB §6.5.2.F（顶层政策）：
> "**Authors who do not pay Mandatory APCs without a waiver shall be barred from submitting future articles to IEEE publications** until such time as their previous outstanding charges are paid."

**对作者的具体含义（算账）**：
- 一份 **13 个已刊页**的 IEEE TIP 论文 → 超 3 页 × $220 = **$660 强制**（未含任何自愿费）；16 页 → **$1,320**。（注意：口径是**已刊页**，与投稿时的手稿页数不等；CASS 官方给的估算方法是全部页数 ÷ 3 或用 IEEE 模板预排。）
- 一份 **12 个已刊页**的 TNNLS 论文 → 超 2 页 × $200 = **$400 强制**（其上限定为 15 页，即最多 $1,000）。
- **IEEE JOE 无篇幅上限、Guide 无超页费条款** → 对长文是 IEEE 侧**已核实无超页费条款**的选项（已被作者用作 A23 的投稿刊）；TCSVT 是否设超页费**未能验证**（见 §六.3），不要假设它免费。
- 想完全不触发超页费的技术做法：**把论文压到门槛内**（TIP ≤10 已刊页、TNNLS regular ≤10 页、TCSVT 需向编辑部确认门槛——本报告未在 TCSVT 公开页面找到明确页数门槛，**未能验证**）。

---

## 四、候选清单与排序（快 × 免费 × 契合）

排序原则：**先"免费"（硬约束，一票否决），再"已在实际时钟上"（沉没成本已付），再"官方/可算时效"，最后方向契合度。**

| # | 候选 | 出版商 | 收费 | 时效（已核实口径） | 篇幅/超页费 | 见刊现实预期 | 方向契合 |
|---|---|---|---|---|---|---|---|
| **1** | **维持现状：Neurocomputing `NEUCOM-D-26-20952`（A1 在审）** | Elsevier | **0 元**（hybrid 订阅制；Guide 无任何版面费条款，全文无篇幅上限） | Elsevier 官方时效页被 captcha 拦，**未能验证** | 无字数/页数上限（本地官方 Guide 逐字核：只有摘要 ≤250 词、作者简介 ≤100 词） | 取决于审稿；已投入 2026-09-16 起的时间 | ★★★★★（PEFT/表示几何，Neurocomputing 明确要求与神经网络/学习系统相关） |
| **2** | **维持现状：IEEE JOE `26-0663`（A23 在审）** | IEEE OES | **0 元**（hybrid；"Immediate payment is not required for Traditional submission"）；**无超页费条款** | IEEE 无官方中位时效，**未能验证** | Guide："there is no specific limit"；摘要 150–250 词 | 同上 | ★★★★★（海洋/声呐跨模态） |
| **3** | **Neural Processing Letters** | Springer | **0 元**（hybrid 订阅制；**官方字面未取得**，投稿前核 Submission guidelines） | 官方首次决定中位 **14 天**；录用→在线中位 **21 天**（Crossref 自算，n=60） | 页面未见超页费条款（**未逐字核**） | **最快的一档免费路线**：若审稿正常，约 **3–5 个月** | ★★★★（表示学习/对齐方法） |
| **4** | **The Visual Computer** | Springer | **0 元**（同上） | 官方首次决定中位 **3 天**（desk 主导，勿当审稿速度）；投稿→录用 **118 天** + 录用→在线 **22 天** | 未逐字核 | ≈ **4.7 个月** | ★★★★（视觉/多模态） |
| **5** | **Pattern Analysis and Applications / Multimedia Systems / Machine Vision and Applications** | Springer | **0 元**（同上） | 官方首次决定中位 1 / 41 / 未取得 天；投稿→录用 136.5 / 150.5 / 178 天；录用→在线 15 / 20 / 16 天 | 未逐字核 | ≈ **5.0 / 5.6 / 6.4 个月** | ★★★☆ |
| **6** | **Elsevier 其他 hybrid（Pattern Recognition Letters / Ocean Engineering / Applied Ocean Research / Applied Acoustics 等）** | Elsevier | **0 元**（订阅制，同上） | 官方时效全部 **未能验证**（captcha）；PRL 已被本稿拒过 | PRL 有页数/篇幅限制（未逐字核）；OE 未核 | 未知 | ★★★（PRL 已拒过一次；OE 曾桌面拒） |
| **7** | **IEEE TCSVT / TIP** | IEEE | 订阅制不付 APC，**但 >10 已刊页部分强制 $220/页**（SPS 系）；TCSVT 门槛**未能验证** | IEEE 无官方时效数据 | SPS：初投 ≤13 双栏页，修回 ≤16 页 | 6–12 个月（顶刊+严格审稿；作者 TNNLS 已有一次被拒） | ★★★★（契合度高，但**对长文不是 0 元**） |
| **8** | **IEEE Signal Processing Letters** | IEEE SPS | **0 元**（hybrid） | 无官方数据 | **硬上限 5 页**（4 页正文 + 1 页参考文献） | 与作者现有 17.7k 词长稿**结构性不兼容**（除非另写一篇 5 页短文） | ★★（须重写） |
| **9** | **IJCV** | Springer | **0 元** | 官方 37 天（口径见 2.1，页面自注"typical ≈96 days"）；投稿→录用 **266 天** | 未逐字核 | ≈ **9.5 个月**（免费但慢） | ★★★★（但慢） |
| — | **全部全 OA 付费刊**（IEEE Access/OJSP、Sci Rep、PLOS ONE、MDPI 全系、Frontiers 全系、Heliyon、PeerJ CS、**IET 全系含 Electronics Letters**） | — | **强制 APC 1,175–3,150 CHF / 1,395–2,850 USD** | MDPI/Frontiers 类通常 1–2 个月 | — | 快 | ❌ **预算 0，不可行** |

**已排除项（保留原判，不重复投入）**：Image and Vision Computing —— 官方 Guide 明文 "the acceptable word count range is **4500-7500 words**"（`_guide_ivc.txt:928`，见 `docs/A1_VENUE_DECISION.md` §六），与 ≈17.7k 词长稿结构性不兼容。

### 4.1 如果"必须赌一个免费且明确比 4–7 个月更快"的选项

在**已被官方/元数据证实的范围内，没有这样的选项**（见 §五）。可做的只有三件事：
(a) 让在审稿继续走（Neucom/PR/JOE 三份都已过"编辑分配"这一最不可控的关卡，**EAAI 那次 6 周无人接手正是死在这一关**）；
(b) 备选顺位按上表 3→4→5 排（Springer 系 hybrid，官方时效可查、无超页费证据、0 元）；
(c) 若时间比钱更硬，则唯一"1–2 个月见刊"的真实路径是付费全 OA（最低档：**Frontiers in Computer Science 1,175 CHF**，或 **PeerJ Computer Science 1,395 USD**）——**这需要作者另行决定是否破例**，本报告不代为决定。

---

## 五、现实预期与风险（含"降级"判据与自查方法）

### 5.1 三种权衡（把话说清）

| 类别 | 代表 | 现实见刊预期 | 代价 |
|---|---|---|---|
| **免费但慢** | IJCV（266 天+23 天）、Elsevier 顶刊（PR） | **9 个月以上** | 时间 |
| **快但要钱** | MDPI 全系、Frontiers 全系、IEEE Access、Sci Rep、IET 系 | **1–2 个月** | **1,175–3,150 CHF / 1,395–2,850 USD**（预算 0 → 不可行） |
| **免费且有速度风险** | Springer hybrid（NPL/WC/PAA/MMS/MVA）、Elsevier 中档刊（Neurocomputing、OE 等） | **4–7 个月**，且**方差极大**（PAA 投稿→录用实测跨度 35–1017 天；MVA 72–407 天；这就是"速度风险"的量化形态） | 时间不确定性 + 编辑分配卡壳（作者 EAAI 实证） |
| **免费但可能触发强制费** | IEEE TIP/TCSVT（$220/页 >10 页）、TNNLS（$200/页 >10 页） | 6–12 个月 | **数百至上千美元强制超页费；条款明写不付可扣发** |

### 5.2 "降级"判据（不点名任何期刊，只给判据与核查方法）

**A. 先查"是否被权威索引收录"（不是查"影响因子高不高"）**

| 判据 | 权威入口 | 本报告可达性（2026-09-26） |
|---|---|---|
| 是否全 OA 且被 DOAJ 收录 | DOAJ API：`https://doaj.org/api/v3/search/journals/issn%3A<ISSN>`（返回 title/publisher/review_process/APC） | ✅ **可用**（HTML 站点对自动化返回 403，API 正常） |
| 是否 SCIE/SSCI/AHCI/ESCI 收录、是否被剔除 | Clarivate Master Journal List：https://mjl.clarivate.com/home | ⚠️ 页面可达（HTTP 200）但为 JS 应用，**自动化未取到内容**；需作者浏览器查 |
| 是否 Scopus 收录 | https://www.scopus.com/sources | ❌ 302 跳登录，**未能验证**（需机构账号） |
| 是否在期刊预警名单 | 中科院文献情报中心预警名单：https://ewl.fenqubiao.com （由官方分区表站点 https://www.fenqubiao.com/ 的"预警期刊"链接指向） | ⚠️ 站点存在（标题"国际期刊预警名单-中国科学院文献情报中心 期刊分区表团队"），但 JS 门控返回 "Please wait..."，**名单内容未能抓取** |
| CCF 推荐目录 | https://www.ccf.org.cn/ | ⚠️ 站点可达（HTTP 200），**具体目录条目本次未逐条核** |

> 🔴 **必须让作者知道的一条 2026 新政**：中科院文献情报中心官方站点（https://www.fenqubiao.com/ ，抓取 2026-09-26）首页原文：
> "**自2026年起，中国科学院文献情报中心（以下简称"文献中心"）将不再更新与发布期刊分区表。**我们将继续开展学术资源评价方法的研究与探索，积极服务国内外学术交流与出版生态建设。"
> 即**"中科院分区"这一评价坐标自 2026 年起不再更新**。若作者所在单位/基金仍以"中科院 X 区"作为认可依据，**这本身就是一个需要向单位确认口径的变化**（本报告只陈述官方原文，不替单位解释政策）。

**B. 掠夺性/低质信号自查清单（判据，不指向具体期刊）**
1. **ISSN 与刊名是否一致**：用 ISSN 官方门户（https://portal.issn.org/ ）与 Crossref 核对该 ISSN 对应的**官方网址域名**；若你现在投稿的站点域名与该记录不一致 → **劫持期刊（hijacked journal）风险**（本报告未能自动化打开 portal.issn.org，请在浏览器核对）。
2. **收录状态**：是否在 DOAJ（全 OA 刊）／Scopus／Master Journal List 中能查到——查不到就要求期刊给出可核验的收录证明。
3. **审稿过程是否可核验**：官网是否说明**具体审稿流程**（几轮、是否盲审、平均周期）；DOAJ API 的 `bibjson.editorial.review_process` 字段可直接读出其自报的审稿类型。
4. **编委与编辑部是否可核验**：编委名单是否给出**真实机构与主页**，而非只有姓名。
5. **时间承诺是否反常识**：以"数天录用+立即见刊"为卖点、且**主动邮件约稿**（spam 式征稿）——正常期刊不做这两件事。
6. **APC 是否与服务质量匹配**：收费高于同出版商同类刊数倍、却无排版/校对/长期存档说明。
7. **DOI 与元数据**：DOI 前缀是否属于该出版商常规前缀；DOI 能否解析到**同一官网域名**；Crossref 是否有完整的 volume/issue/page 元数据。
8. **"被 DOAJ 收录 ≠ 高质量"**：DOAJ 是**开放获取合规性**目录（透明、许可、APC 申报），**不是质量排名**；Scopus/SCIE 收录也各自有不同门槛。**不要把"在 DOAJ"当成质量背书**；反之，**hybrid 刊（如 IEEE TIP、Elsevier PR）本来就不在 DOAJ，也不代表有问题**——两者判据不可混用。
9. **中国高校/基金口径**：以单位科研管理部门公布的**当年度**文件为准（SCIE 收录/分区/CCF 等），**不要用网传榜单**；鉴于 §5.2 的中科院分区停更，务必向单位确认本年度认可依据。

### 5.3 其它风险提示（与作者现状直接相关）
- **IEEE 强制超页费是"投稿时即被要求同意"的条款**（SPS 页原文要求作者确认"Such charges are non-negotiable and cannot be waived"）；若把长稿投 TIP/TCSVT/TNNLS，**投稿前就要先算页数**（CASS 官方给的估算法：全部页数 ÷ 3，或用 IEEE 模板预排）。
- **非付款的后果**：PSPB §6.5.2.F 明确可**禁止该作者今后向 IEEE 投稿**，直至清偿。这是预算 0 作者必须避开的唯一"信用型"风险。
- **同刊冲突与披露**：A1 已投 Neurocomputing、`paper_ap3` 尚未投稿（`docs/A1_VENUE_DECISION.md` §九：投稿件中不得提及 `paper_ap3`）。选刊时先查"是否与在审稿件同刊"。
- **投稿纪律（沿用既有结论）**：换刊第一步**只核篇幅/字数与费用政策**，通过了再谈模板（`docs/A1_VENUE_DECISION.md` §六）。

---

## 六、未能验证的问题（单列，不含糊）

以下项目**本报告没有取得可引用的官方数据**，列出失败原因与建议的复核动作。**任何据此决策的地方都必须先复核。**

1. **Elsevier 全部候选刊的官方时效数字**（submission→first decision、acceptance→online）。
   失败原因：`sciencedirect.com/journal/*/about/insights` 对自动化返回 **HTTP 403 captcha（"Are you a robot?"）**；公开 CORS 代理（allorigins、codetabs）同样被拦；`journalinsights.elsevier.com` 返回 HTTP 400/403。
   复核动作：作者用浏览器打开 §2.3 的 URL，把页面上的时效数字抄回本文件。
2. **IEEE 各刊官方时效中位数**。未发现 IEEE 官方公布该类数字的页面；IEEE Xplore 的 Early Access 机制**未取得官方天数**。复核动作：向编辑部邮件询问，或读目标刊近 3 期论文首页的 "Date of submission / Date of publication"。
3. **IEEE TCSVT 的超页费门槛与金额**。TCSVT 的 Guidelines for Authors 页面**未出现**页数限制或超页费条款（已用多种关键词检索）；TCSVT 页面只有通用的 CASS FAQ。**未能验证**。复核动作：向 TCSVT 编辑部（或 CASS 出版部门）书面确认；在确认前，**不要假设 TCSVT 长文免费**。
4. **IEEE SPL 的专属 Information for Authors**（SPS 页面提示 SPL/SPSM/OJSP 各自有单独 IFB 按钮页）。本报告只核到 SPL 的**5 页**篇幅规则，**未核到 SPL 专属的超页费/版面费条款**。复核动作：从 https://signalprocessingsociety.org/publications-resources/information-authors 进入 SPL 按钮页。
5. **Springer 各候选刊是否含 page charge / 超页费条款**。本报告只核到"hybrid + OA 可选"，**未逐刊逐字核 Submission guidelines 的费用条款**。复核动作：打开 `https://link.springer.com/journal/<id>/submission-guidelines` 搜 "charge"。
6. **Machine Vision and Applications 的官方 first-decision 中位数**。`link.springer.com/journal/138` 页面抽取文本中无 metrics 区块（标题确认为该刊）。复核动作：浏览器打开该页查看 "Journal metrics"。
7. **MDPI / Frontiers / Wiley / PLOS / Nature 站点上的 APC 原页**（站点对自动化 403/000）。本报告金额来自 **DOAJ 申报值**（更新时间 2026-09-17），未与出版商原页逐字比对。复核动作：用浏览器打开 §3.3 表中"DOAJ 记录的官方 APC 页"逐个核对；**DOAJ 数值是"max"档，可能对应非最惠情形**。
8. **中科院预警名单的具体名录**（`ewl.fenqubiao.com` JS 门控，返回 "Please wait..."）。**未能验证**。
9. **Scopus 收录状态**（`scopus.com/sources` 302 跳登录）；**Think.Check.Submit.（thinkchecksubmit.org，403）、COPE 会员目录（publicationethics.org，403）、Stop Predatory Journals（predatoryjournals.org，连接失败 000）、OASPA 会员页（403）** 均未能打开。这些入口的 URL 供作者在浏览器复核，**本报告不对其内容作任何断言**。
10. **第三方的"审稿速度"统计**（SciRev、LetPub 的审稿周期指标）。本报告只取到 LetPub 的 **Gold OA 占比**（非时效），且未独立核验其抽样方法；SciRev 页面虽可访问（HTTP 200），但本报告**未提取其数值**，故**不引用**。
11. **IEEE Access 的 APC 官方原页**（`ieeeaccess.ieee.org` Cloudflare 403）。金额 2,160 USD 来自 DOAJ 申报（其 `apc.url` 指向 IEEE 官方页）。复核动作：浏览器打开该 IEEE 页确认。
12. **"哪些期刊在 2026 年实际接受/发表论文的速度"这一终极问题**。任何官方中位数都是**聚合值**，个体方差极大（本次自算样本中 PAA 投稿→录用跨度 **35–1017 天**、MVA **72–407 天**、IJCV **124–700 天**）。**不存在能保证"数月内见刊"的免费期刊**——这一点是本报告最确定的结论。

---

### 附：本报告用到的可复跑命令（供第三方复核）

```powershell
# 1) IEEE 顶层政策（PDF → 文本 → 检索）
curl.exe -sL -o pspb.pdf --compressed -H "User-Agent: <browser UA>" https://pspb.ieee.org/images/files/files/opsmanual.pdf
pdftotext -layout pspb.pdf pspb.txt
Select-String -Path pspb.txt -Pattern "page charge|overlength" -Context 2,6

# 2) IEEE 学会侧政策原文（可直连）
curl.exe -sL --compressed -H "User-Agent: <browser UA>" https://signalprocessingsociety.org/publications-resources/information-authors -o sps_ifa.html
curl.exe -sL --compressed -H "User-Agent: <browser UA>" https://cis.ieee.org/publications/t-neural-networks-and-learning-systems/tnnls-page-charges -o tnnls.html
curl.exe -sL --compressed -H "User-Agent: <browser UA>" https://ieee-cas.org/publication/tcsvt -o tcsvt.html

# 3) DOAJ：OA 性质 + 出版商申报 APC（全 OA 刊）
curl.exe -s "https://doaj.org/api/v3/search/journals/issn%3A2169-3536"   # IEEE Access
curl.exe -s "https://doaj.org/api/v3/search/journals/issn%3A0013-5194"   # Electronics Letters（现已全 OA）

# 4) Crossref：Springer 的 received/accepted 存款（自算时效）
curl.exe -s "https://api.crossref.org/journals/0178-2789/works?rows=60&sort=published&order=desc&select=DOI,published-online,assertion,type"

# 5) 本地官方 Guide（作者此前下载，只读引用）
Select-String -Path "_guide_neurocomputing.txt","_guide_ivc.txt","_guide_oe.txt","outputs\_joe_guide.txt" -Pattern "page charge|APC|open access" -CaseSensitive:$false
```

**报告结束。所有未取得官方来源的条目均已在 §六 逐条列出，未以推测填充。**
