# A1 目标期刊决定 + 投稿件改造清单

> 记录日期：2026-09-15
> 决定人：作者（Hongrui Wan）。本文件是投稿件改造与合规核对的工作依据，每次核对后在此文件末尾追加结果。

## 一、决定

| 项 | 内容 |
|---|---|
| A1 目标刊 | ~~Image and Vision Computing（Elsevier，中科院 3 区）~~ **已被取代 → Neurocomputing（Elsevier，2 区）**；排除 IVC 的原因见第六节，最终决定见第八节 |
| 投稿方式 | **直接新投（不走 PRL 的 Article Transfer Service）** |
| 前一次决定 | 曾定为 Neurocomputing；2026-09-15 改为 IVC（IVC 与本文"视觉表示 + 评估方法"主题契合度最高，且与 `paper_ap3` 的目标刊不同，无同刊披露约束） |
| 被拒记录 | PRLETTERS-D-26-01941，2026-09-14 Rejected（R1 六条 + R2 五条），逐条应对见 `A1_REVIEWER_RESPONSE_PLAN.md` |
| 参考总纲 | `A1_RESUBMISSION_MASTER_PLAN.md`（§四候选表、§五 ATS 路径——§五本次不采用） |

## 二、已核实的现状（2026-09-15，逐条来自实际文件，非记忆）

1. `paper_a1/main.tex:1` 是 `\documentclass[10pt]{article}` —— **不是 Elsevier 模板**，投 IVC 需切换为 `elsarticle`。
2. `paper_a1/main.tex` / `main_zh.tex` 正文内 **没有** `Pattern Recognition Letters` 字样（grep 0 命中），因此**正文与刊名解耦**，换刊不动正文。
3. `paper_a1/cover_letter.tex` 硬编码 PRL 共 3 处：L22 `Re: Submission to Pattern Recognition Letters`、L27 抬头刊名、L35 `as a research letter in Pattern Recognition Letters`。**"research letter" 是 PRL 文体**，IVC 为全文研究论文，必须改。
4. `paper_a1/declaration.tex`、`highlights.tex` 均为自制 `\documentclass[11pt]{article}`，需按 Elsevier/IVC 要求重做。
5. `paper_a1/` 目录内 PRL 专用投稿件（换刊后不可再用）：`Cover letter.pdf`、`declaration.pdf`、`Authorship Confirmation submit.pdf`、`latex source.zip`、`Guide for authors - Pattern Recognition Letters ...pdf`。

## 三、待作者提供（拿到后逐条比对，不得凭记忆推断）

- [ ] **IVC Guide for Authors**（最新官方版）
- [ ] **IVC 的 LaTeX 模板/样张**（用于确认引用样式是数字制还是 Harvard，以及摘要/关键词/highlights 的具体限制）

## 四、核对项（Guide 到手后按此逐条填"要求 / 现状 / 动作"）

- [ ] 文档类与版式：`elsarticle` 选项（`review`/`preprint`/`final`、`number`/`authoryear`）
- [ ] 摘要字数上限、关键词数量与格式
- [ ] Highlights：条数（Elsevier 惯例 3–5 条）与**单条字符上限**（惯例 ≤85 字符，以 Guide 为准）
- [ ] Declaration of Interest 形式（模板 or 正文声明）
- [ ] CRediT author statement、Data availability statement
- [ ] 图件：分辨率（dpi）、格式（TIFF/EPS/PDF）、单栏/双栏宽度、字号
- [ ] 表格与公式排版要求；附录是否允许
- [ ] 参考文献样式与 DOI 呈现方式
- [ ] 关联稿件披露条款（本稿与 `paper_ap3`、P1 `PR-D-26-10149` 的关系如何声明）
- [ ] 是否要求 cover letter 在投稿系统中单独粘贴、是否需要 suggested reviewers
- [ ] 是否有页数/篇幅限制（A1 现为 28 页 EN / 21 页 ZH）

## 五、投稿顺序（已定）与随之产生的措辞更新

**决定（2026-09-15，作者）：A1 先投 IVC，OE 后投。**

OE 稿中有三处描述 A1 状态的文字，现均写"A1 的修订版正在准备另投他刊"；当 A1 **实际提交之后**、OE 提交**之前**，这三处必须更新为**下表"改为"列给出的文本**（刊名以表中为准，现为 Neurocomputing；A1 的最终目标刊见本文件第八节）。

**状态：已于 2026-09-16 应用**（A1 提交号为 NEUCOM-D-26-20952），原状态为（A1 尚未实际提交，现在写"已投稿"即为不实陈述）。A1 提交完成后立即应用下列改动并重编译 `paper_a2`：

| 位置 | 现在 | 改为 |
|---|---|---|
| `paper_a2/cover_letter.tex:32` | `(decision received; a revised version is in preparation for resubmission elsewhere)` | `(subsequently revised and submitted to \emph{Neurocomputing})` |
| `paper_a2/main.tex:880`（`wan2026a`） | `(decision received); a revised version is in preparation for resubmission elsewhere.` | `The revised manuscript has been submitted to Neurocomputing.` |
| `paper_a2/main_zh.tex:748`（`wan2026a`） | `（已收到决定）；修订版正在准备另投他刊.` | `修订版已投 Neurocomputing.` |

触发条件与顺序（不可颠倒）：

1. A1 稿件（含为 IVC 重做的 cover letter / declaration / highlights）提交完成 → 记下 IVC 的稿件编号；
2. 应用上表三处改动 → `pdflatex`/`xelatex` 重编译 `paper_a2` 四份文档，确认 exit 0/0、0 undefined；
3. 之后才提交 OE。

另：A1 为 IVC 重做的 cover letter 中，需按 IVC 的 Guide 对关联稿件（`paper_ap3`、P1 = PR-D-26-10149）作披露——具体条款见 `SUBMISSION_COMPLIANCE_OE_IVC.md`。

## 六、IVC 被排除（2026-09-15，收到官方 Guide 后）

官方 Guide 原文（`_guide_ivc.txt:928`，已逐字核对）：

> "As per the Journal requirement, the acceptable word count range is **4500-7500 words** and only the below mentioned list is excluded from the word count."

排除项（`:932-942`）仅：参考文献、图与表标题、图内可选文字、表格内容、参考文献之后的章节（含补充材料）。

A1 现稿正文 **≈17{,}679 词**（`paper_a1/main.pdf`，标题→References 之前，已去 caption 行）→ 约为上限的 **2.4 倍**。

**判定：IVC 与本稿结构性不兼容。** A1 的整改方向是**扩写**（8 块整改包 + Related Work 扩写 + E1–E4 四组新实验 + 10 节长文结构），对照 PRL 评审意见而建；砍到 7{,}500 词等于废掉整改策略另写一篇短文。既有的规格物（`paper_a1/graphical_abstract.png` 比例相反、references 无 DOI/卷页、无 CRediT/Data/Funding/GenAI 章节）也随之作废，不再投入。

**连带结论（选刊纪律）：换刊第一步只核"字数/篇幅政策"，通过了再谈模板与格式。** 本文件第三节原列的"待作者提供"清单相应调整为：**只下载 Guide，不下模板**。

## 七、重新选刊：约束与候选

两条硬约束：

1. **必须容纳长文**（现稿 ≈17.7k 词）。
2. `paper_ap3/main.tex:18` 实为 `\journal{Neurocomputing}`。**作者 2026-09-15 确认：`paper_ap3` 尚未投稿，正在等 P1（PR-D-26-10149，Pattern Recognition）的消息。** 因此与 A1 的同刊冲突是**将来可能发生**（仅当 paper_ap3 后续也投 Neurocomputing 时），不是现状；Neurocomputing 因此**重新回到首位候选**——它正是本文件 §一所说、也是 `A1_RESUBMISSION_MASTER_PLAN.md` §四评为"篇幅宽松，容得下 Related Work 扩写"的那本，而 A1 现在最硬的约束恰是篇幅（≈17.7k 词）。
3. 两封 cover letter 目前都**没有**提及 `paper_ap3`。A1 的新 cover letter 需对关联工作作准确披露，可选措辞：与 P1（在 PR 审稿中）的关系必须写；与尚未投稿的 `paper_ap3` 的关系按目标刊 Guide 的条款决定写不写、写到什么程度。

因此候选集中在**长文容忍 + 非 Neurocomputing**：

| 候选 | 出版社 | 分区 | 待办 |
|---|---|---|---|
| The Visual Computer | Springer | 3–4 | 下载 Guide，先核字数/页数政策 |
| Machine Vision and Applications | Springer | 3–4 | 同上 |
| Pattern Analysis and Applications | Springer | 4 | 同上 |
| JVCI | Elsevier | 3–4 | 同上（Elsevier 各刊字数政策互不相同，IVC 就是 4500–7500 的窄区间，JVCI 未知） |

**下一步（作者）**：从上述候选中挑 1–2 本，按既有流程（浏览器打开 ScienceDirect / Springer 的 Guide for Authors 存为 PDF）下载 Guide 放到桌面，我核字数政策后确定目标刊，再开始模板与格式工作。

---

## 八、目标刊最终确定：Neurocomputing（2026-09-15，Guide 已核）

作者下载官方 Guide（`_guide_neurocomputing.txt`，1367 行，pdftotext 抽取 exit 0）。**篇幅闸门通过**：全 Guide 中带数字的篇幅条款只有两条——摘要 **≤250 词**（`:656`）、作者简介 ≤100 词（`:1062`）；**无总字数或页数上限**。这与 IVC 的 "4500-7500 words"（`_guide_ivc.txt:928`）是根本差别，A1 的 ≈17.7k 词在本刊结构上可行。

`paper_ap3` 的同刊问题降级为**将来可能**：作者确认 `paper_ap3` 尚未投稿、在等 P1（PR-D-26-10149）的消息；只有在后续也把 `paper_ap3` 投 Neurocomputing 时才需要同刊披露。

### 已核出的硬要求与处置

| 项 | Guide | A1 现状 | 处置 |
|---|---|---|---|
| 摘要 ≤250 词 | `:656` | 实测 363 词 | 施工中（压缩正文措辞，**不得丢弃任何数字或保留条款**） |
| 关键词 1–7 | `:679` | 5 个 | 合规 |
| Highlights | `:686` encouraged | 5 条、最长 68 字符 | 合规 |
| 竞争利益声明 | `:29/:339/:373` | 无 | 已插入（`AUTHOR: confirm` 标记） |
| 资金来源声明 | `:30/:379` | 无 | 已插入，按"无专项资助"起草，**待作者确认** |
| 生成式 AI 声明 | `:31/:433`（须置于参考文献之前的新章节） | 无 | 已插入，**待作者确认工具名与范围** |
| 致谢位置 | `:1003` 须紧邻参考文献前 | 待核 | 施工中 |
| CRediT | `:1006-1007` 原文为"acknowledge **co-author** contributions" | 单作者 | **不盲加**；多作者场景的要求，单作者稿先按投稿系统实际要求处理 |
| Data statement | ToC `:55-56`、`:889-940` | 无 | 施工中（复用 `main.tex:566` 既有的仓库措辞，不新增"已公开"这类断言） |
| 参考文献格式 | `:1066-1090` 投稿时不严、录用后套用刊方样式；但卷号/文章号/页码须有，能查到 DOI 就带 | 0 个 DOI、多条缺卷页 | 施工中（**逐条经 Crossref 核对标题+作者+年份**，核对不上一律留空） |
| 类文件 | `:606` PDF 不可作源文件、`:609` LaTeX 允许双栏、`:618-623` 鼓励用模板 | `\documentclass[10pt]{article}` | 施工中（切 `elsarticle`） |

### 一个范围框定要求（须体现在 cover letter）

Neurocomputing Type 1 Regular article（`:144-162`）明确不受理 "pure image processing or pure combination of existing algorithms, which are not directly relevant to neural networks or learning systems"。A1 研究对比训练网络的表示几何，**够格**，但封面信与正文框定须把"神经网络 / 表示学习"这一面置于前。

### 仍需作者确认的三件事

1. **资助（已确认）**：作者于 2026-09-16 确认**无任何基金、奖学金或项目资助**，故两篇稿件中的 "This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors." 与实际情况一致。A1 资助声明上方的确认标记已改为 `% AUTHOR CONFIRMED 2026-09-16`。
2. **AI 声明口径（已确认）**：作者于 2026-09-16 确认生成式 AI 声明的**工具名与范围**表述准确。四份主文件（`paper_a1/main.tex:587`、`main_zh.tex:590`、`paper_a2/main.tex:832`、`main_zh.tex:721`）的 `% AUTHOR: confirm` 标记已改为 `% AUTHOR CONFIRMED 2026-09-16`。依据为项目自身记录：`SUBMISSION_CHECKLIST.md:27`（"Claude + DeepSeek"）与旧 `declaration.pdf` 原文。
3. **仓库公开状态（已更正）**：作者 2026-09-16 更正为 **仓库目前仍是 private**。因此正文与 cover letter 中"public repository / 公开仓库"的表述**已全部撤回**，恢复为 "reproducibility archive upon publication"（`paper_a1/main.tex:578`、`main_zh.tex:581`）与 "will be released upon publication"（`cover_letter.tex`）。Elsevier 的数据政策允许在投稿时说明数据暂不可访问的原因，故此表述合规。**若将来把仓库转为 public，才可改回直接可访问的说法。**

## 九、不要在任何投稿件中提及 `paper_ap3`（2026-09-16，操作者指示）

**指示**：投稿件中不得提及 `paper_ap3`。

**事实核对**（`docs/PA_P3_MERGE_PLAN.md:3`，操作者 2026-09-04 决策）：`paper_ap3` 不是一篇独立的
"companion" 稿件，而是 **Paper A（其本身为 P1+P2 合并稿）与 P3 的合并稿**；该行同时明确
"**A1（PRL）与 A2（OE）保持独立不并入**"。触发条件是 **P1 被 PR 拒稿**；操作者 2026-09-16 确认
P1 仍在审 → **合并尚未启动**，`paper_ap3` 是一份待定草稿。

**据此执行的修改**：`paper_a1/cover_letter.tex` 原先用一整段把它描述为"另一位 companion 稿、
尚未投任何刊"——这既是指示禁止的提及，也是**事实描述错误**（它并非独立稿件）。已删除该句，并把
原句中的"the first of these"改为"it"，使段落仅保留对 **P1** 的披露（P1 在 PR 审稿中，且是本文引用
的先前工作，此项披露必须保留）。

**同时修正的不一致**：cover letter 结尾原写 "All data, code, and checkpoints ... will be released upon acceptance"，与正文的 "public repository" 说法矛盾。曾一度改为陈述公开仓库；**在作者更正仓库仍为 private 后，该改动已撤回**，现为 "will be released upon publication"，与正文一致。注意：`.pt` 检查点并不在仓库中，此句是对**将来发布**的承诺而非现状陈述。
upon acceptance"，与正文已改为 "public repository" 的说法矛盾。已改为陈述公开仓库（代码、归档结果
文件与绘图脚本），**并刻意不提 checkpoints 公开**——`.pt` 检查点并未纳入该仓库。

**给后续会话的约束**：A1/A23 的 cover letter、正文与参考文献中均不得出现 `paper_ap3` 的名称或标题。
`docs/` 内的审计记录可以继续引用它（那是内部记录，不随投稿提交）。

## 十、A1 不再提及 PRL 前次投稿（2026-09-16，操作者决定）

**决定**：A1 的 cover letter **不提及**曾被 Pattern Recognition Letters 拒稿一事。已删除原句
"This manuscript was previously submitted to *Pattern Recognition Letters* (manuscript
PRLETTERS-D-26-01941); the decision declining it was received on 14 September 2026."，并核验
`paper_a1/*.tex` 中**不再出现该稿号**。

**依据**：Neurocomputing 的 Guide 只要求两条声明——`:252`（未发表过，预印本等形式除外）与 `:256`
（未在他刊审理中）。**Guide 无"披露前次投稿或被拒"的条款**；唯一涉及稿件流转的是 Elsevier 的
Article Transfer Service（`:1273-1275`），操作者选择不走 ATS。删除后两条强制声明仍然为真，故
不构成不实陈述。留着只会在编辑读稿前立起"上一家拒了"的锚点，而回应 PRL 审稿人的整改工作在本稿中
不可见（`revision_additions.tex` 未被 `\input`），读者看不到"已大幅改进"。

**硬底线**：若投稿系统或编辑**直接询问**是否曾投他刊/是否曾被拒，必须如实回答，不得在直接提问下
作虚假陈述；届时应一并给出整改与新增实验的说明（材料见 `A1_REVIEWER_RESPONSE_PLAN.md`
与 `A1_RESUBMISSION_MASTER_PLAN.md`）。

**预印本**：操作者 2026-09-16 确认**不存在任何预印本**（arXiv 或其他平台）。若将来挂出预印本，
Guide `:252` 明确允许，但应在 cover letter 中如实说明（同时也是对相似度检测命中的预防）。

**连带修改**：A23 中对同伴稿（A1）的披露，原含 "decision received"（读者会推断被拒），已在预写
措辞中一并去掉，改为 "subsequently revised and submitted to Neurocomputing" / "The revised
manuscript has been submitted to Neurocomputing." / 「修订版已投 Neurocomputing.」。注意 A23 保留
"previously submitted to Pattern Recognition Letters" 作为该同伴稿的**识别信息**，这一点仍是事实陈述。

## 十一、A1 已提交（2026-09-16）与 A23 的连带更新（已执行）

**A1 提交号：`NEUCOM-D-26-20952`**（Neurocomputing，提交时间 2026-09-16 04:58，状态 Submitted to Journal）。

第五节预设的触发条件已满足，三处 A23 文字已按预写措辞更新，并**加入该提交号**以便同一出版社的
编辑可直接检索该同伴稿：

- `paper_a2/cover_letter.tex:32` → "(subsequently revised and submitted to \emph{Neurocomputing}, manuscript NEUCOM-D-26-20952)"
- `paper_a2/main.tex:880`（`wan2026a`） → "The revised manuscript has been submitted to Neurocomputing (manuscript NEUCOM-D-26-20952)."
- `paper_a2/main_zh.tex:748`（`wan2026a`） → 「修订版已投 Neurocomputing（稿件编号 NEUCOM-D-26-20952）。」

已核验 `paper_a2/*.tex` 中**不再有**"in preparation for resubmission"/「正在准备另投」这类过期表述。

**由此 A23 可以提交**：其投稿包中的主稿、封面信与参考文献现在对同伴稿的陈述与事实一致。


---

## ⚠️ 2026-10-12 更正（本节状态已过期）

上文关于 A1 的陈述（**Submitted to Journal**，`NEUCOM-D-26-20952`，2026-09-16 提交）**已于 2026-10-10 失效**：

| 字段 | 事实 |
|---|---|
| 决定 | **拒稿**（desk reject，*"after an initial evaluation"*）|
| 理由 | *"falls within the aim and scope of our journal, it did not meet the significance level required"* |
| 审稿意见 | **无**（`Comments to Authors:` 与 `Editor's comments` 均空）|
| 转投 | 有（Elsevier ATS），须在 **`Nov 08 2026 11:59PM`** 前确认 |

**由此连带**：`paper_a2`（A23）里「修订版已投 Neurocomputing（`NEUCOM-D-26-20952`）」这类表述**仍然属实**（那是历史事实），但**不应再暗示该稿仍在审**。
A1 的当前目标刊见 `paper_a1/main.tex` 的 `\journal{}`；投稿件见 `paper_a1/`。
