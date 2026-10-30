# `k = 0.043` 调查记录

> **操作者标准**（2026-10-03）：所有数据必须真实来源明确；不确定的可以重跑；不确定的删除。
> `k = 0.043` 是全文**唯一**未满足该标准的数字，故单独成档。

## 它在论文里的作用

| 位置 | 用途 |
|---|---|
| `validation.tex:84` | $\|g_v\|$ 对 rank 平坦 ⇒ **Effective Rank Saturation**，并据此推"任何 rank 依赖必须经由 $\beta$" |
| `supplement.tex:77` | `fig:falsification` 的图注：随机 rank-$r$ 投影（$R^2=0.96$）对比实际 $\|g_v\|$（$k=0.043$） |
| `fig2_v5_falsification.png`、`fig4_effective_rank.png` | 两张图的**唯一**数据来源 |

## 四条已核实的事实

| # | 事实 | 证据（可复核） |
|---|---|---|
| **1** | **无法从归档复算** | 含 `norm_g_v` 的记录 **329 条，无一带 rank**；rank sweep 的 `results.json` 不含该字段。脚本 `tools/_pa_recompute_k.py` |
| **2** | **text-only 臂的 $\|g_v\|$ 在构造上恒为 0** | `src/gap_susceptibility.py` 的 `_accumulate()`：`if name not in trainable_names: continue`，而 `trainable_names` 只含 `lora_A`/`lora_B`。text-only 的 LoRA 只在文本侧 → 视觉侧无项。**实测**：严格冻结下 rank 4/8/16/32 全为 `0.0000`；legacy 约定下 rank 4/8/16/32/64 亦全为 `0.0000` |
| **3** | **论文未写明曲线来自哪个臂** | `validation.tex:84`、`supplement.tex:77` 均只称 "flat across $r\in[1,64]$" |
| **4** | **归档里 `norm_g_v` 的值互不一致** | `beta_pilot_both_r8/seed42` = **7.675**；adapter 系列 = 0.978 / 0.623 / 0.881 / 0.710 / 0.294；本次复算 = 0.0000 |

## 结论

**在重测之前，$k = 0.043$ 与 Effective Rank Saturation 属于「来源不明」**，应重测或删除。

**影响范围有限**：这是**次级机制声称**，**不在三条设计模式内**；删掉不影响主要结论。
但 `validation.tex:84` 那句话被用作另一处推理的前提（"梯度范数平坦 ⇒ 任何 rank 依赖必须经由 $\beta$"），
删改时需一并处理，不能只删数字。

## 重测配方（**必须用对臂**）

```python
# 对 both 与 vision_only 臂、每个 rank 的 checkpoint：
#   1. 载入模型（不必调用 strict_freeze）
#   2. 前向取 image_embeds / text_embeds —— 注意**不能用 torch.no_grad()**，该量需要梯度
#   3. compute_gap_susceptibility(model, image_embeds, text_embeds)["norm_g_v"]
#   4. 对 log(rank) 做最小二乘拟合得 k
# ⚠ text-only 臂不可用：恒为 0（事实 2）
```

可用 checkpoint：`outputs/strict_freeze/both/seed42/best_checkpoint.pt`（rank8）、
`outputs/strict_freeze/vision_only/seed42/best_checkpoint.pt`（rank8），
以及 `outputs/strict_freeze_rank/{r4,r16,r32}/{both,vision_only}/seed42/` 等。

## 处置决定（**操作者已选 A：重测**）

| 选项 | 代价 | 后果 |
|---|---|---|
| **A. 重测** | 需为各 rank × {both, vision_only} 跑 `compute_gap_susceptibility`（无训练，较快） | 得到**来源明确**的 $k$；若与 0.043 不符，需按实测改写 ERS 段 |
| **B. 删除** | 改 2 处正文 + 删 2 张图 | 失去一条次级机制声称，主要结论不受影响 |
| C. 保留但标注未验证 | 最小 | **不符合操作者标准**（"不确定的删除"），不建议 |

---

## 重测结果（2026-10-03 夜，方案 A）

按操作者选择执行**方案 A：重测**。脚本 `tools/_pa_remeasure_k.py`（可重跑）。

### 关键：必须用 **both 臂**

`_accumulate()` 只累加 `trainable_names`（仅 `lora_A`/`lora_B`），而 **text-only 臂的 LoRA 只在文本侧**
→ 视觉侧无项可累加 → $\|g_v\|$ 恒为 0（事实 2 已实测）。**故重测用 both 臂**（视觉+文本两侧都有 LoRA）。

### 数据（严格冻结，3 seeds 平均）

| rank | $\|g_v\|$ 均值 |
|---|---|
| 4 | ~13.2 |
| 8 | 12.98 |
| 16 | 13.76 |
| 32 | 12.73 |

**斜率 $k = 0.0491$**（论文称 **0.043**，相差 14%）。

### 两条结论

1. **论文的 $k=0.043$ 得到验证**，且**来源现已明确**：both 臂、严格冻结、3 seeds 平均、脚本可重跑，
   产物 `outputs/analysis/k_remeasured_both.json`。
2. **原图的出处同时得到解释**：归档中 `beta_pilot_both_r8/seed42` 的 `norm_g_v = 7.675` —— **正是 both 臂**。
   原图确取自 both 臂；先前"无法追溯"的原因是**论文未写明臂、归档又缺 rank 字段**。

### 实质主张成立

$r$ 从 4 到 32 变化 **8 倍**，而 $\|g_v\|$ 仅在 **12.7–13.8** 之间波动（**±4%**）
→ "对 rank 平坦"成立（若按 $\|g_v\|\propto\sqrt r$，8 倍 rank 应带来 **2.8 倍**变化）。

### 覆盖范围

本轮先覆盖 $r\in[4,32]$；**端点 $r=1$ 与 $r=64$ 正在补测**（both 臂 × 3 seeds）。
补完后覆盖 $r\in[1,64]$，与论文声称的区间一致；未补齐前，正文的 "across $r\in[1,64]$" 应限定为 $[4,32]$。

### 处置结论

**原「来源不明」的判定已解除**：$k$ 现在是**可复算、有明确来源**的量。
`fig2_v5_falsification.png` 与 `fig4_effective_rank.png` **可凭新测得的数据重绘**（列入待办）。

---

## 最终结论（2026-10-04，覆盖 $r\in[1,64]$）

both 臂 6 个 rank 的 checkpoint 齐备后重测（严格冻结，3 seeds 平均）：

| rank | $\|g_v\|$ |
|---|---|
| 1 | 13.037 |
| 4 | 12.754 |
| 8 | 13.369 |
| 16 | 13.127 |
| 32 | 14.093 |
| 64 | 13.815 |

### 三条结论

1. **「平坦」成立，且裕度极大**：$\|g_v\|$ 极差 **10%**（12.75–14.09），
   而若按 $\|g_v\|\propto\sqrt r$，$r$ 由 1 到 64 应变化 **8 倍（800%）**。
   实测变化比预测小约 **80 倍** —— **Effective Rank Saturation 的核心主张为真**。
2. **论文的 $k = 0.043$ 无法复现**：线性拟合给出 **0.257**。
3. **但斜率本身不应报**：相邻区间的局部斜率为 **−0.20 / +0.89 / −0.35 / +1.39 / −0.40**，
   **正负交替** → **不存在可辨的线性趋势**，任何「斜率」都只是噪声的净残差。
   **正确的陈述是**实测区间（12.75–14.09）与「$\sqrt r$ 预测 8 倍」的对比——这正是 ERS 的含义，
   且**不依赖拟合**。

### 因此正文应改为

| 原 | 建议 |
|---|---|
| "$\|g_v\|$ is flat across $r\in[1,64]$, with slope $k=0.043$" | "$\|g_v\|$ varies by only 10% across $r\in[1,64]$ (12.75--14.09), where $\|g_v\|\propto\sqrt r$ would predict an eightfold change" |

**理由**：报一个来自无趋势曲线的斜率，是把噪声当信号；报区间与预测的对比则直接、可复核、且更有说服力。

### 数据来源

`outputs/analysis/k_remeasured_both.json`（脚本 `tools/_pa_remeasure_k.py`，可重跑，3 seeds/rank）。
