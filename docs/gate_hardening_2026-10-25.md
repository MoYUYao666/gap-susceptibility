# 最终门禁加固报告（task-23，2026-10-25）

**来源**：独立审计 A（`docs/audit_manuscripts_2026-10-25.md`）的 D-2/D-3/D-4/D-5 四条发现。
**改动文件**：仅 `tools/_p1454_final_verify.py`（+ 本报告；`docs/audits/` 下由重跑机制生成/覆盖的报告属门禁自身产物）。
**改动量**：旧版（`41788de4`，299 行）→ 新版（HEAD `dd37b361`，**610 行**）：`git diff --stat 41788de4 HEAD -- tools/_p1454_final_verify.py` = `+360 / −32`。
**解释器**：按 2026-10-25 新规，全部门禁用 **base** `D:\Anaconda\python.exe`（训练环境缺 `pypdf` 会伪装成 BLOCKED）。

## 0. 快照（工作树在本任务期间一直在动）

| 时点 | HEAD | 脏树 | 备注 |
|---|---|---|---|
| 任务开始 11:32:02 | `2aa635ce` | **85** | v2.5 DOI backfill 之后 |
| 门禁首次运行 11:36:50 | `26c0bc8b` | 6 | P3 S41 官方对比集成提交 |
| 门禁最终运行完成 11:40:04 | `dd37b361` | 0（跑时） | 期间其他 agent 提交 3 次 |
| 本报告定格 11:44:31 | `dd37b361` | **14** | = 本报告文件 + `M outputs/analysis/final_verification.json` + 12 个严格模式诊断跑新生成的 `docs/audits/AUD-*`（均属本轮产物） |

> 期间其他 agent 的 `git add -A` 提交把我的三个中间版本都扫进了提交历史（`c00f68e3`→`26c0bc8b`→`dd37b361`）；
> 最终磁盘内容与 HEAD 的 `tools/_p1454_final_verify.py` **一致**（`git diff HEAD -- <file>` 为空）。

---

## 1. 逐条修复（每条都保持既有硬检查不变）

### D-2（最高价值）：静默白名单 → **显式、具名、上报的接受通道**
- **旧行为**（`41788de4:tools/_p1454_final_verify.py:26` + `:74-75`）：
  `EXPECTED_AUDIT_FAILS = {"a1_paa": {"I-02"}, "paperA_nc": {"I-02"}}` 且 `ok = (nfail == 0) or (set(blockers) <= expected)`
  ⇒ 两篇最重要的稿件的 **P1 blocker “package copies differ from live files” 被静默放行**，`ALL: PASS` 可与过期包并存。
- **新行为**：
  - `EXPECTED_AUDIT_FAILS` **删除**；改为 `ACCEPTED_DEVIATIONS`（`:54`）——每条显式写明 `checks` / `package` / `reason`（"已投版本在审、包冻结在快照日、本地草案在推进，因此包与 live 不一致是合法的"）。
  - `classify_audit_result()`（`:122`）把每个 `BLOCKER` 分成 **hard**（不接受）或 **accepted**（接受）；接受的条目在运行期解析出**包快照日期**（`package_snapshot()` 取包目录最新 mtime + 文件数）并**计入 WARN 总数**。
  - 硬不变量（`:615`）：`assert not (hard and verdict.startswith("PASS"))` —— **只要存在未被接受的硬失败，总体判决不可能是 PASS**。
  - 新增开关 **`--no-accepted-deviations`**（`:409`）：把所有"接受"变成硬失败，用于给出"零容忍读法"的同树判决（决定可见，不靠隐含）。
  - 若审计报了 `nfail>0` 却解析不出 blocker id ⇒ 一律 **hard**（无法命名=不能接受）。

### D-3：死代码 `EXPECTED_AUDIT_WARNS` → **删掉，改成真正生效的 warn 通道**
- `EXPECTED_AUDIT_WARNS`（旧 `:27`）全文件从未被引用 ⇒ 删除。
- `check_audit()`（`:150-185`）现在从本次审计刚写出的 `AUD-*.json` 里读出**具体 WARN 条目**（check id + 严重度 + 标题），逐条进 `warnings`，并出现在判决行：
  `VERDICT: PASS WITH N WARNING(S)`（N = 实际 warning 数 + accepted deviation 数）。
- 若 JSON 解析失败但审计自报 `warn>0`，仍会产生一条"details unavailable"的 warn（不吞掉计数）。

### D-4：`git_clean` 只打印不参与判决 → **进入判决行，且给出精确计数与路径**
- 旧行为（`:299-308`）：`git_clean` 计算后**不进入 `all_ok`** ⇒ `ALL: PASS` 与 `git clean: False` 并列。
- 新行为：
  - 每次运行记录 `head_at_start` / `head_at_finish`；
  - 脏树**分类**（`:567` 起）：`dirty_other`（真实未提交工作）与 `dirty_audit_reports`（历次审计运行遗留的报告），分别计数并各自产生具名 warn（`dirty_tree` / `untracked_audit_reports`），**完整路径列表写进 JSON**；
  - **精确排除**两类自身产物：`outputs/analysis/final_verification.json`（本脚本输出）与**本次运行刚生成的** `docs/audits/AUD-*`（从审计输出解析出的 `json:`/`markdown:` 路径）。
  - **判决行强制带解释**：只要 `git_clean=False`，`VERDICT:`/`ALL:` 行就带
    `| git_clean=False: N uncommitted path(s) = X pending + Y leftover audit report(s); this run's own output excluded`
    ⇒ **不可能出现裸 `ALL: PASS` 与 `git clean: False` 并存**。

### D-5：staged 包校验陈旧 → **保留 `_p1444` 退出码 + 完整性检查 + 新鲜度检查**
- 旧行为（`:270-274`）：调 `_p1444 --apply` 后**丢弃退出码**、直接读 JSON、只按 `status/page_match` 判 pass
  ⇒ 校验的是 `SUBMISSION/_venue_builds/` 的 **2026-10-24 17:17 快照**（A23 72 页、PaperA 77 页），而 live 草案已是 73/79；且 `_p1444` 用**同目录**的 zip 重编译对比**同目录**的 PDF，结构上不可能因稿件推进而失败。
- 新行为：
  - **不丢退出码**：`_p1444` 非 0 ⇒ hard failure（其 JSON 证据不可信）；
  - JSON 缺包/读不出 ⇒ hard failure；
  - **新鲜度** `check_staged_freshness()`（`:357`）：逐包记录**快照时间戳**与 live 草案时间戳、重测 shipped/live 页数、并与 JSON 记录值交叉比对；差异产生具名 warn：
    `stale_staged_snapshot`（页数不一致）/ `live_draft_newer_than_staged`（live 更新）/ `stale_staged_record`（JSON 记录本身过期）。
  - 结果写进 JSON `staged_freshness.rows`，`PASS` 不再可能是"陈旧"的沉默 PASS。

### 判决语义（明确写进 docstring `:1-27`）
- `PASS`：所有硬门禁过且无任何报告项；
- `PASS WITH N WARNING(S)`：硬门禁全过，但有 N 项**被报告**的偏差（含 accepted deviation）；
- `FAIL`：任一硬门禁失败，或存在未被接受的 blocker；
- **退出码**：0 ⇔ 无硬失败（warnings 不阻塞——否则多 agent 并行、审计报告未提交的常态会让门禁永远红；零容忍读法用 `--no-accepted-deviations` 一遍即可）。
- **未削弱任何既有硬检查**：frozen 12 文件、provenance、A1 ledger 216、六 profile 的非接受失败、P3 双审计、A23 37 hash、Commentary、staged 编译/页匹配、六 PDF 页数、bootstrap 集成、decoder-ladder 集成、`git status` 自身 rc —— 全部照旧为 hard。

---

## 2. 判决文本 before / after（逐字）

**BEFORE**（旧版，审计 A 的 11:24 运行 + 提交版 JSON `41788de4:outputs/analysis/final_verification.json`）：
```
  staged packages: True []
  pages: {...} pass: True
  git clean: False
  ALL: PASS
```
（warn 不显示；`a1_paa`/`paperA_nc` 的 I-02 若失败会被 `EXPECTED_AUDIT_FAILS` 静默吃掉——审计 A 在 11:17 亲自触发过：`BLOCKER I-02 P1` 与 `ALL: PASS` 同时出现；staged 快照 72/77 被判 pass。）

**AFTER 默认模式**（11:40，HEAD `dd37b361`，树干净）：
```
  audit a1_paa: READY fail=0 warn=1 ok=True
  audit paperA_nc: READY fail=0 warn=1 ok=True
  audit paperA_springer: READY fail=0 warn=0 ok=True
  audit p3_prl: READY fail=0 warn=0 ok=True
  audit a23_joe: READY fail=0 warn=1 ok=True
  audit prl_commentary: READY fail=0 warn=1 ok=True
  staged packages: True wrong: [] | freshness warnings: 5
  git clean: True dirty_paths: 0 (self-output excluded: 0, this-run audit reports excluded: 0)
  WARNINGS (9):
    - [audit_warn:a1_paa:A-05] ...
    - [audit_warn:paperA_nc:A-05] ...
    - [audit_warn:a23_joe:A-05] ...
    - [audit_warn:prl_commentary:A-05] ...
    - [stale_staged_snapshot] staged snapshot (2026-10-24 17:17:24) has 72 pages but the live draft paper_a2/main_ieee.pdf has 73 pages
    - [live_draft_newer_than_staged] live draft paper_a2/main_ieee.pdf is newer ... (2026-10-25 08:27:43 vs 2026-10-24 17:17:24)
    - [live_draft_newer_than_staged] live draft paper3/paper_ieee/main.pdf is newer ...
    - [stale_staged_snapshot] staged snapshot (2026-10-24 17:17:25) has 77 pages but the live draft paper合/main_nc.pdf has 79 pages
    - [live_draft_newer_than_staged] live draft paper合/main_nc.pdf is newer ...
  VERDICT: PASS WITH 9 WARNING(S)
  ALL: PASS WITH 9 WARNING(S)
```

**AFTER 严格模式**（`--no-accepted-deviations`，11:42；此时树上有上一条运行遗留的 12 个审计报告）：
```
  audit a1_paa: READY fail=0 warn=1 ok=True      # 六个 profile 与默认模式完全相同
  ...
  git clean: False dirty_paths: 12 (self-output excluded: 1, this-run audit reports excluded: 0)
  WARNINGS (10):
    ... 4× A-05 + 5× staged 陈旧 ...
    - [untracked_audit_reports] 12 untracked docs/audits/AUD-* file(s) left over from earlier audit runs: ?? docs/audits/AUD-a1_paa-...json; ...
  VERDICT: PASS WITH 10 WARNING(S) | git_clean=False: 12 uncommitted path(s) = 0 pending + 12 leftover audit report(s); this run's own output excluded
  ALL: PASS WITH 10 WARNING(S) | git_clean=False: 12 uncommitted path(s) = 0 pending + 12 leftover audit report(s); this run's own output excluded
```

**FAIL 分支的真实证据**（11:36:55 第一次加固后运行，恰好撞上并行的 P3 编辑）：
```
  audit p3_prl: BLOCKED fail=1 warn=0 ok=False
  ...
  git clean: False dirty_paths: 2 ...
  VERDICT: FAIL | git_clean=False: 2 uncommitted path(s), self-output excluded
  ALL: FAIL | git_clean=False: 2 uncommitted path(s), self-output excluded
  # exit code = 1
```
13 秒后同一 profile：`AUD-p3_prl-20261025T033732Z.json` = READY 50/0/0 —— 是并行 agent 编辑期的**瞬时不一致**，不是稿件缺陷，也不是门禁误报（旧门禁同样会 FAIL）。**教训**：最终门禁必须在**已提交、静止**的树上跑（新 JSON 现在自动记录 `head_at_start/head_at_finish`）。

---

## 3. 六个稿件：before / after / 严格模式（今天实际结果）

| profile | 旧门禁（审计 A，11:24） | 新门禁·默认 | 新门禁·`--no-accepted-deviations` | 备注 |
|---|---|---|---|---|
| a1_paa | READY 61/0/0 | READY **60/0/1** | READY **60/0/1** | 若 I-02 失败：旧=静默放行；新=具名 accepted deviation（warn） |
| paperA_nc | READY 67/0/0 | READY **66/0/1** | READY **66/0/1** | 同上 |
| paperA_springer | READY 56/0/0 | READY 56/0/0 | READY 56/0/0 | — |
| p3_prl | READY 50/0/0 | READY 50/0/0 | READY 50/0/0 | 11:36:55 曾瞬时 BLOCKED（并行编辑） |
| a23_joe | READY 58/0/0 | READY **57/0/1** | READY **57/0/1** | — |
| prl_commentary | READY 57/0/0 | READY **56/0/1** | READY **56/0/1** | — |

**PASS 少 1 / WARN 多 1 的原因**：`A-05 Compilation log belongs to the current PDF` —— 是**审计 A 的重建-回填残留**（D-7：live PDF 回填为包内旧字节、`.log` 是新构建），**与本轮加固无关**，且现在被如实上报（旧门禁里它只是"不可见的 warn"）。

### 关于"是否干脆删掉白名单"的判断（Lead 的 note 1）
- **今天两种模式结果完全相同**（六 profile READY、fail=0、accepted=0）⇒ **删掉白名单不会让任何稿件变红**。
- **我的建议：保留"具名接受通道"，不要恢复静默白名单，也不必彻底删除接受机制。** 理由：本项目长期处于"已投版本在审 + 本地草案推进"的状态（A1/PAA、Paper A/NEUCOM 都是 With Editor），"包与 live 不一致"是能持续数周的**合法**状态；若把它做成硬失败，门禁会长期红，反而促使人们绕过它。现在的实现让该状态**必须具名、带包快照日期、计入 WARN**，且可用 `--no-accepted-deviations` 一键切换零容忍读法 ⇒ 决定可见、可审计。
- 若 Lead 选择零容忍：冻结前用 `--no-accepted-deviations` 跑一次，并在任何重建后先走包刷新脚本再跑（见 D-6）。

---

## 4. 自检证据（合成用例，不写仓库）

`python tools/_p1454_final_verify.py` 的判定逻辑单独用 7 个合成 case 验证（临时脚本）：
```
a. a1_paa nfail=1 blocker=I-02 接受开启  -> hard=[] accepted=[I-02, package=SUBMISSION/A1_PatternAnalysisApplications, snapshot=2026-10-24 19:29:46, reason=...] => PASS WITH 1 WARNING
b. 同上，--no-accepted-deviations        -> hard=[I-02]  accepted=[]  => FAIL
c. a1_paa nfail=1 blocker=I-04（未列）   -> hard=[I-04]  accepted=[]  => FAIL
d. a1_paa nfail=1 但 blocker 解析不到     -> hard=[?]     accepted=[]  => FAIL
e. a1_paa nfail=0                        -> PASS
f. paperA_nc nfail=1 blocker=I-02        -> accepted=[I-02] => PASS WITH 1 WARNING
g. paperA_nc nfail=2 blocker=[I-02,I-04] -> hard=[I-04] + accepted=[I-02] => FAIL  ← 关键：接受项不掩护硬失败
SELFTEST: PASSED
```

## 5. 回归（本轮全部重跑，全绿）

| 命令 | rc | 结果 |
|---|---|---|
| `D:\Anaconda\python.exe tools\_p1454_final_verify.py --apply` | 0 | `PASS WITH 9 WARNING(S)`；hard=0、frozen 12/12、pages 全对、6 profile READY fail=0 |
| `... _p1454_final_verify.py --no-accepted-deviations`（对照） | 0 | `PASS WITH 10 WARNING(S)`（多一条遗留审计报告 warn）；六 profile 同为 READY fail=0 |
| `python paper3/paper_ieee/audit_check.py` | 0 | `RESULT: 0 hard failure(s), 0 warning(s)` |
| `python paper3/paper_ieee/audit_pdf.py` | 0 | `RESULT: 0 hard failure(s), 0 warning(s)`；main 10 页 / supp 26 页 |
| `python paper_a2/verify_a23_fix.py` | 0 | `ALL CHECKS PASSED`（37 frozen hashes 不变） |
| `python tools/_p1181_verify_paperA_consistency.py` | 0 | `RESULT: 0 failure(s)` |
| `python tools/_final_check_prl.py` | 0 | `✅ 全部通过，可投稿`；7/7 页 |
| `python tools/_p1428_provenance_gate.py` | 0 | `gate: PASS`（paperA 32、A1 35、P3 43、A23 34，missing/pending/broken 0） |
| `python tools/_claim_ledger.py --apply` | 0 | **96 通过 / 0 失败** |
| `python tools/_claim_ledger_paperA.py --apply` | 0 | **PASS 88 / GAP 0 / total 88** |
| `python tools/_claim_ledger_a1.py --apply` | 0 | **216 pass / 0 fail** |
| `python tools/_p1637_p3_reproduce_all.py --check` | 0 | **OK 983 / MISMATCH 0 / UNSOURCED 0 / UNCHECKED 0 / TOTAL 1021**（并行 agent 在 11:36 的 S41 提交把边界从 955/993 扩到 983/1021，非本轮改动） |

**新报告里的实际脏树计数**：默认运行结束时 `git clean: True, dirty_paths: 0`；本报告定格时（11:44:31）为 **14** = 本报告文件 + 1 个本脚本输出 + 12 个严格模式诊断跑新生成的 `docs/audits/AUD-*`（本轮产物；下一次提交扫入即可清空；门禁会把遗留报告作为 `untracked_audit_reports` warn 如实列出，而不是隐藏）。

---

## 6. 开放项（结构性，请求登账）

### D-6：PDF **不是逐字节可复现**的 ⇒ 任何重建都会打破 I-02
- 证据（审计 A）：用 `FORCE_SOURCE_DATE=1 + SOURCE_DATE_EPOCH=<包内 /CreationDate>` 重建，仍
  `paper_a1/main.pdf` 1,141,937 B vs 包 1,141,948 B（**−11 B**）、`paper合/main_nc.pdf` 1,440,052 vs 1,440,065（**−13 B**），哈希不等。
- 后果：`paper_audit` 的 I-02（包副本 vs live 文件，P1）依赖**字节相等**；重建一次就需要把包内 PDF 回填/刷新，否则出现"看似包过期"的 p1。审计 A 就踩了这个坑（随后回填恢复）。
- 建议：(1) **短期流程**：任何重建后先跑包刷新（`tools/_p1576_refresh_a1_papera_packages.py --apply` / `tools/_p1445_rebuild_packages.py`）再跑最终门禁；(2) **中期**：试 `\pdfsuppressptexinfo`、`\pdftrailerid{}`、`\pdfinfoomitdate` 等字节稳定开关 + `SOURCE_DATE_EPOCH`，验证两次构建哈希一致后写入构建脚本；(3) **备选**：把 I-02 的比较从字节哈希改为**内容级**（页数 + 抽出文本哈希），需要改 `tools/paper_audit/`（不在本任务写入范围）。

### D-8：`p3_prl` profile **没有 package-to-live 映射**，P3 包/live 分歧无门禁可查
- 证据：`AUD-p3_prl-*.json` 的 I-01/I-02/I-03/I-06 全部 `SKIP`（"no submission package configured" / "no package-to-live mapping configured"）；`p3_prl` 的 `freeze_paths` 只覆盖已拒/归档树。
- 现状：`SUBMISSION/P3_PRL_next_revision/Supplementary.pdf` = **18 页（S1--S43，已投冻结版）**，live 补充材料 = **26 页（S1--S46 草案）**。按 task-14 的口径（submitted package is FROZEN）这是**预期**差异，但门禁无法区分"预期冻结"与"忘了重建"。
- 建议：在 `tools/paper_audit/profiles.py` 的 `p3_prl` 里显式声明（照 `a23_joe` 的做法）冻结包 `SUBMISSION/P3_PRL_next_revision` + `package_frozen=True` + freeze manifest，使 I-04 覆盖它、I-02 的 SKIP 有明确依据；等下一轮真正准备修订包时，再换成 package-to-live 映射（届时 I-02 会自动开始检查）。此项需改 `profiles.py`（不在本任务写入范围）。

### 观察（非缺陷）：多 agent 并行时门禁判决会瞬变
- 证据见 §2 FAIL 分支（p3_prl 11:36:55 BLOCKED → 11:37:32 READY）。建议：**最终一次 `_p1454 --apply` 在提交后、无人在写的窗口跑**，并核对 JSON 的 `head_at_start == head_at_finish`（本轮已自动记录；若两者不同，说明跑的过程中树又动了，应重跑）。

---

## 7. 局限（明确未做）

1. 未改 `tools/paper_audit/`（profiles/checks）；D-6 的内容级比较与 D-8 的 profile 映射只能作为建议（超出本任务写入范围）。
2. 未刷新 `SUBMISSION/_venue_builds`（属包/归档，禁止改）；因此 staged 陈旧 warn 会持续存在，直到下次打包轮。
3. 未消除审计 A 留下的 4 条 `A-05` warn（需要重建并刷新包，会撞 D-6；且 `.log` 已不可恢复）——现在它们被**如实上报**而不是隐藏。
4. `--no-accepted-deviations` 的"零容忍"分支今天没有**真实**失败样本（accepted=0），其正确性由 §4 合成用例 (b)/(g) 证明。
5. 未对 `_p1444`/其它门禁脚本做同类加固（写入范围只允许 `_p1454`）；`_p1444` 的"同快照自比"结构问题已由 `_p1454` 侧的新鲜度检查补偿，但脚本本身未改。
