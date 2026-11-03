import io

PATH = "docs/paperA_logic_review_2026-10-25.md"

SECTION = """

---

# Applied fixes（2026-10-25 执行，"全改"；只改稿件，未提交）

> 逐条列出已落到 live 稿的改动。两版共用 `paper合/sections/*`，故正文改动同时进入两版。
> 硬约束：页数必须仍为 **NC 79 / Springer 56**、0 错误 / 0 未定义引用 / 0 overfull、不碰 `SUBMISSION/**`、
> 不改 `tools/_p1454_final_verify.py`、不提交 —— 全部达成（验证见本节末）。

## A-1：DG 不再被称作 predictor（8 处）

| # | 位置（新行号） | 改动 | 理由 |
|---|---|---|---|
| 1 | `paper合/sections/empirical.tex:161` | 小节标题 `Distribution Gap Predicts Retrieval Performance` → `Distribution Gap Is Associated with Retrieval Performance` | 摘要写 "association, not a predictor" |
| 2 | `paper合/sections/empirical.tex:164` | "A key statistical discovery is that the Distribution Gap strongly predicts retrieval performance." → "A key empirical regularity is that the Distribution Gap is strongly associated with retrieval performance." | 同上 |
| 3 | `paper合/sections/empirical.tex:169` | 图注 "as retrieval predictors" → "as correlates of retrieval" | 同上 |
| 4 | `paper合/sections/empirical.tex:181` | 表头 `Predictor` → `Statistic`（表行 DG / CG / CG$\\Delta$ 不变） | 同上 |
| 5 | `paper合/sections/theory.tex:125` | 段首 `DG as a retrieval predictor.` → `DG as a correlate of retrieval.`；"DG predicts R@1" → "DG is associated with R@1" | 同上 |
| 6 | `paper合/sections/validation.tex:202` | `DG as predictor:` → `DG as a correlate of retrieval:` | 同上 |
| 7 | `paper合/sections/introduction.tex:5` | "predicts retrieval performance at $r=-0.714$" → "is associated with retrieval performance at $r=-0.714$" | 同上 |
| 8 | `paper合/sections/introduction.tex:20` + `paper合/sections/conclusion.tex:5` | "DG-based retrieval prediction" → "the DG--retrieval association"；"predicts retrieval performance" → "is associated with retrieval performance" | 同上 |

## A-2：DG 优于 CG 降为描述性（3 处，未引入任何新数字）

| 位置 | 改动 | 理由 |
|---|---|---|
| `paper合/sections/introduction.tex:5` | "far outperforming the commonly reported Centroid Gap" → "more strongly than the commonly reported Centroid Gap" | 无差异检验支撑时不作"显著更优"表述 |
| `paper合/sections/empirical.tex:164` | "substantially outperforming CG ($r=-0.594$)" → "higher than CG ($r=-0.594$)" | 同上 |
| `paper合/sections/empirical.tex:169` | "substantially stronger than CG" → "higher than CG" | 同上 |

**为什么没有采用"两区间重叠 ⇒ 不作差异声明"的措辞**：我用归档三值算了 Hotelling--Williams 相依相关检验
（输入 `outputs/analysis/dg_r1_reproducible.json :: primary.DG_vs_R1 = -0.7142`、
`primary.CG_vs_R1 = -0.5939`、`primary.DG_vs_CG = 0.9451`，`n = 204`）：
**t = -7.86，df = 201，p < 0.001** —— 两个预测子近乎共线（r = 0.945），差异其实高度显著；而"边缘区间重叠"
只描述各自的不确定性，**不能推出差值不显著**（那样写是统计谬误）。因此稿中只做纯描述性降级
（"higher than"），既不加新数字也不写错误推理。若日后要恢复"显著更优"，正确做法是对 $\\Delta r$ 做
**family 聚类自举区间**（`rows[*]` 与 first-path-component 标签均在归档里），与全文聚类口径一致。

## b1：删除重复且自指的 Data availability 小节（1 处删除）

`paper合/sections/conclusion.tex:12-15`（原第 13--15 行及其前导空行）—— 删除
`\\subsection*{Data availability}` 与 "see the Data availability statement in the front matter"。
理由：真正的声明在 back matter（NC 为 `main_nc.tex:81` 起、Springer 为 `\\bmhead` 段），该小节重复且自指。
效果：PDF 里 "Data availability" 由 2 处降为 **1 处**（两版均如此）。

## b2：Springer 的 Data availability 对齐 NC（`main_springer.tex:85-87`，5 处补齐）

① "the per-epoch monitoring trajectories, the strict-freezing controls and the cross-architecture sweeps,
together with the analysis scripts that compute the reported statistics and the training configurations"；
② "in a public repository at"；③ "snapshot **archived on Zenodo** under version DOI ... (\\url{doi})"；
④ "which carries them at and after that release"；⑤ "**No datum used here is restricted.**"
⇒ 两版 Data availability 现已**逐字相同**（用 PDF 文本逐词比对确认，差异仅为抽取时空格）。

## b3：披露分层标签是推导的（1 处）

`paper合/sections/provenance_appendix.tex:6-9`：新增一句 "Dataset/model labels in the stratified analyses of
Section~\\ref{sec:empirical} come from run directory names, not archived fields (evidence:
\\texttt{pr\\_stats\\_hardened.json, label\\_evidence})."

## c：两处廉价修正

- `paper合/main_springer.tex:3` —— 旧注释 `%% Target: EAAI / NCAA / Cognitive Computation` →
  `%% Springer-format variant of the Neurocomputing submission (NEUCOM-D-26-23760); body shared with main_nc.tex`
- `paper合/main_springer.tex:46` —— `characterise` → `characterize`（与 NC 版及正文一致）

## 页数守恒（NC 79 / Springer 56）—— 全部为排版无损压缩

改动令 NC 一度变 **80 页**（第 80 页仅剩最后一条参考文献）。按"同文件内压缩"处理：

| 位置 | 改动 | 作用 |
|---|---|---|
| `paper合/main_nc.tex:113` | `\\setlength{\\bibsep}{0pt}`（natbib 条目间距） | **唯一定点生效项**，NC 由 80 → 79 |
| `paper合/sections/provenance_appendix.tex:11` | `\\arraystretch` 0.9（34 行长表行距收紧） | 辅助（单独不足） |
| `paper合/sections/provenance_appendix.tex:5` | 附录引言并入 `\\footnotesize` 组（与表同字号） | 辅助（单独不足） |
| `paper合/sections/provenance_appendix.tex:11` | `\\tabcolsep` 4pt → 3pt | 辅助（单独不足） |

## 验证（本机实跑，2026-10-25）

- **构建**：两版各 `pdflatex ×2`，exit 0；`main_nc.log` → **79 pages**，`main_springer.log` → **56 pages**；
  两版均 **0 errors / 0 undefined references / 0 undefined citations / 0 overfull hbox / 0 overfull vbox**。
- **`paper_audit --profile paperA_springer --fail-on NONE`** → `READY  grade A  pass=56 fail=0 warn=0 manual=9 skip=21 error=0`
- **`paper_audit --profile paperA_nc --fail-on NONE`** → `BLOCKED  grade D  pass=66 fail=1 warn=0 manual=9 skip=10 error=0`，
  唯一 blocker **I-02**"package copies differ from live files | regenerate the package after rebuilding the manuscript"：
  该 profile 的 package 是 `SUBMISSION/PaperA_Neurocomputing`，按指示**未刷新**。提交后跑
  `python tools/_p1169_refresh_nc_submission.py`（profile 的 `staged_command`）再复跑即可转绿。
- **`tools/_p1454_final_verify.py`**：页数行 `pages: {... 'paper合/main_nc.pdf': 79,
  'paper合/main_springer.pdf': 56 ...} pass: True`；整体 VERDICT 仍 FAIL，**唯一原因是 `git_clean=False`**
  （未提交 + 其他 agent 并行改动），与页数无关。
- **PDF 文本核验**（两版）：`Predictor` **0** 次、`Statistic` 就位；`characterise` **0** 次；
  "see the Data availability statement in the front matter" **0** 次；"No datum used here is restricted"
  与 "come from run directory names" **两版均有**；两版 "Data availability" 各 **1** 处且逐字相同。

## 未做（按指示）

未提交；未碰 `SUBMISSION/**`、`tools/_p1454_final_verify.py`、其它稿件。
`SUBMISSION/PaperA_Neurocomputing/` 的刷新（I-02 的唯一解法）与 git 提交留给 Lead。
"""

with io.open(PATH, encoding="utf-8") as f:
    current = f.read()
if "Applied fixes" in current:
    print("Applied fixes section already present; not appending twice")
else:
    with io.open(PATH, "a", encoding="utf-8", newline="\n") as f:
        f.write(SECTION)
    print("appended %d chars" % len(SECTION))
with io.open(PATH, encoding="utf-8") as f:
    t = f.read()
print("file now", len(t.splitlines()), "lines;", "Applied fixes" in t)
