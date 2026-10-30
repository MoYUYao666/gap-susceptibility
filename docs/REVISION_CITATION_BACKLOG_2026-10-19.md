# 修回引用补录 · 2026-10-19（全部已写入本地工作副本，提交包保持冻结）

**背景**：`docs/reviews/WEEKLY_LIT_2026-10-19.md` 的检索发现需要补引的工作。按"**已投稿件不得改动**"的冻结纪律，
所有修改只进**本地工作副本**；`SUBMISSION/` 下的投稿包（A1 PAA、Paper A Neurocomputing、P3 PRL R1）**一字未动**。
这些修改在收到审稿意见、进入修回轮时直接可用。

**脚本**：`tools/_p1326_add_revision_citations.py`（幂等，带断言；`--apply` 才写盘）。

## 一、A1（`paper_a1/`）

| 项 | 内容 |
|---|---|
| 新增引用 | **Sharma & Saxena 2026**（[arXiv:2609.36101](https://arxiv.org/abs/2609.36101)，"One Geometry, Different Outcomes"，秩一 + readout 三角色）与 **Yaras et al. 2024**（[arXiv:2412.07909](https://arxiv.org/abs/2412.07909)，gap 的梯度流理论）|
| 位置 | `related_work.tex` §"Representation drift and modality-gap geometry under fine-tuning"：新增一段（几何解释 vs 统计充分性/下界的区分）；`main.tex` 参考文献末尾追加 2 条 `\bibitem` |
| 区分要点 | 他们的贡献是**几何**（gap 在分数里的哪个成分起作用）；本稿是**统计充分性**（一阶矩无法决定行序）+ **margin 质量下界** + 标签无关证书；并指出只有充分性陈述能解释"匹配 gap 仍能藏几十个点" |
| 编译 | `main.tex` 三遍：**59 页**（原 58）、0 错误、0 未定义、0 Overfull |
| 台账 | A1 claim ledger **157/157**（数字未变）|

## 二、Paper A（`paper合/`）

| 项 | 内容 |
|---|---|
| bib 升级 | `amblard2025fill` 由 arXiv 预印本升级为**期刊正式版**：*Int. J. Multimedia Information Retrieval*, **15**(4), 2026, DOI **10.1007/s13735-026-00423-w**（Crossref 已核）|
| 新增引用 | Hu et al. 2026（[arXiv:2609.37888](https://arxiv.org/abs/2609.37888)，CLIP 文本权重受 gap 影响、视觉分支更优）与 He et al. 2026（[arXiv:2609.36759](https://arxiv.org/abs/2609.36759)，双模式低秩 + 原型桥补 gap）|
| 位置 | `sections/related_work.tex` gap 小节末尾加一段；`references.bib` 追加 2 条 |
| 编译 | `main_nc.tex` **70 页**、`main_springer.tex` **50 页**；均 0 错误 / 0 未定义 / 0 Overfull（bibtex 已重跑）|
| 台账 | Paper A 台账 **76/76**、主台账 **96/96** |

## 三、P3（`paper3/paper_ieee/`）

| 项 | 内容 |
|---|---|
| 新增引用 | **IFCLoRA**（[arXiv:2607.22251](https://arxiv.org/abs/2607.22251)，训练前零搜索分配）、**StatLoRA**（[arXiv:2607.20205](https://arxiv.org/abs/2607.20205)，假设检验 + 优化器 CLT）、**LoRA-GA²**（[arXiv:2608.19800](https://arxiv.org/abs/2608.19800)，多步梯度对齐）|
| 位置 | `sections/related_work.tex` §"PEFT Rank Allocation"：新增一段区分（IFCLoRA 最接近——也训练前分配，但需**校准集 + 图构造**；本稿为**闭式、无需搜索/校准/目标模型梯度**）|
| 编译 | `main.tex` 10 页，0 错误 / 0 未定义 / 0 Overfull（bibtex 已重跑）|
| 稿件检查 | `audit_check.py` **0 hard failure / 0 warning**；`audit_pdf.py` **0/0** |

## 四、冻结与审计说明

- `SUBMISSION/A1_PatternAnalysisApplications/`、`SUBMISSION/PaperA_Neurocomputing/`、`SUBMISSION/P3_PRL_revision/`
  **仍为投出时的版本**（A1 包仍 58 页；P3 R1 哈希未变）。
- 因此 `paper_audit --profile a1_paa` 会出现**两条预期内的差异**：`I-02`（包内 Manuscript 58 页 ≠ 本地 59 页）与
  `I-06`（包 README 记 58 页）；`A-01`（工作区未提交）在提交后消除。**这不是缺陷，是冻结提交包的应有状态**；
  A1 修回时若要重新出包，再重建即可。
- Paper A / P3 的包同理：修回时用本地最新稿重建，再替换。

## 五、修回轮待办（引用以外）

1. A1：若审稿人问到"另一篇 2026 的 readout 工作"，引用与区分段已就绪。
2. Paper A：Amblard 期刊版已在 bib；CLIP-CIL 两条仅作背景，不改变主张。
3. P3：IFCLoRA/StatLoRA/LoRA-GA² 的区分段已就位；**R1 在审期间仍不得上传替换件**（编辑部 2026-10-18 明确）。
