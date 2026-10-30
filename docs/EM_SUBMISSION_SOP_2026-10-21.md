# EM 投稿标准流程（SOP，2026-10-21 固定）

> 适用：所有 Elsevier Editorial Manager（EM）投稿/改投。目的：把每次投稿变成**可重复的 10 步流程**，避免
> 文件名、摘要、关键词、Contributor roles 等手工字段出错。P3 改投为第一个按此流程执行的稿件。

## 0. 前置产物（投稿前必须齐）

1. **投稿包**：`SUBMISSION/<Pkg>/`，文件名为
   `Manuscript.pdf`、`Supplementary.pdf`、`CoverLetter.pdf`、`TitlePage.pdf`、`Abstract.pdf`、
   `Highlights.pdf`、`LaTeXSource.zip`（**一律无下划线**，项目规则 2026-10-21）。
2. **EM 字段文件**：`SUBMISSION/<Pkg>/EM_FIELDS.md`（title / abstract 纯文本 / keywords / CRediT roles /
   declarations / 前稿号披露），由本 SOP 第 1 步生成。
3. **门禁**：`paper_audit` 对应 profile 无新 failure；`audit_check`/`audit_pdf` 0 hard（适用时）；
   staged 包检查 1:1；页数/摘要词数符合期刊上限。

## 1. 生成 EM 字段（从稿件抽取，不手打）

- Title：与 PDF 标题页逐字一致（含副标题）。
- Abstract：**纯文本版**（LaTeX 数学转写规则：`$\Gamma_k$`→`Gamma_k`，`$\nabla$`→`grad`，
  `$\propto$`→`proportional to`，`$\in$`→`in`，`---`→`---` 保留）；词数 ≤ 期刊上限（PRL 250~300，按 EM 显示）。
- Keywords：`; ` 分隔，数量按期刊要求（P3 为 5 个）；**不要出现 `,;` 这类重复分隔符**。
- CRediT Contributor roles：见第 4 步模板。
- Declarations：competing interests / funding / data availability / generative-AI，均从稿件正文复制。

## 2. EM 起点

- 登录 EM → **Submit New Manuscript**（改投稿件也走这个入口，不是 Revise）。
- 若 EM 问 "Has this manuscript been submitted before?" → **Yes**，填前稿号（P3：`PRLETTERS-D-26-02378R1`）。

## 3. Article type / 分类

- Article type：按期刊下拉选最接近的（PRL：Research Paper / Full-length article）。
- Subject classifications：优先选 **Machine learning / Computer vision / Pattern recognition** 系；最多选 3 个。

## 4. Contributor roles（CRediT）填写模板

**单作者稿件（本项目全部五篇均为单作者）**勾选以下 11 项：

```
Conceptualization
Data curation
Formal analysis
Investigation
Methodology
Project administration
Software
Validation
Visualization
Writing – original draft
Writing – review & editing
```

**不勾选**：Funding acquisition（无资助）、Supervision（无导师/合作者）、Resources（无独立资源贡献）。
若期刊强制要求至少一个"Supervision"，再补 Supervision 并在说明栏注明"sole author"。

## 5. 文件上传（File type 对照）

| 文件 | File type |
|---|---|
| `Manuscript.pdf` | Manuscript（必填项，先传）|
| `Highlights.pdf` | Highlights（若独立项）|
| `Supplementary.pdf` | Supplementary material |
| `CoverLetter.pdf` | Cover letter |
| `TitlePage.pdf` | Title page（无此类型时用 Cover letter 或留到必填前置项）|
| `LaTeXSource.zip` | LaTeX source files |
| `Abstract.pdf`（如有）| Abstract |
| 不传 | Graphical abstract（无）、Figure（图已嵌入）、Macro/style（模板由系统提供）、Audio/Video |

上传顺序：**Manuscript → Supplementary → CoverLetter → TitlePage → Highlights → LaTeXSource**。
上传后在文件排序里复核上述顺序。

## 6. 生成 PDF 复核（最关键）

- 打开 EM 合并生成的审稿 PDF，检查：
  1. 标题/摘要/关键词与 PDF 一致；
  2. 正文在前、补充材料在后；
  3. 封面信/标题页没有插到正文之前（以 EM 的 item 顺序为准）；
  4. 图、表、公式、参考文献完整；
  5. 有 `[?]`、空页、乱码 → 回退修文件。

## 7. 提交前最后一屏

- 逐项确认作者、单位、通讯作者、ORCID；
- 确认 cover letter 已包含前稿披露（改投稿件）；
- 点 **Approve Submission** 后保存 **新稿号 + 提交时间 + 摘要词数 + 包名**。

## 8. 提交后落账（强制）

- `HANDOFF.md` 顶部追加条目：期刊、新稿号、提交时间、状态、包路径、页数；
- `文件地图.md` 加一行；
- `SUBMISSION/README.md` 更新该包状态（已投/在审）；
- 若 24 h 内没有确认邮件，检查 EM 状态并记录。

## 9. 被拒/改投时的处理（P3 已执行一次）

- 原包整体移入 `SUBMISSION/_archive/<Pkg>_rejected_<date>/`（**哈希校验后移动**），附
  `DECISION_REJECTED_<date>.md`；
- 修复/加固后的新包放回 `SUBMISSION/<Pkg>_resubmission/`；
- 更新 `SUBMISSION/README.md` 索引；
- 决定记录同步进 `HANDOFF.md` / `文件地图.md` / 相关 `docs/*.md`。

## 10. 复用检查表（每次投稿逐项打勾）

- [ ] 包内文件名无下划线
- [ ] 标题/摘要/关键词与 PDF 一致，摘要纯文本、词数达标
- [ ] CRediT 11 项（单作者）
- [ ] 前稿披露（改投）
- [ ] 文件类型/顺序正确
- [ ] 合并 PDF 复核通过
- [ ] 新稿号已落账
