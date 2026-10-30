# A1 + Paper A 升级包方案（2026-10-19）

> 适用对象：`paper_a1/`（A1，已投 Pattern Analysis and Applications）与 `paper合/`（Paper A，已投 Neurocomputing `NEUCOM-D-26-23760`）。
> 设计目标：**无论后续有没有 revision 都能用**——有修回意见就直接针对性改；没有则作为改投其他期刊的"加强版"底稿。
> 算力约束：**只用本地机器，不跑云端**；可用共享内存总量 **23.9 GB**，按"峰值不超过 ~8 GB"安排，不跑满。

## 一、统一约束（先定资源纪律）

| 约束 | 做法 |
|---|---|
| 内存 23.9 GB（含共享）| **一次只加载一个骨干模型**；`fp16` 推理；embedding 缓存到磁盘；评测固定 5{,}000 图子集；不同时跑两个大任务 |
| GPU（本地 4060 级，8 GB）| 只用 LoRA/冻结塔前向；batch 16–32；不跑全参数微调、不加载 50k 全量验证集 |
| 时间 | 单任务 ≤ 60 min；长任务拆成可断点续跑的小段（脚本已按"增量写归档"设计）|
| 数据 | 全部用已在本地的数据集（ImageNet-5k 子集、DTD、Food-101、iNaturalist-wild、marine_captions）|
| 冻结纪律 | `SUBMISSION/` 与 `_frozen_submitted/` 一律不动；升级只在本地工作稿 + 新归档进行 |

## 二、升级项总表

| # | 对象 | 升级项 | 现状/差距 | 具体动作 | 预期收益 | 本地资源 | 依赖 revision？|
|---|---|---|---|---|---|---|---|
| P0-1 | **A1** | **可部署的证书监控规则** | 已有 margin 质量 r≈−0.99、逐 epoch 选择 regret 0.06，但还没有"带保证的停机/选择规则" | 在 72 个 campaign checkpoint 上拟合 `M(0.01)` 阈值规则（相对冻结基线），报告**误停率 vs 精度损失**曲线，给出推荐阈值与保证区间 | 把"证书"从诊断升级为**可执行监控器**，审稿人可直接用 | 纯分析，<10 min，<1 GB | 否（通用）|
| P0-2 | **A1** | **证书对文本侧扰动的稳健性** | 已有 prompt 对 CG 的影响，但未测 `M(ε)` 是否受模板影响 | 5 骨干 × 10 模板逐模板算 margin 质量，报告跨模板波动（相对 CG 的 3.4×）| 证明证书**不怕文本侧噪声**，补上最后一块稳健性 | 单骨干串行，~25 min GPU，峰值 ~5 GB | 否 |
| P0-3 | **Paper A** | **位置效应因果性加强** | 位置效应有观测，但缺"秩/预算梯度"证据 | LoRA 秩 {4,8,16} × 适配位置 {text, both, vision} × 2 数据集，各 3 epoch（18 run）| 把位置效应从"相关"推进到**剂量–反应** | ~40–60 min GPU，峰值 ~6 GB | 否 |
| P0-4 | **Paper A** | **ODE 拟合的逐条件诊断** | ODE 有整体拟合，缺逐条件残差/失败案例 | 逐条件报告 R²/残差、标出外推失败区间，附 1 张小图表 | 理论–实证更可信；审稿人常问"拟合质量" | 纯分析，<20 min | 否 |
| P1-5 | **A1** | **定理的 Lipschitz 推广** | 目前下界只针对"嵌入均值统计量" | 加一条 Corollary：任何对均值 **K-Lipschitz** 的统计量，其 minimax 误差 ≥ margin 质量/K 的形式；给出证明与常量 | 把"否证一阶矩"升级为**否证一大类统计量**，新颖性显著提升 | 纯推导，2–3 h CPU，<1 GB | 否 |
| P1-6 | **A1** | **检索段的真实微调证据** | 检索证据是合成扰动 + 真实 checkpoint 的 CG/精度，缺"真实微调后的检索" | 用 marine_captions（536 对）做 2–3 个 LoRA 微调 run，逐 epoch 记 R@1、CG、M_R(ε)、τ | 补上"检索不是反例"的真实证据 | ~15–20 min GPU，峰值 ~4 GB | 否 |
| P1-7 | **A1** | **campaign 图** | 文字描述 670 对匹配，无图 | 画两联图：matched-gap 散点（72 checkpoint）+ `M(0.01)` vs 精度；Times New Roman/STIX/fonttype=42 | 图比表直观，审稿人更容易接受核心主张 | matplotlib，<5 min | 否 |
| P1-8 | **Paper A** | **LoRA vs 整塔微调对照表** | 已有真 LoRA 重跑数据，但未与整塔微调并列 | 汇总成一张对照表（同数据集/同位置/同预算），标注两者差异 | 直接回应"标注不一致"类质疑 | 已有数据 + 少量补算，~10 min | 否 |
| P1-9 | **A1 / PA** | **预判审稿意见与答复素材包** | 无 | 各写 6–8 条最可能质疑 + 对应证据/归档位置/一句话答复 | 修回时 10 分钟出初稿；无 revision 也能用于 cover letter | 纯写作，2 h | 否 |
| P2-10 | **A1** | **统计量对决的轨迹列** | 对决表有分类/检索/真实微调三列，轨迹列早期标"不可比" | 用 campaign 逐 epoch 相关性补齐轨迹列（已有数据，n=72）| 表格四列齐全 | 纯分析，<10 min | 否 |
| P2-11 | **A1** | **多数据集 campaign 扩展** | 3 个分类数据集 | 加 marine（检索）或 NKSID/fathomnet（域外）1–2 个，验证"证书跨域" | 泛化性更强 | 每个 ~20–30 min GPU，峰值 ~5 GB | 否 |
| P2-12 | **Paper A** | **理论示意图** | 无原理图 | 用 TikZ/matplotlib 画"适配位置 → 梯度流 → gap 轨迹"示意，Times 字体 | 提升可读性（Paper A 70 页偏长）| <1 h | 否 |
| P2-13 | **A1 / PA** | **改投/备用版本构建脚本** | 手工 | 幂等脚本：按目标刊参数（页数上限、模板、声明）一键生成投稿包骨架 | 万一被拒可 1 小时内改投 | <2 h 编码 | 否（通用）|
| P2-14 | **两篇** | **证据包统一目录** | 分散在 outputs/tools/docs | 生成 `UPGRADE/` 清单：脚本 → 归档 → 稿件数字的映射表（延续 claim ledger 风格）| 任何审稿人/合作者都可复核 | 纯整理，1 h | 否 |

## 三、优先级与预算

| 优先级 | 项目 | 预估总耗时 | 峰值内存 | GPU 时间 |
|---|---|---|---|---|
| **P0（立即做）** | P0-1、P0-2、P0-3、P0-4 | ~3 h（含写归档）| ≤6 GB | ~1.5 h |
| **P1（修回或改投前做）** | P1-5…P1-9 | ~6–7 h | ≤6 GB | ~40 min |
| **P2（有余力再做）** | P2-10…P2-14 | ~5 h | ≤5 GB | ~1 h |

**内存安全线**：任一时刻只跑一个 GPU 任务；任务前 `nvidia-smi` 确认显存 <2 GB 占用；embedding 一律落盘复用；5,000 图子集评测；不加载 50k 验证集。**全程预计峰值 <8 GB，远低于 23.9 GB 上限。**

## 四、交付物（做完后）

1. 新增归档：`outputs/analysis/a1_certificate_rule.json`、`a1_margin_mass_templates.json`、`paperA_position_sweep.json`、`paperA_ode_diagnostics.json`、`a1_retrieval_realfinetune.json`；
2. 本地稿更新（A1 / Paper A 各自重编译 0/0/0），**投稿包与 `_frozen_submitted/` 不动**；
3. 文档：本文件更新执行状态、`HANDOFF.md` 与 `文件地图.md` 追加条目、`docs/REVISION_CITATION_BACKLOG_2026-10-19.md` 扩充；
4. 门禁：三台账 + `paper_audit`（A1 预期保留冻结包 I-02/I-06）。

## 五、风险与不做清单

- **不做**：云端；全参数微调大模型；50k 全量评测；新下载大型骨干（除已有 5 个）；改动冻结投稿包。
- **风险**：P0-3 的 LoRA 扫描可能因显存/时间超预期——先跑 6 个 run 验证，再扩到 18；P1-5 的推广若证明不通，退化为"Remark + 反例"，不阻塞主线。

---

## 执行状态（2026-10-19 13:40，全部本地完成）

| # | 状态 | 交付物 |
|---|---|---|
| P0-1 | ✅ 完成（结论修正：迁移精度单调下降、无内部最优点 ⇒ **不宣称**验证过的早停规则，改为"监控统计量 + 范围声明"）| `a1_certificate_rule.json`、`a1_certificate_interior.json`；A1 §monitoring 的“Scope of the monitoring claim” 段 |
| P0-2 | ✅ 完成 | `a1_margin_templates.json`；A1 稳健性附录新增段 |
| P0-3 | ✅ 完成（用归档 ODE 拟合，不新增训练）| `paperA_rank_position_dynamics.json`；Paper A 新小节 “Rank Robustness of the Position Effect” + Table |
| P0-4 | ✅ 完成 | `paperA_ode_diagnostics.json`；Paper A 新小节 “Fit Diagnostics” + Table |
| P1-5 | ✅ 完成 | A1 新增 Corollary 1（非线性摘要同样被下界支配） |
| P1-6 | ✅ 完成 | `a1_retrieval_realfinetune.json`；A1 §retrieval 新增真实微调段 |
| P1-7 | ✅ 完成 | `paper_a1/figures/fig6_campaign.{pdf,png,_crop.pdf}`；A1 新增 Figure |
| P1-8 | ✅ 完成 | `paperA_lora_vs_fullft.json`；Paper A 家族对照表 |
| P1-9 | ✅ 完成 | `docs/A1_REVIEWER_OBJECTIONS.md`、`docs/PAPERA_REVIEWER_OBJECTIONS.md` |
| P2-10 | ✅ 完成 | `a1_showdown_within_run.json`；A1 §showdown 新增段 |
| P2-11 | ✅ 完成 | `a1_campaign_crossdomain.json`；并入 A1 稳健性段 |
| P2-12 | ✅ 完成 | `paper合/figures/fig_site_schematic.{pdf,png}`；Paper A 新增示意图 |
| P2-13 | ✅ 完成 | `tools/_p1336_build_venue_package.py`（dry-run 验证通过）|
| P2-14 | ✅ 完成 | `docs/EVIDENCE_MAP_2026-10-19.md` |

**编译**：A1 **60 页** 0/0/0；Paper A NC **72 页**、Springer **52 页**，均 0/0/0。
**台账**：A1 **179/179**、Paper A **88/88**、主 **96/96**。
**冻结**：`SUBMISSION/` 与 `_frozen_submitted/` 未动；A1 审计保留预期差异 I-02（包 58 vs 本地 60 页）。
**算力**：全程本地；峰值内存 <8 GB（模板任务 5 骨干串行，campaign 单模型），未跑云端。

## Round 3 (2026-10-19 19:40): A1 monitoring validation completed

The earlier plan item "monitoring claim scoped as a diagnostic, early stopping left open" is now closed by a re-run in a
regime with an interior optimum (same-domain held-out evaluation, DTD + Food-101, 4 trajectories / 32 checkpoints):
minimum-margin-mass epoch selection reaches mean regret 0.19 (worst 0.74) without labels, against 2.19 for the gap rule,
0.76 for training to the end and 4.03 for the first epoch; pooled r(M, top-1) = -0.983 while r(CG, top-1) = +0.32.
`paper_a1/main.tex` 60 pages, A1 ledger 187/187.
