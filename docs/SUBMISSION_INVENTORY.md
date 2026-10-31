# SUBMISSION 目录清单（2026-10-26 整理后）

用途：把「已投出且冻结」「待下一轮修订的暂存包」「当前要投的包」分清，避免混淆；冻结件一律**只读**，
由门禁哈希守住（`tools/paper_audit/freeze/*.json` + `tools/_p1454_final_verify.py`）。

| 目录 | 状态 | 内容 / 页数 | 门禁 |
|---|---|---|---|
| `A1_PatternAnalysisApplications/` | **已投·冻结**（A1 → PAA，Submission ID `0a4629f0-…`） | 33 文件；Manuscript **64 页** | `a1_paa` 冻结清单 49 条 |
| `A23_JOE/` | **已投·冻结**（A23 → IEEE JOE `26-0663`） | 37 文件（含 `current/`） | `a23_joe` 冻结清单 37 条 |
| `A23_JOE_next_revision/` | **暂存**（下一轮修订用） | 7 文件；Manuscript **73 页**、`SHA256SUMS` 已刷新 | 不冻结；`_p1454` 检查 staged 新鲜度 |
| `P3_PRL_resubmission/` | **已投·冻结**（P3 → PRL `PRLETTERS-D-26-02671`） | 9 文件；Manuscript **10 页** + 补充 8 页（提交时版本） | `p3_prl` 冻结清单 19 条 |
| `P3_PRL_next_revision/` | **暂存**（下一轮修订用） | 9 文件；Manuscript **10 页** | 不冻结 |
| `PaperA_MachineLearning/` | **当前目标包**（Paper A → Machine Learning, Springer） | 26 文件；Manuscript **58 页**（主文 27 + 附录 31）；`SHA256SUMS` 25 条 | 不冻结（尚未投出） |
| `PaperA_Neurocomputing/` | **已投·冻结，已 desk-reject**（`NEUCOM-D-26-23760`） | 54 文件；Manuscript **79 页** | `paperA_nc` / `paperA_springer` 各 54 条（留作历史证据，不可改） |
| `Review_PRL/` | **已投·冻结**（Commentary → PRL `PRLETTERS-D-26-02402`） | 23 文件；Manuscript **7 页** | `prl_commentary` 冻结清单 28 条 |
| `_archive/` | 历史归档（旧投稿包快照） | 341 文件 | 不参与审核 |
| `_frozen_submitted/` | 冻结证据副本 | 14 文件 | 只读 |
| `_venue_builds/` | 各刊模板构建产物 | 30 文件 | 不参与审核 |

## 已移出 SUBMISSION（未投出、已被新目标取代）

| 目录 | 去向 | 说明 |
|---|---|---|
| `PaperA_CVIU/` | `弃用/09_未投出的投稿包/PaperA_CVIU/` | CVIU 要求作者 vitae + 护照照片，放弃 |
| `PaperA_AppliedIntelligence/` | `弃用/09_未投出的投稿包/PaperA_AppliedIntelligence/` | 该刊画像为"新方法+应用基准"，与本文形状不符，改投 Machine Learning |

按审核范围规则，`弃用/` 内一切内容**不参与**任何门禁与台账。

## 操作纪律

1. **冻结件不可动**：`A1_…`、`A23_JOE/`、`P3_PRL_resubmission/`、`PaperA_Neurocomputing/`、`Review_PRL/` 内任何文件都不得修改；
   改动只能在活稿树（`paper_a1/`、`paper_a2/`、`paper3/paper_ieee/`、`paper合/`、`paper_review_prl/`）里做。
2. **暂存包可重建**：`*_next_revision/` 允许随活稿重建，重建后必须刷新自身 `SHA256SUMS.txt`。
3. **当前目标包**（`PaperA_MachineLearning/`）在投出、把哈希登记进冻结清单之前，仍属"可改"状态。
4. 每次投出后：把该包加入对应 profile 的 `package_frozen=True` 与冻结清单，并把状态改成本表第二列的"已投·冻结"。

| `PaperA_MachineLearning_revision/` | Machine Learning (Springer) | next-attempt revision, **not submitted** | 57 pp (main 25 + appendix 32) | built clean, hashes in `docs/SUBMISSION_revision_snapshot_2026-10-27.json` |

| `RS_REVIEW_2026-10-28/` | Remote Sensing (MDPI) review | submitted 2026-10-28 | 26 | `remotesensing-4692108` | Pending review; frozen, 20 files hashed |
| `RS_REVIEW_ISPRSJ_2026-10-31/` | **prepared, not submitted** (survey retarget after the Remote Sensing desk reject) | 7 files; Manuscript **48 pages** (8 tables, 4 figures) | hashes in `SHA256SUMS.txt`; README records status and the fit evidence |
