# P3 补充材料整合 —— 收尾pass记录

日期：2026-10-24（会话时间 22:23–22:30 +08:00）
对象：`paper3/paper_ieee/`（Paper 3, PRL `PRLETTERS-D-26-02378`）
背景：上一个 agent 整合了三个新补充章节后中途失败；本轮只做收尾，不重写。

## 一、接手时已由失败 agent 落地（实测复核，非转述）

| 已做 | 复核方式 | 结果 |
|---|---|---|
| 三个新章节入稿 | `supplementary.tex` 中 `\section{` 计数 | 46 节；`app:allocation-paired` L979、`app:rc-boundary` L1562、`app:gammarobust` L1864 |
| `main.tex` 主文修正 | `sections/experiments.tex` | 已含修正号 `+263.90` \emph{above}、AdaLoRA 边界句、`+1477` |
| 补充材料内部 (Sxx) 指针重编号 | `git diff` | 已按 +1（旧 S20–S33→S21–S34）/ +2（旧 S34–S43→S36–S45）完成 |
| `audit_check.py` | 检查 `forty-six S-sections`、range 检查由文件推导 | 已是 46 节硬检查 |
| `audit_pdf.py` | `SUPP_PAGES = 22`、`SUPP_SECTIONS = range(1,47)` | 已是 22 页 / S1–S46 |
| `docs/provenance_manifest.json` | 三张新表逐条查 | `tab:alloc-paired` / `tab:rc-boundary` / `tab:gammarobust` 均 `status: verified`（script + archive + fields 齐全） |

**未落地（本轮补完）**：`main.tex` L108 仍写 `S1--S43` —— 这正是两份审计的硬检查点（`audit_check.py` 按文件推导出 `S1--S46` 后比对主文声明）。失败 agent 当年的注释把它记为"write scope 之外"，所以留红了。

## 二、本轮实际改动（4 个文件，全部外科式）

1. `paper3/paper_ieee/main.tex` L108：`Supplementary Sections~S1--S43` → `~S1--S46`（唯一一处残留；全树已无其他 `S43` 指针）。
2. `paper3/paper_ieee/audit_check.py`：更新已过期的说明性注释（原称"main.tex 在 write scope 之外、range 检查会一直红"）与失败详情文案，改为"收尾轮已改为 S1–S46"。
3. `paper3/paper_ieee/audit_pdf.py`：同上更新头部注释；L378 注释 `S1--S43 pointer` → `S1--S46`。
4. `docs/p3_integration_finish_notes.md`：本文件（新建）。

`tools/_p1454_final_verify.py` **未改**：其 `PAGES` 只登记 `paper3/paper_ieee/main.pdf: (10,)`，本轮编译后 main.pdf 仍为 10 页，无需变更（该脚本不跟踪 supplementary.pdf）。

## 三、编译与计数（本轮实测）

| 产物 | 页数 | 编译 | LaTeX error | undefined ref/cite | Overfull hbox |
|---|---|---|---|---|---|
| `paper3/paper_ieee/main.pdf` | **10** | `pdflatex` ×2，无 rerun 请求 | 0 | 0 / 0 | 0 |
| `paper3/paper_ieee/supplementary/supplementary.pdf` | **22** | `pdflatex` ×2，无 rerun 请求 | 0 | 0 / 0 | **4** |

补充材料 4 处 overfull hbox（均为 caption/表体，非正文段落）：

- L236（59.86pt）、L542（55.86pt）——本轮新增的 archive 字段串（`rc_by_family...crossing_point` / `mean_dE_by_rank`）撑宽；
- L1899–1921（20.72pt）——新 S46 的表 `tab:gammarobust`；
- L1670–1693（41.83pt）——旧内容（S38）。

前三处属本轮整合引入的排版瑕疵；一律未改（不得重构正文，且 `supplementary.tex` 归另一 agent 所有）。`paper_audit` 的 B-04 只读 `main.log`，故仍 PASS。

## 四、门禁结果（全部本轮实测）

| 门禁 | 结果 |
|---|---|
| `python paper3/paper_ieee/audit_check.py` | **PASS** —— 0 hard failure / 0 warning，exit 0（含 `forty-six S-sections`、range `S1--S46`） |
| `python paper3/paper_ieee/audit_pdf.py` | **PASS** —— 0 hard failure / 0 warning，exit 0（main.pdf 10 页、supplementary.pdf 22 页、`heading S46.`、`range S1-S46` 全 PASS） |
| `python -m tools.paper_audit audit --profile p3_prl --fail-on NONE` | **BLOCKED / grade D**，PASS 48 / FAIL 1 / WARN 1 / SKIP 27 / MANUAL 9 / ERROR 0 —— 唯一 FAIL 为 A-01「paper3 下有未提交改动」（在飞工作未提交，预期内）；WARN 为 J-01「claim-ledger 证据早于稿件源文件」 |
| `python tools/_p1428_provenance_gate.py` | **PASS**，exit 0 —— P3: floats=4 manifest=42 missing=0 pending=0 broken_paths=0 |
| `python tools/_p1637_p3_reproduce_all.py --check --quiet` | OK **832** / MISMATCH **2** / UNSOURCED 45 / UNCHECKED 0 / TOTAL 879，exit 1（详见下节，属另一 agent 在飞文件） |

## 五、遗留问题（均归另一 agent / 未修，仅报告）

1. **`tools/_p1637_p3_reproduce_all.py` 第 1303 行条目 `m-supp-s43` 自身过期**：
   `calc("m-supp-s43", ..., "S1--S43", ..., 43.0, count_supp_sections())`。
   `calc()` 的 `printed` 是**硬编码字符串**，不是从 `main.tex` 解析的，所以本轮把 main.tex 改成 `S1--S46` 后该条目仍报
   「printed S1--S43, recomputed 46」MISMATCH。修法明确：`printed` 改 `S1--S46`、`expected` 改 `46.0`、note 里"两处不一致"的说法删掉。
   **未改**：该文件不在本轮 write scope，且是另一 agent 的在飞文件。
2. **`s11-corr-cg` MISMATCH（旧内容）**：`supplementary.tex:622-623` 印 `r(rank, CG) = -0.43`，复算 `-0.424796723`，
   偏差 `0.00520328 > tol 0.005` —— 是容差边界上的四舍五入问题（-0.4248 印成 -0.43），非新增章节引入。归另一 agent（unsourced-remediation）。
3. **`sections/discussion.tex` 三处 (Sxx) 指针仍是整合前编号**（该文件 mtime 2026-10-24 20:00，早于整合轮，未被任何 agent 改过）：
   - L61 limitation (4)：「newer model family … (Section~S20)」→ S20 现在是 *Paired re-analysis*，目标节已移到 **S21**；
   - L71 limitation (6)：「stack means in `p3_env_matrix3.json` (S29, S37)」→ 环境内容在 **S30**（Second-environment reproducibility）与 **S39**（Variance decomposition），应为 **(S30, S39)**。
   `audit_check.py` 原有注释已记下期望值 S30/S39，但两份审计都只校验补充材料自身 (Sxx) 的**取值范围**，不校验主文散指针的**指向**，所以这两处不会被门禁拦住。**未改**：`sections/*.tex` 不属本轮 write scope。
4. **WARN J-01**：`claim_ledger*.json` 早于稿件源文件 —— 需在定稿后重跑 `tools/_claim_ledger.py --apply`；本轮未做（不在 write scope）。
5. **A-01**：本轮所有改动**未提交**（工作树 dirty）。这是设计使然——另一 agent 仍在同目录作业，中途 commit 会把它的半成品一并固化。定稿后统一提交即可解除。

## 六、与另一 agent 的在飞冲突

- 另一 agent（`_p1637` / unsourced-remediation）在飞文件：`supplementary.tex`、`sections/*.tex`、`sections_full/*.tex`、`main.tex`、`tools/_p1637_p3_reproduce_all.py`。
- 截至本记录写入时（22:29），其最后写入时间为 `supplementary.tex` 22:20:20、`sections/experiments.tex` 22:15:42、`_p1637_p3_reproduce_all.py` 22:17:29，之后**未见新写入**（疑似已停）。
- 本轮对 `main.tex` 的修改（22:24:13）写完即复核仍在；无相互覆盖。
- **风险提示**：若另一 agent 之后按"整文件写回"方式改 `main.tex`，可能把 `S1--S46` 退回 `S1--S43` —— 接手方请重跑两份审计确认。