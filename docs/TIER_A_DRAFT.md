# Tier A 补强执行记录与论文改写草案（paper_ap3）

目的：把 paper_ap3 的 16 条局限里**本地可完成**的部分做成实测证据，并据此改写 §6/§7 的措辞。
约束：所有数字必须来自真实 JSON；GPU 严格串行；不使用云端。

## 0. 运行编排

| 步骤 | 脚本 | 产物 |
|---|---|---|
| 总驱动（GPU 串行） | `tools/ap3_tier_a_runall.py` | `outputs/tier_a_runall_status.json` |
| LLaVA 电池（**34 run**，~25–30 min/run ≈ 14 h） | `tools/ap3_tier_a_battery.py` | `paper3/scripts/outputs/experiments/verify_*.json`，日志 `paper3/scripts/logs/tier_a/` |

电池构成（2026-09-12 扩编，全部显式 `--epochs 3`，文件名带标签防覆盖）：
A5 策略 10 run（uniform/exp/greedy × seeds {42,123,456}，expnorm/deepavoid × {42,123}）→
A4 种子族 10 run（r∈{5,6} × seeds {7,17,27,37,47}）→ A2 门控 4 run（image/text × r∈{5,6}）→
A6 投影器 3 run（proj-only r4 / proj16+llm2 / proj2+llm16）→
A7 三轴 6 run（α=32、仅 q、batch=4，各在 r∈{5,6}）→ A8 亚临界 10-epoch 1 run。
| A1 跨 PEFT Γ 排序 | `tools/clip_peft_gamma_ordering.py` | `outputs/clip_peft_gamma_ordering.json` |
| A3 跨批 Γ + 分层 bootstrap | `tools/llava_gamma_batch_ci.py` | `outputs/llava_gamma_batches.json` |
| A8 二阶 ODE | `tools/clip_llava_second_order_ode.py` | `outputs/llava_second_order_ode.json` |
| A9 E 族选择 | `tools/ap3_e_family_selection.py` | `outputs/e_family_selection.json` |
| A4 统计复算 + BH-FDR | `tools/ap3_phase_stats_recompute.py` | `outputs/phase_stats_recompute.json` |
| 电池结果汇总（A2/A5/A6/A7/A10） | `tools/ap3_tier_a_analysis.py` | `outputs/tier_a_analysis.json` |

`run_training.py` 新增开关（全部写入 JSON，且文件名带标签，绝不覆盖旧结果）：
`--grad-mask {none,image,text}`、`--lora-alpha`、`--attn-targets {qkvo,q,qv,qo,none}`、
`--batch-size`、`--proj-rank`、`--data-offset`、`--block-config {uniform,exp,greedy,expnorm,deepavoid}`、
每 epoch 的路由梯度范数 `grad_norms{vision,proj,llm}`。

### 分配策略（全部与 exp 同预算，除非注明）

| 策略 | shallow/mid/deep | rank-layers | 依据 |
|---|---|---|---|
| uniform | 4/4/4 | 128 | 参考基线（全层 r=4） |
| exp | 9/1/6 | 136 | 适配器子空间 β\*=1/σ(\|Γ\|) 份额（论文已报告） |
| greedy | 16/1/1 | **152** | 角点解（被排块 r≥1 下限，+19% 开销，论文已披露） |
| expnorm | **11/1/4** | 136 | **按块参数量归一化**后的 β\* 份额：\|Γ\|/层数 = 202/545/341，σ=141，β\*=0.0071 → 份额 0.685/0.060/0.255，预算 136 下最优整数实现（与目标份额 L1 误差 0.056） |
| deepavoid | **4/6/1** | 136 | raw 全参数化层剖面的 β\* 份额（层均 \|Γ\| = 0.31/0.13/4.09，deep 最耦合）→ 把容量从 deep 移开 |

> 这两条新策略的 rank 向量由 `run_training.py` 注释中的推导固定，且写入 JSON，可复核。

## 1. 已完成（离线，无需 GPU）

**A4 统计面（已复现论文全部 7 项检验）**：`outputs/phase_stats_recompute.json`
数据族（论文族 = tab:phase 的三个批次，定义写死在脚本里）：r4/r16 ← `E2`；r5–r8 ← `extra`；r20/NaN ← `sweep`。

| 检验 | 复算 p | 论文 p | BH-q |
|---|---|---|---|
| pooled r{4,5} vs r{6,7}（Welch） | 0.00144 | 0.0014 | 0.0101 |
| 第二数据集 Welch r5 vs r6 | 0.01142 | 0.011 | 0.0307 |
| 第二数据集 r6 单样本 t | 0.01315 | 0.013 | 0.0307 |
| 配置级排序 6/6（精确二项） | 0.03125 | 0.031 | 0.0547 |
| LLaVA r6 单样本 t | 0.16993 | 0.17 | — |
| LLaVA r5 单样本 t | 0.37478 | 0.37 | — |
| 第二数据集 r5 单样本 t | 0.91593 | 0.92 | — |

→ **7/7 复现**；FDR≤0.05 存活 3 项，配置级排序 q=0.0547（仅 ≤0.10）——与论文叙述一致。

**A8 二阶 ODE（初版，仅 r5/r6 轨迹）**：M0（论文一阶）mean R²=0.736；M1（一阶+线性漂移）0.982；
M2（阻尼振荡）0.997；AICc 选 M1；"阻尼比" ζ<0（幅度增长，非衰减）；M0 在最小值之后的最大残差 ≈ 836（r5）/702（r6）。
→ 待 r4（亚临界，A8 run）落地后补齐"单调段 M0 足够、回弹段需二阶项"的对照。

## 2. 待 GPU 结果落地后填写（占位符一律用实测值替换）

### A2 梯度通路门控（局限 11：机制从"解释性"到"干预性"）
在首个 LLM 解码层入口按 token 位置切断梯度（前向不变、仅梯度门控），三条件 × r∈{5,6}：
`none`（参考）/ `image`（图像位置梯度被切断）/ `text`（语言位置梯度被切断），并记录路由梯度范数作为"门控是否生效"的硬校验。
预期写入 §6 新小节：交叉是否在 image 门控下消失、在 text 门控下保留；`image` 门控下 ‖g_vision‖≈0 作为干预生效证据。
参考基线（已验证分析管线）：参考协议 r5=−1.33 → r6=+66.83（Δ=+68.16，有交叉）；`--lang-only` r5=−34.5 → r6=−45.5（Δ=−11.0，无交叉）。

### A5 分配策略多种子 + 两个新策略（局限 15）
把"端到端指数分配不具保护性"从 **n=1** 提升到多种子，并新增两条同预算策略（expnorm/deepavoid）。
写入：更新 `tab:policy`（各策略 mean±std、seed 列表、与 uniform 的 Welch 检验、预算与可训练参数量）。

### A6 投影器/LLM 不对称秩（局限 2）
`proj_only_r4`（仅投影器适配器）/ `proj_hi16+llm_lo2` / `proj_lo2+llm_hi16` 三配置 + 已有 `uniform+proj r4` 探查（−85.5 vs uniform −79.0）。
写入：$\Delta E$ 与可训练参数分解，判定"投影器容量近惰性"是否在不对称配置下成立。

### A7 α 消融（局限 14）
α=32 vs 默认 α=2r 在 r5/r6 的 $\Delta E$。
（原计划的 target-modules/batch 两轴因单 run ≈30 min 被削减；如时间允许用 `--stage A7` 追加。）

### A10 ‖g_vision‖ 随 rank（附录 future work 项）
参考协议各 rank 的末 epoch 路由梯度范数 + Spearman(rank, ‖g_v‖) → 判定"梯度饱和"是否在解码器侧成立。

### A1 跨 PEFT 参数化 Γ 排序（局限 3）
CLIP 上四种参数化（full / LoRA r=8 / Adapter 64 / BitFit）在同一 E 与同一任务梯度下的分块 Γ：
块序 Spearman、与 full 的逐块耦合偏差 ε_k（中位数），据此把定理的"正交子群假设"改写为
"在四种非正交参数化下排序实测一致（ρ=…），偏差有界（ε_median=…）"。

### A3 跨批 Γ + 分层 bootstrap（局限 9）
6 个独立样本窗口 × 16 样本；逐块跨批 CI、分层 bootstrap CI、块序 argmax/argmin 频率、批间 Spearman、
**分配向量稳定性**（β\* 份额在同预算 136 下的 rank 向量及 bootstrap 一致率；含按参数量归一化变体）。

### A9 E 族选择（局限 7/13）
5 条策略的实测 ΔE × 6 种 E 实例化的三种风险泛函（P1 线性风险 / P2 容量分散 / P3 最差块）→
Spearman 预测力排序，选"最能预测实测损伤"的实例化作为操作性准则。

### A4 种子族增强（局限 12）
新增 5 个独立种子 × r∈{5,6}（当前环境参考协议，E0=3921 批次）→ 独立复现族的 n 由 3 提升到 6：
r5/r6 均值±CI、单样本 t、Welch、逐种子排序计数；重跑 BH-FDR（论文族不变，新增独立复现族单独报告）。

## 3. 局限逐条改写计划

| # | 现状 | Tier A 后 |
|---|---|---|
| 1 | 7B 块级控制未测（2B 已测） | LLaVA 侧块级/投影器控制由 A6 补上；Qwen-7B 仍为云端项 → 保留但收窄 |
| 2 | 投影器/LLM 不对称秩未测 | **A6 关闭** |
| 3 | 定理假设正交子群 | **A1 量化**（四参数化排序不变 + 偏差上界），理论假设仍保留但不再"未验证" |
| 4 | 目标任务（长文本/零样本分类） | 仍开放（需新评测线）→ 保留 |
| 5 | 连续时间误差界缺失 | **A8 部分闭合**（回弹段用二阶/漂移项建模并给 R²、AICc）；形式误差界仍缺 |
| 6 | 跨环境 r_c | 不变（已有 tf457 对照） |
| 7 | 哪个 E 族"正确"未定 | **A9 给操作性准则**（以实测 ΔE 预测力选定） |
| 8 | 双塔/解码器协议不匹配 | 仍开放（云端项）→ 保留 |
| 9 | Γ 单批估计 | **A3 关闭**（批级 CI + 分层 bootstrap + 分配稳定性） |
| 10 | >7B 绝对成本未测 | 仍开放（云端项）→ 保留；A10 只补梯度饱和 |
| 11 | 机制仅解释性、未 token 级隔离 | **A2 关闭**（梯度通路门控干预 + 范数校验） |
| 12 | 多重比较/检验功效 | **A4 增强**（独立复现族 n=3→6，BH-FDR 复算且脚本可复现） |
| 13 | 解码器 E 池化位置 | **A9 部分闭合**（按预测力选择而非"报告后不管"） |
| 14 | 超参消融不足 | **A7 追加 α 轴**；target-modules/batch 视时间追加 |
| 15 | 端到端负结果 n=1 | **A5 多种子 + 2 新策略** |
| 16 | 符号是预算相对量 | **A8 补 r4 亚临界对照 + 端态值** |

## 5. 可直接粘贴的 LaTeX 片段（数值已定稿的部分）

### 5.1 §6 统计段落（替换 `06_crossarch.tex` 中 "Statistical evidence for the critical point." 段）
> 现有文字报告 LLaVA r5 p=0.37 / r6 p=0.17 等手工值；下面改写为脚本产物 + 复现声明，数值不变（7/7 复现），
> 并补一句"全部 p/q 由 `tools/ap3_phase_stats_recompute.py` 从归档批次复算"。

```latex
\textbf{Statistical evidence for the critical point.} All $p$-values below are
produced by a single reproducibility script from the archived per-seed batches
($\texttt{E2}/\texttt{extra}$ for LLaVA, the second-dataset table, and the
sample-size sweep). At $r=5$, $\Delta E$ is indistinguishable from zero on both
datasets (LLaVA: $-21$, $p=0.375$; second dataset: $+2.7$, $p=0.916$)---the
signature of a critical boundary---while at $r=6$ it is positive on both
(second dataset: $p=0.013$; LLaVA: $+62$, $p=0.170$). The increase across the
crossing is significant: second-dataset Welch $t=4.81$ ($p=0.011$); pooled
$r\in\{4,5\}$ vs.\ $r\in\{6,7\}$ on the phase-table batches, $n=6$ each, gives
$t=4.64$ ($p=0.0014$). The ordering $\Delta E(r{=}6)>\Delta E(r{=}5)$ holds in
all six configurations (four sample sizes, the phase table, and the second
dataset); exact two-sided binomial $p=0.031$.
```

### 5.2 §7 局限 12（多重比较）——把手工 p 值改为脚本产物
```latex
Twelfth, multiple-comparison awareness: \dots\ We now report the
Benjamini--Hochberg false-discovery-rate correction over the complete family of
seven tests, recomputed by a reproducibility script from the archived batches:
the pooled-$t$ ($p=0.0014$, $q=0.010$), the second-dataset Welch test
($p=0.011$, $q=0.031$) and the second-dataset $r{=}6$ one-sample test
($p=0.013$, $q=0.031$) survive at FDR $\le 0.05$; the configuration-level
ordering test ($p=0.031$, $q=0.055$) survives only at FDR $\le 0.10$; the LLaVA
$r{=}5$/$r{=}6$ single-rank tests ($p=0.375$, $0.170$) do not survive either
level. The full table and the test definitions are produced by
\texttt{phase\_stats\_recompute} in the released analysis code.
```

### 5.3 §7 局限 16 / §3b（回弹段的二阶修正）——A8 待 r4 落地后填最终数
```latex
Relatedly, the first-order ODE of Section~\ref{sec:special} is fitted on monotone
dual-encoder trajectories; the decoder rebound trajectories are non-monotone.
Refitting the three candidate models on the ten-epoch decoder trajectories shows
a first-order form reaches only $R^2 = 0.74$ on average, a first-order form with
a linear drift term $R^2 = 0.98$, and a damped-oscillator (second-order) form
$R^2 = 1.00$ with a negative damping ratio (growing oscillation), i.e.\ the
rebound requires the second-order term that the paper's ODE omits
(\texttt{llava\_second\_order\_ode} in the released code).
```

### 5.4 待填（依赖电池）
A2 门控干预段、A5 多种子策略表、A6 不对称秩段、A7 α 段、A10 梯度饱和段、A1 参数化不变性段、
A3 跨批 CI 段、A9 E 族选择段 —— 数值落地后按 §2 的模板写入对应小节。


1. `pdflatex → bibtex → pdflatex ×2`：0 error / 0 undefined / 0 multiply-defined；
2. `python tools/audit_mechanics.py`：未引用 label = 0、无标签引用 = 0；
3. `pdftotext -bbox` + `tools/clip_scan_overflow.py`：越界词 = 0；
4. `tools/audit_fix_regression2.py`（32 项）+ 新脚本产物编号自检；
5. 记录页数与摘要词数（摘要不得超 250 词）；
6. 推送：worktree → `origin/main`（commit message 写清 A1–A10 的实测结论）。

## 6. 执行结果（2026-09-13 收口）

全部 Tier A 项已执行完毕，数字均落在 `outputs/` 的 JSON 中并已写入论文；逐条对应关系如下：

| 项 | 结果文件 | 论文落点 | 结论 |
|---|---|---|---|
| A1 跨参数化 | `clip_peft_gamma_ordering.json` + `clip_a1_parametrization_summary.json` | §6 "Invariance across non-orthogonal parameterizations" | 三 PEFT 块序完全一致；编码器块序与全参一致 |
| A2 梯度门控 | `tier_a_analysis.json::A2_gradmask` | §6 `sec:gradmask` + `tab:gradmask` | r6 损伤 79% 由图像通路承载 |
| A3 跨批 Γ | `llava_gamma_batches.json` | §6 "Cross-batch stability of Γ…" | 排序稳定（6/6 argmax）但份额平坦（10%） |
| A4 种子族 | `phase_stats_recompute.json` | §6 统计段 + 局限 12 | r6 p=3.5e-4（8/8 正），复现族两项 q=7e-4 |
| A5 策略多种子 | `tier_a_analysis.json::A5_policies` | §6 `tab:policy` + 段落 + 局限 15 | 四臂全部劣于基线（p≤0.032） |
| A6 不对称秩 | `tier_a_analysis.json::A6_projector` | §6 "Asymmetric projector/LLM rank" | LLM 秩主导（−128 vs +1700） |
| A7 三轴 | `tier_a_analysis.json::A7_alpha` | §6 "Scaling-factor and target-module axes" | α 反转序、q-only 消交叉、batch 轴 OOM |
| A8 二阶 ODE | `llava_second_order_ode.json` | §6 10-epoch 小节 + 局限 16 | 一阶被拒（R²=0.73）；r4 亦崩溃 |
| A9 E 族选择 | `e_family_selection.json` | 局限 7/13 | 本样本量无法用预测力选定（ρ=0.32, p=0.60） |
| A10 梯度饱和 | `tier_a_analysis.json::A10_gradnorm` | §7 ‖g_v‖ 句 | 关键区间无饱和（ρ=0.4） |

**仍未完成/不可完成**（保持不变）：Qwen-7B 块级控制（云端项）、>7B 绝对成本（云端项）、双塔/解码器协议统一（云端项）、长文本生成与零样本分类作为目标任务、batch>2 的批大小轴（8 GB 设备 OOM）。

**🔟 A4 收口（2026-09-13）：每 rank 扩到 10 个独立种子**——在 8 种子基础上补跑 s57/s67（r=5/6 各 2 个 run，共 4 run ≈1.9 h），复现族统计更新为：**r=5 −34.7（95% CI [−66.5,−2.9]，p=0.036，2/10 为正）**；**r=6 +69.9（[+49.3,+90.5]，p=3×10⁻⁵，10/10 为正）**；两 rank **Welch t=−6.24，p=10⁻⁵**；逐种子排序 **9/10（精确二项 p=0.021）**。复现族自身的 BH-FDR 现在 **四项全部在 FDR≤0.05 存活**（Welch q<10⁻⁴、r6 q=10⁻⁴、排序 q=0.029、r5 q=0.036）。论文 §6 统计段、§6 A2 段参考均值、局限 12 已同步更新并重编译（79 页、0 错误、摘要 248 词）；推送 `8faa115 → 42e6de7`（origin/main）。
