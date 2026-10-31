# AP3 篇幅口径核查（Neurocomputing）

> 核查日期：**2026-09-24**
> 核查对象：`paper_ap3/main.pdf`（87 页，`\documentclass[review,authoryear]{elsarticle}`，`\journal{Neurocomputing}`）
> 对照对象：`paper_a1/main.pdf`（40 页，`\documentclass[review]{elsarticle}`，稿号 NEUCOM-D-26-20952）
> 核查性质：**只读**。本文件是本次核查唯一新建的文件，未修改任何既有文件。
> 纪律：凡引文均给出副本与行号；凡数字均给出实测命令；未能验证的一律写入第五节，不臆测。
>
> **📌 2026-09-24 收尾标注（后于本报告完成，先读这条）**：本报告的篇幅数据取自**改动前**的 `main.pdf`
> （当时 **87 页**）。核查之后按 §4.4 的建议补齐了三处条款缺项（关键词 / 数据可用性 / 生成式 AI 声明节，
> 另加 `Funding` 与 `Declaration of competing interests`），**重新编译后现为 86 页**（`pdfinfo` 与换页符
> 计数一致），0 error / 0 undefined / Overfull>20pt = 0。
> **§一～§三 的条款结论与 §四 的"合规、无需压缩"不受影响**（"无页数/字数条款"与具体页数无关）；
> 下文出现的"87 页"请按**当次测量**读；**当前权威页数以 `docs/AP3_SUBMISSION_READINESS.md` §2 为准。**
>
> **本文件要关闭的待办**：`docs/AP3_SUBMISSION_READINESS.md` 的「决定 4 · 篇幅口径」（该行已按本报告结清）。

---

## 一、官方条款原文

### 1.1 证据来源与抓取状态（先说清楚"原文从哪来"）

**官方 URL**：<https://www.sciencedirect.com/journal/neurocomputing/publish/guide-for-authors>

**本次联网抓取结果（2026-09-24）**：

| 尝试 | 结果 |
|---|---|
| `https://www.sciencedirect.com/journal/neurocomputing/publish/guide-for-authors` | **HTTP 403**（ScienceDirect 拒绝自动抓取，重试仍 403） |
| `https://www.elsevier.com/journals/neurocomputing/0925-2312/guide-for-authors` | 跨域 302 指向 ScienceDirect，同样 **HTTP 403** |

因此，**本次核查未能从官网实时取回原文**。下列引文全部取自仓库内两份**互相独立**的官方页面存档副本，二者在本次引用的每一条条款上**逐字一致**（行号不同，因排版不同）：

| 代号 | 文件 | 性质 | 时间证据 |
|---|---|---|---|
| **副本 A** | `docs/guides/Guide for authors - Neurocomputing - ISSN 0925-2312 _ ScienceDirect.com by Elsevier.pdf` | 浏览器打印 ScienceDirect 页面所得 PDF，**24 页** | PDF 内部元数据 `Creator: … Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0`、`Producer: Skia/PDF m150`、`CreationDate: Sat Jul 4 14:10:09 2026 +08:00` |
| **副本 B** | `_guide_neurocomputing.txt` | 文本副本，**1367 行**；据 `docs/A1_VENUE_DECISION.md:102` 为作者下载官方 Guide 后经 `pdftotext` 抽取 | 文件 mtime **2026-09-16 12:05:41**（+08:00） |

> 注：`docs/SUBMISSION_COMPLIANCE_NEUROCOMPUTING.md:4` 亦将 `_guide_neurocomputing.txt` 登记为 "Elsevier 'Guide for authors – Neurocomputing'"。

### 1.2 是否有页数上限、字数上限？——**两者都没有**

对两份副本做全文穷举检索（关键词：`page limit`、`pages? maximum`、`word limit`、`word count`、`manuscript length`、`number of pages`、`should not exceed`、`no more than`、`exceed`、`maximum`、`minimum`）：

**结果：Guide 中不存在任何针对稿件总页数或总字数的规定。** 全部带数字的条款只有下列 4 条，且均与稿件总篇幅无关：

**① 摘要 ≤ 250 词**
> "You are required to provide a concise and factual abstract which does not exceed 250 words."
> —— 副本 B `:656`；副本 A `:644`

**② 关键词 1–7 个**
> "You are required to provide 1 to 7 keywords for indexing purposes. Keywords should be written in English. Please try to avoid keywords consisting of multiple words (using "and" or "of")."
> —— 副本 B `:679`；副本 A `:656`

**③ Highlights 3–5 条、每条 ≤ 85 字符（含空格）**
> "You are encouraged to provide article highlights at submission."（`:686`）
> "Highlights should consist of 3 to 5 bullet points, each a maximum of 85 characters, including spaces."
> —— 副本 B `:692`；副本 A `:674`

**④ 作者简介 ≤ 100 词**
> "Please submit a short (maximum 100 words) biography of each author and include a passport-type photograph as a separate figure."
> —— 副本 B `:1062`；副本 A `:1004`

### 1.3 是否有"双倍行距 / 单栏 / 行号"这类审稿排版要求？——**没有**

对两份副本检索 `double.?spac`、`double spaced`、`1.5`、`one and a half`、`line number`、`numbered lines`、`12 ?pt`、`Times New Roman`：
**结果：两份副本均 0 命中。**

Guide 中唯一涉及版式/栏数的条款是：

> "Format Word files in a single-column layout. Double-column formatting is only permitted for LaTeX submissions."
> —— 副本 B `:609`；副本 A `:591`

以及源文件格式条款：

> "Save files in an editable format, using the extension .doc/.docx for Word files and .tex for LaTeX files. A PDF is not an acceptable source file."
> —— 副本 B `:606`（副本 A `:589` 处为同一句换行后的片段 "acceptable source file."）

审稿方式（决定是否需要匿名化）：

> "This journal follows a single anonymized review process."
> —— 副本 B `:210`

**小结：本刊不规定行距，不规定行号，不规定页数，不规定总字数。** 双倍行距只是 `elsarticle[review]` 选项自带的排版结果，是**投稿方的选择**，不是**期刊的要求**。

### 1.4 对"与在审/已发表姊妹稿重叠"的原文表述

Guide 中与重叠/重复发表相关的原文**只有下面这几句**，全部为**声明式条款**（陈述投稿即隐含的承诺）与**转引链接**，没有针对"姊妹稿/伴随稿"的专门条款：

> "When authors submit an article to an Elsevier journal it is implied that:
> · The work described has not been published previously except in the form of a preprint, an abstract, a published lecture, academic thesis or registered report. **See our policy on multiple, redundant or concurrent publication.**
> · **The article is not under consideration for publication elsewhere.**
> · The article's publication is approved by all authors and tacitly or explicitly by the responsible authorities where the work was carried out.
> · If accepted, the article will not be published elsewhere in the same form, in English or in any other language, including electronically, without the written consent of the copyright-holder."
> —— 副本 B `:250–262`；副本 A `:253–261`（分句逐字一致）

> "To verify compliance with our journal publishing policies, we may check your manuscript with our screening tools."
> —— 副本 B `:264`

> "Authors must follow ethical guidelines stated in Elsevier's Publishing Ethics Policy."
> —— 副本 B `:246`（"Ethics in publishing" 节全文仅此一句）

> "We advise you to read our policy on multiple, redundant or concurrent publication."
> —— 副本 B `:458`（"Preprints" 节内）

**关键消极证据**：对两份副本检索 `companion`、`sister`、`overlap` —— **均 0 命中**。
Guide **没有**使用"伴随稿/姊妹稿/重叠"这类措辞，也**没有转录** Elsevier "Multiple, redundant or concurrent publication" 政策的正文，**只是外链**指向该政策。

> **可直接引用的口径**：Neurocomputing Guide 对"与在审/已发表稿重叠"的成文要求 = 上述两条声明（未发表过 + 未在他刊审理中）+ 一句"我们可能用筛查工具核查合规"。**不存在"必须披露姊妹稿"的明文条款**；是否披露属于对 Elsevier 伦理政策（外链）的解读，而非本刊 Guide 的成文要求。

---

## 二、与 IVC 的差别（含 `docs/A1_VENUE_DECISION.md` 复核结论）

### 2.1 IVC 的原文条款

> "As per the Journal requirement, the acceptable word count range is **4500-7500 words** and only the below mentioned list is excluded from the word count.
> 1. The reference section,
> 2. Figures and Table captions
> 3. Selectable text within images
> 4. The content of tables
> 5. Sections placed after the references (including supplementary materials)."
>
> "Currently, there is no specific tool available to directly check the word count."
> —— `_guide_ivc.txt:927–945`（标题为 "Journal specific information: Writing and formatting / Word Count"）

### 2.2 政策差别对照

| 维度 | **Image and Vision Computing (IVC)** | **Neurocomputing** |
|---|---|---|
| 总字数 | **4500–7500 词**，硬性区间，并给出排除清单 | **无任何规定**（Guide 全文无字数字数条款） |
| 总页数 | 无明文页数上限，但字数区间构成事实上限 | **无任何规定** |
| 排除口径 | 明确列出 5 类可移出字数的内容（含"参考文献之后的章节"） | 不适用（无字数口径） |
| 超限的后果 | 结构性不兼容：17.7k 词稿 ≈ 上限的 2.4 倍 | **无条款可违反** |

### 2.3 对 `docs/A1_VENUE_DECISION.md` 的复核结论

| 该文件的记载 | 本次复核 | 结论 |
|---|---|---|
| §六（`:67–77`）：IVC 判定依据为 `_guide_ivc.txt:928` 的 "4500-7500 words"，且 A1 正文 ≈17,679 词 ≈ 上限 2.4 倍 → "IVC 与本稿结构性不兼容" | 引文与行号**逐字核对无误**。本次独立实测 A1 正文（标题→References 前）= **17,763 词**（非页码行口径），与该文件所记 17,679 词相差 **0.5%**（该文件口径为"已去 caption 行"，本次未去 caption） | **判定依据成立，结论正确** |
| §六（`:77`）"换刊第一步只核字数/篇幅政策"这一选刊纪律 | 本案中该纪律被正确执行（先下 Guide、先核篇幅，再谈模板） | **成立** |
| §八（`:102`）"全 Guide 中带数字的篇幅条款**只有两条**——摘要 ≤250 词（`:656`）、作者简介 ≤100 词（`:1062`）；**无总字数或页数上限**" | `:656` 与 `:1062` **逐字核对无误**；"无总字数或页数上限"经本次独立穷举检索**证实**。但"只有两条"严格说应为**"篇幅类两条"**——Guide 中带数字的**格式**条款实际共 **4** 条（另加 关键词 1–7（`:679`）、Highlights 3–5 条 ≤85 字符（`:692`）） | **结论不受影响；措辞可更精确（非错误）** |
| §十一（`:180`）：A1 提交号 NEUCOM-D-26-20952，2026-09-16 04:58，状态 **Submitted to Journal** | 与仓库其他记录（`docs/A23_JOE_INQUIRY.md:23`、`docs/A23_VENUE_DECISION.md:69`）一致 | **记录一致**；但"已进入外审"未能核实，见 §五 |

**一句话**：IVC 用字数**封顶**，Neurocomputing **不设篇幅闸门**——这正是当时从 IVC 改投 Neurocomputing 的核心事实依据，复核后依然成立。

---

## 三、实测篇幅对比表（ap3 vs paper_a1）

### 3.1 测量命令（可直接复跑）

```powershell
# 1) 页数
pdfinfo "paper_ap3/main.pdf"
pdfinfo "paper_a1/main.pdf"

# 2) 文本抽取（临时文件放在系统临时目录，未写入仓库）
pdftotext -layout -enc UTF-8 "paper_ap3/main.pdf" "$env:TEMP\ap3_u8.txt"
pdftotext -layout -enc UTF-8 "paper_a1/main.pdf" "$env:TEMP\a1_u8.txt"

# 3) 版面几何（版心宽度、字符数）
pdftotext -bbox -enc UTF-8 "paper_ap3/main.pdf" "$env:TEMP\ap3_bbox.html"
pdftotext -bbox -enc UTF-8 "paper_a1/main.pdf" "$env:TEMP\a1_bbox.html"
```

分词脚本（PowerShell 管道送入 Python，逐行统计；`ref` = 首个独立成行的 `References`，`appA` = 首个匹配 `^Appendix\s+A\.` 的行）：

```python
import re, io
def count(path):
    lines = io.open(path, encoding="utf-8", errors="replace").read().split("\n")
    ref = appA = None
    for i, L in enumerate(lines):
        s = L.strip()
        if ref is None and s == "References": ref = i
        if appA is None and re.match(r"^Appendix\s+A\.", s): appA = i
    numre = re.compile(r"^[\s\dIVXivx]+$")
    def wc(seg):
        n = nn = 0
        for L in seg:
            s = L.strip()
            if not s: continue
            is_num = bool(numre.match(s))
            for tok in s.split():
                if re.search(r"[0-9A-Za-z\u0370-\u03ff\u4e00-\u9fff]", tok):
                    n += 1
                    if not is_num: nn += 1
        return n, nn
    print(path, "FULL", wc(lines), "BODY", wc(lines[:ref]), "PRE-APPENDIX", wc(lines[:appA]), "APPENDIX", wc(lines[appA:ref]), "REFS", wc(lines[ref:]))
```

> **词数口径声明**：空白分词，**包含**页码行、页眉与图表内容；同时给出"非页码行"口径（剔除纯数字/罗马数字行）作对照。**未**套用 IVC 的排除清单，因此本表词数**不可**与 IVC 的官方计数口径直接比较。

### 3.2 对比表

| 指标 | **paper_ap3/main.pdf** | **paper_a1/main.pdf** | ap3 / a1 |
|---|---|---|---|
| **总页数**（`pdfinfo`） | **87** | **40** | **2.18×** |
| **全文词数** | **24,861** | **18,889** | **1.32×** |
| **正文词数**（标题 → References 之前） | **23,814** | **17,763** | **1.34×** |
| ├ 其中附录 A–F | 2,947 | 0（无附录） | — |
| ├ **正文（不含附录）** | **20,867** | **17,763** | **1.17×** |
| └ 参考文献词数 | 1,047 | 1,126 | 0.93× |
| 全文字符数（`-bbox`） | 139,471 | 105,589 | 1.32× |
| 每页字符数 | 1,603.1 | 2,639.7 | 0.61× |
| 正文版心宽度（正文页中位数，`-bbox`） | **343.7 pt** | **470.6 pt** | 0.73× |
| 摘要词数（渲染 PDF，`Abstract`→`Keywords`/通讯作者脚注） | **217** | **246** | — |
| 页面分区 | 正文 1–69 / 附录 A–F 70–82 / 参考文献 83–87 | 正文 1–36 / 声明+参考文献 37–40 | — |
| 版式 | `elsarticle[review,authoryear]`，**未覆盖版心** | `elsarticle[review]`，`geometry` 覆盖为 letterpaper + margin=1in | — |

对照口径（`where` 边界由 `-layout` 文本行号定位，页面归属由 `-bbox` 定位）：
`References` 在 ap3 = 文本第 2954 行 / PDF 第 **83** 页；在 a1 = 文本第 1640 行 / PDF 第 **37** 页。
`Appendix A. Full Axiom Derivation of Γ` 起于 ap3 第 **70** 页（`-layout` 文本第 2482 行）。

### 3.3 由对比得出的判断

1. **按内容量（词/字符）计，ap3 只是 a1 的约 1.3 倍**——词数比 1.32×、正文词数比 1.34×、字符数比 1.32×，三个口径互相一致。
2. **按页数计，ap3 是 a1 的 2.18 倍**——但这个倍数**被排版放大**了：两者的版心宽度不同（343.7 pt vs 470.6 pt）。a1 的 `main.tex` 把 `elsarticle[review]` 的默认版心覆盖成了 1in/letter（`docs/SUBMISSION_COMPLIANCE_NEUROCOMPUTING.md:23` 与 `:45` 记录了这一主动偏离），每页装 2,639.7 字符；ap3 用默认版心，每页只装 1,603.1 字符（为 a1 的 61%）。
3. **归一化估算**：若把 ap3 渲染到 a1 的字符密度，约 **139,471 ÷ 2,639.7 ≈ 52.8 页**。即在同一版心口径下，ap3 ≈ a1 的 **1.32 倍**。
   > ⚠️ 这是**按字符密度线性缩放的估算值**，不是重新编译的实测值，见 §五。
4. **结论**：ap3 相对同刊已投姊妹稿 a1 的量级是 **1.3 倍（内容量口径）**，不是 2 倍量级；页数上的 2.18 倍主要来自版心宽度差异。

---

## 四、结论与建议

### 4.1 结论：**合规，无需压缩**；投稿时**保持当前 `elsarticle[review]` 双倍行距排版**

**依据分层（条款 / 惯例，二者严格区分）**：

| 判断 | 依据性质 | 具体证据 |
|---|---|---|
| 86 页（改动前口径为 87 页）**不违反 Neurocomputing 的任何成文篇幅条款** | **条款**（消极证据：穷举检索证实无该条款） | §1.2：两份官方副本中不存在针对总页数或总字数的规定 |
| 无需为"页数上限"压缩到某个具体页数 | **条款**（同上） | 不存在上限 → 不存在需要压缩到的目标值 |
| 摘要 217 词合规 | **条款** | §1.2 ①：≤250 词 |
| "86 页（改动前口径为 87 页）在同刊是可接受的" | **惯例 + 推断**，**不是条款** | Guide **没有**"允许任意长度"的正面表述；"无上限"是从"无该条款"推出的消极证据。同刊前例：a1 = 40 页已提交（稿号 NEUCOM-D-26-20952） |
| 建议不要为页数改版心 | **惯例/观感**，**不是条款** | 见 4.3 |

### 4.2 直接建议

**按当前 `elsarticle[review,authoryear]` 双倍行距排版直接投稿，不做任何篇幅压缩。** 三条理由：

1. **无条款可违反**——Guide 没有页数或字数上限，"压缩到 X 页"没有对应目标。
2. **内容量只比同刊前例大 1.3 倍**（词/字符口径一致），并非页数显示的 2.2 倍。
3. **压缩会付出真实代价而无条款收益**：ap3 现为 86 页（改动前口径为 87 页） / 0 error / 0 undefined / Overfull(>20pt) = 0（`docs/AP3_SUBMISSION_READINESS.md:17`），正文含附录 A–F 的理论推导与实验细节。为迎合一个不存在的上限删减内容，会破坏当前已通过的门禁。

### 4.3 可选项（**惯例/观感，不是条款**，需重跑门禁后才可采用）

若纯粹希望送审 PDF 更薄（审稿人体感，非合规）：

- 做法：对 ap3 施加与 a1 相同的 `geometry`（letterpaper, margin=1in），把版心从 343.7 pt 放宽到 ~470.6 pt。
- 预期：按字符密度**估算**约 **53 页**（§3.3 第 3 点）。
- **前置条件**：ap3 数学公式与表格密集（含 6 张宽表类内容），放宽版心可能改变断行与浮动体位置，**必须重编译确认 `Overfull>20pt = 0` 仍然成立**，否则得不偿失。
- 注意：`docs/SUBMISSION_COMPLIANCE_NEUROCOMPUTING.md:45` 已把 a1 的版心覆盖登记为"唯一主动偏离模板默认的排版决定"，属于需要**明示**的偏离。若对 ap3 同样处理，应在同类合规记录中一并登记。

### 4.4 附带发现：**真正需要修的不是页数**（本次核查顺带核实，属确凿条款缺项）

以下三项与篇幅无关，但**是成文条款的直接缺项**，会触发编辑部退回，优先级高于页数：

1. **无关键词**。Guide `:679` 要求 "You are required to provide 1 to 7 keywords"。`paper_ap3/main.tex` 的 frontmatter（第 23–40 行）中**没有** `keyword` 环境（全文检索 `keyword` **0 命中**）；渲染 PDF 第 1–3 页检索 `Keywords` **0 命中**。→ **需补关键词**。
2. **无生成式 AI 声明节**。Guide `:432–435`："The use of AI tools in the manuscript preparation process **must be declared** by adding a statement at the end of the manuscript when the paper is first submitted… should be placed in **a new section before the references list**"，并给出官方节标题 "Declaration of generative AI and AI-assisted technologies in the manuscript preparation process"。`paper_ap3/main.pdf` 全文检索 `Declaration of` / `generative ai` / `AI-assisted` **均 0 命中**。→ **需补声明节**（a1 已有同类节，可对齐口径）。
3. **无数据可用性声明**。Guide `:903` "For this journal, **Option C** instructions from our research data guidelines apply"；`:913` "you are **required** to state the availability of any data at submission"。ap3 全文检索 `Data availability` **0 命中**（正文含 `github` 相关表述的检索亦 0 命中）。→ **需补数据声明**。

> 本节三项**仅报告事实**，不涉及任何文件修改（本次核查为只读）。

---

## 五、不确定项

以下各项**本次未能验证**，不代表已确认或已否定：

1. **官方页面未能联网复核**。2026-09-24 对 ScienceDirect 与 Elsevier 的 Guide for Authors 页面抓取均为 HTTP 403。本报告全部引文来自两份本地存档副本（副本 A = 2026-07-04 浏览器打印；副本 B ≈ 2026-09-16 下载）。**无法排除 2026-09-16 至 2026-09-24 之间官网改版**。若要消除此风险，需人工在浏览器中打开官方 URL 复核 §1.2–§1.4 的条款是否仍然一致。
2. **Elsevier "Multiple, redundant or concurrent publication" 政策正文未取得**。该政策是 Guide `:253`/`:458` 外链所指，但：(a) Guide 本身未转录其正文；(b) 政策页 <https://www.elsevier.com/about/policies-and-standards/publishing-ethics> 两次抓取（HTTP 200）均在 "Duties of the Publisher" 处被截断，未能取到 "Duties of Authors" 下该节文字。因此**"与在审/已发表姊妹稿重叠"的完整官方表述未能验证**；本报告只能确证 Neurocomputing Guide 自身的两条声明条款（§1.4）与该外链的存在。
3. **编辑部是否存在未成文的篇幅偏好（desk 惯例）**——无任何公开文本支持或反对，**未能验证**。本报告"无需压缩"的结论只针对**成文条款**。
4. **a1 是否已进入外审未能核实**。任务背景称 a1 "已被 Neurocomputing 受理进入审稿"，但仓库记录（`docs/A1_VENUE_DECISION.md:180`）所载状态为 **"Submitted to Journal"**（提交时间 2026-09-16 04:58）。本报告按仓库记录表述，未采用"已进入外审"这一未经核实的前提。该差异**不影响**本次篇幅结论（对照价值在于"同刊同版式的已提交稿件"，而非其审稿阶段）。
5. **~52.8 页是估算值，不是实测值**。其算法为「ap3 全文字符数 ÷ a1 的每页字符数」线性缩放，**未**重新编译 ap3。实际重排版后的页数会受公式断行、浮动体位置、图表尺寸影响，可能偏离估算。
6. **词数口径不可与 IVC 官方口径直接比较**。本报告用 `pdftotext` + 空白分词，**包含**页码、页眉、图表内容；IVC 的官方口径是「生成 PDF → 拷入 Word → 读字数」并排除 5 类内容（`_guide_ivc.txt:932–942`）。两者数值不同源。本报告同时给出的"非页码行"口径与主口径相差 <0.5%（ap3: 24,770 vs 24,861；a1: 18,825 vs 18,889），可作内部一致性参考。
7. **未逐行复核 Guide 全部 1367 行**。仅对**本报告引用到的**条款及其所在小节做了逐字核对。未引用的部分（如补充材料、视频、开放获取等）未审。
8. **a1 的正文词数与既有记录相差 0.5%**（本次 17,763 vs `docs/A1_VENUE_DECISION.md:73` 的 17,679）。差异来源为该记录额外剔除了 caption 行，本次未剔除。**该差异不改变任何结论**（两者都约为 IVC 上限的 2.4 倍）。

---

## 附：本次核查未修改任何既有文件

- 新建文件：`docs/AP3_LENGTH_CHECK.md`（本文件）
- 临时文件（系统临时目录，**未写入仓库**）：`$env:TEMP\ap3_u8.txt`、`a1_u8.txt`、`ap3_bbox.html`、`a1_bbox.html`、`guide_pdf.txt` 及若干 `.py` 计数脚本
- 只读访问：`paper_ap3/`、`paper_a1/`、`docs/`、`_guide_neurocomputing.txt`、`_guide_ivc.txt`
