# Paper A 转投候选：SCIE 核验与契合度评估（2026-10-26）

> **任务**：Neurocomputing 对 Paper A 桌面拒稿（`NEUCOM-D-26-23760`，编辑 Ana Carolina Lorena，未送外审），
> Elsevier 提供 article transfer，**答复截止 2026-11-24 23:59**。按 standing rule（`AGENTS.md`/`CLAUDE.md`：
> "不管投哪，必须是SCI期刊，记录进规则"），任何转投目标在写进方案前必须完成 **MJL 一手核实**并在
> `docs/VENUE_SCI_REGISTRY.md` 登记来源 URL 与核实日期。本文件是核实记录与契合度评估。
> **核实人**：agent `p3-stats`；**核实日期**：**2026-10-26**（Asia/Shanghai）。
> **稿件**：Paper A，`paper合/`（Neurocomputing 变体 `main_nc.pdf` **79 页**；Springer 变体 56 页）。
> 内容：PEFT 适应位点选择（视觉编码器 / projector / 语言主干 / 全栈）与对比双编码器 modality-gap 演化的
> 理论 + 经验规律 + 大量负结果。

---

## 1. 结论（一句话）

**8 个候选刊物全部在 Clarivate Master Journal List（MJL）上判为 SCIE**（`Web of Science Core Collection:
Science Citation Index Expanded`），**没有一个是 ESCI-only / 未收录** ⇒ 按资格规则**全部可作转投候选**；
真正区分它们的是**篇幅限制与 scope 契合度**（见 §3），而不是索引资格。
第二来源（Elsevier 的 Abstracting & Indexing 页）**不可达**，本轮判定由 MJL 一手来源单独支撑（§4 如实记录）。

---

## 2. 逐刊核验表（MJL 一手结果）

> MJL 检索 URL 统一为 `https://mjl.clarivate.com/search-results?issn=<ISSN>&hide_exact_match_fl=true`；
> 8 次检索均返回 **1 条结果**，结果标题为 `Journals Relevant To "<ISSN>"`，刊名/ISSN 与候选一致，
> 结果卡片逐字含：`Web of Science Core Collection: Science Citation Index Expanded`。

| # | 刊名 | ISSN / eISSN | 出版商（MJL 登记）| 收录类型 | 核实日期 | 核实途径 |
|---|---|---|---|---|---|---|
| 1 | **Pattern Recognition** | 0031-3203 / 1873-5142 | Elsevier Sci Ltd | **SCIE ✅** | 2026-10-26 | MJL（Edge CDP，浏览器渲染后读结果卡片）|
| 2 | **Information Fusion** | 1566-2535 / 1872-6305 | Elsevier | **SCIE ✅** | 2026-10-26 | 同上 |
| 3 | **Knowledge-Based Systems** | 0950-7051 / 1872-7409 | Elsevier | **SCIE ✅** | 2026-10-26 | 同上 |
| 4 | **Engineering Applications of Artificial Intelligence** | 0952-1976 / 1873-6769 | Pergamon-Elsevier Science Ltd | **SCIE ✅** | 2026-10-26 | 同上 |
| 5 | **Image and Vision Computing** | 0262-8856 / 1872-8138 | Elsevier | **SCIE ✅** | 2026-10-26 | 同上 |
| 6 | **Computer Vision and Image Understanding** | 1077-3142 / 1090-235X | Academic Press Inc Elsevier Science | **SCIE ✅** | 2026-10-26 | 同上 |
| 7 | **Applied Soft Computing** | 1568-4946 / 1872-9681 | Elsevier | **SCIE ✅** | 2026-10-26 | 同上 |
| 8 | **Expert Systems with Applications** | 0957-4174 / 1873-6793 | Pergamon-Elsevier Science Ltd | **SCIE ✅** | 2026-10-26 | 同上 |

**MJL 同页 Additional Web of Science Indexes（逐刊）**：8 刊均为
`Current Contents Engineering, Computing & Technology | Essential Science Indicators`；
**Pattern Recognition** 另含 `Biological Abstracts | BIOSIS Previews`。

**逐刊 MJL 来源 URL**（可直接复核）：

- Pattern Recognition：`https://mjl.clarivate.com/search-results?issn=0031-3203&hide_exact_match_fl=true`
- Information Fusion：`https://mjl.clarivate.com/search-results?issn=1566-2535&hide_exact_match_fl=true`
- Knowledge-Based Systems：`https://mjl.clarivate.com/search-results?issn=0950-7051&hide_exact_match_fl=true`
- EAAI：`https://mjl.clarivate.com/search-results?issn=0952-1976&hide_exact_match_fl=true`
- Image and Vision Computing：`https://mjl.clarivate.com/search-results?issn=0262-8856&hide_exact_match_fl=true`
- CVIU：`https://mjl.clarivate.com/search-results?issn=1077-3142&hide_exact_match_fl=true`
- Applied Soft Computing：`https://mjl.clarivate.com/search-results?issn=1568-4946&hide_exact_match_fl=true`
- Expert Systems with Applications：`https://mjl.clarivate.com/search-results?issn=0957-4174&hide_exact_match_fl=true`

---

## 3. 资格判定 + 对 Paper A 的契合度（一行评估 + 页数/字数限制）

### 3.1 可作候选（SCIE，8 刊）

| 刊名 | 页数/字数限制（guide for authors 实际读到）| 对 Paper A 的一行契合评估 |
|---|---|---|
| **Pattern Recognition** | **20–35 页**（单栏双倍行距，含 figures/tables/references/biosketches；**附录不计入**；survey 可至 40 页；<20 页建议改投 PRL）| 方法论/表征分析 + 负结果可发、scope 匹配较好；但 79 页变体与 20–35 页硬限差距大，必须先做"贡献前置 + 负结果归节 + 大幅压缩"，否则重演 desk-reject。 |
| **Information Fusion** | 原创研究 **10–35 页**（含全部内容）、**最多 50 条参考文献**；综述可至 50 页/300 refs | 多模态对齐分析可勉强归入 fusion，但本文是 image–text 双编码器对齐理论、并非多源信息融合；**契合中低**，且 **≤50 条参考文献是硬约束**（Paper A 引文数需另行核对）⇒ 不建议优先。 |
| **Knowledge-Based Systems** | 原创/综述**最好 ≤20 双倍行距页**（含表图）；short communication ≤10 页 | 偏知识系统/应用，纯理论 + 大量负结果契合**低**；20 页上限对 79 页变体几乎不可行 ⇒ 不建议。 |
| **Engineering Applications of Artificial Intelligence** | **≤50 页**（硬性，超过即 desk rejection），文件 ≤100 MB | 工程应用导向；本文理论与负结果无应用落点，契合**低**；50 页硬限虽可容长度，但 scope 不合 ⇒ 不建议。 |
| **Image and Vision Computing** | **正文 4500–7500 words**（Word Count 节；opinion paper ≤2 页）| 对比双编码器对齐/PEFT 属视觉-语言表征分析，契合**中**；但 4500–7500 词硬限要求把 79 页压成短版方法/分析文 ⇒ 可行但需重写而非转格式。 |
| **Computer Vision and Image Understanding** | guide 中**未见页数/字数硬限**（仅摘要 ≤250 words 等常规项）| 多模态对比表征理论 + 表征诊断契合**较好**；**无页数硬限**，对长篇理论稿最友好 ⇒ 本组中**首选候选之一**（仍需先修 framing）。 |
| **Applied Soft Computing** | technical paper **20–30 页、至多 50 页**；letter ≤3500 words（约 10 页）| 软计算/应用为主，theory-first 契合**中低**；20–30 页需大压缩 ⇒ 不建议优先。 |
| **Expert Systems with Applications** | guide 中**未见页数/字数硬限**（仅摘要 ≤250 words 等常规项）| 专家/应用系统导向，纯理论 + 负结果契合**低**；虽无长度限制但 scope 不合 ⇒ 不建议。 |

### 3.2 不合格 / 排除（本次 8 刊之外，供对照）

| 刊物 | 结论 | 依据 |
|---|---|---|
| **Neural Networks**（0893-6080）| **排除**（虽 SCIE）| 同一稿族已被该刊拒稿（`NEUNET-D-26-09426`），转投流程上不可行 |
| Frontiers in Artificial Intelligence（2624-8212）| **不合格** | ESCI/Scopus，非 SCIE（registry §4.3）|
| Frontiers in Big Data（2624-909X）| **不合格** | ESCI/Scopus，非 SCIE（registry §4.3）|
| `Patterns`（2666-3899）| **仍待核** | 疑似 ESCI；本轮不在候选清单内，未核 |

> 判据：Web of Science Core Collection 的 **SCIE** 才合格；ESCI-only / Scopus-only / 无 WoS 收录一律不合格。
> 8 刊均只显示 SCIE 一行（无 ESCI 行），不是"SCIE+ESCI 双收录"的模糊状态。

---

## 4. 访问路由与阻塞项（如实记录）

| 目标 | 结果 | 说明 |
|---|---|---|
| **MJL（mjl.clarivate.com）** | ✅ 成功 | JS 单页应用：静态 `web_fetch` 只返回标题；本轮用 **Edge CDP 代理**（`web-access` skill 路由）在浏览器渲染后读取结果卡片。**8 条判定全部来自这条路由。** |
| **Elsevier A&I 页（8 刊）** | ❌ 未取得 | `https://www.sciencedirect.com/journal/<slug>/about/abstracting-and-indexing` **重定向到期刊首页**，页面无索引数据库清单；`journalinsights.elsevier.com` 亦重定向。与 2026-10-25 对 Neurocomputing/PRL 的记录一致（Elsevier 已不在公开页列 A&I）⇒ 8 刊**无第二来源**，判定仅由 MJL 一手来源支撑，**未用第三方循环印证**。 |
| **ScienceDirect（headless 直连）** | ❌ 被拦 | 返回 "There was a problem providing the content you requested"（`CPE00001`，HTTP 403 类）；换 **可见的 Edge（独立临时 profile）** 后同一页面可正常打开 ⇒ 阻塞原因是 headless 检测，不是内容不存在。 |
| **guide for authors（8 刊）** | ✅ 成功（可见 Edge）| 各刊 `/publish/guide-for-authors` 页面均可读；§3 的页数/字数限制是**从这些页面逐字摘录**，未使用第三方转述。 |
| **Elsevier Article Transfer Service 公共页** | ✅ 成功 | `https://www.elsevier.com/authors/article-transfer-service`：说明 ATS 由编辑团队 + 匹配算法推荐更合适的期刊、可"无需重新排版"转移；**`enhanced transfer offer` 可能含 conditional acceptance 或 guaranteed peer review**。**该公共页不列出本稿可转的具体期刊清单**；实际清单在编辑邮件/作者专属转投链接中（含个人 token，本轮**未使用**）。 |
| **JCR 分区 / Impact Factor** | ❌ 不可得 | JCR 需订阅登录；按规则**不填分区**。ScienceDirect 期刊页公开显示的 CiteScore/IF 属出版商展示的第三方数据，仅可记录、不用于资格判定（本轮只记录资格相关事实）。 |
| **作者专属转投链接** | 未使用 | 按指示**不使用**作者个人 token/链接；因此"服务实际提供哪些期刊"无法在无 token 情况下枚举，需以编辑邮件里的 offer 列表为准，再与 §3 候选比对。 |

---

## 5. 写回 registry 的动作

- `docs/VENUE_SCI_REGISTRY.md`：
  - **新增 §4.4**（Paper A 转投 8 刊的 MJL 核实表：ISSN/eISSN、出版商、SCIE、来源 URL、2026-10-26、页数/字数限制）；
  - **新增 §4.5**（资格判定：8 刊可作候选；Neural Networks 排除）；
  - §4.1 的三行（Pattern Recognition / Information Fusion / Knowledge-Based Systems）补注"2026-10-26 MJL 已复核，见 §4.4"；
  - §4.1 的 Neural Networks 行补注"同一稿族已拒（`NEUNET-D-26-09426`），Paper A 不得转投"；
  - §5 变更记录新增 2026-10-26 行。
- **五个当前目标刊物（Neurocomputing / PAA / PRL ×2 / IEEE JOE）所在 §3 未动。**

---

## 6. 诚实标注 / 未决项

1. **第二来源缺失**：Elsevier A&I 页已不可达（重定向/无清单），8 条 SCIE 判定均只有 MJL 一手来源——
   这与 2026-10-25 对 Neurocomputing/PAA/PRL/IEEE JOE 的处理一致（当时也只有 PAA 有 Springer 第二来源）。
2. **JCR 分区未取得**（需订阅），按规则不填。
3. **转投服务实际 offer 列表未取得**（需作者个人链接/token，按指示未使用）；本文件只能确认"候选刊是 SCIE"，
   不能确认"ATS 一定提供这些刊"——最终以编辑邮件中的 offer 列表为准。
4. **收录状态会变**：本核验是 2026-10-26 的快照；正式投稿前应按 §2 重新复核。
5. **篇幅限制来自各刊 guide for authors 当前版本**（可见 Edge 读取，2026-10-26）；若期刊改版需以最新 guide 为准。
