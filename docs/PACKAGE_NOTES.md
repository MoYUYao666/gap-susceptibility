# Paper A 的 CVIU 投稿包（2026-10-26）

> 任务：按操作者选定的目标与标题，为 Paper A 做一次**全新投稿**（fresh submission）的完整包。
> 状态：包已建成并通过构建/独立编译/哈希自洽校验；**未提交**（按指示）。
> 交付目录：`SUBMISSION/PaperA_CVIU/`（12 文件，含 `SHA256SUMS.txt`）。

---

## 0. 决策（逐字记录）

| 项 | 取值 | 依据 |
|---|---|---|
| 目标刊 | **Computer Vision and Image Understanding**（Elsevier） | 操作者选定 |
| ISSN | **1077-3142**（eISSN 1090-235X） | `docs/VENUE_SCI_REGISTRY.md` §4.4 |
| 收录核实 | **SCIE**（Web of Science Core Collection: Science Citation Index Expanded） | MJL 一手来源，核实人 agent `p3-stats`，**2026-10-26**；MJL URL `https://mjl.clarivate.com/search-results?issn=1077-3142&hide_exact_match_fl=true` |
| 页数限制 | **无硬性页数/字数限制** | guide 全文 0 命中 page/word limit（见 §1） |
| 标题（逐字使用） | *Adaptation-Site Selection for PEFT of Contrastive Dual-Encoders: A Gradient-Flow Characterisation of Cross-Modal Alignment and Its Measured Bounds* | 操作者指定；reframed 树的 T1 已就是该标题 |
| 源稿 | `paper合/reframed/main.tex`（2026-10-26 构建：main text **39 pp**、总 **83 pp**） | 操作者指定；**未使用也未改动** `paper合/main_nc.tex` / `main_springer.tex` |
| 评审格式 | elsarticle `[review,authoryear]`：**单栏、双倍行距**；**不加 `lineno`** | guide **不要求**双倍行距或行号（0 命中）；`[review]` 是现成构建，保留 |

---

## 1. Guide for Authors 要求（逐字摘录）

- **来源 URL**：`https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/publish/guide-for-authors`
- **访问方式**：**可见 Edge**（独立临时 profile，CDP 端口 9224）。headless 客户端被 **403 / CPE00001** 拒绝，
  与 2026-10-26 转投候选核实记录一致（`docs/venue_transfer_candidates_2026-10-26.md` §4）。
- **访问日期**：2026-10-26（Asia/Shanghai）。捕获页面正文 **54,426 字符**。
- **原文留档**：`docs/cviu_guide_quotes_2026-10-26.txt`（逐字英文摘录，含"guide 中不存在的要求"一节）。

| 要求 | guide 原文（摘） | 本包如何满足 |
|---|---|---|
| 评审模式 | "This journal follows a **single anonymized** review process." | 单盲 ⇒ **不需要**匿名版；作者/单位/通讯作者在稿件与 `TitlePage.pdf` 内 |
| 页/字限制 | （无）—— 全文 0 命中 `pages`/`page limit`/`word limit` | 83 页全稿直接提交 |
| 摘要 | "does not exceed **250 words**" | 摘要 **246 词** |
| 关键词 | "**1 to 7** keywords for indexing purposes" | **6** 个 |
| Highlights | "**3 to 5** bullet points, each a maximum of **85 characters**, including spaces"；"a separate **editable file** … with the word \"highlights\" included in the file name" | `Highlights.txt`（5 条，最长 **71** 字符）+ `Highlights.pdf` |
| Graphical abstract | "You are **encouraged** to provide a graphical abstract" | **未提供**（非必需，见 §6） |
| 论文文件格式 | "`.tex` for LaTeX files. **A PDF is not an acceptable source file**"；"single-column … Double-column only permitted for LaTeX" | `LaTeXSource.zip`（可编辑源码）+ `Manuscript.pdf`（仅供阅读/审稿） |
| Title page | title / author names / affiliations（"full name and postal address … including the country name"）/ corresponding author + **email on the title page** | `TitlePage.pdf` 全部含 |
| 参考文献 | "does **not set strict requirements** on reference formatting at submission"；"any style … as long as the style is consistent"；作者-年、字母序、给 DOI | elsarticle-harv（作者-年、字母序）✓ |
| 附录 | "format: **A, B**, etc."；"Eq. **(A.1)**"；"Table **A.1**; Fig. **A.1**" | 稿件附录 A–H（标题内手写字母）✓ |
| CRediT | "Corresponding authors are **required** to acknowledge co-author contributions using CRediT" | 稿件与 `TitlePage.pdf` 均有 CRediT 段 |
| 竞争利益 | "The **declarations tool** should always be completed."；"The resulting **Word document** … Save the document in **.doc/.docx** format. Author signatures are not required." | `DeclarationOfInterest.docx` |
| 经费 | 无经费时的标准句："This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors." | 稿件与 `TitlePage.pdf` **逐字使用该句** |
| 生成式 AI | 新节标题与模板句（见留档 §[Declaration of generative AI use]）；"placed in a new section **before the reference list**" | 稿件 123–127 行，标题与句式与 guide 模板一致 ✓ |
| 研究数据 | "For this journal, **Option C** … apply … Deposit … **Cite and link** … If this is not possible, make a statement" | 稿件 Data availability 段 + 版本 DOI `10.5281/zenodo.23632347` ✓ |
| 致谢 | "Acknowledgments … **directly before the reference list**. Do **not** include acknowledgments on your title page" | 本稿**无致谢节**（无可致谢对象），未违反 |
| Vitae | "short (maximum **100 words**) biography … **passport-type photograph** … editable format" | **无法提供**（见 §6） |
| 图 | "Figures … **must be supplied as separate files** along with the manuscript" | 图在 `LaTeXSource.zip` 内；**未拆成独立 artwork 文件**（见 §6） |
| Cover letter | （guide **未要求**，"cover letter" 0 命中） | 仍按惯例提供 `CoverLetter.pdf` |
| 推荐审稿人 | （guide **未要求**） | **未提供**，符合"guide 不要求就不加" |

---

## 2. 包内文件（12 个，含 `SHA256SUMS.txt`）

| 文件 | 大小 | 页数 | 说明 |
|---|---|---|---|
| `Manuscript.pdf` | 1,478,042 B | **83** | 由 `paper合/reframed/main.tex` 构建（`\journal{Computer Vision and Image Understanding}`） |
| `CoverLetter.pdf` | 130,880 B | **2** | 致 CVIU 编辑；含贡献一句、被拒历史、非一稿多投、DOI |
| `CoverLetter.tex` | 4,378 B | — | 该信源码（Times 兼容） |
| `Highlights.pdf` | 110,706 B | **1** | 5 条 bullets（与 txt 同内容） |
| `Highlights.txt` | 344 B | — | **可编辑**版（guide 要求 editable + 文件名含 highlights） |
| `Highlights.tex` | 1,165 B | — | 渲染源 |
| `TitlePage.pdf` | 112,510 B | **1** | 标题/作者/单位（含邮编国家）/通讯作者+email/声明 |
| `TitlePage.tex` | 3,233 B | — | 该页源码 |
| `DeclarationOfInterest.docx` | 36,971 B | — | Elsevier 竞争利益声明（Word，无签名） |
| `LaTeXSource.zip` | 2,177,728 B | — | **自包含**：`root.tex` + `sections/`(10) + `figures/`(18) + `references.bib` + `root.bbl`，共 36 文件 |
| `README.md` | 2,821 B | — | 包说明 + guide 对应 + 复现命令 |
| `SHA256SUMS.txt` | 899 B | — | **11 条**，覆盖除自身外全部文件 |

**上传文件名全部无下划线**（已逐条核验）：`Manuscript.pdf`、`CoverLetter.pdf`、`Highlights.pdf`、
`Highlights.txt`、`TitlePage.pdf`、`DeclarationOfInterest.docx`、`LaTeXSource.zip`。
`*.tex` 为仓库内部源码（非上传件），同样无下划线。

---

## 3. 字体检查（`pdffonts`，全部 Type 1 嵌入，无 Computer Modern / DejaVu / Arial）

```
CoverLetter.pdf   WDCXOK+TeXGyreTermesX-Regular, UQTMPC+TeXGyreTermesX-Italic,
                  LOUNJQ+TeXGyreTermesX-Bold, GZILWF+txsys
Highlights.pdf    VWTLSU+TeXGyreTermesX-Bold, ITWMAL+TeXGyreTermesX-Italic,
                  PFQPHP+TeXGyreTermes-Regular, ASUXRG+TeXGyreTermesX-Regular
TitlePage.pdf     UBAEYG+TeXGyreTermesX-Bold, JMEBQZ+TeXGyreTermesX-Regular,
                  GLKFAD+TeXGyreTermesX-Italic, EPOWKE+t1xtt
```
- 正文 = **TeX Gyre Termes**（Times 克隆）；数学 = **newtxmath** 组（`txsys`/`NewTXMI`/`txmiaX`）⇒ Times 兼容 ✓
- 三份文档均 **0 errors / 0 overfull**；`CoverLetter.pdf` **2 页**（要求 1–2）、`Highlights.pdf` **1 页**、`TitlePage.pdf` **1 页**
- `Manuscript.pdf` 由 reframed 构建（elsarticle 默认 Times 族），83 页，0 errors / 0 overfull。

---

## 4. 构建命令（可重放）

```bash
# 1) 稿件（首次会写入 \journal 与一处摘要措辞，之后幂等）
python tools/_p1676_cviu_manuscript.py --apply
#    -> paper合/reframed/main.pdf  83 pages, 0 errors

# 2) 整个包（构建三份 PDF、docx、自包含 zip、独立编译验证、README、哈希）
python tools/_p1677_cviu_assemble.py --apply
#    -> CoverLetter.pdf 2pp / Highlights.pdf 1pp / TitlePage.pdf 1pp
#    -> standalone build 83 pages (== manuscript), zip round-trip 83 pages, 0 errors
```

单文件手工构建：`cd SUBMISSION/PaperA_CVIU && pdflatex -interaction=nonstopmode <file>.tex`（×2）。

---

## 5. 独立编译验证（`LaTeXSource.zip`）

| 检查 | 结果 |
|---|---|
| 解压后 `pdflatex root.tex` ×2（无 bibtex，靠随包的 `root.bbl`） | **83 页**，0 errors，0 overfull |
| 与 `Manuscript.pdf` 页数一致 | **83 = 83** ✓ |
| 把**打好的 zip 再解压**后重新编译 | **83 页**，0 errors ✓ |
| zip 内容 | 36 文件：`root.tex`、`sections/*.tex`(10)、`figures/*.pdf`(18)、`references.bib`、`root.bbl` |

> 说明：`root.tex` 由 `main.tex` 派生，只把 `\graphicspath{{../figures/}{../}}` 改成 `{{figures/}}`、
> `\bibliography{../references}` 改成 `{references}`，其余逐字不变——因此审稿人/排版方拿到的是**可直接编译**的树。

---

## 6. 对源稿做的两处改动（`paper合/reframed/main.tex`，该树不在禁改清单内）

1. `\journal{}` → `\journal{Computer Vision and Image Understanding}`。
2. 摘要一处口径修正："the Distribution Gap **predicts** retrieval degradation" → "**is associated with**
   retrieval degradation"。
   - 理由：同一摘要末尾已写明 "we report an **association, not a predictor**"；且 2026-10-25 的 A-1 修正已把
     正文 8 处改成 "associated with"（reframed 树的 sections 已带入），摘要这一处是唯一残留。
   - 影响：摘要 244 → **246** 词，仍 < 250；**无任何数字变化**。

> `paper合/main_nc.tex`、`main_springer.tex`、`SUBMISSION/PaperA_Neurocomputing/`、其它稿件**均未改动**。

---

## 7. 无法提供 / 未提供（诚实清单）

1. **Vitae（作者简介 + 护照型照片）**：guide 要求 ≤100 词 bio + 护照型照片、可编辑格式（Word）。
   仓库里**没有** bio 文本，也**没有**照片 ⇒ 需操作者提供；本包未包含。
2. **独立 artwork 文件**：guide 说图 "must be supplied as separate files"。本包的 18 张图在
   `LaTeXSource.zip` 内（PDF 矢量图，可直接取用），**没有**再拆一份独立图片上传件；若投稿系统要求逐图上传，
   可从 zip 的 `figures/` 目录直接拖入。
3. **Graphical abstract**：guide 是 "encouraged"（鼓励，非必需）⇒ 未提供。若需要，建议用稿内
   `figures/fig1_ode_fits.pdf` 或重绘（需 ≥1328 px 宽、13 cm 可读、TIFF/EPS/PDF/MS Office）。
4. **Abstract 单独文件**：CVIU guide **未要求**（与 Neurocomputing 等刊不同）⇒ 未提供 `Abstract.pdf`。
5. **`\journal{}` 文本不渲染**：elsarticle 的 `[review]` 模式不打印 `\journal` 文本（源码已正确设置）；
   投稿系统里会单独填写刊名，不影响。
6. **未使用 Elsevier 官方 LaTeX 模板**：guide 只是 "We encourage you use our LaTeX template"；本稿用官方
   `elsarticle` 类（`[review,authoryear]`），满足 "editable `.tex`" 的硬要求。
7. **未建议审稿人**：guide 未要求，按"guide 不要求就不加"处理。

---

## 8. 与 2026-10-25 Paper A 评审的关系

reframed 树的 sections **已带入** 10-25 的修正（已核验原文含 `is associated with retrieval performance`、
`DG as a correlate of retrieval`、`come from run directory names` 等）；唯一残留是摘要那处 `predicts`，本次修掉。
A-2 的"高估"措辞在 reframed 树中已是 `higher than`（未复活 `substantially outperforming CG`）。

---

## 9. 状态

- **已建成**：`SUBMISSION/PaperA_CVIU/` 12 文件；页数 **83 / 2 / 1 / 1**；0 errors / 0 overfull；字体 Times 兼容；
  独立 zip 编译 **83 页**；`SHA256SUMS.txt` **11 条自洽**（无缺失、无多余）。
- **未提交**（按指示）。
- **待操作者提供**：作者护照型照片 + ≤100 词 bio（Vitae）；如需要再决定是否补 graphical abstract。
