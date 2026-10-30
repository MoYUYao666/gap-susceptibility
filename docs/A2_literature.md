# A2 文献清单（全部核验过来源，2026-08-25）

**核验方法**：OpenAlex API（doi/venue/year）+ arXiv 页面 + HF 模型卡/集合 + A1 已审计条目（`docs/A1_literature_check.md`、`paper_a1/main.tex` 13 条，08-15 已逐条联网核实）。**未核实来源的条目一律不写。**

## A. 对齐/间隙理论（复用 A1 已审计 13 条中的核心）

| # | 引用（建议 bibkey）| 完整信息 | A2 用途 | 核验 |
|---|---|---|---|---|
| 1 | liang2022 | V. W. Liang, Y. Zhang, Y. Kwon, S. Yeung, J. Zou, "Mind the Gap: Understanding the Modality Gap in Multi-modal Contrastive Representation Learning," NeurIPS 2022 | 间隙概念源头 | A1 已审计 ✓ |
| 2 | radford2021 | A. Radford et al., "Learning Transferable Visual Models from Natural Language Supervision," ICML 2021 | CLIP/零样本背景 | A1 已审计 ✓ |
| 3 | chowers2026 | I. Chowers, O. Naparstek, "Is the Modality Gap a Bug or a Feature? A Robustness Perspective," CVPR 2026（arXiv:2603.29080）| 差异化：文本侧平移弱效应 vs 我们图像侧偏置场 | A1 已审计+全文已读 ✓ |
| 4 | grassucci2026 | E. Grassucci, L. Cicchetti et al., "Closing the Modality Gap Aligns Group-Wise Semantics," ICLR 2026（arXiv:2601.18525）| 差异化：训练式闭合 vs 平移闭合 | A1 已审计+全文已读 ✓ |
| 5 | wortsman2022 | M. Wortsman et al., "Robust Fine-tuning of Zero-shot Models," CVPR 2022 | 权重空间解耦对应 | A1 已审计 ✓ |
| 6 | levi2025 | D. Levi, G. Gilboa, "The Double-Ellipsoid Geometry of CLIP," ICML 2025 | 嵌入几何结构背景 | A1 已审计 ✓ |
| 7 | yi2025 | L. Yi, R. Douady, C. Chen, "Decipher the Modality Gap in Multimodal Contrastive Learning: From Convergent Representations to Pairwise Alignment," arXiv:2510.03268, 2025；**已有 ICML 2026 正式版（"The Convergent Representation of V-L Contrastive Learning…"）→ revision 时/投稿用正式版** | 收敛表示机制 | A1 已审计 ✓（正式版变更见 HANDOFF）|
| 8 | biderman2024 | D. Biderman, J. Portes, J. J. G. Ortiz, M. Paul et al., "LoRA Learns Less and Forgets Less," NeurIPS 2024（arXiv:2405.09673）| **新增**：PEFT 少遗忘的保留机制——支撑"参数通路限制"解释（PEFT 保护≠σ_m 压平）| 本轮 OpenAlex 确认 arXiv 版 ✓（NeurIPS 2024 为公开记录，若稳妥可仅引 arXiv）|

## B. 海洋/水下视觉语言模型（本轮 OpenAlex/arXiv/HF 核验）

| # | 引用 | 完整信息 | A2 用途 |
|---|---|---|---|
| 9 | aquaticclip2026 | B. Alawode, I. I. Ganapathi, S. Javed, N. Werghi, M. Bennamoun, A. Mahmood, "AquaticCLIP: A Vision-Language Foundation Model and Dataset for Underwater Scene Analysis," **IEEE TNNLS, 2026**, DOI [10.1109/tnnls.2026.3657138](https://doi.org/10.1109/tnnls.2026.3657138)（arXiv:2502.01785, 2025）| 水下 VLM 前沿；**无公开权重**（arXiv 摘要链接为占位符）→ 描述为"代码未公开" |
| 10 | marinegpt2023 | Z. Zheng, J. Zhang, T.-A. Vu, S. Diao et al., "MarineGPT: Unlocking Secrets of 'Ocean' to the Public," arXiv:2310.13596, 2023（[arXiv](https://arxiv.org/abs/2310.13596)，OpenAlex 确认作者与年份 ✓）| 海洋 VLM 例子；无期刊版 → 按预印本引用 |
| 11 | oceanclip2025 | zjunlp, "OceanCLIP-0.15B: Marine Vision-Language Model," HuggingFace model（[zjunlp/OceanCLIP-0.15B](https://huggingface.co/zjunlp/OceanCLIP-0.15B?library=open_clip)），属 [OceanGPT-X collection](https://huggingface.co/collections/zjunlp/oceangpt-x)｜BioCLIP 基座+海洋微调 | **本研究主角模型**；无正式论文 → 引用模型卡+GitHub/HF |
| 12 | oceangpt2023 | Z. Bi, N. Zhang, Y. Xue, Y. Ou et al., "OceanGPT: A Large Language Model for Ocean Science Tasks," NeurIPS 2023（[项目页](https://zjunlp.github.io/project/OceanGPT/)，arXiv:2310.02031；OpenAlex 确认作者 ✓）| 海洋 LLM 背景（zjunlp 海洋主线）|
| 13 | waterbench2025 | ayushprd, "WaterBench," HuggingFace dataset（[HF](https://huggingface.co/datasets/ayushprd/WaterBench)）| 可选：水下能力基准（无论文 → 按数据集引用；A2 正文可不引，留作 future work 提及）|

## C. 自身工作（双盲注意 ⚠️）

| # | 引用 | 状态 | 使用策略 |
|---|---|---|---|
| 14 | a1 | H. Wan, "A Decoupled View of Class-Ordering and Classification Robustness…"（A1 题名以投稿版为准），Pattern Recognition Letters，**in review**（PRLETTERS-D-26-01941）| **理论母本**——A2 的 Theorem 1–5 与 λ 手术协议全部来自 A1。双盲：投稿时按期刊惯例处理在审引用（"X. Author, under review"）；若 A1 已出结果则引正式版 |
| 15 | p1 | H. Wan, "Protect, Don't Perturb…," Pattern Recognition，**in review** | PEFT 保护母本（§6 对照）|

## D. 待定/不建议引用

- **MARINER**（arXiv 2604.08615，ACM MM 2026 基准）——仅命中镜像站/二手链接，**未能在权威源核验**；投稿前用 arXiv 官方站复核后再决定。
- 一切"海洋视觉基础模型综述/水下 VLM"类未经权威源确认的条目——**禁止写入**。

## E. 引用规则（自查清单）

1. 每条必须能在 OpenAlex/arXiv 官方/HF 卡片任一权威源命中；
2. 预印本必须写 arXiv + 年份（除非确认期刊/会议版）；
3. 数据集引用用 HF 链接；模型引用用模型卡；论文引用用 DOI/venue；
4. A1/P1（在审）引用前先向用户确认期刊双盲政策（PRL 允许 "under review" 引用但需匿名化处理）。
