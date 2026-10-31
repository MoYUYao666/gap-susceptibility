# Paper 1 评测口径核查（2026-08-16，响应训练参数 bug 的追溯审计）

## 核查对象

`apply_lora_to_model` 只冻结被替换的 Linear 层 → Embedding/LayerNorm 仍
requires_grad=True。问题：P1 的 116 实验训练与评测，测的到底是
"纯 LoRA"、"LoRA+Embedding/LN 混合"，还是"LoRA-only 重构"？

## 核查结论（逐文件读源码）

1. **P1 训练器（`src/trainer.py`）的优化器参数**：
   `get_peft_params`（`src/peft_methods.py:137`）= `[p for p in model.parameters()
   if p.requires_grad]` —— **与出 bug 的脚本同一模式**。因此 P1 的 "LoRA" 训练
   实际训练了 **LoRA + Embedding + LayerNorm**（未冻结参数全部进 AdamW）。

2. **P1 的训练期指标（CG/DG 演化——论文核心）**：trainer 在**同一进程内**训练并
   记录 gap 指标 → 这些数字描述的是**实际训练出来的混合模型**（真实测量，无编造）。

3. **P1 的零样本数字（Table 7，58.66/59.67 等）**：`paper/scripts/zeroshot_extra.py`
   加载**检查点**评测；而 `_save_checkpoint`（`src/trainer.py:893`）**只存
   lora_state_dict**（注释明言"仅LoRA权重，不含冻结的完整模型"）→ 零样本数字
   描述的是 **LoRA-only 重构**。

## 影响评估

- **无编造、无篡改**：所有数字都是真实测量；各自口径内部自洽。
- **两个不一致的口径并存**：训练期 CG/DG = 混合模型；零样本 = LoRA 重构。
  审稿人若按"归档权重"复现，只能复现零样本那半边。
- **"LoRA 微调"的表述不精确**：实际训练还包含 Embedding/LayerNorm。

## revision 动作（必做清单）

1. 在 Setup/附录披露训练配置精确口径："LoRA adapters on attention projections;
   the embedding and LayerNorm parameters remain trainable (as in the reference
   implementation)"——或把 trainer 改为纯 LoRA 后重跑关键行（text-only/both
   × 主数据集），对比确认结论方向不变；
2. 说明零样本数字来自归档 LoRA 检查点（重构模型）；
3. 若重跑，用 `get_lora_params`（src/lora.py:290，正确的 LoRA-only 过滤器，
   与 P1 训练器现有调用不同）。
