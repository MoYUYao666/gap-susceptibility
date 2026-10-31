# P3 补充材料可读性轮（2026-10-25）

范围：`paper3/paper_ieee/supplementary/supplementary.tex`（+`audit_check.py` / `audit_pdf.py` 的针脚、
`tools/_p1637_p3_reproduce_all.py` 的账本条目）。**未动** `main.tex`、`sections/*.tex`、
`SUBMISSION/**`、`HANDOFF.md`、`文件地图.md`、其它论文与任何归档。

## 1. 报告（改之前的实测）

**版式（`pdflatex` 全新日志，基线 = 本轮改动前的 supplementary.tex）**

| 项 | 基线 | 现在 |
|---|---|---|
| 页数 | 22 | **23** |
| Overfull \hbox | **4 条** | **0 条** |
| Float too large | 0 | 0 |
| 段数 / 编号表数 | 46 段 / 45 个编号表（1 个无题注） | 46 段 / **49 个编号表 S1–S49** |

基线 4 条 overfull（逐条）：

1. `59.86pt` — fig:ers 题注（第 236 行）：`rc_by_family.llava-1.5-7b.strata.llava_ers_1epoch.crossing_point,`
   中的 `\texttt` 路径无断点。
2. `55.86pt` — tab:sharegpt 题注（第 542 行）：`...strata.llava_sharegpt.mean_dE_by_rank`。
3. `41.83pt` — tab:instrument 题注（第 1677–1700 行）：`outputs/analysis/p3_instrument_r24_lr0.0001.json).`。
4. `20.72pt` — **表格本体**：tab:gammarobust 第 4 列 `\texttt{rho_advantage_lost_on_linear_objective}` 撑破栏宽。

**过长的表**（数据行数，含表头则 +1）：`tab:perlayer` **33 行**（32 层 + vision 塔）、
S13 provenance 表 30 行、`tab:claims` 26 行、`tab:sharegpt` 15 行。
49 个浮动体、297 个数据行。**没有表超过一页**（日志无 `Float too large`）；超宽只有上面第 4 条。

**一格里混两种量**：

- `tab:perlayer`：32 个逐层耦合（0.02–0.13）与 vision 塔（**1.4108**）同列，量级差一个数量级。
- `tab:gammarobust`：前 3 行是 break-even 阈值 ρ，后 2 行是实测离散度比值（只靠 `\addlinespace` 分隔）。
- `tab:beta`：表头声明 5 列（β, vision, shallow, mid, deep），数据行却只有 2 格 `0.05 & 4/4/4/4`
  —— 同一格的四个块秩被斜杠塞进一列，PDF 里读作 `4/4/4/4`。

**必须交叉读 3 张以上表才能读懂的数**：`r=5/6` 交叉点的定位要同时读 S10 tab:samplesize、
S14 tab:seed5、S16 tab:protocol_shift、S34 tab:crossing10、S35 tab:rc-boundary、S33 tab:robust 六张表；
环境占比要在 S17 tab:claims、S30 tab:envcloud、S39 tab:envvar 三处之间来回对。

**表格编号错位（最严重的一条）**：4 个表的 `\label` 写在 `\caption` **之前**
（tab:gamma_detail / tab:gamma_rank / tab:samplesize / tab:sharegpt），于是 `\ref` 解析到**所在节**的计数器：
正文里印成 “Table S4”“Table S5”，`tab:samplesize`/`tab:sharegpt` 更印成 **“Table S9.5”“Table S9.6”**
（第 9.5/9.6 小节号），读者按它去找表会走错。

**S17 环境行与本轮之前不一致**：`tab:claims` 的 “crossing stable across torch/CUDA versions” 行仍印
三栈取值（means −23/−44/+25、share **45%** [21, 75]、指针 **S29, S37**），而 S39/S30 已改为四栈
（49.59%、[35.8%,74.9%]、S30/S39）——同一件事两张表两个数。

**墙状文本**（本轮只报告、不删改）：S6 “Decoder VLM” 242–271 行一整段约 700 词、S7 “Downstream check”
286–309 行约 450 词、S20 982–1016 行约 35 行、S34 1545–1559、S46 1884–1912。
另有**三重重复**：“Decoder VLM (summary)” 在 S6（273–282）、S9（587–596）各印一次，
“Downstream check (summary)” 在 S7（311–326）、S9（570–585）各印一次；两处标题还带 “.}” 前的空格笔误。
`tab:claims` 的 21 个 “(Sxx)” 指针逐条核对过：20 个指向正确的节，只有环境行的 (S29, S37) 是实质错指（已修）。

## 2. 改了什么（改动后行号）

| 位置 | 改动 | 表标签 |
|---|---|---|
| 48–115 行 | **新增** claims / evidence / boundary 摘要表（6 行：交叉点、环境占比、秩/目标控制、decoder 阶梯、分配对比、迁移边界），置于正文最前，成为 **Table S1**；每格都是 `\ref` 到已有标签或归档值 | `tab:claims-summary`（S1） |
| 967 行 | S17 环境行由三栈改为四栈（means −23.0/−43.7/+24.0/−63.8、share 49.59%、CI [35.8%,74.9%]），指针 S29,S37 → **S30,S39** | `tab:claims` |
| 1473–1543 行 | `tab:perlayer` 一表拆二：`llm_00–llm_15` / `llm_16–llm_31` + vision 塔（vision 用 `\midrule` 单列并说明不同量级）；原本夹在浮动体内的“Ten-seed robust summaries”段落移回正文 | `tab:perlayer`、`tab:perlayer-tail` |
| 2011–2061 行 | `tab:gammarobust` 一表拆二：break-even 阈值 / 实测离散度比值；列宽改 `p{}` 修掉超宽 | `tab:gammarobust`、`tab:gammarobust-noise` |
| 1570–1586 行 | `tab:beta` 由斜杠打包改为 5 列真网格（6 行数据一行不少） | `tab:beta` |
| 220 / 254 / 543 / 611 行 | 4 个 `\label` 从 `\caption` 之前移到之后，`\ref` 现在解析到真正的表号 | 同上四表 |
| 842 行 | S13 无题注浮动体补题注（原表无编号、无法被引用），并在正文说明覆盖范围（后加的表在各自题注里给归档；权威清单是 `docs/provenance_manifest.json`） | `tab:provenance`（S10） |
| 305, 609, 1778, 1796 行；2023, 2050–2051 行 | 无断点 `\texttt` 路径插入 `\allowbreak`，消掉 3 条正文/题注超宽；`tab:gammarobust` 长字段名逐下划线加断点 | — |
| 343, 657, 355, 381, 640 行 | 修 `replicate .}` / `suggest\n.}` 的空格-句点笔误 | — |

**未生成任何新图**：任务允许“长表 → 紧凑表 + 图”，但生成图需要新的 PNG 与 `tools/` 出图脚本
（两者都不在本轮写范围内，且会新开一条 provenance 条目），故按兜底方案拆表——数据一行未删
（49 表 / 297 数据行，`audit_check.py` 新增 “forty-nine table floats” 硬检查）。

## 3. 新计数

`main.pdf` **10 页**（未动）；`supplementary.pdf` **23 页**、**46 段**（`main.tex` 的 S1–S46 声明仍成立）、
**49 个编号表 S1–S49**、0 overfull、0 float-too-large。

## 4. 门禁（全部实跑）

| 命令 | 结果 |
|---|---|
| `pdflatex -interaction=nonstopmode supplementary.tex` ×2（supplementary/ 内） | 退出 0；23 页；overfull **0**；float-too-large 0；字体形状 1 条 + hyperref 15 条与基线相同；`[h]`→`[ht]` 提示 44 条（基线 40 条）：浮动体由 46 增到 49（46 个 `[h]` + 3 个 `[t]`），该提示只说明 `h` 未被满足，非缺陷 |
| `python paper3/paper_ieee/audit_check.py` | **0 hard failure / 0 warning**；新增 SUPP_READABILITY_NUMBERS(14) / _ABSENT(3) + 结构检查（49 浮动体、每表恰一个 `\caption`、`\label` 不得早于 `\caption`） |
| `python paper3/paper_ieee/audit_pdf.py` | **0 hard failure / 0 warning**；`SUPP_PAGES 22→23`；新增 S1–S49 表头全在、16 条摘要表/拆表针脚、5 条“替换形态必须消失”针脚（含 `TableS9.5`/`TableS9.6`） |
| `python -m tools.paper_audit audit --profile p3_prl --fail-on NONE` | pass=49 fail=**1** warn=0 → **BLOCKED / grade D**；唯一 fail = **A-01** “uncommitted changes under paper3/paper_ieee” |
| `python tools/_p1428_provenance_gate.py` | **PASS**（paperA 32/32、A1 35/35、P3 4/4、A23 34/34，broken_paths 0） |
| `python tools/_p1637_p3_reproduce_all.py --check --quiet` | **OK 902 / MISMATCH 0 / UNSOURCED 0**（TOTAL 940；新增 22 条断言 + 7 条 DUPLICATE 指针） |

**A-01 说明（不是本轮引入）**：`git show HEAD:paper3/paper_ieee/supplementary/supplementary.tex` 里没有
`p3_env_stack_seeds.json`、`49.59\%`、`1.08\times10^{-5}` 等上一轮（2026-10-25 种子轮）的内容，
说明本轮开工前工作区**已经是脏的**；本轮的 3 个文件与账本条目同样未提交。是否提交留给 lead/操作者决定，
不在本轮写范围内。其余与补充材料有关的检查均通过：B-04 无 overfull、B-05 无超页浮动体、
**D-07 supplementary 23 页**、F-05 一致性门禁、I-04 frozen 文件未变。

## 5. 故意没动

1. **三重重复的两段小标题**（S6/S7 的 “(summary)” 与 S9 内的同名小节，共 4 处）：内容与正文同源，
   删除属于内容决策而非排版修复；已在上文报告，改动量小、可随时单独一轮处理。
2. **墙状长段**：只报告（S6/S7/S20/S34/S46），未重写措辞——本轮不引入新的表述风险。
3. **S13 provenance 表的覆盖缺口**：它自称 “every table and figure”，实际只列到 `tab:vqa`，
   缺 S18/S37/S48/S49/S32/S1 等后加表。已把正文改成如实描述并把权威清单指向
   `docs/provenance_manifest.json`，**没有**替它补行（补行要同时动 manifest 与账本，超出本轮范围）。
4. **`\resizebox` 缩放的 5 张表**（tab:gamma_detail / tab:gamma_rank / tab:samplesize / tab:sharegpt /
   tab:supp-rank）：它们按 `\columnwidth` 等比缩小，永不超宽，但 8pt 字被再缩小；本轮只保留。
5. **44 条 `[h]`→`[ht]` 浮动体警告**：全仓库既有写法，非缺陷。
6. `main.tex` / `sections/*.tex` / `SUBMISSION/**`：按写范围不动（因此 S17 之外没有节号变化，
   `main.tex:108` 的 S1–S46 无需改）。