# P3 环境堆叠种子轮 —— 重复计数修复与入稿记录

日期：2026-10-25。脚本：`tools/_p1613_p3_cloud_runner.py`（解释器 `D:\Anaconda\envs\torch26\python.exe`）。
归档：`outputs/analysis/p3_env_stack_seeds.json`（47 行）、`outputs/analysis/p3_env_seeds_runlog.json`。

---

## 1. 发现的重复单元格与处置

聚合脚本给 torch 2.4/cu121 同时收集两种文件名（未打标签的行 + 带 `_torch24` 后缀的行）。
`run_training.py` 不会写堆叠后缀，所以这一轮把训练脚本刚写的未打标签输出**复制**成带后缀的名字；
而**同一个单元（stack, rank, seed）被两个文件同时命中**时，它就被算了两次：rank 5 的 `values_by_seed`
只有 5 个种子却报 `n = 7`。

逐单元核对（`delta_E` 与 `E` 轨迹都不同 ⇒ 确实是两次不同的运行，不是同一次测量的两份拷贝）：

| stack | rank | seed | 保留（未打标签，归档行） | 丢弃（本轮 `_torch24` 行） | 关系 |
|---|---|---|---|---|---|
| torch24_cu121 | 5 | 123 | **-2.5** `verify_r5_s123_..._a10.json` | -50.0 `..._a10_torch24.json` | 同一单元的两次运行（E 轨迹不同） |
| torch24_cu121 | 5 | 999 | **+64.5** `verify_r5_s999_..._a10.json` | +58.5 `..._a10_torch24.json` | 同一单元的两次运行（E 轨迹不同） |

> 判据不是偏好，而是**可复现性**：冻结的三栈参考桶（`outputs/analysis/p3_env_variance.json` 的
> `envs["torch 2.4/cu121"]`，`n = 4`、`mean = 25.25`、`values = [-2.5, 41.0, -2.0, 64.5]`）里
> -2.5 / -2.0 / +64.5 正是这三条**未打标签**的行；`tools/_p1570_env_variance_update.py` 当年用
> `verify_r5_s*_a10*.json` 松散 glob 排序取值，未打标签的名字排在带后缀的名字之前，已发表的桶就是这样形成的。
> 若改用带后缀的重复行，已发表参考会被静默改指到另一次运行。

**两条都没有被静默丢弃**：被丢弃的行连同数值、文件路径、字段名、以及被保留的行，全部写进归档
`acceptance.discarded_duplicate_rows`；每单元的处置理由写进 `duplicate_cells` 与 `meta.registry_notes`。
聚合新增断言 `acceptance.one_row_per_stack_rank_seed_cell == true`。

（附带发现，未改判：torch24_cu121 在 rank 5 另有一条**不属于冻结桶**的 seed 7 测量
`+19.0`（`..._a10_torch24.json`）。冻结桶的 `n = 4` 与 `mean = 25.25` 不含它，
所以它不参与三栈参考，但**保留在四栈设计里**；这条区别记录在
`meta.frozen_three_stack_reference.excluded`。）

## 2. 修正后的分解（`outputs/analysis/p3_env_stack_seeds.json`）

字段路径：`ranks.<rank>.stacks.<stack id>.{n,mean,sd}`；
`sigma_by_rank.<rank>.all_rows.{sigma_env,sigma_seed,env_variance_share}`；
`sigma_by_rank.<rank>.all_rows.bootstrap.{share_ci95,sigma_env_ci95,sigma_seed_ci95}`；
`sigma_by_rank.<rank>.three_stack_reference`；`sigma_by_rank.<rank>.common_seed_design`。

### rank 5（主假设秩）

| 设计 | n | 每堆叠 n | sigma_env | sigma_seed | 环境占比（95% CI） |
|---|---|---|---|---|---|
| 四栈（本轮） | 24 | 5 / 10 / 5 / 4 | **32.4602** | **32.7245** | **49.59%**（[35.8%, 74.9%]） |
| 三栈冻结参考 | 19 | 5 / 10 / 4 | 31.1489 | 34.2950 | 45.20% |
| 平衡共同种子（42/123/999） | 12 | 3 / 3 / 3 / 3 | 32.8100 | 21.0525 | 70.84%（[53.6%, 96.6%]） |

sigma 的 bootstrap 区间（同一 10,000 次重抽）：sigma_env [21.41, 47.92]，sigma_seed [20.67, 36.96]。

每堆叠 mean ± sd（rank 5）：torch 2.9/cu130 −23.0 ± 22.3（n=5）；torch 2.12/cu130 −43.7 ± 38.8（n=10）；
torch 2.4/cu121 +24.0 ± 28.9（n=5）；torch 2.6/cu124 −63.8 ± 29.3（n=4）。

### rank 6

| 设计 | n | sigma_env | sigma_seed | 环境占比（95% CI） |
|---|---|---|---|---|
| 四栈 | 23 | 33.1592 | 30.7631 | 53.74%（[33.6%, 82.0%]） |
| 三栈 | 19 | 0.0000（原始矩为负，被 clamp） | 30.6802 | 0% |
| 平衡共同种子 | 12 | 25.4911 | 33.7849 | 36.28%（[8.0%, 87.9%]） |

rank 6 每堆叠 mean ± sd：torch 2.9 +65.5 ± 38.5（n=5）；torch 2.12 +87.3 ± 29.9（n=10）；
torch 2.4 +82.25 ± 19.0（n=4）；torch 2.6 +4.63 ± 31.2（n=4）。

### 与已发表三栈值的关系

* **三栈参考被逐位复现**：31.1489 / 34.2950 / 0.4520（新增 `three_stack_reference` 由
  `meta.frozen_three_stack_reference` 记录的冻结行集算出，不再被新测量扰动）。
* **环境占比会动**：三栈 45.20% → 四栈 **49.59%**（+4.4 个百分点）；sigma_env 31.15 → 32.46，
  sigma_seed 34.29 → 32.72。原因是第四个堆叠（torch 2.6/cu124，均值 −63.8）与 torch 2.12/cu130 差异很大，
  把环境项顶上去，同时把种子项压下来。
* 四栈设计本身**已经包含**冻结桶排除掉的那条新测量（torch 2.4/cu121 rank 5 seed 7 = +19.0），
  所以四栈 = 冻结桶 + 被排除单元，不需要第二个变体；这一点由聚合的断言
  `sigma_by_rank.<rank>.frozen_bucket_exclusions_not_in_design` 为空来保证。
  （把该条算进 torch 2.4 桶后 torch 2.4 rank 5 的 n 由 4 变 5、均值由 +25.25 变 +24.0，
  即四栈的 `ranks.5.stacks.torch24_cu121`。）

## 3. 稿件改动（含行号，改后行号）

| 文件 | 行 | 改动 |
|---|---|---|
| `paper3/paper_ieee/sections/discussion.tex` | 49–55 | `TODO(envseeds)` 标记换成归档字段路径注释（脚本 + 归档 + 字段名） |
| 同上 | 71–77 | 限制 (6) 的环境数字：四栈均值 −23.0 / −43.7 / +24.0 / −63.8；占比 49.59%（CI [35.8%,74.9%]）；sigma_env 32.46 / sigma_seed 32.72；并列三栈 45.20% / 31.15 / 34.29；归档指到 `p3_env_stack_seeds.json` 与 `p3_env_variance.json`；`(S30, S39)` 指针保持不变（S30 = `app:envcloud`，S39 = `app:envvar`） |
| `supplementary.tex` | 1350–1362（S30） | 表 `tab:envcloud` 说明补四栈口径与四栈分解值、指向 `p3_env_stack_seeds.json`；表格数字未动（全部仍由归档支持） |
| `supplementary.tex` | 1702–1732（S39，`app:envvar`） | 表 `tab:envvar` 加 torch 2.6/cu124 行（n=4，−63.8，29.3），torch 2.4/cu121 行改为 5 / +24.0 / 28.9；题注改为四栈（32.46 / 32.72 / 49.59%，CI [35.8%,74.9%]）并保留冻结三栈对照（31.15 / 34.29 / 45.20%） |
| `paper3/paper_ieee/audit_check.py` | 253–299 | `ENV_NEEDLES` 换成四栈新值 + 新归档；`ENV_ABSENT` 增加被取代的旧 CI `[21.2%,74.7%]`、旧 S37 行与旧 sigma（新值在场、旧值不在场） |
| `paper3/paper_ieee/audit_pdf.py` | 183–222 | `ENV_MAIN_VALUES` / `ENV_MAIN_ABSENT` 同上（PDF 针） |
| `tools/_p1613_p3_cloud_runner.py` | 914–981（`dedupe_cells`）、983–1073（`reference_three_stack`）、1075–1145（`collect_env_rows`）、1232–1265（`bootstrap_share` 增加 sigma 区间）、1267–1520（聚合与验收，含 `common_seed_design` 的 bootstrap 与「冻结桶被排除单元已在设计中」断言） | 去重、冻结参考、丢弃记录、验收断言 |
| `tools/_p1637_p3_reproduce_all.py` | 1345–1453 | 新增 15 条四栈账目（每堆叠均值、占比与 CI、两个 sigma、三栈对照、n=24、去重单元数、S39 表数字），全部指向 `p3_env_stack_seeds.json` |
| `docs/provenance_manifest.json` | P3 `tab:envvar` / `tab:envcloud` 两条 | 生成脚本改为 `tools/_p1613_p3_cloud_runner.py`，归档加 `outputs/analysis/p3_env_stack_seeds.json`，note 写入字段路径 |

补充材料仍是 **46 节**，`main.tex` 的 `S1--S46` 未动。

## 4. 页数与门禁结果（2026-10-25）

| 门禁 | 结果 |
|---|---|
| `pdflatex` ×2 `main.tex` | **10 页**（PRL 上限，未涨页；两次输出一致 422,509 B） |
| `pdflatex` ×2 `supplementary/supplementary.tex`（在 `supplementary/` 内） | **22 页**（418,310 B） |
| `python paper3/paper_ieee/audit_check.py` | 0 hard failure / 0 warning（环境节全 PASS，46 节，指针全注册） |
| `python paper3/paper_ieee/audit_pdf.py` | 0 hard failure / 0 warning（main.pdf == 10 页；四栈针全在场） |
| `python -m tools.paper_audit audit --profile p3_prl --fail-on NONE` | BLOCKED / grade D，**唯一 blocker = A-01「uncommitted changes under paper3/paper_ieee」**；该 blocker 在 2026-10-24T23:16:11Z 的基线审计里已存在（本次改动前），其余 49 项 pass、无 LaTeX 错误/未定义引用/溢出行，日志与 PDF 一致 10 页 |
| `python tools/_p1428_provenance_gate.py` | **PASS**（P3 floats=4 / manifest=42，missing=0 pending=0 broken_paths=0） |
| `python tools/_p1637_p3_reproduce_all.py --check --quiet` | **0 MISMATCH**（OK 880 / MISMATCH 0 / UNSOURCED 0，共 911 条） |
| `python tools/_p1613_p3_cloud_runner.py --job env-seeds --aggregate --strict` | **[5] strict acceptance: satisfied**（exit 0）；断言账本 4 项 0 失败；三栈参考 31.1489 / 34.2950 / 0.4520 = 归档值，且 0 个重复单元 |

归档本次新生成的审计报告：`docs/audits/AUD-p3_prl-20261024T231611Z.{json,md}`（改动前基线）、
`docs/audits/AUD-p3_prl-20261024T231826Z.{json,md}`、`docs/audits/AUD-p3_prl-20261024T232128Z.{json,md}`、
`docs/audits/AUD-p3_prl-20261024T232321Z.{json,md}`（末次，唯一 blocker 同前）。

## 5. 遗留与提请裁决

1. **paper_audit 的 A-01 blocker 需要一次提交才能清掉**：它是「paper3/paper_ieee 下有未提交改动」，
   本次改动前（2026-10-24T23:16:11Z 基线）就已存在。改完稿件后提交即可消失，本会话未提交（写权限边界内不动 git）。
2. **本轮实际只落了 4 条 `_torch24` + 2 条 `_torch29` 归档**，与任务书说的「八条 `_torch24` + 两条 `_torch29`」不符：
   当前 `verify_r[56]_s*_{torch24,torch29}.json` 共 6 个文件；torch26 的 4 条来自更早的一轮
   （`runlog` 无对应记录）。归档里的 6 个 torch26 行因此是**较早一轮的测量**，四栈数字用的就是它们。
   另外 `runlog` 最后两条把同一批运行记成了 `torch29` 后缀（本机装的是 torch 2.9.1），
   对应 `..._torch29.json` 两个文件（按 `torch29_cu130` 栈登记，`p3_seeds_combined.json` 已有同样 5 个种子）。
   这两点都不改变本次去重结论，但 `torch26_cu124` 的硬件栏（`p3_env_stack_seeds.json` 的
   `meta.hardware_caveat`）仍待核实，未在本次改动范围内。
3. **S29 的节题名与任务书措辞**：任务书写「S29/S37」，实际是 S30/S39（见下）。

### 与任务书的两处差异（如实记录）

1. **任务书写「S29/S37」，实际节号是 S30/S39**：`supplementary.tex` 里 `app:envcloud` 是第 30 节、
   `app:envvar` 是第 39 节（`audit_check.py` 的 `SECTION_POINTER_ANCHORS` 也按 `(S30, S39)` 校验）。
   因此 discussion 里保留 `(S30, S39)` 指针，task 里的 S29/S37 视为笔误；`main.tex` 的 `S1--S46` 与
   「46 节」计数未受影响。
2. **S30 节标题「Second-environment reproducibility」里那张 `tab:envcloud` 表的数字未改**：
   它是 seed-42 的跨环境对照（3930.5 / +41.0 等），仍由 `p3_env_matrix3.json` 与
   `verify_*_torch26.json` 支持；四栈分解值只写进它的题注与 S39 的表。