# A1 统计与溯源修订记录（2026-10-24，第 1595 轮 A1 分支）

本轮范围：`paper_a1/` + 本文件。依据 `docs/a1_paperA_bootstrap_text.md` §1.3–§1.5（插入点 A1-1/A1-2/A1-3）
与归档 `outputs/analysis/a1_monitoring_bootstrap.json`（生成脚本 `tools/_p1595_bootstrap_ci_round.py`）。

## 1. 改动清单（`paper_a1/main.tex`，行号为编译后行号）

| 位置 | 行 | 改动 |
|---|---|---|
| 引言 `sec:intro` | 90–99 | 追加 A1-1 句：16 个大划分 run 的 run 级百分位自助法（20,000 次重抽）区间；并点明 0.37（及 1.08）是"每次 run 内"二项标准误的均值，只界定 run 内抽样误差 |
| 协议小节 `sec:protocol` | 1309 | 删去裸写的 `($1.08$ binomial SE)`（draft A1-2 明确要求替换该措辞） |
| 协议小节 `sec:protocol` | 1311–1316 | 追加 A1-2 句：16 个大划分 run 的区间 + 4 个小划分 run 的区间；保留"不优于训练到底、只买早停"的诚实表述 |
| 表 `tab:monitor_regret` 题注 | 1339–1341 | 追加 A1-3 句 + `Source:` 行（`outputs/analysis/a1_monitoring_bootstrap.json`） |
| 溯源附录 `app:provenance` | 1734 | **严重度 A 修复**：原行只给 `a1_monitor_split_diagnosis.json`（仅覆盖 10 个单元格中的 6 个）；现补 `tools/_p1398_a1_combined.py`、`tools/_p1595_bootstrap_ci_round.py` 与 `a1_monitor_combined.json`、`a1_monitoring_bootstrap.json` |

每个新增/涉及数字的来源（脚本 → JSON 字段）：

| 数字 | 来源 |
|---|---|
| 0.58 [0.28, 0.93]；sd 0.68 | `a1_monitoring_bootstrap.json::result.groups.large.per_rule.regret_minM.{mean, ci95_percentile, sd_ddof1}` |
| 0.52 [0.26, 0.79]；sd 0.56 | 同上 `…regret_last_epoch.*` |
| 3.55 [2.42, 4.71]；sd 2.40 | 同上 `…regret_first_epoch.*` |
| +0.06 [−0.34, +0.50]（含 0） | `…large.paired_differences.minimum_margin_mass_minus_training_to_the_end.{mean_difference, ci95_percentile, ci95_excludes_zero}` |
| −2.96 [−4.11, −1.86] | `…large.paired_differences.minimum_margin_mass_minus_first_epoch.*` |
| −3.03 [−4.21, −1.86] | `…large.paired_differences.training_to_the_end_minus_first_epoch.*` |
| 小划分 [4.51, 8.75] / [3.75, 5.28] / [9.27, 32.50] | `…small.per_rule.{regret_minM, regret_last_epoch, regret_first_epoch}.ci95_percentile` |
| 1.45 / 3.65（minCG）、0.64 / 16.53（seqM） | `a1_monitor_combined.json::per_run[*].{oracle,minCG,seqM}`（`tools/_p1398_a1_combined.py`） |
| 0.37 / 1.08（未改，仅加解释） | `a1_monitor_split_diagnosis.json::summary.{large,small}.mean_regret_minM_in_SE`；自助法归档内复核值 `…mean_regret_minM_in_binomial_SE_recomputed` |
| 20,000 次重抽、n=16/n=4 | `a1_monitoring_bootstrap.json::method.resamples`、`result.groups.{large,small}.n_runs` |

## 2. 编译

- 命令：`cd paper_a1; pdflatex -interaction=nonstopmode main.tex`（连跑 2 次）
- 结果：**64 页**（与改前一致）、0 error、0 undefined reference、0 undefined citation、
  0 `Overfull \hbox` / `Overfull \vbox`、无 `Rerun to get`、无字体替换警告；
  改前同样各为 2 处的 `Underfull \hbox`（位于表内单元格与参考文献条目，均不在本轮改动处）与 2 处 `h`→`ht` 浮动体提示仍在，
  末页题注 `Source:` 行渲染正常。

## 3. 包刷新与审计

- 刷新（A1 分支）：`python tools/_p1576_refresh_a1_papera_packages.py --apply` 的 A1_PAA 分支
  → `Manuscript.pdf`/`Title Page.pdf` 与 live 文件 SHA-256 一致、`latex_source.zip` 21 条 = `latex_source/` 21 文件
  （zip 内 `main.tex` 已含本轮新句与附录补档）、README 事实 64 页 / 241 词。
- 审计：`python -m tools.paper_audit audit --profile a1_paa --fail-on NONE`
  → **BLOCKED / grade D**；PASS 59、FAIL 1、WARN 1、SKIP 16、MANUAL 9、ERROR 0。
  报告：`docs/audits/AUD-a1_paa-20261024T084211Z.md` / `.json`。
  - FAIL = A-01（P1）` M paper_a1/main.tex` —— **预期**，等 lead 提交后消失。
  - WARN = J-01「claim-ledger evidence older than the manuscript sources」—— 因为本轮改了 `main.tex`，
    提交前需重跑 `python tools/_claim_ledger_a1.py --apply`。
  - 包与编译类检查（A-04/A-05、B-01…B-04、B-08、I-01/I-02/I-05/I-06/I-07）全部 PASS。
- 自助法脚本复核：`python tools/_p1595_bootstrap_ci_round.py`（dry run）→ **A1 checks 23 / failures 0**
  （附录那条 flag 由 FAIL 转 OK）；剩余 2 条失败属 Paper A / P3，不在本轮范围。
- A1 账本复核：`python tools/_claim_ledger_a1.py`（dry run）→ **216 pass / 0 fail**。

## 4. 建议的溯源清单补录（越出本轮写权，未改）

1. `docs/provenance_manifest.json` → `manuscripts.A1.floats` 的 `tab:monitor_regret`：
   `script`: `tools/_p1408_a1_table.py` + `tools/_p1398_a1_combined.py` + `tools/_p1595_bootstrap_ci_round.py`；
   `archive`/`archives`: `outputs/analysis/a1_monitor_split_diagnosis.json`、
   `outputs/analysis/a1_monitor_combined.json`、`outputs/analysis/a1_monitoring_bootstrap.json`（status `verified`）。
2. `docs/PROVENANCE_MANIFEST_2026-10-20.md` 第 40 行同一行同步更新。
3. `tools/_claim_ledger_a1.py` 增加 "monitoring bootstrap" 块（区间/配对差 → 上表字段路径），
   否则新句里的 8 组数字不在 A1 账本门禁覆盖内。
4. `outputs/analysis/claim_ledger_a1.json` 由第 3 条 `--apply` 重写，顺带消掉 J-01 警告。

## 5. 未决与偏离（需 lead 决定）

- **只跑了 A1 包分支**：`tools/_p1576_refresh_a1_papera_packages.py --apply` 会**同时**刷新 Paper A（Neurocomputing）包
  （复制 `paper合/*.pdf`、重建 zip、改其 README 状态行）。本轮写权只授权 A1 包，故用临时脚本按该模块自身
  `main()` 原样只执行 `A1_PAA` 分支（断言与打印一致，未改 `tools/` 任何文件）；`SUBMISSION/PaperA_Neurocomputing` 未动。
- **引言 `($1.08$ SE)` 的处置**：draft A1-1 对该句只追加、不删；A1-2 明确删掉协议段里裸的 1.08。
  为与该处一致、避免"把 run 内 SE 当均值不确定度"复现，本轮采取：协议段删去、引言保留并纳入同一句解释
  （"the 0.37 above (and the 1.08 on the four small splits) … bounds within-run sampling error only"）。
  若要连引言的 1.08 一并删除，改 1 行即可。
- **不要重跑** `tools/_p1405_a1_split_text.py --apply`：它按旧措辞整体替换引言与协议段，会覆盖本轮改动
  （该脚本是历史一次性脚本，非门禁）。
- **归档自检块待刷新**：`outputs/analysis/a1_monitoring_bootstrap.json` 里仍留着修复前的自检结果
  （`provenance_appendix_citation.names_a1_monitor_combined = false`、`manuscript_digits` 末条 `matches = false`）。
  dry run 已复算为 OK，但要落进归档需跑 `python tools/_p1595_bootstrap_ci_round.py --apply`——
  该命令会**同时重写 Paper A 归档** `outputs/analysis/paperA_strict_bootstrap.json`，故本轮（写权在 `outputs/` 之外）未执行。