# P3 一致性修复轮记录（2026-10-24）

> 输入：`docs/P3_CHANGE_SUMMARY_2026-10-24.md`（首投→当前工作稿的变更史调查，指出工作稿与自身归档矛盾）。
> 本轮只做「改回有来源的值 + 加门禁」，不新增实验、不改任何冻结包。
> 命令一律可重跑；下文每个数字都写成 `脚本 → 归档 :: 字段`。

---

## 1. 环境数字（`sections/discussion.tex` Limitations (6)）

**旧稿（HEAD `3db89e4`）写**：`three-environment matrix`、torch 2.4 的 r=5 均值 `+34`、环境占比 `about 48%`。

**归档实测**（`outputs/analysis/p3_env_variance.json`，产出脚本 `tools/_p1570_env_variance_update.py`）：

| 值 | 归档字段 | 数值 |
|---|---|---|
| torch 2.9/cu130 r=5 均值 | `envs."torch 2.9/cu130".mean`（n=5） | **-23.0** |
| torch 2.12/cu130 r=5 均值 | `envs."torch 2.12/cu130".mean`（n=10） | **-43.7** |
| torch 2.4/cu121 r=5 均值 | `envs."torch 2.4/cu121".mean`（n=4） | **+25.25** |
| 环境占比 | `env_share` | **0.4520380…** → 45.20% |
| bootstrap CI | `bootstrap.share_ci95` | **[0.21198, 0.74720]** → [21.2%, 74.7%] |
| σ_env / σ_seed | `sigma_env` / `sigma_seed` | **31.1489** / **34.2950** |

**结论**：
- `+34` **没有任何归档来源**（r=5 的 torch 2.4 均值在归档里是 +25.25；早期 n=3 口径也只有 +20.0）⇒ **不保留、不另造**，改用 `+25.25`；
- `48%` **没有任何归档来源**（`p3_env_variance_boot.json :: share_mean = 0.341988` 是 n=3 的旧口径 34.2%，也不是 48%）⇒ **删除该说法**，改用归档的 45.20%；
- `three-environment` → 改为 **four-stack**：S29 已覆盖四栈（`supplementary.tex:1256-1258`），四栈列表本身即来源。

**改动位置**：`paper3/paper_ieee/sections/discussion.tex:64-72`（(6) 整段重写，末尾附归档路径 `outputs/analysis/p3_env_variance.json` 字段名与 `p3_env_matrix3.json`）。

**为什么要压字数**：本轮初稿把这段写长后 main.pdf 变成 **11 页**（超出 10 页上限）。逐轮压缩到「比原段仅多 389 字符」才回到 **10 页**；为此把「四栈全名」简写为 `four-stack matrix`（栈清单仍在 S29 表内），数字与归档字段**一个都没删**。

**未落地的归档（TODO）**：torch 2.6/cu124 的 seed 补跑（`tools/_p1613_p3_cloud_runner.py --job env-seeds --stack-suffix torch26`，6 条里当时只完成 1 条）仍在跑，`outputs/analysis/p3_env_stack_seeds.json` **尚不存在** ⇒ 本轮用现有归档，并在 `discussion.tex:49-51` 留标记：

```
% TODO(envseeds): re-point to p3_env_stack_seeds.json once the seed extension lands
```

一条 `grep -rn "TODO(envseeds)"` 即可定位后续工作。**注意**：`audit_check.py` 原本把 `TODO` 当占位符残留，本轮为该标记加了显式白名单（`MARKER_EXEMPT`），其余任何 `TODO/TBD/XXX/FIXME/??` 仍然会 FAIL。

---

## 2. S17 claims table 的 97.9% → 98.1%

- **归档判据**：`outputs/analysis/p3_qwen_perlayer_summary.json :: share.llm_00 = 0.9811478…` → **98.1%**；同一个值在 S42 的表/图注（`supplementary.tex:1705`、`:1710`）已经是 98.1%。同文件的 `first4_share = 0.9946680` → S42 的 99.5%。
- **97.9% 无来源**：在 `outputs/**`、`paper3/scripts/outputs/**` 全量搜 `0.979*` / `97.9`，没有任何与 Qwen 逐层耦合相关的条目；该串是 `91d1f7d`（2026-10-24「纯本地补跑」提交）新写 S17 行时引入的笔误。
- **改动**：`supplementary/supplementary.tex:890` 由 `97.9\%` 改为 `98.1\%`。
- **S42 vs S43 的分工（实测）**：`supplementary.aux` 中 `app:qwenlayer → S42`（Per-layer coupling on a second model）、`app:smolvlm → S43`（SmolVLM-500M）。S17 该行讲的是 Qwen2.5-VL-3B 逐层耦合 ⇒ 指向 **S42**。

---

## 3. 交叉引用与陈旧指针

| 位置 | 旧 | 新 | 依据 |
|---|---|---|---|
| `supplementary.tex:890` | `(S43)` | `(S42)` | `supplementary.aux`：逐层耦合节 = S42；补充材料共 43 个 `\section`，**`(S44)` 不可能存在** |
| `main.tex:108` | `Supplementary Sections~S1--S9` | `~S1--S43` | 补充材料实际 43 节（`supplementary.tex` 43 个 `\section`，`audit_check.py` 断言 43） |

`(S44)`、`97.9\% of the coupling` 现在都进了「必须不存在」门禁（源文件 + PDF 双向）。

---

## 4. `SUBMISSION/P3_PRL_next_revision/` 重建

**该包此前含被取代的串**（实测旧包 PDF）：`1434 training pairs`、`(S44)`、`97.9`。

**是否被哈希钉住**：否。`tools/paper_audit/freeze/p3_prl.json` 的 10 个条目**只覆盖**
`SUBMISSION/_archive/P3_PRL_rejected_2026-10-21/{CORRECTED_2026-10-15,UPLOAD_2026-10-15}/**`；
全仓库没有任何 JSON/脚本把 `P3_PRL_next_revision` 的哈希写死 ⇒ **直接重建，不会覆盖任何钉住的产物**。

**做法**：`tools/_p1445_rebuild_packages.py` 写的是 `SUBMISSION/_venue_builds/*`（且会顺带重建另外四篇的包），
并不会刷新本包；因此新增幂等脚本 **`tools/_p1627_rebuild_next_revision.py --apply`**，它与
`tools/_p1574_record_and_refreeze.py`（当年冻结该包时用的命令）逐参数一致：`_p1336_build_venue_package.py`
→ `SUBMISSION/P3_PRL_next_revision`，再补 `EM_FIELDS.md`、README 冻结记录、`SHA256SUMS.txt`。
脚本重建前先断言源文件已无 `1434 training pairs` / `(S44)` / `97.9\%`，重建后再对包内 `.tex` 与 zip 逐条复查。

**重建结果**（2026-10-24 20:06）：`Manuscript.pdf` **10 页** / `Supplementary.pdf` **18 页**（S1–S43），
README 表格已写 18 页；旧串全部消失；`SHA256SUMS.txt` 覆盖 8 个文件。

**冻结件未被触碰（实测）**：

- `SUBMISSION/P3_PRL_resubmission/**`：全部文件仍是 2026-10-21 的尺寸与 mtime（Manuscript 421,012 B、
  Supplementary 331,816 B、LaTeXSource.zip 335,159 B）；`git status --porcelain -- SUBMISSION` **为空**；
- `tools/paper_audit/freeze/p3_prl.json`：未修改（SHA-256 `64572a98…a1c933`），其 10 个条目**复算 10/10 一致，0 changed、0 missing**。

---

## 5. 文档修复

1. `docs/P3_RESPONSE_LETTER.md`：补回缺失的最后一段 **「Title.」**（归档副本
   `SUBMISSION/_archive/P3_PRL_rejected_2026-10-21/response/P3_RESPONSE_LETTER.md` 才有）。补后
   44,468 B → **44,995 B**，与归档副本 **SHA-256 逐字节相同**（`f9388525…b931ce73`）。
2. `docs/P3_SUBMISSION_STATUS.md` 四处陈旧点：
   - claims table 行数 `24 rows` → **`25 rows (24 plus the SmolVLM-500M row)`**（`supplementary.tex:867-891` 实测 25 行数据）；
   - `three-stack environment matrix` → **`four-stack environment matrix`**（S29 四栈）；
   - `next_revision` 口径：`Supplementary 18 pp, S1–S43; the 2026-10-23 freeze was 17 pp`、
     `frozen draft built | 2026-10-23; rebuilt 2026-10-24`、`8 → 18 pages, S1–S43`（实测 18 页）；
   - DOI 段：原来 v2.3 与 v2.4 都被写成 "current repository release" ⇒ 现在只有
     **`v2.4`（current, 2026-10-24, 10.5281/zenodo.23614290）**；v2.3（`10.5281/zenodo.23609295`）标为
     **superseded（保留历史，不静默删除）**；v2.2（稿件实际引用的 `10.5281/zenodo.23523263`）与
     v1.0-prl-revision（`10.5281/zenodo.23341223`）保留原样。
     **正文 DOI 未改**：`main.tex:133` 仍是 v2.2，与已投件一致。
3. 落地脚本：`tools/_p1625_p3_consistency_fixes.py`（幂等、带断言）、
   `tools/_p1626_fix_status_doi_block.py`（DOI 段一次性重排）。

---

## 6. 新增门禁（每个被改的数字都有「新值在 + 旧值不在」两条）

`paper3/paper_ieee/audit_check.py`（源文件级）：

- `ENV_NEEDLES`（10 条）：`four-stack matrix`、`$-23.0$, $-43.7$, $+25.25$`、`$45.20\%$`、
  `$[21.2\%,74.7\%]$`、`$\sigma_{\mathrm{env}}=31.15$, $\sigma_{\mathrm{seed}}=34.29$`、
  `outputs/analysis/p3_env_variance.json`、`outputs/analysis/p3_env_matrix3.json`、
  `98.1\% of the coupling on Qwen2.5-VL-3B`、`(S42)`、`Supplementary Sections~S1--S43`；
- `ENV_ABSENT`（4 条）：`three-environment`、`$+34$ (torch 2.4/CUDA 12.1)`、
  `about 48\% of the $r=5$ variance`、`97.9\% of the coupling`；
- 另加：`main text / supplement: no (S44) pointer`、`supplementary-material section free of the old S1--S9 range`；
- `MARKER_EXEMPT`：只放行 `TODO(envseeds)` 这一条标记，其余占位符照旧 FAIL。

`paper3/paper_ieee/audit_pdf.py`（PDF 级）：

- `ENV_MAIN_VALUES`（8 条）：`four-stackmatrix`、`-23.0,-43.7,+25.25`、`45.20%`、`[21.2%,74.7%]`、
  `31.15`、`34.29`、`outputs/analysis/p3_env_variance.json`；
- `ENV_MAIN_ABSENT`（2 条）：`34(torch2.4/CUDA12.1)`、`48%ofthe`；
- `SUPP_CHECKS` 增：`98.1%ofthecoupling`、`Qwen2.5-VL-3B(S42)`、`S37 env matrix/variance archive`；
- `SUPP_ABSENT`（3 条）：`97.9%ofthecoupling`、`Qwen2.5-VL-3B(S43)`、`(S44)`；
- `MAIN_CHECKS` 增：`SupplementarySectionsS1-S43`。

---

## 7. 重新编译与页数

| 文件 | 命令 | 结果 |
|---|---|---|
| `paper3/paper_ieee/supplementary/supplementary.tex` | 在 `supplementary/` 目录内 `pdflatex` ×2 | **18 页**（S1–S43），0 错误、0 undefined ref/cite |
| `paper3/paper_ieee/main.tex` | 在 `paper3/paper_ieee/` 内 `pdflatex` ×2 | **10 页**（与上限一致），0 错误 |

页数**未变**（10 / 18），因此 `SUPP_PAGES = 18`、`MAIN_PAGES = 10` **不需要改**；
两个审计脚本的文档字符串已注明本轮改动「未增删小节、未移分页」。

> ⚠️ **踩到的坑（写下来避免复现）**：`pdflatex supplementary/supplementary.tex` 会把 `supplementary.pdf`
> 写到**当前工作目录**（`paper3/paper_ieee/`），而不是源文件所在子目录；此前 `paper3/paper_ieee/` 下就留着
> 一份 19:52 的旧 `supplementary.pdf/.aux/.log/.out`。本轮已删除这 4 个未跟踪的残留文件，并在
> `supplementary/` 目录内编译，确保 `supplementary/supplementary.pdf` 才是被审计的那份。

---

## 8. 门禁结果（2026-10-24 20:0x）

| 命令 | 结果 |
|---|---|
| `python paper3/paper_ieee/audit_check.py` | **0 hard failure / 0 warning**（新增的环境轮 10+4+2 条全 PASS） |
| `python paper3/paper_ieee/audit_pdf.py` | **0 hard failure / 0 warning**（main 10 页 / supp 18 页，含新增 PDF 门禁） |
| `python -m tools.paper_audit audit --profile p3_prl --fail-on NONE` | **BLOCKED / grade D**，唯一 blocker = `A-01 uncommitted changes under paper3/paper_ieee`（**预期**：改动待 lead 提交）；另有 1 warning `J-01 claim-ledger evidence older than the manuscript sources`（claim ledger 文件比稿源旧，属既有状态）。报告：`docs/audits/AUD-p3_prl-20261024T120830Z.{md,json}` |
| `python tools/_p1428_provenance_gate.py` | **PASS**（P3 floats=4 / manifest=39 / missing=0 / pending=0 / broken_paths=0） |
| `python tools/_claim_ledger.py`（额外自查） | **96/96 通过、0 失败**（本轮改动未触碰台账引用的任何数字） |
| freeze 复核（额外自查） | `tools/paper_audit/freeze/p3_prl.json` 10/10 哈希一致 |

---

## 9. 本轮改动文件清单

| 文件 | 改动 |
|---|---|
| `paper3/paper_ieee/sections/discussion.tex` | (6) 段重写（+:49-51 TODO 标记） |
| `paper3/paper_ieee/supplementary/supplementary.tex` | S17 行：`97.9\%`→`98.1\%`、`(S43)`→`(S42)` |
| `paper3/paper_ieee/main.tex` | `S1--S9` → `S1--S43` |
| `paper3/paper_ieee/audit_check.py` | 新增环境轮门禁、`(S44)`/S1--S9 检查、`MARKER_EXEMPT` |
| `paper3/paper_ieee/audit_pdf.py` | 新增 `ENV_MAIN_VALUES`/`ENV_MAIN_ABSENT`/`SUPP_ABSENT` 与 S42/S37 针 |
| `SUBMISSION/P3_PRL_next_revision/**` | 由 `tools/_p1627_rebuild_next_revision.py --apply` 重建（10 页 / 18 页） |
| `docs/P3_RESPONSE_LETTER.md` | 补「Title.」段（= 归档副本） |
| `docs/P3_SUBMISSION_STATUS.md` | 四处陈旧点修正（行数、四栈、页数口径、DOI current） |
| `tools/_p1625_p3_consistency_fixes.py`、`tools/_p1626_fix_status_doi_block.py`、`tools/_p1627_rebuild_next_revision.py` | 本轮落地脚本（幂等、带断言） |
| `docs/p3_consistency_round_notes.md` | 本文件 |

**本轮明确未做**：未改 S28（451 题口径）与 S37（三栈分解，归档 `env_share=45.20%` 与其 45% 四舍五入一致，
仅三栈 ⇒ 保留「three cu121/cu130 stacks」表述）；未动 `SUBMISSION/P3_PRL_resubmission/`、
`SUBMISSION/_frozen_submitted/`、`SUBMISSION/_archive/**`、任何 `outputs/**` 归档。

## 10. 留给下一步的一件事

`outputs/analysis/p3_env_stack_seeds.json` 落地后（torch 2.6/cu124 六条 seed 补跑完成）：
① 用该归档重算环境占比并与 `p3_env_variance.json` 对齐；② 更新 `discussion.tex:49-51` 的 TODO 段所指归档；
③ 更新 S37 表与 `ENV_NEEDLES`；④ 重跑第 8 节四条门禁。定位命令：`grep -rn "TODO(envseeds)"`。