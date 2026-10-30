# 新论文想法备忘（2026-10-21）

> 状态：**仅记录，暂不启动**。操作者指示：先把五篇现有稿件的升级与审核走完，再决定新论文。
> 每条的"数据就绪度 / 工作量 / 目标期刊"只作粗略判断，启动前需重新评估。

## 提案 A（最推荐，零新实验）

**题目（暂）**：What a modality gap can measure: a measurement theory for alignment health

- **增量**：把 A（梯度流 ODE）、A1（order-statistic 表征定理 + 停时证书）、P3（协议依赖的临界点）、A23（跨域矩阵 + 精确 τ 预测器）合成一个统一框架：
  1. first-moment 指标（gap/CG）与 order-statistic（τ）的不可比性定理（A1 表征定理的一般化）；
  2. "何时 gap 可以作为健康指标"的可判定条件（类中性干预）；
  3. 停时证书的成本-收益定理（A1 stop-rule regret 上界）；
  4. 报告清单（Commentary 的 12 条 → 可机检的 R-MAP）。
- **数据就绪度**：100%（204 个实验、96 条 ODE、5 域 × 4 族、118 标定点均在 `outputs/`）。
- **工作量**：写作 2–3 周；无需新 GPU。
- **目标**：TMLR / JMLR，或 Nature Machine Intelligence perspective。
- **风险**：与四篇在审稿 self-overlap；增量必须写成"统一理论 + 新 meta-analysis"，并等至少一篇接收再投。

## 提案 B（少量 GPU）

**题目（暂）**：Protocol phase diagrams for PEFT alignment

- **增量**：把 P3 的 crossing（r∈[5,6]，5-seed p=0.008）从"单点"扩成 (num_samples × epochs × rank) 相图，主张"crossing 位置是协议坐标的函数"，并给出可检验的函数形式。
- **数据就绪度**：P3 已有部分消融；需 10–15 个 LLaVA/Qwen2-VL-2B runs。
- **目标**：PRL / NeurIPS。
- **依赖**：P3 决定结果；若 P3 被拒可作为它的 follow-up。

## 提案 C（中等）

**题目（暂）**：Label-free early-stopping certificates for PEFT of VLMs

- **增量**：把 A1 的 margin-mass 证书基准化到 CLIP/LLaVA/Qwen 多任务，给出成本-精度 frontier 与 regret 上界的实验验证。
- **数据就绪度**：A1 已有分类/检索/双塔；缺 LLaVA 指令微调的逐 epoch 监控。
- **工作量**：30+ 小 runs（本地数天 / 云一周）。
- **目标**：ICLR / TMLR。

## 提案 D（应用向，需外部数据）

**题目（暂）**：Gap-based health diagnostics for underwater perception: a field protocol

- **增量**：A23 的工程化 + 更多声呐数据集（SCTD-3.0 / URPC）+ 部署清单；UATD 失败案例作为"部署警告"卖点。
- **数据就绪度**：4 个声学数据集已就绪；SCTD/URPC 受网络限制未取全。
- **目标**：IEEE JOE / OCEANS。

## 提案 E（meta-science，小众）

**题目（暂）**：Reproducibility audit of PEFT alignment claims

- **增量**：用本仓库的 `provenance_manifest.json` + `claim_ledger` 方法对 30–50 篇文献做数字审计，量化"多少结论不可复算"。
- **数据就绪度**：方法就绪（本项目已实践）；需要文献 PDF 获取与人工核对。
- **目标**：FAccT / NeurIPS Datasets & Benchmarks。

## 启动判据（建议）

1. 五篇中至少一篇收到"接收/小修"决定；
2. 提案 A 的 outline 与四篇的 overlap 分析通过（列出每条增量的"新在哪里"）；
3. 新论文不得复用未发表稿件的定理原文，只能引用其 arXiv/DOI（或明确改写一般化）。
