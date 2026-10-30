# 门禁结构性修复（task-25，2026-10-25）：P3 冻结包映射（D-8）+ PDF 字节可复现性（D-6）

**来源**：独立审计 A 的两个结构性开放项（`docs/audit_manuscripts_2026-10-25.md` §D-6/§D-8；`docs/gate_hardening_2026-10-25.md` §6）。
**写入范围（本任务授权）**：`tools/paper_audit/**`、`docs/audits/**`、本报告。
**改动文件**：`tools/paper_audit/profiles.py`、`tools/paper_audit/checks.py`、`tools/paper_audit/registry.py`、
`tools/paper_audit/freeze/p3_prl.json`（共 +164 / −28 行）。**未动任何稿件、未动 `SUBMISSION/` 冻结包、未动 `_p1454_final_verify.py`。**
**解释器**：全部用 base `D:\Anaconda\python.exe`（项目新规）。

## 0. 快照（工作树在本任务期间被其他 agent 推进过）

| 时点 | HEAD | 脏树 |
|---|---|---|
| 任务开始 12:22:53 | **`50ebe6a0`** | 0（clean） |
| 任务结束 12:30:06 | **`dcd65678`** | **1**（只剩本报告未跟踪；我的 4 个代码文件已被下面那次提交扫进去） |

**HEAD 变了（两次）**：期间其他 agent 提交 2 次 —— `efa9118e "A23 next-revision package: add the revision cover letter"`、
`dcd65678 "Venue registry: SCIE status re-verified against the Master Journal List for all five target journals"`。
我的 4 个代码改动被**第二次提交（`dcd65678`，别人的 `git add -A` 扫入）**带进历史；已核对
`git show HEAD:tools/paper_audit/freeze/p3_prl.json` = 19 条 entries / 3 条 paths，与磁盘一致
（`git diff --numstat HEAD -- tools/paper_audit` 为空）。这与上一任务的现象相同：多 agent 并行时，中间版本会被他人提交扫入。

---

## 1. D-8：给 `p3_prl` 一个显式的"冻结包"声明（before → after）

### Before
`p3_prl` 的 profile 没有 `package` / `package_map` / `package_frozen`：I-01/I-02/I-03/I-06 全部 **SKIP**
（`no submission package configured` / `no package-to-live mapping configured`）⇒ 提交包与 live 草案的分歧**无门禁可查**；
当时唯一的动作是 I-04 覆盖两棵已拒/归档树。审计计数：`READY grade A pass=50 fail=0 warn=0 manual=9 skip=27`。

### After（`profiles.py`，照 `a23_joe` 的模型 + 显式 package 路径）
```python
package="SUBMISSION/P3_PRL_resubmission",
package_expected=["Manuscript.pdf","Supplementary.pdf","TitlePage.pdf","Highlights.pdf",
                  "AuthorshipConfirmation.pdf","CoverLetter.pdf","EM_FIELDS.md",
                  "LaTeXSource.zip","README.md"],
package_map=[["Manuscript.pdf","main.pdf"],
             ["Supplementary.pdf","supplementary/supplementary.pdf"]],
package_frozen=True,
freeze_paths=[... 原两棵已拒树 ..., "SUBMISSION/P3_PRL_resubmission"],
```
并在 `BASE_PROFILE` 增加默认键 `"package_frozen": False`（语义写进注释：冻结包**不再**与 live 做字节比较，
改由 I-02 出**具名警告**、I-04 保证完整性）。

**冻结清单**：`python -m tools.paper_audit freeze --profile p3_prl --write` →
`tools/paper_audit/freeze/p3_prl.json` 由 **10 条 → 19 条**（原有 10 条逐条哈希不变，已断言：`old entries all present & unchanged: True`），
新增 9 条即 `SUBMISSION/P3_PRL_resubmission/` 的 9 个文件（含 `LaTeXSource.zip`、`Manuscript.pdf`、`Supplementary.pdf`）。

**I-02 的实际输出（逐字，含包名与快照日期）**：
```
I-02 WARN | frozen submitted package (not compared with the live draft)
  evidence: package=SUBMISSION/P3_PRL_resubmission snapshot=2026-10-21 09:13 UTC;
  deliberately not compared with the live draft (the submitted version is frozen while the
  local draft is revised). Integrity is verified by I-04.
  Divergence: Supplementary.pdf 8 pp vs live supplementary/supplementary.pdf 26 pp.
  Unchanged: Manuscript.pdf 10 pp = live main.pdf 10 pp.
I-01 PASS | package present with 9 expected files
I-04 PASS | 19 frozen files unchanged
I-05 PASS | all package files under 50 MB
```
**现在门禁能区分**："提交版故意冻结、与 live 草案分歧（WARN，具名 + 快照日期 + 分歧页数，完整性由 I-04 管）" vs
"包忘了重建而过期（I-02 在**非冻结** profile 上是 P1 FAIL）"。
（同样的语义也自动应用到 `a23_joe`：它的 I-02 从 SKIP 变为具名 WARN，点名 `SUBMISSION/A23_JOE`，快照 `2026-10-12 08:44 UTC`。）

**计数变化（同一棵树，只改 profile/检查）**：
| profile | before | after |
|---|---|---|
| p3_prl | `READY A 50/0/0/27skip` | **`READY A 54/0/1/22skip`**（多 4 PASS：I-01/I-04(19)/I-05 + 1 WARN：I-02） |
| a23_joe | `READY A 58/0/0/19skip` | **`READY A 58/0/1/18skip`**（I-02 SKIP→WARN） |

**冻结包未被改动（证据）**：`SUBMISSION/P3_PRL_resubmission/` 9 个文件的 mtime 全为 **2026-10-21**（未重写）；
`paper_audit freeze --profile p3_prl` 校验 `added=[] removed=[] changed=[] n=19`。

---

## 2. D-6(a)：PDF 字节可复现性实验 —— **结论：可以做到字节稳定**

**方法**：把 `paper3/paper_ieee`（10 页主稿）复制到 `%TEMP%` 的独立目录，**同一源码各建两次**（各自 2 遍 pdflatex，
从零开始），比较最终 `main.pdf` 的 SHA-256；仓库内文件一律不动。四种设置：

| case | 设置 | 两次构建 identical | SHA-256（A = B） | 大小 | 页数/文本 |
|---|---|---|---|---|---|
| **baseline** | 原样 `pdflatex` ×2 | **False** | A `487c4dd9a1a7790d904e8bad5b376604a3f94d433b1131faef3e4c613db67c01`<br>B `3fa17722481e6c08aaa1da04fac28323a954bbd12674654396acf3aa634ae4e7` | 415,446 B | 10 pp / 文本相同 |
| **dates** | `SOURCE_DATE_EPOCH=1792841361` + `FORCE_SOURCE_DATE=1` | **True** | `5ee9ffaad40b188c40daeaeaa13968ea5bf8d2d1f09b9db4812eaf54d64a0048` | 415,435 B | 10 pp / 文本相同 |
| **prims** | 源码加 `\pdfinfoomitdate=1` `\pdftrailerid{}` `\pdfsuppressptexinfo=1` | **True** | `c02b6db5a05fd6d5fd90a381c04f161b9e632ac049bc1434ca61b2c35894e2c9` | 415,192 B | 10 pp / 文本相同 |
| **both** | prims + epoch | **True** | `c02b6db5a05fd6d5fd90a381c04f161b9e632ac049bc1434ca61b2c35894e2c9` | 415,192 B | 10 pp / 文本相同 |

**baseline 的差异到底是什么**：两次构建**大小完全相同**（415,446 B），首个不同字节在 offset **410,465**，内容是
```
A: /CreationDate (D:20261025122420+08'00')  /ModDate (D:20261025122420+08'00')
B: /CreationDate (D:20261025122423+08'00')  /ModDate (D:20261025122423+08'00')
```
⇒ **唯一差别就是嵌入的创建时间戳**（相差 3 秒），正文与页数完全一致 —— 这正是 D-6 的根因，也解释了为什么
I-02 的字节比较会在任何一次重建后误报"包过期"。

**可用配方（推荐，无需改稿件）**：
```powershell
$env:SOURCE_DATE_EPOCH = "1792841361"   # 固定常量，全项目统一
$env:FORCE_SOURCE_DATE = "1"
pdflatex -interaction=nonstopmode main.tex
```
`prims` 方案（改 `.tex` 加三个 pdfTeX 原语）同样有效且与 epoch 方案输出**同一哈希**（`c02b6db5…`），但需要改稿件源码，
不推荐（本任务也不允许改稿件）。**真正落地需要把这 2 个环境变量写进构建脚本**（`tools/_p1174_build_paperA_editorial.py`、
`tools/_build_prl_tex.py`、`paper3/paper_ieee/audit_pdf.py` 的构建入口等）——**它们不在本任务写入范围**，故作为建议登记（§6）。

> 注意一个**不可回避的边界**：已经投出的**冻结包 PDF 是在没有 pin epoch 的情况下构建的**，无法回溯修改（冻结纪律），
> 所以即便今后启用 epoch 配方，**旧包 vs 新重建仍会字节不同** —— 这就是必须保留 I-02 内容级比较的原因。

---

## 3. D-6(b)：I-02 内容级比较（byte-first，content-fallback）——实现与自检

`tools/paper_audit/checks.py::check_I02` 现在的逻辑：

1. **逐对比较字节哈希**；相等 ⇒ 记 `mode=byte`。
2. 字节不同且**两边都是 PDF** ⇒ 取**页数 + 空白归一化后的抽取文本哈希**：
   - 页数或文本哈希不同 ⇒ **硬失败**（`CONTENT differs: pages X vs Y, text sha ...`）——**绝不会被放行**；
   - 文本相同但**文件大小差 > 1%** ⇒ **硬失败**（"内嵌资源可能变了，请重建包"）——防止"只换图不换字"被内容模式静默放过；
   - 否则 ⇒ 记 `mode=content`，通过，并在消息里写明原因：
     `"%d of %d package copies match (%d byte-equal, %d content-equal; content mode is used because pdfTeX embeds a creation date/trailer ID, so a rebuild is not byte-stable)"`。
3. **非 PDF 对**字节不同 ⇒ 仍按原逻辑**硬失败**（内容模式只对 PDF 生效）。
4. **冻结包**（`package_frozen`）⇒ 不比较，出**具名 WARN**（§1），不再静默 SKIP。
5. `pypdf` 不可用等异常 ⇒ 该对**硬失败**（`content comparison failed`），不降级为通过。

**自检（6 例，全过；用真实 profile 定义 + pdflatex 造的合成 PDF）**：
```
f  p3_prl 冻结包          -> WARN  "frozen submitted package ... package=SUBMISSION/P3_PRL_resubmission
                                    snapshot=2026-10-21 09:13 UTC ... Divergence: Supplementary.pdf 8 pp vs live 26 pp ..."
g  a23_joe 冻结包         -> WARN  点名 SUBMISSION/A23_JOE，快照 2026-10-12
a  真实 paperA_nc 包      -> PASS  "5 package copies match the live files (mode=byte)"
b  同源码两次构建(不同 epoch)-> 字节不等、size_delta=0.00000% -> PASS "1 of 1 ... 1 content-equal" (b 的 fixture: byte_equal=False)
c  同页数、文本不同        -> FAIL  "CONTENT differs: pages 1 vs 1, text sha 02fd46a6d5e8 vs ffe95281895d"
d  页数不同               -> FAIL  "CONTENT differs: pages 1 vs 2"
SELFTEST: PASSED
```
⇒ 满足"不得把 I-02 弱化成 always-pass"：**真正的文本差异与页数差异仍然是硬失败**。

**登记表**：`tools/paper_audit/registry.py` 的 I-02 method 描述已同步改为
"byte-first … content mode (page count + extracted-text hash + size delta ≤ 1%) … frozen package → named warning"。

---

## 4. 回归（全部 fresh 跑，base 解释器）

| 命令 | rc | 结果（逐字） |
|---|---|---|
| `python -m tools.paper_audit selftest` | 0 | `SELFTEST PASSED`（检查表/档案/冻结基线） |
| `python -m tools.paper_audit freeze --profile {a1_nn,a1_paa,a23_joe,p3_prl,prl_commentary}` | 0×5 | 全部 `added=[] removed=[] changed=[]`；`n` = **16 / 16 / 37 / 19 / 28** |
| `python -m tools.paper_audit audit --profile a1_paa --fail-on NONE` | 0 | `READY  grade A  pass=61 fail=0 warn=0 manual=9 skip=16 error=0` |
| `... --profile paperA_nc` | 0 | `READY  grade A  pass=67 fail=0 warn=0 manual=9 skip=10 error=0` |
| `... --profile paperA_springer` | 0 | `READY  grade A  pass=56 fail=0 warn=0 manual=9 skip=21 error=0` |
| `... --profile p3_prl` | 0 | `READY  grade A  pass=54 fail=0 warn=1 manual=9 skip=22 error=0` ← +4 PASS / +1 WARN（D-8） |
| `... --profile a23_joe` | 0 | `READY  grade A  pass=58 fail=0 warn=1 manual=9 skip=18 error=0` |
| `... --profile prl_commentary` | 0 | `READY  grade A  pass=57 fail=0 warn=0 manual=9 skip=20 error=0` |
| `python tools/_p1454_final_verify.py --apply` | **0** | 见下 |

`_p1454` 逐字结尾：
```
  audit p3_prl: READY fail=0 warn=1 ok=True
  audit a23_joe: READY fail=0 warn=1 ok=True
  ...
  VERDICT: PASS WITH 11 WARNING(S) | git_clean=False: 29 uncommitted path(s) = 5 pending + 24 leftover audit report(s); this run's own output excluded
  ALL: PASS WITH 11 WARNING(S) | git_clean=False: 29 uncommitted path(s) = 5 pending + 24 leftover audit report(s); this run's own output excluded
```
11 条 WARN = **我新增的 2 条**（`audit_warn:p3_prl:I-02`、`audit_warn:a23_joe:I-02`，即 D-8 的具名冻结包声明）
+ 7 条 staged 快照陈旧（上一任务 D-5 的既有暴露，非本任务引入）+ 2 条脏树（我的改动 `M tools/paper_audit/*` 4 个文件 +
另一 agent 的 `M docs/VENUE_SCI_REGISTRY.md`；24 个遗留审计报告）。**硬失败 0，六 profile 全 READY fail=0。**

---

## 5. 本任务改了什么 / 没改什么

**改了**（`git diff --numstat 50ebe6a0 HEAD -- tools/paper_audit`）：
`checks.py +109/−7`、`profiles.py +22/−2`、`registry.py +5/−1`、`freeze/p3_prl.json +28/−18`（10→19 条），
合计 **+164/−28**；外加新增本报告。（回归产生的 `docs/audits/AUD-*` 属门禁产物，不入库计数。）
**没改**：任何 `.tex`/PDF 稿件、`SUBMISSION/**` 冻结包（mtime 仍 2026-10-21）、`_p1454_final_verify.py`、其它 tools。
**实验产物**：`%TEMP%\d6_repro_20261025\{d6_repro_result.json, *_A/, *_B/}`（不在仓库内）。

---

## 6. 仍然做不到 / 需要别人决定的事（明确登记）

1. **字节稳定的落地需要改构建脚本**（不在本任务写入范围）：建议在 `tools/_p1174_build_paperA_editorial.py`、
   `tools/_build_prl_tex.py`、以及 A1/A23 的构建入口里统一 `SOURCE_DATE_EPOCH=<固定常量>` + `FORCE_SOURCE_DATE=1`。
   在完成之前，**I-02 内容模式是必要的安全网**，不是永久替代。
2. **已投出的冻结包不可能回溯**：它们的 PDF 没有 pin epoch，和新构建永远不会字节相等（冻结纪律不允许重写）⇒
   内容模式必须长期保留；这不是"还没修好"，而是正确设计。
3. **纯图像替换**（文字/页数/版式不变，仅换figure）只能靠 **1% 体量守卫** 间接拦截；若两版图片压缩后体量差 <1%，
   内容模式会判通过。彻底解决需要加入图像指纹（`pypdf` 图像抽取 + 哈希），本次未做（复杂度/脆弱性高）。
4. **不同 TeX 版本之间不保证字节一致**（字体子集/压缩差异），可能触发 1% 体量守卫而误报；方向是"更保守"，可接受。
5. **D-8 不是"消除分歧"而是"把分歧显式化"**：P3 冻结包（10 pp + 8 pp/S1–S17）与 live 草案（10 pp + 26 pp/S1–S46）
   仍会长期不同，这是设计；任何**新投稿**前必须重建包并清掉 `package_frozen`（profile 里已写 remediation）。
6. 未做 `--staged` 独立编译（I-03）的实测；`p3_prl` 没有 `staged_command`，仍为 SKIP（与之前一致）。
