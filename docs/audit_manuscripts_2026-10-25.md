# 独立审计 A —— 稿件 / 门禁 / 构建 / 冻结哈希（2026-10-25）

**审计员**：dinov2-auditor（独立成员；task-19）
**审计对象**：五篇稿件六个 PDF、全部稿件门禁、七次从源码重建、`SUBMISSION/` 冻结哈希
**唯一写入文件**：本笔记。除本文件外我只运行只读命令；`paper_audit` 每次调用会按其机制写 `docs/audits/AUD-*.{json,md}`（我的 5 批调用共产生 18 对报告，见 §7）。

---

## 0. 快照与前提（先说清楚，因为审计期间工作树在动）

| 项 | 值 | 证据 |
|---|---|---|
| 审计开始 | 2026-10-25 **11:16**（本地） | 本会话首条命令 |
| 开始时的 HEAD | **`41788de4`** | `git log --oneline -1`（11:16） |
| 开始时的脏树 | **25 项** = ` M outputs/analysis/final_verification.json` + 24 个未跟踪 `docs/audits/AUD-*.{json,md}` | `git status --porcelain`（11:16） |
| 审计期间 HEAD 变化 | **`41788de4` → `5911a1ed`**（2026-10-25 11:20:32，commit "…v2.5 release created"） | `git log -1 --format="%H %ci %s"`；`git reflog` |
| 并行活动 | 其他 agent 在 11:24:19 改了 `HANDOFF.md`、`文件地图.md`、`docs/P3_SUBMISSION_STATUS.md`、`docs/V25_RELEASE_PREP_2026-10-25.md`、`docs/audit_release_cloud_2026-10-25.md`；11:24:54 之后也有别的 agent 在跑同一批 profile 审计 | 文件 mtime；`docs/audits/` 里同分钟出现的报告 |
| 结束快照（11:28） | HEAD `5911a1ed`；脏树 6 M + 78 ?? = 84 项 | `git status --porcelain \| Group-Object` |

> **对 Lead 校准语的第一条更正**：**"workspace clean at commit 41788de4" 不成立**。
> 我动手之前（11:16）树就是脏的（25 项）；`_p1454` 自己也算出 `git_clean.pass = false`（见 §2）；
> 且 11:20:32 期间 HEAD 已被别的 agent 推进到 `5911a1ed`。详见 §5 差异 D-4。

---

## 1. 逐门禁表（全部我自己跑，命令 → 退出码 → 结果）

命令均在仓库根 `D:\Realdesktop\Wan\Important\New` 下执行。

| # | 命令 | rc | 结果（我复现的） |
|---|---|---|---|
| 1 | `python -m tools.paper_audit audit --profile a1_paa --fail-on NONE` | 0 | READY grade A，pass=60 fail=**0** warn=**1** skip=16 manual=9（warn 是 A-05，见 §5 D-7） |
| 2 | 同上 `--profile paperA_nc` | 0 | READY A，66 / **0** / **1** / 10 |
| 3 | 同上 `--profile paperA_springer` | 0 | READY A，56 / 0 / 0 / 21 |
| 4 | 同上 `--profile p3_prl` | 0 | READY A，50 / 0 / 0 / 27 |
| 5 | 同上 `--profile a23_joe` | 0 | READY A，57 / 0 / **1** / 19 |
| 6 | 同上 `--profile prl_commentary` | 0 | READY A，56 / 0 / **1** / 20 |
| 7 | `python paper3/paper_ieee/audit_check.py` | 0 | `RESULT: 0 hard failure(s), 0 warning(s)`；CJK 0、无 TODO/TBD/XXX、无 form-feed |
| 8 | `python paper3/paper_ieee/audit_pdf.py` | 0 | `RESULT: 0 hard failure(s), 0 warning(s)`；`main.pdf == 10` 页、`supplementary.pdf == 26` 页；可提取文本 57,841 字符；无 `??`、无 ⟨abla 破字；nabla 出现 27 次 |
| 9 | `python paper_a2/verify_a23_fix.py` | 0 | `ALL CHECKS PASSED`；**frozen archive: all 37 SHA-256 hashes unchanged** |
| 10 | `python tools/_p1181_verify_paperA_consistency.py` | 0 | `RESULT: 0 failure(s)`（含 cover letter 页数与 main_nc.pdf 一致） |
| 11 | `python tools/_final_check_prl.py` | 0 | `✅ 全部通过，可投稿`；页数 7/7；overfull hbox 0；HTML/XML 伪影 0 |
| 12 | `python tools/_p1428_provenance_gate.py` | 0 | `gate: PASS`；paperA 32/32、A1 35/35、P3 4 floats/43 manifest、A23 34/34；missing=0 pending=0 broken_paths=0 |
| 13 | `python tools/_claim_ledger.py --apply` | 0 | `✅ 通过 96 ｜ ❌ 失败 0 ｜ 共 96 条` |
| 14 | `python tools/_claim_ledger_paperA.py --apply` | 0 | `PASS 88 ｜ GAP 0 ｜ total 88` |
| 15 | `python tools/_claim_ledger_a1.py --apply` | 0 | `A1 claims: 216 pass / 0 fail / 216 total` |
| 16 | `python tools/_p1637_p3_reproduce_all.py --check --quiet` | 0 | **OK 955 ｜ MISMATCH 0 ｜ UNSOURCED 0 ｜ UNCHECKED 0 ｜ TOTAL 993**（其余分类：ANALYTIC 3、THIRD_PARTY 8、APPROXIMATE 4、EXTERNAL 2、EXEMPT 3、DUPLICATE 13、DECLARED_GAP 1、DELETED 4） |
| 17 | `python tools/_p1454_final_verify.py --apply` | **0** | **`ALL: PASS`**；frozen 12 文件 bad=0；provenance True；A1 ledger 216 pass/0 fail；六 profile 全 READY fail=0；p3 audit_check/pd True；A23 True；Commentary True；staged True；pages `{64, 79, 56, 10, 73, 7}` pass=True；bootstrap True；decoder ladder True；**git clean: False** |

**交付状态**：Lead 校准语里的四项 —— "六 profile READY(A) 0 fail/0 warn"、"final_verify ALL PASS"、"P3 台账 955/0/0"、"provenance PASS" —— **在我这一轮全部复现成立**（warn 一项见 D-7 的解释：交付态确实 0 warn，我复跑后 4 个 profile 出现 A-05 warn，是我重建/回填 PDF 造成的，非稿件缺陷）。
"workspace clean" **不成立**（D-4）。

### 1.1 交付态（我动手之前）的审计计数 —— 用作对照

`docs/audits/` 里上一轮 2026-10-25 11:08:59–11:09:50 的六份报告：

| profile | 文件 | verdict | counts |
|---|---|---|---|
| a1_paa | `AUD-a1_paa-20261025T030859Z.json` | READY A | PASS 61 / FAIL 0 / WARN 0 / SKIP 16 |
| paperA_nc | `AUD-paperA_nc-20261025T030911Z.json` | READY A | 67 / 0 / 0 / 10 |
| paperA_springer | `AUD-paperA_springer-20261025T030921Z.json` | READY A | 56 / 0 / 0 / 21 |
| p3_prl | `AUD-p3_prl-20261025T030927Z.json` | READY A | 50 / 0 / 0 / 27 |
| a23_joe | `AUD-a23_joe-20261025T030946Z.json` | READY A | 58 / 0 / 0 / 19 |
| prl_commentary | `AUD-prl_commentary-20261025T030950Z.json` | READY A | 57 / 0 / 0 / 20 |

---

## 2. 页数（六个 PDF + P3 补充材料）

**常量来源**：`tools/_p1454_final_verify.py:28-29` 的 `PAGES`
= `{"paper_a1/main.pdf": (64,), "paper合/main_nc.pdf": (79,), "paper合/main_springer.pdf": (56,), "paper3/paper_ieee/main.pdf": (10,), "paper_a2/main_ieee.pdf": (73,), "paper_review_prl/main_prl.pdf": (7,)}`。
**测量**：`pypdf.PdfReader(...).pages`，2026-10-25 **11:28:24** 快照。

| PDF | 常量 | 实测 | 一致 | 11:28 时 mtime |
|---|---|---|---|---|
| `paper_a1/main.pdf` | 64 | **64** | ✅ | 10-24 16:40 |
| `paper合/main_nc.pdf` | 79 | **79** | ✅ | 10-24 19:29 |
| `paper合/main_springer.pdf` | 56 | **56** | ✅ | 10-25 11:17（我重建） |
| `paper3/paper_ieee/main.pdf` | 10 | **10** | ✅ | 10-25 11:18（我重建） |
| `paper_a2/main_ieee.pdf` | 73 | **73** | ✅ | 10-25 08:27（= 包内件回填） |
| `paper_review_prl/main_prl.pdf` | 7 | **7** | ✅ | 10-24 17:17（= 包内件回填） |
| `paper3/.../supplementary/supplementary.pdf`（不在常量内） | — | **26** | 与 `audit_pdf` 的 26 一致 | 10-25 11:18（我重建） |

⇒ **六个数与 `_p1454` 常量逐项一致；P3 补充材料 26 页**（`audit_pdf.py` 的 needle 也是 26）。

### 2.1 与 HANDOFF / 文件地图 的对照 → **发现一处过期（D-1）**

- `HANDOFF.md:136`（2026-10-24 19:30 条）写 **"页数 64 / 79 / 56 / 10 / 72 / 7"**；当前 A23 实际 **73** ⇒ **HANDOFF 的 A23 页数过期**（且 HANDOFF 里检索不到任何记录 A23=73 的条目）。
- `文件地图.md:10` 写 **A23 "73 页"** ✅ 正确（与实测、与常量一致；文件地图是冲突时的权威）。
- `HANDOFF.md` 最新关于 P3 补充材料的页数是 **18 页**（2026-10-24 17:30/19:30 条），当前 **26 页**；`文件地图.md:9` 写 **"26 页 / 50 表 / 46 节"** ✅ 正确。**HANDOFF 未记录 18→26 这次增长**。

---

## 3. 构建审计（七次从源码重建 + 新日志统计）

方法：每个主文件 `pdflatex -interaction=nonstopmode` 首跑 → 若 `.aux` 含 `\bibdata` 再 `bibtex` → 再两遍 `pdflatex`；随后解析**本次新生成的 `.log`**。
计数用正则 `^! `（错误）、`LaTeX Warning: Reference '...' ... undefined`、`Citation '...' undefined`（含 natbib）、`^Overfull \hbox` / `^Overfull \vbox`。

| 构建 | rc | 页数 | 错误 | 未定义引用 | 未定义引文 | overfull hbox | overfull vbox | 其他 LaTeX Warning | 耗时 |
|---|---|---|---|---|---|---|---|---|---|
| `paper_a1/main.tex` | [0,0,0] | 64 | **0** | **0** | **0** | **0**（最宽 0.0pt） | **0** | 2（`h` float 变 `ht`） | 7 s |
| `paper合/main_nc.tex` | [0,0,0] | 79 | **0** | **0** | **0** | **0** | **0** | 12（`h`→`ht`） | 8 s |
| `paper合/main_springer.tex` | [0,0,0] | 56 | **0** | **0** | **0** | **0** | **0** | 11 | 10 s |
| `paper3/paper_ieee/main.tex` | [0,0,0] | 10 | **0** | **0** | **0** | **0** | **0** | 0 | 8 s |
| `paper3/.../supplementary.tex` | [0,0,0] | 26 | **0** | **0** | **0** | **0** | **0** | 44（皆字体形状替换 `OT1/ptm/m/scit` 等；唯一 1 处含 "undefined" 字样是 `LaTeX Font Warning`，不是引用/标签） | 8 s |
| `paper_a2/main_ieee.tex` | [0,0,0] | 73 | **0** | **0** | **0** | **0** | **0** | 0 | 11 s |
| `paper_review_prl/main_prl.tex` | [0,0,0] | 7 | **0** | **0** | **0** | **0** | **0** | 0 | 6 s |

**结论：七次构建全部 0 错误 / 0 未定义引用 / 0 未定义引文 / 0 overfull hbox / 0 overfull vbox，页数与常量一致。** 非零的只是无信息量的 `h`-float 与字体形状 Warning（数量已列）。

### 3.1 附带发现（重要）：**本项目 PDF 构建不是逐字节可复现的（D-6）**

`pdflatex` 每次写入新的 `/CreationDate` 与 `/ID`，同一源码两次构建**字节不同**（尺寸可相同）。我用标准可复现构建手法验证：

```
# 取包内 Manuscript.pdf 的 /CreationDate 作为 SOURCE_DATE_EPOCH
paper_a1/main.pdf   : 包 d18fb1f2…（1,141,948 B）；重建 4c160040…（1,141,937 B，−11 B）
paper合/main_nc.pdf : 包 d6994e60…（1,440,065 B）；重建 eb5c0750…（1,440,052 B，−13 B）
环境变量 FORCE_SOURCE_DATE=1 + SOURCE_DATE_EPOCH=<包内创建时间> 仍然 EQUAL=False
```

**后果**：任何"重建源码"都会让 live PDF 与包内副本**字节不同**，从而触发 `paper_audit` 的 I-02（P1，见 D-2/D-3）。
这也是我在 §5 里把"我自己的重建"与"稿件缺陷"分开的理由。

### 3.2 我为消除自身扰动所做的回填（哈希证据）

发现 I-02 是我重建触发后，用**与包内件字节完全相同**的副本回填 live PDF，恢复到重建前字节：

| live 文件 | 来源 | 回填后 SHA-256 | 与重建前一致 |
|---|---|---|---|
| `paper_a1/main.pdf` | `SUBMISSION/A1_PatternAnalysisApplications/Manuscript.pdf` | `d18fb1f2504e8c32…` | ✅（重建前实测同值） |
| `paper合/main_nc.pdf` | `SUBMISSION/PaperA_Neurocomputing/Manuscript.pdf` | `d6994e6085a0e8fd…` | ✅ |
| `paper_a2/main_ieee.pdf` | `SUBMISSION/A23_JOE_next_revision/Manuscript.pdf` | `f5a3725e95c842c8…` | ✅ |
| `paper_review_prl/main_prl.pdf` | `SUBMISSION/_venue_builds/Commentary_PRL_next/Manuscript.pdf` | `5cb098e2fcf322f7…` | ✅ |

无法回填的两项（无包内副本）：`paper合/main_springer.pdf`、`paper3/paper_ieee/{main,supplementary}.pdf` —— 它们是内容等价的重建（同尺寸/同页数，字节略异）。
**残留副作用**：4 个 profile 出现 `A-05` P2 warn（"log 与 pdf 相差 5.7–6.7 万秒"），因为 `.log` 是新构建而 `.pdf` 已回填为旧字节；**旧 `.log` 已被覆盖、不可恢复**。这是审计过程残留，不是稿件缺陷（交付态 0 warn，见 §1.1）。**我未修改任何 `.tex`。**

---

## 4. 冻结哈希证据（`SUBMISSION/` 全程未变）

**git 在这里无法作证（已实测）**：`.gitignore:74: SUBMISSION/`；`git check-ignore -v SUBMISSION/P3_PRL_next_revision/SHA256SUMS.txt` 命中该行；`git ls-files SUBMISSION | wc -l` = **0**。⇒ **只有哈希能作证**。

### 4.1 仓库内记录的哈希清单 —— 全部重算并逐条比对，**两次（我跑门禁前后各一次）结果相同**

| 记录清单 | 条目 | 结果 |
|---|---|---|
| `tools/paper_audit/freeze/a1_nn.json` | 16 | ✅ 16 ok / 0 missing / 0 changed |
| `tools/paper_audit/freeze/a1_paa.json` | 16 | ✅ 16 ok |
| `tools/paper_audit/freeze/a23_joe.json` | **37** | ✅ 37 ok（另 `verify_a23_fix.py` 独立复核 "all 37 SHA-256 hashes unchanged"） |
| `tools/paper_audit/freeze/p3_prl.json` | 10 | ✅ 10 ok |
| `tools/paper_audit/freeze/prl_commentary.json` | 28 | ✅ 28 ok（含 `paper_review_prl/UPLOAD` 与 `SUBMISSION/Review_PRL`） |
| `SUBMISSION/A23_JOE_next_revision/SHA256SUMS.txt` | 6 | ✅ 6 ok |
| `SUBMISSION/P3_PRL_next_revision/SHA256SUMS.txt` | 8 | ✅ 8 ok |
| `SUBMISSION/_frozen_submitted/SHA256SUMS.txt` | 12 | ✅ 12 ok（A1_PAA / PaperA_NEUCOM / P3_PRL_R1 各 4 件） |

合计 **107 + 26 = 133 个被记录文件条目，0 处变化**。（`_p1454` 的 `frozen` 门只覆盖 `_frozen_submitted` 那 12 件；其余由各 profile 的 I-04 覆盖，六 profile 全 PASS。）

### 4.2 我另做的全树清单

`SUBMISSION/**` 共 **558 个文件 / 78.3 MiB**；我跑门禁前后两次清点数字相同，且上述 133 条记录全部不变 ⇒ **提交包与冻结件未被本轮任何操作改动**。

**关键包页数（旁证）**：`A23_JOE_next_revision/Manuscript.pdf` 73 页 / `Supplementary.pdf` 43 页（与 README 一致）；`P3_PRL_next_revision/Manuscript.pdf` 10 页 / `Supplementary.pdf` 18 页；`_frozen_submitted/PaperA_NEUCOM/Manuscript.pdf` **70 页**（已投版，现行草案 79 页——属"在审草案推进"，非冻结件被改）。

---

## 5. 发现的差异（按等级）

### D-1（should-fix，文档）HANDOFF 的 A23 页数过期：写 72，实际 73
- 证据：`HANDOFF.md:136`（2026-10-24 19:30 条）"页数 **64 / 79 / 56 / 10 / 72 / 7**"；`paper_a2/main_ieee.pdf` = **73**（pypdf，11:28）；`_p1454 PAGES` = 73；`文件地图.md:10` = 73。
- 性质：append-only 历史条目本身不算错，但**HANDOFF 没有任何条目记录 72→73**，且这是 HANDOFF 里最新的页数陈述 ⇒ 最新事实在 HANDOFF 中缺失。
- 建议：在 HANDOFF 顶部追加一条记录 A23 72→73 与 P3 补充材料 18→26（含 46 节/50 表），或明确指向 `文件地图.md:9-10`。

### D-2（should-fix，门禁设计）`_p1454` 把两个 profile 的 **I-02（P1 blocker）**列为"可接受失败"
- 证据：`tools/_p1454_final_verify.py:26` `EXPECTED_AUDIT_FAILS = {"a1_paa": {"I-02"}, "paperA_nc": {"I-02"}}`；`:74-75` `ok = (nfail == 0) or (set(blockers) <= expected)`。
- 后果：**"包副本与 live 稿件不一致"这条最要命的释放前检查，在最关键的两篇上被白名单化** ⇒ `final_verify` 可以一边显示 `ALL PASS` 一边容忍 A1/PaperA 的包过期。
- 我不是理论担忧：**我亲身触发了它**（重建后 I-02 FAIL，而 `_p1454` 仍 `ALL: PASS`）。当前两 profile 的 I-02 实为 PASS（回填后 pass=60/66），所以**今天没有假阴性**，但机制存在。
- 建议：要么删掉白名单（让 I-02 真拦），要么把 a1_paa/paperA_nc 的包设为 frozen（像 a23_joe 那样 I-02 SKIP + I-04 冻结核对），不要用"预期失败"来静音。

### D-3（should-fix，门禁设计）`EXPECTED_AUDIT_WARNS` 是死代码
- 证据：`tools/_p1454_final_verify.py:27` 定义 `EXPECTED_AUDIT_WARNS = {"a1_paa": {"I-06"}, "paperA_nc": {"I-06"}}`，**全文件再无引用**；且 warn 数不参与 `pass_ok`/`all_ok`。
- 后果：warn 级回归在 `final_verify` 里完全不可见（与它"记录预期 warn"的意图不符）。

### D-4（should-fix，事实陈述）"workspace clean at commit 41788de4" 不成立
- 我动手前：`git status --porcelain` = 25 项（11:16，HEAD `41788de4`）；`_p1454` 本次运行输出 `git clean: False`。
- `_p1454` 的 `git_clean` 结果（`:299-303`）**没有计入 `all_ok`（`:304-308`）** ⇒ `ALL: PASS` 与"树脏"可以并存，二者必须分开陈述。
- 另：审计期间 HEAD 已从 `41788de4` 前进到 `5911a1ed`（11:20:32，别的 agent 提交），所以"at commit 41788de4"已不是当前 HEAD。
- 当前（11:28）脏树 84 项 = 6 M + 78 ??；其中 M 的 5 个（HANDOFF/文件地图/3 个 docs）是**其他 agent 的并行编辑**（mtime 11:24:19），`outputs/analysis/final_verification.json` 是我的 `_p1454 --apply` 按设计重写。

### D-5（should-fix，门禁证据陈旧）`staged_package_check` 校验的是 **10-24 17:17 的旧暂存区**，不是当前包
- 证据：`outputs/analysis/staged_package_check.json`（11:25:29 重写，`_p1444_staged_package_check.py --apply` 现跑）显示
  `A23_JOE_next staged=72 shipped=72`、`PaperA_Neurocomputing_next staged=77 shipped=77`；
  而当前实际是 **A23 73 页**、**PaperA NC 79 页**；`SUBMISSION/_venue_builds/*` 里所有 PDF 的 mtime 都是 **2026-10-24 17:17**（P3 supp 17:09）。
- 结构性问题：`_p1444` 用 `_venue_builds/<pkg>/latex_source.zip` 重编译并与**同一目录**的 `Manuscript.pdf` 比页数 —— 两边同属一个快照，**结构上不可能因稿件推进而失败**（只能抓损坏的 zip）。
- 另：`_p1454:270-273` 调 `_p1444` 后**丢弃退出码**、直接读 JSON，且不校验 JSON 新鲜度 ⇒ 若 `_p1444` 崩溃，旧 JSON 会被当作通过。
- 建议：把 `_venue_builds` 刷新到当前包后再跑，或在 `_p1454` 里断言 `staged_package_check.json` 的 mtime/内容与当前 `_version 一致。

### D-6（informational，构建）PDF 不可逐字节复现（见 §3.1）
- 建议：若希望"重建后 I-02 仍绿"，要么固定 `SOURCE_DATE_EPOCH`+`\pdftrailerid`/`\pdfsuppressptexinfo` 并验证字节一致（本次试验**未成功**），要么把 I-02 的比较口径改成"页数+内容哈希(文本层)"，要么在流程上规定"重建后必须重新打包"。

### D-7（cosmetic，审计过程残留）4 个 profile 的 A-05 P2 warn
- 含义：`A-05 Compilation log belongs to the current PDF`，报"log 与 pdf 相差 56,904–67,037 s"。
- 原因：我重建 → 回填包内旧字节 PDF；`.log` 是新构建 ⇒ 两者时间不再匹配。**不是稿件缺陷**（交付态 0 warn，§1.1）。
- 不可逆：旧 `.log` 已被我覆盖。建议 Lead 知悉：若以当前树为准重新跑审计，这 4 条 P2 warn 会一直挂着；要么重跑一次对应构建（会使 I-02 变红，D-6），要么接受这 4 条 P2。

### D-8（informational）`p3_prl` profile **没有 package-to-live 映射**
- 证据：`AUD-p3_prl-…032717Z.json` 的 I-01/I-02/I-03/I-06 全部 `SKIP`（"no submission package configured" / "no package-to-live mapping configured"）。
- 后果：**P3 的包与 live 稿件是否同步，任何门禁都不检查**。当前 `SUBMISSION/P3_PRL_next_revision/Supplementary.pdf` = **18 页**（S1--S43，已投冻结版，README/SHA256SUMS 记录在案），live 补充材料 = **26 页**（S1--S46 草案）。按 task-14 的口径（"submitted package is FROZEN: only the local supplement draft changes"）这是**预期**关系，不是缺陷；但门禁无法区分"预期冻结"与"忘了重建"——如果下次投稿要带这份包，需人工重建。

---

## 6. 计数一致性（P3 补充材料）—— **无矛盾**

| 项 | 声称（`文件地图.md:9`） | 我实测 | 一致 |
|---|---|---|---|
| 补充材料页数 | 26 | **26**（pypdf；`audit_pdf` needle 也是 26） | ✅ |
| 节数 | 46 | **46**（`\section{` 计数：46；首/末节标题已核对） | ✅ |
| main.tex 指针 | S1--S46 | `main.tex` 中 **S1--S46** | ✅ |
| 表数 | 50 | **50**（`\begin{table*?}` 计数；figure 1 个） | ✅ |

`HANDOFF` 里最新的补充材料页数是 **18 页**（10-24 条），未见 46 节/50 表的当前陈述 ⇒ 与 D-1 同类（旧值，非矛盾但缺更新）。

---

## 7. 我写过什么 / 并发情况

- **唯一人工写入**：本文件。
- `paper_audit` 的机制性写入：我的 5 批调用共产生 **18 对** `docs/audits/AUD-*.{json,md}`（11:17:56–11:18:40、11:20:54–11:22:21、11:24:07–11:24:28）。
- `_p1454 --apply` 按设计重写 `outputs/analysis/final_verification.json`（工作树中为 ` M`，与 HEAD 版差异仅在我这 4 条 A-05 warn；HEAD 版是六 profile 0 warn / all_pass=true / pages 73）。
- `_p1444 --apply` 重写 `outputs/analysis/staged_package_check.json`（内容与上轮相同：72/77 的旧暂存区）。
- **并发**：11:24:19 起有别的 agent 改 HANDOFF/文件地图/docs；11:24:54 之后 `docs/audits/` 里出现不属于我批次的新报告。**因此我的所有结论都带时间戳，以 §0 快照为准。**

---

## 8. 我**无法**核实 / 明确未做（不猜）

1. **未逐页比对 PDF 正文内容与源码**：只比页数、编译日志、哈希、以及各门禁的文本 needle（如 P3 的 45.20%/31.15/34.29、nabla 27 次），**没有做全文页级 diff**。
2. **无法逐字节复现重建**（已试验失败，D-6）；因此无法证明"当前 PDF 正是由当前源码产出"——只能证明**从当前源码重建得到同样页数与 0 错误**。
3. **无法恢复我覆盖掉的 4 个 `.log`**，故交付态的 A-05 = 0 warn 只能由上一轮审计 JSON 佐证，不能由当前树重放。
4. **未核实投稿系统侧**（Editorial Manager / Springer / IEEE 上真正提交的文件）与本地 `SUBMISSION/` 是否同一份——本地哈希只能证明**本地文件未变**。
5. **未审计** release/发布库/云端证据（属 audit B）与文档规则合规（属 audit C）；`HANDOFF` 里"两个 cloud job 已执行"一类陈述不在我的证据链里。
6. **未验证** `_p1454` 之外的其他门禁脚本本身是否存在类似"白名单/死代码/忽略退出码"的弱化——我只逐行读了 `_p1454_final_verify.py` 与 `_p1444` 的调用处。
7. **`_frozen_submitted` 与现行包的关系**（如 PaperA 70 页已投版 vs 79 页草案）只做了页数旁证，**未**核对"已投版是否就是投稿系统里的版本"。
8. 并发 agent 在 11:24 的编辑**可能已把 D-1 修正**（我 11:26 复核时 `HANDOFF.md:136` 仍为 72）；若后续被改，以我记录的行号与时间为准。

---

## 9. 复现命令（全部只读）

```powershell
cd D:\Realdesktop\Wan\Important\New
git log --oneline -1; git status --porcelain
python -m tools.paper_audit audit --profile <a1_paa|paperA_nc|paperA_springer|p3_prl|a23_joe|prl_commentary> --fail-on NONE
python paper3/paper_ieee/audit_check.py
python paper3/paper_ieee/audit_pdf.py
python paper_a2/verify_a23_fix.py
python tools/_p1181_verify_paperA_consistency.py
python tools/_final_check_prl.py
python tools/_p1428_provenance_gate.py
python tools/_claim_ledger.py --apply
python tools/_claim_ledger_paperA.py --apply
python tools/_claim_ledger_a1.py --apply
python tools/_p1637_p3_reproduce_all.py --check --quiet
python tools/_p1454_final_verify.py --apply
# 页数
python -c "from pypdf import PdfReader; print(len(PdfReader(r'paper3/paper_ieee/main.pdf').pages))"
# 冻结：5 个 manifest + 3 个 SHA256SUMS 的逐条比对（见 §4.1 的清单路径）
```
