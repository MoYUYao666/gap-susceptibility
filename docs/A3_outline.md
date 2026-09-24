# A3 提纲：《Alignment Health Across Modalities: Does the Bias-Field Theory Transfer to Acoustic Perception?》

> **状态（2026-08-27）**：✅ **初稿+增强全部完成**（EN 10 页 / ZH 7 页，0 错误；`paper_a3/main.tex`+`main_zh.tex`）。**核心结果**：① Theorem 1 跨模态 18/18 零偏差；② 域亲和复现且更锐利（SonarCLIP top-1 16.2%→96.8%、τ@λ=1 −0.02→0.90、σ_m 0.0239→0.0063，陆地对照 3.4× 深）；③ 对称化复现（Δτ +0.052→+0.003）；**增强**：④ 谱系·声呐版（NCC 平坦 94.8–96.8 @λ≤1 → 跨模态层级复现）；⑤ PEFT 3-seed（LoRA-both 100.0±0.0/τ 0.575±0.062；FullFT **τ 0.881±0.015 最佳但 1/3 种子停滞**（top1 21.9%，τ 仍 0.86——τ 跟踪结构非精度））；⑥ **方向感知测试=负面但有价值**（逐图 λ_i 分解几乎不改善 → **核心开放问题=方向解析算子**）。数据：sonar_protocol/sonar_peft/sonar_degradation/sonar_spectrum/sonar_peft_ms/direction_aware.json + sonar_clip_ft.pt。

**日期**：2026-08-26 ｜ 数据基线 = `data/NKSID/`（2617 图/8 类，Bohai Bay，Oculus M750d FLS，MIT）＋ 复用 CLIP ViT-B/32 与 `outputs/ocean_clip_flickrft.pt`（陆地 FT 对照）
**定位**：A2 的理论升级——把"间隙手术 + 类偏置场"从视觉语言模态搬到**声呐（声学成像）**域，检验理论是否**模态无关**。

## 0. 动机（一句话）

A2 证明"域亲和"（海洋）压平偏置场；E 问：这是**视觉特例**还是**普适规律**？声呐是理想检验——同为中国海洋感知场景、图像模态不同（声学成像）、类目少（8 类）且域特化强。

## 1. 标题候选

1. *Alignment Health Across Modalities: Does the Bias-Field Theory Transfer to Acoustic Perception?*（主推）
2. *SonarCLIP: Domain Affinity Is Not Visual—Bias-Field Diagnostics on Forward-Looking Sonar*

## 2. 设置（与 A2 逐字对齐）

- **数据**：NKSID，8 类（big/small propeller、cylinder、fishing net、floats、iron/soft pipeline、tire），2617 图，长尾（fishing_net 20 张，如实保留）；类提示 `a photo of a {class}`；每类上限 90（记账并披露）。
- **模型对**：(基座, 域适配) = (CLIP ViT-B/32 冻结, **SonarCLIP** = CLIP FullFT 10ep，调度与 A2 判别实验完全一致) ＋ (陆地对照: 已有 `ocean_clip_flickrft.pt` = CLIP+FlickrFT10) → **2×2 域/剂量判别**。
- **协议**：与 A2 相同——d̂=类文本质心差；图像侧 λ∈{−1,−0.5,0,0.5,1,2}；文本侧 λ=1；τ/top-1/CG；margins 精确预测（Lemma 1）；σ_m/mean_m；逐类位移 Pearson（可选）。

## 3. 判据（三问三答）

| 问题 | 判据 | 结论含义 |
|---|---|---|
| τ 精确预测器是否逐值命中？ | max \|diff\| ≤ 0.05（期望 ≤0.001）| 算子**模态无关**成立 |
| 声呐微调是否压平 σ_m？ | σ_m(SonarCLIP) ≪ σ_m(frozen)（期望 ≥3× 于陆地对照）| "域亲和"故事**跨模态**成立 |
| 非对称性/鲁棒性 | 与 A2 对比 Δτ、λ=1 保留率 | 域特化模型的对称化是否通用 |

**任一反例 = "模态边界"**（如 τ 预测失准/σ_m 不压平）——同样是有价值的结果（说明理论依赖视觉统计特性）。

## 4. 章节结构（12–14 页 elsarticle，OE 或 TNNLS 备选）

1. Intro（声呐感知工程语境 → 模态无关性问题）；2. Related（声呐 ATR 深度学习 [核验后再引] + A2 理论）；3. Setup（上述 §2）；4. Results（λ 曲线/τ 预测对拍表/σ_m 2×2 表/非对称性）；5. Discussion（模态无关 or 边界 + 与海洋结果对照表）；6. Concl。

## 5. 交付

`paper_a3/main.tex + main_zh.tex`（EN/ZH 双版、ctex/elsarticle 同 A2 惯例）、`tools/clip_sonar_protocol.py`、`outputs/sonar_protocol.json`、`outputs/sonar_clip_ft.pt`、GitHub 归档（main 线）。
引用新增（均需先核验）：NKSID 论文（若已发表）+ 声呐 ATR 代表文献。

## 6. 风险与处置

- **8 类偏少**：τ 统计量可承受（top-5 秩检验），但 m_c/σ_m 分布样本小 → 结果定性表述，不做过细定量；
- **fishing_net 20 张**：保留（长尾真实），报告中披露类别不均衡；
- **CLIP→声呐零样本可能差**：无妨——协议本测的是损伤结构而非绝对值；
- **无法下载/许可**：NKSID MIT ✓ 已下载（2617 图核验通过）。
