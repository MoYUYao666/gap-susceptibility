# A23 目标期刊记录（Ocean Engineering 桌面拒稿与转投）

> 记录日期：2026-09-16
> 相关：`HANDOFF.md`（投稿状态）、`docs/A1_VENUE_DECISION.md`（A1 的选刊与整改记录）
> **✅ 最终结果（2026-09-21 系统时间）：已投 IEEE Journal of Oceanic Engineering，稿号 `26-0663`，状态 Received。**
> 完整提交记录与合规处理见 `docs/A23_JOE_MIGRATION.md` 第八节。本文件保留选刊决策过程。

## 一、事实：桌面拒稿，未经同行评审

| 项 | 内容 |
|---|---|
| 稿号 | **`OE-D-26-11643`** |
| 期刊 | Ocean Engineering（Elsevier） |
| 提交 | 2026-09-16 |
| 决定 | **Rejected（桌面，scope 原因，未送外审）**，决定信日期 **2026-09-18** |
| 签发人 | Yan Wei，Executive Editor |
| 编辑原话 | "the content of your paper is **outside the scope** of Ocean Engineering … While your results are of potential interest, the topic of your manuscript falls outside of the scope of this journal." |
| 原件 | `SUBMISSION/A23_JOE/supplementary/A23_OE-D-26-11643_decision_letter.pdf`（操作者 2026-09-24 提供） |
| 文本证据 | `outputs/_oe_decision.txt`（`pdftotext -layout` 提取） |

**关键点：这不是审稿意见。** 信里"view your reviewer feedback"链接指向的只是上述 scope 说明；**没有任何审稿人意见需要应对**，因此也不存在"逐条回应"的工作量。稿件的科学内容未被质疑。

## 二、拒稿原因分析（我方判断失误）

我在选 OE 时**核查过范围条款，但把风险定位错了**：

- 我盯住的是 Guide `:178-182` 的军用/两用排除句，并把 `:158-159` 的 "civilian applications of underwater imaging" 当作入范围依据；据此还建议在投稿系统的分类里勾选 "Marine Sensing, Imaging and Perception" → "Civilian applications of underwater imaging"。编辑没有提军用内容，说明那方面我们处理得没问题。
- 真正的问题更基本：**Ocean Engineering 是一本海洋/海事"工程"期刊**，范围是平台、结构、水动力、海上作业、仪器与系统等工程贡献；本文本质是**对比式表示诊断的方法与评测研究**（gap surgery、Kendall 序保持、PEFT 对照、界），海洋与声呐数据只是应用场景。Guide 里 "theoretical papers without any application to ocean engineering" 一句已经暗示了这一点。
- **教训（写进流程）**：选刊第一步必须核对**范围条款（scope）而不只是主题词匹配**——主题词命中（"underwater imaging"）不等于该刊接受这类**贡献类型**。这与 A1 那次"IVC 4500–7500 词硬上限"是同一类错误的不同面：**先读 Guide 的范围与篇幅条款，再谈契合度**。

## 三、损失评估：无实质损失

- **稿件完好**：`paper_a2/main.tex`（65 页）+ 中文镜像（46 页）编译 0 错误、0/0 undefined；投稿前 PDF 门禁 `tools/audit_submission_pdfs.py` → **PROBLEMS 0**；`SUBMISSION/A23_OceanEngineering/`（22 文件）可整体复用。（第三轮整改后英文稿为 **66 页**，见第七节。）
- **时间**：提交当日即被桌面拒稿，几乎无损失。
- **不需要改动的**：正文、图、结果、声明、highlights、abstract 文件（都与期刊无关）。

## 四、转投前必须改动的清单（换刊后逐项执行）

| 位置 | 内容 | 说明 |
|---|---|---|
| `paper_a2/main.tex:13` | `\journal{Ocean Engineering}` | 换为新刊名 |
| `paper_a2/main_zh.tex:30` | 文件头注明英文稿投 OE | 同步 |
| `paper_a2/cover_letter.tex` | 刊名、"Fit with the journal" 段、以及那句 "matching the journal's explicit in-scope clause for civilian applications…" | 该句是**为 OE 的范围条款量身写的**，换刊后必须重写或删除 |
| 摘要长度 | OE 限 200 词（Guide `:644`），现约 195 词 | 新刊上限若更严需再压；若更宽可不动 |
| 篇幅 | OE 的 "preferably ≤40 双倍行距页"（`:189`）是 OE 专属 | 新刊政策未知，须重新核 |
| 投稿系统分类 | 已选 OE 的类目 | 换刊后重选 |
| 附录的军事/两用措辞软化 | 已做（只删了**未获得**数据集的武器类别枚举，未改任何实测标签） | **保留**：无害且更稳妥 |

**不需要重做的**：正文论证、数字、引用、图表、声明章节、`declaration_of_interest.docx`、`highlights.*`、`abstract.*`。

## 五、候选期刊（须先核 Guide，不得凭主题词匹配下结论）

按"贡献类型匹配"而非"主题词匹配"排序：

| 候选 | 出版社 | 为什么可能合适 | 待核 |
|---|---|---|---|
| **Engineering Applications of Artificial Intelligence** | Elsevier | 定位就是"AI 技术在工程中的应用"，接受以应用为载体的方法/评测研究 | 范围条款、字数/篇幅政策 |
| **IEEE Journal of Oceanic Engineering** | IEEE | 水声、成像与海洋信号处理方向会发这类 ML 分类/识别研究；保住海洋读者群 | 是否需要更强的工程贡献叙事；篇幅政策 |
| **Neurocomputing** | Elsevier | 方法/评测类稿件的天然归宿 | ⚠️ **A1 已投该刊**（`NEUCOM-D-26-20952`）→ 同刊双稿需披露，且两篇方法同源，编辑可能追问重叠 |
| **IEEE Access** | IEEE | 范围宽、见效快、几乎无 scope 拒稿风险 | APC（约 USD 1,950）、单位认可度 |
| **Journal of Marine Science and Engineering (JMSE)** | MDPI | 海洋科学+工程，接受 ML 应用 | APC、审稿周期的口碑 |
| ~~Image and Vision Computing~~ | Elsevier | 主题契合 | ❌ 4500–7500 词硬上限（`_guide_ivc.txt:928`），本文远超，需大砍 |
| ~~Applied Ocean Research~~ | Elsevier | 海洋工程 | ⚠️ 与 OE 同族，scope 拒稿风险很可能相同 |

**建议下一步**：从中挑 1–2 本，按既有流程（浏览器打开该刊 Guide for Authors 存为 PDF）下载，**先核范围与篇幅条款**，再决定；其后按第四节清单改稿并重编译。

## 六、与 A1 的关系不受影响

A1 已投 Neurocomputing（`NEUCOM-D-26-20952`，Submitted to Journal），其封面信只披露 P1；A23 正文与封面信披露 A1（含稿号）。**本次拒稿不改变任何已提交内容**，无需通知 Neurocomputing。

## 七、稿件整改记录（2026-09-16，第三轮；EN/ZH 同步）

三处改动，属"陈旧表述纠正 + 补强外部引用"，**不涉及任何数字、结论或图表**。由 `tools/_a23_round3_fix.py` 执行，每处替换均断言唯一命中（全部 PASS），改动后另用 `pdftotext` 复核**落版 PDF 文本**（教训：替换计数通过 ≠ 正文正确，必须读编译产物）。

| # | 位置 | 原（陈旧） | 现 | 理由 |
|---|---|---|---|---|
| 1 | `main.tex:85`；ZH `:84` | "in our network environment **only NKSID was retrievable**, and we document the failed attempts…" | "…bulk transfer from our environment failed repeatedly in 2026-08; the reachable channels were **eventually acquired** through retries, a VPN and API/CDN routes, and the full attempt log—including the sets that remain unobtainable—is documented in Appendix~\ref{app:data}." | 该句写于**第一次采集失败时**；到 2026-08-31 / 09-03 已取得水槽集、riku-1825、UATD。原句与正文"四台声学仪器"直接矛盾，属必须纠正的陈旧表述。 |
| 2 | `main.tex:811`；ZH `:699` | "We therefore report single-dataset acoustic evidence … and mark cross-dataset replication as an explicit future item." | "**At the time of this first pass** we therefore reported single-dataset acoustic evidence …; **the retries documented below supersede that state**." | 附录按时间顺序书写（首轮 → 08-30/31 重试日志 → 08-31 补录 → 09-03 补录）。首轮段的结论必须以"当时"框定，否则读者会以为全篇仍是单数据集声学证据。 |
| 3 | `main.tex:85` 与 `:811`（ZH 对应处）+ 新增参考文献条目 | 未引用 | `\bibitem[Aubard et al.(2025)]{aubard2025}`：Aubard, Madureira, Teixeira & Pinto, *Sonar-Based Deep Learning in Underwater Robotics: Overview, Robustness, and Challenges*, IEEE Journal of Oceanic Engineering, 2025, DOI `10.1109/JOE.2025.3531933` | 用**同行评议的权威综述**支撑"带标注声呐数据仍是长期约束"这一数据可得性主张——原先只有我方自己的尝试记录作证。两处引用：§2 数据集段、附录~\ref{app:data} 首句。 |

编译：EN **66 页**（+1 页，来自新增参考文献条目与三句正文）/ ZH 46 页，0 error、0 undefined、无 undefined citation。

## 八、声学数据集补采结论（2026-09-16 复核）：不需要、也不存在可用的第二套多类声呐集

转投材料定稿前的最后一次"还能不能补一套声学数据"复核，结论是**不再补**——理由是数据现实，不是工作量：

| 候选 | 复核方式与结果 | 判断 |
|---|---|---|
| UATD（Xie et al. 2022） | 本地已完整（`data/second_sonar/UATD`：9{,}200 图 + 9{,}200 XML）；正文已用，且其三个域微调变体的**失败**已如实报告 | ✅ 已使用（Gemini 1200ik） |
| marine-debris 水槽集 | 解包逐类核对：11 类（Wall 1056 / Tire 615 / Bottle 468 / Drink-carton 347 / Chain 320 / Can 292 / Valve 240 / Propeller 197 / Hook 171 / Shampoo-bottle 111 / Standing-bottle 65；background 类按正文排除） | ✅ 已使用（ARIS 3000） |
| riku-1825 | 11 类（ARIS3k 全分辨率 + sonar7 水雷集） | ✅ 已使用（ARIS3k） |
| **SCTD v2** | WinRAR 解包后**仅 2 类**（`small_target` 1028、`WH` 767） | ❌ 非多类集，不可用 |
| OpenSonarDatasets 公开目录 | 逐项核对：公开侧扫集的标注普遍只有 **1–3 类** | 印证多类侧扫集在公开数据中确实不存在 |

**因此**：A23 已覆盖**四台声学仪器**（Oculus M750d / ARIS 3000 / ARIS3k 全分辨率 / Gemini 1200ik）；论文披露的唯一缺口（多类侧扫集）是**真实的数据现实**，而非采集能力或投入不足。该缺口现有 JOE 2025 综述 + 我方逐条尝试日志双重支撑，并已在正文与附录如实声明。

- 已核实的冗余副本：桌面 `21331143.zip`（4.8 GB）与本地已解包的 UATD 重复，**可删**（清理后 D 盘余量约 97.9 GB）。
- **决定：不再为补第二套声学数据投入时间。**

## 九、最终候选排序与当前动作（2026-09-16）

按"贡献类型匹配 → 分区/影响力 → 审稿速度 → 适配度"重排。**OE 拒稿后新增硬性步骤：先核范围条款，再谈主题词契合。**
（各刊 IF/分区的当年数值以 JCR 与期刊官网为准；本记录不固化未经二次复核的数值。）

| 序 | 期刊 | 速度证据 | 适配判断 | 费用 |
|---|---|---|---|---|
| 1 | **Neurocomputing** | SciRev N=12：首轮约 2.5 个月，全程约 3.9 个月 | 方法/评测稿的天然归宿；IF 6.500（Southampton 协议核过）；⚠️ **A1 已投该刊** → 同刊双稿需披露 A1 稿号 | £0（转换协议覆盖 APC £2,130） |
| 2 | **IEEE Journal of Ocean Engineering** | 速度数据薄（SciRev N=1） | 范围条款明确接受"理论/分析性贡献"与"已有技术的创新应用"；编委含侧扫声呐+ML、声呐处理+ML、海洋声学深度学习、水下 CV/DL 多位 AE | 传统投稿 0 APC；OA US$2,800 |
| 3 | **IEEE Access** | 约 4 周首轮 | 范围宽、几乎无 scope 拒稿风险 | APC ≈ US$2,160 |
| 4 | **ESWA**（降级） | ⚠️ 用户在投稿件 5 周仍停在 "With Editor" | 适配尚可，流程体验差 | 待核（Elsevier 协议通常覆盖，需按刊名核） |

已排除：**IVC**（4500–7500 词硬上限）、**Applied Ocean Research**（与 OE 同族，scope 风险同源）、**EAAI**（用户已有在投积压）。

**当前动作**：向 IEEE JOE 主编发 presubmission inquiry（`joe-editor@ieeeoes.org`，抄送 `journal@ieeeoes.org`；主编 Karl von Ellenrieder），主动说明贡献类型与四台声学仪器的复现范围，**先确认方法/评测类稿件是否在范围内再决定是否正式投稿**——这一步就是为了不再重演 OE 式桌面拒稿。

⚠️ JOE 残余风险：其范围措辞偏"电气/电子工程"传统，编委文化可能期待更强的**工程贡献**叙事。因此 inquiry 中要点明"我们在真实声呐数据上做了跨仪器复现并给出可部署的逐图算子"，而不只讲诊断方法。若 JOE 回复不利，按序落到 Neurocomputing 或 IEEE Access。

## 十、换刊后仍需执行的改动（承第四节）

稿件的三处整改（第七节）与期刊无关，已完成；**换刊确定后**再执行第四节清单中与刊名相关的项：`main.tex:13` 的 `\journal{}`、`main_zh.tex:30` 的文件头说明、`cover_letter.tex` 的刊名 / "Fit with the journal" 段 / 删除 OE 专属的 in-scope 句，并按新刊 Guide 复核摘要长度与篇幅政策。
