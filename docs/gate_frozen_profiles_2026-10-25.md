# 冻结包 profile 扩展（2026-10-25）：a1_paa / paperA_nc / paperA_springer / prl_commentary

**背景**：A1 修订后 `paper_a1/main.pdf` 与 2026-10-18 已投冻结包合理分叉，`paper_audit --profile a1_paa` 被 **I-02（P1）** 判 BLOCKED。
`a23_joe`/`p3_prl` 已用 `package_frozen=True` + freeze manifest 解决同类问题；本轮把同一模式扩到其余四个"live 稿会合法分叉"的 profile。
**写入范围**：`tools/paper_audit/**`、`outputs/analysis/claim_ledger_a1.json`、本文件。**未动稿件、未动 `SUBMISSION/**`、未 commit。**

## 1. 四个 profile 的冻结声明（`tools/paper_audit/profiles.py`）

| profile | package（冻结目录） | package_expected | package_map（包文件 → live 文件） | freeze_paths 新增 |
|---|---|---|---|---|
| `a1_paa` | `SUBMISSION/A1_PatternAnalysisApplications` | 5（Manuscript/Title Page/Cover Letter/latex_source.zip/README） | Manuscript→main.pdf、Title Page→title_page.pdf、Cover Letter→cover_letter_paa.pdf（原有） | `SUBMISSION/A1_PatternAnalysisApplications` |
| `paperA_nc` | `SUBMISSION/PaperA_Neurocomputing` | 7（Manuscript/Cover Letter/Highlights.pdf/Highlights.txt/Abstract/latex_source.zip/README） | Manuscript→main_nc.pdf、Cover Letter→cover_letter_nc.pdf、Highlights→…、Abstract→abstract_nc.pdf（原有） | `SUBMISSION/PaperA_Neurocomputing` |
| `paperA_springer` | `SUBMISSION/PaperA_Neurocomputing`（Springer 版是同一 Paper A 内容的渲染，不是独立投稿） | 7（同上） | Manuscript→main_nc.pdf | `SUBMISSION/PaperA_Neurocomputing` |
| `prl_commentary` | `SUBMISSION/Review_PRL` | 3（main_prl.pdf / cover_letter.pdf / highlights.pdf） | 同名一对一 | 无（`SUBMISSION/Review_PRL` 原本已在 freeze_paths 内） |

四者都设 `package_frozen=True`；`BASE_PROFILE["package_frozen"] = False` 保持默认未变；`a23_joe`/`p3_prl` 未改动（无回退）。

## 2. 冻结清单（`tools/paper_audit/freeze/<profile>.json`）

| profile | 冻结条目 before → after | 旧条目哈希 | 校验 |
|---|---|---|---|
| `a1_paa` | **16 → 49（+33）** | 全部保持不变（断言 `old-hashes-unchanged=True`，removed=0） | `added=[] removed=[] changed=[] n=49` |
| `paperA_nc` | **0 → 54（新建）** | 新建 | `n=54` |
| `paperA_springer` | **0 → 54（新建）** | 新建 | `n=54` |
| `prl_commentary` | **28 → 28** | 全部不变（包目录原本已覆盖） | `n=28` |
| `a23_joe` / `p3_prl` / `a1_nn`（对照，未改） | 37 / 19 / 16 | — | `changed=[]` |

计数高于顶层文件数的原因：`tree_hashes` 递归包含 `latex_source/`、`figures/`、`UPLOAD/` 子目录
（A1 包 33 文件、PaperA 包 54 文件、Review_PRL 23 文件 + `paper_review_prl/UPLOAD`）。
`paper_audit selftest` → **SELFTEST PASSED**（`frozen files verified: 257` = 16+49+37+19+28+54+54）。

## 3. I-02 语义（为什么是 WARN 而不是 FAIL）

`check_I02` 的冻结分支（`tools/paper_audit/checks.py`）本轮加强为逐对报告：
**包路径 + 包内文件数 + 快照日期（目录最新 mtime，UTC）+ 每对映射的页数/字节/文本分歧 + 明确指向 I-04（冻结哈希）**。
非冻结 profile 的字节/内容比较逻辑完全不变（真差异仍硬失败）。单元验证（本轮实测）：

```
frozen(a1_paa)   status = WARN
  evidence: package=SUBMISSION/A1_PatternAnalysisApplications (33 files) snapshot=2026-10-25 04:14 UTC;
            deliberately not compared with the live draft ... Integrity is verified by I-04 (frozen hashes).
            Diverged: Manuscript.pdf 64 pp = 64 pp, text differs.
            Unchanged: Title Page.pdf byte-identical; Cover Letter.pdf byte-identical.
non-frozen(stale) status = FAIL | package copies differ from live files
  evidence: Manuscript.pdf != main_zh.pdf (CONTENT differs: pages 64 vs 22, text sha ... )
frozen(stale)     status = WARN
→ SEMANTICS OK: frozen -> WARN (named), non-frozen stale -> FAIL
```

注：warning 里的 `snapshot=` 取的是**包目录最新 mtime**。A1 与 PaperA 的包在 2026-10-25 04:14 UTC 由授权刷新脚本重写过（README / latex_source / 图），但 `Manuscript.pdf` 等冻结件内容仍等于已投版本（I-04 的哈希基线已覆盖当前状态）；因此该日期是“目录快照日”，不是“投稿日”。

registry 里 I-02 的 method 描述同步更新为"frozen package 以具名 warning 报出 package 路径/快照/文件数/逐文件页与文本分歧，并指向 I-04；绝不静默跳过"。

## 4. 六 profile 判决（base 解释器，`--fail-on NONE`，逐字）

```
a1_paa            BLOCKED  grade D  pass=58 fail=1 warn=1 manual=9 skip=17 error=0
paperA_nc         READY  grade A  pass=66 fail=0 warn=1 manual=9 skip=10 error=0
paperA_springer   READY  grade A  pass=61 fail=0 warn=1 manual=9 skip=15 error=0
p3_prl            READY  grade A  pass=54 fail=0 warn=1 manual=9 skip=22 error=0
a23_joe           BLOCKED  grade D  pass=57 fail=1 warn=1 manual=9 skip=18 error=0
prl_commentary    BLOCKED  grade D  pass=57 fail=1 warn=2 manual=9 skip=17 error=0
```

**I-02 在六个 profile 上全部是具名 WARN**（无一个 FAIL）：
- `a1_paa`：`Diverged: Manuscript.pdf 64 pp = 64 pp, text differs; Title Page/Cover Letter byte-identical`
- `paperA_nc` / `paperA_springer`：`package=SUBMISSION/PaperA_Neurocomputing (54 files) snapshot=…`（正文/高亮等分叉）
- `p3_prl`：`package=SUBMISSION/P3_PRL_resubmission (9 files) snapshot=2026-10-21 09:13 UTC`
- `a23_joe`：`package=SUBMISSION/A23_JOE (37 files) snapshot=2026-10-12 08:44 UTC`
- `prl_commentary`：`package=SUBMISSION/Review_PRL (23 files) snapshot=2026-10-12 09:14 UTC, Diverged: main_prl.pdf 7 pp …`

**三个 BLOCKED 的唯一 FAIL 都是 `A-01`（该稿目录有未提交改动），不是 I-02**：
- `a1_paa`：`M paper_a1/main.tex`、`M paper_a1/related_work.tex`、`M paper_a1/abstract.tex` —— 上一轮 A1 "全改"（按 lead 要求未 commit）；
- `a23_joe`：`M paper_a2/main_ieee.tex` 等 —— 并行 A23 "全改"任务在写；
- `prl_commentary`：`M paper_review_prl/main_prl.tex` 等 —— 并行 Commentary "全改"任务在写。

`prl_commentary` 的第 2 条 WARN 是 `H-02 data statement contains no URL or DOI`：并行任务正在改写 `paper_review_prl/main_prl.tex` 的 Data availability 段，当前工作树版本暂时没有 DOI（HEAD 版本含 `10.5281/zenodo.23632347`）。**不是本轮改动引入**。
⇒ 这些并行改动提交后（且 Commentary 的 data statement 恢复 DOI），六个 profile 预期全部 **READY grade A、fail=0**，warn 只剩各自的具名 I-02（a1_paa/paperA_*/p3_prl/a23_joe = 1，prl_commentary = 1）。

## 5. A1 ledger 刷新

```
D:\Anaconda\python.exe tools/_claim_ledger_a1.py --apply
  A1 claims: 216 pass / 0 fail / 216 total
```
`outputs/analysis/claim_ledger_a1.json` 的 `"abstract words (audit counter)"` 记录为 `manuscript=243, computed=241.0, pass=True`（当前 abstract 实测 241 词），此前的瞬时值 237 已被覆盖，该文件回到 HEAD 状态（git 不再显示 M）。

## 6. 文件与残余

**改动**：`tools/paper_audit/profiles.py`（4 个 profile）、`tools/paper_audit/checks.py`（I-02 冻结分支）、
`tools/paper_audit/registry.py`（I-02 描述）、`tools/paper_audit/freeze/a1_paa.json`、`freeze/prl_commentary.json`、
新增 `freeze/paperA_nc.json`、`freeze/paperA_springer.json`、`outputs/analysis/claim_ledger_a1.json`（刷新）、本文件。
**未动**：`SUBMISSION/**`（只读哈希）、稿件、`_p1454`、`a23_joe`/`p3_prl` 的 profile 与 manifest。
**残余**：
1. `a23_joe` 仍是"只有 `package_frozen` + freeze_paths、无显式 package/package_map"的旧写法（lead 要求不回退）；它的 I-02 具名 WARN 已给出 package 路径与快照，若要与本轮四个 profile 完全对齐，可后续补 `package="SUBMISSION/A23_JOE"` + expected/map。
2. 三个 A-01 blocker 与 Commentary 的 H-02 依赖并行任务完成/提交后自动消失；本轮无法也不应代为提交。
3. `paperA_springer` 的冻结参照是 Neurocomputing 包（同一 Paper A 内容），其自身 `main_springer.pdf` 是排版变体、不参与 I-02 比较——已在 profile 注释与 notes 中写明。


---

## 补充：`a23_joe` 对齐（2026-10-25）

`a23_joe` 原先只有 `package_frozen=True` + `freeze_paths`；现与其余五个 profile 完全同形：
`package="SUBMISSION/A23_JOE"`、`package_expected` 6 项（A23_latex_source.zip / abstract_plaintext.txt / README.md / current/{main_ieee,cover_letter,abstract}.pdf）、
`package_map` 3 对（current/main_ieee.pdf→main_ieee.pdf、current/cover_letter.pdf→cover_letter.pdf、current/abstract.pdf→abstract.pdf）、`package_frozen=True`。
**冻结条目不变**：`freeze/a23_joe.json` **37 条**；`freeze --profile a23_joe` → `added=[] removed=[] changed=[] n=37`；
`paper_audit selftest` → **SELFTEST PASSED**（`frozen files verified: 257`）。

**a23_joe 的 I-02（逐字 evidence）**：
```
I-02 WARN | package=SUBMISSION/A23_JOE (37 files) snapshot=2026-10-12 08:44 UTC;
deliberately not compared with the live draft ... Integrity is verified by I-04 (frozen hashes).
Diverged: current/main_ieee.pdf 64 pp vs live main_ieee.pdf 73 pp (page count differs);
current/cover_letter.pdf 3 pp = 3 pp, text differs; current/abstract.pdf 1 pp = 1 pp, text differs.
```
仍是**具名 WARN**（非失败）。

**六 profile 复跑（逐字）**：
```
a1_paa            BLOCKED  grade D  pass=58 fail=1 warn=1 manual=9 skip=17 error=0
paperA_nc         READY  grade A  pass=66 fail=0 warn=1 manual=9 skip=10 error=0
paperA_springer   READY  grade A  pass=61 fail=0 warn=1 manual=9 skip=15 error=0
p3_prl            READY  grade A  pass=54 fail=0 warn=1 manual=9 skip=22 error=0
a23_joe           READY  grade A  pass=62 fail=0 warn=1 manual=9 skip=14 error=0
prl_commentary    BLOCKED  grade D  pass=58 fail=1 warn=1 manual=9 skip=17 error=0
```
`a1_paa` 与 `prl_commentary` 的唯一 FAIL 仍是 **A-01**（未提交改动）：前者是 `M paper_a1/figures/fig2_tau_top1.png`（本轮更新的预览 PNG，`.gitignore` 忽略 PDF 故只此一项），
后者是并行 Commentary 任务留下的 `M paper_review_prl/MANUSCRIPT.md`、`M paper_review_prl/main_prl.tex`。**I-02 在六个 profile 上仍全部是具名 WARN，无 I-02 FAIL。**
