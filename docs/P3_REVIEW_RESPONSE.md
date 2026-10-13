# P3 审稿意见逐条应答（工作文档）

> **稿件**：`PRLETTERS-D-26-02378` — *Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation*
> **期刊**：Pattern Recognition Letters｜**决定**：**Revise**（可修改后重审）
> **状态日期**：2026-10-12｜**修订截止**：**2026-11-02**（逾期视为撤稿）
> **编辑**：Yonghuai Liu（Editor-in-Chief）
> **总评**：*clarity of technical details and sufficiency of experimental studies*
> **平台要求**：**must reply to reviews on Editorial Manager**

## 条目总览：**33 条**（R1 5｜R2 5｜R3 23）

## 归纳：条目高度重复，实际集中在以下根问题

| 根 | 问题 | 出现于 | 处理类型 |
|---|---|---|---|
| **A** | block additivity does NOT imply bilinear (norm-squared is block-additive) | R1.5, R3.3 | 理论必须改 |
| **B** | uniqueness of gamma vs optimality under a chosen entropy-regularised objective | R1.3, R3.1 | 理论表述 |
| **C** | why |gamma| is used when its sign carries direction | R1.3, R3.8 | 澄清 |
| **D** | orthogonal reparameterisation assumption vs non-orthogonal LoRA A/B | R2.5, R3.2, R3.3 | 澄清+限定 |
| **E** | no true block-wise gamma-guided allocation experiment (Theory group used uniform r=4) | R2.2, R2.4, R3.9 | 需补实验 |
| **F** | no downstream evaluation (only alignment energy) | R1.3, R2.3, R3.15, R3.16 | 需补实验 |
| **G** | blank images and small training sets instead of real image-text data | R1.4, R3.13, R3.14, R3.23 | 需补实验 |
| **H** | cross-architecture evidence thin (LLaVA-1.5 + Qwen2-VL only; Qwen2-VL behaves differently) | R1.4, R3.10, R3.11 | 需补实验/改表述 |
| **I** | statistics and reproducibility (3 seeds; CI spans zero; 30x comparison; NaN attribution; software versions) | R3.17, R3.18, R3.19, R3.20, R3.21, R3.22 | 需补统计/诊断 |
| **J** | zero-shot definition unclear (does it ever access target-model gradients?) | R2.1, R3.10 | 澄清 |

## 逐条应答（每条下方留空供填写回复）

### R1（5 条）

#### R1.1 — 写作/定位

> The paper addresses an important PEFT design problem: how to allocate LoRA capacity across different model components without expensive target-model search.

**建议动作**：在回复中确认动机陈述，无需改稿

**回复（待填）**：

```

```

#### R1.2 — 写作/定位

> The first-order gradient-coupling interpretation is intuitive and well motivated. The relation \(\Delta E_k\approx-\eta\Gamma_k\) provides a simple way to connect task gradients with changes in cross-modal alignment. Weaknesses

**建议动作**：确认一阶解释成立；回复中致谢

**回复（待填）**：

```

```

#### R1.3 — 写作/澄清

> The practical meaning of the alignment metric is somewhat limited by the experimental setting. The main LLaVA experiments use blank images and very small training sets specifically to isolate representation geometry. This is useful diagnostically, but it leaves unclear whether minimizing the proposed alignment energy translates into better downstream multimodal performance.

**建议动作**：区分「接受性」与「唯一性」；并说明 |Γ| 与符号的关系（与 R3.8 同源）

**回复（待填）**：

```

```

#### R1.4 — 需补实验

> Given the strong cross-architecture generalization claim, validation on only LLaVA-1.5 and Qwen2-VL is limited, particularly because LLaVA-1.5 is now a relatively dated VLM architecture. Testing at least one more recent model family would provide substantially stronger evidence that the observed gradient structure is transferable rather than specific to these architectures.

**建议动作**：用真实图文对复跑主实验；补一个更新的 VLM 家族（与 R2.3/R3.4 同源）

**回复（待填）**：

```

```

#### R1.5 — 需改理论表述

> However, the proof contains an important gap. In the appendix, the manuscript states that block decomposability implies that the “most general first-order functional” must be bilinear, \(S(x,y)=x^\top Ay\), but block additivity alone does not imply bilinearity; quantities such as \(\|x\|^2\) are also block-additive.

**建议动作**：最严重：block additivity 不能推出 bilinear（‖x‖² 亦 block-additive）。必须把定理假设显式化（先设一族函数再证族内唯一），或把唯一性降级为族内唯一

**回复（待填）**：

```

```


### R2（5 条）

#### R2.1 — 写作/澄清

> Zero-shot definition is unclear and inconsistent. The abstract claims no target-model gradient access, but the appendix describes computing Γ on LLaVA. Please clarify what is truly zero-shot versus post-hoc validation.

**建议动作**：明确区分「零样本分配」（不访问目标模型梯度）与「后验验证」（在目标模型上测 Γ）——与 R3.10 同源

**回复（待填）**：

```

```

#### R2.2 — 需补实验

> The exponential allocation rule is not experimentally validated. The "Theory" group uses uniform r=4, not block-wise non-uniform allocation based on Γ. Please either provide a true block-wise Γ-guided allocation experiment or soften the claim.

**建议动作**：真正的逐块 Γ 引导分配实验（Theory 组现用 uniform r=4）——与 R3.9 同源

**回复（待填）**：

```

```

#### R2.3 — 需补实验

> Only alignment energy ΔE is reported. Please add at least a small downstream evaluation (e.g., VQA, captioning) or state that "optimal" refers only to alignment energy.

**建议动作**：补下游评测（VQA / captioning），或明确把 optimal 限定为 alignment energy——与 R1.3/R3.16 同源

**回复（待填）**：

```

```

#### R2.4 — 需补实验/改表

> Table IV is qualitative only. A comparison with at least one or two methods (e.g., AdaLoRA, HALoRA) under the same budget is needed.

**建议动作**：Table IV 是定性表 → 与 AdaLoRA / HALoRA 等同预算定量比较——与 R3.9 同源

**回复（待填）**：

```

```

#### R2.5 — 写作/限定

> The theorem assumes orthogonal reparameterization and block additivity, but LoRA's A/B decomposition is not orthogonal and blocks may interact. Please clarify the scope and limitations.

**建议动作**：正交重参数化假设的适用范围与限制——与 R3.2/R3.3 同源

**回复（待填）**：

```

```


### R3（23 条）

#### R3.1 — 写作/澄清

> Could the authors clarify more rigorously why requirements R1–R5 are necessary conditions for a PEFT allocation statistic rather than assumptions imposed by the proposed framework?

**建议动作**：R1–R5 是必要条件的公理化，还是框架强加的假设 → 需明确表述

**回复（待填）**：

```

```

#### R3.2 — 写作/澄清

> In Theorem III.1, how is the restriction to the orthogonal subgroup of reparameterizations justified, given that practical LoRA uses non-orthogonal \(A/B\) factorization?

**建议动作**：正交子群的限制与 LoRA 非正交 A/B 的矛盾（与 R2.5/R3.3 同一问题）

**回复（待填）**：

```

```

#### R3.3 — 需改理论表述

> Could the authors provide a more rigorous treatment of the claim that the Representation Theorem establishes uniqueness, particularly under practical non- orthogonal PEFT parameterizations?

**建议动作**：唯一性证明在非正交参数化下的严谨性（与 R1.5/R3.2 同源）

**回复（待填）**：

```

```

#### R3.4 — 写作/补充

> The definition of \(\Gamma_k\) uses \(E_{\text{batch}}[\nabla_{M_k}L]\); how is this expectation estimated in practice, and how sensitive is \(\Gamma_k\) to the choice and size of the reference batch?

**建议动作**：Γ 的期望如何估计、对参考 batch 大小与选择的敏感度 → 可做敏感性实验

**回复（待填）**：

```

```

#### R3.5 — 需补实验

> The first-order approximation assumes that the second-order curvature term is negligible; could the authors provide direct empirical evidence on LLaVA and Qwen2-VL that the Hessian contribution is indeed sufficiently smaller than the \(\Gamma\) term?

**建议动作**：直接经验证据：Hessian 项确实小于 Γ 项（LLaVA / Qwen2-VL）

**回复（待填）**：

```

```

#### R3.6 — 写作/限定

> The paper assumes that PEFT operates in a small-perturbation regime, but the experiments include ranks as high as 64 and even representation collapse; does the first- order GFAP formulation remain theoretically valid in these high-rank regimes?

**建议动作**：一阶 GFAP 在 r=64 与表示塌缩时是否仍有效 → 需明确适用域

**回复（待填）**：

```

```

#### R3.7 — 写作/补充

> How is the entropy-regularization parameter \(\beta\) selected, and why is the reported \(\beta=0.137\) appropriate for zero-shot cross-architecture transfer without target-model calibration? 3

**建议动作**：β 的选择依据（0.137 为何适用于跨架构零样本）→ 需说明选取流程

**回复（待填）**：

```

```

#### R3.8 — 写作/澄清

> The exponential allocation formula depends on \(|\Gamma_k|\); could the authors explain why the absolute value is used for allocation when the sign of \(\Gamma_k\) has a direct interpretation as alignment-improving or alignment-damaging?

**建议动作**：为何用 |Γ|（符号有方向含义）—— 与 R1.3 同源

**回复（待填）**：

```

```

#### R3.9 — 需补实验

> Could the authors provide a quantitative comparison between the proposed GFAP allocation and established methods such as AdaLoRA, HALoRA, IGU-LoRA, ShapLoRA, and NTK-based allocation under the same parameter budget and training conditions?

**建议动作**：与 AdaLoRA / HALoRA / IGU-LoRA / ShapLoRA / NTK 的同预算定量比较 —— 与 R2.2/R2.4 同源

**回复（待填）**：

```

```

#### R3.10 — 写作/澄清

> The claimed zero-shot transfer is primarily demonstrated from CLIP to LLaVA; how can the authors establish that the observed transfer is genuinely cross-architecture rather than arising from shared pretrained components or related vision-language representations?

**建议动作**：零样本迁移是否真的跨架构，而非共享预训练组件所致 —— 与 R2.1 同源

**回复（待填）**：

```

```

#### R3.11 — 需澄清

> Since the paper reports that Qwen2-VL exhibits substantially different behavior from LLaVA, does this result challenge the claim that \(|\Gamma_k|\) ordering is architecture- transferable, and under what conditions does the proposed partial-order preservation actually hold?

**建议动作**：要小心：Qwen2-VL 行为不同是否挑战 |Γ| 排序可迁移性？→ 需说明部分序保持成立的条件

**回复（待填）**：

```

```

#### R3.12 — 需补数据表

> Could the authors provide the complete block-wise \(\Gamma_k\) values for CLIP, LLaVA, and Qwen2-VL together with their corresponding optimal ranks, rather than relying mainly on qualitative ordering?

**建议动作**：给出 CLIP / LLaVA / Qwen2-VL 的完整逐块 Γ_k 与对应最优 rank（而非只有定性排序）

**回复（待填）**：

```

```

#### R3.13 — 写作/澄清

> Why are blank images used as the visual inputs in the main experiments, and could this experimental choice substantially simplify the cross-modal alignment problem compared with realistic multimodal inputs?

**建议动作**：为何主实验用 blank images（与 R1.4/R3.14 同源）

**回复（待填）**：

```

```

#### R3.14 — 需补实验

> Could the authors repeat the key experiments using real image–text pairs to determine whether the observed rank transition and \(\Gamma\)-based allocation persist when meaningful visual information is present?

**建议动作**：用真实图文对重复关键实验（与 R1.4 同源）

**回复（待填）**：

```

```

#### R3.15 — 需补证据

> The alignment energy is defined as the mean squared distance between visual and language hidden states; what evidence demonstrates that this quantity is sufficiently correlated with actual downstream multimodal task performance?

**建议动作**：alignment energy 与真实下游表现的相关性（与 R1.3/R2.3/R3.16 同源）

**回复（待填）**：

```

```

#### R3.16 — 需补实验

> Could the authors report downstream task metrics such as instruction-following, visual question answering, or retrieval performance to establish that minimizing alignment degradation also improves practical model performance?

**建议动作**：报告下游指标（指令跟随 / VQA / 检索）（与 R2.3/R3.15 同源）

**回复（待填）**：

```

```

#### R3.17 — 需补实验/改表述

> The reported critical rank \(r_c\in[5,6]\) is based on only three seeds per rank; is this sample size sufficient to support such a sharp phase-transition claim, particularly given the reported environmental sensitivity?

**建议动作**：r_c ∈ [5,6] 只有 3 seeds → 样本量是否支撑敏锐相变？与 R3.19 同源

**回复（待填）**：

```

```

#### R3.18 — 需补分析

> The manuscript acknowledges that an earlier software environment produced different signs for \(r\in[5,8]\); could the authors provide a systematic reproducibility analysis across software versions, random seeds, CUDA/PyTorch versions, and hardware environments?

**建议动作**：系统可复现性分析（软件版本 / seed / CUDA / PyTorch / 硬件）

**回复（待填）**：

```

```

#### R3.19 — 需改表述

> At \(r=5\), the reported confidence interval spans both positive and negative values, while \(r=6\) remains statistically uncertain in the LLaVA three-seed analysis; can the authors justify describing the transition as a sharp and statistically established phase transition?

**建议动作**：r=5 的 CI 跨正负、r=6 统计不确定 → 敏锐相变表述须降级（与 R3.17 同源）

**回复（待填）**：

```

```

#### R3.20 — 需补统计

> The claim that \(\Gamma\)-guided allocation reduces uncertainty by 30× is based on comparing standard deviations of 27 and 808; could the authors provide additional robust measures such as confidence intervals, median absolute deviation, worst-case performance, and statistical significance for this comparison?

**建议动作**：30× 不确定度降低基于 sd 27 vs 808 → 补 CI / MAD / 最坏情况 / 显著性检验

**回复（待填）**：

```

```

#### R3.21 — 需澄清

> In the counterfactual experiment, the theory group uses \(r=4\), whereas the random group samples from \(\{4,16,32,64\}\); could the authors clarify how the comparison controls for the substantially different rank distributions and ensures an equivalent effective parameter budget?

**建议动作**：反事实实验中 Theory 组 r=4 vs Random 组 r∈{4,16,32,64} → 如何控制有效参数预算

**回复（待填）**：

```

```

#### R3.22 — 需补诊断

> The paper interprets NaN outputs at high rank as genuine representational collapse; could the authors provide additional diagnostics of the model weights, activations, gradients, or loss trajectories to distinguish representational collapse from numerical 4 instability associated with quantization, optimizer settings, or mixed precision?

**建议动作**：NaN 是表示塌缩还是数值不稳定（量化/优化器/混合精度）→ 需权重/激活/梯度/loss 轨迹诊断

**回复（待填）**：

```

```

#### R3.23 — 需补实验

> The paper uses only Alpaca and ShareGPT for dataset validation; could the authors evaluate the proposed framework on a substantially different multimodal dataset, such as visual question answering or image-captioning data, to establish that the phase transition is not specific to instruction-tuning distributions?

**建议动作**：只在 Alpaca / ShareGPT 验证 → 补一个差异大的多模态数据集（VQA 或 captioning）

**回复（待填）**：

```

```


## 回复撰写纪律（本项目铁律）

1. **每个数字都要能指名产出脚本与归档文件+字段** —— 新补的实验必须先有归档才能写进回复。
2. **不许承诺做不到的事**：若某条只能澄清、不能补实验，就明确说明并把主张降级。
3. **区分「已做/已改」与「将做」**：不得混写。
4. **全称否定需机器穷举**：凡写「无 X / 从未 X」，先给出穷举产物（列表/计数/扫描范围）。
5. **截止 2026-11-02**，逾期视为撤稿。
