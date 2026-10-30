# P3 证据整合批次记录（2026-10-24，会话收尾件）

本文件记录本轮"四份已完成分析的整合"实际改了什么、每个新数字出自哪个归档字段、页数/节数、门禁结果，
以及**未能溯源**与**与源文档不一致**之处。数字若未在此列出字段路径，即为本轮未引入。

---

## 0. 结果一句话

- `supplementary/supplementary.tex`：**43 → 46 节**（新增 S20 / S35 / S46），正文 1741 → **1929 行**，
  编译 **18 → 22 页**。
- `paper3/paper_ieee/main.pdf`：**保持 10 页**（PRL 上限）；为抵消新增句子，在 `sections/experiments.tex`
  内做了 12 处等义压缩（见 §5）。
- 门禁：`tools/_p1428_provenance_gate.py` **PASS**；`audit_check.py` 87 PASS / **1 FAIL**；
  `audit_pdf.py` 218 PASS / **1 FAIL**；`paper_audit --profile p3_prl` **BLOCKED（grade D，2 blocker）**。
  两个 audit 脚本的唯一失败项同源：**`main.tex` 第 108 行的 S1--S43 未更新为 S1--S46**，而 `main.tex`
  不在本轮写入范围（见 §8.1）。

---

## 1. 三个新补充材料小节（`supplementary/supplementary.tex`）

| 小节 | 节号 | 标题行 | 表标签（行） | 来源脚本 | 归档 |
|---|---|---|---|---|---|
| `app:allocation-paired` | **S20** | 978（label 979） | `tab:alloc-paired`（1040） | `tools/_p1634_p3_allocation_paired.py` | `outputs/analysis/p3_allocation_paired_stats.json` |
| `app:rc-boundary` | **S35** | 1561（label 1562） | `tab:rc-boundary`（1610） | `tools/_p1635_p3_rc_family.py` | `outputs/analysis/p3_rc_family_boundary.json` |
| `app:gammarobust` | **S46** | 1863（label 1864） | `tab:gammarobust`（1922） | `tools/_p1636_p3_gamma_robustness.py` | `outputs/analysis/p3_gamma_robustness.json` |

插入位置按源文档指定：S20 在 `\section{Newer model family}` 之前（原 969/970 行之间）；S35 在
`\section{Curvature at high rank}` 之前（原 1488 行前）；S46 在 `\bibliographystyle{IEEEtran}` 之前
（现 1925 行）。三处锚点互不冲突，因此**未做任何顺序调整**。每个小节均有结果表 + caption 末尾
`Source:` 行命名脚本与归档。

### 1.1 S20 的每个数字 → 归档字段

前缀 `outputs/analysis/p3_allocation_paired_stats.json`。

| 稿中数字 | 字段 |
|---|---|
| $-3570.10$ / CI $[-5524.16,-1850.31]$ | `paired.capacity_matched_by_seed.mean_difference`（−3570.0983）/ `.ci95_percentile` |
| 六对全负、无重采样触及 0 | `.n_pairs_negative`=6、`.bootstrap_share_difference_le_zero`=1.0 |
| $t=-3.55$, df $9.64$, $p=0.0055$ | `controls.capacity_matched.welch_unpaired.welch_t/.df/.p_two_sided` |
| 边际 $1899.90$ / TOST $p=0.916$ / 需 $6231.85$ | `equivalence.capacity_matched_tost.margin/.p_tost/.smallest_equivalent_margin` |
| 匹配损失 $+3125.68$、CI $[+368.73,+5882.64]$、$n=2$ | `controls.matched_loss.paired_by_seed.mean_difference/.ci95_percentile/.n_pairs` |
| 匹配损失 TOST $p=0.633$ | `equivalence.matched_loss_tost.p_tost` |
| 池配对 $+1106.47$、CI $[-2493.78,+3883.70]$ | `paired.random_pool_by_seed.mean_difference/.ci95_percentile` |
| 逐方案 $-1869.98$、CI $[-3653.59,-122.78]$ | `paired.random_pool_by_plan.mean_difference/.ci95_percentile` |
| 仅 2 个方案更低（$-2927.76$、$-1699.64$），下一个 $+263.90$ **高于** | `controls.random_pool.plan_deviations_from_gamma_mean.plans_lower_than_gamma_mean`=2、`.per_plan[0..2].difference_from_gamma_mean` |
| 功效不足（内极差 $14{,}331$ vs 方案间 $1870$） | `controls.random_pool.archived_power_diagnosis.max_within_plan_range/.between_plan_mean_diff`；判定 `controls.random_pool.archived_verdict`=UNDERPOWERED_TO_DISTINGUISH |
| 反转规则 $+2470\pm4111$、对均匀 $-2577.34$、CI $[-5418.28,+1255.35]$ | `controls.reversed_rule.arms.inverse_beta_paper_0.137.mean/.sd_ddof1_sample`、`.paired_by_seed_vs_uniform.mean_difference/.ci95_percentile` |
| 表内 5 行（含随机池 $0.357$、反转 $0.628$、$10^{-3}$ 扫描 $-2068.44$、$0.509$） | `equivalence.all_contrasts_summary[*].mean_difference/.ci95_bootstrap/.tost_p_at_margin` |
| $20{,}000$ 次重采样 | `meta.bootstrap.n_boot` |

### 1.2 S35 的每个数字 → 归档字段

前缀 `outputs/analysis/p3_rc_family_boundary.json`。

| 稿中数字 | 字段 |
|---|---|
| LLaVA 主层 $r_c=5.334$、CI $[5.195,5.467]$、括号 5/6 | `rc_by_family.llava-1.5-7b.strata.llava_blank3ep_cloud10.crossing_point`（5.333588）/`.bootstrap.ci95`/`.crossing_bracket` |
| 五种子复跑 $5.260$ | `.strata.llava_rerun5.crossing_point`（5.259887） |
| 8 层跨 $[4.96,46.76]$ | `rc_by_family.llava-1.5-7b.sensitivity_span`=[4.957447, 46.759029]、`.n_strata`=8 |
| 5 backbone / 19 strata；3 有交叉、2 全无、1 单一定义 | `family_list`（5 项）、各 `rc_by_family.<f>.n_strata`（4+8+5+1+1=19）、`conclusion.families_with_a_crossing_in_at_least_one_stratum`、`.families_with_no_crossing_anywhere`（clip-vit-base-patch32、qwen2-vl-7b）、`.families_with_one_well_defined_rc` |
| SmolVLM 单一交叉 $5.699$、CI $[5.556,5.830]$ | `rc_by_family.smolvlm-500m.strata.smolvlm_r5_r6.crossing_point`（5.698748）/`.bootstrap.ci95` |
| AdaLoRA 4/4 更低、逐格 $[-3416.56,-2789.87,-4059.40,-4242.14]$、均值 $-3627.0$、CI $[-4678.5,-2575.5]$ | `adalora_boundary.matched_cells[*].difference_adalora_minus_gamma`、`.summary.mean_difference`（−3626.993653）/`.summary.ci95_t`/`.summary.n_cells_adalora_lower`=4 |
| 符号检验下限 $p=0.125$ | `.summary.exact_sign_test_two_sided_p` |
| 与 uniform 同一 rank plan（rank 4 / 324 模块） | `.comparison_plane.adalora_and_uniform_share_one_rank_plan`=true、`.adalora_config.rank_distribution`={"4":324}、`.adalora_config.n_modules`=324 |
| 预算 $7{,}237{,}632$ | `.comparison_plane.budget_params`（=`.adalora_config.target_budget_params`） |
| 邻域反转 3 格（$+2223$/$+2591$；$+3462$/$+9344$；$-1487$/$+2250$；最大 $5882.6$） | `adalora_boundary.reversal_regime.cells[*].uniform_delta_E/.gamma_delta_E/.difference_gamma_minus_uniform`、`.n_cells_where_plain_uniform_beats_the_gamma_rule`=3 |
| 表 4 行（$-182$/$+3235$、$-84$/$+2706$、$-1468$/$+2591$、$-757$/$+3485$） | `adalora_boundary.matched_cells[*].adalora_delta_E/.gamma_delta_E` |

### 1.3 S46 的每个数字 → 归档字段

前缀 `outputs/analysis/p3_gamma_robustness.json`。

| 稿中数字 | 字段 |
|---|---|
| 每个 rank 10 seed；$r=3,4,5$ 全负、$r=6,7,8$ 全正 | `rank_sensitivity.primary_n_seeds_per_rank`=10、`.sign_split.fully_negative_ranks/.fully_positive_ranks/.crossing_between`=[5,6] |
| 12/15 对逐 seed 同序；例外 $r3$-$r4$、$r4$-$r5$、$r7$-$r8$ | `rank_sensitivity.n_pairs_sign_separated`=12、`.n_pairs`=15、`.non_sign_separated_pairs` |
| Spearman $+1.00$ / $-1.00$ | `batch_sensitivity.ordering_reversal_within_families.extra_spearman/.sweep_spearman` |
| 共享 4 rank、3 个符号不一致、最大分歧 $+383.0$（$r=8$） | `batch_sensitivity.support_counts.n_ranks_shared_by_two_families`=4、`.n_shared_ranks_sign_disagreeing`=3、`.shared_rank_comparison["8"].difference`=383.0 |
| batch size 1→2 保号、缩小 $23.0$–$34.0$、4/4 格 | `batch_sensitivity.batchsize_paired_by_rank["5"].differences`=[−30.5,−23.0]、`["6"].differences`=[−30.5,−34.0]；`.conclusions.n_batchsize_cells_preserving_side_at_bs2`=4、`.n_batchsize_cells`=4 **（字段名与源文档不一致，见 §9.1）** |
| $\rho=0.160$（绑定对 llm_shallow vs llm_mid）、$0.087$、$3.33$ | `noise_break_even.rho_order_flip`/`.rho_order_flip_binding_pair`/`.rho_split_all_pairs`/`.rho_advantage_lost_on_linear_objective` |
| 观测相对 sd $4.227$、$26.4\times$、$0$ of $3$ | `.noise_to_tolerance_ratios.worst_observed_relative_sd`/`.worst_observed_relative_sd_over_rho_order`、`.n_seeds_preserving_point_order`=0、`.n_seeds_available`=3 |
| 计划本身无 break-even（权重→计划映射无档） | `.softmin_weight_check_summary.n_softmin_weights_reproduced`=5、`.n_plans_checked`=5、`.n_archived_plans_reproduced_by_nearest_target_rank`=0、`.verdict` |

---

## 2. 小节重编号（S-pointer）

`sections` 编号是位置式的，插入 3 节后：**旧 S20--S33 → S21--S34，旧 S34--S43 → S36--S45**。
本轮在 `supplementary.tex` 内改了 **19 处**指针（第 875–899 行的 claims 表 + 第 1857 行 SmolVLM caption），
并新增 claims 行 `crossing transfers across backbones` → **(S35)**（第 895 行）。

新增 claims 行内容：`crossing transfers across backbones & not supported & five backbones, nineteen strata:
two contain no crossing anywhere in their measured range, only one yields a single well-defined $r_c$, and
the LLaVA strata span $[4.96,46.76]$ (S35)`。

---

## 3. 两处 caption 对账（任务 2）

| 位置 | 改动 | 依据字段 |
|---|---|---|
| `tab:sharegpt` caption（535–543 行） | 原"sign flip occurs between $r=5$ and $r=6$" → 按归档均值（$r4$ −60.0、$r5$ +2.667、$r6$ +133.5）改为**在 $r=4$ 与 $r=5$ 之间，拟合 4.957**，并写明该曲线**三次过零**（4/5 上穿、32/48 下穿、48/64 上穿） | `rc_by_family.llava-1.5-7b.strata.llava_sharegpt.mean_dE_by_rank`、`.crossing_point`、`.forward_crossings`、`.reverse_crossings` |
| `fig:ers` caption（232–236 行） | 原"earlier than the 3-epoch critical rank" → **"later, not earlier"**，并给出拟合 $46.76$（CI $[45.95,48.77]$） | `.strata.llava_ers_1epoch.crossing_point`（46.759029）、`.bootstrap.ci95` |

**额外（同一缺陷的邻句，任务未点名，为免自相矛盾一并改）**：

- 第 218 行正文 `the mechanism operates earlier:` → `the flip moves to a higher rank:`。
- 547–556 行 `Result.` 段：删去"$r_c\in[5,6]$ reproduces on a second dataset"，改为
  "sign flip reproduces … what reproduces is the existence of a crossing, not its position（4.957）"，
  并把"critical rank is a stable structural property"改为"the transition itself is not"。

---

## 4. 正文修改（`sections/experiments.tex`，428 行）

| 行 | 改动 | 归档字段 |
|---|---|---|
| 246–249 | 原"Three of the ten allocations have a lower mean … the third is lower by 264" → **"Only two … the next plan is $+263.90$ above it, so there is no third lower plan"** | `p3_allocation_paired_stats.json :: controls.random_pool.plan_deviations_from_gamma_mean.plans_lower_than_gamma_mean`=2、`.per_plan[2].difference_from_gamma_mean`=+263.8974609375 |
| 255–257 | $+11.5$ 一句补上归档引用：`(…; archive \texttt{p3\_upgrade\_analysis.json}, field \texttt{theory\_vs\_random.mean\_diff\_end\_E})` | `outputs/analysis/p3_upgrade_analysis.json :: theory_vs_random.mean_diff_end_E`=11.5、`::ci95`=[6.75,16.25] **（上限舍入见 §9.2）** |
| 278–284 | AdaLoRA 让步段追加两句边界：**参数完全相同**（同一 rank plan，rank 4 / 324 模块）与**邻域反转**（plain uniform 在 3 个归档单元胜出：$3\times10^{-4}$ 两个 seed、$10^{-3}$ seed 123） | `p3_rc_family_boundary.json :: adalora_boundary.comparison_plane.adalora_and_uniform_share_one_rank_plan`、`.reversal_regime.cells`、`.n_cells_where_plain_uniform_beats_the_gamma_rule`=3 |

---

## 5. 为守住 10 页所做的等义压缩（`sections/experiments.tex`，未删任何数字/主张）

行号均为压缩后的行：119、135–137、148–150、200–202、226–228、234、289–292、404–408、412–419
（另含 246–249、278–284 两处本身即为上表改动）。共 12 处，净 −9 行（437 → 428 行）。
改动性质：删除与图注/前文重复的从句、合并同义句。所有 `audit_check.KEY_NUMBERS` 与
`audit_pdf.MAIN_CHECKS` 针点经复跑确认仍全部命中（唯一例外见 §7 注）。

---

## 6. 被取代的长版（任务 3 第 4 项）

`paper3/paper_ieee/sections_full/experiments.tex` 第 331–334 行：**两件事都做了**——
把 `+1478` 改为 `+1477`，并在上方加 3 行 `%` 注释说明该文件为 superseded、原值是归档均值
1477.4501953125 的舍入产物（引 `p3_allocation_paired_stats.json :: rounding_artefacts.printed_plus_1478_vs_archive`）。
`audit_check.py` 新增硬检查：该文件必须含 `+1477 \pm 1563`、不得含 `+1478 \pm 1563`（均通过）。

---

## 7. 门禁结果（本轮实测）

| 门禁 | 命令 | 结果 |
|---|---|---|
| 溯源门禁 | `python tools/_p1428_provenance_gate.py` | **PASS**（P3 floats=4 / manifest=42，missing=0 pending=0 broken=0）→ exit 0 |
| 源审计 | `python paper3/paper_ieee/audit_check.py` | **87 PASS / 1 FAIL**（88 项）→ exit 1 |
| PDF 审计 | `python paper3/paper_ieee/audit_pdf.py` | **218 PASS / 1 FAIL**（219 项）→ exit 1 |
| paper_audit | `python -m tools.paper_audit audit --profile p3_prl --fail-on NONE` | **BLOCKED / grade D**：pass=48 fail=2 warn=0 manual=9 skip=27 error=0 → exit 0 |

- 两个 audit 脚本的**唯一失败项同源**：main 文本仍声明 `Supplementary Sections~S1--S43`（应为 S1--S46）。
  这是唯一需要越界修改的一项，见 §8.1。
- `paper_audit` 的 2 个 blocker：`A-01`（paper3/paper_ieee 下有未提交改动——本轮的改动本身）与
  `F-05`（上述 2 个一致性门禁失败）。报告落在 `docs/audits/AUD-p3_prl-20261024T142040Z.{json,md}`
  （工具自带的归档副作用）。
- 注：`audit_pdf.MAIN_CHECKS` 中 `-4.6% / -36.8%` 原为一个连续针点；本轮压缩使 Fig. 2 移到该栏顶端，
  pdftotext 两值之间被图注截断，故改为两个独立针点（两个值仍都必须出现）——这是**版式**变化，不是数值变化。

---

## 8. 未做 / 未能处理

### 8.1 越界阻塞项（需写入范围外的一次改动）

`paper3/paper_ieee/main.tex` 第 108 行仍是 `Supplementary Sections~S1--S43`，应为 **S1--S46**。
`main.tex` 不在本轮 WRITE SCOPE（"Nothing else"），故**未改**；两个 audit 脚本与 `paper_audit` 因此各报 1 项失败。
一并需要改的还有 `paper3/paper_ieee/sections/discussion.tex` 第 61 行 `Section~S20` → **S21**
与第 71 行 `(S29, S37)` → **(S30, S39)**（同为范围外）。

### 8.2 数字上未能溯源的项

- **无新增数字缺失来源**：本轮引入的每个数字都在 §1 有字段路径。
- 但正文散文中的数字（如 $+263.90$、3 archived cells、324 modules）**未在 letter 内逐条写 Source**——
  与既有正文惯例一致（letter 只写结果，字段路径在补充材料 caption 的 `Source:` 行与
  `docs/provenance_manifest.json` 内）。若要求 letter 内也逐条标注，需要额外版面（当前 10 页已满）。

### 8.3 归档里确实没有的东西（因此未写入）

- peft 是否真的施加了 `orth_reg_weight=0.5` 正交正则：无任何归档记录（rc 文档 caveat 7(i)），未断言。
- 预注册的等价边际不存在：稿中已明写边际是 data-derived（$1899.90$），未称作预注册。
- 随机池除 42/123/456 之外没有 per-seed 归档，因此无法做六 seed 的方案配对。

---

## 9. 与源文档不一致之处（已按归档更正，未静默）

### 9.1 `docs/p3_gamma_robustness_text.md` §3 的字段名错了

该文档把"batch size 1→2 使效应缩小 23.0–34.0"归到
`batch_sensitivity.batchsize_paired_by_rank.{5,6}.mean_difference`；但该字段实为 **−26.75 / −32.25**（两环境均值）。
23.0–34.0 来自 `.batchsize_paired_by_rank["5"].differences` = [−30.5, −23.0] 与 `["6"].differences` = [−30.5, −34.0]。
本轮稿中数字仍为 23.0–34.0（正确），manifest 与审计针点引用的是 **`.differences`**。

### 9.2 `+11.5` 的 CI 上限不是逐位相同

`p3_upgrade_analysis.json :: theory_vs_random.ci95` = **[6.75, 16.25]**，稿中印 **`[+6.8, +16.2]`**。
均值 11.5 逐位相同；上限按 round-half-even（16.25→16.2）而非 round-half-up（→16.3）。按指令
**未改数字**，仅在正文补了归档引用，并在此记录该舍入差异。

### 9.3 舍入位数

任务书给出两位小数（−3570.10、−5524.16/−1850.31、1899.90、6231.85、+3125.68、+368.73/+5882.64），
而 `docs/p3_allocation_text.md` 的草稿用整数（−3570、−5524、+3126…）。两者都是对同一归档值的舍入；
本轮统一采用**两位小数**（更贴近归档字段原值），表与正文一致。

---

## 10. 本轮写入的文件

| 文件 | 变化 |
|---|---|
| `paper3/paper_ieee/supplementary/supplementary.tex` | 1741 → 1929 行；43 → 46 节 |
| `paper3/paper_ieee/sections/experiments.tex` | 437 → 428 行（3 处规定修改 + 12 处守页压缩） |
| `paper3/paper_ieee/sections_full/experiments.tex` | 331–334 行：+1478 → +1477 并加注释 |
| `paper3/paper_ieee/audit_check.py` | 新增 EVIDENCE_* 针点/缺失针点、S-pointer 范围检查、sections_full 检查；节数 43 → 46 |
| `paper3/paper_ieee/audit_pdf.py` | `SUPP_PAGES` 18 → 22、`SUPP_SECTIONS` → S1–S46、新增 `SUPP_EVIDENCE_VALUES/ABSENT` |
| `docs/provenance_manifest.json` | P3 floats 39 → 42（新增 `tab:alloc-paired`、`tab:rc-boundary`、`tab:gammarobust`，各带 `fields` 字段路径） |
| `docs/p3_evidence_integration_notes.md` | 本文件 |
| （副作用）`docs/audits/AUD-p3_prl-20261024T142040Z.{json,md}` | `paper_audit` 运行自带的归档 |

未触碰：`SUBMISSION/**`、`HANDOFF.md`、`文件地图.md`、其他论文、任何分析脚本、`main.tex`、
`sections/discussion.tex`。工作区另有**本轮之前就存在**的未提交改动 `tools/_p1637_p3_reproduce_all.py`（非本轮所为）。