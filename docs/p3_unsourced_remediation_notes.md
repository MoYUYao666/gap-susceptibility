# P3 台账 UNSOURCED 清理记录（2026-10-24）

**任务**：把 `tools/_p1637_p3_reproduce_all.py` 台账里的 **45 条 UNSOURCED** 逐条分桶处理，
并修掉 2 条 MISMATCH。本文件是**未来修订信（revision letter）的审计底稿**——
凡"删了哪个数字、为什么删、投稿包里有没有"都以此为准。

**唯一原则**（`AGENTS.md`）：每个印刷数字必须能指名 (a) 脚本、(b) 归档文件与字段；
**无法给出来源的一律删除**，不得保留"待查"，**也不得用别的实验的数值顶替**。

**本次改动范围**：`paper3/paper_ieee/{supplementary/supplementary.tex, sections/*.tex,
sections_full/*.tex, main.tex}` + `tools/_p1637_p3_reproduce_all.py`（仅台账登记）+
本文件。**未改动投稿包** `SUBMISSION/P3_PRL_resubmission/`。

---

## 1. 台账计数（本机实测）

运行：`python tools\_p1637_p3_reproduce_all.py --apply`

| 状态 | 清理前 | 清理后 |
|---|---|---|
| `OK` | 832 | **863** |
| `MISMATCH` | 2 | **0** |
| `UNSOURCED` | **45** | **0** |
| `UNCHECKED` | 0 | 0 |
| `ANALYTIC` | — | 3 |
| `THIRD_PARTY` | — | 8 |
| `APPROXIMATE` | — | 4 |
| `EXTERNAL` | — | 2 |
| `EXEMPT` | — | 3 |
| `DUPLICATE` | — | 6 |
| `DECLARED_GAP` | — | 1 |
| `DELETED` | — | 4 |
| **合计** | 879 | **894** |

**条数由 879 涨到 894（+15）**，来源三处：
- **+13**：桶 (a) 的 12 条原始 UNSOURCED ID 被拆成 **25 条逐数条目**（原先一条登记常含多个数字，
  如 `e-paired-diff` 一条含 4 个数、`s6-real-range` 一条含 4 个数），便于逐数断言；
- **+1**：既有的 OK 条目 `q-real-lo` 原先把印刷的 `-135` 拿去和**无关的**本地重跑（-352）比，
  报 OK 却未真正溯源；现拆为 `q-real-hi`（-135）与 `q-real-lo`（-271），两者都指向
  `p3d_qwen_summary.json::table`；
- **+1**：`c-converge14`，把"ranks $\le14$ converge"独立断言到
  `p3_upgrade_analysis.json::rank_sweep.critical_rank.last_converged_rank`（见 §4，判决后新增）。

台账退出码 0（无 MISMATCH）。新状态词与判定规则写在工具 docstring 的
"Status vocabulary" 一节。`--summary` 现同时给出 MRK（不可复算）列；
"fully sourced sections" 由 30/46 升到 **34/46**。

---

## 2. 分桶总表

**计数口径 = 原先那 45 条 UNSOURCED 台账 ID**（不是清理后的条目数）：

| 桶 | 含义 | 条数 | 稿件是否改动 |
|---|---|---|---|
| **(a)** | 归档存在，台账路径或口径写错 | **14** | 不改（改登记；台账内拆成逐数条目） |
| **(b)** | 归档存在，稿件印错 | **0** | — |
| **(c)** | 第三方 / 近似 / 解析式，正文已如此标注 | **27** | 不改（改登记） |
| **(d)** | 无来源 | **4** | **删数字**（必要时改句） |

14 + 0 + 27 + 4 = 45 ✓

> **桶 (b) 由 2 变 0（判决结果，2026-10-24 晚）**：首轮把 `c-diverge16` / `c-diverge20` 判为
> "稿件印错"，并按 `E2_results.json` 的**非有限**口径把句子改写成
> `ranks $\le20$ converge, all three seeds diverge at $r=24$`。复核后**撤销**该改写：
> 同一句括号里的 crossiing bracket（`between $r=14$ and $r=16$`）与
> `p3_upgrade_analysis.json::rank_sweep.critical_rank` 逐项吻合，该块的"diverge"口径是
> **末端能量越过本批 $E_0=3927$**，`rows[*].n_diverged` 为 r≤14→0、**r=16→2**、r=20→3，
> 原句正是照它写的；改成"≤20 才不发散"会让括号与同句 bracket 自相矛盾，且是用另一个
> run family 的 NaN 口径顶替。详见 §4。

清理后台账的类别计数（与上表对应）：`DELETED` 4 = 桶 (d)；其余 27 条 = 桶 (c)，
按 8 个类别记（`THIRD_PARTY` 8、`DUPLICATE` 6、`APPROXIMATE` 4、`ANALYTIC` 3、`EXEMPT` 3、
`EXTERNAL` 2、`DECLARED_GAP` 1）。

---

## 3. 桶 (a)：归档存在，台账路径或口径错（14 条原始 ID，稿件未改）

台账此前只在少数几个归档里找，**没有找到真正的字段**。逐条指名如下（字段路径为精确路径）。

其中 12 条的**数字**本来就在归档里，另 2 条（`c-diverge16`、`c-diverge20`）是首轮按错误口径
（NaN）读档后误判为"稿件印错"，经复核**撤销改写、稿件保持原句**，另见 §4。

对应的 **12 条原始 UNSOURCED ID**：`c-p6-instruction`、`c-p6-caption`、`e-paired-diff`、
`e-power-hi`、`q-blank-cross`、`s6-real-range`、`s6-real54`、`s32-signed-de`、
`s33-signflip-r7r8`、`s33-signflip-r3r4`、`s33-signflip-r4r5`、`s33-pair-cis`。
下表按清理后的逐数条目列出（含由既有 OK 条目 `q-real-lo` 拆出的两条）。

| 台账 ID | 稿件印刷值 | 归档文件 `::` 字段 | 归档值 | 也在投稿包？ |
|---|---|---|---|---|
| `c-p6-instruction-lo` | `+83.0`（instruction，r=5） | `paper3/scripts/outputs/experiments/verify_r5_s42_lr5e-05_nw_float1_adamw_imgs_e3.json::delta_E` | 83.0 | 是（源 + Manuscript.pdf） |
| `c-p6-instruction-hi` | `-7.5`（instruction，r=6） | `.../verify_r6_s42_lr5e-05_nw_float1_adamw_imgs_e3.json::delta_E` | -7.5 | 是 |
| `c-p6-caption-lo` | `+66.5`（caption，r=5） | `.../verify_r5_s42_lr5e-05_nw_float1_adamw_imgs_cap_e3.json::delta_E` | 66.5 | 是 |
| `c-p6-caption-hi` | `-39.5`（caption，r=6） | `.../verify_r6_s42_lr5e-05_nw_float1_adamw_imgs_cap_e3.json::delta_E` | -39.5 | 是 |
| `e-paired-diff` | `+11.5` | `outputs/analysis/p3_upgrade_analysis.json::theory_vs_random.mean_diff_end_E` | 11.5 | 是 |
| `e-paired-ci-lo` / `-hi` | `[+6.8,+16.2]` | 同上 `::theory_vs_random.ci95.0/1` | 6.75 / 16.25 | 是 |
| `e-power-hi` | `28` | `outputs/analysis/p3_alloc_random_pool.json::variance_decomposition.mixed_pool_sd`（4771.180）代入 `2(z+z)²σ²/3570²` | 28.04 → 28 | 是（PDF） |
| `q-blank-r1` / `-r16` | `-260` / `+179` | `outputs/analysis/p3d_qwen_summary.json::table[blank,1].dE_eval_real.mean` / `table[blank,16]…` | -260.203 / +178.739 | 是 |
| `q-real-hi` / `q-real-lo` | `-135` / `-271` | 同上 `table[real,*].dE_eval_real.mean` 的 max/min（r=16 / r=2） | -134.656 / -270.983 | 是 |
| `s6-real-range-hi/lo` | `+450` / `+194` | `p3d_qwen_summary.json::table[real,*].dE_train.mean` max/min | 449.944 / 193.562 | **是**（投稿版 `supplementary.tex` 与 Supplementary.pdf 同句印 `+194 to +450`） |
| `s6-blank-range-lo/hi` | `-519` / `-185` | 同上 `table[blank,*].dE_train.mean` min/max | -518.918 / -184.500 | **是**（同句印 `-519 to -185`） |
| `s6-real54-r4` / `-r16` | `-554` / `-471` | `outputs/analysis/p3d_qwen_ranksweep_mp50176.json::runs[rank=4,condition=real].dE_train` / `[rank=16,…]` | -554.186 / -471.166 | **是**（投稿版同句印 `real pairs -554, -471`） |
| `s32-signed-b1-de` | `+232.5` | `.../verify_r1_s42_bcexplicit_v1_s6_m5_d4.json::delta_E`（分配 = β=1 的 1/6/5/4） | 232.5 | 否 |
| `s32-signed-b2-de` | `+264.0` | `.../verify_r1_s42_bcexplicit_v1_s7_m5_d3.json::delta_E`（分配 = β=2 的 1/7/5/3） | 264.0 | 否 |
| `s33-signflip-r7r8/r3r4/r4r5` | `p=0.061 / 0.039 / 0.014` | `outputs/analysis/p3_rank_separation_extended.json::separation.pairs[rank_a,rank_b].p_paired_signflip` | 0.060547 / 0.039063 / 0.013672 | 否（S33 为投稿后新增） |
| `s33-ci-78-lo/hi` | `[-77.20,-0.25]` | 同上 `separation.pairs[7,8].ci95_diff.0/1` | -77.20 / -0.25 | 否 |
| `s33-ci-34-lo/hi` | `[-37.35,-7.75]` | 同上 `separation.pairs[3,4].ci95_diff.0/1` | -37.35 / -7.75 | 否 |

**结论**：这 **12 条原始 ID**（清理后台账里对应 25 条逐数条目）**稿件数字本来是对的**，
是台账找错了地方。
两个反复出现的根因，已写进工具注释备后人：
1. `p3d_qwen_summary.json::table` 是**按 (condition, rank) 组织的派生表**，且每个单元有
   **两个不同量**——`dE_train`（补充材料引的 15/54 token 区间）与 `dE_eval_real`
   （正文与 S8 引的 held-out 评测）。只读其中一个就会误判另一个"无归档"。
2. `p3_rank_separation_extended.json` 的**逐对**字段在 `separation.pairs[*]`，
   而 `conclusion` 块只有计数与最小值；只看 `conclusion` 就会误判逐对 p 与 CI"无归档"。

> **投稿包比对口径（复核后修正）**：本表"也在投稿包？"一列以
> `SUBMISSION/P3_PRL_resubmission/LaTeXSource.zip` 的 `sections*/`、`supplementary/supplementary.tex`
> ＋ `Manuscript.pdf` / `Supplementary.pdf` 的文本层为准。复核发现 **`s6-real-range`（`+194 to +450`、
> `-519 to -185`）与 `s6-real54`（`-554` / `-471`）在投稿版补充材料里就印着**（同一句），
> 首轮曾误记为"否"，已改正为"是"；`s32-signed-*` 与 `s33-*` 确实**不在**投稿版
> （投稿版 `supplementary.tex` 只有 17 个 section，无 `tab:siglip`、无 sign-flip 段落）。
> 这三类都是**桶 (a)**——稿件不用改，因此修订信**无需披露**；需要披露的是桶 (d) 的四个删除值
> 与 S11 的 `-0.43 → -0.42`（见 §6、§7）。

---

## 4. `c-diverge16` / `c-diverge20`：首轮误判，已撤销改写（归入桶 (a)，稿件**未改**）

改写位置：`paper3/paper_ieee/sections/conclusion.tex:25-27`

**现状（终稿）**：句子保持投稿版原文——

> places the crossing higher, between $r=14$ and $r=16$ (ranks $\le14$ converge,
> two of three seeds diverge at $r=16$, all three by $r=20$)

**已撤销的改写**：`ranks $\le20$ converge, all three seeds diverge at $r=24$`。

| 台账 ID | 印刷值 | 归档文件 `::` 字段 | 归档值 | 也在投稿包？ |
|---|---|---|---|---|
| `c-converge14` | `ranks $\le14$ converge` | `outputs/analysis/p3_upgrade_analysis.json::rank_sweep.critical_rank.last_converged_rank` | 14 | 是（源 + Manuscript.pdf） |
| `c-diverge16` | `two of three seeds diverge at r=16` | 同上 `::rank_sweep.rows[rank=16].n_diverged` | 2（三条末能量 3810.0 / 5359.0 / 5464.0，后两条越过 $E_0=3927$） | 是 |
| `c-diverge20` | `all three by r=20` | 同上 `::rank_sweep.rows[rank=20].n_diverged` | 3（6585.0 / 6786.0 / 7114.0） | 是 |

**为什么首轮判错**：首轮用 `paper3/scripts/outputs/experiments/E2_results.json::sweep`，把
"diverge" 定义成"轨迹末端**非有限**（NaN）"。按这个口径 r≤20 全为 0/3、首个 3/3 是 r=24，
于是原句被判为"与归档矛盾"。

**为什么撤销**：
1. 同一句括号里的 bracket 是 **crossing 的符号边界**（per-rank 均值 r=14 = $-106.0$ 负、
   r=16 = $+950.7$ 正），它与 `rank_sweep.critical_rank` 的
   `{last_converged_rank: 14, first_majority_diverged_rank: 16, boundary_interval: [14,16],
   partial_divergence_ranks: [16]}` **逐项吻合**——该块就是这个句子的归档摘要；
2. 该 sweep 自己的"diverge"口径就是**末能量越过本批 $E_0$**（`rows[*].n_diverged`：
   r≤14→0、r=16→2、r=20→3），原句照此写成；
3. 改写成"≤20 才不发散"后，括号与同句 `between $r=14$ and $r=16$` **自相矛盾**，且是用
   另一个 run family（$E_0=3921$ 的 NaN 口径）的数去描述这个 $E_0=3927$ 的密扫——
   正是"不得用别的实验的值顶替"所禁止的。

**修订信口径**：这一条**不需要披露**（终稿与投稿版一致）；但首轮那句撤销的改写**不得**再出现，
已由 `audit_check.py` 的 `REMEDIATION_ABSENT` 硬门守住
（针：`all three seeds diverge at $r=24$`），并由 `REMEDIATION_NUMBERS` 守住恢复后的原句。

> 交叉引用：`c-dense-bracket` 断言"crossing 夹在 r=14 与 r=16 之间"依据的是**符号**
> （r=14 均值 −106.0 负、r=16 均值 +950.7 正），与发散计数彼此独立；台账注释里
> "r=16 mixes one finite seed with two collapsed ones"这类旧表述已删除。

---

## 5. 桶 (c)：第三方 / 近似 / 解析式（27 条，稿件未改）

正文**已如此标注**，台账改为对应类别（不再记 UNSOURCED）：

| 类别 | 台账 ID | 说明 |
|---|---|---|
| `THIRD_PARTY`（8） | `f2-mdi-llava`、`f2-mdi-qwen` | Wu et al. 第三方 MDI，正文带 `\cite{wu2025language}` |
| | `t-proj-var`、`t-proj-eps`、`t-identifiability`、`t-ers-k` | Paper 2（伴随研究）数字，P3 归档树外 |
| | `t-intro-r2`、`t-textonly-5` | 伴随研究结论转述 |
| `APPROXIMATE`（4） | `s1-llava-min`（`~34 min/run`） | 带波浪号；最近的归档尺度是 re-run 家族 `elapsed_min`（n=14，均值 31.0，区间 21.3–65.8），同量级但非所述量 |
| | `s1-qwen-min`（`~1--2 min/run`） | 云端逐 run 记录**无**耗时字段 |
| | `s1-cost`（`~$7.5 total`）、`c-usd8`（`~$8 USD`） | 账单数字，归档不存 |
| `ANALYTIC`（3） | `t-c2`、`t-c3`、`t-ode-beta` | KKT 推论 / 符号推论 / 定义式关系，非测量；其实测实例另有 `f4-gamma-*`、`S18`、`S32` 断言 |
| `EXTERNAL`（2） | `c-zenodo-doi`、`m-github` | DOI 与仓库 URL，非可复算数字 |
| `EXEMPT`（3） | `s9-qwen-mse` | `tab:comparison` 为纯文献方法对比表，符合溯源规则的豁免 |
| | `s22-hardware`、`t-ers-plateau` | 声明的局限 / 定性指代，本身不含数字 |
| `DUPLICATE`（6） | `c-five-seed-quote` | 结论里复述的五个 per-seed 值，已在 S12/S13/S22/`f1-five-seed-*` 逐条断言 |
| | `s16-adalora-claim`、`s16-igu-claim`、`s16-signed-claim`、`s16-three-s28` | `tab:claims` 的行引用，数值在 `e-adalora-*`、`s39-arm`、`s32-*`、`s28-*` 断言 |
| | `s8-real-eval` | 补充材料对正文四数的复述，已在 `q-real-hi/lo`、`q-blank-r1/r16` 断言 |
| `DECLARED_GAP`（1） | `s28-steps` | **稿件自己写**"the optimizer step count is not archived"，已核实 `cloud_vqa_full451_*` 确无该字段。诚实声明，不是缺陷 |

---

## 6. 桶 (d)：无来源 → 删除（4 条，已改稿）

**规则**：删数字；句子若因此失去意义就改写；**不得**换用别的实验的值。

| 台账 ID | 删除的数字 | 归档为何不能支撑 | 改后文字 | 也在投稿包？ |
|---|---|---|---|---|
| `f2-llava-surge` | `LLaVA's $46\times$ surge`（连"against"短语一起删） | 同一统计量（秩网格上 per-rank 均值的 max/min）在归档里是 **26.98**（`E2_results.json::sweep`，10 个有限秩）或 **27.19**（`p3_stats_hardened.json::phase_transition`）；`dE(r=16)/|dE(r=4)|` = 14.94；补充材料自己的 $|\Gamma_k|$ 增长是 26×。**没有任何一致读法给出 46**；凑出 46 需把不同协议的块（2859.7/62.3）混用，正是规则禁止的跨实验顶替 | `sections/experiments.tex:132`：`... ranging from $+78$ to $+214$ (a gradual $2.7\times$ increase), and the increase is monotonic ...`（`sections_full/experiments.tex:151` 同步） | **是**（源 + Manuscript.pdf） |
| `e-reversed-p3` | `($p = 0.037$)` | 归档只有六 seed 的 `p3_alloc_results.json::comparisons.inverse_beta_paper_0.137.vs_uniform.p_two_sided = 0.2057`；`p3_allocation_paired_stats.json` **没有** reversed-vs-uniform 块，三 seed 值无处可复算。`outputs/analysis/key_number_check.json` 里的 `0.037` 只是"核对稿面印刷值"的检查表，**不是测量归档** | `sections/experiments.tex:251-252`：`... ($+2470 \pm 4111$, $p = 0.21$); the apparent difference at three seeds we record as a small-sample artefact.`（`sections_full/experiments.tex:355-356` 同步） | **是**（源 + Manuscript.pdf） |
| `c-runs-132` | `132 runs` | 实验树 374 个归档、跨多个 run family；唯一与 run 计数有关的字段是 `p3_alloc_results.json::n_runs_total = 57`，它数的是**容量对齐分配研究**（另一批），不是"present protocol"。任何取数都是台账自定的口径 | `sections/conclusion.tex:19`：`Experimental validation comprises the present protocol together with the capacity-matched allocation study of Section~IV.` | **是**（源 + Manuscript.pdf） |
| `s1-qwen-stack` | `(bitsandbytes 0.49.2)` | 无任何归档字段带库版本：Qwen 云端逐 run 记录无 bitsandbytes 键；LLaVA 记录只有 `compute_dtype`；环境归档 `p3_environment_matrix.json::software_pairs` 的 torch/transformers 都是 `null`（写档时 torch 不可导入）。run 日志里也没有版本行 | 五处 `(bitsandbytes 0.49.2)` 全部删去括号，句子不变：`sections/experiments.tex:7`、`sections_full/experiments.tex:7`、`sections/appendix.tex:31`、`sections_full/appendix.tex:31`、`supplementary/supplementary.tex:78` | **是**（源 4 处 + Manuscript.pdf + 投稿版 Supplementary.pdf） |

---

## 7. 两条 MISMATCH 的处置

| ID | 原状 | 处置 | 也在投稿包？ | 状态 |
|---|---|---|---|---|
| `m-supp-s43` | `main.tex:108` 印 `S1--S43`，补充材料实有 **46** 个编号 section | **已由并发分支修复**：`main.tex:108` 现印 `S1--S46`（22:24 写入），`audit_check.py` / `audit_pdf.py` 的 S1--S46 针同步就位。台账登记改名为 **`m-supp-s46`** 并断言"声明区间 = 文件实际节数 = 46"，旧 id 不再存在以免被误读为"曾经通过" | **否**：投稿版 `main.tex:108` 印的是 `S1--S9`（Manuscript.pdf 亦印 `S1-S9`），`S1--S43` 是投稿后才引入的串 | 已修，台账现 OK |
| `s11-corr-cg` | 补充材料印 `r(rank, CG) = -0.43`，归档 **-0.4247967** | 改印 **`-0.42`**，并在正文注明取整口径：`supplementary.tex:630` → `r(\text{rank},\text{CG}) = -0.42$ (the archive value is $-0.4248$, printed here to two decimals)`。归档：`outputs/analysis/p3_rank_local_control.json`（60 个 checkpoint 上 rank×CG 的 Pearson） | **是**：投稿版 `supplementary/supplementary.tex` 与 Supplementary.pdf 同句印 `-0.43` ⇒ **需在修订信披露**（工作稿纠错，投稿版数字错误） | 已修，台账 OK |

**投稿包里的 S 区间（新发现，需 lead 决定是否披露）**：投稿包的 `main.tex:108` 写
`Supplementary Sections~S1--S9`（Manuscript.pdf 亦印 `S1-S9`），而其
`supplementary/supplementary.tex` 实有 **17** 个编号 section ⇒ **投稿版本本身也存在
"声明区间 ≠ 实际节数"**。当前工作稿的 `S1--S43` 是投稿之后新引入的，投稿包里**没有**这个串。

---

## 8. 编译与审计（改后实测）

| 命令 | 结果 |
|---|---|
| `pdflatex ×2`（`paper3/paper_ieee/main.tex`） | 通过，`main.pdf` **10 页** |
| `pdflatex ×2`（`paper3/paper_ieee/supplementary/supplementary.tex`） | 通过，`supplementary.pdf` **22 页**；PDF 文本层只出现 `-0.42` 与 `-0.4248`，**不再有 `-0.43`** |
| `python tools\_p1637_p3_reproduce_all.py --check --quiet` | **OK 863 / MISMATCH 0 / UNSOURCED 0 / 合计 894**，退出码 0；`--summary` 报 fully sourced sections **34/46** |
| `python paper3\paper_ieee\audit_check.py` | **0 硬失败 / 0 警告**（含新增的主文指针硬门与 remediation 守卫，见 §12） |
| `python paper3\paper_ieee\audit_pdf.py` | **0 硬失败 / 0 警告** |
| `python -m tools.paper_audit audit --profile p3_prl --fail-on NONE` | **READY / grade A**，pass=50 fail=0 warn=0 manual=9 skip=27；报告 `docs/audits/AUD-p3_prl-20261024T145557Z.{md,json}` |
| `python tools\_p1428_provenance_gate.py` | **gate: PASS**（P3 floats=4 manifest=42 missing=0 pending=0 broken_paths=0） |

> 注：首次运行（`AUD-p3_prl-20261024T144339Z`）还报了 `A-04`（PDF 旧于源，起因是并发分支在
> 22:42:45 与 22:45:48 又改了 `sections/discussion.tex` / `sections/conclusion.tex`，晚于当时的编译）。
> 已在 22:49 重编译 `main.pdf`，第二次运行 `A-04` 已消失。
>
> ⚠️ **并发写入实测冲突一次**：22:32 改好的 `sections/conclusion.tex:25-26` 在 22:45:48 被并发分支
> **覆盖回旧文字**，22:49 重新施加；随后 22:52:46 并发分支又写入"$\le20$ / $r=24$"版本，
> **22:54:12 起终稿固定为原句**（见 §4 判决），并已随 `bc3c3fbc` 提交。

### 审计脚本的三处一行修改（**已完成**）

删除 `46×` 后两个硬门曾按旧针搜索而报错；三处已改完并实测通过：

| 文件:行 | 处置 | 状态 |
|---|---|---|
| `paper3/paper_ieee/audit_check.py` | 删除 `("LLaVA surge 46x", "46\\times")` 这一针（`2.7\times` 仍在上一行单独成针），并新增 `REMEDIATION_ABSENT` / `REMEDIATION_NUMBERS` 守卫 | 已改，`audit_check.py` 0 硬失败 |
| `paper3/paper_ieee/audit_pdf.py:159` | 针改为 `2.7increase),andtheincrease`（归一化文本实测命中） | 已改 |
| `paper3/paper_ieee/audit_pdf.py:160` | 删除 `("LLaVA surge 46x", "46surge")` | 已改，`audit_pdf.py` 0 硬失败 |

`A-01`（`paper3/paper_ieee` 未提交）已随 `bc3c3fbc` 提交而消失；提交与编译均已完成。

---

## 9. 遗留发现（**本次未处理**，供 lead 决策）

台账的 `OK` 并**不**等价于"印刷值与归档一致"：条目的比较是
`|复算值 − expected| ≤ tol`，而 `expected` 有的地方被写成了**归档值**而非**印刷值**，
于是"印刷值 ≠ 归档值"也能报 OK（但作者都在 `note` 里如实记了）。
实测：**39 条 OK 条目带非空 caveat**，其中**印刷值与所引归档确实矛盾**的有：

`s6-gap54-pct`（印 50.9%，归档 51.61%）、`s6-gap54-blank`（22,207 / 22,313）、
`s6-gap15-blank`（22,373 / 22,400）、`s6-gap15-real`（21,753 / 21,751.8，超容差 1.18）、
`t-secondorder` 与 `s18-secondorder-3.5`（3.5% / 3.56%）、`s16-curvature`（"低于 0.6%" / 归档 0.73%）、
`s43-mean-r5`/`-r6`（−74.4/+32.1 与 `p3_smolvlm_family.json` 的 −56.375/+3.625 是不同 seed 集，
表内逐 seed 值另有断言）、`s39-target-rank`（印 rank 16 / 归档 `meta.target_rank` 4，**同名不同量**）、
`f1-exact-sign-p`（0.031 / 0.0078125）、`d-swap-n16-energy-p`（9.5e-7 / 6.41e-5）、
`d-swap-n1024-r1-p`（7.6e-6 / 2.14e-4）、`d-real-r1` 与 `d-blank-r1-val`（第四位小数）、
`e-below-3`（分母口径）、`f1-six-configs`（6 / 8）、`s33-ten-at-min`（10 / 12）。

另一类是同性质的**容差约定**问题：`tab-phase-*` 等 26 条 Table II 条目印**整数**、
归档是小数，但 `tol` 取了 `T_EXACT=5e-7` 而非"印刷位半单位"（`T_INT=0.5`）；
印刷值本身是正确取整（−105.17→−105 等），只是比较过严，语义上不可比。

**建议**（未施行）：给条目加一个显式 `printed_value` 字段（印刷串所指数值），
让 `evaluate()` 在 `printed_value` 存在时直接比较它与 `expected`，把上述条目一次性
变成真实的 MISMATCH，再逐条按桶 (b)/(d) 处置。这属于**下一轮**的工作，
本次只把清单与命令留在本文件。

复现命令（只读，不改任何文件）：

```powershell
python -c "import importlib.util,os; spec=importlib.util.spec_from_file_location('led','tools/_p1637_p3_reproduce_all.py'); led=importlib.util.module_from_spec(spec); spec.loader.exec_module(led); print([ (e['id'],e['printed']) for e in led.ENTRIES if led.evaluate(e)[0]=='OK' and (e.get('note') or '').strip() ])"
```

---

## 10. 其他口径说明

- 台账 `where` 字段里的行号是**快照**，稿件每次编辑都会漂移（本次并发分支就在编辑中，
  S33 的引用行号已从 1456 漂到 1530）。**承载判断的是 `src` + `field`**，`where` 只作人读锚点；
  该免责已写进工具 docstring。
- 本文件为中文（`docs/` 汇报类按 `AGENTS.md` 用中文）；稿件与脚本内文字一律英文。

---

## 11. 改后核验清单（全绿才可视为"已做完"）

| 核验项 | 命令 / 判据 | 结果 |
|---|---|---|
| 4 个删除串已消失 | `Select-String` 搜索 `bitsandbytes 0.49.2`、`46\times$ surge`、`$p = 0.037$`、`covers 132 runs`——覆盖 `main.tex` + `sections/*.tex` + `sections_full/*.tex` + `supplementary.tex` | **全部 0 命中**（另由 `audit_check.py::REMEDIATION_ABSENT` 硬门持续守住，含撤销的 `all three seeds diverge at $r=24$`） |
| 修正已在位 | `Experimental validation comprises`（1）、`$2.7\times$ increase), and the`（2）、`difference at three seeds we record`（2）、`\text{CG}) = -0.42$`（1） | **全部命中** |
| 发散句恢复原口径 | `-0.43` 型误改不存在；`two of three seeds diverge at $r=16$` 在 `sections/conclusion.tex`（1） | **命中**（由 `REMEDIATION_NUMBERS` 硬门守住） |
| 主稿编译 | `pdflatex ×2` → `main.pdf` **10 页** | 通过 |
| 补充材料编译 | `pdflatex ×2`（在 `supplementary/` 内） → `supplementary.pdf` **22 页**、**46** 个编号 section | 通过 |
| 补充材料 PDF 文本层 | 只含 `-0.42` / `-0.4248`，无 `-0.43` | 通过 |
| 台账 | `python tools\_p1637_p3_reproduce_all.py --check --quiet` 退出码 0 | **OK 863 / MISMATCH 0 / UNSOURCED 0 / 总 894** |
| 硬门 | `audit_check.py`、`audit_pdf.py` | **各 0 硬失败 / 0 警告** |
| 论文审核 | `paper_audit --profile p3_prl --fail-on NONE` | **READY / grade A**（pass=50 fail=0 warn=0） |
| 溯源门 | `python tools\_p1428_provenance_gate.py` | **gate: PASS** |
| 提交 | `git log --oneline -1` | **`bc3c3fbc`**（含本轮全部稿件与台账改动） |

---

## 12. 收尾分支补做的三项（`bc3c3fbc` 内）

| 项 | 内容 | 验证 |
|---|---|---|
| 主文指针修复 | `sections/discussion.tex`：limitation (4) `Section~S20` → **S21**（"newer model family"，`app:newer`）；limitation (6) `(S29, S37)` → **(S30, S39)**（`app:envcloud` / `app:envvar`）。limitation (5) 的 `Section~S18` 复核为**正确**（`app:hessian`，3.5% 二阶占比） | 按补充材料实际 46 节的标题/`\label` 逐条核对 |
| **新增硬门：主文指针目标** | `audit_check.py` 第 15 节：把 `main.tex` + `sections/*.tex` 里**每个**硬编码 `Section~S<n>` / `(S<n>)` 解析到补充材料**当前** section 列表；`SECTION_POINTER_ANCHORS` 进一步把 10 条指针钉到目标节必须携带的 `\label`（或标题串），并要求**没有未登记的指针**——节次一挪动即硬失败，不再可能"号码还在、指向已错" | `audit_check.py` 输出 3 条 PASS：`every section pointer lies inside S1--S46`（12 个单号指针）、`every registered section pointer still names its section`（10 anchors / 12 sites）、`no unregistered section pointer` |
| **新增硬门：删除值不得回流** | `audit_check.py::REMEDIATION_ABSENT`（5 条：删掉的 `46×`、`bitsandbytes 0.49.2`、`covers 132 runs`、`$p = 0.037$`、以及撤销的 `all three seeds diverge at $r=24$`）+ `REMEDIATION_NUMBERS`（2 条：`-0.42`、恢复后的 `two of three seeds diverge at $r=16$`）；其中 4 条同时出现在投稿包，标注为**修订信条目** | 2 条 PASS |

> 说明：`docs/p3_concurrent_edit_audit.md`（并发写入审计）与本文件同轮产生；本轮稿件改动已全部落地并提交，
> 该文件保留为过程记录。§9 的"39 条 OK 带 caveat / 26 条 tolerance 约定"属于**下一轮**工作，本轮未处理。