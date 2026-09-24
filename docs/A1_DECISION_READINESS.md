# A1 决策就绪清单（PRL / Pattern Recognition Letters, PRLETTERS-D-26-01941）

**状态**：**REJECTED（2026-09-14）**——AE 建议拒稿（六条理由，见 HANDOFF 同日条目）；投稿 2026-08-16，技术检查两轮 08-18/19/20 完成。**下一步见本文 §3（换刊决策）与 HANDOFF 的转投计划。**
**题名**：*The Modality Gap Is Not a Universal Health Metric: Order Preservation Governs Zero-Shot Robustness*
**投稿包**：`paper_a1/`（main.pdf 7 页；Highlights 5 条；Declaration 含生成式 AI 声明；`Figure_1..4.png` 300dpi；竖版 graphical abstract）

> 本文件的目的：Decision in Process 是"出结果前最后一站"，收到决定信后 24 小时内即可按下面分支执行，不必临时梳理。

## 0. 决定信到达当天（无论何种结果）

1. 把决定信原文存 `paper_a1/decision_<date>.txt`，并在 `HANDOFF.md` 顶部速览与文末条目记录（含日期、决定类型、审稿人数量、返修期限）。
2. `git -C . log --oneline -1` 记录当前归档点；确认 `paper_a1/` 与 GitHub `origin/main` 一致（`paper_a1` 目录不在发布仓库时，改为记录本地 zip 快照名）。
3. 对照下表确定分支，并预估工作量。

| 决定 | 概率性提示 | 首要动作 | 典型期限 |
|---|---|---|---|
| Accept | DIP 后直接接收不常见，但 PRL 有"accept as is / minor editorial" | 校样（proof）+ 在线发布 + 更新互引 | 校样 48–72 h 内回 |
| Minor revision | 常见 | 直接在本地修复版上做小改 + 回复信 | 30 天 |
| Major revision | 可能 | 全量重跑/补实验 + 回复信 | 60 天（Elsevier 常见） |
| Reject（含 transfer 建议） | 可能 | 见 §3 换刊决策 | — |

## 1. 若需返修（Minor/Major）

**基线选择**：以**本地 `paper_a1/` 为基线**；注意**本地正文与投稿正文一致**（见下），返修时直接在本地 `main.tex` 上改，已投稿 PDF 仅用于校样比对。**本地 vs 投稿版的真实差异（2026-09-13 按文件 mtime 与投稿日 08-16 逐项核实）**：
- **正文与主图完全未改**：`main.tex`（08-15 12:08）与 `figures/fig1_lambda`–`fig4_spectrum` 均早于投稿日 → **本地正文 ≡ 投稿正文**；`main.pdf`/`main_zh.pdf`（08-16 22:06）只是同一源码的重编译。故"本地修复版"一说对 A1 不准确：凡图序/计数一类的核对修改都发生在投稿日之前，属**投稿版的一部分**；
- **投稿后本地新增的返修素材（尚未并入正文）**：`revision_additions.tex`（09-12）——8 块 = ①逐点预测 τ(λ)（9 个 λ 误差 ≤0.002，无拟合）②Qwen2-VL 解码器式跨架构（文本侧 τ≡1.000）③5 seeds 稳健（τ 0.9167±0.0064、偏置场 Pearson 恒 1.0000）④训练期类别对齐剂量-响应（top-1 58.1%→54.4%、τ 0.711→0.611 而验证损失改善）⑤DINOv2 阴性对照（τ 全 λ>0.93）⑥τ 为最早侵蚀信号（逐 epoch）⑦纯 LoRA 协议披露 ⑧跨族留出泛化（R² 0.371/0.378、Spearman 0.927, p=1.4e−12）+ 3 条 rebuttal 问答模板；`figures/figT1`–`figT6`（6 张补充图，08-23）；支撑数据 `outputs/a1_*.json` 与溯源表 `docs/A1_NUMBERS_PROVENANCE.md`；每块的建议落点与可直接粘贴的正文句子写在 `revision_additions.tex` 的注释里；
- **投稿流程文件**（非论文内容）：`Authorship Confirmation submit.pdf`、`PRLETTERS-D-26-01941.pdf`（编辑部返回的投稿件）、`authorship_form_fill_guide.md`、`archive/`；⚠️ **一处待确认**：`figures/graphical_abstract.png` 于 **08-22** 被改动（晚于投稿日）→ 返修或转投前先确认公开版用哪一版。**更正（2026-09-13）**：本行此前列的是「fig5 → Route E、fig8 补 Full FT 柱、fig13 删 R@1 面板」等条目 —— 那是 **P1/P3 的图修复清单**，与 A1 无关（A1 只有图 1–4 与补充图 T1–T6，不存在 fig5/fig8/fig13），已删除并替换为上面按 mtime 核实过的真实差异。

- **已清理的历史问题（保留备查）**：幻影引用类问题在 A1 已清理（"The constancy assumption (A1)" 等）；图表编号与正文图序一致（哈希 9446B517/3DDF15FF 对齐）、5k/50k 抽样口径披露、τ 声称加"非类对齐扰动"限定、fig1 图注——这些修改均发生在**投稿日之前**，因此已包含在投稿版中，返修时无需重做，但若审稿人问及可作为"已核对"的证据。

**执行顺序**：
1. `cd paper_a1 && pdflatex → bibtex → pdflatex ×2`，跑 0 error / 0 undefined / Overfull 检查；
2. 逐条把审稿意见转成 TODO（按 [must / should / rebut] 三档分类），must 项先做；
3. 每条意见写 point-by-point：**引用修改后的页码/行号 + 原文摘录**，未采纳的给出技术理由；
4. 若审稿人质疑"排序保持 vs 鲁棒性"的因果性：可用 `outputs/a1_*.json`（Kendall τ 强耦合、类偏置场 r=1.000）与 `docs/A1_literature_check.md` 的差异化段落回应；
5. 回传前重跑一次 `tools/clip_a1_*.py` 的复算脚本，确认正文数字与 JSON 一致；
6. 更新 `HANDOFF.md`（决定类型、返修项、版本号）。

## 2. 若中稿（Accept）

1. 校样阶段核对：作者信息（Hongrui Wan / hw4c24@soton.ac.uk / University of Southampton）、基金、AI 声明、图分辨率；
2. **互引更新**：
   - `paper_ap3/`（Neurocomputing 目标，单盲）：把 "the companion study" 匿名指代升级为正式引用；Related Work 增加一句分工定位（A1：排序保持支配零样本鲁棒性；本文：Γ 的表示定理 + 分配律 + 相变）；cover letter 增加 A1 关系披露；
   - `paper_a2/`（海洋/声呐合并稿）：在"跨模态对齐健康度"叙事处引用 A1；
3. arXiv/ORCID/Google Scholar 同步（若挂 arXiv，注意 Elsevier 的 preprint 政策允许）；
4. 更新 `HANDOFF.md` 顶部速览：A1 = Published（DOI 待补）。

## 3. 若被拒（含 transfer）

**先判断拒稿类型**：
- **技术性拒稿（审稿人质疑核心结论）** → 需要补实验，见下"可选补强"；
- **范围/新颖性拒稿（"更适合 XX 刊"）** → 走转投，无需改结论。

**换刊候选（按契合度）**：
| 候选 | 理由 | 风险 |
|---|---|---|
| Elsevier 转投（Pattern Recognition / Neurocomputing / Displays） | 流程最省事，编辑已熟悉 | 与 `paper_ap3` 同家族，需披露重叠（一短一长，不构成重复投稿） |
| IEEE Signal Processing Letters | 7–8 页短稿契合、周期快 | 需转 IEEE 模板 |
| CVPR/ICCV workshop 或 Tiny Papers | 快速获得反馈与引用 | 非正式发表 |

**关键取舍：是否与 `paper_ap3` 合并？**
- 合并的好处：把"排序保持 → 鲁棒性"作为现有 Γ 排序叙事的**下游应用**一章，强化 paper_ap3 的完整性；
- 合并的代价：paper_ap3 已 73 页、目标刊页数压力大；且 A1 的独立贡献（类偏置场 r=1.000、逐类预测）会被压缩；
- **建议**：除非 A1 被两轮以上技术性拒稿，否则优先"换刊重投 + 互引"，保持两篇独立；仅在 A1 第三次被拒时再考虑合并。

**可选补强（若审稿人要求更强因果证据）**：
- 图像侧/文本侧非对称扰动已有（"移图像侧触发逐类偏置场崩塌"）；
- 可补：多数据集（ImageNet/DTD/Food101 已在 A1 内）之外的**跨架构**复现（SigLIP/BLIP-2，脚本 `tools/clip_a1_crossmodel.py` 现成）；
- 可补：**类级排序保持**的置信区间（bootstrap over classes，复用 `tools/clip_clustered_bootstrap.py` 的写法）。

## 4. 与 `paper_ap3` 的合规检查（投稿前必做）

- [ ] `paper_ap3` cover letter 明确披露 **A1（PRL, Elsevier）** 与 **P1（PR, Elsevier, 仍在审）** 的存在与关系（P1 未被拒；`paper_ap3` 是按合并方案预先备好的应急稿，投递时机取决于 P1 结果：**P1 若中稿 → 合并方案作废、PA 归档**）；
- [ ] 若 A1 已发表，`paper_ap3` 正文引用其 DOI，并在 Related Work 写明分工；
- [ ] 若 A1 仍在审，`paper_ap3` 不得复述 A1 的结论性表述（避免自我重复投稿），只作方法论关联；
- [ ] `paper_ap3` 与 `paper_a2` 之间的重叠（都含"对齐健康度/Γ"叙事）同样在各自 cover letter 披露。
