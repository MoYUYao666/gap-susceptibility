# Commentary 终审：内容、归因与语气（2026-10-25，只读）

> 审计者：`p3-stats`。对象：`paper_review_prl/main_prl.pdf`（**7 页**，PRL `PRLETTERS-D-26-02402`，在审）。
> 方法：全文通读（7 页，无遗漏）+ 逐条核对"对其他文献的量化陈述"与引用 + 检查 `main_prl.tex` 与
> `publish_clean/`（v2.5 快照）的一致性 + 语气/体裁核对（PRL 的 Commentary = subject review，见 `SPEC.md` §5）。
> **未改任何稿件**（只写本笔记）。

**先说一个范围问题**：这是一篇 **subject review（批判性综述）**，`SPEC.md` §5 明确"Commentary 可为 lecture notes /
subject reviews / reports / debates"，因此**没有一个"被评论的目标论文"**；"straw man" 风险针对的是它对
*被引综述*（[43]/[44]/[18]/[34]）与 *被引实验*（POPE、MMBench、DoRA 等）的转述，而不是某一篇 target article。
下面按此口径审计。

---

## 0. 总体结论

结构清楚（two decisions → six instances → 12-item checklist → conclusions），**语气在 PRL commentary 可接受范围**
（第一人称论证、有明确 scope 声明，无攻击性措辞）。主要问题：**Data availability 声称的"analysis archive"并不存在**、
**一处引用把 MME 挂在 MMBench 的量化结论上**、**对 DoRA 的否定性归因没有 pin-cite（且自述"每个 instance 都可核实"）**、
以及**Table 1 对三篇综述的定位没有页码/章节定位**。修掉这四点即可。

---

## (a) 必须修（事实/合规风险）

### C1（最高优先）Data availability 声称一个不存在的 "analysis archive"
- `paper_review_prl/main_prl.tex:217-218`：
  "**Data availability.** No new data were generated for this article. The analysis archive behind the six instances is
  available under version DOI `10.5281/zenodo.23632347`."
- 核查：
  - `outputs/analysis/` 下**没有任何 commentary 归档**（无 `commentary*.json`；六个 instance 的数值是**引用文献**
    的数值，不是本项目生成的结果）。
  - 仓库内唯一相关是 `docs/commentary_compression_and_table.md`，但它是"压缩方案 + 表"的工作草稿（标题自述
    "DRAFTS ONLY"），且 live 版本 sha256 前缀 `169c4812…` 与 `publish_clean/`（v2.5 快照）里的同名文件
    `53f078c2…` **不同** ⇒ 即便把它当 archive，当前稿依赖的版本也不在 v2.5 里。
  - `publish_clean` 的 v2.5 tag 时间 **11:13**，而 `main_prl.tex` mtime **12:08** ⇒ 当前稿晚于该快照。
- **修法**：改为 "No new data were generated; all quantitative values in §3 are quoted from the cited sources."（删掉
  archive/DOI 句）；若确实要留 archive，需先真实建立并登记（当前不存在）。

### C2 引用错配：MMBench 的"约 10 分下降"挂上了 MME [10]
- `main_prl.tex:136`："… moving a model from the vanilla to the circular protocol reduces the score of OpenFlamingo v2
  from 36.7\% to 2.6\%, and reduces scores for proprietary models by roughly ten points \cite{liu2025mmbench,fu2025mme}."
- `:234` `\bibitem{fu2025mme}` = **MME: A Comprehensive Evaluation Benchmark**（另一套 benchmark）；
  MME 不是 MMBench circular-protocol 的来源。`\cite{liu2025mmbench}` 单独即可；若要保留 [10]，需指出 MME 中
  支持"~10 points"的具体位置（否则这是"把第三方量化结论挂错源"）。
- **修法**：删 `fu2025mme`，或改为 `\cite{liu2025mmbench}`。

### C3 "每个 instance 都可核实"与 DoRA 的否定性归因没有 pin-cite
- `main_prl.tex:76`：`… each instance is verifiable against the cited source.`
- 但 `:134` 对 DoRA 的否定性断言最脆弱："A later paper reporting full fine-tuning, LoRA and its own method on the same base
  model gives a single "POPE" column with the values **85.9, 86.4 and 87.2**, and **does not state which subset is used**
  \cite{liu2024dora}."
  - 否定性事实（"没有说明 subset"）与具体数字都需要**表号/页码**才能核实；目前只有 `\bibitem{liu2024dora}`。
  - 这是全文最可能被原作者反驳的一句：如果 DoRA 在表注/附录里其实标了 subset，这一 instance 就塌了。
- **修法**：给出 `\cite{liu2024dora}` 的表号（如 "Table 5"）并核对；若找不到明确证据，把该句降级为
  "the table does not name the subset in its header"（限定范围）或删除该 instance，只保留 LLaVA-1.5 三子集的正例。

（同理 `:134` 的 LLaVA-1.5 三值 87.3/86.1/84.2 应给出表号；这是全文唯一的另一个"别人论文数字"。）

---

## (b) 逻辑缺口 / 审稿人会攻击的点

### B1 Table 1 对三篇综述的"定位"缺 locator
- `main_prl.tex:87-89`（Table 1，`:82` caption "Positioning against existing reviews"）：
  `[44] language models / method families, with assessment / reported results, per family`；
  `[18] multimodal LLMs / efficiency techniques / qualitative`；
  `[34] multimodal LLMs / the token budget axis / reported results`。
- 这是对三篇综述的**分类断言**；若审稿人正是这些综述的作者，会要求"你说我的轴是 X，依据是哪章"。建议每个 cell
  补 section/table 级 locator，或把表改成 "as summarised in their abstracts/introductions"。

### B2 conclusions 的一句超出六个 instance 的证据范围
- `main_prl.tex:213`："Another adapter variant under an unstated protocol **adds little**. A study that fixes the base
  model and protocol and varies only the division of the budget … **our survey found none** for multimodal models."
- 六个 instance 证明的是"报告缺失导致不可比"，**不是**"新的 adapter 变体价值很小"；且 "our survey found none"
  未给检索范围（数据库/年份/关键词），作为文献综述性断言应限定为 "in the works cited here / in the literature we surveyed"。
- **修法**：软化第一句（"adds little to comparability"），并把 "our survey found none" 限定范围。

### B3 abstract/highlights 的 POPE 表述不精确
- `main_prl.tex:58`（highlight）："Reported POPE values differ without naming the benchmark subset"；
  `:52`（abstract）："reported numbers for the same base model that differ because an evaluation subset is unstated"。
- 但 §3.1 的事实是：**LLaVA-1.5 明确标了 subset**，是"后一篇（DoRA）没标"；highlight 的泛指会被读成"两篇都没标"。
- **修法**：highlight 改为 "Reported POPE values are incomparable when one paper does not name the subset"；
  abstract 保持（"for the same base model"已有限定）或加 "in one of the two papers"。

### B4 six instances 是 illustrative，但 abstract 的"checkable"需要 C3 的 locator 支撑
- `:52` "instances checkable against their sources"；`:166` §3.7 已诚实写 "checkable illustrations rather than a systematic
  sample"。逻辑上自洽，但"C3 没有 locator"使 checkable 不成立 ⇒ 与 C3 一起修即可。

---

## (c) 润色 / 一致性

1. `:217-218` 两句话可合并（"No new data were generated; all quantitative values are quoted from the cited sources."），
   避免"no new data … archive available"的自相矛盾观感。
2. `:52` abstract 说 "moves a model's score from 36.7% to 2.6%"，未点名 OpenFlamingo/model；§3.2 点名了，
   摘要可加 "OpenFlamingo v2" 提高可核性（加 1–2 词，7 页有空间）。
3. `:82` Table 1 caption 与 `:90` this-review 行一致 ✅；`:94` 的 "The last row is the contribution" 与 Table 1 呼应 ✅。
4. 语气：全文无针对个人的攻击、无贬损性形容词；`:213` 是唯一偏强的一句（见 B2）。
5. 引用格式：`:223` `thebibliography` 49 条；[2]/[29] 标 "to appear" — 按 PRL 政策需确认 latest 版本可用性（非本审计可核定）。
6. `:166-167` 的 "Two limits are explicit" 与 §3.7 的三条 practitioner 结论位置清楚，逻辑顺序无问题。

---

## 附：核对清单（lead 关注的四个问题）

| 问题 | 结论 |
|---|---|
| 是否准确归因"被评论的论文"（无 straw man）？ | 本文是 subject review，**没有单一 target paper**；对综述/实验的转述总体忠实，但 **DoRA 的否定性断言缺 pin-cite（C3）**、Table 1 三行缺 locator（B1）——这两处最可能被原作者反驳 |
| 每个关于他人论文的量化陈述是否有来源？ | LLaVA-1.5 三值有 cite 但缺表号；DoRA 三值有 cite 缺表号且含否定断言；MMBench 36.7→2.6 有 cite ✅；"~10 points" **挂错到 MME（C2）**；"several points [40,48]" 是定性转述，可接受但最好注明是综述性归纳 |
| 语气是否在 PRL commentary 规范内？ | 总体可以：第一人称论证、§3.7 明确"illustrations not systematic sample"；唯一偏强的是 conclusions 的 "adds little" / "our survey found none"（B2） |
| v2.5 DOI 语句是否与依赖一致？ | **不一致（C1）**：声称的 "analysis archive behind the six instances" 不存在；当前稿（12:08）也晚于 v2.5 tag（11:13）。应改为"无新数据、数值全部引自被引文献" |

## 最强 / 最弱（简要）
- **最强**：① "两次决策"框架清楚且可操作，Table 2 把 siting/division 分离得很干净；
  ② 12 项 checklist 每项都对应一个具体不可比失败，可落地；③ scope 诚实（§3.7 明确非系统抽样）。
- **最弱**：① 六个 instance 都是文献转述且缺 locator/页码，最关键的 DoRA 否定句最脆；
  ② data availability 的 archive/DOI 声明不实；③ conclusions 的"adapter 变体价值小"超出证据。

---

# Applied fixes（2026-10-25 第二轮，操作者"全改"）

> 编辑范围：`paper_review_prl/MANUSCRIPT.md`（唯一源文件）→ `tools/_build_prl_tex.py` 重新生成
> `main_prl.tex` + `main_prl.pdf`；同步 `paper_review_prl/highlights.tex` 与 `_refs_used.json`。
> **未提交**。重建后 **main_prl.pdf = 7 页**（0 errors / 0 undefined / 0 overfull / abstract 224 词 /
> 5 highlights / 12 checklist items / 48 refs）。行号以改动后的 `MANUSCRIPT.md` 为准。

## (a) 必修项

1. **Data availability 重写（C1）** — `MANUSCRIPT.md:377`（原 377-379 合并）：删除 "The analysis archive
   behind the six instances is available under version DOI ..."（archive 不存在，六个 instance 是引用文献数值），
   改为 "**No new data were generated for this article; all quantitative values in Section 3 are taken from the
   cited sources.**"（无 DOI、无 archive 声明）。
2. **MMBench "~10 points" 引用修正（C2）** — `MANUSCRIPT.md:209`：`[liu2025mmbench; fu2025mme]` →
   `[liu2025mmbench]`；`_refs_used.json` 移除不再被引用的 `fu2025mme`（49→48 entries），
   使 builder 的 `cite keys == bibliography entries` 检查通过。
3. **外部文献 pin-cites（C3）** — `MANUSCRIPT.md:197-201`：
   - LLaVA-1.5 三值 87.3/86.1/84.2：改为 "as its results table reports them [liu2024llava15; li2023pope]
     (**§4.2** of the former)"（§4.2 = Empirical Evaluation → Results，arXiv HTML 目录核实）；
   - DoRA 三值 85.9/86.4/87.2 与 "without naming the subset there"：改为 "[liu2024dora]
     (**§5.3 and Appendix A.5**)"（两节标题 arXiv HTML 目录核实；附录正文因截断/验证码未取得，
     **"未标 subset" 未能二次核验**，见"未解"）。

## (b)/(c)

4. **Table 1 定位说明** — `MANUSCRIPT.md:76`：caption 追加 "Each row summarises the scope that review states
   in its abstract and introduction; the locator is the cited version."（对 [44]/[18]/[34] 给 locator 类别；
   三篇综述 PDF 本轮未逐一下载，未编造页码）。
5. **Conclusion 软化（B2）** — `MANUSCRIPT.md:362-364`：
   "adds little" → "**adds little to comparability**"；"our survey found none for multimodal models" →
   "**in the works cited here we found none** for multimodal models"。
6. **POPE highlight 修正（B3）** — `tools/_build_prl_tex.py:55` 与 `highlights.tex:24`：
   "Reported POPE values differ without naming the benchmark subset" →
   "**Reported POPE values are incomparable when one paper does not name the subset**"（77 字符 < 85 上限）。
7. **摘要点名模型（C4）** — `MANUSCRIPT.md:19`："moves a model's score from 36.7% to 2.6%" →
   "moves **OpenFlamingo v2's** score from 36.7% to 2.6%"。

## 验证（base 解释器 `D:\Anaconda\python.exe`）

- `tools/_build_prl_tex.py` → `pages 7 (limit 7)` / `LaTeX errors 0` / `undefined refs 0 / cites 0` /
  `overfull hboxes 0` / `abstract words 224 (limit 250)` / `highlights 5 (max 77 chars)` /
  `bibliography 48 entries` / `checklist items 12` / **`OK: all build checks passed`**。
- `python -m tools.paper_audit audit --profile prl_commentary --fail-on NONE` →
  **`BLOCKED grade D pass=54 fail=1 warn=1 manual=9 skip=21 error=0`**；唯一 blocker
  **`A-01 uncommitted changes under paper_review_prl`**；warn **`H-02 data statement contains no URL or DOI`**
  （因 C1 删除 DOI/archive；P2 可接受——本评论无自有数据。若期刊强制 DOI，可在 cover letter 说明）。
  报告：`docs/audits/AUD-prl_commentary-20261025T083827Z.{md,json}`。

## 未解/需作者确认

- **DoRA 表注（已解决）**：2026-10-25 末期已按 arXiv PDF `2402.09353v6` 核实——Appendix A.5 的
  **Table 12**（PDF p.18）表头仅写 "POPE"，全文无 rand/pop/adversarial 字样；三值 85.9/86.4/87.2 即 FT/LoRA/DoRA
  三行。评论的负面归因成立，pin-cite 已补 "Table 12, whose column is headed only 'POPE'"。
- **Table 1 三篇综述**的具体页码未核验；当前用 caption 的 "abstract and introduction" 定位，如审稿要求
  精确页码需再下载三篇 PDF。

---

# Applied fixes 第二轮（2026-10-25 末期，"全部改对不要留错误"）

## 1. DoRA 否定归因——已按一手 PDF 核实（结论：成立）

- **取到原文**：`https://arxiv.org/pdf/2402.09353v6`（7,830,644 B，pdftotext 后定位）。
- **位置与内容**（一次文献，实际读到）：
  - **Appendix A.5 "Visual instruction tuning evaluation result"** 文内即写 "Table 12 presents the
    evaluation result of LLaVA-1.5-7B fine-tuned using DoRA, LoRA, and FT with visual instruction tuning data."
  - **Table 12** caption："Visual instruction tuning evaluation result of DoRA, LoRA, and FT for
    LLaVA-1.5-7B on a wide range of 7 vision-language tasks."
  - 表头列：`Method | # Params (%) | VQAv2 | GQA | VisWiz | SQA | VQAT | **POPE** | MMBench | Avg.`
  - 三行：`FT 100 … 85.9`；`LoRA 4.61 … 86.4`；`DoRA (Ours) 4.63 … 87.2`。
  - 全文两处 POPE：§5.3 的 benchmark 列举（"… SQA, VQAT, POPE, MMBench …"）与 Table 12 表头；
    **表头只写 "POPE"，全文没有任何 rand/pop/adversarial 子集字样** ⇒ 评论的负面归因成立。
- **改动**：`MANUSCRIPT.md:202` 的 pin-cite 由 "(§5.3 and Appendix A.5)" 改为
  "(§5.3 and Appendix A.5, **Table 12**, whose column is headed only \"POPE\")"；
  现在该句可逐字核对（表号 + 表头引用均来自原文）。
- 因此原先"未解 DoRA 表注"一条**已关闭**，不再需要作者二次核对。

## 2. H-02 警告——按 (a) 方案诚实清除

- 采用 lead 允许的 **(a)**：细化检查，而非给评论硬塞一个不实 archive/DOI。
- `tools/paper_audit/checks.py::check_H02`：当数据声明既无 URL 也无 DOI、但含显式
  "no new data were generated" 声明时，返回 **PASS**（"explicit no-new-data declaration;
  values quoted from the cited sources"）；否则仍 warn。
- `tools/paper_audit/registry.py`：H-02 描述中记录理由（2026-10-25：PRL Commentary 不产生数据，
  删掉 archive/DOI 句比编一个 DOI 诚实；故显式无新数据声明应通过）。
- 未添加任何 repository DOI；Data statement 仍是
  "No new data were generated for this article; all quantitative values in Section 3 are taken from the
  cited sources."

## 3. J-01 警告——刷新 claim ledger

- `python tools/_claim_ledger.py --apply` → `✅ 通过 96 ｜ ❌ 失败 0 ｜ 共 96 条`，
  `outputs/analysis/claim_ledger.json` 更新时间 16:50:36，晚于 `main_prl.tex` 16:50:17 ⇒ J-01 PASS。

## 4. 重建与门禁（base 解释器 `D:\Anaconda\python.exe`）

- `tools/_build_prl_tex.py` → `pages 7 (limit 7)` / `LaTeX errors 0` / `undefined refs 0 / cites 0` /
  `overfull hboxes 0` / **`OK: all build checks passed`**；PDF 7 页不变。
- `python -m tools.paper_audit audit --profile prl_commentary --fail-on NONE` verbatim：
  **`PRL Commentary - Pattern Recognition Letters (cas-dc) BLOCKED  grade D  pass=58 fail=1 warn=1
  manual=9 skip=17 error=0`**
  - 唯一 blocker：**`A-01 P1 uncommitted changes under paper_review_prl`**（未提交 ⇒ 需 lead 提交后才会消失；
    本次按纪律不 commit）；
  - 唯一 warn：**`I-02 P1 frozen submitted package (not compared with the live draft)`**（预期、具名）；
  - **H-02 已 PASS**、**J-01 已 PASS**（此前两条 warn 清除）。
- 若 lead 提交后再跑，预期即为 **READY / grade A / fail=0 / 仅 I-02 warn**。
- 报告：`docs/audits/AUD-prl_commentary-20261025T085047Z.{md,json}`。


