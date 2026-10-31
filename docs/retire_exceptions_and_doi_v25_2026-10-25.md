# 归档收尾 + 活稿 DOI 升到 v2.5（2026-10-25）

> 本轮两件事：**Task A** 把最后三个顶层目录移入 `弃用/`；**Task B** 把五篇活稿的仓库版本 DOI
> 统一到 v2.5（`10.5281/zenodo.23632347`）并重编译。本文是 Task C 的交付件：
> 记录移动了什么、哪些引用改了/哪些**刻意没改**、每处 DOI 变更的 file:line、页数、全部门禁结果，
> 以及**已投冻结件与活稿在 DOI 上的刻意分歧**。
>
> 执行脚本（均幂等、带断言）：`tools/_p1661_retire_three_dirs.py`（移动）、
> `tools/_p1662_retire_docs.py`（规则与交接文档）、`tools/_p1663_doi_v25_live.py`（DOI + 门禁针）、
> `tools/_p1664_rebuild_doi_pdfs.py`（重编译）、`tools/_p1665_scan_dir_refs.py`（引用复扫）。

---

## 一、Task A：三个顶层例外移入 `弃用/`

### 1.1 先纠正一个假阳性

早先的守卫用**朴素子串**匹配，把 `SUBMISSION/_archive/...` 误判为对根级 `_archive/` 的引用，
于是把三个目录留在顶层（AGENTS.md 审核范围规则第 5 条）。本轮改用**根锚定**匹配重查：

- 扫描 **15,111** 个文本文件（`.py/.md/.tex/.json/.txt/.sh/.ps1/.yml/.cfg/.toml/.bib`）；
- 只看**门禁链 53 个脚本**（`tools/paper_audit/**`、`_p1428`、`_p1637`、`_p1454`、`audit_check.py`、
  `audit_pdf.py`、`verify_a23_fix.py`、`_p1181`、`_final_check_prl`、`_claim_ledger*`）：
  三个目录的**根级引用 = 0**；
- `tools/paper_audit/profiles.py` 与五份 `tools/paper_audit/freeze/*.json` 里的 **46 处** `_archive/`
  **全部是 `SUBMISSION/_archive/...`**（冻结路径，未动）⇒ **133 条冻结哈希不受影响**。

### 1.2 三次移动（逐条校验内容一致）

| 目录 | 文件数 | 新位置 | 引用处理 |
|---|---|---|---|
| `_archive/` | **251** | `弃用/08_历史归档/_archive/` | **无需改引用**（见 1.1） |
| `paper/` | **111** | `弃用/06_归档稿件/paper/` | 活引用 1 处已更新；**冻结叙述 2 处未改**（见 1.3） |
| `paper_review/` | **30** | `弃用/06_归档稿件/paper_review/` | 活引用 **5 处已更新** + docs 1 处 |

**校验方式（脚本内断言）**：每次移动前对源目录做 `{相对路径: (字节数, sha256)}` 清单，
移动后对目标目录再做一次，**三次均逐条相同**，且源目录不残留。
`弃用/` 现共 **1,005 文件**（首轮 613 + 本轮 392）。

### 1.3 引用处理明细

**已更新的活引用（7 处）**：

| 文件:行 | 原 | 新 |
|---|---|---|
| `paper_review_prl/MANUSCRIPT.md:3` | `paper_review/refs_all.json` | `弃用/06_归档稿件/paper_review/refs_all.json` |
| `paper_review_prl/MANUSCRIPT.md:4` | `paper_review/sections/evidence.md` | 同上，新路径 |
| `paper_review_prl/DRAFT_OUTLINE.md:16` | `paper_review/refs_all.json` | 同上 |
| `paper_review_prl/FIXES_2026-10-18.md:96` | `paper_review/refs_all.json` | 同上 |
| `paper_review_prl/FIXES_2026-10-18.md:111` | `paper_review/refs_all.json` | 同上 |
| `docs/commentary_compression_and_table.md` | `paper_review/sections/taxonomy.md` | 同上（2 处） |
| `paper3/README_是哪篇.md:12` | 目录清单里的 `paper/` | 标注 `paper/`（已移入 `弃用/06_归档稿件/paper/`） |

**一个真断点（移动后才发现，已修）**：`tools/_final_check_prl.py:19` 用**裸字符串**拼路径
`REFS = REPO / "paper_review" / "refs_all.json"`——**没有斜杠**，所以"带斜杠"的扫描漏掉了它，
移动后该门禁直接 `FileNotFoundError`。已改为
`REPO / "弃用" / "06_归档稿件" / "paper_review" / "refs_all.json"`，`_final_check_prl` 恢复
`✅ 全部通过，可投稿`。**这条已写入** `docs/PATH_MIGRATION_2026-10-25.md` 的教训段。

**刻意未改（冻结规则）**：

| 位置 | 内容 | 为什么不动 |
|---|---|---|
| `SUBMISSION/_archive/PaperA_Neurocomputing_2026-10-12_60pp/README.md` | 提到 `paper/` | 冻结提交包的历史叙述 |
| `SUBMISSION/_archive/_old/P1_PatternRecognition/README.md` | 提到 `paper/` | 同上 |
| `SUBMISSION/README.md`、`SUBMISSION/P3_PRL_resubmission/README.md` | 提到 `_archive/` | 同上 |

**历史一次性脚本**（`_p1170_organize.py`、`_p1467_fix_c07_and_refs.py` 等）仍写着旧路径——
按"存量脚本是记录、不是维护对象"的既有规则保留；重跑它们需要先改路径（属预期，已在迁移文档写明）。

---

## 二、Task B：活稿 DOI 升到 v2.5

### 2.1 变更清单（file:line，全部为 `→ 10.5281/zenodo.23632347`）

| # | 文件:行 | 原值 | 备注 |
|---|---|---|---|
| 1 | `paper合/main_nc.tex:87` | `23609295`（2 处，含 `\url`）+ 标签 `v2.3, 24 October 2026` | 标签改为 `v2.5, 25 October 2026` |
| 2 | `paper合/main_springer.tex:87` | `23609295` + `v2.3, 24 October 2026` | 同上 |
| 3 | `paper_a1/main.tex:1472` | `23609295` + `v2.3, 24 October 2026` | 同上 |
| 4 | `paper_a1/title_page.tex:36` | `23609295` + `v2.3, 24 October 2026` | 同上（与 main.tex 的数据声明重复，必须同步） |
| 5 | `paper_a2/main_ieee.tex:839` | `23609295` | 该句无版本标签，**未加**（不加新主张） |
| 6 | `paper_review_prl/main_prl.tex:218` | `23609295` | 同上 |
| 7 | `paper3/paper_ieee/main.tex:133-134` | `23523263`（2 处，含 `\url`） | 该句无版本标签，**未加**（P3 main 已满 10 页） |
| 8 | `paper3/paper_ieee/sections/conclusion.tex:49` | `23523263` | 同上 |
| 9 | `paper_a1/cover_letter.tex:104` | `23609295` | A1 工作包可刷新 ⇒ 投稿信须与稿件一致 |
| 10 | `paper_a1/cover_letter_paa_revision.tex:47` | `23609295` | 同上 |
| 11 | `paper合/cover_letter_nc.tex:116,117` | `23609295`（2 处） | Paper A 工作包可刷新 ⇒ 同上 |
| 12 | `paper合/cover_letter_nc_revision.tex:39` | `23609295` | 同上 |

### 2.2 **刻意没改**的 DOI（逐条给理由，不是漏改）

| 位置 | 现引用 | 为什么不动 |
|---|---|---|
| `SUBMISSION/_frozen_submitted/**` | 各自投稿时 DOI | **冻结铁律**：投出件保留原 DOI |
| `paper3/paper_ieee/cover_letter_prl.tex:80` | `23341223`（v1.0） | P3 **已投**的投稿信，记录当时事实 |
| `paper3/paper_ieee/cover_letter_prl_revision.tex:47` | `23341223` + "a newer archive version also exists" | 同上（已投修订信） |
| `paper_review_prl/RESPONSE_TEMPLATE.md:56` | `23341223`，原文写明 **"frozen Zenodo version DOI"** | 明确标注冻结 |
| `paper3/paper_ieee/PRL_submission/EM_author_classifications.txt:132` | `23341223` | EM 系统表单填写记录（历史） |
| `paper_a1/FIXES_2026-10-18.md`（5 处） | `23341223` | 历史修订日志，记录当时的核对结果 |

**概念 DOI**：五篇活稿**均未引用概念 DOI**（只引版本 DOI），故本轮无"概念 DOI 保留"的情形需要处理。

### 2.3 门禁针同步（避免门禁继续检查过期值）

| 文件:行 | 原针 | 新针 |
|---|---|---|
| `paper3/paper_ieee/audit_check.py:716` | `"10.5281/zenodo.23523263" in tex` | `"10.5281/zenodo.23632347" in tex` |
| `paper3/paper_ieee/audit_pdf.py:186` | `("Zenodo DOI", "10.5281/zenodo.23523263")` | `("Zenodo DOI", "10.5281/zenodo.23632347")` |
| `tools/_p1181_verify_paperA_consistency.py:82` | `"10.5281/zenodo.23609295"` | `"10.5281/zenodo.23632347"` |
| `tools/_p1637_p3_reproduce_all.py:1568` | 描述串 `version DOI 10.5281/zenodo.23523263` | 同上，新 DOI |
| `tools/_p1637_p3_reproduce_all.py:1569` | 值 `"10.5281/zenodo.23523263"` | 同上，新 DOI |

复核：四个门禁文件里旧 DOI 出现次数 **0**，新 DOI 已在位。

### 2.4 重编译结果（页数必须一点不变）

| 稿件 | 命令 | 页数 | 常量 | 错误 | 未定义引用 | 未定义引文 | overfull hbox/vbox |
|---|---|---|---|---|---|---|---|
| A1 `paper_a1/main.tex` | `pdflatex ×2` | **64** | 64 | 0 | 0 | 0 | 0 / 0 |
| Paper A NC `paper合/main_nc.tex` | `pdflatex ×2` | **79** | 79 | 0 | 0 | 0 | 0 / 0 |
| Paper A Springer `main_springer.tex` | `pdflatex ×2` | **56** | 56 | 0 | 0 | 0 | 0 / 0 |
| P3 `paper3/paper_ieee/main.tex` | `pdflatex ×2` | **10** | 10 | 0 | 0 | 0 | 0 / 0 |
| A23 `paper_a2/main_ieee.tex` | `pdflatex ×2` | **73** | 73 | 0 | 0 | 0 | 0 / 0 |
| Commentary `paper_review_prl/main_prl.tex` | `pdflatex ×2` | **7** | 7 | 0 | 0 | 0 | 0 / 0 |
| A1 投稿信 `cover_letter.tex` | `pdflatex ×2` | 2 | — | 0 | 0 | 0 | 0 |
| A1 修订信 `cover_letter_paa_revision.tex` | `pdflatex ×2` | — | — | 0 | 0 | 0 | 0 |
| Paper A 投稿信 `cover_letter_nc.tex` | `pdflatex ×2` | 3 | — | 0 | 0 | 0 | 0 |
| Paper A 修订信 `cover_letter_nc_revision.tex` | `pdflatex ×2` | — | — | 0 | 0 | 0 | 0 |

页数由 `tools/_p1664_rebuild_doi_pdfs.py` 从**新日志**读取（`Output written on … (N pages`），
并与 `tools/_p1454_final_verify.py :: PAGES` 常量逐一比对（该常量是运行时读取，不是硬编码，避免漂移）。

### 2.5 工作包刷新

`SUBMISSION/A1_PatternAnalysisApplications` 与 `SUBMISSION/PaperA_Neurocomputing` 是**可刷新的工作包**
（真正的投出件在 `SUBMISSION/_frozen_submitted/{A1_PAA,PaperA_NEUCOM,P3_PRL_R1}`，**未触碰**）。
DOI 改动后必须刷新，否则包内稿件与投稿信不一致：

`python tools/_p1576_refresh_a1_papera_packages.py --apply`
→ A1_PAA：live 64 页 / 241 词，source archive 21 条目；PaperA_NEUCOM：live 79 页 / 242 词，45 条目。

---

## 三、门禁结果（全部用 base 解释器 `D:\Anaconda\python.exe`）

| # | 门禁 | 退出码 | 结果 |
|---|---|---|---|
| 1 | `tools/_claim_ledger.py --apply` | 0 | 写入 `outputs/analysis/claim_ledger.json`（24 条主张全过） |
| 2 | `tools/_claim_ledger_a1.py --apply` | 0 | 写入 `claim_ledger_a1.json` |
| 3 | `tools/_claim_ledger_paperA.py --apply` | 0 | 写入 `claim_ledger_paperA.json` |
| 4 | `tools/_p1637_p3_reproduce_all.py --check --quiet` | 0 | **No mismatches**（955 OK / 0 MISMATCH / 993 条） |
| 5 | `tools/_p1428_provenance_gate.py` | 0 | `gate: PASS` |
| 6 | `paper3/paper_ieee/audit_check.py` | 0 | 0 hard failure / 0 warning |
| 7 | `paper3/paper_ieee/audit_pdf.py` | 0 | 0 hard failure / 0 warning |
| 8 | `paper_a2/verify_a23_fix.py` | 0 | `ALL CHECKS PASSED`（37 条冻结哈希） |
| 9 | `tools/_p1181_verify_paperA_consistency.py` | 0 | 0 failure |
| 10 | `tools/_final_check_prl.py` | 0 | `✅ 全部通过，可投稿` |
| 11 | `paper_audit a1_paa` | 0 | **READY grade A** pass=61 fail=0 warn=0 |
| 12 | `paper_audit paperA_nc` | 0 | **READY grade A** pass=67 fail=0 warn=0 |
| 13 | `paper_audit paperA_springer` | 0 | **READY grade A** pass=56 fail=0 warn=0 |
| 14 | `paper_audit p3_prl` | 0 | **READY grade A** pass=50 fail=0 warn=0 |
| 15 | `paper_audit a23_joe` | 0 | **READY grade A** pass=58 fail=0 warn=0 |
| 16 | `paper_audit prl_commentary` | 0 | **READY grade A** pass=57 fail=0 warn=0 |
| 17 | `tools/_p1454_final_verify.py --apply` | 0 | **ALL: PASS WITH 8 WARNING(S)**；`pages … pass: True`；`staged packages: True (wrong: [])`；`Commentary final check: True` |

**关于第 17 项那 8 条 warning（如实列出，不掩盖）**：7 条是
`[live_draft_newer_than_staged]` / `[stale_staged_snapshot]`——因为活稿刚重编译，而
`SUBMISSION/_frozen_submitted` 的 staged snapshot 仍停在 2026-10-24（**这是冻结件的正确状态**，
活稿与投出件本就应当不同）；1 条是 `[untracked_audit_reports]`（24 个 `docs/audits/AUD-*`，
是每次跑 profile 都会新生成的审计报告）。**这两类都归 task-23 的既有发现，本轮不处理。**

**重要：门禁的最终形态是在"提交之后"测的。** 提交前 `a1_paa/a23_joe/p3_prl/prl_commentary`
报 `A-01 uncommitted changes under <tree>`、`a1_paa/paperA_nc` 报 `I-02 package copies differ from
live files`——这两类都是**本轮改动的正常中间态**（未提交 / 工作包还没刷新），提交 + 刷新包后
全部转绿（见上表 11–16）。

---

## 四、**刻意保留的分歧**：已投冻结包 vs 活稿（务必记住）

- **P3 的已投冻结包仍写 v2.2（`10.5281/zenodo.23523263`）**，而**活稿现写 v2.5**。
  原因：投出件按冻结铁律保留投稿时的 DOI；活稿跟随最新归档 v2.5。
  ⇒ **提交件与活稿在 P3 的 DOI 上不一致是刻意的**，不是漏改。
- A1 与 Paper A 同样存在"投出件（`_frozen_submitted/`，写旧 DOI）vs 活稿（写 v2.5）"的分歧；
  它们的**工作包**已刷新到 v2.5，与活稿一致。
- Commentary 与 A23 的活稿写 v2.5；其投出件若已冻结则保留原 DOI。
- 该分歧已同步写入 `docs/P3_SUBMISSION_STATUS.md`（见 §五）与 `HANDOFF.md` 的 2026-10-25 条目。

---

## 五、文档同步

| 文件 | 内容 |
|---|---|
| `AGENTS.md` / `CLAUDE.md` | 审核范围规则第 5 条改写：三个例外已移入 `弃用/`，并纠正假阳性；原条目保留在 `<…>` 中供追溯 |
| `docs/PATH_MIGRATION_2026-10-25.md` | 新增 "Second pass" 段（三次移动 + 引用处理 + 冻结 README 情形 + 裸名引用教训）；原 "Deliberately NOT moved" 标题加删除线 |
| `docs/P3_SUBMISSION_STATUS.md` | 版本清单：v2.5 = current（`23632347`）；**v2.2 = 已投稿件所引 DOI，保持冻结** |
| `文件地图.md` | 顶部新增 `2026-10-25 12:05` 状态块（迁移 + DOI + 分歧提醒） |
| `HANDOFF.md` | 顶部新增 `2026-10-25 12:05` 节（迁移细节、DOI 清单、页数、门禁、分歧） |
| 本文件 | Task C 交付件 |

---

## 六、尚未处理 / 留给后续

1. **`publish_clean` 未改动**：本轮只动稿件、归档目录与工作包，**公开库不含稿件**（发布边界），
   故无需 push；本轮**未**产生新的 `publish_clean` 提交。
2. **历史一次性脚本**仍引用旧路径（`_p1170_organize.py`、`_p1467_fix_c07_and_refs.py` 等）：
   属"存量记录"，重跑前需改路径。
3. **`docs/audits/AUD-*`** 每次跑 profile 都会新增（本轮已提交了一批），
   与 `_p1454` 的 staged-snapshot 新鲜度警告一并归 **task-23**。
