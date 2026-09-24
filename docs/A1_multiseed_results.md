# A1 关键数字多 seed 区间（#8，2026-08-16 完成）

> 数据：`outputs/a1_multiseed.json`（5 seed × 26 条件；随机性双覆盖：
> 扰动随机性 RandomState(seed) + 采样随机性 RandomState(100000+seed) 重抽 5k 子集）。
> 脚本：`tools/clip_a1_multiseed.py`（本地 RTX 4060，约 2 小时夜跑）。

## 结果：论文值 vs 5-seed 均值±std

| 量 | 论文值 | 5-seed 均值 ± std | 稳健性 |
|---|---|---|---|
| τ Spearman（vs top-1） | 0.926 | **0.9167 ± 0.0064** | ✅ 极稳，仍居首位 |
| CG Spearman | −0.082 | **−0.1313 ± 0.0285** | ✅ 稳在 0 附近（负值，"无信息"成立） |
| CKA Spearman | 0.755 | **0.7781 ± 0.0209** | ✅ |
| mean_cos Spearman | 0.872 | **0.8672 ± 0.0046** | ✅ |
| 偏置场 Pearson（r=1.000） | 1.000 | **1.0000 ± 0.0000** | ✅ 确定性（跨 seed 无波动） |

## 解读

1. **四个 Spearman 全部落在 seed 噪声内**：论文单次运行值（RandomState(7)）与
   5-seed 均值差距 ≤1.7 std——"sampling noise"质疑可定量回应；
2. **τ 依然是最好代理**：0.9167 显著高于 cos 0.8672 / CKA 0.7781；CG −0.1313
   连符号都反向，进一步坐实"CG 无信息"；
3. **偏置场验证是确定性的**（r=1.0000±0.0000）：m_c 与 margin 均来自冻结模型，
   不随扰动随机性变化——理论验证本身不需要 seed。

## 用途

- PRL 审稿人若问 "single-run noise"：回复信中给上表 + 一句
  "across 5 seeds (perturbation + sampling randomness), all headline correlations
  are stable within ±0.03; τ remains the strongest (0.9167±0.0064), and the
  bias-field Pearson is exactly 1.0000 in every seed"。
- 顺带保护 Paper 1 的零样本数字（同套 5k/50k 口径）。
