# P3 VQA 全测试集（451 题）改写轮 — 轮次记录

日期：2026-10-24（本轮）
性质：把 S28（VQA-RAD downstream check）与其在 S17 主张表中的行，从 **300 题**子集口径改写为**全 451 题测试集**口径；同步更新两道审计门禁的期望值。
写入范围（本轮只改了这 4 个文件）：

| 文件 | 变更 |
|---|---|
| `paper3/paper_ieee/supplementary/supplementary.tex` | S17 行 + S28 正文/表/图注 |
| `paper3/paper_ieee/audit_check.py` | 新增 451 期望 + 300 值缺席断言 |
| `paper3/paper_ieee/audit_pdf.py` | S28 PDF needles + 300 值缺席断言 |
| `docs/p3_vqa451_round_notes.md` | 本文档 |

**未改动**（按指令）：`SUBMISSION/**`、`HANDOFF.md`、`文件地图.md`、`docs/provenance_manifest.json`、其它论文。

---

## 1. 归档先决条件核查（先做，后改）

四个新归档在本轮开始时**已于 18:15:09–18:15:10 落到本地**（复制由 lead 侧完成；我在核查中途看到文件出现，非同一次列举）。
逐项验证（`python -c` + `json.load`，UTF-8）：

| 归档 | 记录数 | 关键校验 |
|---|---|---|
| `outputs/analysis/cloud_vqa_full451_base.json` | `questions` = 451 | `meta.train_samples` = 0（base 无适配器） |
| `outputs/analysis/cloud_vqa_full451_5.json` | 451 | `meta.train_samples` = 1793、`meta.epochs` = 3 |
| `outputs/analysis/cloud_vqa_full451_6.json` | 451 | `meta.train_samples` = 1793、`meta.epochs` = 3 |
| `outputs/analysis/p3_vqa_full_equivalence.json` | — | `n_questions` = 451、`n_boot` = 20000、`refs_identical_across_arms` = true |

* **配对前提成立**：三臂 `refs_sha256` 完全相同（`9730a909…a3e167`），即同 451 题、同顺序。
* **未重训**：`p3_vqa_full_equivalence.json` 记录 `adapter_source` 均为 `pre_existing`，适配器目录
  `outputs/p3_vqa_adapters/r5_step`（sha256 `1615d21e…4767b`）与 `r6_step`（sha256 `5f681f3f…ee42`），
  `train_samples` 仍为 1793、`epochs` 仍为 3 —— 与 300 题归档同源，未重新训练。
* **数值与任务书给定值逐条一致**：`vqa_equivalence.contrasts.*` 的 delta / ci95 / tost_p /
  `min_equivalent_margin` 与交付指令中的 MEASURED 值完全吻合（见 §2 表）。
  归档中的 300 题对比字段 `comparison_to_300q_archive` 为 `null`，因此**本轮正文/图注不引用任何 300↔451 的量化对比**。

## 2. 改写后的数字（全部出自归档字段，逐条可指认）

臂级指标（`arms.*`，表中四舍五入到 4 位）：accuracy base 0.3303769 → **0.3304**，r=5 0.3880266 → **0.3880**，
r=6 0.3348115 → **0.3348**；token F1 base 0.3553271 → **0.3553**，r=5 0.4216549 → **0.4217**，r=6 0.3983164 → **0.3983**。

对比量（`vqa_equivalence.contrasts.*`；差值按归档符号原样引用，正文用 "base minus r=5" 等措辞消歧）：

| 对比 | 指标 | 归档字段路径 | delta | ci95 | tost_p | min_equivalent_margin | 判定 |
|---|---|---|---|---|---|---|---|
| base−r=5 | accuracy | `contrasts.base_minus_5.accuracy` | −0.057650 | [−0.0976, −0.0177] | 0.6528 | 0.0909 | r=5 优于 base（CI 排除 0） |
| base−r=6 | accuracy | `contrasts.base_minus_6.accuracy` | −0.004435 | [−0.0399, +0.0310] | **0.0057** | 0.0333 | **EQUIVALENT** |
| r=5−r=6 | accuracy | `contrasts.5_minus_6.accuracy` | +0.053215 | [+0.0222, +0.0865] | **0.5778** | 0.0820 | **NOT equivalent（已解析的反转）** |
| base−r=5 | token F1 | `contrasts.base_minus_5.token_f1` | −0.066328 | [−0.1056, −0.0265] | 0.7924 | 0.0991 | r=5 优于 base（CI 排除 0） |
| base−r=6 | token F1 | `contrasts.base_minus_6.token_f1` | −0.042989 | [−0.0790, −0.0074] | 0.3538 | 0.0727 | r=6 优于 base（CI 排除 0） |
| r=5−r=6 | token F1 | `contrasts.5_minus_6.token_f1` | +0.023338 | [−0.0055, +0.0534] | **0.0396** | 0.0483 | **EQUIVALENT** |

阈值规则（`vqa_equivalence.declared_margin_rule`）：**±0.05 予先声明、不随集合大小改**；451 题下单臂 accuracy 的二项标准误约 **0.022**，
故约两个标准误（≈0.045）以内的差异属该评测集的分辨极限；每个对比同时报 `min_equivalent_margin`（`smallest_equivalent_margin` 六个键与之逐条一致）。

诚实读法（与指令一致，已写入稿件）：
* token F1：**两个秩都优于 base**；
* accuracy：**只有 r=5 在 base 之上被解析**，r=6 与 base **等价**（不是"更好"）；
* r=5−r=6 的 accuracy **+0.0532（CI 排除 0）** 在全测试集上是**已解析的反转**，且在 ±0.05 下**不成立等价**；
* token F1 上 r=5−r=6 **仍等价**（+0.0233，TOST p=0.0396）。

## 3. 稿件改动（含行号范围）

`paper3/paper_ieee/supplementary/supplementary.tex`（88316 → 89693 字节）：

| 位置 | 行号 | 改动 |
|---|---|---|
| S17 主张表 `tab:claims` 的 "energy predicts VQA accuracy" 行 | **879** | 300 题口径 → "1793 training pairs, all 451 held-out questions"，并写入"仅 r=5 在 accuracy 上解析、r=5−r=6 accuracy +0.0532 CI [+0.0222,+0.0865] 不成立等价（TOST p=0.5778）、token F1 仍等价"；原 300 题值 `TOST p=0.0074` 与 `+0.0433` 已移除 |
| S28 正文（`\label{app:vqa}`） | **1206–1217** | "evaluated on all 451 held-out questions of the test split, not only the first 300"；二项标准误 0.027–0.028 → **0.022**（约两个标准误 ≈0.045）；明写 margin 由 300 题分析**原样沿用、未按大集合重拟**，且每个对比都报最小等价 margin；明写复用同一 `r5_step`/`r6_step` 适配器、"变的只有题目数"；`refs` 三归档逐字节相同 |
| S28 表 `tab:vqa` | **1218–1229**（数据行 1225–1227） | `n` 300 → **451**；accuracy 0.3300/0.3933/0.3500 → **0.3304/0.3880/0.3348**；token F1 0.3563/0.4276/0.4210 → **0.3553/0.4217/0.3983** |
| S28 图注 | **1230–1250** | 全量重写为新数字（差值/CI/TOST/min margin/上界 8.2 点），并把被替换的 300 题归档显式标为 **superseded**；Source 行按要求给出（见 §4） |

S28 图注 Source 行（最终形态）：
`tools/_p1595_p3_rank_separation.py → outputs/analysis/p3_rank_separation_extended.json`（保留：该文件承载 300 题分析与本表的 claim status）
`; tools/_p1613_p3_cloud_runner.py → outputs/analysis/p3_vqa_full_equivalence.json`
（`vqa_equivalence.contrasts`、`vqa_equivalence.claim_verdict`、`smallest_equivalent_margin`）
`; archives outputs/analysis/cloud_vqa_full451_{base,5,6}.json`，fields `accuracy`、`token_f1`、`hypotheses`、`refs`、`meta.train_samples`。

**校验**：全仓 `paper3/**/*.tex` 中，旧的 300 题数字（0.0433 / 0.0074 / 0.0767 / 0.0713 / 0.0633 / 0.0067 / 0.4276 / 0.3563）
**已一处不剩**；唯一命中是第 1232 行的新 CI 端点 `[-0.0790,-0.0074]`（子串巧合，非旧值）。
文中仍出现 "300" 的三处均为**历史指称**（"not only the first 300"、"carried over from the 300-question analysis"、
"earlier 300-question … are superseded"），不是当前结果。

## 4. 审计门禁改动（含行号范围）

`paper3/paper_ieee/audit_check.py`：

| 行号 | 改动 |
|---|---|
| 4–13 | 模块 docstring 记录本轮（S28/S17 由 300 → 451，未增删小节、未移分页） |
| 150–162 | `SUPP_NEW_NUMBERS` 收窄为**仅 S33** 五项（原 S28 三项迁出） |
| **164–195** | 新增 `SUPP_VQA451_NUMBERS`：**26 条**须存在的 451 期望（训练对 1793 未变、全测试集陈述、二项 SE 0.022、三行表格、六个 delta/CI、三个 TOST p、两个 min margin、上界 8.2、两个来源路径、S17 行文本） |
| **197–219** | 新增 `SUPP_SUPERSEDED_300Q`：**20 条**旧值**缺席**断言（旧表格串、旧 CI、`TOST $p=0.0074$`、`$+0.0433$`、`$0.0767$`、`bounded above $7.7$ points` 等） |
| 336–346 | `main()` 中新增两条硬门禁：`supplement: 451-question VQA numbers present`、`supplement: superseded 300-question VQA values absent`（失败时逐条打印缺项/复现项） |

`paper3/paper_ieee/audit_pdf.py`：

| 行号 | 改动 |
|---|---|
| 4–13 | 模块 docstring 记录本轮 |
| 174–210 | `SUPP_CHECKS` 的 S28 段由 3 条扩为 **21 条**：`1793trainingpairs`、`all451held-outquestions`、表格数字网格、六条 CI、`TOSTp=0.0057`/`0.0396`/`0.5778`、`0.0483`/`0.0820`、`+0.0532`、两个来源路径 |
| **194** | 表格 needle 用 **数字网格**：`4510.33040.35534510.38800.42174510.33480.3983`（pdftotext 把 tabular 抽成"列成组"而非逐行；同表臂标签单列一组，故以数字网格为准，仍按列序把每个 n=451 与其 accuracy/token F1 绑定） |
| **215–232** | 新增 `SUPP_SUPERSEDED_300Q`：**15 条**缺席断言 |
| 277–279 | `main()` 中新增 `supplementary.pdf free of superseded 300-question value: …` 逐条硬门禁 |

**一处如实记录的取舍**：`audit_check.py` 的 451 清单里**没有**放 `$0.0333$`（base−r=6 accuracy 的 min margin）。
原因：图注按指令报的是该对比的 TOST p=0.0057 与"equivalent"判定，未引用 0.0333；若把 0.0333 设成硬门禁即等于要求稿件写一个指令未要求的数。
该值仍可从归档 `contrasts.base_minus_6.accuracy.min_equivalent_margin` 读到，若 lead 希望一并写出，我再补 needle 与图注。

## 5. 编译、页数与门禁结果

编译（在 `paper3/paper_ieee/supplementary/`，`pdflatex -interaction=nonstopmode -halt-on-error supplementary.tex` **×2**）：

* 两次均 `Output written on supplementary.pdf (18 pages, 397256 bytes)`，退出码 0，无 error。
* **页数 18 → 18（不变）**，`audit_pdf.py` 的 `SUPP_PAGES = 18` **无需修改**。
* **小节数 43 → 43（不变）**，`audit_check.py` 的 "forty-three S-sections" 期望**无需修改**。
* 日志仅余既有告警：字体形状 `OT1/ptm/m/scit` 未定义、一处 Overfull \hbox（41.83pt，位于 1545–1568 行，与 S28 无关）。

门禁（全部在本机实测）：

| 命令 | 结果 |
|---|---|
| `python paper3/paper_ieee/audit_check.py` | **0 hard failure(s), 0 warning(s)**；其中 `451-question VQA numbers present [all 26 present]`、`superseded 300-question VQA values absent [none of 20 present]` |
| `python paper3/paper_ieee/audit_pdf.py` | **0 hard failure(s), 0 warning(s)**；`main.pdf page count == 10 [measured 10]`、`supplementary.pdf page count == 18 [measured 18]` |
| `python -m tools.paper_audit audit --profile p3_prl --fail-on NONE` | **BLOCKED / grade D：pass=49 fail=1 warn=0 manual=9 skip=27 error=0**；唯一失败为 **A-01 `uncommitted changes under paper3/paper_ieee`** —— 即**预期中的 git-dirty**，待 lead 提交后即消。除此之外**无其它失败**。报告：`docs/audits/AUD-p3_prl-20261024T102508Z.md` / `.json` |

本轮改动文件（`git status --porcelain`）：`M paper3/paper_ieee/audit_check.py`、`M paper3/paper_ieee/audit_pdf.py`、
`M paper3/paper_ieee/supplementary/supplementary.tex`（+ 新建本文档）。diffstat：3 files changed, 165 insertions(+), 32 deletions(-)。
四个新归档落在 `outputs/` 下，被 `.gitignore` 忽略（未出现在 `git status`），与仓库既有约定一致。

## 6. 建议的 provenance manifest 行（**尚未落地**）

`docs/provenance_manifest.json` 在 `manuscripts/P3/floats[18]` 的 `tab:vqa` **仍指向 300 题归档**，需由 lead 替换为下条
（注意该文件**不在本轮写入范围**，故此处只给出待落地的行）：

```json
{
  "label": "tab:vqa",
  "kind": "table",
  "script": "tools/_p1613_p3_cloud_runner.py",
  "archive": "outputs/analysis/p3_vqa_full_equivalence.json",
  "archives": [
    "outputs/analysis/cloud_vqa_full451_base.json",
    "outputs/analysis/cloud_vqa_full451_5.json",
    "outputs/analysis/cloud_vqa_full451_6.json",
    "outputs/analysis/p3_vqa_full_equivalence.json"
  ],
  "status": "pending",
  "note": "S28/S17 rewritten 2026-10-24 from the 300-question subset to the full 451-question test set; values from p3_vqa_full_equivalence.json :: vqa_equivalence.contrasts.*, claim_verdict and smallest_equivalent_margin. Supersedes the cloud_vqa1793_{base,5,6}.json archives for this table; the 300-question analysis stays archived in p3_rank_separation_extended.json and is cited only as superseded."
}
```

配套动作（同样超出本轮范围）：`tools/_p1428_provenance_gate.py` 若把 `status` 限为 `verified|exempt`，需在核对归档后改为 `verified`；
`status` 保留 `pending` 是有意为之——**归档已实测、但 manifest 尚未改，落盘前不应写成"已核"**。

## 7. 未做 / 待办（如实标注）

1. **未提交**：本轮改动留在工作区（A-01 因此失败），需 lead 提交。
2. **未更交接文档**：`HANDOFF.md`、`文件地图.md` 按指令未动；`docs/p3_cloud_round_notes.md`（该轮的准备记录）第 317–327 行
   仍以"待改写"口吻描述 S28，**现已过时**，建议 lead 在该文档加一条"已由 `docs/p3_vqa451_round_notes.md` 落实"的指向，而非改写历史条目。
3. **未动 `docs/P3_SUBMISSION_STATUS.md` / `docs/p3_rank_separation_text.md`**：两者仍引用 300 题数字，属其它文档，超出写入范围。
4. **`comparison_to_300q_archive` 为 `null`**：本轮因此未做 300↔451 的量化对比叙述；若需"题量增加是否改变结论"的定量说明，需云端补该聚合字段。
5. **`SUBMISSION/**` 未重建**：投稿包内的 supplementary 仍是旧版；重建属超出范围，且包内文件名规则（无下划线）由 `tools/_p1336_build_venue_package.py` 负责。