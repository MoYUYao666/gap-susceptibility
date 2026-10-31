# P3 官方实现对比整合笔记（task-22，2026-10-25）

> 状态：**已完成**。本文件是 task-22 的交付件与门禁记录。
> 触发：独立审计 `docs/audit_docs_rules_2026-10-25.md` 的 **blocking B1** —— 官方 IGU 对比结果
> 已归档但未进入任何稿件（grep `196.05` / `150.5` 在稿件树 0 命中），而交接文档把剩余工作收窄为
> "A23 cover letter"。
> 本文件为中文工作笔记；稿件与代码/归档内容为英文。

---

## 1. 加了什么（只动补充材料 S41，`main.tex` 未改）

`paper3/paper_ieee/supplementary/supplementary.tex`：

| 位置 | 改动 |
|---|---|
| **S41 内（`\section{Official IGU allocation stage}` 之后、`\section{Instruction-family replication...}` 之前）** | 新增 `\subsection{Official implementation versus the block-level rule}`（`\label{app:igucompare}`）+ 三段正文 + 一张新表 `\label{tab:igucompare}`（表格编号 **S45**） |

**新增内容要点**：

1. **六臂与分配距离**：官方分配器（`official_corrected_map`）与块级 reimplementation（`reimpl_igu_style`）
   在 seeds **42 / 123 / 789** 各训练一次（六臂）；校正映射下分配为 **11/1/2/2** vs **11/1/3/1**，
   块级 **L1 = 2/16**（容差 2）；**归档映射**（12/1/2/1 vs 11/1/3/1）下同样 L1 = 2
   ⇒ 结论**不依赖**采用哪套映射约定。
2. **配对判定**：配对（按 seed）官方减块级 **ΔE 差 = −59.5**，**95% CI [−150.5, −8.0]**
   （20,000 次百分位 bootstrap，RNG seed 20261024）；预声明 margin **196.05 = 5% × E(0)=3921.0**；
   双侧单侧 TOST 在 margin 处**通过**（归档 `tost_p = 0.0`，即没有一次重采样达到 margin；
   最小等价 margin **107.0**）；arm verdict `equivalent`；结合 L1 在容差内，预声明规则给出
   **总体 verdict `small`** ⇒ 分配规则基线以官方实现为准报告。
3. **单栈声明**：三对全部训练在同一软硬件栈（**torch 2.12.1+cu130 / CUDA 13.0 / NVIDIA RTX 4080 SUPER**；
   `same_stack_for_every_pair = true`、`stack_mix_warning = null`），配对对比不受栈混杂影响。
4. **复现性 caveat（诚实边界）**：每臂在相同 argv 下再跑 2 次（`--force` 破缓存），
   单臂 ΔE 三次运行极差**最大 132.0**、**均值 76.1**；该离散度与被判断的差距（校正映射 **59.5**、
   归档映射 **92.5**）**同量级** ⇒ 这些 seed 上两个分配规则的差异**小于 run-to-run 噪声**；
   因此对比以**预声明 margin + L1 距离**为框架，**不把单 seed 缺口当可复现读数**；
   primary 与两个 pinned anchors 在复现前后**逐字节不变**（sha256 记录于归档）。
5. **Source 行**：caption 末尾给出全部脚本与归档字段路径（见 §2），并注明对比脚本
   `tools/_p1639_p3_official_igu.py --compare` 与复现脚本 `tools/_p1646_p3_arm_replicates.py`。

**表 `tab:igucompare`（S45）7 行**：配对差+CI、预声明 margin（5% of E(0)）、TOST 归档 p、
最小等价 margin、块级 L1（两套映射）、复现极差、verdict。

---

## 2. 每个数字的字段路径（Source 行已写进 caption）

**对比归档** `outputs/analysis/p3_official_vs_reimpl.json`（sha256 `4698a6e7…`）：

| 数字 | 字段 |
|---|---|
| 配对差 **−59.5** | `overall.mean_gap_delta_E` |
| CI **[−150.5, −8.0]** | `overall.ci95` |
| margin **196.05**、5% × E(0) | `overall.margin`、`meta.margin_fraction_of_E0` |
| E(0) = **3921.0** | `pairs[0].reimpl.E[0]` |
| TOST p = **0.0** | `per_configuration.trained_arm_delta_E.tost_p` |
| 最小等价 margin **107.0** | `per_configuration.trained_arm_delta_E.min_equivalent_margin` |
| 块级 L1 **2**、容差 **2** | `per_configuration.allocation.l1`、`meta.allocation_l1_tolerance` |
| 归档映射 L1 **2** | `allocation_sensitivity_to_the_block_mapping.archived.l1` |
| 校正映射 L1 **2** | `allocation_sensitivity_to_the_block_mapping.corrected.l1` |
| 官方/块级分块 rank **11/1/2/2、11/1/3/1** | `official_side.allocation.*`、`reimpl_side.allocation.*` |
| 配对 seed 数 **3** | `n_pairs`、`seeds_common` |
| 单栈 **true / null** | `same_stack_for_every_pair`、`stack_mix_warning` |
| 栈版本/GPU | `pairs[].official.env.{torch,cuda,gpu}` |

**六臂归档** `outputs/analysis/p3_official_igu_run.json`（sha256 `8f4546ed…`）：
`runs[]` 共 **6** 条（`config`、`seed`、`delta_E`）。

**复现归档** `outputs/analysis/p3_official_igu_replicates.json`（sha256 `e38f65ab…`）：

| 数字 | 字段 |
|---|---|
| 极差最大 **132.0** | `summary.max_spread_across_arms` |
| 均值 **76.1** | `summary.mean_spread_across_arms` = 76.0833 |
| 归档映射差距 **92.5** | `summary.archived_official_minus_reimpl_gap` |
| 六臂、每臂 2 次复跑 | `summary.n_arms=6`、`summary.n_replicate_passes=2` |
| anchors 前后一致 | `pinned_anchors_sha256_before` == `pinned_anchors_sha256_after` |

**单 seed 读数**（官方 seed42 = 182.5、块级 seed42 = 333.0 等）**故意不打印**：
`audit_check.py` 的**域内**检查会在 S41 切片里 forbid `182.5` / `333.0`，
防止把单 seed 缺口当作对比结论。

---

## 3. 生成器、清单、账本、审计针脚

| 交付物 | 改动 |
|---|---|
| `tools/_p1660_official_igu_integration.py` | **新增**（幂等、`--force` 重渲染）。渲染前对归档逐项断言（隙/CI/margin/TOST/L1/六臂/复现统计/单栈/anchors），保证稿件不会与归档漂移；本次插到 **S41 内第 1958 行起、73 行**，记录 JSON `outputs/analysis/p3_iguofficial_insert.json` |
| `docs/provenance_manifest.json` | P3 新增 **`tab:igucompare`** 行（script + 3 个归档 + 字段路径），P3 条目 43→44 |
| `tools/_p1637_p3_reproduce_all.py` | 新增 **S41c 块（94 行，29 条）**：对比/复现/单栈/anchors/哈希全部登记为归档字段或 `calc`；**账本 OK 983 / MISMATCH 0 / UNSOURCED 0（TOTAL 1021）** |
| `paper3/paper_ieee/audit_check.py` | 新增 `SUPP_IGU_NUMBERS`（**28 条 present**）+ **域内 absent 检查**（S41 切片禁用单 seed 读数 182.5/333.0）；表数 **50→51** |
| `paper3/paper_ieee/audit_pdf.py` | 新增 **12 条 PDF 针脚**（子节标题、表格数字、单栈、GPU、两个归档名的小大写形式）；`SUPP_TABLE_HEADINGS` **1..51**、检查文案 `S1--S51` |

---

## 4. 计数

| 项 | 之前 | 现在 |
|---|---|---|
| `main.pdf` 页数 | 10 | **10（未变）** |
| `supplementary.pdf` 页数 | 26 | **26（未变）** |
| 补充 `\section` 数 | 46 | **46（未变；新增的是 `\subsection`）** |
| 补充编号表 | 50（S1–S50） | **51（S1–S51；新表 = S45）** |
| overfull / float-too-large | 0 / 0 | **0 / 0** |
| manifest P3 条目 | 43 | **44** |
| 账本条目 | 993 | **1021** |
| `paper3/paper_ieee` 改动文件 | — | `supplementary.tex`、`audit_check.py`、`audit_pdf.py` |

> **`main.pdf` 未变 10 页**：整合全部落在补充材料（`supplementary.tex` 独立编译），
> 因此**没有触发"压缩正文"**——本轮**没有缩短任何正文/数字**。
> 补充材料也恰好保持 26 页，`audit_pdf.py::SUPP_PAGES` 无需改动。

---

## 5. 门禁（全部实跑；按 2026-10-25 新规用 base 解释器 `python`）

| 命令 | 结果 |
|---|---|
| `pdflatex ×2 supplementary.tex` | 退出 0；**26 页**；overfull **0**；float-too-large **0** |
| `main.tex`（pdflatex+bibtex+pdflatex×2） | **10 页**；overfull **0** |
| `python paper3/paper_ieee/audit_check.py` | **0 hard failure / 0 warning**（IGU 28 present 全过 + 域内单 seed 禁项通过；51 表；46 段） |
| `python paper3/paper_ieee/audit_pdf.py` | **0 hard failure / 0 warning**（main 10、supp 26、S1–S51 全印出、IGU 12 针脚全过） |
| `python -m tools.paper_audit audit --profile p3_prl --fail-on NONE` | pass=**49** fail=**1** warn=0；唯一 fail = **A-01 "uncommitted changes under paper3/paper_ieee"**（本轮改动尚未提交；提交后即 READY A，03:04 曾实测 pass=50/fail=0）。`--fail-on NONE` 退出码 0 |
| `python tools/_p1428_provenance_gate.py` | **gate: PASS**（P3 floats=4 / manifest=44 / missing=0 / pending=0 / broken_paths=0） |
| `python tools/_p1637_p3_reproduce_all.py --check --quiet` | **OK 983 / MISMATCH 0 / UNSOURCED 0**（TOTAL 1021） |
| `python tools/_claim_ledger.py --apply` | **96/96 通过，0 失败** |

---

## 6. 未能溯源 / 未做的项

1. **A-01 未提交**：本轮 `paper3/paper_ieee` 下 3 个文件仍是工作区改动；`paper_audit` 因此唯一 fail。
   是否提交由 lead 决定（本任务写范围不含 git 操作）。
2. **Zimmerman/第三方 API 线上核验**：未调用外部 API；所有数字来自本地归档，归档 sha256 已在
   caption/账本登记（对比 `4698a6e7…`、run `8f4546ed…`、复现 `e38f65ab…`）。
3. **`paper3/paper_ieee/sections/` 未改**：对比材料按任务要求放在补充材料；主文 `main.pdf` 保持 10 页。
4. **单 seed 读数**（182.5 / 333.0 等）按 caveat 要求**不进入稿件**；它们仍是归档的一部分，
   但任何人要看"谁高谁低"必须看配对差与 CI，不能引用单点。

---

## 7. 复现命令（按序）

```powershell
# 1) 渲染整合块（幂等；改模板后加 --force）
python tools\_p1660_official_igu_integration.py

# 2) 清单与账本（幂等）
python tools\_p1661_manifest_official_igu.py
python tools\_p1662_ledger_igu.py

# 3) 编译
cd paper3\paper_ieee\supplementary; pdflatex -interaction=nonstopmode supplementary.tex; pdflatex -interaction=nonstopmode supplementary.tex
cd ..; pdflatex -interaction=nonstopmode main.tex; bibtex main; pdflatex -interaction=nonstopmode main.tex; pdflatex -interaction=nonstopmode main.tex

# 4) 门禁
cd ..\..; python paper3\paper_ieee\audit_check.py; python paper3\paper_ieee\audit_pdf.py
python -m tools.paper_audit audit --profile p3_prl --fail-on NONE
python tools\_p1428_provenance_gate.py
python tools\_p1637_p3_reproduce_all.py --check --quiet
python tools\_claim_ledger.py --apply
```
