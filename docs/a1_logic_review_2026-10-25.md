# A1 逻辑与主张审查（2026-10-25，只读）

**对象**：`paper_a1/`（A1，目标 Pattern Analysis and Applications，`main.tex:21` 的 `\journal{Pattern Analysis and Applications}`）。
**范围**：`main.pdf` 64 页逐页通读（文字层 198,188 字符）+ 源码 `main.tex`(1,510 行)/`related_work.tex`(379)/`abstract.tex`/`title_page.tex` + 归档 `outputs/**`、`outputs/analysis/**` + 台账 `tools/_claim_ledger_a1.py`（今日重跑 **216 pass / 0 fail**）。
**约束**：只读，未改任何稿件；唯一写入本文件。`SUBMISSION/**` 仅作冻结证据引用。
**快照**：HEAD `718290d7`，开始 dirty=0（16:21），结束 dirty=4（其他 agent 在写）。
**任务书稿号勘误**：`NEUCOM-D-26-20952` 是 A1 **早前投 Neurocomputing** 的稿号（后 "Submission Transferred" 到 Neural Networks，以 `NEUNET-D-26-09426` 桌面拒，见 HANDOFF L1920/L2477）。当前 A1 的 PAA Submission ID 是 `0a4629f0-0a6d-45d8-b5b1-3681cc4adc8b`（HANDOFF L1535/L1566/L1683）。

## 1. 核查通过项（明确"对得上"）

| 项目 | 结果 |
|---|---|
| DOI | `main.tex:1472`（Data availability）与 `title_page.tex:36` 均为 **v2.5 `10.5281/zenodo.23632347`** ✓；`paper_a1/*.tex` 无旧 DOI / 旧版本号残留 ✓ |
| 页数陈述 | PDF = 64 页；`cover_letter_paa_revision.tex:28` "64 pages" ✓（v1.0 投稿件 58 页，HANDOFF L1566，属版本差异非行文错误） |
| Supplementary 指针 | **A1 没有补充材料**：全文无 "Supplementary Section S…"/S1–Sn 引用，附录自包含（Appendix A）；**无死指针** ✓（唯一附录问题是编号 bug，见 A2） |
| 摘要数字可溯源 | 32.7/0.028、52.1、62.0、72、48.5/0.0242、−0.154、−0.223、+0.832、−0.143、−0.996、−0.970、0.094 等均被台账断言并落到 `outputs/analysis/*.json` 字段 ✓ |
| 归档完整性 | 稿件引用的 **35 个归档路径全部存在**（逐个 `Path.exists()` 核实，0 缺失）✓ |
| Table 8 / §5.3 数据 | Table 8 六个数来自 `outputs/a1_crossmodel_results.json`（0.9396 / 1.1955 等）；§5.3 真实检查点来自 `a1_e2b_e3b.json::results.E3b_real_checkpoints` 与 `a1_tau_trajectory.json::text_only` ✓ |
| 引言 59.7%/59.3% | `a1_h_offset.json::checkpoints[5].summary_top1_50k = 59.662`（`flickr30k_both_r8`）vs Table 11 的 59.28 ⇒ "0.4 点" ✓（但不在台账 216 条内，见 B2 附注） |
| SOTA 类措辞 | 全文检索 `state-of-the-art / outperform / surpass / novel` = **0 命中** ✓ |
| 摘要 vs 结果 | 摘要中每一条主张都能在 Results/Discussion 找到对应；**没有"只出现在摘要"的对照实验** ✓ |
| Limitation ↔ 控制 | 讨论 (a)–(g) 七条 limitation 每条都有实测控制（(a) Table 2；(b) Table 5/12/13；(c) Table 14；(d) Table 15；(e) 概念性说明；(f) §3 重建披露；(g) Table 9）✓ |

## 2. (a) 投稿前必须修

**A1. PDF 可见的坏交叉引用：`\\ref` 多了一个反斜杠。**
`main.tex:180`：`Corollary~\\ref{cor:lipschitz} matters because ...`（label 在 `main.tex:168`）⇒ PDF 第 13 页印成
**"Corollary refcor:lipschitz matters because the substitutes a practitioner might reach for…"**（"Corollary 2" 的编号丢失、字面 token 泄漏）。且 `cor:lipschitz` 全稿再无正常引用。修：`\\ref` → `\ref`。

**A2. "Appendix Appendix A.n" ×4，且其中三处指针错指到 A.4。**
- `main.tex:70`（引言）："and Appendix Appendix A.3 reports robustness checks"（目标对、词重复）。
- `main.tex:1327`："Appendix Appendix A.4 turns this trade-off into a frontier"（应为 frontier 那一节）。
- `main.tex:1330`："Appendix Appendix A.4 collects the rule variants"（应为 variants 节）。
- `main.tex:1474`："listed in Appendix Appendix A.4"（应为 provenance 表）。
机制：elsarticle 的 appendix 使 `\ref` 输出 "Appendix A.n"（所以 `Appendix~\ref{}` 重复了单词）；而 `app:monitor_variants`/`app:monitor_frontier`/`app:provenance` 三个 label 挂在**无编号** `\section*`（`main.tex:1635/1670/1702`）下，`\ref` 继承最近编号小节 = **A.4 "Graphical abstract"**。PDF 页 3/51/52/56。修：删 4 处 "Appendix~" 前缀；把三个无编号小节编成 A.5/A.6/A.7（或改用显式名称）。

**A3. 摘要把理想化命题写成经验事实（与 Table 3 自相矛盾）。**
`main.tex:41`（摘要）："translating the text side leaves predictions unchanged and moves the gap arbitrarily"。
但 Table 3（`main.tex:500–513`，`tab:asym`）实测 text-side 平移：λ=1 → 45.1%、λ=2 → 38.3%，对比 frozen 59.28%（**−14 / −21 点**）；同一节 §5.5 还说它 "should therefore be markedly less destructive"（相对而言对，但"unchanged"不对）。论文自己在 §4 的 assumptions（`main.tex:459–464`）写明：归一化 embedding 下共同 text 平移只在一阶抵消、二阶仍会扰动排序。修："leaves predictions unchanged **in the unnormalised arithmetic of Proposition 1**; with L2-normalised CLIP text embeddings the effect is second-order and empirically much milder (Table 3)"。

**A4. 结论/引言 "governed by τ" 与本文 "necessary but not sufficient" 自相矛盾。**
- `main.tex:1450`（Conclusion）："zero-shot classification accuracy is governed by the order-preservation coefficient τ"；
- `main.tex:74`（贡献 i）："zero-shot top-1 is governed by τ"；
- `main.tex:455`（Fig. 3 caption）："Accuracy is governed by τ"。
反例就写在 §5.4.1/Table 2：class contraction τ=0.615 时 78.6%，而 Gaussian τ=0.761 时 58.8%（**τ 更低反而更准**）；摘要本身承诺 "necessary but not sufficient"。修：改成 §5.4.1 的措辞 "on the destruction side, accuracy tracks τ"。

**A5. 检索 τ–R@1 相关：同一个量，正文与 Table 20 两个值。**
`main.tex:975`（§5.15）："τ does not track R@1 (Pearson **-0.17**) any better than the gap does (-0.23)"；
Table 20（`main.tex:1175`，`tab:showdown`）："order statistic τ5 … **−0.143**"。
两个归档都真实：`a1_retrieval_evidence.json::correlation.tau_vs_R1 = −0.1657`（**21 个配置**）与 `a1_statistic_showdown.json::retrieval.tau5 = −0.1427`（**17 个配置**）；台账 L168/L224 两条都断言，但正文没说它们是两个不同网格。审稿人对着 Table 20 查 §5.15 就会发现差 0.03。修：择一，或写明"17/21 配置两种口径"。

**A6. iNaturalist / rare-species 两套口径，且一句"not used anywhere"是事实错误。**
- §5.11 Table 10（`main.tex:786–789`）：iNat-wild **718 图 / 48 类 / 11.14**；rare-species **1,000 图 / 50 类 / 16.40**。
- §5.19（`main.tex:1146–1148`）："We add two further local benchmarks that were **not used anywhere in the construction of the argument**: iNaturalist-wild (**50 species**) and a rare-species release"；Table A.25（`main.tex:1539`）：iNat **50 类 / 720 图 / 10.6**；rare **398 类 / 5,000 图 / 26.9**。
问题：(i) iNat-wild 与 rare-species 在 §5.11 已经用过（只是 48/718 与 50/1000 的不同子集），"not used anywhere" 不成立；(ii) 同名 benchmark 两套计数/冻结准确率从未解释。修：明确两套子集（哪一份进 Table 10、哪一份进 Table A.25），并删/改这句话。

## 3. (b) 应当修

**B1. "four controlled experiments" 只列了三项。** `main.tex:70`："We resolve this decoupling with **four** controlled experiments … **First** … **Second** … **Third** …"（缺第四个，即 matched-gap/四控制）。修：补 "Fourth, a matched-gap control …" 或把 four 改 three。

**B2. 摘要相关数字与 §5.5 的口径差异没有衔接（同一量两个数）。**
摘要："gap correlates with accuracy at r=−0.15 … Kendall order statistic reaches +0.83"——这是 Table 20 的 **Pearson**（17 配置，`a1_statistic_showdown.json`）；
§5.5 `main.tex:518`："the Spearman correlation … τ 0.9125 … Centroid Gap **−0.215**"——这是 **26 条件网格的 Spearman**（`outputs/a1_h_baseline_metrics.json::metric_correlations`，已核实 CG=−0.215(n=26)、tau_k5=0.9125）；Table 6 另有 −0.082（stored 单跑）/ −0.1313（5-seed 均值）。
四处都能溯源、§5.7.3/5.7.4 也解释了"stored 不可认证"，但摘要读者会看到 −0.15 与 §5.5 的 −0.215 并列。修：摘要标注 "Pearson r = −0.15 (17-configuration grid)"，并在 §5.5 补一句与 26 条件网格的对照。

**B3. Table 8 的 Centroid Gap 口径未说明，与 Table 16/19 同模型不同值。**
Table 8（`main.tex:731–733`）：CLIP **0.82**（与 Figure 1 的 Flickr30k gap 0.8154 一致）/ OpenCLIP **0.94**（`outputs/a1_crossmodel_results.json` 0.9396）/ SigLIP **1.20**（1.1955）；
而 Table 16/19 与 §5.2/§5.18 给同三个模型 **0.855 / 0.791 / 1.116**（`outputs/analysis/a1_matched_gap_dense.json`：0.8555 / 0.7906 / 1.1155）。
两套都是真实测量（前者似为 Flickr30k 口径、后者为 benchmark 内估计），但 Table 8 caption 没写口径；§5.2 "the absolute centroid gaps in this subsection are slightly larger than in Figure 1" 对 OpenCLIP/SigLIP 的方向反而相反。修：caption 加一句 gap 估计约定。

**B4. Appendix A.3 "widest real pair (6.64 points)" 与 Table 17 的 48.5 点冲突。** `main.tex:1584`：应为 "among the eleven archived checkpoints"，否则与 §5.16/Table 17 的 48.5 点（campaign，72 检查点）并读会矛盾。

**B5. §5.11 把"自一致性"写成"matches measurement"。** `main.tex:791`："the exact bias-field predictor **matches measurement** to better than 5×10⁻⁷ … the difference is **exactly 0**"——这正是 §5.5.3（`main.tex:600+`）自己声明为 self-consistency（两侧都从同一 frozen scores 算出）的那类一致性，此处没有交叉引用。修：加 "(a self-consistency check, Section 5.5.3)"。

**B6. 结论低估了真实检查点证据。** `main.tex:1450`："34 perturbation conditions … plus **seventeen** fine-tuned checkpoints"，而摘要主打的 72 个 LoRA 检查点（§5.16/Table 17）与 12 个 offset 检查点（Table 15）没进结论。修：结论纳入 campaign。

**B7. 全参数微调的对比结论建立在"重建"权重上。** `related_work.tex:166–167`："our observations are qualitatively consistent with it: full fine-tuning damages zero-shot behaviour far more severely than parameter-efficient adaptation." §3（`main.tex:130–135`）却明确说三行 full-FT 是 **reconstructions**（原训练脚本丢失、seed-42 重建已发散：val loss 4.11→7.88、R@1 0.2%）。修：加 "in the reconstructed runs"。

**B8. "best available proxy" 过强。** `main.tex:518`："it is the **best available** proxy for zero-shot health among common metrics"——证据只是本网格上 4 个候选的比较。修："the best of the four candidates tested here"。

## 4. (c) 文字/编号/小瑕疵

- **C1** Table 18 先于 Table 17 被引用（`main.tex:1015` 引 `tab:realpairs`=Table 18，`main.tex:1025` 才引 `tab:campaign`=Table 17），PDF 中两表顺序相反。建议按出现顺序重编。
- **C2** 摘要 "the hidden error is bounded **below** by the margin mass"：方向易误读（Prop 4 给的是"能改变的行数 ≤ mass"的上界，Prop 5 才说明 mass 可达到）。建议 "the error that can be hidden is at least the margin mass"。
- **C3** `main.tex:824` "the paper's **one** unresolved numerical discrepancy"：至少还有 §5.7.3 的 0.926 不可认证、真实检查点 +3.62 点 offset、(a) 的 +0.033/+0.114 协议差；"one" 不准确。
- **C4** 附录结构：`§A.4 Graphical abstract` 之后混放三个 `\section*`（variants / frontier / provenance），既造成 A2 的错指，也让"附录只有 A.1–A.4"的编号与内容不符。建议编成 A.5–A.7。
- **C5** 参考文献顺序：PDF 第 61 页开头 "Hu (LoRA) … Zhang (2026)" 两条在按字母序的列表之前（`main.tex` 中这两条 `\bibitem` 位于 `\begin{thebibliography}` 前部）；不影响引用但排版不齐。另有 Sharma & Saxena (2026) 只有 arXiv 号（`arXiv:2609.36101`），建议标 arXiv 或补 venue。
- **C6** SigLIP frozen top-1：Table 8 印 73.2（=73.15），§5.2 印 73.3（=73.34），差在末位，来自两个归档（`a1_crossmodel_results.json` vs `a1_matched_gap_dense.json`）；建议统一到同一评估。

## 5. 三条最可能被审稿人攻击 / 三条最强

**最弱 W1（操作性）**：监测收益薄。Table A.24 里 τ-max 与"第 1 个 epoch 就停"**打平**（regret 0.05 vs 0.05），因为归档轨迹的 oracle 都在 epoch 1；有内部最优的真实场景只有 12 个 DTD/Food-101 文本塔 run（mass 0.41 vs last-epoch 0.60），且本文自认 τ 不能在同一数据集内给 run 排序。审稿人会问："这套监测在哪个现实场景优于常数基线？"

**最弱 W2（自一致性占比）**：最强的定量一致性（per-class shift r=1.000、τ(λ) MAE 0.0013、五 benchmark "差值正好 0"）都是同一批 frozen scores 的恒等式（论文自己在 §5.5.3 降级）；独立证据只剩 held-out R² 0.371/0.378（ntest=20/4）与 28 条件池。审稿人会追问："去掉自一致性后，'governed by τ' 还剩多少？"

**最弱 W3（matched-gap 的混淆）**：72 检查点 campaign 的最宽 pair 是 **DTD ep3 (8.9%) vs Food-101 ep1 (57.4%)**——跨数据集且跨训练阶段；gap 匹配了，数据集难度/阶段没匹配。加上 archived both_r8 的 gap 有两个口径（+0.033 / +0.114），而招牌例子"gap 变大而准确率几乎不变"取决于取哪个口径。审稿人会要求"同一数据集/同一 run 内"的 matched pair 作为主证据（本文有：19.6 点在 |ΔCG|=0.0125，但被放在次位）。

**最强 S1（理论）**：Theorem 1 + Prop 1/3/4/5 + Corollary 2 把"gap 能否当健康指标"从相关性经验升级为**刻画**：一阶矩统计量恰在 class-neutral 干预上有效；一般情形误差由 margin mass 给出下界且可达到。这是本文最不可替代、也最难被驳倒的部分。

**最强 S2（反例）**：matched-gap dissociation 本身——同 gap（ΔCG=0.028）下 32.7 点、0.038 下 52.1 点；五个 backbone 复现（最高 62.0）；72 个真实 LoRA 检查点 48.5 点 @ ΔCG=0.0242（bootstrap [47.0, 50.0]）。干净、可复算、不依赖新理论。

**最强 S3（诚实度）**：主动把 r=1.000 标为 self-consistency、并列报告 +0.033/+0.114、披露 0.926 不可认证、保留检索负结果与"τ 不能给 run 排位"、把 offset 列为 open question。这类披露通常被审稿人视为可信度加分，也让本文的每个数字可复核。

## 6. 未覆盖 / 限制

- 未做逐条数值复算（除台账 216 条 + 本文点查的 20 余个数字）；未改任何稿件。
- 参考文献只做了抽查（4 条 2026 预印本 + 顺序检查），未逐字段核对（不在本轮范围）。
- 渲染/字体/嵌入未查（属 `paper_audit` 渲染维度，今日 READY）；PDF 与 tex 内容一致性通过 PDF 文字层抽查（未发现 tex≠pdf 的段落）。
- `SUBMISSION/**` 冻结包只读引用（A1 包内 PDF 与 live 的差异属 I-02 门禁范围，不在本审查内）。


---

## Applied fixes（2026-10-25，operator 指示 "全改"，已全部落盘并重建）

**构建结果**：`paper_a1/main.pdf` = **64 页**（`_p1454` 硬约束 ✓），pdflatex ×2 `rc=0`；
`main.log`：`! errors 0 / Undefined control 0 / undefined refs 0 / undefined citations 0 / Overfull hbox 0 / Overfull vbox 0 / LaTeX Warning 0`；
PDF 文字层：`refcor` **0**、`Appendix Appendix` **0**、`not used anywhere` **0**、`leaves predictions unchanged` **0**。
PDF sha256：改前 `d8de0a4b…fe0e`（1,141,891 B / 64 pp）→ 改后 `2019a3d1…3ef8`（1,143,409 B / **64 pp**）。
`main.tex` 1,821 → 1,826 行；`related_work.tex` 409 → 412 行。`SUBMISSION/**` 未动（冻结包哈希不变）。
文件改动：`paper_a1/main.tex`（124 行变更）、`paper_a1/related_work.tex`（4 行）、`paper_a1/main.pdf` + log/aux，及本记录。
（注：`paper_a1/abstract.tex` 的 `M` 状态是**并发他人改动**——其 diff 是把 preamble 更新为当前 main.tex 状态，本任务未写该文件。）

### (a) 投稿前必须修 —— 全部已改

| ID | file:line（当前行号） | change | why |
|---|---|---|---|
| A1 | `main.tex:182` | `Corollary~\\ref{cor:lipschitz}` → `Corollary~\ref{cor:lipschitz}`（去掉重复反斜杠） | PDF 第 13 页原印出 "Corollary **refcor:lipschitz**"；重建后 PDF 中 `refcor` = 0 |
| A2 | `main.tex:70 / 1331 / 1334 / 1479` | 四个 `Appendix~\ref{...}` → `\ref{...}`（去掉 "Appendix~" 前缀） | elsarticle 的 `\ref` 本身输出 "Appendix A.n"，前缀导致 "Appendix Appendix A.n" |
| A2 | `main.tex:1640 / 1675 / 1707` | 三个 `\section*{...}` → `\subsection{...}`（Monitoring rule variants / Risk–compute frontier / Data and code provenance） | 原先挂在无编号 `\section*` 下，三个 `\ref` 全部继承 A.4（Graphical abstract）；现在自动编号 **A.5 / A.6 / A.7**，PDF 中指针分别显示 "Appendix A.5/A.6/A.7" 各 2 次，"Appendix A.4" 仅剩 A.4 标题本身 |
| A3 | `main.tex:41` | 摘要句改为 "a text-side translation moves the gap arbitrarily yet perturbs predictions only at second order (Table~\ref{tab:asym})" | 原句 "leaves predictions unchanged" 与 Table 3 实测（text-side λ=1/2 → 45.1%/38.3% vs frozen 59.28 = **−14/−21 点**）矛盾；现按数据降级并指向 Table 3 |
| A3b | `main.tex:502` | "the benign per-image term" → "the comparatively benign per-image term" | 同上，45.1% 不是 "benign" |
| A4 | `main.tex:76`（贡献 i） | "top-1 **is governed by** τ" → "top-1 **tracks** τ" | 与 §5.4.1 反例（τ=0.615/78.6% 优于 τ=0.761/58.8%）及摘要 "necessary but not sufficient" 一致 |
| A4 | `main.tex:457`（Fig. 3 caption） | "Accuracy is governed by τ" → "**On the destruction side**, accuracy tracks τ" | 同上 |
| A4 | `main.tex:1455`（结论） | "accuracy **is governed by** the order-preservation coefficient τ" → "**tracks** ... **on the destruction side**" | 同上 |
| A5 | `main.tex:977` | 改写为 "Pearson **−0.166** over 21 configurations; **−0.143** over the 17 of Table 20) any better than the gap does (**−0.234**; **−0.223**)" | 原文只给 −0.17/−0.23 且未说两个网格；四个数分别来自 `a1_retrieval_evidence.json::correlation.tau_vs_R1/CG_vs_R1` 与 `a1_statistic_showdown.json::retrieval.tau5/CG` |
| A6 | `main.tex:1150` | 改为 "on larger splits than those of Section 5.11: iNaturalist-wild (**50 species, 720 images**, against the **48-class/718-image** subset used there) and a rare-species release (**398 classes, 5,000 images**, ... against the **1,000-image/50-species** subset used there)"；删除 "**not used anywhere**" | 原句与 §5.11/Table 10 冲突（那里用过 iNat-wild 718/48 与 rare-species 1,000/50），且两套计数从未解释；数字均取自 Table 10 与 Table A.25 |

### (b) 应当修 —— 全部已改

| ID | file:line | change | why |
|---|---|---|---|
| B1 | `main.tex:71` | 补第四项："Fourth, a matched-gap control: cross-family configurations matched on the centroid gap, plus 200 random gap-preserving directions." | 原文 "four controlled experiments" 只列 First/Second/Third |
| B2 | `main.tex:520` | 追加 "(The Pearson values on the 17-configuration grid of Section 5.20 are −0.154 (gap) and +0.832 (τ), Table 20; the two grids are not directly comparable.)" | 摘要 −0.15（Pearson/17 配置）与 §5.5 −0.215（Spearman/26 条件）之间缺桥接；数值取自 Table 20 |
| B3 | `main.tex:727` | Table 8 caption 增补 "The CG values are from this cross-model re-run, not the benchmark-estimated gaps of Tables 16 and 19 (0.855, 0.791, 1.116 for the same three models)." | Table 8 的 0.82/0.94/1.20 与 Table 16/19 的 0.855/0.791/1.116 是两套口径却未说明 |
| B4 | `main.tex:1589` | "the widest real pair (6.64 points)" → "the widest pair **among the eleven archived checkpoints** (6.64 points)" | 否则与 Table 17 的 48.5 点冲突 |
| B5 | `main.tex:793` | "matches measurement" → "**reproduces the measured τ** ... (**a self-consistency check, Section 5.5.3**: both sides use the same frozen scores)" | 该一致性与 §5.5.3 自认的 self-consistency 同类，原措辞会被读成独立验证 |
| B6 | `main.tex:1454` | 结论补 "**and 72 LoRA campaign checkpoints (matched pairs up to 48.5 points at |ΔCG|=0.024)**" | 原结论只算 seventeen，漏掉摘要主打的 72 检查点 campaign |
| B7 | `related_work.tex:168` | 加限定 "**in the reconstructed full-fine-tuning runs of Section 3, whose original training script is lost**" | 三个 full-FT 行是 reconstruction（seed-42 已发散），原句未限定 |
| B8 | `main.tex:520` | "the **best available** proxy ... among common metrics" → "the **best of the four candidates tested here**" | 证据只是 4 候选单网格 |

### (c) 安全项 —— 全部已改

| ID | file:line | change | why |
|---|---|---|---|
| C1 | main.tex 表块顺序 | `tab:campaign` 表块移到 `tab:realpairs` 表块之后 | 原来正文先引 Table 18（realpairs）再引 Table 17（campaign）；交换后 **Table 17 = Real fine-tuned checkpoints（realpairs）、Table 18 = Real LoRA campaign**，正文引用顺序 17→18 ✓ |
| C3 | `main.tex:826` | "the paper's **one** unresolved numerical discrepancy" → "the paper's **most conspicuous** unresolved numerical discrepancy" | 另有 §5.7.3 的 0.926 不可认证、+3.62 点 offset、+0.033/+0.114 协议差 |
| C5 | `main.tex:1772 / 1819 / 1798 / 1813` | 参考文献按字母序重排：Hu(LoRA) 插到 Houlsby 之后、Zhang 插到 Zhai 之后、Sharma 插到 Ramasesh 之后、Yaras 插到 Yamaguchi 之后 | 原来 Hu/Zhang 在列表最前、Sharma/Yaras 附在末尾；PDF 末段顺序现为 Yüksekgönül→Zhai→Zhang→Zhou ✓ |

### 为守住 64 页所做的压缩（lead 授权 "compress within the file"）

- 新增措辞全部用紧凑版（A5/A6/B1/B2/B3/B5/B6 的数字一个未删）。
- 附录 5 个 table 的 `\small` → `\footnotesize`（原 1513/1534/1556/1658/1692 处）。
- 两张图宽度：graphical abstract `0.84→0.74\textwidth`（`main.tex:1622`）、fig6 campaign `0.95→0.88\textwidth`（`:1035`）。
- 摘要压缩后 237 词；再把两处措辞恢复原文（"which can be monitored"、"by dense sweeps"，`main.tex:40/46`）使摘要回到 **241 词**，与冻结包 README 的 "241 abstract words" 一致（消除 I-06 WARN）。
- 两个 `\begin{table}[h]` → `[ht]`（`:1654/:1688`，消除 2 条 float-specifier warning）。
- 结果：**64 页 / 0 errors / 0 undefined / 0 overfull / 0 warnings**。

### 门禁逐字（base 解释器）

```
D:\Anaconda\python.exe -m tools.paper_audit audit --profile a1_paa --fail-on NONE
A1 - Pattern Analysis and Applications (Springer)    BLOCKED  grade D  pass=59 fail=2 warn=0 manual=9 skip=16 error=0
  BLOCKER A-01   P1     uncommitted changes under paper_a1
  BLOCKER I-02   P1     package copies differ from live files
```

- **A-01** = 本轮改动未提交（lead 要求不 commit）：`M paper_a1/main.tex`、`M paper_a1/related_work.tex`（外加 `M paper_a1/abstract.tex` 的**并发他人改动**）。提交后即消失。
- **I-02** = 修订后的 live 稿与 **2026-10-18 已投冻结包**不再一致（`Manuscript.pdf != main.pdf`，**CONTENT differs: pages 64 vs 64, text sha 4cbeaeb819fa vs 1fcf21bbf12e**）。这是"改稿 → 冻结包不动"的必然结果，不是内容缺陷；`_p1454` 已把 `a1_paa` 的 I-02 登记为具名 accepted deviation（task-23）。若要让 `paper_audit` 单独也 READY，需在 `tools/paper_audit/profiles.py` 给 `a1_paa` 加 `package_frozen=True`（与 `a23_joe`/`p3_prl` 同）——该文件不在本任务写入范围，列为建议。

### 残余（明确未做）

1. **Fig. 3 图内标题**（`figures/fig2_tau_top1_crop.pdf` 里的位图文字 "Top-1 is governed by order preservation τ, not by the gap"）仍是 "governed"；LaTeX caption 已改为 "tracks ... on the destruction side"。要改需重新生成该图（`tools/clip_a1_figures.py`），不在本任务范围。
2. `paper_a1/abstract.tex` 的并发改动未纳入本次变更（非本任务所写），也未提交。
3. 未提交任何文件（lead 明确要求）；`SUBMISSION/**` 未动。


---

## 图内标题修复（2026-10-25 补，Fig. 3 / Figure 3）

**问题**：Fig. 3 的**图内标题**仍是 "Top-1 is governed by order preservation τ, not by the gap"，与已改的 LaTeX caption（"tracks … on the destruction side"）不一致。
**修复**：
- `tools/clip_a1_figures.py:79`：`ax.set_title(r'Top-1 is governed by order preservation $\tau$, not by the gap')` → `r'Top-1 tracks $\tau$ on the destruction side, not the gap'`（该脚本的 "Fig 2" 块 = 稿件 Figure 3）。
- `tools/clip_a1_graphical_abstract.py:31`（legacy 脚本，防未来重引入）：`'top-1 is governed by $\tau$, not by the gap'` → `'top-1 tracks $\tau$ on the destruction side, not the gap'`；其 PNG 已被 `_p1276_graphical_abstract.py`（稿件实际使用的 graphical abstract，面板标题 A–D 无 "governed"）取代，故未重生成该 PNG。
- 重生成：`D:\Anaconda\envs\pytorch\python.exe tools/clip_a1_figures.py`（与上次生成同一环境）；**只保留 fig2 的新输出**，fig1/fig4 已从备份原样还原（sha 与改前一致：`20a4ae63…` / `7baf2055…`）。
- **crop 重建**：本机 `pdfcrop` 因符号链接权限失败（`!!! Error: Link from … failed (Operation not permitted)`）；改用等价变换重建——旧 crop 的结构即 `q 1 0 0 1 -11 -11 cm /Im1 Do Q` + MediaBox `[0 0 354 253]`。先用 pypdf 对**旧 full** 施加同一平移/box 得到复现，`pdftoppm -r 150` 渲染比对：**0 / 389,664 像素不同（完全一致）**；再对**新 full** 施加同一变换 → 新 crop 画布 738×528 px 与旧一致，与旧 crop 的像素差异仅在第 **0–18 行（标题带）**，即"只改了标题"。

**证据**：
| 资产 | before | after |
|---|---|---|
| `paper_a1/figures/fig2_tau_top1.pdf` | `b395d33deda033d3…` 40,638 B | `7fa201095644f17b…` 40,625 B |
| `paper_a1/figures/fig2_tau_top1_crop.pdf` | `144e7061621c9d8d…` 40,950 B | `96e32323262d089b…` 48,276 B |
| 图内标题文字 | `Top-1 is governed by order preservation τ, not by the gap` | `Top-1 tracks τ on the destruction side, not the gap` |

**字体硬规则**（`pdffonts`，两文件相同）：只有 `TimesNewRomanPSMT` + `STIXGeneral-Italic`，**CID TrueType**，**无 Type 3** ✓。
**重建**：`paper_a1/main.pdf` = **64 页**，`0 errors / 0 undefined refs / 0 undefined citations / 0 overfull hbox / 0 overfull vbox / 0 LaTeX warnings`。
PDF 文字层可提取新标题（"Top-1 tracks τ on the destruction side, not the gap"），"governed by order preservation" 已消失；全文 `governed` 只剩 2 处合法行文：
"retrieval is governed by the gap rather than by the order statistic"（任务敏感性结论）与 "Order destruction is governed by the dispersion of m_c"（偏置场机制）。
`main.pdf` sha256 `e3764ecf6d16de1a76a1fa8156e25dcdda0f659bd1345e27c5dc55b38e4ffa12`（1,150,814 B）。
**注**：`paper_a1/figures/*.pdf` 被 `.gitignore:15` 的 `*.pdf` 忽略（不入库），跟踪的只有 `fig2_tau_top1.png` 等预览 PNG（已同步更新）；因此 `paper_audit a1_paa` 的 A-01 现在仅由该 PNG 未提交触发，提交即消失。
