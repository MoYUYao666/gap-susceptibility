# ap3 投稿就绪清单（2026-09-20，Round 1–7 汇总）

对象：`paper_ap3/`（合并稿，`\journal{Neurocomputing}`，elsarticle）。
执行记录与逐条依据：**`docs/AP3_SYNC_PLAN.md`**（§0–§7.5）。本文件是给操作者的一页速览。

---

## 1. 一句话状态

**稿件本身已达可投标准**；**现在不能投**——ap3 含 P1 内容而 P1 仍在 *Pattern Recognition* 审稿中，
按操作者 2026-08-05 自己的判定（`HANDOFF.md:219`）这构成重复投稿。**正确时机 = PR 对 P1 出决定当天。**

## 2. 门禁（最近一次全跑，均通过）

| 项 | 结果 | 复跑命令 |
|---|---|---|
| 编译 | **86 页 / 0 error / 0 undefined / Overfull>20pt = 0** | `cd paper_ap3; pdflatex -interaction=nonstopmode main.tex`（×2，改 bib 时先 `bibtex main`） |
| 全文内容体检 | **A/C/E = 0、B = 0 → PASS**；D=46 条**已全部定性**（见 §4）。<br>（2026-09-23 前 B=1，那条重复句来自暂存文件，随 `@@` 标记消解而消失） | `python tools/ap3_fulltext_lint.py`（`--all` 出完整 D 清单） |
| **P1 同步回归门禁** | **0 problem**：20 项必在（117 / 279 / 469 / ±0.008 / 23.3% / −0.714 / −0.594 / −0.581 / +0.945 / +0.190 / 12 clusters / withdrawn / 1.4× / +0.237 / +0.103 / +0.064 / 50,000-image / 0.8 points / 128-for-five-seed / adapter subspace），14 项必不在（116 runs、116 experiments、278、468、−0.827、−0.807、−0.683、n=81、outperforming CG、by 24%、0.9 points、weight update matrix、batch 128 覆盖式说法、reduces gap more effectively） | `pdftotext -layout paper_ap3/main.pdf paper_ap3/_ap3pdf.txt` → `python tools/_ap3_sync_check.py` |
| 禁词扫描 | 干净（无 TODO/FIXME/`??`/占位标记/内部路径/工作区文件名）；`@@` 标记已**全树归零**（2026-09-24，见 §8） | 见 `docs/AP3_SYNC_PLAN.md` §7.5 的扫描清单 |
| 引文库审计 | 54 条，无真实缺陷；历史 5 条伪造引文确认不存在；3 条承重引文 ID 外部验证为真 | `python tools/_ap3_bib_audit.py` |
| 发布侧漂移 | **[A]=0 [B]=0**（1700+ 跟踪文件，与 `ssh-origin/main` 一致） | `python tools/_publish_live_drift.py` + `tools/_publish_new_files.py` |

## 3. 与 P1 整改的同步（本轮已完成的实质改动）
计数量（116→117、278→279、468→469）· full-FT sd（±0.007→**±0.008**）· **DG/CG 整块换到 n=204**
（−0.714/−0.594/偏相关 −0.581/**DG↔CG +0.945**/CGΔ +0.190 p=0.007/自助 **12 簇** −0.738 [−0.889,−0.613] 0/10000）
并删掉 "substantially outperforming CG" · **撤回 2.6× 噪声主张**（含用它支撑理论的那句）· GSNR **1.5×→1.4×** ·
有效秩改为**嵌入**口径（原写成 ΔW 权重矩阵）· 删掉与"95.96% 可训参数"矛盾的"按构造零视觉扰动" ·
零样本 0.9→**0.8** 点并补 ImageNet 50k 协议 · CG 24%→**23.3%** · **Adapter 换到共同基线**
（d=16/32/64 = +0.237/+0.103/+0.064，且无配置降 gap）· **$g_v=0$ 精确化** · 协议口径（batch 128/64 拆分）·
重建 **fig_corr.png**（n=204，脚本从原始行独立重算后才出图）· MDI 补层次限定 + 引文补真实作者与 DOI ·
**新建 `paper_ap3/cover_letter.tex/.pdf`**（2 页，三段披露）。

## 4. 数值溯源状态

D 类 48 条候选已**逐条定性**，抽到的每一条归入三类之一：

1. **派生量**（均值/sd/差值/倍数）——从档案原始数组重算，已验证：反事实批（−108±27 / +1508±155 / +491±808 / r=32 5/5 NaN / 30.3×）、
   敏感度矩阵（−18.0 / +93.5 / 111.5 / Rebound 233.5、168.5）、样本量表（n=256 行逐格）、β 扫描间隔（1112/5365/625）、
   10-seed 复现批（ΔE(r=5) = −34.7，CI [−66.5,−2.9]，2/10）。
2. **表格单元**——同上逐格核。
3. **文献值**——MDI 10.23/33.10 已对 [arXiv:2508.10552](https://ar5iv.labs.arxiv.org/html/2508.10552) Table 1 核实。

**结论：本地不存在"既非派生、又无来源"的数字。** 方法论：派生量永远不会以字面值存在于 JSON，
必须"按实验名找到定义档案 → 用原始数组重算"；`tools/_ap3_trace_numbers.py` 只能给线索（每个值会撞上 19–586 个档案数字）。

## 5. 决策与执行状态（2026-09-20 指示，2026-09-23/24 更新）

操作者指示（2026-09-20）：**Tier-A 并入**、**其余按"事实正确"的那个选项做**。
操作者指示（2026-09-24）：**ap3 补齐**、**`paper合` 放在备选、目前弃用**。

| # | 事项 | 状态 |
|---|---|---|
| 1 | Tier-A 块 | ✅ **已完成**（`ad80b9f`）：十个块已并入，并逐块对档案复核（A2 门控表、A3 跨批统计、A6 非对称秩、A1 参数化不变性、A5 策略表**全部精确吻合**）；唯一未并入的 A10 已补，并按档案真值（Spearman ρ=0.40、p=0.60）**如实地报为"未能分辨"**而非支持饱和论断；区间 0.93–0.96 更正为 **0.93–1.00**；暂存文件移入 `paper_ap3/_superseded_2026/` → 页数 86→**87** |
| 1b | 占位标记 | ✅ **已消解（2026-09-24）**：全部 37 个 `@@@` 子串（逐 token 计 70 个填位）**只在暂存文件里**，主稿 `sections/*.tex` 与 `main.tex` 从未含占位标记。已按"内容早已并入"的事实替换为 `[A#-NN]` 追溯锚点 + 重写文件头，整棵树 `@@` 归零；脚本 `tools/_ap3_superseded_marker_cleanup.py`（幂等、带计数断言）。见 §8 |
| 2 | DG/CG 措辞 | ✅ **维持保守版**（即事实正确版）；回归门禁确认无越界表述 |
| 3 | `paper合/` | ✅ **已弃用**（操作者 2026-09-24 决定；65 个文件已于 09-22 归档在 `备选/06_归档稿件/paper合/`，根目录无该目录）。**随之关闭**：为它准备的 1,053–1,413 词重合改写**不再需要**（重合在 `paper合` ↔ P1，与 ap3 无关）。⚠️ 若日后重启该稿，`docs/PAPERHE_OVERLAP_RESOLUTION.md` 的 §2 选型与 §3 Adapter 旧口径同步仍是必办项，且 `tools/audit/` 下 5 个脚本的字面路径需先改回 |
| 4 | 篇幅口径 | ✅ **已核（2026-09-24）**：**合规，无需压缩**。Neurocomputing 官方 Guide **无页数上限、无字数上限**；本次引用的条款取自仓库内两份互相独立的官方存档副本（`docs/guides/…Neurocomputing….pdf` 与 `_guide_neurocomputing.txt`，逐字一致；官网当日抓取 HTTP 403）。带数字的条款只有四条，均与总篇幅无关：摘要 ≤250 词、关键词 1–7、Highlights 3–5 条 ≤85 字符、作者简介 ≤100 词。**也没有"双倍行距/行号"要求**——双倍行距是 `elsarticle[review]` 自带，属投稿方选择。详见 **`docs/AP3_LENGTH_CHECK.md`** |
| 4b | **篇幅引出的三处条款缺项** | ✅ **已补齐（2026-09-24）**：核查篇幅时发现同家族其它稿件都有、**只有 ap3 缺**的三节，已按同伴稿口径补入 `main.tex`——① **关键词**（Guide 必填 1–7；原稿 0 命中）② **数据可用性声明**（Guide Option C + "required"）③ **生成式 AI 声明节**（含 `Declaration of competing interests` 与 `Funding`，与 `paper/main_nn.tex:83/92`、`paper_a1/main.tex:588`、`paper_a2/main.tex:819` 一致）。见 §9 |
| 5 | §4 机理解释 | ✅ **已完成**（`da81e23`）：改名 "Mechanism Probes and a Strict Control"，加入严格对照（196,608 可训 / 0.13% / **0/199 视觉张量变化** / CGΔ **−0.0465±0.0027** / R@1 0.6238±0.0049，对照 legacy 145,170,177 参数含视觉的 −0.0635），结论本地化到"适配器位置"，附录引用同步改正 —— **全文已无 "fragility" 一词** |

**仍未完成**：两项与 PR 决定绑定的固定动作（改封面信两处句子、封版前重跑门禁）。<br>
**已关闭**：③ 的重合改写（随 `paper合` 弃用一并关闭）、④ 的篇幅确认与 4b 的三处条款缺项（2026-09-24 完成）。

## 6. 投稿前**必须执行**的步骤

1. **改封面信两处 PR 相关句子**：`paper_ap3/cover_letter.tex` 里带 `% UPDATE ON PR DECISION` 注释的两句，
   按 PR 的实际结果改写（替换文本已写在注释里）；随后重编译并核对 `\mbox{...}` 编号仍完整。
   **该动作的触发条件是 PR 对 P1 出决定，不能提前做**——现在写"被拒"或"在审"都可能是假的。
2. **封版前重跑全部门禁**（§2 的五条命令），特别是 **P1 同步回归门禁**与漂移检查。

## 7. 投稿包（尚未生成）

`tools/build_submission_packages.py` 目前只有 A1/A23/P1 三个 spec；ap3 的包**待篇幅口径（决定 4）确定后再加**，
以免按错误格式打包。加 spec 时需要：manuscript PDF、cover letter、highlights、declaration、LaTeX 源码、figures。

> 2026-09-23：决定 4 已有结论（`docs/AP3_LENGTH_CHECK.md`），但**仍不建议现在生成包**——封面信两处句子
> 尚未按 PR 结果改写，此时打包会固化一个可能为假的表述。封版时连包一起做。

## 8. `@@` 占位标记消解记录（2026-09-24）

**事实澄清**：`@@@` 从来**不在主稿里**。全树扫描显示 37 个 `@@@` 子串**全部**位于
`paper_ap3/_superseded_2026/_TIER_A_PENDING.tex`（一个不被 `\input`、不参与编译的暂存文件）；
`sections/*.tex` 与 `main.tex` 零命中。所以这一项不是"补数字"，而是**消解已被并入内容的暂存残留**。

**执行**：`tools/_ap3_superseded_marker_cleanup.py`（幂等，首轮带计数断言，复跑输出 `nothing left to replace`）

| 项 | 数量 | 处理 |
|---|---|---|
| 形如 `@@NAME@@` / `@@@NAME@@` 的命名填位 | 35 | → `[NAME]` 追溯锚点（保留"段落 → 来源 JSON"对应） |
| 裸 `@@@` 填位 | 35 | → `[A#-NN]`，按块在文件内顺序编号 |
| `@@"` / `"@@` 斜体引号约定 | 2 | → 普通引号 |
| 文件头"待填数"说明 | 1 段 | 重写为"SUPERSEDED + 来源映射"，并写明保留理由 |

**计数口径**（写进脚本头，供第三方复核）：原始文件含 37 个 `@@@` **子串**；由于
`@@A2_IMAGE@@"` 这类 token 尾部会与引号形成 `@@@`、`@@@NAME@@` 前缀又落在命名正则里，
故命名正则匹配 35 个、裸正则匹配 35 个，**逐 token 合计 70 个填位**——两种计数都不遗漏。
（这也解释了先前"37 个 `@@@`"与"70 个填位"两个数字并存不是矛盾。）

**验证**：
- 整棵 `paper_ap3` 树 `@@` 归零（`.tex`/`.bib`/`.md` 全扫；README 中出现的 `@@` 是**记录本次改动**的引文，非残留）；
- 主稿 `sections/*.tex`、`main.tex` 本次**一字未改**（内容早已并入，无需重编译）；
- 十个已并入块的落点按关键词复核（A2 `sec:gradmask`、A5/A7 策略表、A6 非对称秩、A3 层次自助、
  A8 阻尼比、A9 判据、A10 `ρ=0.40`）全部命中；
- `tools/ap3_fulltext_lint.py` 复跑：**A/C/E = 0、B = 0 → PASS**（D 类 46 条仍为提示性，已在 §4 定性）。

**目录 README**：`paper_ap3/_superseded_2026/README.md` 已同步，含 marker 消解表与十一条块的落点表。

## 9. 篇幅核查引出的三处条款缺项 —— 已补齐（2026-09-24）

篇幅核查（`docs/AP3_LENGTH_CHECK.md`）的**真正产出不是页数结论，而是发现 ap3 少了同家族其它稿件都有、
且 Guide 明确要求的三节**。三节均为**追加性**内容，不动任何数字与论证。

| # | 缺项 | 依据 | 处置 |
|---|---|---|---|
| 1 | **关键词** | Guide：`You are required to provide 1 to 7 keywords`（B:679） | 在 `\end{abstract}` 后加 `\begin{keyword}` 块，5 个词：parameter-efficient fine-tuning / gradient structure / rank allocation / vision-language models / cross-modal alignment。措辞与 `paper_a1/main.tex:35`、`paper_a2/main.tex:35` 同风格，并与封面信 §(a) 的定位句一致 |
| 2 | **数据可用性声明** | Guide：`Option C instructions … apply` + `you are required to state the availability of any data at submission`（B:903/913） | 加 `\section*{Data availability}`：所有数据集与模型均为公开；全部结果 JSON、分析脚本与训练配置归档于项目仓库（当前私有，发表后公开，审稿人可索取）；无需外部仓库入库、无受限数据 |
| 3 | **生成式 AI 声明节** | Guide：`must be declared by adding a statement at the end of the manuscript when the paper is first submitted`…`placed in a new section before the references list`（B:432–435） | 加 `\section*{Declaration of generative AI …}`，措辞照抄已投稿口径（`paper/main_nn.tex:92`、`paper_a1/main.tex:588`）。✅ **作者已于 2026-09-24 确认**工具名与范围无误；注释随之改为 `AUTHOR CONFIRMED 2026-09-24`（与 `paper_a1/main.tex:587` 同格式），并**已重编译**（86 页 / 0 error / 0 undefined / Overfull>20pt = 0，注释未进 PDF，lint 与同步回归复跑通过） |
| 附 | **Funding / 竞争利益** | 惯例（Guide 的 declaration 步骤） | 一并补 `\section*{Funding}` 与 `\section*{Declaration of competing interests}`，与 `paper_a2/main.tex` 的对应节一致；封面信 L73 已声明无竞争利益，两处口径相同 |

**编译与门禁（改动后实测）**：

| 项 | 结果 |
|---|---|
| 页数 | **86**（`pdfinfo`；此前脚本口径报 87，差 1 页系计数方式，以 `pdfinfo` 为准） |
| error / undefined refs / cites | **0 / 0 / 0** |
| Overfull > 20pt | **0**（全部 Overfull 仅 2 条，均 < 20pt） |
| 全文体检 `ap3_fulltext_lint.py` | **A/C/E = 0、B = 0 → PASS**（D = 46 条提示性） |
| P1 同步回归门禁 `_ap3_sync_check.py` | **0 problem(s)**（20 项必在、14 项必不在，全 ok） |
| 摘要词数 | **245 词**（源码口径，Guide 上限 250）——**此前漏统计**：脚本口径对 PDF 抽取会漏掉行内公式，**源码口径更保守且仍通过**，故以 245 为准 |

**落地验证**：新章节在编译产物中的位置与顺序已用 `pdftotext` 复核——`Data availability` 在第 81 页末、
`Declaration of competing interests` 与 `Declaration of generative AI …` 在第 82 页、
**`References` 紧随其后**（符合 Guide 的"references 之前的新节"要求）；三段的文本偏移单调递增，
说明顺序为 Data availability → Competing interests → AI declaration → References。
