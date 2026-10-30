# Neurocomputing 投稿合规核对（A1）

- 稿件：`paper_a1/main.tex`（英文主稿，英文版为投稿与引用准据）+ `paper_a1/main_zh.tex`（中文参考译本）
- 指南：`_guide_neurocomputing.txt`（Elsevier "Guide for authors – Neurocomputing"）
- 规则：表中"官方要求"一律给出指南行号；**指南未规定**的条目直接写"Guide 未规定"，不拿通用 Elsevier 惯例冒充本刊要求。
- 核对者只拥有 `main.tex` / `main_zh.tex` / `related_work.tex` / 本文件；`declaration.tex`、`highlights.tex`、`cover_letter.tex`、`related_work_bibitems.tex`、`figures/` 由其他协作者所有，表中只记录其状态、不代改。

| 核对项 | 官方要求 (guide line) | 当前状态 (file:line) | 需改动作 |
|---|---|---|---|
| 摘要 | :656 "a concise and factual abstract which does not exceed 250 words"；:670 自足；:672 避免文献引用 | `paper_a1/main.tex:31-33`（原 363 词已压缩） | **已完成**：texcount 247 词 / PDF 渲染文本 245 词 / `.tex` 原始 token 244 词，三种口径均 ≤250；被点名不可删的数字与声明全部保留（CG 0.82→0.01、59.3%→32.0%、CGΔ +0.033（共享评测子集）与 +0.114（旧训练期记录器）及"报区间不取大值"、34 条件/三家族/17 检查点＝14 LoRA+3 重建全量微调、τ=Kendall 排序保持、r=1.000 明示为自洽性检查而非独立验证、59.3%→78.6% 与必要非充分（τ=0.615 收缩 vs 0.761 高斯噪声））。中文摘要已同步镜像（`main_zh.tex:36-38`） |
| 关键词 | :679 需 1–7 个、英文；:680 尽量避免含 "and/of" 的多词关键词 | `main.tex:35-37`（elsarticle `keyword` 环境，5 个：modality gap / zero-shot classification / order preservation / cross-modal alignment / fine-tuning） | 无需改动：5 个在 1–7 区间且无 "and/of" 组合；原 `\noindent\textbf{Keywords:}` 手工行已改为模板 `keyword` 环境，使关键词落在题名页规定位置 |
| Highlights | :686 鼓励提供；:690 需作为单独可编辑文件提交；:692 3–5 条、每条 ≤85 字符（含空格） | `paper_a1/highlights.tex`（他人所有，未改） | 已合规：5 条，长度 68 / 61 / 65 / 54 / 50 字符（实测），均在 85 字符内；提交时按 :690 作为单独文件上传 |
| 竞争利益声明 | :339 全体作者须披露可能影响工作的经济/个人关系；:361 "The declarations tool should always be completed"；:373 无冲突者选 "I have nothing to declare"；:375-376 工具生成的 Word 须为 .doc/.docx 且无需签名 | 正文节 `main.tex:580-581`（本次新增）；`paper_a1/declaration.tex`（他人所有） | 正文节已完成；**仍需**在投稿系统内完成 declarations tool 并上传其 .doc/.docx —— 该工具是强制步骤（:361），正文声明不能替代它 |
| 资助 | :379-382 必须披露资助来源并说明资助方是否参与研究设计/数据/写作/投稿决策；:395-397 无资助时推荐句式 "This research did not receive any specific grant…" | `main.tex:583-584`（上方保留 `% AUTHOR: confirm before submission …` 注释） | 已加入 :395-397 推荐句式；作者需确认"确无资助"属实，若有则按 :384-389 标准格式补写 |
| 生成式 AI 声明 | :400-401 投稿时必须声明；:432-433 首次投稿时以"新节"形式置于**参考文献列表之前**；:435 官方节标题；:436-437 官方句式模板 | `main.tex:587-589`（节标题与指南 :435 逐字一致）；中文侧 `main_zh.tex:591-592` | 已完成：工具名与范围（Claude (Anthropic) 与 DeepSeek V4；起草修订稿件文字、准备实验代码与图表）与 companion 稿件一致，并保留 `% AUTHOR:` 待确认注释；声明为正文内新节，位于 `\begin{thebibliography}`（`main.tex:592`）之前，符合 :433 |
| CRediT 作者贡献 | :1006-1007 "Corresponding authors are required to acknowledge **co-author** contributions using CRediT roles"（:1010-1044 角色表；:1047 "Not all CRediT roles will apply"） | 本文为**单作者**稿件（`main.tex:22`），`main.tex` 内未加 CRediT 节 | **刻意不改**：该条以"合著者贡献"为对象，单作者不存在需致谢的合著者贡献；正文加 CRediT 块无依据。若投稿系统要求，按 sole author（通讯作者本人）填报即可 |
| 数据声明 | :913 "you are required to state the availability of any data at submission" → **必须**（非"鼓励"）；:903 本刊适用研究数据指南 Option C；:906-911 需（1）存入合适仓库、（2）在文中引用并链接、（3）若不可行则说明原因；:915-917 在**投稿过程中**声明，随文章在 ScienceDirect 发布 | `main.tex:578` 结论末已链接 `github.com/MoYUYao666/gap-susceptibility`（"reproducibility archive upon publication"） | 待办（系统步骤，非稿件改动）：投稿时按 :913 填写数据声明，沿用现有措辞，建议原文："Code and data: github.com/MoYUYao666/gap-susceptibility (reproducibility archive upon publication)." **不得**改写为"仓库已公开"——正文明确其为发表后公开的复现档案 |
| 致谢位置 | :999-1004 致谢须为独立一节，且"directly before the reference list"；:1003-1004 不得置于题名页、题名脚注或其他位置 | `main.tex` 无致谢节（全文检索 0 命中）；本次新增三节位于 `main.tex:580-589`，参考文献起于 `main.tex:592` | 无需移动（现无致谢）。若后续添加，必须插在 `main.tex:589` 与 `:592` 之间 |
| 文章类型与范围 | :144-162 Types 1–7；Type 1 常规论文须"directly relevant to Neural Networks and/or Learning Systems"；:156-158（并在 :200-201 重复）明确**不接受**纯动力系统、纯控制工程、纯模糊逻辑、纯图像处理、纯现有算法组合 | 稿件主题为对比视觉–语言模型（CLIP 家族）的表征几何与 PEFT 微调健康诊断（`main.tex:41-83`） | 无需改动：按 Type 1 Regular article 投稿，主题属神经网络/学习系统，不落入 :156-158/:200-201 排除项；投稿系统 Article Type 选 "Regular article/Research paper" |
| 参考文献格式与 DOI | :1066-1079 正文引用与文献表须一一对应、须为真实存在来源、**尽量**给出 DOI；:1089-1090 "does not set strict requirements on reference formatting at submission"；:1098-1099 期刊样式在录用后（校样阶段）统一施加；:1102-1104 正文用方括号编号；:1106 按出现顺序编号；:1082-1086 未刊成果需以 "unpublished results" 标注；:1215-1219 预印本须标明服务器并给出预印本 DOI | `main.tex:592-607`（`thebibliography` 起 :592，13 条 `\bibitem` 在 :593-605，`\input{related_work_bibitems}` :606，共 56 条；他人文件未改） | 已完成可核验补全：`main.tex:593` liang2022 补 pp.17612–17625 / DOI 10.52202/068431-1280；`:600` yamaguchi2025 补 pp.4256–4266 / DOI 10.1109/CVPR52734.2025.00402；`:601` sofer2025 补 pp.196–200 / DOI 10.21437/Interspeech.2025-1664；`:604` wortsman2022 补 pp.7949–7961 / DOI 10.1109/CVPR52688.2022.00780；`:595` yi2025 补预印本 DOI 10.48550/arXiv.2510.03268（DataCite 渠道核验，见下）。其余 8 条无 Crossref 命中，逐字节保持不变（未发明任何 DOI/卷期/页码） |
| 图表与美术稿 | :750 图须在正文中被引用；:756 每图单独文件；:762-765 每图须有标题＋说明；:768-769 按格式表提交；:780-782 照片 TIFF/JPG/PNG，最低 300 dpi（最小宽度：单栏 1063 px、整页 2244 px）；:786-788 位图线稿 TIFF/JPG/PNG，最低 1000 dpi（单栏 3543 px、整页 7480 px） | 4 张图均在正文中被引用（`main.tex:109/120/311/359`，`\ref` 实测均 ≥1 次）；`figures/`（他人所有）：fig1_lambda.png 1560×1080 px、声明 300 dpi；fig2_tau_top1.png 1560×1140；fig3_trajectory.png 1500×1320；fig4_spectrum.png 1380×1020 | 按**照片行**（:780-782）全部合格：像素宽 1380–1560 ≥1063，声明 300 dpi，且在本文版心下的**实际**输出分辨率 435–511 dpi（fig1 435 / fig2 435 / fig3 511 / fig4 441）。按**位图线稿行**（:786-788，≥3543 px）则均不合格——若编辑按线稿行审核会被要求重传；建议改出矢量 PDF/EPS（:776 矢量行）或按 ≥3543 px 重导（`figures/` 非本人所有，需其所有者处理） |
| 补充材料 | :842-851 鼓励使用；:848 必须在正文中引用每个补充文件；:851 与稿件同时提交；:854 每个文件需简明说明性标题；:859-860 不作排版、原样上线 | 主稿未引用任何补充文件（`main.tex` 无 "supplement" 引用） | 无需改动。若后续新增补充文件，必须同时在正文引用并给出描述性标题（:848/:854） |
| LaTeX / 模板规则 | :604-609 须提供可编辑源文件（.tex）；"A PDF is not an acceptable source file"；Word 须单栏，"Double-column formatting is only permitted for LaTeX submissions"；:618-620 鼓励使用 Elsevier LaTeX 模板；:622-623 提供 LaTeX 投稿说明与模板 | `main.tex:1` `\documentclass[review]{elsarticle}`（由 `article` 切换）；`main.tex:2` 保留 `\usepackage[letterpaper,margin=1in]{geometry}` | 已完成切换并说明取舍：选 **review**（单栏、1.5 倍行距、Elsevier 审稿版式）而非 3p/5p 双栏——正文 6 张宽表按单栏 469.755pt 版心排定，3p 单列宽仅 384pt 会导致表格越界；同时保留原 1in/letter 版心，否则 elsarticle review 自带 345pt 版心会产生 9 处 overfull（最大 112.8pt），实测恢复版心后为 0 处 |
| 题名页 | :631-652 需题名；作者全名；单位含**完整邮政地址与国家**；明确通讯作者并提供其邮箱（会随文章发表） | `main.tex:20-29`：`\title`（:20）、`\author[1]{Hongrui Wan\corref{cor1}}`（:22）、`\affiliation`（:23-27，University of Southampton, University Road, Southampton, SO17 1BJ, UK）、`\cortext`（:28）、`\ead`（:29） | **已完成**：改用 elsarticle `frontmatter` 后补齐了原 `article` 版本缺失的单位邮政地址/国家与通讯作者标注；渲染结果见 `main.pdf` 第 1 页 |
| 评审方式 | :209-212 本刊为 single anonymized review（编辑初筛 + 不少于两位审稿人） | `main.tex:22-29` 保留作者姓名、单位、邮箱 | 符合单盲要求，无需匿名化；无需改动 |
| 预印本引用 | :1215-1219 预印本须清晰标注（含"preprint"字样或服务器名）并给出预印本 DOI | `main.tex:595` yi2025 标为 `arXiv:2510.03268, 2025`，本次补 `DOI: 10.48550/arXiv.2510.03268` | 已完成：DOI 经 arXiv 摘要页（标题/作者/年份均匹配）与 doi.org handle（解析至 arxiv.org/abs/2510.03268）双重核验；因 arXiv DOI 由 DataCite 注册，Crossref 查不到，故列为 Crossref 之外的核验渠道 |
| 图形摘要 | **Guide 未规定**（全文检索 "graphical abstract" 0 命中） | `figures/graphical_abstract.png`（531×1328、100 dpi，未在正文引用） | 无需改动，也无需修复：本刊未要求图形摘要，不必为它做 300 dpi 处理，也不必加入正文或投稿包 |
| 投稿信 / 推荐审稿人 / 主编 | **Guide 未规定**（"cover letter"、"Editor-in-Chief"、"suggested reviewer" 均 0 命中） | `paper_a1/cover_letter.tex`（他人所有，存在） | 无需改动：指南对投稿信、推荐审稿人、主编姓名均无要求，该文件不构成合规项 |
| 提交清单（通用） | :1242-1244 需指定通讯作者并提供完整联系方式；:1246-1247 所有文件（含图、表、脚注、补充材料）齐全；:1249 拼写语法检查；:1252 正文引用与文献表互相覆盖；:1255 版权许可 | 对应状态见"通讯作者"、"图表"、"参考文献"各行；引用/被引一致性由编译验证 → 未定义引用与未定义文献均为 **0** | 提交前按 :1238-1259 清单逐项自查；拼写/语法检查（:1249）由作者完成（本次未代跑） |

## 本次核验的实测数据（编译与字数）

- `main.tex`：`pdflatex` ×2 → **40 页**，LaTeX 错误 **0**，未定义引用/文献 **0/0**，overfull hbox **0**，underfull hbox **2**（`main.log` 定位：108–109 行为图片段落、604–605 行为参考文献段落；均为松散行，无越界）。
- `main_zh.tex`：`xelatex` ×2 → **22 页**，错误 **0**，未定义引用/文献 **0/0**，overfull **0**，underfull **2**。
- 摘要字数（三种口径）：`texcount -1 -sum` **247**；编译后 PDF 首页 `pdftotext` 渲染文本 **245**；`main.tex` 原文 token **244**。压缩前为 363 词（原始 token 363 / LaTeX 剥离 362）。
- 切类前基线（`article` 10pt + geometry 1in/letter，仅作对照，未保留在仓库）：28 页、overfull **0**、underfull **0**。

## Desk-reject risk（按优先级）

1. **竞争利益声明工具未完成**（:361、:375-376）：正文声明已加，但系统内 declarations tool 与 .doc/.docx 上传是独立强制步骤，缺失会在编辑部初审被退回。
2. **数据声明未在投稿系统填写**（:913 为"required"）：这是必填项而非可选项；且档案仓库尚未公开（正文写 "reproducibility archive upon publication"），声明若写成"已公开"即与正文自相矛盾，属事实性错误。
3. **图件位图线稿分辨率**（:786-788）：4 张 PNG 单栏最小宽度 3543 px 全部不达标，若编辑按"位图线稿"行审核会被要求重传；改出矢量 PDF/EPS 可一次性规避。
4. **`\bibitem{wan2026protect}` 印出的投稿状态**（`main.tex:605`："under review, Pattern Recognition, 2026"）：`docs/CITATION_INTEGRITY_AUDIT.md:195` 记载工作区记录自相矛盾（一处"仍在审"，另一处"曾投稿并被拒"）。这是印在参考文献里的**事实性陈述**且可被编辑核实，投稿前必须由作者确认；若实际状态变化，应改为 `unpublished results` 之类中性表述（:1082-1084）。
5. **参考文献编号顺序**（:1106 按出现顺序编号）：现有 `\bibitem` 顺序为固定编号（本次任务明确要求"保持现有编号"故未重排），首次引用顺序并不严格递增（例如 levi2025 [5] 首次出现在 Related Work，晚于 Introduction 中的 imod [6]）。指南在投稿阶段明确"does not set strict requirements"（:1089-1090），录用后由出版社统一编号，风险低，但需知晓。
6. **版心与模板默认不一致**：为让 6 张宽表不越界，`main.tex:2` 保留 1in/letter 版心（469.755pt），与 elsarticle `review` 自带的 345pt 版心不同。若编辑要求严格套用模板版式，需将相关表格改为 `\small`/`\resizebox` 或接受 9 处 overfull（最大 112.8pt）。这是本次唯一主动偏离模板默认的排版决定，已在此明示。
7. **预印本 DOI 渠道**：`main.tex:595` 的 arXiv DOI 由 DataCite 注册，无法用 Crossref 复核；已在条目内按 :1217 给出，并在上表记录核验方式（arXiv 摘要页 + doi.org handle 双证据）。投稿系统若对 DOI 格式有校验，需确认其接受 `10.48550/...` 前缀。
