# P3 第二个下游任务 POPE 整合笔记（task-18，2026-10-25）

> 状态：**已完成**（门禁全部实跑，见 §7）。本文件是 task-18 的交付件与缺陷记录。
> 范围：`paper3/paper_ieee/supplementary/supplementary.tex`（S29 内新增 `\subsection`）、
> `paper3/paper_ieee/audit_check.py`、`paper3/paper_ieee/audit_pdf.py`、
> `tools/_p1640_p3_second_downstream.py`（修复）、`tools/_p1637_p3_reproduce_all.py`（账本）、
> `docs/provenance_manifest.json`、`outputs/analysis/p3_second_downstream.json`（本地重算）、
> `docs/audits/AUD-p3_prl-20261025T023624Z.{md,json}`（审计产物）。
> **未动**：`main.tex`、`sections/*.tex`、`SUBMISSION/**`、`HANDOFF.md`、`文件地图.md`、其它论文。

---

## 1. 归档来源与校验（先于任何写作）

云端 `p3-downstream` 把 POPE 产物取回到 `cloud_retrieved/round2_2026-10-25/pope/`，附
`POPE_SHA256.txt` 与实例侧 `verify.json`（`n_failures: 0`）。本任务用
`tools/_p1645_stage_pope_archive.py` 逐文件核对 sha256 后落到 `outputs/analysis/`：

| 文件 | 字节 | sha256（前 16） | 校验 |
|---|---|---|---|
| `p3_second_downstream.json` | 12957 | `1c389125f0c3ce55` | ✅ 与实例一致 |
| `p3_second_downstream_base.json` | 1459283 | `a458a76602a18363` | ✅ |
| `p3_second_downstream_5.json` | 1353582 | `ea042cb675ecf629` | ✅ |
| `p3_second_downstream_6.json` | 1356329 | `ff1e8f96149e3970` | ✅ |
| `p3_second_downstream_prepare.log` | 1506 | `bd34c056c8c04bb4` | ✅ |
| `p3_second_downstream_eval.log` | 22733 | `a70d1132cd69a9e0` | ✅ |

实例侧日志结论：`[3] arm=={base,5,6} accuracy/token_f1/pope_f1/yes_ratio (n=3000)`、
`[5] strict acceptance: satisfied`。

---

## 2. 🔴 发现并修复两个脚本缺陷（与 `_p1639` 事件同格式记录）

### D1：聚合把 `relaxed_accuracy` 装进了 `arms.*.token_f1`

- **缺陷**：`outputs/analysis/p3_second_downstream.json`（云端原版，sha256 `1c389125…`）的
  `arms.<t>.token_f1` **不是 token F1**，而是逐臂归档里的 `relaxed_accuracy`；
  `contrasts.*.token_f1` 由同一批 arm 记录构造，**继承同一误标**。
- **机制（精确位置）**：`tools/_p1640_p3_second_downstream.py::arm_from_payload()`
  原第 915 行
  `f1 = np.array([float(token_f1(a, b)) for a, b in zip(nref, nhyp)])`
  —— 被 import 的 `token_f1(refs, hyps)` 期望**两个序列**，传进来的是**两个字符串**，
  于是它 `zip` 的是**字符**而不是 token；在 yes/no 标签空间下，字符级 F1 退化成
  "假设是否以参考答案的字符开头"，数值上恰好等于 relaxed accuracy。
  对比：`--eval` 路径（第 779 行）写法正确 `per_f1 = float(token_f1([nref], [nhyp]))`。
- **证据（三方）**：
  | | 云端原版 `arms.*.token_f1` | 逐臂归档 `token_f1` | 逐臂归档 `relaxed_accuracy` |
  |---|---|---|---|
  | base | **0.8926667** | **0.6826015** | **0.8926667** ← 完全相等 |
  | r=5 | 0.8716667 | 0.8716667 | 0.8716667（碰巧相等） |
  | r=6 | **0.8460000** | **0.8409513** | **0.8460000** ← 完全相等 |

  独立复算：`tools/_p1647_pope_corrected_metrics.py` 用 `_p1516` 的 `norm()/token_f1()`
  从 `hypotheses/refs` 重算，三个臂的 accuracy/token_f1/pope_f1/yes_ratio **与逐臂归档逐项吻合
  （<5e-7）**，混淆矩阵 `tp/fp/fn/tn` 也逐项相等。
- **修复**：改成 `token_f1([a], [b])`，并加断言——聚合算出的 token F1 必须等于逐臂归档的
  `token_f1` 字段（不等即 `SystemExit`），使回归无法静默复发。
- **影响**：修正后 `contrasts.base_minus_5.token_f1.delta` 从 `+0.0210` 变为 **−0.189065**；
  `base_minus_6` 从 `+0.046667` 变为 **−0.158350**。**这两个数在稿件里曾经会印错方向。**

### D2：判定规则的符号方向与 contrast 定义相反

- **缺陷**：contrast 定义是 `delta = arm_a − arm_b`，`a = "base"` ⇒ **负值表示适配器更好**；
  原规则却按 `adapter − base` 写：`keep = equivalent or ci95[0] > 0`、`lose = ci95[1] < −margin`
  （原第 1090–1091 行）。结果：适配器**好 24.6 个点**（CI 全在 −0.05 以下）被读成"loses"，
  输出 `task_dependent_effect`。
- **证据**：accuracy `base−r5 = −0.2460`，95% CI `[−0.2627,−0.2297]`；
  `base−r6 = −0.2140`，CI `[−0.2310,−0.1970]`。按预声明散文口径（plan §7：
  "adapters 在 accuracy 上等价或更好"，即 adapter−base 的 CI 下界 > 0）：
  r5 = **+0.2460** CI `[0.2297,0.2627]`、r6 = **+0.2140** CI `[0.1970,0.2310]`，**两个都满足**。
- **修复**：`equivalent_or_better = TOST 等价 OR ci95 上界 < 0`；`loses = ci95 下界 > +margin`；
  加断言"两分支不可同时成立"；修正后标签为 **`supports_the_adapters`**（仅 accuracy 口径）。
  另在 `claim_verdict.metric_directions` 里**显式记录每个指标的方向**：
  accuracy = `adapter_better`（两臂），**yes-class F1 = `base_better`（两臂）**，
  使标签不可能被读成"所有指标都支持"。
- **处置选择**：**不用标签驱动稿件**。正文写 **metric-dependent**，把 accuracy/token-F1 的
  上升与 yes-class F1 的下降同时印出（见 §3）。

### 附带修正（同一文件）

- `_interval()` 补文档与断言，明确**一个口径**：`ci95` = 2.5/97.5 分位（双侧 95%）；
  `min_equivalent_margin` 用 5/95 分位（与 TOST 的两个单侧 5% 检验对应）。
  两者都是归档实际使用的口径，且**互相自洽**（`tools/_p1648_probe_bootstrap_variants.py`
  证明归档 `ci95` 恰为同一重采样分布的 2.5/97.5 分位）。
- `meta` 增加 `metric_definitions`、`verdict_rule`、`supersedes`（含被取代文件的 sha256、
  两条缺陷、以及"为何无需 GPU 重跑"）。
- `caveat_sentences` 新增 `metric_dependent`，并把旧的 `task_dependent` 标为 DEPRECATED
  （其句子断言"适配器掉 accuracy"，与数据不符）。
- 新增 CLI `--allow-missing-prepared`：本地未取回 `paper3/test-pope-random.parquet` 时，
  把行序子检查记为 `NOT_VERIFIED_LOCALLY`，并**代替性地**校验三个逐臂 `meta` 的
  `prepared_parquet_sha256` 一致（实测三者一致：`66faa5e6de3be237…`）。
- **不需要 GPU、也不需要重跑云端**：聚合只消费三个逐臂归档，是纯 CPU 步骤。
- **被取代的旧聚合已保留**：`outputs/analysis/p3_second_downstream_pre_correction.json`
  （sha256 `1c389125f0c3ce55056dea67ca5a3ded0ac09740465e37b640989ad66fcfb947`）。

---

## 3. 修正后的数字（全部带归档字段路径）

归档：`outputs/analysis/p3_second_downstream.json`（**重算后 sha256 = `52e4e7bd377d85cdf9cc1343a5dfe5bcb04c0b513864acb0bd3d2941e3f8f2fe`**，
同输入重跑**逐字节一致**，已实测两次）。
独立复算交叉验证：`outputs/analysis/p3_pope_corrected_metrics.json` —— **9/9 个对比
（3 pair × 3 metric）的 delta、CI、最小等价边界全部与聚合一致**。

- 数据集：`meta.dataset.{id,config,split,revision}` = `lmms-lab-encoder/POPE` / `Full` / `random` / `4db12766`；
  `meta.dataset.n_questions = 3000`；金标 yes 恰为 1500（`0.5`，由 `refs` 计数）。
- 二项标准误：`sqrt(0.25/3000) = 0.0091`（由 `meta.dataset.n_questions` 计算）。

### 三臂（`arms.<t>.*`）

| arm | accuracy | token F1 | yes-class F1 | yes 率 |
|---|---|---|---|---|
| base | 0.6256667 | 0.6826015 | 0.8849178 | 0.4326667 |
| r=5 | 0.8716667 | 0.8716667 | 0.8593350 | 0.4123333 |
| r=6 | 0.8396667 | 0.8409513 | 0.8236641 | 0.3733333 |

混淆计数（逐臂归档 `confusion.*`）：fn = **262 → 324 → 421**（金标 yes 中漏判），
fp = **60 → 61 → 41**。

### 九组对比（`contrasts.<pair>.<metric>.*`；delta = 前 − 后，故负值 = 适配器更好）

| pair | metric | delta | 95% CI | TOST p | 最小等价边界 | 等价? |
|---|---|---|---|---|---|---|
| base−r5 | accuracy | −0.2460 | [−0.2627,−0.2297] | 1.0000 | 0.2600 | 否 |
| base−r5 | token_f1 | −0.1891 | [−0.2030,−0.1752] | 1.0000 | 0.2008 | 否 |
| base−r5 | pope_f1 | **+0.0256** | [+0.0152,+0.0364] | 0.0000 | 0.0346 | **是** |
| base−r6 | accuracy | −0.2140 | [−0.2310,−0.1970] | 1.0000 | 0.2284 | 否 |
| base−r6 | token_f1 | −0.1583 | [−0.1731,−0.1438] | 1.0000 | 0.1706 | 否 |
| base−r6 | pope_f1 | **+0.0613** | [+0.0481,+0.0747] | 0.9536 | 0.0725 | **否** |
| r5−r6 | accuracy | +0.0320 | [+0.0230,+0.0413] | 0.0002 | 0.0397 | 是 |
| r5−r6 | token_f1 | +0.0307 | [+0.0218,+0.0398] | 0.0001 | 0.0383 | 是 |
| r5−r6 | pope_f1 | +0.0357 | [+0.0251,+0.0465] | 0.0057 | 0.0448 | 是 |

`claim_verdict.second_task_verdict = supports_the_adapters`（**仅 accuracy 口径**）；
`claim_verdict.metric_directions` = accuracy:`adapter_better`(两臂)、pope_f1:`base_better`(两臂)。

### 结论（稿件写法）

**metric-dependent**：两臂都显著提高 accuracy 与 token F1（远超 0.05 边界，故是"已分辨差异"
而非"等价"）；但 yes/no 先验向 "no" 移动（yes 率 0.4327 → 0.4123 / 0.3733，在**金标 0.5 平衡集**上），
r=6 的 yes-class F1 掉 **+0.0613**（CI [+0.0481,+0.0747]）**超出**预声明 0.05 边界、**不判等价**，
r=5 掉 **+0.0256**（CI [+0.0152,+0.0364]）**在边界内、判等价**。
因此**不能**声称"下游 accuracy 增益证明了对齐能量排序可迁移"；能支撑的是更弱的陈述：
**r=5 在全部三个指标上都优于 r=6**，方向与其对齐损伤更小一致。

---

## 4. 稿件改动（行号为改动后）

`paper3/paper_ieee/supplementary/supplementary.tex`：

| 位置 | 改动 |
|---|---|
| **1405–1467** | **新增** `\subsection{A second downstream task: POPE}`（`\label{app:pope}`）+ 一段协议说明 + `\label{tab:pope}` 表（3 臂 × 5 列）+ 结果与边界段 + Source 行。**置于 S29 内、`\section{Second-environment reproducibility}` 之前**。 |
| 表 | 新表 `tab:pope`（`[htbp]`）；长 `\texttt` 路径加 `\allowbreak`，消掉 1 条 overfull |

- **是 `\subsection` 而非 `\section`** ⇒ 补充材料仍 **46 段**，`main.tex:108` 的
  `S1--S46` 指针**无需改动**（审计已确认 46 段、指针全在范围内且仍指向正确节）。
- 表格编号：新增 1 张表 ⇒ 补充材料编号表从 **S1–S49** 变为 **S1–S50**（后续表号自动顺延，全部经 `\ref` 引用）。

---

## 5. 审计/账本/清单改动

### `paper3/paper_ieee/audit_check.py`
- 新增 `SUPP_POPE_NUMBERS`（24 条 present 针脚，逐条对应 §3 的数字/句子）与
  `SUPP_POPE_ABSENT`（4 条退役针脚：`0.8927`、`0.8460`、`$+0.0210$`、旧的 task-dependent 句子）。
- 新增 "POPE SECOND-DOWNSTREAM ROUND" 检查段（present/absent）。
- 表数硬检查由 **49 → 50**（"fifty table floats (the readability splits added three, POPE added one)"）。

### `paper3/paper_ieee/audit_pdf.py`
- `SUPP_PAGES` **23 → 26**；`SUPP_TABLE_HEADINGS` 由 `range(1,50)` → `range(1,51)`，
  检查文案 `S1--S49` → `S1--S50`，头部说明同步。
- 新增 15 条 PDF 针脚（POPE 子节标题、表头、**表格数字网格**
  `300030003000accuracytokenF1yes-classF1yesrate0.6257…0.3733`、六条 CI/delta、
  r5-vs-r6 三条、`metric-dependent`、来源归档名）。

### `tools/_p1637_p3_reproduce_all.py`
- 在 S28 块之后、S29 环境块之前新增 **S29b 块（80 行）**，把 §3 的每个数字登记为
  归档字段（`arms.*`、`contrasts.*`、`confusion.*`、`meta.dataset.n_questions`）或
  `calc`（1500 金标 yes、0.0091 二项 SE、verdict 与方向断言）。

### `docs/provenance_manifest.json`
- P3 增加 `tab:pope`（script `tools/_p1640_p3_second_downstream.py`；
  archive `outputs/analysis/p3_second_downstream.json` + 三个逐臂 + 独立复算；
  字段路径写在 `note`；`status: verified`）。

---

## 6. 计数

| 项 | 基线 | 现在 |
|---|---|---|
| `main.pdf` 页数 | 10 | **10**（未变） |
| `supplementary.pdf` 页数 | 23 | **26**（+3） |
| 补充材料 `\section` 数 | 46 | **46**（未变） |
| 补充材料编号表 | 49（S1–S49） | **50（S1–S50）** |
| 补充材料 overfull | 0 | **0** |
| Float too large | 0 | 0 |
| provenance manifest P3 条数 | 42 | **43** |
| 账本条目 | 940 | **993** |

> ⚠️ 补充材料 +3 页：新增子节约 1 页文字 + 1 个表浮动体；页数变动已在
> `audit_pdf.py::SUPP_PAGES` 与 `paper_audit` 的 D-07 中如实反映（D-07 PASS，26 页）。

---

## 7. 门禁（全部实跑，2026-10-25）

| 命令 | 结果 |
|---|---|
| `pdflatex ×2 supplementary.tex`（supplementary/ 内） | 退出 0；**26 页**；overfull **0**；float-too-large 0 |
| `pdflatex + bibtex + pdflatex ×2 main.tex` | 退出 0；**10 页**；overfull **0** |
| `python paper3/paper_ieee/audit_check.py` | **0 hard failure / 0 warning**（46 段、S1--S46、50 表、POPE 24 present + 4 absent 全过） |
| `python paper3/paper_ieee/audit_pdf.py` | **0 hard failure / 0 warning**（main 10 页、supp 26 页、S1–S50 全部印出、15 条 POPE PDF 针脚全过） |
| `python -m tools.paper_audit audit --profile p3_prl --fail-on NONE` | pass=**49** fail=**1** warn=0；**唯一 fail = A-01 "uncommitted changes under paper3/paper_ieee"**（工作区脏，非本轮引入；见 §9）；**D-07 PASS（supplementary 26 页）**、D-01 PASS（10 页）、B-04 PASS（0 overfull）、B-05 PASS |
| `python tools/_p1428_provenance_gate.py` | **gate: PASS**（P3 broken_paths 0、missing 0、pending 0） |
| `python tools/_p1637_p3_reproduce_all.py --check --quiet` | **OK 955 / MISMATCH 0 / UNSOURCED 0**（TOTAL 993） |
| `python tools/_p1640_p3_second_downstream.py --self-test` | 退出 0（54 个数字断言全 OK） |
| `python tools/_p1640_p3_second_downstream.py --aggregate --strict --allow-missing-prepared` | 退出 0；`[4] assertion ledger: 5 checks, 0 failed`；`[5] strict acceptance: satisfied`；`[6] printed-number ledger: 54 numbers …` 全 OK |
| 聚合确定性 | 同输入重跑 **逐字节一致**（sha256 `52e4e7bd…` 两次相同） |
| `python tools/_p1644_verify_pope_archive.py` | **VERIFICATION PASSED**（逐臂指标从 hypotheses 重算、acceptance、verdict 重推、metric_directions 全过） |
| `python tools/_p1647_pope_corrected_metrics.py` | **9/9 对比与聚合精确一致**（delta/CI/最小边界） |
| `python tools/_p1645_stage_pope_archive.py` | 6/6 文件与实例 sha256 一致后落地 |

---

## 8. 未完成 / 限制（如实标注）

1. **`paper3/test-pope-random.parquet` 未取回本地** ⇒ 聚合的 `acceptance
   .refs_match_prepared_parquet_order` 记为 `NOT_VERIFIED_LOCALLY`（字符串，不是 True）；
   代替检查是三个逐臂 `meta.prepared_parquet_sha256` 一致（`66faa5e6de3be237…`）。
   云端原版该子检查为 true。**这是本地重算唯一无法复验的验收项。**
2. **补充材料页数 +3（23→26）**：非笔误，已同步 `SUPP_PAGES` 与 D-07。
3. **未提交**：全部改动仍是工作区未提交状态，导致 `paper_audit` 的 **A-01** 唯一失败。
   这与上一轮（可读性轮）记录的情况相同；是否提交由 lead/操作者决定，不在 task-18 写范围内。
4. **未改** `HANDOFF.md` / `文件地图.md`（不在 task-18 写范围；请 lead 按阶段收尾规则更新）。
5. **未改任何 `paper3/**/sections/*.tex` 与 `main.tex`**：POPE 材料按任务要求放在补充材料 S29 内。

---

## 9. 与上一轮记录的关系

- 上一轮（可读性轮，`docs/p3_supplement_readability_notes.md`）基线是 **23 页 / 49 表 / 46 段**；
  本轮把 **表数改为 50**、**页数改为 26**，段数保持 46。
- `paper_audit` 的 A-01（未提交）在上一轮就已存在（该文档 §4 有同样记录），**不是本轮引入**。

---

## 10. 复现命令（按序）

```powershell
# 1) 归档：核对 sha256 后落到 outputs/analysis/
python tools\_p1645_stage_pope_archive.py

# 2) 修正后的聚合（CPU；--self-test 先跑）
python tools\_p1640_p3_second_downstream.py --self-test
python tools\_p1640_p3_second_downstream.py --aggregate --strict --allow-missing-prepared

# 3) 逐字段校验 + 独立复算
python tools\_p1644_verify_pope_archive.py
python tools\_p1647_pope_corrected_metrics.py

# 4) 稿件子节（幂等）
python tools\_p1649_pope_supplement_insert.py

# 5) 门禁登记（幂等）
python tools\_p1653_manifest_pope.py
python tools\_p1654_ledger_pope.py

# 6) 编译与审计
cd paper3\paper_ieee\supplementary; pdflatex -interaction=nonstopmode supplementary.tex; pdflatex -interaction=nonstopmode supplementary.tex
cd ..; pdflatex -interaction=nonstopmode main.tex; bibtex main; pdflatex -interaction=nonstopmode main.tex; pdflatex -interaction=nonstopmode main.tex
cd ..\..; python paper3\paper_ieee\audit_check.py; python paper3\paper_ieee\audit_pdf.py
python -m tools.paper_audit audit --profile p3_prl --fail-on NONE
python tools\_p1428_provenance_gate.py
python tools\_p1637_p3_reproduce_all.py --check --quiet
```

---

## 9. `POPE 验收闭环（2026-10-25 收尾）`

> 本节由 `p3-downstream` 追加；前 8 节是 task-18 的原始记录，未改动。

### 9.1 关闭 `acceptance.refs_match_prepared_parquet_order`

- 评估所用 prepared parquet 已本地化：`paper3/test-pope-random.parquet`
  **61,909 B**，sha256 **`66faa5e6de3be2374be68b8794a14cf660ff14670575ea47b9b77da8b43a71d4`**
  （与实例上同名文件哈希一致；来源 `cloud_retrieved/round2_2026-10-25/parquet/test-pope-random.parquet`）。
- 重跑命令（纯 CPU）：`python tools/_p1640_p3_second_downstream.py --aggregate --strict`
  → 输出末行 **`[5] strict acceptance: satisfied`**。
- `acceptance.refs_match_prepared_parquet_order` 现在由 `refs_match_parquet()` **真实逐行比对**
  parquet 的 `output` 列得到，而不是"预存 parquet 缺失时的替代不变量"。
- 聚合归档 sha256：
  - 重跑前（parquet 不在本机）：`52e4e7bd377d85cdf9cc1343a5dfe5bcb04c0b513864acb0bd3d2941e3f8f2fe`（15,379 B，
    副本 `cloud_retrieved/round2_2026-10-25/pope/aggregate_before_rerun.json`）
  - 重跑后（含诚实性修复，见 9.2）：**`41723dc2f1be53cf0eba0adb132c0381cf64f3524893b8fe25ab643b9dfe9e97`**（15,366 B）
- **数值零变化**：新旧 JSON 深度比对只有 **2 处差异，且都不是数值**——
  `meta.dataset.prepared_parquet`（`"not retrieved locally (see the per-arm meta)"` →
  `"paper3/test-pope-random.parquet"`）与新增字段 `acceptance.prepared_parquet_order_check: true`。
  所有 contrast 的 `delta` / `ci95` / `tost_p` / `min_equivalent_margin`、以及
  `claim_verdict.second_task_verdict = supports_the_adapters` **逐位不变**（token-F1 修正与判定修正都保住了）。

### 9.2 顺带修掉一处"把未验证写成已验证"的诚实性缺陷

- **缺陷**：`_p1640` 在 parquet 缺失（`--allow-missing-prepared`）时把行序检查写成**字符串**
  `"NOT_VERIFIED_LOCALLY (prepared parquet absent on this machine)"`，但 `aggregate_core()` 用
  `bool(match_parquet)` 存盘，而 **`bool(<非空字符串>) == True`** ⇒ 归档里出现
  `refs_match_prepared_parquet_order: true`，**而该检查从未执行**，且该字符串本身没有落盘、事后无从察觉。
  证据：重跑前归档里 `refs_match_prepared_parquet_order: true` 与
  `prepared_parquet: "not retrieved locally (see the per-arm meta)"` **同时存在**，全文无 `NOT_VERIFIED` 字样。
- **修复**：`tools/_p1650_fix_pope_acceptance_bool.py`（幂等，带断言）把该字段改为
  「`match_parquet` 是 bool 就照抄，否则记 `False`」，并新增
  `acceptance.prepared_parquet_order_check` **原样保存**哨兵字符串。布尔键类型与语义不变
  （= 行序到底有没有被真实验证），下游消费者不受影响。
- 修复后重跑仍是 `[5] strict acceptance: satisfied`，`prepared_parquet_order_check: true`。

### 9.3 第三方独立复算（另一 agent，2026-10-25）

该 agent 从**各臂原始逐题记录**重算，用归档的 `norm()`/`token_f1()`、20,000 次配对 bootstrap、RNG 20261024：

| 对比 | 指标 | 点估计 | 95% CI |
|---|---|---|---|
| base−r5 | accuracy | **−0.246000** | [−0.262667, −0.229658] |
| base−r5 | token F1 | **−0.189065** | [−0.203349, −0.174709] |
| base−r6 | accuracy | **−0.214000** | — |
| base−r6 | token F1 | **−0.158350** | — |
| r5−r6 | accuracy | **+0.032000** | — |
| r5−r6 | token F1 | **+0.030715** | — |

点估计与修正后聚合（`52e4e7bd…`）**完全一致**，CI 在 bootstrap 噪声内，判定 `supports_the_adapters`
与修正版一致、与被取代的旧版（`1c389125…`）相反 ⇒ **该修正得到独立第三方验证**。

**口径提醒（必须保持的边界）**：base 的 yes-class F1 仍**更高**（0.8849 vs 0.8593/0.8237），
因为适配器预测 "yes" 更少（0.4327 → 0.4123/0.3733）；`claim_verdict.metric_directions` 已分开记录。
⇒ **判定标签不得被扩大**为"全面更好"，正确表述只有：
**accuracy 与 token F1 提升、yes-class F1 下降**（指标依赖的第二下游结果）。

---

## 11. 措辞修改（lead 决定，2026-10-25 11:0x）：改为「先 verdict、后指标分解」

> 本节由 `p3-stats` 追加；§9（验收闭环）为 `p3-downstream` 的记录，未改动。

### 11.1 为什么改

初版 S29 子节把 "metric-dependent" 放在**标题位置**。这虽然诚实，但**没有陈述预声明 verdict**：
读者（或审稿人）一旦在补充材料中找到预声明规则（plan §7：adapters 在 accuracy 上"等价或更好"），
会觉得正文与它自己写下的规则**相矛盾**。lead 要求：**先明说预声明判据已满足
（verdict = `supports_the_adapters`），紧接着给指标分解的边界**，而不是把两者顺序倒置。

### 11.2 改法（只动 S29 POPE 子节，**数字一个未变**）

1. **第一段改为 verdict 先行**：写明预声明规则（accuracy 上等价或更好 = TOST 0.05 边界满足，
   或 base−adapter 差值的 95% 区间整体低于 0）；**两臂均满足**：
   base−r5 `−0.2460` CI `[−0.2627,−0.2297]`、base−r6 `−0.2140` CI `[−0.2310,−0.1970]`；
   token F1 同向（`−0.1891` CI `[−0.2030,−0.1752]`；`−0.1583` CI `[−0.1731,−0.1438]`）。
   因此归档 verdict 为 **`supports_the_adapters`**（字段 `claim_verdict.second_task_verdict`）。
2. **第二段紧接着给边界**：yes-class F1 反向（r5 `+0.0256` CI `[+0.0152,+0.0364]` 在 0.05 边界内→等价；
   r6 `+0.0613` CI `[+0.0481,+0.0747]` 超边界→不等价）；机制是 yes/no 先验移动
   （yes 率 `0.4327→0.4123→0.3733`、1500 道金标 yes 的漏判 `262→324→421`、误报 `60→61→41`）；
   并明说 **`claim_verdict.metric_directions` 记录了这个分裂**（accuracy = adapter better、
   yes-class F1 = base better），所以 verdict 是**关于预声明 accuracy 判据**的陈述，**不是关于所有指标**。
3. **第三段保留两条限制**：① 第二个任务**不**表明对齐能量排序可迁移到下游；
   ② r=5 在三个指标上都优于 r=6（`+0.0320` / `+0.0307` / `+0.0357`），这是该任务支撑的**更弱的方向性陈述**。
4. "metric-dependent" **不再作为标题句**（该短语已从子节文本中移除），**实质边界内容全部保留**。

### 11.3 生成器与审计针脚同步

- `tools/_p1649_pope_supplement_insert.py` 增加 **`--force`** 重渲染模式：改模板后用 `--force`
  替换整块，避免稿件与生成器漂移。本次即由 63 行替换为 **71 行**（`outputs/analysis/p3_pope_tex_insert.json`
  记录 `status: replaced`、行号与 rendered block）。
- `audit_check.py::SUPP_POPE_NUMBERS`：
  - **移除** `"metric-dependent"` 针脚；
  - **新增 7 条**：`The pre-declared criterion is met`、`\texttt{supports\_the\_adapters}`、
    `\texttt{claim\_verdict.second\_task\_verdict}`、`must be read together with the metric split`、
    `\texttt{claim\_verdict.metric\_directions}`、`does not show the alignment-energy ordering transferring`、
    来源归档名；
  - 把因换行变化失效的 4 条数字针脚改为**不含换行假设**的短串
    （`$+0.0256$` / `[+0.0152,+0.0364]` / `$0.4327$ (base) to …` / `$262$ to $324$ and $421$`），
    并把 accuracy 两条改为括号形式 `$-0.2460$ (95\% CI …)`。
- `audit_check.py::SUPP_POPE_ABSENT`：**保持**只禁止**旧被取代值**
  `0.8927` / `0.8460` / `$+0.0210$`（外加旧的 task-dependent 句子）；
  **未**把新 verdict 句列入禁止项（lead 明确要求）。
- `audit_pdf.py`：移除 `"metric-dependent"` PDF 针脚；新增 6 条
  （`Thepre-declaredcriterionismet`、`supports_the_adapters`、`claim_verdict.second_task_verdict`、
  `claim_verdict.metric_directions`、`mustbereadtogetherwiththemetricsplit`、
  `doesnotshowthealignment-energyorderingtransferringdownstream`）。

### 11.4 与 §9.1 的关系（聚合 sha 已再次变化）

本节的数字读取的是**当前**聚合 `outputs/analysis/p3_second_downstream.json`
（sha256 **`41723dc2f1be53cf…`**，15,406 B —— 即 §9.1 用本地 parquet 重跑后的版本）。
**所有数值与 lead 消息里引用的 `52e4e7bd…` 版本逐位相同**（§9.1 已逐字段比对），
且 `_p1649` 渲染时对每个数字都有断言（必须等于聚合字段），所以措辞改动不可能带入数值漂移。

---

## 12. 措辞改动后的门禁复跑（2026-10-25）

| 命令 | 结果 |
|---|---|
| `pdflatex ×2 supplementary.tex` | 退出 0；**26 页**（未变）；overfull **0**；float-too-large 0 |
| `main.tex`（pdflatex + bibtex + pdflatex×2） | **10 页**（未变）；overfull **0** |
| `audit_check.py` | **0 hard / 0 warn**（POPE 段 present+absent 全过；50 表；46 段；S1--S46 指针不变） |
| `audit_pdf.py` | **0 hard / 0 warn**（main 10、supp 26、S1–S50 全印出） |
| `paper_audit --profile p3_prl --fail-on NONE` | pass=**49** fail=**1** warn=0，**唯一 fail = A-01 "uncommitted changes under paper3/paper_ieee"**（本轮措辞改动尚未提交；`--fail-on NONE` 下退出码 0）。**同类改动在提交后该审计为 READY grade A / pass=50 / fail=0**（03:04 实测）；提交本轮 5 个改动文件即恢复。 |
| `_p1428_provenance_gate.py` | **gate: PASS**（P/ A1 / A23 / P3 全 broken_paths 0、missing 0、pending 0） |
| `_p1637 --check --quiet` | **OK 955 / MISMATCH 0 / UNSOURCED 0**（TOTAL 993，未变） |
| `_claim_ledger.py --apply` | **96/96 通过，0 失败** |
| `_p1644_verify_pope_archive.py` | **VERIFICATION PASSED**（对当前 `41723dc2…` 聚合） |
| `_p1647_pope_corrected_metrics.py` | **9/9 对比精确一致**（delta / CI / 最小等价边界） |

**计数（措辞改动后未变）**：`main.pdf` **10 页**；`supplementary.pdf` **26 页**；
`\section` **46**；编号表 **50（S1–S50）**。

### 12.1 本轮改动的文件（5 个）

| 文件 | 改动 |
|---|---|
| `paper3/paper_ieee/supplementary/supplementary.tex` | S29 POPE 子节 1405–1475 行重渲染（63→71 行；verdict 先行） |
| `paper3/paper_ieee/audit_check.py` | `SUPP_POPE_NUMBERS` 增删改（+7 条 verdict/边界针脚，4 条改短串） |
| `paper3/paper_ieee/audit_pdf.py` | POPE PDF 针脚：删 1 增 6 |
| `tools/_p1649_pope_supplement_insert.py` | 模板改写 + `--force` 重渲染模式 |
| `outputs/analysis/p3_pope_tex_insert.json` | 生成器记录（`replaced`、行号、rendered block） |

> ⚠️ **编号冲突提示**（项目规矩）：`p3-downstream` 的 `tools/_p1650_fix_pope_acceptance_bool.py`
> 与本任务此前的 `tools/_p1650_diagnose_p1640_metric_bug.py` **同号不同名**，不会互相覆盖；
> 引用时请连文件名一起看。
