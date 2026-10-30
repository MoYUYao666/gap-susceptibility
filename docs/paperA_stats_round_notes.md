# Paper A 统计轮次笔记（2026-10-24，bootstrap / dispersion convention 整合）

**范围**：把 `docs/a1_paperA_bootstrap_text.md` 里 Paper A 部分的 bootstrap / 离散度约定修正整合进 `paper合/` 工作稿；
A1（`paper_a1/`）与 Paper 3 部分不在本轮，未动。

**证据链**：脚本 `tools/_p1595_bootstrap_ci_round.py`；结果 `outputs/analysis/paperA_strict_bootstrap.json`；
文本建议稿 `docs/a1_paperA_bootstrap_text.md`。Bootstrap 设定：percentile，20{,}000 次重采样，
固定 RNG 种子（20261024），按 seed 配对（同一 archive 内）。

---

## 1. 改动清单（英文正文，文件 : 行号）

### 1.1 `paper合/sections/empirical.tex`

| 行 | 位置 | 改动 |
|---|---|---|
| 15 | `\subsection{Experimental Design}` | 统计句改为 "…Welch's $t$-test and ANOVA, and a seed-level percentile bootstrap (`paperA_strict_bootstrap.json` from `_p1595_bootstrap_ci_round.py`) for seed-paired comparisons." |
| 60–64 | `tab:position_strict` caption | **删除失实的 sd 断言**；改为：dual-encoder 四行 $0.0006$–$0.006$，BioCLIP 三臂 $0.002/0.010/0.015$；并加指针句 "Seed-level percentile bootstrap intervals (20,000 resamples, seed pairing kept, at most $\pm0.004$ here) are in Section~\ref{sec:r1provenance}, with the arm differences they resolve." |

### 1.2 `paper合/sections/supplement.tex`

| 行 | 位置 | 改动 |
|---|---|---|
| 271–275 | `tab:vlm` caption | 加一句：$\pm$ 后为 **population sd（ddof=0）**，并给出 sample sd（$0.46/0.30/1.06$）；加三臂 seed-level bootstrap 区间 $98.57$ [$98.33$,$98.81$]、$96.74$ [$96.57$,$96.88$]、$89.41$ [$88.82$,$89.93$]。 |
| 292–296 | E 节正文 | 加配对 bootstrap：text−both $-1.82$ [$-2.09$,$-1.54$]、both−vision $+9.16$ [$+8.69$,$+9.68$]，均不含 0。 |
| 311, 313–320 | F 节（`sec:r1provenance`） | **"all twelve" → "all eighteen"**（6 行 × 3 臂）；加 bootstrap 认证段：五 seed 行臂均值区间 $\le\pm0.004$、BioCLIP $\le\pm0.013$、text−vision 每行不含 0，并给 CLIP B/32 r8 $-0.057$ [$-0.063$,$-0.052$] 与 SigLIP 反转 $+0.014$ [$+0.008$,$+0.018$]。 |
| 366–368 | `tab:llava` caption | 加：$\pm$ 后为 **population sd（ddof=0）**，sample sd 为 $9.23/20.00/9.69$；bootstrap 区间在正文。 |
| 387–391 | G 节正文 | 三臂 bootstrap 区间 $73.27$ [$67.61$,$83.92$]、$95.66$ [$86.04$,$105.43$]、$121.48$ [$99.53$,$138.68$]；另两个配对差 $-22.39$ [$-37.15$,$-11.59$]、$-48.21$ [$-70.40$,$-31.92$]。 |
| 392–401 | G 节正文 | **新配对结论**：both − vision $=-25.81$ [$-33.25$,$-13.48$]（不含 0，三个 seed 逐一为 $-30.71/-13.48/-33.25$）；**原有 unpaired 谨慎表述保留**，并说明两者差别只在"是否去掉 seed 间方差"。 |

### 1.3 覆盖信 / 校验脚本

| 文件 | 行 | 改动 |
|---|---|---|
| `paper合/cover_letter_nc.tex` | 26 | 75 → **77 pages** |
| `paper合/cover_letter.tex` | 26 | 75 → **77 pages** |
| `paper合/cover_letter_nc_revision.tex` | 26 | 75 → **77 pages**（`cover_letter_nc_revision.pdf` 重编译，1 页） |
| `tools/_p1454_final_verify.py` | 28 | `PAGES` 中 `paper合/main_nc.pdf` 75 → **77** |
| `tools/_p1454_final_verify.py` | 71–112, 184–187 | 新增 `check_bootstrap_integration()`：24 条断言（sd 修正/约定/配对 CI/18 cells/写作用域），并计入 `all_pass` |

（另有 `paper合/cover_letter_nc.pdf`、`paper合/cover_letter.pdf` 重编译；`SUBMISSION/PaperA_Neurocomputing` 与
`SUBMISSION/A1_PatternAnalysisApplications` 由 `tools/_p1576_refresh_a1_papera_packages.py --apply` 刷新。）

---

## 2. 页码

| 文件 | 本轮前 | 本轮后 | 说明 |
|---|---|---|---|
| `paper合/main_nc.pdf` | 75 | **77** | 见下"为什么是 77" |
| `paper合/main_springer.pdf` | 54 | **54** | 未变 |
| `paper合/cover_letter_nc.pdf` | 3 | 3 | 仅页数声明改字 |
| `paper合/cover_letter.pdf` | 3 | 3 | 同上 |
| `paper合/cover_letter_nc_revision.pdf` | 1 | 1 | 同上 |

**为什么是 77（已实测二分）**：把 `tab:position_strict` caption 写满 bootstrap 起止区间后，该表从第 16 页被
float 推到第 51 页，文档 75 → 76 页；`Experimental Design` 的统计句再加 1 页。因此本轮把 **bootstrap 细节放进
F 节正文**、caption 只留指引句：若连 `Experimental Design` 那句一并去掉可保持 75 页，但那样该节"用了 bootstrap"
这一方法论就无出处（违反"每个数字须指名脚本 + JSON"），故选择保留并如实报 77 页、同步改三封覆盖信 + `PAGES`。

---

## 3. 构建与门禁结果

### 3.1 编译（`paper合/`，均 `pdflatex -interaction=nonstopmode` ×2，退出码 0）

| 变体 | 页数 | Overfull hbox/vbox | undefined refs/cites | rerun 提示 |
|---|---|---|---|---|
| `main_nc.tex` → `main_nc.pdf` | 77 | 0 / 0 | 0 / 0 | 0 |
| `main_springer.tex` → `main_springer.pdf` | 54 | 0 / 0 | 0 / 0 | 0 |

### 3.2 一致性门禁

`python tools/_p1181_verify_paperA_consistency.py` → **RESULT: 0 failure(s)**（53 条 PASS，含
"cover-letter page count matches main_nc.pdf" 两条动态校验）。

### 3.3 `paper_audit`

`python -m tools.paper_audit audit --profile paperA_nc --fail-on NONE` →
**READY grade A pass=67 fail=0 warn=0 manual=9 skip=10 error=0**（本轮末次报告
`docs/audits/AUD-paperA_nc-20261024T085232Z.{md,json}`；中间一次为
`AUD-paperA_nc-20261024T085059Z`）。
说明：第一次跑到 `BLOCKED grade D / BLOCKER I-02`（package copies differ from live files），原因是刷新包之后
又改了一处正文措辞；重跑 `_p1576_refresh_a1_papera_packages.py --apply` 后即为上表结果。
本轮**未出现** git-dirty 型 failure（该检查与本 profile 的 I-02 是两回事）。

### 3.4 新增校验

`tools/_p1454_final_verify.py::check_bootstrap_integration()` → **pass=True，24/24 checks OK**，含写作用域守卫
`section_h_not_edited`（比对 `git diff` hunk 行号与 `\section*{H.` 起始行 421/422，确认 Section H / `sec:decoderconfound` 零改动）、
`bioclip_sds_reproduce`、`siglip_reversal_ci_reproduces`、`llava_paired_ci_reproduces` 等按 JSON 复算的断言。

### 3.5 `_p1595` dry run（证据脚本自校验）

`python tools/_p1595_bootstrap_ci_round.py` → **A1 checks 23 / failures 0；Paper A checks 87 / failures 2**，退出码 1。
两条 FAIL 及其归属（**均非本轮改动引入，且都不在 Paper A 稿件层面**）：

1. `PaperA tab:position_strict caption sd range incl. BioCLIP`：脚本断言的是**旧 blanket 措辞**是否仍覆盖 BioCLIP，
   本轮正是把它改成分开陈述，故该"期望失败"仍然为 FAIL（脚本未随文本更新，`_p1595` 不在本会话写作用域内）。
2. `P3 capacity-matched: integer rounding of the Gamma-guided mean (+1478)`：Paper 3 的 `+1478` 应为 `+1477`，属 P3 轮次。

另有 A1 provenance appendix 一行（`a1_monitor_combined.json`）在 A1 轮次处理，本轮未动 `paper_a1/`；
A1 侧本轮 `_p1595` 的 23 条断言全过。

### 3.6 未做（超出写作用域）与它对 `_p1454` 的影响

`SUBMISSION/_venue_builds/PaperA_Neurocomputing_next/` 仍是 2026-10-24 16:39 的**75 页**快照
（`Manuscript.pdf` 1424275 B、`LaTeXSource.zip` 3923775 B），而 `SUBMISSION/` 不在本轮写作用域内，故未重建。
实测 `python tools/_p1444_staged_package_check.py`（dry run，只写临时目录）对五个包的现况：

```
A1_PAA_next: ok errors=0 pages=64/64      P3_PRL_next: ok errors=0 pages=10/10
A23_JOE_next: ok errors=0 pages=70/70     Commentary_PRL_next: ok errors=0 pages=7/7
PaperA_Neurocomputing_next: ok errors=0 pages=75/75
```

即脚本本身全过，但 Paper A 这一包仍是旧页数；`tools/_p1454_final_verify.py` 的 `staged_packages` 一关
在重建前会因 75 ≠ 77 而失败（`outputs/analysis/staged_package_check.json` 亦为 15:16 的旧记录）。
**待办（需更宽作用域或由 lead 执行）**：`python tools/_p1445_rebuild_packages.py --apply`
（重建五个 `_venue_builds/*_next`，其中 Paper A 包会取到当前 77 页的 `main_nc.pdf` + 新覆盖信），
再 `python tools/_p1444_staged_package_check.py --apply` 刷新该 JSON。

---

## 4. 建议写入 provenance manifest 的条目（**未改 `docs/provenance_manifest.json`**）

| label | 生成/验证脚本 | 结果归档（字段路径） |
|---|---|---|
| `tab:position_strict` ΔCG（18 cells）+ 臂均值/配对差 CI | `tools/_p1595_bootstrap_ci_round.py`（验证） | `outputs/analysis/paperA_strict_bootstrap.json::paperA.tab_position_strict.rows.<row>.{arms,paired_differences}.*.{mean,ci95_percentile}` |
| `tab:vlm` 三臂区间 | 同上 | `…::paperA.tab_vlm.{arms,paired_differences}.*.ci95_percentile` |
| `tab:llava` 三臂区间 + 配对差（含 $-25.81$ [$-33.25$,$-13.48$]） | 同上 | `…::paperA.tab_llava.{arms,paired_differences}.*.ci95_percentile` |
| ddof 约定（`tab:vlm` 13 seeds / `tab:llava` 3 seeds） | 同上 | `…::paperA.{tab_vlm,tab_llava}.sd_convention.<arm>.{manuscript,ddof0,ddof1,matches}` |
| `tab:position_strict` caption sd 范围（0.0006–0.006 / BioCLIP 0.002,0.010,0.015） | 同上 | `…::paperA.tab_position_strict.caption_digit_checks.{computed_sd_ddof1_range_excluding_bioclip,computed_sd_ddof1_bioclip_arms}` |

---

## 5. 未决 / 边界

- 未动：`paper合/sections/supplement.tex` 的 Section H（`sec:decoderconfound`，第 421 行 `\section*{H.`，`\label` 在第 422 行）、`HANDOFF.md`、
  `文件地图.md`、`docs/provenance_manifest.json`、`SUBMISSION/**`、其它论文；`paper_a1/main.tex` 的既有改动
  （另有 A1 轮次）自始至终未触碰。
- `tab:llava` 的 "unresolved" 与配对 bootstrap 已在同一段内**同时**保留并解释，不再互相矛盾。
- 本轮数据没有新的实验/新训练，全部数值来自既有 archive；`_p1595` 以 dry run 复跑（结果见 3.5），未 `--apply`、
  未改动 `outputs/analysis/*.json`。