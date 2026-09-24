# A2 大纲：《Flattened Bias Fields: Why Marine Vision-Language Models Survive Gap Surgery》

**状态**：2026-08-25 草案 ｜ 数据基线 = 海洋探索全部结果（`outputs/ocean_*.json` ×13 + 对照权重 ×6）
**OE 版完成（2026-08-26）**：`paper_a2/main_oe.tex` + `main_oe.pdf`——elsarticle review 格式（18 页双倍行距 ≈ 10 页印刷版），工程化重构（新增 §5 Engineering implications 决策表 + 阈值协议 + 匹配规模判别指纹），Theorem 1 自含附录（Lemma 1/2 + Theorem 1 证明 + 假设 A1–A5 + 精确性说明），新增 3 条核验海洋感知文献（Chen ACM CSUR 2025 / Jian IMTS 2024 / Qin Remote Sens. 2022）；数字引用 ✓ 0 错误；摘要已压至 250 词内；Cover letter 已备（`paper_a2/cover_letter_oe.pdf`，含 companion 披露）。
**临时信号（2026-08-26，轨迹实验进行中）**：海洋 FT 逐 epoch：top-1 21.70→58.4→100.0%（ep1→10），**τ 第 1 epoch 即崩至 ~0.18 并保持平坦**，CG 0.52→1.10——"τ 是早于准确率的训练期警示"在训练方向更极端（对比 A1 ImageNet 版 τ 0.83→0.82 温和；海洋域是断崖式）。flickr 对照 + 回填正文 §5/limitations 进行中。

---

## 0. 定位

- **一句话**：把 A1 的"间隙手术 + 类偏置场"理论框架搬到海洋视觉模型，用判别实验证明**海洋微调把类偏置场压平一个数量级（且快速饱和）、使模型手术对称化、并放大类目数鲁棒性**——三条跨域新规律，非单纯复现。
- **与已投工作关系**：A1（PRL 在审）为理论母本（Theorem 1–5、λ 手术协议），A2 是其**应用延伸**，正文明确引用差异；不依赖 2026 综述（已投，双盲，仅作背景动机一句话，不引用）。
- **与文献差异化**：Chowers CVPR26（文本侧 α·g 移动→精度效应弱；我们显微调后**非对称性消失**并给出 σ_m 解释）；Grassucci ICLR26（instance/group-wise gap 敏感性；我们提供**偏置场-排序**机制）；Wortsman（权重空间解耦；我们嵌入空间）。海洋域模型（OceanCLIP/AquaticCLIP/MarineGPT）此前**无对齐结构理论分析**。

## 1. 标题候选

1. *Flattened Bias Fields: Why Marine Vision-Language Models Survive Gap Surgery*（主推）
2. *Gap Surgery in the Ocean: Cross-Domain Validation of the Class Bias Field Theory*
3. *Domain-Adaptation Flattens the Class Bias Field: Evidence from Marine Vision-Language Models*

## 2. 摘要骨架（~180 words）

p1 背景：对比模型的对齐健康/脆弱性诊断（τ/top-1 解耦、CG 无信息）已确立于 ImageNet 域（引 A1）。
p2 问题：理论是否跨域成立 + 海洋域模型会被如何诊断（海洋是天然小类目＋强域特化场景）。
p3 方法：3 个海洋域 VLM（oceanclip/bioclip/openclip/siglip）@ rare-species 67 类子集，重放 λ 手术协议；margins 精确预测；2×2 匹配规模微调判别实验。
p4 结果四条：① Theorem 1 逐点算子跨域机器精度命中；② 海洋微调 σ_m 压平 7–10×（0.0078 vs 0.0535/0.067）且 10ep 即饱和；③ 匹配规模判别：海洋域压平幅度是陆地域 3.6×（域特异，非纯训练量）；④ 非对称性消失（Δτ +0.246→+0.007）。
p5 含义：偏置场结构是"域亲和"的组织指标；海洋域零样本/泛化探针与 PEFT 实践建议。

## 3. 贡献（三条，逐条"主张一分量一证据"）

| # | 贡献 | 核心数字 | 证据 |
|---|---|---|---|
| C1 | 偏置场压平是**域特异的微调效应**（非训练量） | σ_m: 67 类域 = oc 0.0078 / bio 0.0535 / sig 0.0299 / ocp 0.0739；判别 = 0.0064(海) vs 0.0233(陆)，3.6×；50ep≈10ep（饱和 0.0078 vs 0.0064） | §5 (fig2, table2) |
| C2 | 手术对称化 = 海洋微调的指纹（非 d̂ artifact） | Δτ(λ=1)=oc +0.007 / bio +0.246；Flickr d̂ 复核 oc 0.479 vs 0.430 | §5 (fig1), §5.2 |
| C3 | 手术保留率由**类集构成（多样性/margin）**决定，而非类目数本身 | fish-only N=20/40/67 keep=99.1/98.1/96.7%（单调）但 fauna-117 反升 98.5%（鸟类/哺乳/珊瑚视觉差异大→margin 大）；ImageNet 54% @N=1000 | §4/§5 (fig3) |

## 4. 设置（§3）

- **模型**：oceanclip-0.15B（BioCLIP 基座+海洋 50ep）、bioclip 基座、openclip(B-32)、siglip-base（后两者为通用对照）。所有模型**同类集同图像同协议**。
- **数据**：imageomics/rare-species（BioCLIP 基准，cc0）两类子集：① 鱼类 **67 类/1608 图**（Actinopterygii+Chondrichthyes+Coelacanthi）；② 扩展"海洋动物" **117 类/2808 图**（+Cetacea/鳍足类/鹱形目/企鹅/珊瑚/海参，跨类群多样性检验）。筛选 ≥8 图/类、≤24 图/类，seed42；类名=拉丁 sciName；模板 `a photo of a {}`。
- **协议（与 A1 逐字对齐）**：d̂=质心差归一；图像侧 img'=N(img+λ‖g‖d̂)，λ∈{−1,−0.5,−0.25,0,0.25,0.5,1,2}；文本侧 txt'=N(txt−λ‖g‖d̂)，λ∈{0,0.5,1,2}；指标 CG/τ_top5（逐图 top-5 Kendall 均值）/top-1；margins 精确预测（10 对 d_ij + b_ij=m_j−m_i，λ‖g‖b_ij>d_ij）。
- **PFT 实验（§6）**：Flickr 1000 对/500 对 val，10ep，lr 1e-4（FT 5e-5），cosine，seed42；方法 LoRA(r16α32)-text/both、BitFit、FullFT；探针=任务 R@1+海洋零样本 top1/τ/CG。

## 5. 正文结构（7 页 PRL 版 / 可扩展长文版）

1. **Intro**：对齐健康诊断现状（A1 三现象）→ 海洋域为何是理想试金石（小类目、强域特化、数据稀缺、综述背景）→ 三个问题。
2. **Related Work**：① 间隙/对齐理论（A1 家族 + Chowers/Grassucci/Wortsman 定位）；② 海洋/水下 VLM（OceanCLIP/AquaticCLIP 无理论分析 + 数据集）；③ PEFT 与零样本退化（P1 + RotLLM 实践）。
3. **Setup**（§4 内容）。
4. **Results A — 重放与普适性**：λ 曲线族（fig1：4 模型 × 图像/文本 双侧 τ/top1/CG 面板）；对照 ImageNet 保留率表（table1）；**Theorem 1 精确验证**（fig3 预测-实测散点 8λ×2模型×3N，r=1.000）。
5. **Results B — 偏置场与判别实验（核心新贡献）**：m_c 分布对比（σ_m/mean_m 表）；2×2 匹配规模判别（table2 + fig2：σ_m 柱状 4 元组 + 饱和曲线）；逐类位移 Pearson（bioclip 0.96 / oceanclip 信噪比崩）；非对称性（fig1 双侧差 Δτ 汇总）；Flickr d̂ 复核。
6. **Results C — PEFT 保护跨域再验证**：PEFT vs FullFT 表（fig4），LoRA-both 反超 FullFT（0.627 vs 0.603）、BitFit 保护最佳（−2.6%）、bioclip FullFT −56.4%≈P1 ImageNet −59%。
7. **Discussion**：三个机制解释（σ_m 压平=域亲和；对称化=文本/图像簇结构平衡；N→top-1 = 竞争强度）；实践建议（PEFT 优先、τ 监控、CG 禁用、类目数报告）；与 A1 的关系（延伸非重复）。
8. **Limitations**：rare-species 为濒危/百科全书图像；d̂ 自估（已复核）；类目 67（补强到 ≥100 后更新）；单 seed 主结果（补强加 3-seed τ 置信）；oceanclip 训练数据不可见（scale 混叠已用匹配规模控制）。
9. **Conclusion**。

## 6. 图表规划

| 图/表 | 内容 | 数据源（JSON） |
|---|---|---|
| fig1 | λ 曲线族（4 模型×双侧，3 面板：τ/top1/CG） | ocean_gap_surgery.json + ocean_flickr_dhat.json |
| fig2 | σ_m 结构：4 模型柱 + 2×2 判别柱 + 饱和点 | ocean_margins/sigma_other/flickrft_sigma/marineft10_sigma |
| fig3 | Theorem 1：预测 vs 实测逐点（含 N-sweep） | ocean_margins/nsweep |
| fig4 | PEFT 保护：任务 R@1 vs 零样本保持（散点+线） | ocean_peft.json |
| table1 | 模型健康画像（诊断卡浓缩） | 汇总 |
| table2 | 2×2 判别表（σ_m/mean_m/gap/top1） | §6 数据源 |
| table3 | margins/m_c 统计 + 独立性 | ocean_margins.json |

## 7. 数据清单（应备尽备）

- 已有（全本地可复算）：`outputs/ocean_{gap_surgery,subset,margins,nsweep,sigma_other,flickrft_sigma,marineft10_sigma,peft,flickr_dhat}.json` + 对照权重 `ocean_{flickrft,marineft10}_bioclip.pt`
- 补强新增（§8）：`ocean_margins_x.json`（siglip/openclip 预测）、`ocean_inat_large.json`（大类目复验）、`ocean_clip2x2.json`（CLIP 族判别）

## 8. 补强实验状态

| # | 实验 | 目的 | 状态 | 关键结果 |
|---|---|---|---|---|
| ⑤ | siglip/openclip 的 τ 精确预测验证 | Theorem 1 全模型族覆盖 | ✅ | 4 模型族 diff ≤0.0001（openclip 0.0361=siglip 0.0462 等逐值）|
| ④ | 海洋动物扩展类集（117 类/2808 图）复验 | 更大 N + 跨类群（多样性）检验 | ✅ | τ_pred=τ_meas 逐值；σ_m: bio 0.0595/oc 0.0067（9×）；Pearson: bio 0.970 / oc 0.509；**保留率非 N 单调（98.5%>96.7%），改由构成决定** |
| ⑥ | CLIP 族 2×2（Flickr/海洋 10ep） | σ_m 压平域特异性跨模型族 | ✅ | CLIP: frozen 0.0333 / FlickrFT 0.0203 / MarineFT **0.0092**（2.2×）；bioclip: 0.0535/0.0233/0.0064（3.6×）→ **跨模型族成立**；CLIP 海洋 FT 后 τ_l1 从 0.06→0.616 重构排序 |
| ⑦ | 多 seed（1/42/99） | 主结果抽样噪声 | ✅ | τ@1: bio 0.458±0.005 / oc 0.450±0.006；top1@0 ±0.4pp 内 |
| ⑧ | 多模板 3/7 套（A1 同款） | 模板稳健性 | ✅ | λ=1 曲线平行（τ 变动 ≤0.015，top1 ≤0.7pp）；与 A1 ImageNet 平行性一致 |
| ⑨ | iNat 野生照片跨来源复验 | EOL 图 vs 野生照 | ✅ | 48 类/576 图；τ 预测逐值（0.5087/0.6149）；σ_m: bio 0.0611/oc **0.0050**；保留率 oc 98.8%/bio 80.8% —— 全部结论跨来源成立 |
| ⑩ | PEFT 3-seed（{1,42,99}） | 训练随机性稳健 | ✅ | PEFT 波动 ≤0.6pp（top1）/FullFT ±0.7~1.3pp；LoRA-both 0.620±0.005 ≥ FullFT 0.587±0.015；bioclip FullFT −61.6%±1.3 |
| Ⓐ | 退化-手术压力测试（雾化 t=0.6/0.3 + 色偏） | 域退化可预测性 | ✅ **负结果=亮点** | λ_eff≈0（≤0.034）但 τ 0.29–0.64；间隙预测器失效 0.36–0.68 → **离轴结构化扰动 = 精确算子边界**；海洋模型退化更稳；future work 改写为方向感知扩展 |
| Ⓑ | 任务敏感性谱系海洋版（NCC/top1/R@1 同 λ 网格） | A1 三档谱系跨域 | ✅ | NCC 平坦（λ≤1 ≤2pp）✓；R@1 与 top1 均 τ 敏感、**不**跟踪 CG（缺自然图文对，已披露）|
| Ⓒ | 监控器工作示例表（τ 轨迹 ep1/3/5/10 + 决策列） | 工程可用性 | ✅ | marine FT ep1 报警（τ 0.177, top1 58.4%）；Flickr 同报警（τ 0.069, top1 5.9%）——"τ 报警、top-1 定方向" |
| Ⓓ | 自然字幕检索探针（BLIP 536 对；WaterBench 核验不可用→回退） | "检索跟踪 CG"自然 caption 判定 | ✅ **边界** | OpenCLIP R1 15.5%→7.1% 单调而 CG λ=2 回弹→不跟踪 CG；海洋模型通用字幕近随机（≤1.4% vs 0.19%）→特化代价（§4.2.2 已写入 EN/ZH）|

**论文终态（v3，2026-08-26）**：EN 22 页 / ZH 16 页，0 错误；5 图 7 表；引用 22 条（含 2 篇 OE 本刊先例 Christensen/Maione 2026）；`main` = `bf43e90`（全部归档）。**A2 定稿可投。**

## 9. 风险与对策

- **与 A1 重复度质疑**：正文显式定位"应用延伸+三条新规律"，Table 对照 A1 域；评审若要求 → 缩减为 A1 的 companion。
- **海洋特殊性论证**：无海陆对照会虚弱 → 2×2 判别就是回应；再补 CLIP 族（⑥）。
- **类目小（67）**：④ 补大；若新来源噪声大 → 只新增趋势证据，主表保留 67。
- **双盲**：不引已投综述；A1 相关引用仅"已送审/在审工作"表述按投稿刊要求处理。
