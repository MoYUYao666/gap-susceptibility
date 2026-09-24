# A2 扩展执行规划：《Alignment Health Diagnostics: A General Framework》（单篇大作）

> 2026-08-30 立项。目标：在 A2（合并稿，35p review ≈ 印刷 15p）之上扩展为**单篇印刷 ~35p（review ~80-90p）**的框架级长文。
> 基础 = `paper_a2/`（EN 35p/ZH 26p；GitHub main=46f30ff）+ `docs/theory_tau_bound.md`（完整定理文档）+ 全部实验 JSON。

## 目标结构（Part I–V）

| Part | 内容 | 来源 | 目标页数 |
|---|---|---|---|
| I 理论框架 | Theorem 1(τ 算子) / 2(分布模型: 高斯闭式+Chebyshev+尾界) / 3(top-1 三界) / 4(文本侧非对称 0.13λ) / 5(类收缩=同构偏置场) / 6(方向解析子空间算子 v2) + Corollary 1-2 + 完整证明 | theory_tau_bound.md 入文 + 新 v2 推导 | 15-20 |
| II 域-模型基阵法 | **五域**（rare-species / NKSID / **ImageNet-5k / DTD / Food101**）× 五主线（精确性/σ_m/对称化/PEFT 边界/退化）+ 谱系 | 新实验 domain_matrix + 已有 | 15-20 |
| III 训练动力学 | 全模型族分 epoch τ/σ_m/top-1 轨迹矩阵（BioCLIP+Flickr 已有轨迹；补 CLIP+Flickr / CLIP+Sonar / CLIP+Marine 各 10ep 逐 epoch）→ 首 epoch 崩溃律 + 饱和时机 + 阈值标定 | 新实验 dynamics + ocean_tautraj | 8-12 |
| IV 退化地图 | 退化类型×强度×域×模型矩阵 + 方向解析 v2（k=2/3 子空间投影残差分解） | 改造 degradation/方向算子脚本 | 8-12 |
| V 机制与工程 | 类构成理论（margin/相似度→σ_m 定量）、提示空间（3/7 模板）、检索特化全景（MarineLife QA 分层）、监控器工具化 + 决策树 + 健康预算表 | 已有 JSON 重析 + 新小实验 | 8-10 |

## 执行批次

### 批次 1（零算力，立即）✅ 计划
- 理论章 LaTeX 起草（Theorem 2/4/5/Corollary 1-2 从 theory_tau_bound.md 转主文格式 + 证明完整化）
- 类构成机制分析（ocean_subset/nclasses 扫描 JSON 重析 → σ_m 与 margin 结构关系）
- 监控器工具批注化（已有 monitor 表扩展为阈值标定方程）

### 批次 2（中算力实验，后台并行）
- **E1 域矩阵** `clip_domain_matrix.py`：ImageNet-5k 子集 / DTD / Food101 × {CLIP,OpenCLIP,SigLIP,BioCLIP 冻结} 完整 λ 手术 τ/σ_m/谱系（NCC）→ `outputs/domain_matrix.json`
- **E2 训练动力学** `clip_dynamics.py`：{CLIP+Flickr10ep, CLIP+Sonar10ep} 逐 epoch 存权重+评测（BioCLIP 轨迹复用 ocean_tautraj）→ `outputs/dynamics_matrix.json`
- **E3 退化矩阵扩展** `clip_degradation_matrix.py`：现有（海洋 3 退化/声呐 4）× 强度 2 档 + ImageNet/DTD 各 2 退化 → `outputs/degradation_matrix.json`
- **E4 方向解析 v2** `clip_direction_subspace.py`：k=2/3 子空间（PCA/退化方向集）投影预测 → `outputs/direction_subspace.json`
- **E5 检索 QA 分层**（MarineLife QA 类型 central_object/颜色/时序 分层 R@1）→ `outputs/ml16k_qa_layers.json`

### 批次 3（成文）
- Part II–V 按 JSON 数据写作；Part I 与批次 1 合成
- EN 编译 0 error → ZH 版 → 图表（fig8-14 新图脚本）

## 验收
- 每 Part 数字必须来自真 JSON（禁编造）
- EN review ~80-90p / ZH ~55-60p 0 error；表格右缘扫描无溢出（复用 scan 脚本）
- GitHub 归档 + HANDOFF 更新 + 新备份

## 风险
- 单篇 90p review：OE 理论上是"research paper"上限内长文；若审稿人嫌长 → 保留拆分预案（Part I-III = 框架篇，IV-V = 应用篇）
- S3Simulator/音频模态：本环境不可达则如实 future work（不做承诺）
