# 文献追踪（D9，2026-08-16）

> 追踪对象：A1 引用中最关键的三个"最新"条目 + 潜在新文献。结论只更新此处与 HANDOFF。

## 1. chowers2026 —— ✅ 已正式出版

- **CVPR 2026 正式版已上线**（openaccess）：[CVF 页面](https://www.openaccess.thecvf.com/content/CVPR2026/html/Chowers_Is_the_Modality_Gap_a_Bug_or_a_Feature_A_CVPR_2026_paper.html)
- 另有 arXiv 版：[arXiv:2603.29080](https://arxiv.org/html/2603.29080v2)（CC BY 4.0）
- 对 A1 的影响：bib 条目 "CVPR 2026" 正确；可选在 revision 中补 arXiv 号 2603.29080。差异化定位（我们统一其"文本侧弱效应"）不变。

## 2. cai2026 —— ✅ ICML 2026 确认

- [ICML 2026 poster 页面](https://icml.cc/virtual/2026/poster/63447) 确认收录 "The Geometric Mechanics of Contrastive Representation Learning: Alignment Potentials, Entropic Dispersion, and Cross-Modal Divergence"
- arXiv 版疑似 [arXiv:2601.19595](https://arxiv.org/list/cs.LG/2026-01?skip=1175&show=2000)（2026-01 列表出现同标题）
- 对 A1 的影响：bib "ICML 2026" 正确；可补 arXiv 号。

## 3. yi2025 —— ⚠️ 有 ICML 2026 改名版

- 原引用 arXiv:2510.03268（2025）"Decipher the Modality Gap in Multimodal Contrastive Learning: From Convergent Representations to Pairwise Alignment"（[Semantic Scholar](https://www.semanticscholar.org/paper/Decipher-the-Modality-Gap-in-Multimodal-Contrastive-Yi-Douady/235e284a00b853bdef085824a65ddc815507586b) / [ADS](https://ui.adsabs.harvard.edu/abs/2025arXiv251003268Y/abstract)）确认存在。
- **同名工作 ICML 2026 版**：[poster 66630](https://icml.cc/virtual/2026/poster/66630) "The Convergent Representation of Vision-Language Contrastive Learning: Geometry, Modality Gap and Shared Space Alignment"（另有 paperreading 标题变体 "Decrypt Modality Gap…From Convergent Representation to Pair Alignment"）。
- 对 A1/Paper 3 的影响：现 bib（arXiv:2510.03268, 2025）可保留；revision 时优先改为 ICML 2026 正式版条目并核对作者列表。**注意**：Paper 3 的 references.bib 变体错版问题（已记 HANDOFF）在改这条时一并处理。

## 4. 潜在新文献信号

- ICML 2026 上"modality gap / convergent representation"主题出现多篇（cai2026、yi 版、poster 66630），说明该方向热度上升——A1 的"任务特异性"定位仍是差异点，但扩展版写作前应再扫一次 ICML 2026 收录列表确认无撞题。

## 5. 各论文 bib 影响映射（D9 → 哪篇补什么）

| 论文 | 引用情况（grep 核实） | revision 时动作 |
|---|---|---|
| **A1**（PRL 已投） | yi2025（arXiv 版 ✓）、cai2026（ICML 2026 ✓）、chowers2026（CVPR 2026 ✓） | 可选：yi2025 升级为 ICML 2026 正式版（新题名）；chowers2026 补 arXiv:2603.29080；cai2026 补 arXiv:2601.19595。**投稿版不用动**。 |
| **Paper 3**（TNNLS 在审） | `paper_ieee/references.bib` 的 yi2025 条目是**变体错版（必须修）** | 修错版 + 直接改成 ICML 2026 正式版条目（一石二鸟）；另 `paper3/paper/` 与 `paper3/paper_ICLR_backup/` 同 key 条目需一并核对（非投稿版，低优先）。 |
| **Paper 1**（PR 在审） | `yi2025decipher`（arXiv 版条目正确） | 可选升级 ICML 2026；**注意**：正文把 yi 归因为"dimension collapse 是根因"——升级前须复核 ICML 版内容是否保留该结论（改名可能伴随内容修订）。 |
| **Paper 2 / Paper A** | 同 Paper 1（条目正确） | 同上，可选升级 + 归因复核。 |
| 共同 | cai2026geometric（P1/P2/PaperA）、cai2026（A1） | 条目已正确（ICML 2026）；补 arXiv:2601.19595 纯锦上添花，非必需。 |

## 6. 下一步（随缘）

- 等 PRL 意见回来前再查一轮 "order preservation + zero-shot + modality gap" 关键词；
- 若扩展版动笔，先读 ICML 2026 改名版 yi 全文，确认与 arXiv 版差异与作者列表。

## 7. 新增追踪：Karniadakis 组 Nature Communications 时序架构选择（2026-08-22 加入）

- **题名**：Automatic selection of the best neural architecture for time series forecasting
- **期刊**：*Nature Communications*（2026 年第 17 卷；发表日 2026-06-02）
- **DOI**：10.1038/s41467-026-73687-9 ｜ [原文链接](https://www.nature.com/articles/s41467-026-73687-9)
- **作者**：Qianying Cao, Shanqing Liu, Alan John Varghese, Jérôme Darbon, Michael S. Triantafyllou, George Em Karniadakis（Brown University；MIT）
- **预印本**：arXiv:2501.12215（v1 题名为 "…via multi-objective optimization and Pareto optimality conditions"，[ar5iv](https://ar5iv.labs.arxiv.org/html/2501.12215)）——正式版标题有改动，引用以 NC 版为准。
- **与本项目关系**：暂与 A1/P1/P3 无直接引用关系（纯时序建模方向，非多模态对比学习）；作为科研动态记录（Karniadakis 组对 AutoML/架构选择的向量化多目标方法），若后续涉及时序任务或方法学对比可回查。
