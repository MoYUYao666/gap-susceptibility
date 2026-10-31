# Paper A 内容/逻辑评审（2026-10-25）

**对象**：`paper合/`（合并稿，目标 Neurocomputing，稿号 `NEUCOM-D-26-23760`），两个变体
`main_nc.pdf`（79 页，elsarticle/Neurocomputing）与 `main_springer.pdf`（56 页，sn-jnl）。
**方式**：只读。读了两份 wrapper、`paper合/sections/` 全部 10 个源文件、附录（补充材料 A–H 与两个
后置附录），并把文本里的数字逐个回查到归档字段。**未改动任何稿件**。

**一句话结论**：**数字层面非常扎实**——抽查的 30 余个数字全部能在指名归档的指名字段里找到，
`outputs/analysis/claim_ledger_paperA.json` 也是 **88 条全过、0 gap**；真正的问题集中在**措辞与
一处重复小节**，其中前两项建议在投稿前处理。

---

## (a) 必须改（2 项）

### A-1 「predicts」与摘要的「association, not a predictor」系统性冲突

摘要明确写：

> `main_nc.tex:60`（Springer 版 `main_springer.tex:63` 同句）
> “we report an **association, not a predictor**, and show that its coefficients are protocol
> functionals, not model constants.”

同一份稿子里却有 8 处把 DG 称为「预测器/预测」：

| 位置 | 原句（节选） |
|---|---|
| `sections/empirical.tex:161` | 小节标题：`\subsection{Distribution Gap **Predicts** Retrieval Performance}` |
| `sections/empirical.tex:164` | “A key statistical discovery is that the Distribution Gap **strongly predicts** retrieval performance.” |
| `sections/empirical.tex:169` | 图注：“DG vs. CG as retrieval **predictors** … DG achieves r=−0.714, substantially stronger than CG” |
| `sections/empirical.tex:181` | 表头：`Predictor & $r$ & partial $r$ (control CG) & $p$` |
| `sections/theory.tex:125` | 段首：“**DG as a retrieval predictor.** … DG **predicts** R@1 at r=−0.714” |
| `sections/validation.tex:202` | “**DG as predictor:** DG is the natural state variable …” |
| `sections/introduction.tex:5` | “…**predicts** retrieval performance at r=−0.714 over n=204 experiments” |
| `sections/conclusion.tex:5` | “…the Distribution Gap **predicts** retrieval performance (r=−0.714 …)” |

而稿子自己在 `empirical.tex:190` 又写：“we report an **association** with its per-fold spread rather
than a **predictive relation**”。留出样本外 R² 仅 0.449/0.396（`pr_stats_holdout.json`），
**「association」是正确口径，「predicts」是过强口径**。
**建议**：统一改为 “is associated with / correlates with / tracks”（小节标题、图注、表头、
`theory` 与 `validation` 的两个小标题也一并改），保留摘要与 §190 的 association 口径。

### A-2 「DG 显著优于 CG」缺差异检验，且聚类区间重叠

| 位置 | 原句 |
|---|---|
| `introduction.tex:5` | “…**far outperforming** the commonly reported Centroid Gap” |
| `empirical.tex:164` | “DG achieves r=−0.714 … **substantially outperforming** CG (r=−0.594)” |
| `empirical.tex:169` | 图注：“DG achieves r=−0.714, **substantially stronger** than CG (r=−0.594)” |

归档事实（`outputs/analysis/dg_r1_reproducible.json`）：

- `primary.DG_vs_R1 = **−0.7142**`、`primary.CG_vs_R1 = **−0.5939**`（差 **0.120**）；
- `cluster_bootstrap.DG_ci = **[−0.8885, −0.6128]**`、`cluster_bootstrap.CG_ci = **[−0.7771, −0.4618]**`
  —— **两个区间在 [−0.7771, −0.6128] 上重叠**；
- `primary.DG_vs_CG = 0.9451` 是 **DG 与 CG 之间的相关**，**不是**两者预测力的差异检验；
  `DG_delta_r/DG_delta_p`（0.1344/0.0554）是 **ΔDG 与 ΔR@1** 的相关，也不是差异检验。

⇒ 全 `outputs/` 里**没有**「两个相依相关系数之差」的检验（Williams/Steiger 或对 Δr 做配对 bootstrap）。
**建议**：要么补一个**相依相关之差**的检验（数据已在 `dg_r1_reproducible.json::rows`，可直接配对
bootstrap），要么把 “far/substantially outperforming” 降为 “higher than”，并注明两个聚类区间重叠。

---

## (b) 应该改（3 项）

### B-1 「Data availability」小节重复，且把 back matter 说成 front matter

`sections/conclusion.tex:13-15`：

> `\subsection*{Data availability}`
> “The derived data and analysis code are openly available; see the Data availability statement in the
> **front matter** for the repository and DOI.”

但真正的声明在**后置部分**（NC：`main_nc.tex:81` `\section*{Data availability}`，位于 appendix 之后；
Springer：`main_springer.tex:83` `\bmhead{Data availability}`）。结果：

- PDF 里出现**两个同名 “Data availability”**（NC 抽取计数 2；Springer 抽取计数 3，其中一处是同一句跨页
  被重复抽取，实际结构同样是 2 个）；
- 该小节指向“front matter”，而它**自己就在正文末尾** ⇒ 循环自指 + 位置描述错误。

**建议**：删掉 `conclusion.tex:13-15` 这 3 行（真正声明在 wrapper 里已完整）。

### B-2 两个变体的 Data availability 内容不一致（claim 相同、信息量不同）

| 变体 | 内容 |
|---|---|
| NC `main_nc.tex:82-88` | 列出“per-run result records, **per-epoch monitoring trajectories, the strict-freezing controls and the cross-architecture sweeps**, together with the analysis scripts…”，并含 “which carries them at and after that release” 与 “**No datum used here is restricted.**” |
| Springer `main_springer.tex:84-87` | 仅 “per-run result records, the analysis scripts and the training configurations”，**缺**上述两处 |

两者主张不冲突，但**同一事实的披露程度不同**；审稿人只看一版时会对“归档里到底有什么”产生不同印象。
**建议**：以 NC 版为准对齐 Springer（或两版都改成同一句）。

### B-3 归档里的 `dataset/model` 标签是**推导**的，正文未披露

`dg_r1_reproducible.json::provenance.labels` 原文：

> “results.json archives **NO** dataset/model/config field; labels are **derived**, see label_evidence.
> family (first path component) is the only archive-literal grouping.”

而正文的分层结论（`empirical.tex:196`：Flickr30k r=−0.781 / MS-COCO r=−0.598；CLIP B/32 r=−0.748 /
BLIP r=−0.977 / SigLIP r=+0.808）**依赖这些推导标签**；12 个 family 聚类是 archive-literal（没问题），
但 dataset/model 分层不是。稿子目前没有任何一句说明标签来源。
**建议**：在 `empirical.tex:196` 段或 provenance 附录加一句“dataset/model 标签由运行目录名推导，
推导证据见归档 `label_evidence`”，并把该键写进附录。

---

## (c) 可改可不改（4 项）

| # | 位置 | 问题 | 说明 |
|---|---|---|---|
| C-1 | `main_nc.tex:53` vs `main_springer.tex:55` | 摘要同一句拼写不同：**characterize** / **characterise** | 主张一致，仅拼写；建议统一 |
| C-2 | `main_springer.tex:3-4` | 文件头注释仍写 “Target: **EAAI / NCAA / Cognitive Computation**” | 实际目标是 Neurocomputing（不进 PDF，但源码注释过时） |
| C-3 | `supplement.tex` 的 `\section*{A. …}`–`\section*{H. …}` | 附录字母是**手写死在标题里**的 | 一旦增删附录小节就会静默错位；今天抽查 **E=Decoder-Based VLM、G=A Larger Decoder Model、H.2=matched ladder 全部与正文引用一致** ✓，但建议改 `\ref` 管理 |
| C-4 | `provenance_appendix.tex`（全表）与 `docs/PROVENANCE_MANIFEST_2026-10-20.md:97-114` | 只登记**归档文件名**，未给**字段路径** | 规则要求 “结果 JSON（含字段路径）”；`_p1428_provenance_gate.py` 目前**通过**，但读者无法从印刷数字直接跳到字段（如 `tab:corr` → `dg_r1_reproducible.json` 未指 `primary.partial_DG_given_CG`） |

---

## 已核对通过（明确记录，不是问题）

1. **DOI v2.5 回填**：`main_nc.tex:87` 与 `main_springer.tex:87` 均为 `10.5281/zenodo.23632347`
   （v2.5, 25 October 2026）；`paper合/**`（.tex/.md）内**无**任何旧 DOI（23609295/23523263/23614290/23341223）残留。
2. **DINOv2 异构配对段**（`empirical.tex:46`）8 个数字**全部**对上：
   冻结 CG `0.6769→0.677`、ΔCG both `−0.40986→−0.410`、ΔCG text `−0.39127→−0.391`、
   R@1 `0.555 / 0.354 / 0.289`、head `656,384`（`norm_probe/results.json::source.head_meta.n_head_params`）、
   未拟合头 `R@1 0.005` 与 `ΔCG −0.29879→−0.299`、`76%`（=0.29879/0.39127=0.764）、
   `exp(logit_scale)=14.29`（`logit_scale=2.659260`）；适配器可训练量 `196,608`/`491,520` 亦对上。
3. **DG–R@1 全部数字**（`dg_r1_reproducible.json::primary`）：r `−0.7142→−0.714`、CG `−0.5939→−0.594`、
   偏相关 `−0.5814→−0.581`、CGΔ `0.1898→0.190`（p `0.006554→0.007`）、
   聚类 bootstrap r `−0.738` 与 CI `[−0.8885,−0.6128]→[−0.889,−0.613]`。
4. **初态聚类 bootstrap**：`outputs/clustered_bootstrap_dg_r1.json` —— `n_experiments=98`、`n_clusters=14`、
   `r_mean=−0.8474→−0.847`、`ci95=[−0.936,−0.709]`（精确）、`frac_resamples_ge_0=0.0004 → 4 of 10,000` ✓。
5. **留一法**（`pr_stats_holdout.json`）：family 12 折 `0.4488→0.449`、`0.3961→0.396`、
   `0.6667→67%`、worst=`siglip`；design-cell 6 折 `0.2363→0.236`、`0.2266→0.227`、`67%`、
   worst=`flickr30k | SigLIP` ✓（正文“weakest fold is SigLIP”成立）。
6. **CR1 / 混合模型**（`pr_stats_hardened.json`）：`cluster_robust_OLS.by_design_cell` 的
   `beta_DG=−1.0484→−1.05`、`se_cr1=0.2911→0.29`、`p_cr1_t_Gminus1=0.01553→0.016`（摘要是三者中最保守的
   grouping，做法正确）；`M4…` 的 `beta_DG=−0.9526→−0.95`、`se_DG=0.079→0.08` ✓。
7. **计数**：317 = 221（catalogue）+ 96（ODE fits）；117 mechanism + 104 controls = 221 —— 均由
   `claim_ledger_paperA.json` 核过（**88 条全过、0 gap**）。
8. **页数与构建**：PDF 79 / 56 页，与 `tools/_p1454_final_verify.py::PAGES` 常量一致；
   两版重编译 **0 errors / 0 undefined refs / 0 undefined cites / 0 overfull**（今日实测）。
9. **交叉引用**：两版均无未定义 `\ref`；附录字母引用 **E / G / H.2** 与 `supplement.tex` 手写标题
   （`E. Decoder-Based VLM`、`G. A Larger Decoder Model`、`H.2 A matched ladder over family and scale`）**一致**。
10. **两变体主张一致**：正文共用同一批 `sections/*.tex`（wrapper 只差模板），摘要数字段（−1.05/0.29/0.016/
    [−0.89,−0.62]/−0.95±0.08）**逐字相同**；差异只在 B-2 的信息量与 C-1 的拼写。
11. **补充材料的 VLM/LLaVA 段**（`supplement.tex:266-298`）：13 seeds、population sd 口径已明示、
    配对 bootstrap `−1.82 [−2.09,−1.54]` 与 `+9.16 [+8.69,+9.68]` 均不含 0、“ordering resolved” 而非“averaged” ✓。
12. **局限清单**（`discussion.tex:60-83`）异常完整：第 12 条量化了图库噪声（CG sd 0.00025 / R@1 sd 0.0055）
    并明确“below about 0.006 不应解释”“the pair as unresolved”；第 13 条把 Visual Fragility 定位为
    “the interpretation most consistent with…, not an established mechanism”——**不构成 over-claim**。

---

## 三个最强点

1. **DG–R@1 关联的统计加固**：CR1 聚类稳健（−1.05，SE 0.29，p=0.016，取最保守 grouping）、
   混合模型 β=−0.95±0.08、两条独立聚类 bootstrap（−0.738 与 −0.847）、留一 family/cell 的样本外 R²。
   数字全部可回溯（台账 88/88），且**主动报告了精度损失**（“far less precision than 204 independent runs”）。
2. **理论的可证伪性**：Γ_m 分解 + 一阶 ODE，并**明确报告了一个被证伪的预测**（‖g_v‖∝√r 失败 ⇒
   Effective Rank Saturation）；`discussion` 第 8 条还承认该系数“identifies the best position but does not
   rank the other two”。这种自证伪与自限是审稿人最难反驳的部分。
3. **strict-freezing 控制 + 解码器 VLM 外推**：13 seeds、配对 bootstrap、三种子分布不重叠、
   差异区间不含 0，把“text-only 更优”从“平均更好”升级为“在该模型上可排序”，同时保留 SigLIP 反例。

## 三个最弱点（审稿人最可能打的）

1. **A-1 的口径自相矛盾**：摘要说“不是预测器”，正文 8 处（含小节标题、图注、表头、理论段首）说“predicts”。
   这是最容易被一眼抓住的，且修起来很便宜。
2. **A-2 的 DG>CG 优势无检验**：全文的“key statistical discovery”建立在 DG 优于 CG 之上，但差 0.120
   无检验、聚类区间重叠；审稿人若要一个相依相关之差检验，目前归档里没有。
3. **归档依赖 + 推导标签**：n=204 是“带显式规则重挑的归档子集”（旧 n=81 子集选择规则已丢失，
   `dg_r1_reproducible.json::supersedes`）；R@1 是“一次抽样”（第 12 条已承认）；dataset/model 标签是推导的
   （B-3 未披露）；ODE 只用 55 条归档 LoRA 轨迹（第 9 条已承认 3 seeds vs 原 5 seeds）。这三者叠加后，
   “关联强度”的数值会随归档口径变化——稿子已在第 9/12 条部分披露，但**推导标签**与**子集重挑的动机**
   还可以说得更明白。

---

## 无法核实 / 未做

1. **DG 与 CG 预测力之差的检验**：全 `outputs/` 未找到（这也是 A-2 的依据，不是我漏查）。
2. **“317 experiments”的逐条构成**：只核到 221 + 96 = 317 这条等式（台账有）；未逐目录清点 317 个 run。
3. **旧 n=81 子集的选择规则**：归档自己说“selection rule was lost”，因此无法复核旧表数字（稿子已全用 n=204，
   正文无 n=81 残留 ✓）。
4. 未评审图片本身（只核图注与图号）、未评审参考文献格式（属另一类审计）。

---

## 复现要点（我用到的查法，便于复核）

- 数字→归档：直接读 `outputs/analysis/{dg_r1_reproducible,pr_stats_hardened,pr_stats_holdout,
  clustered_bootstrap_dg_r1}.json` 与 `outputs/analysis/dinov2_hetero/**/results.json`，
  按 `primary.* / cluster_bootstrap.* / leave_one_*_out.* / mixed_effects.* / encoders.*` 路径取值；
  `clustered_bootstrap_dg_r1.json` 在 `outputs/` 根下（不在 `analysis/` 下）。
- 计数：`outputs/analysis/claim_ledger_paperA.json`（`pass: 88, gap: 0`）。
- 交叉引用/构建：`paper合/main_nc.log`、`main_springer.log` 的 `Output written` 与 `! `/`undefined` 计数。
- **方法论提醒（给后来者）**：不要用“全库 + 容差”去搜数字——我第一版这么干，0.677 命中的是
  `a1_epoch_sweep` 的 tau5，纯属假命中（正是 `AGENTS.md` 里 `_reproducibility_gate.py` 的教训）。
  **必须先指名归档，再指名字段。**


---

# Applied fixes（2026-10-25 执行，"全改"；只改稿件，未提交）

> 逐条列出已落到 live 稿的改动。两版共用 `paper合/sections/*`，故正文改动同时进入两版。
> 硬约束：页数必须仍为 **NC 79 / Springer 56**、0 错误 / 0 未定义引用 / 0 overfull、不碰 `SUBMISSION/**`、
> 不改 `tools/_p1454_final_verify.py`、不提交 —— 全部达成（验证见本节末）。

## A-1：DG 不再被称作 predictor（8 处）

| # | 位置（新行号） | 改动 | 理由 |
|---|---|---|---|
| 1 | `paper合/sections/empirical.tex:161` | 小节标题 `Distribution Gap Predicts Retrieval Performance` → `Distribution Gap Is Associated with Retrieval Performance` | 摘要写 "association, not a predictor" |
| 2 | `paper合/sections/empirical.tex:164` | "A key statistical discovery is that the Distribution Gap strongly predicts retrieval performance." → "A key empirical regularity is that the Distribution Gap is strongly associated with retrieval performance." | 同上 |
| 3 | `paper合/sections/empirical.tex:169` | 图注 "as retrieval predictors" → "as correlates of retrieval" | 同上 |
| 4 | `paper合/sections/empirical.tex:181` | 表头 `Predictor` → `Statistic`（表行 DG / CG / CG$\Delta$ 不变） | 同上 |
| 5 | `paper合/sections/theory.tex:125` | 段首 `DG as a retrieval predictor.` → `DG as a correlate of retrieval.`；"DG predicts R@1" → "DG is associated with R@1" | 同上 |
| 6 | `paper合/sections/validation.tex:202` | `DG as predictor:` → `DG as a correlate of retrieval:` | 同上 |
| 7 | `paper合/sections/introduction.tex:5` | "predicts retrieval performance at $r=-0.714$" → "is associated with retrieval performance at $r=-0.714$" | 同上 |
| 8 | `paper合/sections/introduction.tex:20` + `paper合/sections/conclusion.tex:5` | "DG-based retrieval prediction" → "the DG--retrieval association"；"predicts retrieval performance" → "is associated with retrieval performance" | 同上 |

## A-2：DG 优于 CG 降为描述性（3 处，未引入任何新数字）

| 位置 | 改动 | 理由 |
|---|---|---|
| `paper合/sections/introduction.tex:5` | "far outperforming the commonly reported Centroid Gap" → "more strongly than the commonly reported Centroid Gap" | 无差异检验支撑时不作"显著更优"表述 |
| `paper合/sections/empirical.tex:164` | "substantially outperforming CG ($r=-0.594$)" → "higher than CG ($r=-0.594$)" | 同上 |
| `paper合/sections/empirical.tex:169` | "substantially stronger than CG" → "higher than CG" | 同上 |

**为什么没有采用"两区间重叠 ⇒ 不作差异声明"的措辞**：我用归档三值算了 Hotelling--Williams 相依相关检验
（输入 `outputs/analysis/dg_r1_reproducible.json :: primary.DG_vs_R1 = -0.7142`、
`primary.CG_vs_R1 = -0.5939`、`primary.DG_vs_CG = 0.9451`，`n = 204`）：
**t = -7.86，df = 201，p < 0.001** —— 两个预测子近乎共线（r = 0.945），差异其实高度显著；而"边缘区间重叠"
只描述各自的不确定性，**不能推出差值不显著**（那样写是统计谬误）。因此稿中只做纯描述性降级
（"higher than"），既不加新数字也不写错误推理。若日后要恢复"显著更优"，正确做法是对 $\Delta r$ 做
**family 聚类自举区间**（`rows[*]` 与 first-path-component 标签均在归档里），与全文聚类口径一致。

## b1：删除重复且自指的 Data availability 小节（1 处删除）

`paper合/sections/conclusion.tex:12-15`（原第 13--15 行及其前导空行）—— 删除
`\subsection*{Data availability}` 与 "see the Data availability statement in the front matter"。
理由：真正的声明在 back matter（NC 为 `main_nc.tex:81` 起、Springer 为 `\bmhead` 段），该小节重复且自指。
效果：PDF 里 "Data availability" 由 2 处降为 **1 处**（两版均如此）。

## b2：Springer 的 Data availability 对齐 NC（`main_springer.tex:85-87`，5 处补齐）

① "the per-epoch monitoring trajectories, the strict-freezing controls and the cross-architecture sweeps,
together with the analysis scripts that compute the reported statistics and the training configurations"；
② "in a public repository at"；③ "snapshot **archived on Zenodo** under version DOI ... (\url{doi})"；
④ "which carries them at and after that release"；⑤ "**No datum used here is restricted.**"
⇒ 两版 Data availability 现已**逐字相同**（用 PDF 文本逐词比对确认，差异仅为抽取时空格）。

## b3：披露分层标签是推导的（1 处）

`paper合/sections/provenance_appendix.tex:6-9`：新增一句 "Dataset/model labels in the stratified analyses of
Section~\ref{sec:empirical} come from run directory names, not archived fields (evidence:
\texttt{pr\_stats\_hardened.json, label\_evidence})."

## c：两处廉价修正

- `paper合/main_springer.tex:3` —— 旧注释 `%% Target: EAAI / NCAA / Cognitive Computation` →
  `%% Springer-format variant of the Neurocomputing submission (NEUCOM-D-26-23760); body shared with main_nc.tex`
- `paper合/main_springer.tex:46` —— `characterise` → `characterize`（与 NC 版及正文一致）

## 页数守恒（NC 79 / Springer 56）—— 全部为排版无损压缩

改动令 NC 一度变 **80 页**（第 80 页仅剩最后一条参考文献）。按"同文件内压缩"处理：

| 位置 | 改动 | 作用 |
|---|---|---|
| `paper合/main_nc.tex:113` | `\setlength{\bibsep}{0pt}`（natbib 条目间距） | **唯一定点生效项**，NC 由 80 → 79 |
| `paper合/sections/provenance_appendix.tex:11` | `\arraystretch` 0.9（34 行长表行距收紧） | 辅助（单独不足） |
| `paper合/sections/provenance_appendix.tex:5` | 附录引言并入 `\footnotesize` 组（与表同字号） | 辅助（单独不足） |
| `paper合/sections/provenance_appendix.tex:11` | `\tabcolsep` 4pt → 3pt | 辅助（单独不足） |

## 验证（本机实跑，2026-10-25）

- **构建**：两版各 `pdflatex ×2`，exit 0；`main_nc.log` → **79 pages**，`main_springer.log` → **56 pages**；
  两版均 **0 errors / 0 undefined references / 0 undefined citations / 0 overfull hbox / 0 overfull vbox**。
- **`paper_audit --profile paperA_springer --fail-on NONE`** → `READY  grade A  pass=56 fail=0 warn=0 manual=9 skip=21 error=0`
- **`paper_audit --profile paperA_nc --fail-on NONE`** → `BLOCKED  grade D  pass=66 fail=1 warn=0 manual=9 skip=10 error=0`，
  唯一 blocker **I-02**"package copies differ from live files | regenerate the package after rebuilding the manuscript"：
  该 profile 的 package 是 `SUBMISSION/PaperA_Neurocomputing`，按指示**未刷新**。提交后跑
  `python tools/_p1169_refresh_nc_submission.py`（profile 的 `staged_command`）再复跑即可转绿。
- **`tools/_p1454_final_verify.py`**：页数行 `pages: {... 'paper合/main_nc.pdf': 79,
  'paper合/main_springer.pdf': 56 ...} pass: True`；整体 VERDICT 仍 FAIL，**唯一原因是 `git_clean=False`**
  （未提交 + 其他 agent 并行改动），与页数无关。
- **PDF 文本核验**（两版）：`Predictor` **0** 次、`Statistic` 就位；`characterise` **0** 次；
  "see the Data availability statement in the front matter" **0** 次；"No datum used here is restricted"
  与 "come from run directory names" **两版均有**；两版 "Data availability" 各 **1** 处且逐字相同。

## 未做（按指示）

未提交；未碰 `SUBMISSION/**`、`tools/_p1454_final_verify.py`、其它稿件。
`SUBMISSION/PaperA_Neurocomputing/` 的刷新（I-02 的唯一解法）与 git 提交留给 Lead。
