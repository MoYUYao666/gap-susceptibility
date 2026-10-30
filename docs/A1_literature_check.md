# A1 文献排查备忘录（2026-08-15 更新：三篇全文已读，差异化定稿）

## 一、三篇全文读后结论（关键！）

### Chowers et al., CVPR 2026 "Bug or a Feature?" —— 撞车程度：方法级，但结论互补
- **他们做的**：平移 **文本** 嵌入（α·g⃗，Figure 2 caption 原文 "moving the text embeddings by α·g⃗"）调整 gap，发现下游性能变化**不一致/微弱**（zero-shot ImageNet 甚至受益于轻微拉大 gap）；真正贡献=gap 与**鲁棒性**（扰动下输出翻转概率）单调相关，提出 gap 闭合作为鲁棒性后处理。
- **我们的关系**：我们移**图像**侧（崩塌 59.3→32.0），他们移**文本**侧（微弱）。**我们的非对称性实验正是统一两者的理论**：移图像→逐类偏置场 λ‖g‖m_c（破坏排序）；移文本→逐图项 δ·x（跨图零均值，良性）。他们的"微弱/不一致"= 文本侧的弱效应；我们的"崩塌"= 图像侧的强效应。**差异化定位：我们是机制统一者（偏置场解释两侧）+ τ 监控量 + 任务谱系 + 训练期轨迹。**
- 必引必差分。正文加一句话点破："our asymmetry also reconciles Chowers et al.'s observation that text-side shifts leave accuracy largely unchanged"。

### Grassucci et al., ICLR 2026 "Closing the Gap Aligns Group-Wise Semantics"
- **他们**：gap 对 **instance-wise 任务（retrieval，基于相对排序）无关紧要**、对 **group-wise 任务（clustering，基于绝对距离）影响显著**；方法=训练式闭合（保持结构）。
- **我们的关系**：他们的"相对排序 vs 绝对距离"二分正是我们的机理语言；但他们把 **zero-shot 归入"instance-wise→gap 不敏感"**，而我们的手术证明 **zero-shot 的排序本身可被偏置场摧毁**（图像侧平移）。→ 我们的谱系更细：NCC < zero-shot < retrieval 三者都在"instance-wise"内部。他们的闭合是结构保持的训练式 → 与"如何闭合才重要"完全一致。
- 必引必差分：一句"while training-based closing leaves instance-wise tasks unaffected (Grassucci), we show naive global closing (image-side translation) destroys zero-shot ordering via a bias field"。

### Wortsman et al., CVPR 2022 WiSE-FT —— 无撞车，纯引用
- 权重插值保留 zero-shot+fine-tuned 双精度 = 解耦的权重空间版。引用+定位即可。

## 二、最终差异化三句话（已写入正文）
1. 我们反对的不是 gap 闭合方法，而是"gap 大小=通用健康指标"；
2. 移哪一侧、怎么移，决定后果——图像侧平移的偏置场才是破坏源（r=1.000 验证）；
3. τ 是分类族的正确监控量（26 条件 Spearman 0.926；CG −0.082 无信息）。

## 一、最接近的先验工作（必须差异化）

| 论文 | 内容 | 与 A1 的关系 | 策略 |
|---|---|---|---|
| **Chowers & Naparstek, "Is the Modality Gap a Bug or a Feature? A Robustness Perspective", CVPR 2026**（arXiv:2603.29080） | 从鲁棒性（对抗/OOD）角度问 gap 是好事还是坏事 | **最接近的立意**（bug-or-feature 问法） | **投稿前必读全文**；A1 的差异化 = ① 控制实验（gap surgery 精确平移）vs 他们的相关性/鲁棒性视角；② 机制（类偏置场，r=1.000 验证）；③ τ 作为可操作监控量 + 任务谱系。Intro 主动引用并定位"互补" |
| **Grassucci, Cicchetti et al., "Closing the Modality Gap Aligns Group-Wise Semantics", ICLR 2026**（arXiv:2601.18525） | 关闭 gap 对 group-wise 语义对齐有益 | 与我们"平移闭合 gap 反而破坏分类"**表面冲突** | **必须精确区分**：他们用训练式对齐（保持结构）闭合 gap；我们用全局平移（破坏结构）闭合 gap——"如何闭合"才是关键，两者互补而非矛盾。正文明确写这一点，防止审稿人误判 |
| **Wortsman et al., "Robust Fine-tuning of Zero-shot Models" (WiSE-FT), CVPR 2022**（arXiv:2109.01903） | 零样本/微调模型权重插值同时保住两种精度 | 同一解耦现象在**权重空间**的体现 | 引用 + 定位："我们的 τ 给出该现象在嵌入几何层面的解释" |

## 二、必须引用的方法线（gap 关闭/对齐方法）

| 论文 | 定位 |
|---|---|
| Mistretta et al., "Cross the Gap", ICLR 2025（arXiv:2502.04263） | 模态反转暴露 CLIP 模态内失配（Paper 1 bib 已有 mistretta2025cross） |
| Yamaguchi et al., "Post-Pre-training for Modality Alignment in VL Foundation Models", CVPR 2025（arXiv:2504.12717） | 后预训练模态对齐（Paper 1 bib 已有 yamaguchi2025cliprefine） |
| Sofer et al., "Pull It Together: Reducing the Modality Gap in Contrastive Learning", Interspeech 2025 | 对比学习中的 gap 缩减方法（作者全名待查，引用用 "Sofer et al."） |

## 三、风险项（防审稿人"撞车"质疑的预案）

1. **与 Chowers 2026 的撞车风险**：若其核心主张也是"gap 对分类无关紧要"，则 A1 的贡献重心要往**机制 + τ 监控量**倾斜（我们的手术验证 r=1.000、文本/图像非对称性、训练期 τ 轨迹都是他们没有的）。投稿前通读该文并视需要重写 Intro 定位段。
2. **"缩小 gap=变好" 的朴素主张**（grassucci2026/yamaguchi2025 的语境）：A1 正文需显式写出"我们反对的不是 gap 对齐方法本身，而是把 gap 大小当通用健康指标；结构保持的闭合（训练式）与结构破坏的闭合（平移）效果相反"——避免被读成攻击这些工作。
3. **WiSE-FT 的权重插值现象**：审稿人可能说"这已知"——回应：已知的是权重空间解耦，我们给出的是嵌入几何机制（偏置场）与可部署监控量（τ），并拓展到三模型家族与训练期动态。

## 四、结论

- 不存在"完全同题"的已发表工作（gap surgery + τ + 偏置场机制这套组合未见）；最需小心的是 Chowers 2026 与 Grassucci 2026。
- 下一步行动：① 通读 Chowers 2026 全文（arXiv:2603.29080）并写一页差异化笔记；② 论文 Related Work 已补 6 条引用 + Intro 定位段（已完成，见 paper_a1/main.tex v0.3）。
