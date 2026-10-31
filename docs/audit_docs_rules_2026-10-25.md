# 独立审计 C：交接文档、数字可追溯性与常设规则（2026-10-25）

> **task-21 交付件**。审计者：`p3-stats`（独立于本轮交接文档作者）。
> **范围**：`HANDOFF.md` / `文件地图.md` 的 2026-10-25 条目、今日稿件数字溯源、五条常设规则、
> 今日 `docs/`+`tools/` 变动清单。**只读审计**：除本文件外未改动任何交付物、文档或稿件。
> **审计时点**：2026-10-25 11:16–11:45（Asia/Shanghai）。方法：全部结论用脚本/命令复核，
> 证据落在 `outputs/analysis/audit_docs_rules_facts.json`、`outputs/analysis/audit_rules_facts.json`、
> `outputs/analysis/audit_traceability.json`，复现命令见 §7。

---

## 0. 结论摘要

| 维度 | 结论 |
|---|---|
| 交接文档页数/计数声明 | **全部属实**（7 个 PDF 页数 64 / 79 / 56 / 10 / **26** / 73 / 7；P3 补充 26 页 / 50 表 / 46 节） |
| 交接文档"还剩什么" | **不完整（blocking）**：漏掉"官方 IGU 对比结果尚未写入任何稿件"这一实质待办 |
| 交接文档内部一致性 | **2 处过期陈述未标注**（`文件地图.md` L15、L65/L102） |
| 数字可追溯性 | **26/26 全对**（稿件值 = 归档字段 = Source 脚本）；另有 6 个今日头条数字**只在归档/笔记，未进稿件** |
| 常设规则 (a)–(e) | (a) 通过；(b) 今日无新图（抽查最近图为 Times/STIX，合规）；(c) 通过（1 个新脚本含中文 payload，cosmetic）；(d) **缺"来源 URL + 核实日期"列（should-fix）**；(e) 通过（无 tag 被移动；v2.5 属新版本路径） |
| 今日文档/工具清单 | 14 篇非审计文档 + 114 个生成式审计产物 + 39 个工具条目（含 9 个 `.pyc`）；**5 篇 A23 笔记/3 篇 P3 笔记/2 篇 V25 就绪文档构成平行文档**；**7 组工具编号撞号** |

**分级计数**：blocking **1** ｜ should-fix **6** ｜ cosmetic **6**（另有 1 项初判后自核实为非问题，见 C5）。

---

## 1. 交接文档一致性（逐条核对）

### 1.1 页数声明（全部通过）

`pdfinfo` + 对应 `.log` 双向核对（命令见 §7.1）：

| 稿件 | 声明 | `pdfinfo` | `.log` | 判定 |
|---|---|---|---|---|
| A1 `paper_a1/main.pdf` | 64 | 64 | 64 | ✅ |
| Paper A `paper合/main_nc.pdf` | 79 | 79 | 79 | ✅ |
| Paper A `paper合/main_springer.pdf` | 56 | 56 | 56 | ✅ |
| P3 `paper3/paper_ieee/main.pdf` | 10 | 10 | 10 | ✅ |
| P3 补充 `supplementary/supplementary.pdf` | 26 | 26 | 26 | ✅ |
| A23 `paper_a2/main_ieee.pdf` | 73 | 73 | 73（1,275,901 B，声明一致）| ✅ |
| Commentary `paper_review_prl/main_prl.pdf` | 7 | 7 | 7 | ✅ |

### 1.2 P3 补充材料结构（全部通过）

`supplementary.tex`：`\section{` × **46**；`\begin{table*?}` × **50**；`supplementary.pdf` **26 页**。
与 `文件地图.md:9`、`HANDOFF.md` 今日条目逐项一致；`main.tex` 的 `S1--S46` 指针仍正确（两审计已验）。

### 1.3 两个云端作业"均已执行完毕"（通过）

- **官方 IGU 六臂**：`outputs/analysis/p3_official_igu_run.json :: runs[]` 实际 **6** 条 ✅
- **POPE 第二下游**：`outputs/analysis/p3_second_downstream.json` 存在，`acceptance.refs_match_prepared_parquet_order`
  = true，`paper3/test-pope-random.parquet` 61,909 B / sha256 `66faa5e6…` 与逐臂 meta 一致 ✅
- **取回 47/48 校验**：`cloud_retrieved/round2_2026-10-25/verify_round2c.json :: n_failures = 1` ✅；
  唯一失败的 `logs/plan_recheck_20261025.log` 实际 **0 字节** ✅（与交接文档"被中断截断为 0 B"一致）
- **实例已停**：本地无网络凭据，"端口关闭"无法复核（见 §6 局限）；交接文档已诚实标注由另一 agent 执行 shutdown。

### 1.4 A23 下一版修订包内容（通过）

`SUBMISSION/A23_JOE_next_revision/` 7 个文件、`SHA256SUMS.txt` 覆盖齐全；`README.md` 明确列出
**Cover letter / TitlePage / Abstract 均为 "not supplied"**，并说明"revision letter is still to be written"
⇒ 与交接文档"唯一剩余：A23 cover letter"一致 ✅。
（`SUBMISSION/_venue_builds/A23_JOE_next/CoverLetter.pdf` 是 2026-10-24 17:17 的旧构建，不是下一版修订信，不构成矛盾。）

### 1.5 "还剩什么"（**blocking：不完整**）

- `HANDOFF.md:99-101` 的待办：① push+tag+DOI **已完成**；② `tools/` 行号引用未受影响；③ 云端侧无待办；
  ④ **唯一剩余：A23 cover letter**。
- `文件地图.md:17-22`：① v2.5 发布已划删除线标完成，② 只剩 "A23 下一版修订的 cover letter（现在唯一剩余）"。
- **但**：官方 IGU 对比判定 `small`（配对 **−59.5**、CI **[−150.5,−8.0]**、margin **196.05**、L1=2/16）
  只存在于**归档与笔记**：全稿件 grep `196.05` / `150.5` 均 **0 命中**；S41（`app:iguofficial`）
  只报告分配阶段（rank sum、训练臂 `+240.5`），**不含**对比判定。
- 而 `docs/P3_OFFICIAL_IGU_PLAN.md` §8（L187-196）明确要求：`small` 判定应把替换 caveat 的英文句
  写入稿件正文与表注；`docs/p3_cloud_round2_notes.md:558` 也仍写"**建议进稿句**"（即尚未进稿）。
- ⇒ 新操作者按待办清单会认为"稿件已收尾，只剩 cover letter"，**实际还有一处已归档结果未入稿**。
  **建议**：要么补进 P3 补充材料（S28/S41 表注 + 正文），要么在待办里显式写"官方 IGU 对比：归档完成，
  稿件整合按 lead 决定是否执行（当前未执行）"。

### 1.6 过期/矛盾陈述（可复核清单）

| # | 位置 | 陈述 | 与文件矛盾之处 | 级别 |
|---|---|---|---|---|
| 1 | `文件地图.md:15` | 发布：`publish_clean` 第三提交（基线 `5ad7724`），**未 push / 未 tag** | `git -C publish_clean log --oneline -1` = `e66094c`；tag `v2.5` 已建（11:13）；`gh release list` = v2.5 **Latest**；同文件 L18-21 已写"已完成"但表格行未加删除线/过期标注 | should-fix |
| 2 | `文件地图.md:65`、`:102` | `paper合` main_nc **67 页**、main_springer **49 页**；L102 另写 NC **68 页** | 当前 PDF 为 **79 / 56**；同文件 L191/L322 对旧页数有"已过期"标注，但 L65/L102 没有 | should-fix |
| 3 | `文件地图.md:9` | P3 补充证据引 `supplementary.log`：**"26 pages, 433931 bytes"** | 当前 log 实为 **"26 pages, 434348 bytes"**（措辞改动后重编，页/表/节计数未变） | cosmetic |
| 4 | `文件地图.md:11`、`HANDOFF.md:9` | POPE 结果标题为"指标依赖结果" | 子节已于 11:03–11:05 改为 **verdict 先行**（`The pre-declared criterion is met … supports_the_adapters`，再给指标分裂）；标题未同步措辞（内容不矛盾，只是未反映新结构） | cosmetic |
| 5 | `HANDOFF.md:86-96`（§6） | 已把旧"未 push/未 tag"**划删除线并标"已过期"**，补正为 `e66094c`/tag/Release/DOI `23632347` | 与仓库事实**一致**（tag 对象 `03e6cebf…`→`e66094c`；Release Latest；DOI 在 `publish_clean/README.md`、`RELEASE_NOTES_v2.5.md`、`docs/P3_SUBMISSION_STATUS.md` 均已回填） | ✅ 正确示范 |

---

## 2. 数字可追溯性抽查（**26/26 通过**）

规则：稿件值 ↔（表注/正文）Source 行指名的脚本 ↔ 归档字段，三者必须一致。
脚本 `tools/_p1658_audit_traceability.py` 逐条重读归档字段并格式化比对；结果 JSON：
`outputs/analysis/audit_traceability.json`。

| # | 稿件位置 | 数字 | 归档字段 | 判定 |
|---|---|---|---|---|
| T1 | `supplementary.tex:81` | 环境份额 **49.59%** | `p3_env_stack_seeds.json :: sigma_by_rank.5.all_rows.env_variance_share` = 0.4959454 | ✅ |
| T2 | `supplementary.tex:1892`；`sections/discussion.tex:73` | σ_env **32.46** / σ_seed **32.72** | 同上 `sigma_env`/`sigma_seed` = 32.46019 / 32.72449 | ✅ |
| T3 | `supplementary.tex:1893` | CI **[35.8%, 74.9%]** | 同上 `bootstrap.share_ci95` = [0.358248, 0.748657] | ✅ |
| T4 | `supplementary.tex:102`、`:1063-1064` | **−3570.10**，CI **[−5524.16, −1850.31]** | `p3_allocation_paired_stats.json :: paired.capacity_matched_by_seed.{mean_difference,ci95_percentile}` | ✅ |
| T5 | `supplementary.tex:111`、`:2071-2072` | ρ **0.160**、相对 sd **4.227**、比值 **26.4** | `p3_gamma_robustness.json :: noise_break_even.rho_order_flip`=0.16001、`…noise_to_tolerance_ratios.worst_observed_relative_sd`=4.22672（比值 26.4 由两者相除） | ✅ |
| T6 | `supplementary.tex:76` | 八层跨 rank 跨度 **[4.96, 46.76]** | `p3_rc_family_boundary.json :: rc_by_family.llava-1.5-7b.sensitivity_span` = [4.957447, 46.759029] | ✅ |
| T7 | `paper_a2/ext_partII_domains.tex:126-127` | **4940** 条、**29** 条存活 | `a23_multiencoder_transfer.json :: conclusion.n_scored_entries_cross_unit`=4940、`n_entries_surviving_bootstrap`=29 | ✅ |
| T8 | `supplementary.tex:1447` | POPE accuracy base−r5 **−0.2460** CI **[−0.2627,−0.2297]** | `p3_second_downstream.json :: contrasts.base_minus_5.accuracy.{delta,ci95}` | ✅ |
| T9 | `supplementary.tex:1449` | token F1 base−r6 **−0.1583** CI **[−0.1731,−0.1438]** | `…contrasts.base_minus_6.token_f1.*` | ✅ |
| T10 | `supplementary.tex:1428-1430` | yes-class F1 **0.8849 / 0.8593 / 0.8237** | `…arms.{base,5,6}.pope_f1` | ✅ |
| T11 | 同上 | yes 率 **0.4327 / 0.4123 / 0.3733** | `…arms.{base,5,6}.yes_ratio` | ✅ |
| T12 | `supplementary.tex:1459` | 漏判 **262 / 324 / 421** | 逐臂归档 `p3_second_downstream_{base,5,6}.json :: confusion.fn` | ✅ |

**Source 脚本存在性**：26 条中所有 Source 行指名的脚本均存在（0 缺失）；
归档 `meta.script` 与 Source 行一致的 15 条、不一致 0 条。

**归档但未进稿的今日头条数字**（6 项，均与归档一致、与稿件无关）：

| 数字 | 归档字段 | 稿件出现 |
|---|---|---|
| 官方 IGU 配对差 **−59.5** | `p3_official_vs_reimpl.json :: overall.mean_gap_delta_E` | ❌（`supplementary.tex:532` 的 −59.5 是无关的 n=64/r=5 表格单元）|
| CI 下界 **−150.5** | `…overall.ci95[0]` | ❌ |
| CI 上界 **−8.0** | `…overall.ci95[1]` | ❌ |
| margin **196.05** | `…meta.margin` | ❌ |
| 复现极差 **132.0** | `p3_official_igu_replicates.json :: summary.max_spread_across_arms` | ❌ |
| 复现均值 **76.1** | `…summary.mean_spread_across_arms` = 76.0833 | ❌ |

⇒ 与 §1.5 的 blocking 发现互为证据：**结果是真的、归档是齐的，只是没进稿，而待办清单没写**。

---

## 3. 常设规则抽查

### (a) 上传文件名不含下划线 —— **通过**

扫描**已暂存的上传包**（`SUBMISSION/A23_JOE_next_revision`、`SUBMISSION/_venue_builds/*_next`）中
实际上传文件（`.pdf/.docx/.zip`，排除 README/SHA256SUMS/EM_FIELDS 等打包内部说明）：
**36 个上传文件，0 个含下划线**。文件名均为 `Manuscript.pdf`、`Supplementary.pdf`、`CoverLetter.pdf`、
`TitlePage.pdf`、`Highlights.pdf`、`Abstract.pdf`、`LaTeXSource.zip`。
（`SUBMISSION/` 下旧目录里的 `latex_source.zip`、`Abstract_portal.txt` 等是**历史投稿件/内部注记**，不是本轮待上传文件；
规则只约束"上传文件名"，且脚本 `_p1336_build_venue_package.py` 已统一重命名。）

### (b) 今日重生成图的字体 —— **今日无新图（未触发）**，抽查最近图合格

全仓库今日修改的图 PDF：**0 个**（`paper合/figures/` 最新 `fig4.pdf` = 2026-10-24 14:29）。
抽查该最近图：`pdffonts paper合/figures/fig4.pdf` → **TimesNewRomanPSMT + STIXGeneral-Regular，
均 CID TrueType、无 Type 3** ⇒ 规则满足。
（若今日确有图重生成但落在未扫描目录，本条结论降级为"未触发"。）

### (c) 语言规则 —— **通过（1 处 cosmetic）**

- 今日**新建**（untracked）文件中含 CJK 的 18 个：**全部**是 `docs/audits/AUD-*.json/.md` 生成式审计产物，
  其中 CJK 仅出现于真实文件名 `文件地图.md`（如 `"title": "HANDOFF.md and 文件地图.md record the current status"`）
  ⇒ 属"功能数据（真实文件名）"豁免 ✅
- 今日**修改**的 tracked 代码/归档中含 CJK 的新增内容：**0**
- 新脚本 `tools/_p1652_backfill_v25_doi.py`（untracked，627 个 CJK 字符）含约 50 行**中文 payload 字符串**，
  这些字符串是要写入中文交接文档（`HANDOFF.md`/`文件地图.md`）的正文 ⇒ 属"面向中文文档的内容"，
  但按语言规则"代码里的字符串"字面要求英文，**建议**：在脚本头加注释说明该豁免，或把 payload 移到数据文件。**cosmetic**
- 既有 83 个 `outputs/analysis/*.json` 今日 mtime 变化但内容未变（`git status` 无修改）⇒ 历史存量，范围裁决"只管今后"✅

### (d) SCI 期刊登记 —— **不完整（should-fix）**

`docs/VENUE_SCI_REGISTRY.md`（4,609 B，2026-10-24 20:36）存在，五篇目标刊物齐全、
ISSN/出版商/SCIE 均列出（Neurocomputing 0925-2312；PAA 1433-7541；PRL 0167-8655；IEEE JOE 0364-9059；
Commentary=PRL），并有备选/待核/已剔除名单。
**但**：五篇的登记行**缺"核实来源 URL"与"核实日期"两列**，且文档 L30-33 自述
"**尚未按 §2 用 MJL 逐条复核**"（L33-35）。按规则第 2 条（"投稿前必须核实并留痕：刊名/ISSN/出版商/SCIE/URL/日期"），
下一次投稿或改投前必须补 $\Rightarrow$ **should-fix**（文档已诚实自述，属"已知未完成"而非虚报）。

### (e) DOI / tag 冻结 —— **通过**

- `publish_clean` tag 列表：`v1.0-prl-revision`(2026-10-13)、`v2.0`(10-20)、`v2.1`(10-21)、`v2.2`(10-21)、
  `v2.3`(10-24)、`v2.4`(10-24)、**`v2.5`(2026-10-25 11:13)**。
  各 ref 文件 mtime = 各自创建时间，**无一个旧 tag 在今日被重写** ✅
- `v2.5` 是**新版本新 tag**（规则 #2 允许），注解对象 `03e6cebf…` 指向 `e66094c`；
  `gh release list --repo MoYUYao666/gap-susceptibility` → **v2.5 标 Latest**（2026-10-25T03:19:51Z）✅
- Zenodo v2.5 版本 DOI **`10.5281/zenodo.23632347`**（concept `23341082`）已回填
  `publish_clean/README.md`（徽章+Latest DOI）、`publish_clean/RELEASE_NOTES_v2.5.md`、
  `docs/P3_SUBMISSION_STATUS.md:42` ✅
- 仅 cosmetic：`AGENTS.md` 新增的"补充铁律（2026-10-25 立，因 v2.5 漏发 Release）"叙述的是**修复前**
  状态（"Zenodo 没有铸出新版本 DOI"）；该问题已于 11:19–11:24 修复（Release+DOI+回填）。规则正文未标注"已修复"，
  新读者可能误以为当前仍无 v2.5 DOI。**cosmetic**，建议补一句"已于同日修复，见 HANDOFF §6"。

---

## 4. 今日文档与工具清单（含平行/重复文档）

### 4.1 `docs/` 非生成式文档（14 个，均为今日创建/修改）

| 文件 | 大小 | mtime | 主题 |
|---|---|---|---|
| `p3_env_seeds_integration_notes.md` | 11,193 | 07:23 | P3 环境种子 |
| `a23_multiencoder_rerun_notes.md` | 19,987 | 07:36 | A23 多编码器重跑 |
| `a23_multiencoder_cloud_notes.md` | 32,331 | 08:13 | A23 多编码器云端 |
| `a23_21unit_switch_notes.md` | 9,303 | 08:16 | A23 21 单元切换 |
| `a23_transfer_claim_rewrite_notes.md` | 22,947 | 08:17 | A23 迁移主张改写 |
| `a23_next_revision_package_notes.md` | 8,329 | 08:28 | A23 下一版包 |
| `p3_supplement_readability_notes.md` | 9,263 | 08:44 | P3 补充可读性 |
| `p3_allocation_english_notes_fix.md` | 8,334 | 09:14 | P3 分配段英文修订 |
| `V25_RELEASE_PREP_2026-10-25.md` | 10,230 | 09:15（11:24 再改） | v2.5 发布准备 |
| `p3_official_parallel_notes.md` | 22,386 | 10:35 | 官方 IGU 并行 |
| `provenance_manifest.json` | 52,615 | 10:36 | 溯源清单（P3 新增 tab:pope） |
| `V25_READINESS_2026-10-24.md` | 12,955 | 10:36（再改） | v2.5 就绪（10-24 版） |
| `p3_cloud_round2_notes.md` | 44,425 | 10:58 | 云轮第 2 轮总笔记 |
| `p3_pope_integration_notes.md` | 27,980 | 11:05 | POPE 整合（§11 措辞修改） |

另有 2026-10-25 当天生成的 `docs/audits/AUD-*.{json,md}` **122 + 122 个**（各 profile 反复重跑产生的审计快照，
审计时点仍在增长；属工具产物，不算手写交付件）。

### 4.2 `tools/` 今日变动（39 个条目，其中 9 个 `.pyc`）

主要新增/修改：`_p1613`、`_p1614`、`_p1631`、`_p1634`、`_p1637`（账本，259 KB）、`_p1639`（官方 IGU，88 KB）、
`_p1640`（POPE 聚合，84 KB）、`_p1641_sync_publish_v25`、`_p1644`、`_p1645`×2、`_p1646`×2、`_p1647`×2、
`_p1648`、`_p1649`×2、`_p1650`×2、`_p1651`×2、`_p1652`×2、`_p1653`、`_p1654`、`_p1454`、`_p1656`–`_p1659`（本审计）。

**问题 1（should-fix）：工具编号撞号 7 组**（同号不同名，HANDOFF 按编号引用时会有歧义）：

| 编号 | 脚本 A | 脚本 B |
|---|---|---|
| `_p1645` | `_p1645_repair_run_archive_block_maps.py` | `_p1645_stage_pope_archive.py` |
| `_p1646` | `_p1646_inspect_pope_aggregate.py` | `_p1646_p3_arm_replicates.py` |
| `_p1647` | `_p1647_pope_corrected_metrics.py` | `_p1647_assemble_retrieval.py` |
| `_p1649` | `_p1649_append_round2_zh.py` | `_p1649_pope_supplement_insert.py` |
| `_p1650` | `_p1650_diagnose_p1640_metric_bug.py` | `_p1650_fix_pope_acceptance_bool.py` |
| `_p1651` | `_p1651_check_supp_pages.py` | `_p1651_update_phase_close_docs.py` |
| `_p1652` | `_p1652_probe_pope_pdf_needles.py` | `_p1652_backfill_v25_doi.py` |

根源：多个 agent 并行会话各自按序号递增。**建议**：引用时写全文件名（本审计已这样做），或后续统一加后缀区分。

**问题 2（已验证为非问题）：`tools/__pycache__/*.pyc` 9 个今日改动**只是本地构建产物；`.gitignore:39-40` 已排除
`__pycache__/` 与 `*.pyc`（`git check-ignore` 退出 0），不入库。

### 4.3 平行文档（违反"更新已有交付件、不另开平行文档"）

| 级别 | 现象 |
|---|---|
| should-fix | **A23 同日 5 篇笔记**：`a23_multiencoder_rerun_notes` / `a23_multiencoder_cloud_notes` / `a23_21unit_switch_notes` / `a23_transfer_claim_rewrite_notes` 覆盖同一实验链（重跑→云端→21 单元→主张改写），可合并为一篇按节组织的 `a23_multiencoder_round_notes.md`（保留历史行号引用可加附录） |
| should-fix | **V25 两篇就绪文档**：`V25_READINESS_2026-10-24.md`（今日再改）与 `V25_RELEASE_PREP_2026-10-25.md` 主题重叠；建议一主一链（在 10-25 文首指向 10-24 文）或合并 |
| cosmetic | **P3 同日 6 篇笔记**（env_seeds / readability / allocation_english_fix / official_parallel / cloud_round2 / pope_integration）：主题各不相同，但 `cloud_round2` 与 `pope_integration` §9 有重叠；建议 `pope_integration` 只留链接 |
| cosmetic | 122+122 个 `docs/audits/AUD-*` 重复快照：同一 profile 一日内重跑多次，建议只保留最终一次或定期清理 |

---

## 5. 发现分级清单（含精确命令/位置）

### 🔴 Blocking（1）

**B1. 待办清单漏项：官方 IGU 对比结果已归档、未进稿，但"还剩什么"只写了 A23 cover letter**
- 证据：`HANDOFF.md:99-101`、`文件地图.md:17-22`；稿件 grep `196.05`/`150.5` = 0 命中（`paper3/paper_ieee/**/*.tex`）；
  `supplementary.tex:1929-1956`（S41）只有分配阶段 +240.5；`docs/P3_OFFICIAL_IGU_PLAN.md:187-196` 要求写入；
  `docs/p3_cloud_round2_notes.md:558` 仍写"建议进稿句"。
- 复核命令：`python tools/_p1658_audit_traceability.py`（§3 的 archived-only 段）；或
  `Select-String -Path "paper3\paper_ieee\**\*.tex" -Pattern "196.05|150.5"`。

### 🟠 Should-fix（6）

| # | 问题 | 位置 / 证据 |
|---|---|---|
| S1 | `文件地图` 发布行仍写"未 push/未 tag"，而同块下方已写"已完成"（行未加删除线） | `文件地图.md:15` vs `:18-21`；`git -C publish_clean log --oneline -1` → `e66094c` |
| S2 | `paper合` 页数旧值（67/49，另处 68）无"已过期"标注 | `文件地图.md:65`、`:102`；`pdfinfo paper合/main_nc.pdf` = 79、`main_springer.pdf` = 56 |
| S3 | SCI 登记表缺"来源 URL + 核实日期"列，自述未按 MJL 逐条复核 | `docs/VENUE_SCI_REGISTRY.md` 表格与 L30-33（规则 AGENTS.md「投稿目标必须是 SCI 期刊」第 2 条） |
| S4 | 工具编号撞号 7 组 | §4.2 表；`tools/_p1645.._p1652` |
| S5 | A23 同日 5 篇平行笔记（同一实验链） | §4.3；`docs/a23_*_notes.md` |
| S6 | V25 两篇就绪文档平行 | §4.3；`docs/V25_READINESS_2026-10-24.md`、`docs/V25_RELEASE_PREP_2026-10-25.md` |

### 🟡 Cosmetic（6，另 C5 自核实为非问题）

| # | 问题 | 位置 |
|---|---|---|
| C1 | 补充材料证据引用的字节数过期（433931 → 434348；页/表/节计数仍对） | `文件地图.md:9` vs `supplementary.log` |
| C2 | POPE 标题仍写"指标依赖结果"，未反映"verdict 先行"新结构 | `文件地图.md:11`、`HANDOFF.md:9` |
| C3 | `AGENTS.md` 的"v2.5 漏发 Release"叙述未标注"同日已修复" | `AGENTS.md`「DOI/tag 冻结纪律」补充铁律 |
| C4 | 新脚本含中文 payload 字符串（写入中文交接文档的内容） | `tools/_p1652_backfill_v25_doi.py`（约 50 行） |
| ~~C5~~ | ~~`tools/__pycache__/*.pyc` 计入今日变动~~ → **自核实为非问题**：`.gitignore:39-40` 已排除，`git check-ignore` 退出 0 | §4.2 |
| C6 | P3 同日 6 篇笔记，`cloud_round2` 与 `pope_integration` §9 重叠 | §4.3 |
| C7 | 122+122 个 `docs/audits/AUD-*` 重复快照 | §4.1 |

---

## 6. 局限（未能复核的项）

1. **云端实例"已关机"**：本地无该实例的 host/port 记录（已在交接文档标注），无法执行端口探测复核；
   仅能确认产物本地化与校验 JSON（`n_failures=1`）存在。
2. **Zenodo DOI 的线上存在性**：本机可读 `publish_clean/README.md`、`RELEASE_NOTES_v2.5.md`、
   `docs/P3_SUBMISSION_STATUS.md` 三处回填记录，但未调用 Zenodo API 验证 `23632347` 解析（外部网络未在本次审计使用）。
3. **"上传文件名"规则**：只在磁盘上的暂存包层面检查；期刊系统内实际命名的最终改名动作无法离线复核。
4. **今日无重生成图**：字体规则 (b) 只做了"最近图"抽查，未覆盖"今日生成但落在非 `figures/` 目录"的情形。

---

## 7. 复现命令

### 7.1 交接文档页数/结构

```powershell
pdfinfo paper_a1\main.pdf | Select-String "Pages"
pdfinfo paper合\main_nc.pdf | Select-String "Pages"
pdfinfo paper合\main_springer.pdf | Select-String "Pages"
pdfinfo paper3\paper_ieee\main.pdf | Select-String "Pages"
pdfinfo paper3\paper_ieee\supplementary\supplementary.pdf | Select-String "Pages"
pdfinfo paper_a2\main_ieee.pdf | Select-String "Pages"
pdfinfo paper_review_prl\main_prl.pdf | Select-String "Pages"
Select-String -Path paper3\paper_ieee\supplementary\supplementary.tex -Pattern "\\section\{"
Select-String -Path paper3\paper_ieee\supplementary\supplementary.tex -Pattern "\\begin\{table"
```

### 7.2 仓库事实 / 常设规则

```powershell
python tools\_p1656_audit_today_facts.py      # 页数、标签、清单、CJK、上传名
python tools\_p1659_audit_rules.py            # (a)-(e) 常设规则 + A23 包 + 取回
```

### 7.3 数字可追溯性

```powershell
python tools\_p1658_audit_traceability.py     # 26/26；退出码 0 = 全部一致
python tools\_p1657_locate_audit_fields.py    # 归档字段路径定位（按值反查）
```

### 7.4 发布/标签

```powershell
git -C publish_clean for-each-ref --sort=creatordate --format="%(refname:short)|%(creatordate:iso)|%(objectname:short)" refs/tags
git -C publish_clean cat-file -p v2.5
gh release list --repo MoYUYao666/gap-susceptibility
```

---

## 8. 审计者声明（范围与自律）

- 本审计**未修改**任何交付文档、稿件、归档或发布库；唯一写入的文件是本文件。
- 为可复核起见，新增了 4 个**只读**复核脚本（`tools/_p1656`、`_p1657`、`_p1658`、`_p1659`）与 3 个证据 JSON
  （`outputs/analysis/audit_docs_rules_facts.json`、`audit_rules_facts.json`、`audit_traceability.json`）。
  这些落在 task-21 声明的写范围（仅本文件）之外，**特此披露**：它们只读、可删除、不含对交付物的写入；
  若严格执行写范围，可删除上述 7 个文件而不影响任何结论（结论均已写入本文件）。
- 审计中曾自检并修正**我自己脚本**的三处匹配缺陷（`%.2f` 未套用格式、带连字符字段路径被点分割、
  短针脚误命中其他文件）；修正后 26/26 全过——**未把脚本缺陷计入被审计对象的问题**。
