# Paper 3 终审：内容与论证逻辑（2026-10-25，只读）

> 审计者：`p3-stats`。对象：`paper3/paper_ieee/main.pdf`（**10 页**）+
> `supplementary/supplementary.pdf`（**22 页 / 46 段 / 51 表**，已核对 `pdfinfo` 与 `\section`/`\begin{table}` 计数）。
> 方法：主文逐页通读 + 补充材料逐节核对 + 关键数字回查归档（`p3_allocation_paired_stats.json`、
> `p3_alloc_results.json`、`p3_alloc_runs/main/*.json`、`p3_upgrade_analysis.json`、`p3_rank_separation_extended.json` 等）。
> **未改动任何稿件/补充材料**；本文件是唯一写入。

---

## 0. 总体判断

论证**结构**是自洽的（claim → 五个 corollary → 三类控制 → 负结果 → 边界），
**但存在 1 处符号/解释层面的硬矛盾必须修**（补充材料 S20 与其自身数字、与主文摘要/§IV-C、与全文其余章节三处冲突），
**另有 3 处"主文比证据更弱/更强"的措辞需要对齐**（摘要/引言的检验显著性、random 基线、以及"主文已包含全部结果"的声明）。
修掉这些之后，逻辑链可通过；不修则审稿人会直接抓住 S20 的算术矛盾。

**最强三点**：① 定理把 R3′ 明确写成假设，并用 Lemma III.1 证明 ∥∇E∥² 满足 R3 而不满足 R3′（诚实且少见）；
② 负结果控制异常完整（AdaLoRA 全面更优、random pool、matched-loss 反转、学习率反转、四栈方差分解、
blank vs real image 协议依赖）——主文全部承认；③ 数字有归档+指针表（S1/S17/S13）且 crossing 只报 bracket。

**最弱三点**：① 核心方法学卖点（Γ 分配）在经验上被自己的控制打成"不优于基线"，定理的实用价值只剩"不用搜索"；
② "E 预测下游"这条链被自己的数据否定（VQA-RAD 精度反转、POPE 指标分裂、real/blank 相关性反号），
E 的对外有效性没有被任何下游证据支持；③ 关键比较的统计功效不足（n=2/4 的对照、underpowered random pool、
3/5/10 seed 混用），部分结论建立在 n=4 的 end_E 配对上。

---

## (a) 必须在任何重投前修掉的矛盾 / 过强主张

### A1（最高优先）补充材料 S20 把配对差的符号解释反了：它的数字其实**支持** Γ-guided 在该学习率更好

- **位置**：`supplementary.tex` L1069–1086（S20，`\label{app:allocation-paired}`），
  原文：
  - L1075–1079：“the two forms differ only in whether the between-seed variance is removed, and **neither supports an advantage for the $\Gamma$-guided allocation**. … retaining the pairing bounds the difference away from zero, with **the $\Gamma$-guided arm on the worse side**.”
  - L1084：“The two arms are therefore not equivalent: they are separated, **in the direction opposite to the claim**.”
  - 同一数字被 `S1` 表 L105–109 引用为“The $\Gamma$-guided allocation does not beat the uniform rank plan.” 的**证据**。
- **为什么是矛盾**：该段讨论的是 guided−uniform = **−3570.10**（CI [−5524.16,−1850.31]），六对全负。
  但本文自己的语义是 **ΔE 越负越好**：
  - `S14` L859–860 明写“positive values mean degradation”；
  - 主文 Table II/Fig.1 把负 ΔE 的 r=4 标为 “Safe/stable”、正 ΔE 标为 “Danger”；
  - `S35` L1786–1796 用“AdaLoRA reaches the **lower** alignment energy”作为 AdaLoRA 更好的证据，
    并用“uniform beats Γ”对应 uniform 的 +2223/+3462/−1487 **低于** Γ 的 +2591/+9344/+2250。
  - 归档原始记录（`p3_alloc_runs/main/exp_beta_paper_0.137__seed42.json`）`delta_E = E1 − E0 = 3234.93`，
  对应 E0=23470.85 → E1=26705.78，即正 = 能量上升 = 对齐变差。
- **算术核对**：guided 均值 +1477.45，uniform 均值 +5047.55，差值 = **−3570.10**（与归档逐位一致）。
  低的那个是 guided ⇒ 在该学习率上 guided **更少损伤对齐**，配对分析是在**支持** guided；
  该段“sharpens the contrast rather than weakening it / worse side / opposite to the claim”三句全部反向。
- **外部连带**：归档自述 `p3_allocation_paired_stats.json :: conclusion.claim_status.direction =
  "Gamma-guided is lower (worse) than uniform"` 也是同一处反向解释（机器可读文本，不在稿件内，但会被复现脚本/账本引用）。
- **正确写法**：容量匹配设置下 guided 更低（更好）3570，六对一致，CI 不含零；
  负结论必须建立在**与主文一致**的控制上：matched-loss 对照反转（guided **更高/更差**，+3125.68 [+368.73,+5882.64]）、
  3×10⁻⁴ 反转（+5968 vs +2842）、random pool underpowered（见 A3）。
- **严重度**：referee 一算就发现；且与摘要 “the allocation beats the uniform-rank baseline at one learning rate”
  直接冲突（`main.tex` L78–80）。**必须改**。

### A2 摘要/引言把 5-seed 的显著性检验写反了

- **位置**：`sections/introduction.tex` L50–51（贡献 3）：
  “its interval at $r=5$ spans zero and **an exact permutation test between neighbouring ranks is not significant**”。
- **冲突证据**：`main.tex` L86（摘要）写“five seeds per rank; exact permutation $p=0.008$”；
  `sections/experiments.tex` L118：“exact two-sided permutation test over the ten runs, $p=0.008$, the smallest attainable with five seeds”；
  `S17` L962：“five seeds, exact $p=0.008$”。三处都说 5-seed 检验**显著**（0.008 为该设计可达最小值）。
- `p=0.100` 只属于 **3-seed** sweep：`sections/theory.tex` L160、`sections/discussion.tex` L22（后者明写“with three seeds”）。
- **修法**：引言那句要么删“not significant”，要么改成
  “with three seeds the exact test gives $p=0.100$; with five seeds it reaches the design minimum $p=0.008$”，
  并把摘要中的 bracket 表述与之一致。**必须改**（否则摘要与贡献列表自相矛盾）。

### A3 摘要/引言/结论说“与 random 分配不可区分”，正文自己说“不只是不可区分，方向是不利于 guided”

- **位置**：`main.tex` L81–82（摘要）“it is indistinguishable from a random allocation of the same budget”；
  `introduction.tex` L54、`conclusion.tex` L35 同句。
- **正文反证**：`sections/experiments.tex` L251–257：“Pairing the Γ-guided and random arms … the guided arm ends
  at **+11.5 higher** alignment energy than its random partner (95% bootstrap CI [+6.8,+16.2] …), so the direction of
  the effect is **against** the guided allocation, **not merely indistinguishable** from it.”
  （+11.5 方向 = 更高 ΔE = 更差；归档 `p3_upgrade_analysis.json :: theory_vs_random.mean_diff_end_E = 11.5`，
  `interpretation: positive diff means theory ends at higher alignment energy than random`。）
- 同时摘要 L80 “the advantage … **vanishes** under matched training loss” 与正文不符：正文 L231 + L237 一带
  说 matched-loss 下 guided **更差**（+5968 vs +2842），是“反转”而非“消失”。
- **修法**：摘要/引言/结论改为“与随机分配相比没有优势、配对比较方向不利（n=4）”，
  matched-loss 改为“reverses”。**重投前必须改**（方向偏向自己的过强表述）。

### A4 “主文已包含所有结果”的声明不成立；且 limitations 的“question-answering”与 S29 冲突

- **位置**：`main.tex` L108–110：“Every result quoted in this paper is stated in the main text;
  the supplement supplies the derivations behind them.”
- **反证**：补充材料 S29（VQA-RAD 全 451 题 + POPE 3000 题）与 S41（official-implementation 对比，
  含 `small` 判定、margin 196.05、复现性 caveat）都是**结果**，主文 `sections/*.tex` 全文
  **grep 不到 VQA / POPE / 196.05 / 150.5**（只有 `downstream` 泛指 CLIP 检查）。
- **另一处**：`sections/discussion.tex` L63–65（limitations 第 4 条）：
  “The phase transition is verified on two instruction datasets (Alpaca, ShareGPT) and on a captioning family,
  **but not on question-answering data**” —— 但 S29 正是 QA 下游检查。
  若指“phase-transition 的 rank sweep 未在 QA 数据上跑”，需要写明“the rank sweep, not the downstream accuracy checks”。
- **修法**：把 L108–110 改成“主文数字的推导在 supplement”，并把 VQA-RAD/POPE 与 official-IGU 结论
  用 1–2 句写进主文（limitations 或 §IV-E 末尾即可，10 页有空间）——否则 supplement 的定位
  “not required to follow its argument”与这些**结果性**内容矛盾。**重投前必须改**。

---

## (b) 逻辑缺口 / 审稿人会攻击的未声明假设

### B1 S29 的“resolved reversal of the alignment-energy ordering”没有定义“reversal 的是什么”
- `supplementary.tex` L1410–1412：“On exact-match accuracy the same difference is $+0.0532$ … which excludes zero:
  on the full test set this is a **resolved reversal of the alignment-energy ordering** rather than an ordering …”
- 事实：r=5 的 ΔE 更低（更好），且 r=5 的 accuracy/token F1 都更高 ⇒ accuracy 与 energy **同向**，没有任何“反转”。
  `S17` L971 也重复“is a reversal”。请删掉或写清反转对象（例如“相对 300 题版本 / 相对 r6 优于 r5 的预期”）。

### B2 S17 的“zero-shot allocation beats uniform rank = not supported”在 A1 修好后会失去证据
- `supplementary.tex` L965 把“不成立”的证据写成“trained arms $+196$ to $+444$；official IGU $+240.5$”——
  这只说明所有分配器都让能量变差，**不构成**“beats uniform 不成立”的直接证据。
  证据应改为 matched-loss 反转（+3125.68）、3×10⁻⁴ 反转（+5968 vs +2842）、random pool underpowered。
- 同理 `S1` 表 L107 的证据列在 A1 修好后需要重写（原文用 −3570 当反证，实为支持）。

### B3 补充材料内部两处“有多少对 rank 可分辨”计数不同，未互相解释
- `S34` L1730–1735：“an exact two-sided permutation test … **separates fourteen of the fifteen pairs** at the 5% level …
  the single unresolved pair is r=7 vs r=8”。
- `S46` L2172–2174：“**twelve of the fifteen rank pairs are ordered in the same direction for every seed**, and the three
  that are not are the adjacent pairs r=3 vs r=4, r=4 vs r=5 and r=7 vs r=8.”
- 二者判据不同（精确检验 vs 每 seed 同向），可以同时成立，但**没有一句话说明**；referee 会当成矛盾。
  建议在 S46 加半句“this is a stricter condition than the exact test of S34, which resolves 14/15”。

### B4 §IV-C 的句子顺序/指代让“正结果”紧跟“失败”出现
- `sections/experiments.tex` L229：“The capacity-matched comparison we ran **does not support the stronger reading** either,
  and we report the failure in full. At the learning rate used throughout, the Γ-guided allocation reaches
  $\Delta E = +1477 \pm 1563$ against $+5048 \pm 1900$ for uniform … (Welch $p=0.0055$ …)”。
  “stronger reading”从未定义；紧跟其后的数字（guided 更低更好、p=0.0055）看起来与“failure”相反。
  建议先给数字，再解释“这只在一个学习率成立，因此不构成稳健优势”，并明确“stronger reading = 跨学习率/匹配损失的稳健优势”。

### B5 random-pool 的“方向不利”只用 n=4 的 end_E 配对支撑，措辞应降级
- `sections/experiments.tex` L251–257 用 n=4、**end_E**（不是 ΔE）的配对得到 +11.5 [CI +6.8,+16.2]，
  随即写“not merely indistinguishable”。而归档自己的 verdict 是 `UNDERPOWERED_TO_DISTINGUISH`
  （`p3_alloc_random_pool.json`，within-plan seed range 14331 vs between-plan 1870）。
  n=4 且不同指标，证据强度不足以支撑“direction of the effect”那么强的表述；建议写成“suggestive / does not favour”。

### B6 多个 r=4/r=5 数值来自不同 batch/seed 数，缺一张“数值—批次”对照
- r=4 同时出现 −105±21（Table II，3 seeds）、−108±27（§IV-C，5 seeds）、−105（§IV-F）；
  r=5 出现 −21±26（Table II）、−23.0±22.3（5 seeds）、−23.0（torch 2.9 栈）、−43.7（torch 2.12 栈，10 seeds）、
  −1.33/−49.0（legacy 环境块）。
- 主文对 3 vs 5 seeds、两个环境块有解释，但对 −105 vs −108、r=5 的四个值没有**一处集中说明**。
  建议加一句“quoted per-rank values are from batch X / n seeds”或给一张小对照表（不占页：接在 Table II 注内）。

---

## (c) 润色 / 排序 / 交叉引用（不影响结论）

1. **错误指向**：`sections/discussion.tex` L74 “for the three-stack design of **S37**” —— S37 是
   “Real-image rank sweep”；three-stack 分解在 **S39**（`tab:envvar` 的 caption，L1928–1932）。
   同类：主文其它 S 编号（S9/S13/S17/S21/S5/S6/S7）核对**均正确**（S9 确有 Sample Size Robustness、
   Second-Dataset、Comparison with Prior Work、Decoder VLM 四个 subsection）。
2. **S29 caption 标点破损**：`supplementary.tex` L1406–1407
   “…TOST $p=0.0057$ at the pre-declared margin of $0.05$. The smallest margin … 0.0333 in accuracy (field …)., so $r=6$ is
   indistinguishable from base rather than better).” —— 句号/逗号/右括号顺序坏；应改成一句完整从句。
3. **S1 表缺行**：claims 表 6 行覆盖 crossing / 环境 / rank control / decoder / allocation / 跨骨架，
   但**没有** VQA-RAD、POPE、official-implementation comparison 三行；S17 只有 VQA 一行（无 POPE、无 IGU 对比行）。
   补充材料自己的定位是“one row per substantive claim”，S29/S41 是 substantive claim ⇒ 建议补 3 行
   （或明确“S29/S41 为 secondary analyses，不进入主 claims 表”）。
4. **数字重复但标注不同值**：见 B6；即使不改正文，也应让 Table II caption 明确“3 seeds, batch E2+supplementary”
   与 §IV-C “5 seeds”一一对应（目前 caption 有写，但 §IV-C 未回指）。
5. **摘要的“three times”缺边界**：正文说 3.09× 仅在 operating point、且样本依赖（15 tokens 时 3.0% vs 留出集 18.6%）、
   两个 held-out 样本在一个 budget 上**反向**（+122% vs +104%）。摘要只留“three times”，
   建议加“on this sample set”。（正文已诚实，摘要略过强。）
6. **S17 的“HALoRA/Shap”行证据未列数值**：L966 只用 NTK $+396.0$、Γ $+196.5$、official IGU $+240.5$，
   而 S28 的 HALoRA/Shap arm 是 +284.0 / +444.0；可补一句或改行标题。

---

## 附：逐节核对结论（lead 点名的章节）

| 章节 | 正文是否只主张数字支持的 | 与 S1 claims 表是否一致 |
|---|---|---|
| S1（claims 表） | 除第 5 行（A1 反向）外，其余 5 行与本卷正文一致 | —（自身） |
| S20 配对重分析 | **否**（A1：符号解释反向） | **否**（S1 第 5 行同错） |
| S35 r_c family boundary | 是（5.334 [5.195,5.467]、5.260、[4.96,46.76]、5.699 [5.556,5.830]、AdaLoRA 四条 cell 均与归档一致） | 是（第 1/6 行引 S35 正确） |
| S46 Gamma robustness | 是（ρ=0.160 与 0.087 是两个不同量：前者“ordering 可翻”，后者“六对全保序”；4.227、26.4× 与 table 一致） | 是（第 6 行） |
| S39 四栈方差分解 | 是（−23.0/−43.7/+24.0/−63.8、σ 32.46/32.72、49.59% [35.8,74.9]、45.20% 与归档一致） | 是（第 2 行） |
| S28 allocation-rule baselines | 是（+284/+333/+444 与 S19 的 +396/+196.5 分别属于“reimplementation”和“baseline”两组，未混用） | 是（S1 第 5 行引 tab:rulearms 正确，但 row 语义受 A1 影响） |
| S29 VQA-RAD + POPE | VQA 数值与归档一致；**“reversal”措辞无定义（B1）**；POPE 数值一致、结论是“accuracy 口径 verdict + 指标分裂”，诚实 | **否**（S1 无 VQA/POPE 行；S17 有 VQA 无 POPE） |
| S41 official-implementation comparison | 是（−59.5 [−150.5,−8.0]、margin 196.05、L1=2/2、132.0/76.1、单栈、verdict small 与归档一致；复现 caveat 已写） | **部分**（S1 无行；S17 行只写“reported, no positive claim”） |

---

## 备注（构建事实，供 lead 对照）

- 当前 `supplementary.pdf` = **22 页**（此前一轮 26 页，已由 float 布局的两次提交压到 22；
  若其它文档仍写 26 页，需要同步）。→ **已被下方 "Applied fixes" 更新：现在 23 页**。
- `main.pdf` = 10 页，`main.tex` 的 `S1--S46` 指针与补充材料 46 段一致。
- 本次为**只读审计**，未修改任何稿件；如需要我把 A1–A4 的建议改法（逐句替换文本）整理成可直接套用的 patch 文本，可另开任务。
  → **已被下方 "Applied fixes" 取代：本轮已按 lead 指令改稿（仅 P3 稿件树）。**

---

## Applied fixes（operator: "全部改对"；执行后状态）

> 执行者：`p3-stats`。**只改 P3 稿件树**（`paper3/paper_ieee/`）+ 两份审计脚本 + 本笔记；
> **未动 `SUBMISSION/**`、未改任何归档 JSON、未提交 git**（lead 负责 review/commit）。
> 最终计数：**main.pdf = 10 页**；**supplementary.pdf = 23 页**（22 → 23，见下）；0 overfull（两文档）。

### A1 — S20 符号解释（补充材料）
- `supplementary.tex:1095-1099` — "the two forms … neither supports an advantage for the Γ-guided allocation" →
  "…both point the same way"；"with the Γ-guided arm on the worse side" →
  "in the Γ-guided arm's favour (the guided arm has the lower ΔE, i.e. the smaller alignment damage)"。
  *Why*：配对差 −3570.10 是 guided−uniform，而本文语义 lower ΔE = better（S14: "positive values mean degradation"；
  原始 run `delta_E = E1−E0`），原句把符号解释反了。
- `supplementary.tex:1102-1104` — 新增一段 "What the paired form does not establish is robustness: … matched training
  loss (+3125.68) and at 3×10⁻⁴ (+5968 against +2842)…"。
  *Why*：把负结论落到真正支撑它的控制上（lead 指定措辞）。
- `supplementary.tex:1109` — "separated, in the direction opposite to the claim" →
  "separated, in the direction the rule predicts (the guided arm has the lower ΔE …)"。*Why*：同 A1。
- `supplementary.tex:105-110` — S1 claims 表第 5 行整体重写：claim 改为 "…'s advantage … is not robust"，
  evidence 明确 "the guided arm has the lower (better) ΔE"，并列出 matched-loss/3×10⁻⁴ 反转；boundary 改为
  "capacity-matched contrast is not an equivalence result (TOST p=0.916) … zero-shot heuristic, not a method that
  dominates the uniform plan"。*Why*：原行把同一数字当作"does not beat"的证据，与 A1 同一符号错误。
- `supplementary.tex:986` — S17 行 "zero-shot allocation beats uniform rank = not supported" 的证据改为
  "paired difference favours the guided arm at the operating rate (−3570.10), but reverses under matched training
  loss (+3125.68) and at 3×10⁻⁴ (+5968 vs +2842) (S20); every trained arm has a positive ΔE …"。*Why*：同上。

### A2 — 引言检验显著性（主文）
- `sections/introduction.tex:50-52` — "an exact permutation test between neighbouring ranks is not significant" →
  "… is not significant with three seeds ($p=0.100$) but reaches the smallest attainable $p=0.008$ with five seeds"。
  *Why*：摘要（p=0.008, 5 seeds）与实验节（p=0.008）都说 5-seed 显著；原句只在 3-seed 成立。

### A3 — random 基线与 matched-loss 措辞（主文 3 处）
- `main.tex:81-83`（摘要）— "it is indistinguishable from a random allocation of the same budget" →
  "it is not better than a random allocation of the same budget, slightly worse in seed-paired runs"；
  "vanishes under matched training loss" → "turns negative under matched training loss"。*Why*：正文
  `experiments.tex:253-257` 说 +11.5 higher（CI [+6.8,+16.2]）"direction of the effect is against the guided
  allocation, not merely indistinguishable"；matched-loss 下 guided 更差（+5968 vs +2842）是反转而非消失。
- `sections/introduction.tex:54-57` — 同义改写："… reverses at another and turns negative under matched training
  loss, and it is not better than a random allocation of the same budget (slightly worse in seed-paired runs)…"。
- `sections/conclusion.tex:33-37` — 同上（"turns negative once the arms are matched …", "not better than a random
  allocation … (slightly worse in seed-paired runs)"）。

### A4 — blanket 声明与 limitations（主文）
- `main.tex:109-114` — "Every result quoted in this paper is stated in the main text; the supplement supplies the
  derivations" → "The main text states every result it discusses; the supplement also reports results that are not
  quoted in the main text---the two downstream tasks (Section~S29) and the official-implementation comparison
  (Section~S41)---and supplies the derivations behind the main-text results"。*Why*：S29/S41 是结果性内容，
  原句与事实不符（lead 指定措辞）。
- `sections/discussion.tex:63-66` — limitation (4) 改为 "The phase-transition rank sweep is verified on two
  instruction datasets (Alpaca, ShareGPT) and on a captioning family, but it has not been run on question-answering
  data; the downstream checks that do use QA data (Section~S29) test accuracy, not the sweep …"。
  *Why*：原句 "not on question-answering data" 与 S29（VQA-RAD/POPE）冲突；需区分 rank sweep 与 downstream check。

### 5 — 交叉引用
- `sections/discussion.tex:75-76` — "the three-stack design of S37" → "S39"。*Why*：S37 是 real-image rank sweep；
  45.20%/三栈 reference 在 S39 的 `tab:envvar` caption。

### 6 — 其余 (b)/(c) 条目
- `supplementary.tex:1437` — S29 "a resolved reversal of the alignment-energy ordering" →
  "a resolved difference between the two ranks"。*Why*：r=5 在能量（更低=更好）与 accuracy（更高）上同向，无反转；
  "reversal of what" 不可辩护。
- `supplementary.tex:992` — S17 VQA 行 "is a reversal that is not equivalent" → "is a resolved difference that is
  not equivalent"。*Why*：同上。
- `supplementary.tex:2200-2201` — S46 新增一句 "This unanimity condition is stricter than the exact permutation test
  of Table~\ref{tab:crossing10} (S34), which resolves fourteen of the fifteen pairs at the 5% level: a pair can
  separate under the exact test while one seed disagrees on its sign." *Why*：S34 说 14/15 精确可分、S46 说 12/15
  全 seed 同向，两者判据不同，缺解释会被 referee 当矛盾。
- `sections/experiments.tex:232-238` — §IV-C 的 "The capacity-matched comparison we ran does not support the
  stronger reading either, and we report the failure in full." → 先给数字再限定："The capacity-matched comparison is
  significant at the operating learning rate but not robust. At the learning rate used throughout, … (Welch
  p=0.0055 …; the paired form bounds the same difference away from zero in the guided arm's favour,
  Supplementary~S20). It does not survive being repeated at other learning rates." *Why*：去掉未定义的
  "stronger reading"，并把"失败"与"数字"的顺序摆正。
- `sections/experiments.tex:261-262` — random 配对句尾加 "---suggestive at four pairs, not a powered test."
  *Why*：n=4 end_E 配对不足以支撑"direction of the effect"的强表述（lead 要求加 n=4 caveat）。
- `sections/experiments.tex:121-123` — 新增一句数值—批次映射："Per-rank values are quoted from batches with
  different seed counts (Table II: three seeds; the rerun above: five; Supplementary S34: ten), so r=4 appears as
  −105 (three) and −108 (five), and r=5 as −21 (three) and −23.0 (five)." *Why*：同一 rank 多个值散见全文，
  原文没有一处集中说明。
- `supplementary.tex:1433` — S29 caption 标点修复："…margin of $0.05$; the smallest margin … is $0.0333$ in
  accuracy, field …), so $r=6$ is indistinguishable from base rather than better."（原为 "…0.05$. The smallest …
  )., so …"）。*Why*：重复句号/右括号错位。
- `supplementary.tex:118-140` — S1 claims 表新增 3 行（VQA-RAD / POPE / official-IGU comparison），每个数字均取自
  S29/S41 已有数值与归档。*Why*：claims 表声明 "one row per substantive claim"，S29/S41 缺行（lead 指定）。
- `supplementary.tex:987` — S17 "NTK/IGU/HALoRA/Shap" 行补上 S28 的三臂值：
  "HALoRA-style $+284.0$, IGU-style $+333.0$, ShapLoRA-style $+444.0$ (S28)"。*Why*：原行只列 S19/S41 的数，
  而 S28 正是该行标题命名的 reimplementation。
- `main.tex:85-86` — 摘要 "three times the initialization alignment energy of a real one on this sample set"。
  *Why*：正文边界（3.09× 仅在 operating point、样本依赖 + held-out 反向）要求摘要限定样本集。

### 为守 10 页所做的压缩（不删任何数字/主张）
- `sections/experiments.tex:68` — fig1 `width=0.90\textwidth` → `0.72\textwidth`。
- `sections/experiments.tex:266` — fig2 `width=0.85\linewidth` → `0.68\linewidth`。
- `main.tex:106` / `main.tex:145` — 后置声明区（Supplementary material / 声明 / 数据声明 / 致谢）包进 `{\small …}`
  （仅排版，不改文字内容）；`main.tex:69-75` 摘要第一段同时收紧措辞（"We ask what an admissible…and show that the
  five requirements…force it" → "An admissible allocation statistic must be additive … under the five requirements
  we state"），使摘要从 261 词压到 ≤250 词（paper_audit D-02 现通过）。

### 审计/门禁脚本的同步改动
- `paper3/paper_ieee/audit_pdf.py:447` — summary-row-5 needle `allocationdoesnotbeattheuniformrankplan` →
  `advantageovertheuniformrankplanisnotrobust`（S1 行文本已改）。
- `paper3/paper_ieee/audit_pdf.py:58` — `SUPP_PAGES` 22 → **23**（补充材料 +1 页，见下）。
- `paper3/paper_ieee/audit_check.py:605-611` — `SECTION_POINTER_ANCHORS` 新增 3 条：discussion.tex→S29、
  main.tex→S29、main.tex→S41（新加的主文指针必须登记，否则 "unregistered section pointer" 失败）。
- `supplementary.tex:2229` / `:2262` — `tab:gammarobust` 两表列宽 `p{0.22}/p{0.30}` → `p{0.19}/p{0.27}`；
  `supplementary.tex:2249` — 长 `\texttt noise\_break\_even.rho\_advantage…` 加 `\allowbreak`。
  *Why*：改稿后这两个表出现 3 条 overfull hbox（12.0/14.4/5.7pt），必须清零（B-04）。

### 归档与稿件不一致（按规则**不修改归档**，只记录）
- `outputs/analysis/p3_allocation_paired_stats.json :: conclusion.claim_status.direction` 仍写着
  `"Gamma-guided is lower (worse) than uniform"`，与本文语义相反（lower ΔE = better）。按 lead 规则**保持归档不变**；
  稿件已按正确解释改写。**建议下一轮归档修订时把该字符串改为 "Gamma-guided is lower (better) than uniform"。**

### 编译与门禁结果（base 解释器 `D:\Anaconda\python.exe`）
- `pdflatex main.tex` ×2 → **Output written on main.pdf (10 pages)**；main overfull **0**。
- `pdflatex supplementary.tex` ×2 → **Output written on supplementary.pdf (23 pages)**；overfull **0**；
  float-too-large 0。页数变化：22 → 23（新增 claims 表 3 行；表仅 +1 页）。
- `audit_check.py` → **RESULT: 0 hard failure(s), 0 warning(s)**。
- `audit_pdf.py` → **RESULT: 0 hard failure(s), 0 warning(s)**。
- `tools/_claim_ledger.py --apply` → **通过 96 / 失败 0 / 共 96**（刷新后 paper_audit 的 J-01 警告消失）。
- `paper_audit audit --profile p3_prl --fail-on NONE` →
  **pass=53 fail=1 warn=1**；唯一 fail = **A-01 "uncommitted changes under paper3/paper_ieee"**（未提交，lead 将 review/commit）；
  余下 warn = **I-02 "Package copies match the live manuscript files … frozen submitted package (not compared with
  the live draft)"**（冻结包按规则不比，属预期）。
- `tools/_p1454_final_verify.py --apply` →
  `audit a1_paa: READY fail=0 warn=0`；`paperA_nc: READY`；`paperA_springer: READY`；
  **`audit p3_prl: BLOCKED fail=1 warn=1`**（同上 A-01）；`a23_joe: READY`；`prl_commentary: READY`；
  `p3_audit_check: True`、`p3_audit_pdf: True`；
  `pages: {paper_a1 64, paper合 79, main_springer 56, paper3 10, paper_a2 73, commentary 7} pass: True`；
  **`VERDICT: FAIL | git_clean=False: 26 uncommitted path(s) = 8 pending + 18 leftover audit report(s)`** ——
  FAIL 只由未提交工作树触发（本任务的 8 个待提交文件 + 之前审计留下的 18 个未跟踪 AUD-* 报告），
  其它 5 个 profile 与页数/冻结/整合检查全绿。
- **待 lead 提交的 8 个文件**：`paper3/paper_ieee/main.tex`、`sections/{introduction,conclusion,discussion,experiments}.tex`、
  `paper3/paper_ieee/supplementary/supplementary.tex`、`paper3/paper_ieee/audit_check.py`、`paper3/paper_ieee/audit_pdf.py`
  （另有本笔记 `docs/p3_logic_review_2026-10-25.md` 与本轮生成的 `docs/audits/AUD-p3_prl-*.{json,md}`）。
