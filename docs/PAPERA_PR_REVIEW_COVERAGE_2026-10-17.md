# Paper A 对 P1 审稿意见（PR-D-26-10149）的覆盖审计

> 日期：2026-10-17 22:40 ｜ 对象：`paper合/`（Paper A，68 页 NC / 49 页 Springer） ｜ 依据：`docs/reviews/P1_PR-D-26-10149_reviews.txt`
> 方法：逐条把审稿点转成"可检索的证据构造"，在 `main_nc.tex` + `sections/*.tex` 中定位；**缺失即记录缺失**。
> 复跑：`python tools/_p1182_audit_against_pr_review.py`

## 结论

14 组意见中 **12 组已实质解决**，**2 组部分解决**（见"缺口"）。整体回应水平远超"改文字"：其中三处是**主动撤回自己的证据/贡献**。

## 一、已解决（附证据）

| 审稿点 | Paper A 的处理 | 证据位置 |
|---|---|---|
| **R1-W1 / R3-1 数值不一致**（AE 点名的致命项）| `+0.079` 明确定性为"属于另一配置"；CGΔ 十二格由逐 seed JSON 复现（噪声低于组间差 80–200×）；R@1 列**逐格溯源**（6 格精确、3 格跨归档、1 格混用非严格版、5 格差 ≤0.0022），并承认 vision-only 格 `0.700` 是高分抽样（复测 0.675–0.682）| `empirical.tex`；补充 **F. Provenance** |
| **R1-W2 / R3-2 / R2-5 伪重复** | cluster-robust CR1（斜率 −1.05，SE 0.29，p=0.016）+ family-clustered bootstrap CI [−0.89,−0.62] + 混合模型（随机 dataset/backbone/config 截距）β=−0.95±0.08 + **12 折 leave-one-family-out** 样本外检验；明确"report an **association**, not a predictor" | `main_nc.tex` 摘要；`empirical.tex` |
| **R1-Q4 分层图 + 组内相关** | 每数据集 r=−0.781（Flickr, n=183）vs −0.598（COCO, n=16）；每骨干 CLIP B/32 −0.748（n=192）…；并新增 `fig:stratified`（按 dataset / model 两栏）| `empirical.tex` |
| **R1-W3 / R3-3 因果过度声称** | 噪声实验标为 **(withdrawn)**：交代 LayerNorm 被误扰动、占视觉塔注入 Frobenius 范数 **73.9%**（正对审稿人指出的相对扰动不匹配）；重做后五 seed 无稳定排序（1.90±1.83% vs 2.48±3.25%，p=0.77）；全文 **0 处** "direct causal"；保留证据改用**匹配相对扰动** ‖ΔW‖F/‖W‖F；小节改名 "…an Interpretation…, **Not** of a Fragile Tower" | `empirical.tex` 视觉脆弱小节 |
| **R1-W4 / R3-4 COCO/BLIP-1** | 写明 COCO 近随机原因（validation split 复用为 gallery ⇒ R@1=1/5000），**声明 COCO 行只作 gap 测量、不报 ODE 系数**；并**修复协议**（split 不相交 + 唯一图库 + 全 5 caption，10k 训练/3k 评估）⇒ 0.579 / 0.607±0.002 / 0.623±0.001；BLIP-1 主动交代"非 LoRA 注入而是选择性解冻 query/value"| `empirical.tex`（三处）|
| **R1-W5 / R2-5 DG-ES** | **撤掉该贡献**：全文 0 处 early stopping / DG-Guided / zero-overhead；明确"Monitoring DG and **stopping** on DG are different claims, and only the first…"；监测另有 88/94 run 证据 | `discussion.tex`；`conclusion.tex` |
| **R1-W6 学习率公平性** | "Tuning each method to its own learning rate **removes the adapter methods' apparent advantage**：LoRA 与 full-FT 一致（60.69% vs 60.87%）" | `main_nc.tex` 摘要 |
| **R2-1 标题/框架过宽** | 改名 "Adaptation Site and the Modality Gap… for PEFT of **Contrastive Dual-Encoders**" | 标题 |
| **R2-2 新颖性** | 新增 "What This Paper Adds" 小节 | `related_work.tex` |
| **R2-3 规模/多样性** | 新增两个 decoder VLM（Qwen2-VL-2B 13 seeds；LLaVA-1.5-7B）+ 221-run 目录 + COCO 全量重做 | 补充 E/G；`empirical.tex` |
| **R1-Q1 收窄一般性** | 4 处 "universal" **全为否定**（"architectural, not universal"）；**0 处** "across architectures" | 全稿 |
| **R1-Q4 表** | 221-run 实验目录表 + 配置分层对照 | 补充 A 节 |

## 二、仍有缺口（2 处，如实列出）

### 缺口 1（建议修）：R2-W4 替代解释未明说

审稿人要求承认"正则化 / 模态特定优化效应"等替代解释不能排除。现稿把 Visual Fragility 降级为 *Interpretation*、撤回了噪声线，
但**在小节 9,000 字符内检索 `alternative / cannot exclude / confound / causal / correlational` 全部 0 命中**；
真正的替代解释讨论 `discussion.tex` 也没有（局限节 6 条讲的是 ODE 近似、规模、量化、COCO 等）。

**建议**：在 Limitations 加 2 句：Visual Fragility 是对"适配位置"的解释，正则化强度与模态特定优化动力学**未被排除**，现有证据为梯度信噪比与有效秩的**相关性证据**，非因果剥离。

### 缺口 2（可选修）：R1-Q2 配置差异缺少正面对照表

审稿人要求说明"看起来相似的配置为何给出不同数字"（target modules / seeds / data splits / implementation），并建议配置对照表。
现稿已有：严格冻结隔离、补充 F 逐格溯源、`+0.079` 改判、COCO 协议修复 —— 但补充 A 的目录表**只有两列**（章节 | 实验数），
**没有**把 core / Route D / layered / strict-freezing 四组的 target modules、seed、split、pipeline 差异并列。

**建议**：补一张小表（四组 × 五列），这是 R1 最直接可验收的回应，成本约 1 段 + 1 表。

## 三、不建议再动

- R3 的"cover letter 稿号不符"属投稿事务（P1 已拒，Paper A 为新稿）；
- 语言问题：未检出重复冠词等模式，全稿已重写。

## 四、复跑入口

```powershell
python tools\_p1182_audit_against_pr_review.py
```

## 五点五、缺口已闭合（2026-10-17 23:10）

| 缺口 | 处理 | 证据 |
|---|---|---|
| **R2-W4 替代解释未明说** | 局限节新增 **Thirteenth** 条：承认正则化强度与模态特定优化动力学可能产生同一排序；明确指出保留的两条证据（梯度信噪比、有效秩变化）是**相关性**证据；并说明设计用来分离二者的噪声实验已撤回 | `discussion.tex`（局限节）|
| **R1-Q2 配置差异缺对照表** | 补充新增 **A.1 节 + Table 9（`tab:config_groups`）**，四组 × 三列：Core LoRA / Route D / Layered / Strict-freezing，逐组给出 Settings 与"为何数字不可互换" | `supplement.tex` A.1 |
| **R1-W1 `+0.079` 的根因** | 由归档**逐字段核实**：`d1_alpha64_text_r8`（Route D）与 core `alpha_64` 同为 $r=8$、$\alpha=64$、145,170,177 可训练参数，但验证损失 **2.331 vs 0.499**、R@1 **0.389 vs 0.637** ⇒ 是**退化拟合**，不是"另一种配置"。正文改判句已按此重写 | `outputs/route_d/d1_alpha64_text_r8/results.json`；`outputs/flickr30k/alpha_64/results.json`；`empirical.tex` |

**数值依据（可直接复核）**：Route D 全组 d1 +0.079 / d2 +0.183 / d3 +0.164 / d4 +0.188 / d5 +0.196；core $\alpha$ 扫描
$\alpha=4$ $-0.017$ → $\alpha=64$ $-0.081$（验证损失 0.499–0.541）。复跑脚本：`tools/_p1184_diff_disputed_runs.py`。

**重建结果**：NC **70 页**、Springer **50 页**，均 0 错误 / 0 未定义 / 0 Overfull / 0 float-too-large；
投稿包已刷新并独立编译 **70 页一致**；台账 **76/76**、主台账 **96/96**。

## 六、评审建议落实情况（2026-10-17 23:20 复核）

| 建议 | 状态 | 证据 |
|---|---|---|
| ① 局限节补替代解释 | **已落实** | `discussion.tex` Thirteenth：「Regularisation strength」/「correlational」/「not as an established mechanism」三处均命中 |
| ② 补充补配置对照表 | **已落实** | `supplement.tex` A.1 + `tab:config_groups`，四组齐全，正文 `empirical.tex` 有 `\ref` |
| ③ `+0.079` 根因改写 | **已落实** | `empirical.tex`：「degenerate fit」+「validation loss of $2.33$」 |

复核脚本：`tools/_p1182_audit_against_pr_review.py`（构造命中）、本文件五点五节（数值依据）。
