# Paper A 第二轮候选刊：MJL 核实 + 指南可行性（2026-10-26）

> **任务触发**：CVIU 因指南要求作者 **Vitae（≤100 词 bio + 护照型照片）** 而被排除（操作者"换期刊吧"）。
> 本轮按 standing rule（`AGENTS.md`：投稿目标必须是 SCIE 且须 MJL 一手核实 + 登记 URL/日期）核实 4 个新候选：
> **Information Sciences**、**International Journal of Computer Vision (IJCV)**、**Applied Intelligence**、
> **Cognitive Computation**。
> **方法**：MJL（JS 单页应用）与 Elsevier guide 用**可见 Edge + CDP**（headless 被 403/CPE00001 拦）；
> Springer 的三个 `submission-guidelines` / `aims-and-scope` 页同样用可见 Edge 渲染后读取。
> 捕获的原文留在 `%TEMP%\mjl_*.txt`、`guide_*.txt`、`scope_*.txt`；本文件逐条引用关键原句。
> **日期**：全部核实与访问均为 **2026-10-26（Asia/Shanghai）**。

---

## 1. 结论（一句话）

**四刊全部为 SCIE**（MJL `Exact Match Found` 卡片逐条确认）。但 **Information Sciences 与 CVIU 踩同一个坑**：
它的指南同样要求 **Vitae + 护照型照片**（原文见 §3），且页数/图表指导值要求把 83 页压到 40–45 页、图表压到 8–10 个。
**Cognitive Computation** 要求 **Word 投稿 + 全篇 ≤10,000 词 + 结构化摘要**，改造量最大且 scope 最不合。
⇒ **推荐 Applied Intelligence**（无页数限制、无 Vitae、无 highlights、摘要 150–250 与关键词 4–6 均已满足）；
**IJCV 作为"冲刺"备选**（25 journal pages 上限下 39 页双倍行距主文大概率可容，但选择性极高）。

---

## 2. MJL 核实（一手来源，逐刊）

| 刊 | 出版商（MJL 卡片） | ISSN / eISSN | 收录 | MJL 来源 URL（本次实际访问） | 日期 |
|---|---|---|---|---|---|
| **Information Sciences** | ELSEVIER SCIENCE INC（New York） | 0020-0255 / 1872-6291 | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0020-0255&hide_exact_match_fl=true` | 2026-10-26 |
| **International Journal of Computer Vision** | SPRINGER（Dordrecht） | 0920-5691 / 1573-1405 | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0920-5691&hide_exact_match_fl=true` | 2026-10-26 |
| **Applied Intelligence** | SPRINGER（Dordrecht） | 0924-669X / 1573-7497 | **SCIE** | `https://mjl.clarivate.com/search-results?issn=0924-669X&hide_exact_match_fl=true` | 2026-10-26 |
| **Cognitive Computation** | SPRINGER（New York） | 1866-9956 / 1866-9964 | **SCIE** | `https://mjl.clarivate.com/search-results?issn=1866-9956&hide_exact_match_fl=true` | 2026-10-26 |

四张卡片共同字段（逐字）：`Exact Match Found` + 刊名 + `Publisher:` + `ISSN / eISSN:` + `Web of Science Core Collection: **Science Citation Index Expanded**` + `Additional Web of Science Indexes: Current Contents Engineering, Computing & Technology | Essential Science Indicators`。
四刊**均无 ESCI 行**（不是"SCIE+ESCI 双收录"的模糊状态）。

**第二来源**：仍不可得（Elsevier/Springer 的 A&I 页不列索引库）——与 2026-10-25/26 既有记录一致，非本轮新增阻塞。

---

## 3. 指南要点（逐刊，英文原句）

### 3.1 Information Sciences（Elsevier）

| 项 | 原文 / 结论 |
|---|---|
| 评审 | "This journal follows a **single anonymized** review process." ⇒ 单盲 |
| **长度（关键）** | "As a guideline: **experimental manuscripts should not be longer than 40 double-spaced typed pages and 8 figures + tables**; for **theoretical manuscripts a maximum of 45 pages and 10 figures + tables** is suggested." ⇒ 按**投稿稿**计（双倍行距），未提附录豁免 |
| 摘要 | **冲突**：刊内行 "Contributions should contain an **Abstract (of up to 200 words)**"；Elsevier 通用段 "does not exceed **250 words**" ⇒ 以 **≤200** 为安全值 |
| 关键词 | "You are required to provide **1 to 7** keywords" ⇒ 6 ✓ |
| Highlights | "You are **encouraged** to provide article highlights… **3 to 5** bullet points, each a maximum of **85 characters**" ⇒ 非必需；现稿 5 条 ≤71 字符 ✓ |
| **Vitae / 照片（致命）** | "Please submit a short (**maximum 100 words**) biography of each author and **include a passport-type photograph as a separate figure**. Please provide the biography in an editable format (e.g. Word, not in PDF format)." ⇒ **与 CVIU 同一要求、同一模板段** |
| LaTeX | "Submit files with .doc/.docx … and **.tex** for LaTeX files. **A PDF is not an acceptable source file.**" ⇒ LaTeX 源码必需 |
| 参考文献 | Elsevier 刊内风格（投稿不严格；接受后 proof 阶段套版）|
| 数据声明 | "For this journal, **Option C** instructions … apply"（deposit + cite/link + statement）⇒ **Option C** |
| scope（一行） | "publish original, innovative and creative research results … **balanced coverage of both theory and practice**… Topics include … **Artificial Intelligence, Computational Intelligence** … Image Processing and Computer Vision Systems" |

### 3.2 International Journal of Computer Vision（Springer）

| 项 | 原文 / 结论 |
|---|---|
| 评审 | guide **未明示**（只有 Springer 通用句："If the journal that you are submitting to uses **double-anonymous** peer review …"）⇒ 需在投稿系统确认 |
| 长度 | submission-guidelines 页**无页数限制**；**aims & scope 页**给："**Regular articles (up to 25 journal pages)** present major technical advances of broad general interest."（journal pages = 排版页，不是双倍行距稿页）|
| 摘要 | "Please provide an abstract of **150 to 250 words**" ⇒ 246 ✓ |
| 关键词 | "Please provide **4 to 6** keywords" ⇒ 6 ✓ |
| Highlights | **无要求**（0 命中）|
| Vitae / 照片 | **无要求**（仅图注中提及 photograph 的图形说明）✓ |
| LaTeX | "For LaTeX submissions we encourage authors to use the Springer Nature LaTeX template… **choosing the formatting option '[iicol]'**. The submission should include the original source (including all style files and figures) **and a PDF version** of the compiled output."；"**Please do not use subfolders** for your LaTeX submission, e.g. for figures or bibliographic files." |
| 参考文献 | **APA v7**："Authors are encouraged to follow official APA version 7 guidelines…"; "Reference list entries should be alphabetized by the last names of the first author"; "please always include **DOIs as full DOI links**" |
| 数据声明 | "This journal follows Springer Nature research data policy… authors **must add a Data Availability Statement**"；另有 "**Statements and Declarations**" 必填（Competing Interests / Funding / Ethics / Consent / Authors' contributions）|
| 其它 tripwire | 图单独文件且字体嵌入；"Acknowledgments … separate section **on the title page**"（与 Elsevier 两刊相反）；LLM 不得列为作者 |
| scope（一行） | "forum for the dissemination of new research results in … **computer vision**… Papers should cover: Mathematical, physical and computational aspects of computer vision … **machine learning techniques; statistical approaches** …" |

### 3.3 Applied Intelligence（Springer）

| 项 | 原文 / 结论 |
|---|---|
| 评审 | guide **未明示**（同上，仅通用双盲句）⇒ 需确认 |
| 长度 | **无页数/字数限制**（0 命中相关限制）⇒ 83 页全稿无需压缩 |
| 摘要 | "abstract of **150 to 250 words**" ⇒ 246 ✓ |
| 关键词 | "**4 to 6** keywords" ⇒ 6 ✓ |
| Highlights | **无要求** |
| Vitae / 照片 | **无要求** ✓ |
| LaTeX | "Manuscripts should be submitted in LaTeX. Please use Springer's LaTeX macro package and **choose the formatting option 'smallcondensed'**."；"include the original source (including all style files and figures) and a PDF version"；"**do not use subfolders**" |
| 参考文献 | "authors … can use the bibliography style file **sn-basic.bst**"（Springer 数字编号式）⇒ 需从作者-年改数字式 |
| 数据声明 | "authors **must add a Data Availability Statement**" + "Statements and Declarations" 必填；欢迎建议/回避审稿人 |
| 其它 tripwire | 图单独文件、字体嵌入；标题页致谢 |
| scope（一行） | "research advances on new and innovative **intelligent systems' methodologies and their applications**… areas … **learning methodologies** … optimization, **neural networks**, mining data and patterns … **modeling** … **pattern recognition**, **computer vision**…" |

### 3.4 Cognitive Computation（Springer）

| 项 | 原文 / 结论 |
|---|---|
| 评审 | guide **未明示**（同上）⇒ 需确认 |
| **长度（硬）** | "**Full-length or Regular papers can be up to 10,000 words in length**"；Short paper ≤3,000 words + 3 图 + 1 表 |
| 摘要 | **结构化**："Please provide a **structured abstract of max. 250 words with the headings**: …"（另处"Structured Abstract (150-250 words)"）⇒ 需重写成分段式摘要 |
| 关键词 | "**minimum 3, maximum 6**" / "**4 to 6** Keywords" ⇒ 6 ✓ |
| Highlights | **无要求** |
| Vitae / 照片 | **无要求** ✓ |
| **格式（硬）** | "**Manuscripts should be typed in Word.**"（另 "Use a normal, plain font (e.g., 10-point Times Roman)"）⇒ **LaTeX 不是目标格式**，需转 .docx |
| 参考文献 | 数字编号式（示例 "Slifka MK, Whitton JL. … J Mol Med 2000; doi:…"）⇒ 需改式 |
| 数据声明 | DAS 必填（Springer Nature 政策）+ Declarations 段（Funding/Competing interests/Ethics/Consent/Data/Material/Code/Authors' contribution）|
| scope（一行） | "publishes … original basic and applied work involving **biologically-inspired computational accounts** of all aspects of natural and artificial **cognitive systems**" |

---

## 4. 资格判定

| 判定 | 刊物 | 理由 |
|---|---|---|
| **排除** | **Information Sciences** | ① **Vitae + 护照型照片**（与 CVIU 同类要求，操作者已因此换刊）；② 页数指导值 40（实验）/45（理论）双倍行距页 + 8/10 个图表 ⇒ 现稿 83 页、主文 9 个图表，需砍 ≥38 页并再移 1 个图表；③ 摘要需压到 ≤200 词 |
| **排除** | **Cognitive Computation** | ① **Word 投稿**（LaTeX 非目标格式）；② **≤10,000 词**（主文已 10,943 词）；③ **结构化摘要**需重写；④ scope 是认知/生物启发系统，与本稿（VLM 对齐理论 + 负结果）明显不合 |
| **可作候选（推荐）** | **Applied Intelligence** | SCIE；**无页数限制**；**无 Vitae**；无 highlights；摘要 150–250 与关键词 4–6 均已满足；scope 含 "learning methodologies / neural networks / modeling / pattern recognition / computer vision" |
| **可作候选（冲刺）** | **IJCV** | SCIE；**无 Vitae**、无 highlights；"Regular articles (up to 25 journal pages)"下 39 页双倍行距主文≈19–20 排版页，**大概率可容**；但选择性远高于另两刊，且需 APA v7 + `[iicol]` 模板 |

---

## 5. 长度差额（我方现稿基线）

| 指标 | 数值 | 来源 |
|---|---|---|
| 总页数（双倍行距单栏） | **83** | `paper合/reframed/main.pdf` |
| 主文 | **39 页**（p1–39）| `paper合/reframed/PAGE_BUDGET.md` + 实测 |
| 主文字数 | **10,943**（附录 5,313；被移出分析 8,005；全篇 24,261）| 实测 |
| 主文图/表 | **4 图 + 5 表 = 9**（附录 14 图 + 9 表 = 23）| 源码清点 |
| 摘要 / 关键词 / highlights | **246 词 / 6 / 5 条（最长 71 字符）** | 实测 |

| 刊 | 规则 | 差额（需要做多少） |
|---|---|---|
| Information Sciences | 40 页（实验）/45 页（理论）+ 8/10 图表 | 若按全稿：**需从 83 页减到 ≤45 页（移出/删除 ≥38 页）**，并从主文移出 1 个图表（9→8，按实验口径）；若只按主文：39 页 ✓ 但图表 9>8 |
| IJCV | 25 journal pages（regular）| **无压缩需求**（39 双倍行距页 ≈ 19–20 排版页）；附录通常在线 |
| Applied Intelligence | 无 | **无压缩需求** |
| Cognitive Computation | ≤10,000 words（full paper）| **主文需删 ≥943 词**（10,943→≤10,000，约 −8.6%），另加 Word 转换 + 结构化摘要重写 |

---

## 6. 推荐

> **推荐目标：Applied Intelligence（Springer，ISSN 0924-669X，SCIE 已于 2026-10-26 用 MJL 核实）。**

**一句话理由**：四刊中唯一同时满足「无页数限制 + 无 Vitae/照片 + 无 highlights + 摘要/关键词现成合规 + scope 明确覆盖 learning methodologies / neural networks / modeling / pattern recognition / computer vision」的 SCIE 刊，且无家族投稿史 ⇒ 对这篇"理论 + 实测边界 + 15 项负结果"的 39 页主文**不需要任何压缩**，只需换模板与参考文献体例。

**排名与理由**

| 排名 | 刊 | 判据 |
|---|---|---|
| **1（推荐）** | **Applied Intelligence** | 零压缩、零 Vitae、摘要/关键词已合规；scope 明确含学习方法、神经网络、建模、模式识别、计算机视觉；选择性中等（可及性优于 IJCV）；改造仅为机械性（`sn-jnl` + `smallcondensed`、`sn-basic` 数字参考文献、源码去子目录、图单独文件） |
| 2（冲刺） | **IJCV** | 同样零压缩、零 Vitae；`[iicol]` + APA v7 的改造量与 AI 相当；但"major technical advances"门槛高，本稿非新视觉方法、且刚刚被 Neurocomputing 桌面拒稿 ⇒ 再被 desk-reject 风险高 |
| 3（排除） | Information Sciences | Vitae+照片（与 CVIU 同类，操作者已因此弃 CVIU）；40/45 页与 8/10 图表需大砍 |
| 4（排除） | Cognitive Computation | Word-only + 10k 词 + 结构化摘要；scope 不合 |

**若操作者不愿/不能提供护照照片** ⇒ Information Sciences 直接出局（与 CVIU 同因）。
**若追求更高影响力且接受 desk-reject 风险** ⇒ 可先投 IJCV，被拒后再转 Applied Intelligence（两者均无家族冲突）。

---

## 7. 未决 / 需确认项（如实记录）

1. **IJCV / Applied Intelligence / Cognitive Computation 的评审类型**：三份 guide **均未明示**单盲/双盲，只有 Springer 通用句（"If the journal that you are submitting to uses double-anonymous peer review …"）⇒ 投稿前需在系统/期刊页确认；若为双盲，则需另做匿名版 + 独立 title page（CVIU 的单盲结论不能直接套用）。
2. **Second source（出版商 A&I 页）**：四刊均未取得，判定仅由 MJL 一手来源支撑（与既有记录一致）。
3. **Applied Intelligence 的 "smallcondensed"**：需要在投稿时选对该 Springer 模板选项，本次未构建模板（按指示不建包）。
4. **IJCV 的 "25 journal pages"** 是**排版页**口径，我按"双倍行距稿页 ≈ 2× 排版页"估算（39→~19–20）；这是估算，不是官方换算规则，投稿前宜再核。
5. 本轮**未**读取四刊的 APC/开放获取费用；若需要可另查（不影响资格判定）。

---

## 8. 留痕

- MJL 截图式捕获：`%TEMP%\mjl_is.txt`、`mjl_ijcv.txt`、`mjl_ai2.txt`、`mjl_cc.txt`（含 `Exact Match Found` 卡片）。
- 指南捕获：`%TEMP%\guide_is.txt`（53,450 字符）、`guide_ijcv.txt`（55,065）、`guide_ai.txt`（53,117）、`guide_cc.txt`（46,202）。
- 范围捕获：`%TEMP%\scope_ijcv.txt`、`scope_ai.txt`、`scope_cc.txt`。
- 抓取脚本：`tools/_p1674_cdp_fetch_guide.mjs`（单页）、`tools/_p1678_cdp_batch_fetch.mjs`（批量）、
  `tools/_p1679_venue_guide_extract.py`（按模式抽取要点）。
- registry 更新：`docs/VENUE_SCI_REGISTRY.md` 新增 §4.6（见该文件）。
