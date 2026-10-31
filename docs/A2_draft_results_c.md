# A2 §6（Results C）草稿 —— PEFT 保护跨域再验证

> 状态：2026-08-25 完成稿（3-seed 已回填，数据 `outputs/ocean_peft_ms.json`，seed∈{1,42,99}）

## 正文（英文版骨架）

**PEFT protects, full fine-tuning destroys — cross-domain re-validation.**

Setup. 在 Flickr30k（陆地区域任务，1000 对训练 / 500 对验证，10 epoch，lr 1e-4（FullFT 5e-5），
cosine，对称对比损失）上微调海洋模型，探针双份：任务性能（Flickr R@1）与海洋零样本保持
（rare-species 67 类 top-1，冻结基线 bioclip 21.70 / oceanclip 24.19）；训练随机性 seed∈{1,42,99}。

Result 1. 参数通路决定零样本命运（3-seed 均值±sd）：

| 配置 | R@1 (mean±sd) | marine top1 (mean±sd) | 相对冻结基线 |
|---|---|---|---|
| bioclip LoRA-text | 0.1139 ± 0.0037 | 22.95 ± 0.20 | **+5.8%** |
| bioclip FullFT | 0.3398 ± 0.0542 | 8.33 ± 1.32 | **−61.6%** |
| oceanclip LoRA-text | 0.3484 ± 0.0035 | 23.36 ± 0.13 | −3.4% |
| oceanclip LoRA-both | 0.6200 ± 0.0050 | 22.22 ± 0.36 | −8.1% |
| oceanclip BitFit | 0.1781 ± 0.0018 | 23.51 ± 0.05 | **−2.8%** |
| oceanclip FullFT | 0.5870 ± 0.0151 | 20.52 ± 0.71 | −15.2% |

Result 2. 小数据规模下 PEFT 不再输任务性能：
- LoRA-both R@1 = 0.620 ± 0.005 **≥ FullFT 0.587 ± 0.015**——任务最优与零样本保护可兼得；
- BitFit 保护最佳（−2.8%）但任务最弱（0.178）→ PEFT 内"保护–性能"可连续调节，且始终优于 FullFT 的零样本代价。

Result 3. 离散度对比：PEFT 配置跨种子波动 ≤0.6pp（top1），FullFT ±1.3pp（bioclip）/+0.7（oceanclip）——
方向性结论对训练随机性稳健（样本量 3 下 bioclip FullFT 三值 7.03/7.84/10.14 均远低于 PEFT 的 ≥22.70）。

Result 4. 与 σ_m 判别的解耦证据：FullFT（Flickr）σ_m 压半（0.0233）却零样本崩 → 偏置场压平 ≠ 零样本保护，
PFT 保护是"参数通路限制"，σ_m 重排是"嵌入结构效应"，两者独立（§5 呼应）。

Fig4 说明：x=任务 R@1，y=海洋 top-1 相对基线（%），点=配置（误差棒=3-seed sd）；
PEFT 位于"右上（高任务+高保持）"，FullFT 位于"右下"。
