# A1 审稿意见逐条应对计划（PRLETTERS-D-26-01941，2026-09-14 拒稿）

审稿人原文要点：R1 六条（另有一次 "Initial submission, September 1" 记录）、R2 五条。总评：问题有趣但"理论过度简化、度量配置武断、实验面窄"。

**先说结论**：11 条里 **6 条靠写作与已有数据就能解决**、**3 条需要本地跑新实验（不需要云端）**、**2 条要求我们主动收窄主张**。我方最危险的攻击点是 R1.3（"τ 与准确率的关系部分是定义使然"）与 R2.5（"相关系数恰好 1.0 很可疑"）—— 这两条必须正面回应，不能绕。

---

## R1（Reviewer 1）

| # | 意见 | 我们已有 | 要做的事 | 成本 |
|---|---|---|---|---|
| **1.1** | 论文说"模态差被广泛当作通用指标"，但所引文献主要研究对齐/检索，缺少"前作确实主张 gap 小 ⇒ zero-shot 好"的证据 | 现有引文；`docs/A1_literature_check.md` | **二选一**：(a) 补引真正做该主张的工作；(b) **改用更弱且更准确的措辞** —— "gap 被广泛用作表示健康度的诊断量（多用于检索/对齐），并常被隐含读作质量代理"。推荐 (b) 为主 + 少量补引 | 低（写作） |
| **1.2** | Related Work 太短（仅一段），缺 zero-shot robustness / 微调后表示漂移 / VLM 灾难性遗忘 / 排序稳定性 / 校准 / prompt 敏感性 / 替代相似度度量 | 无 | **把 Related Work 从 1 段扩成正式小节**，按上述 7 个主题各 1 段，并写明"我们与它们的区别" | 中（写作 + 查文献） |
| **1.3** | **"τ 与准确率的关系部分是定义使然"**（zero-shot 取决于 image–class 相似度排序，而 τ 正测排序变化） | 见下"关键反驳"合集 | 正面回应 + 措辞收窄 | 中（写作） |
| **1.4** | **自家结果自相矛盾**：Gaussian τ=0.761→58.8%，类收缩 τ=0.615→78.6%（τ 更低却准确率更高）→ τ 显然不足以解释 zero-shot | 该两行数据本就在我们的表里（诚实呈现） | **承认并收窄**："τ 是*破坏方向*上的必要代理；跨机制的充分性不成立。" 加一段把两类干预分开（平移族 vs 向真类收缩），并指出收缩是改变 argmax 而不同时保持排序的另一机制 | 中（写作） |
| **1.5** | 全局平移 ≠ 真实微调（局部几何、类结构都会变） | **块 4**（训练期类别对齐剂量-响应）、**块 6/7**（真实 LoRA 微调轨迹：τ 最早侵蚀、top-1 惰性）、`train_class_aligned.py` 严格 LoRA-only | 把这三块从"补充"提到**正文主证据**；正在跑的补种子给出误差棒 | 已在进行 |
| **1.6** | 只 5 个检查点且全在 Flickr30k 微调 → 不足以支撑"通用监控指标"的推荐 | 块 3（5 seed）、块 8（跨族 28 条件：CLIP/OpenCLIP/SigLIP） | **① 收窄"通用"措辞**；**② 新增在不同数据上微调的检查点**（本机 data/ 已有 DTD、Food-101、iNat、rare-species 等，可在本地跑 LoRA 微调 → 检验 τ–准确率关系是否跨数据集成立） | 中高（本地 GPU） |

## R2（Reviewer 2）

| # | 意见 | 我们已有 | 要做的事 | 成本 |
|---|---|---|---|---|
| **2.1** | 一阶近似假设小扰动，但实验扰动尺度≈gap 本身 → 必须解释为何忽略高阶项仍成立 | **块 1 的配对反转条件是精确的**（非一阶）：`pair (i,j) 反转 ⟺ λ‖g‖(m_j−m_i) > d_ij` | **明写"这不是一阶近似"**：反转判据对任意 λ 精确（给定冻结 margin），一阶展开只用在文本侧/逐类常数的讨论；高阶项只通过"冻结量本身的变化"进入 | 低（写作，杀伤力大） |
| **2.2** | top-5 的选择缺论证 → 需要 **top-k 消融** | 现有 τ 计算即基于 frozen top-5 sets | **跑 top-k 消融**（k ∈ {1,3,5,10,20,50,100}）：τ–准确率相关性与 λ 曲线是否稳定 → 做成一张表 | 中（本地，纯评测） |
| **2.3** | 仅 ImageNet + Flickr30k → 需更多 zero-shot 分类基准与细粒度数据集 | `data/` 已有 dtd / food-101 / inat_wild / rare-species / marinelife16k / NKSID | **加 3–4 个 zero-shot 基准**（含细粒度）：冻结/平移/收缩三种条件下的 top-1 与 τ → 检验主张的跨数据集稳定性 | 中高（本地，纯评测） |
| **2.4** | 需引用 3 篇 compositional zero-shot 工作（Concept-Aware GCN / Semi-Negative Contrastive Subclass Discriminative / Multi-Level Contextual Prototype Modulation） | 无 | 查证并补引 + 一句 contextualize | 低 |
| **2.5** | **"相关系数恰好 1.0"很可疑** → 需散点图、置信区间、误差分析，证明不是同义反复/样本方差 | 已有 max_abs_diff **0.0019**、mean_abs_diff 0.0013、n=9、`identical=False`；S4 高斯界（R²=0.986、最大误差 0.170）；跨族留出 R² 0.371/0.378 | **诚实重述**：把 r=1.0 明确定位为**闭式恒等式的自洽检查**（两侧共享同一批冻结分数），不是独立验证；**独立证据改用**跨族留出 + 新 50k 样本上的预测。补散点图 + 误差分布 + 该检查的适用前提 | 低（写作 + 一张图） |

---

## 关键反驳合集（针对 R1.3 / R1.4 / R2.5 三条"同义反复"类质疑）

这五条事实必须同时摆在 rebuttal 里：

1. **τ 与准确率不是同一对象**：τ 只在**冻结 top-5 集合**上算 Kendall，准确率是**1000 类全 argmax**；前者是后者的稀疏子集统计。**若二者定义同一，就不会出现审稿人自己举的反例**（τ=0.615 却 78.6%）。
2. **R1.3 与 R1.4 互为反证**：1.3 说"关系太必然"，1.4 说"关系不成立"——同一份数据不可能同时支持两者；正确结论是**必要不充分**。
3. **可预测性来自留出族**：τ 预测器在**完全留出的模型族**上仍有 R²=0.371 / 0.378（Spearman 0.927, p=1.4e−12），而 CG 预测器在每个折都差于均值（ρ=−0.251, p=0.20）→ 这不是把准确率换个写法。
4. **闭式不是拟合**：τ(λ) 由冻结 margin 逐点算出（9 个 λ，最大误差 0.0019），**零自由参数**；这是"可计算性"，不是"重新定义准确率"。
5. **边界要写明**：高斯代理退化（R²=0.986、误差 0.170）与 τ 在收缩机制下的失效——**主动划出适用域**比被动挨打好。

## 我方主张需要收窄的两处（必须做，否则 1.3/1.4/1.6 会再被打一次）

- **"τ 是通用监控指标"** → 改为 **"τ 是 gap-平移族内、跨模型族可迁移的排序保持代理；跨干预机制不充分，且需配合数据集级校准"**。
- **"gap 是通用健康指标"的否定表述** → 保留（这是本文的核心贡献，有 34 条件 + 3 模型族支撑），但明确"我们否定的是*无条件的* gap 指标观"。

## 执行优先级

1. **R2.4 + R1.1 + R1.2**（写作/文献，零算力）→ 立刻可做
2. **R2.1 + R2.5 + R1.3 + R1.4**（写作，含关键收窄）→ 立刻可做，杀伤力最大
3. **R2.2（top-k 消融）+ R2.3（更多基准）** → 本地纯评测，无需云端
4. **R1.6（更多微调检查点）** → 本地 LoRA 微调，最耗算力，但直接回应"实验面窄"
5. **R1.5** → 已在补（`pwsh-3` 补种子 + 块 4/6/7 提为正文）

## 转投目标（不变）

Elsevier 转投（Pattern Recognition / **Neurocomputing** / Displays）为首选：篇幅宽松，容得下 Related Work 扩写 + 四组新实验；须披露与 `paper_ap3` 的重叠（一短一长）。次级：IEEE SPL（快，但要大压）。

---

# 已落地（2026-09-14 实施记录）

**改动文件**：`paper_a1/revision_additions.tex`（新增块 9–15；块 8 补 `\label{sec:holdout}`）。**未改动**：`paper_a1/main.tex`、`paper_a1/related_work.tex`、`outputs/` 下任何文件。
**编译核验**：先确认本文件**没有任何文件 `\input` 它**（`paper_a1/` 全目录 grep `revision_additions|\\input` 无命中），故不参与任何构建；另在临时目录用最小 wrapper（article + amsmath + booktabs）`pdflatex` ×3 通过：**0 error、7 页**，剩余 undefined 引用只有 `main.tex` 内的 `lem:inversion`/`sec:analysis`/`sec:results`/`sec:traj`/`tab:spectrum`（并入正文后消失），唯一 Overfull 为块 12 itemize 的 19.99pt。
**数字复核**：块 9–15 中出现的每一个数字都用一次性脚本对 `outputs/a1_{tau_holdout,subspace_results,theory_verify,tau_trajectory,multiseed}.json` 与 `outputs/a1_class_aligned/lr0.0/seed42/{eval_epoch1,2,3,5,10,results}.json` 逐条复算，**45/45 命中、0 处不一致**（脚本为临时文件，已删除；如需长期门禁，可在 `tools/` 下重建同名检查）。

| 审稿项 | 新增块（label） | 引用的数字 | 数字出处（JSON 键路径） |
|---|---|---|---|
| **R2.1** 非一阶近似 | 块 9 `sec:exactness` | 残余 max 0.0019 / mean 0.0013（n=9，5k）；max 0.0011 / mean 0.0009（n=3，50k）；高斯代理 Pearson 0.9865 / max 0.1695；std(m_c)=0.0673 | `outputs/a1_tau_holdout.json::theory_vs_measured_tau.predicted_tau_exact_vs_measured_tau_5k`（`.max_abs_diff`/`.mean_abs_diff`）、`..._50k`、`predicted_tau_gauss_vs_measured_tau_5k`（`.pearson_r`/`.max_abs_diff`）、`::key_numbers.baseline_theory_verification.std_m_c` |
| **R1.4** 承认并收窄 | 块 10 `sec:necessary` | Gaussian σ=0.25：58.8 % / τ=0.7612；σ=0.5：55.14 / 0.6111；σ=1.0：41.5 / 0.4337；σ=2.0：15.18 / 0.2609；类收缩 a=0.25：70.32 / 0.7598；a=0.5：78.58 / 0.615；自场 0.0435 ± 0.0288 | `outputs/a1_subspace_results.json::results`（gaussian 与 class_contraction 行）；`outputs/a1_theory_verify.json::class_contraction.measured` 与 `.self_field_mean_a1`/`.self_field_std_a1`（三行同为 5k 样本，`tools/clip_a1_subspace.py:25` N=5000、RandomState(42)） |
| **R1.3** 非同名 + 局限 | 块 11 `sec:tau_scope` | 冻结 top-5（1000 类中 5 类）；max 误差 0.0019；留出 R² 0.371（CLIP）/0.378（SigLIP）、pooled Spearman 0.927 | `outputs/a1_tau_holdout.json::theory_vs_measured_tau`、`::leave_one_model_out`、`::pooled_predictors`；口径见 `main.tex` §Setup 与 `results.json::fingerprint.class_names=1000` |
| **R1.1 + R1.6①** 收窄措辞 | 块 12 `sec:wording` | 三族模型、28 个带 (CG,τ,top1) 的条件、5 个检查点、R² 0.371/0.378、Spearman 0.927 | `a1_tau_holdout.json::rows_summary.models`、`::key_numbers.total_conditions_with_metrics=28`、`a1_multiseed.json::n_seeds=5` |
| **R2.5** 重定位 r=1.0 | 块 13 `sec:identity_check` | identical=false；max 0.0019 / mean 0.0013（n=9）；CLIP R² 0.3712（n_test=20）、SigLIP 0.3776（n_test=4）、pooled Spearman 0.9272 / p=1.36e−12；CG R² −1.5199 / −1.1251 / −1.4516、pooled Spearman −0.2507 / p=0.198；新样本 max 0.0011 / mean 0.0009（n=3） | `outputs/a1_tau_holdout.json::theory_vs_measured_tau.*`、`::leave_one_model_out.{clip,openclip,siglip}`、`::pooled_predictors.{tau,CG}` |
| **内部复核两条局限** | 块 14 `sec:disclosed` | τ 0.7563→0.7088；top-1 59.79→58.08 %；val loss 最低 2.3101（ep3）→ 2.3591（端点）；相对侵蚀 6.3 % vs 2.9 %；归档复评 top-1 58.50–58.62 %（epoch1–4 窄带 58.58–58.62 %）、τ 0.7638→0.7497 | `outputs/a1_class_aligned/lr0.0/seed42/eval_epoch{1,2,3,5,10}.json`（`.tau_final`/`.top1_50k`/`.val_loss`）、`.../results.json::val_loss=2.359054...`、`outputs/a1_tau_trajectory.json`（`both[*].top1`、`both[0].tau`/`both[9].tau`） |
| **R2.4** CZSL 引文 | 块 15 `sec:czsl` | 无实验数字（明写为 open question，不编造） | 三条文献经 Crossref DOI 元数据核验，见下 |

## 三条 CZSL 文献（Crossref 核验，2026-09-14）

同一作者组（Yang Liu / Xinshuo Wang / Xinbo Gao / Jungong Han / Ling Shao），全部 DOI 元数据可核验；块 15 按全文内联格式给出完整著录（本文件无 `.bib`）：

1. *Concept-Aware Graph Convolutional Network for Compositional Zero-Shot Learning*, **IEEE TNNLS** 36(6): 10394–10406, 2025 — doi:10.1109/TNNLS.2025.3528885。
2. *Semi-Negative Contrastive Subclass Discriminative Network for Compositional Zero-Shot Learning*, **IEEE TIP** 35: 2640–2652, 2026 — doi:10.1109/TIP.2026.3671655。
3. *Multi-Level Contextual Prototype Modulation for Compositional Zero-Shot Learning*, **IEEE TIP** 34: 4856–4868, 2025 — doi:10.1109/TIP.2025.3592560。

## 口径差异与需裁定事项（实施时发现，未擅自改动）

1. **块 7 的 `58.58--58.62\%` 窄于实测**：`a1_tau_trajectory.json` 的 both 族 10 个 epoch 的 top-1 实际区间是 **58.50–58.62**（epoch 6 = 58.5 最小，epoch 4 = 58.62 最大；`58.58–58.62` 恰好只是 epoch 1–4）。块 14 采用全区间 58.50–58.62 并注明块 7 的窄带来源；**块 7 原文未改**，请裁定是否同步放宽。
2. **同一 run 两个 val loss 记录**：`results.json::val_loss` = 2.3591（训练记录）vs `eval_epoch10.json::val_loss` = 2.3642（复评），块 6 caption 已披露 ≤0.005 差异；块 14 引用 2.3591（端点）与 2.3101（ep3 最低），与块 6 表格口径一致。
3. **`docs/A1_tau_earlystop_results.md` 是 2026-08-16 的作废口径**（τ 0.8327、top1 58.58、val 2.4639，来自已作废的参照缓存），与现行 `eval_epoch*.json` 不一致；本轮未引用它，建议加"作废"标注或重写。
4. **R1.1 / R1.6① 被改的句子在 `main.tex`**（Abstract 两处、Introduction、Discussion、Conclusion），不在本次授权改动范围，故块 12 只做**逐句摘录 + 替换文本**（可审计），未动 `main.tex`。
5. **论文里第二个 r=1.000（逐类分数位移，§Mechanism）不是同一件事**：它是把实测逐类位移与 λ‖g‖m_c 比对的一阶**量级**陈述（对图像取均值），不是排序层面的恒等式；故写进块 9（R2.1 的"量级/一阶语言"一侧）并注明将按一阶量级检查标注，而未混入块 13 的恒等式论证。
6. **未留数字空白的项**：7 项全部落地；其中 CZSL（R2.4）本组未跑实验，块 15 明确写成 open question 而非给出任何数字。
