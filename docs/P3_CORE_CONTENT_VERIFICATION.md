# P3 核心内容独立核验（2026-09-26，投稿前）

> 目的：不依赖"稿件自己的审计清单"，**从源档案独立重算** P3 的核心量化断言。
> 方法：只读源 JSON → 按稿件声明的口径重算 → 与稿面数字逐条比对。
> 复跑：`python tools/_p3_recompute_counterfactual.py`、`python tools/_extract_em_fields.py`、
> `python tools/_audit_prl_package.py`；P3 自带 `paper3/paper_ieee/audit_check.py` 与 `audit_pdf.py`。

---

## 一、结论

**核心量化断言与源档案一致。稿件无需任何改动。** 共核 **28 项**（核心 12 + 反事实节 14 + 两项口径溯源），
**28 项全部通过**。

**本轮三次自我纠错（全部是我的误判，非稿件缺陷）**：
1. 误判 `:278` 的 "sample std over 15 runs" 是把记录数当有效运行数 → 稿件 `:289` 已写明 "two of fifteen runs produce NaN"，统计用 13 个有效值。
2. 误判主表的 ± 需要"改成与正文一致的口径" → 表注 `:69-73` 已写 "**population std** over 3 seeds"，正文 `:87` 写 "sample standard deviations"，**两种口径都已正确标注**。
3. 误判结论句的 "9 block-level" 无据 → 依据就在 `paper3/PAPER3_EXPLAIN.md` §4.2 的官方构成表（我先前只搜 `outputs/`，搜错了地方）。

**教训**：三次都源于**先下结论、后找依据**。正确顺序是先把稿件自身的标注与项目文档读全，再判定"缺什么"。

---

## 二、逐条核验表

| # | 稿件/封面信断言 | 源档案 | 我的独立重算 | 判定 |
|---|---|---|---|---|
| 1 | **190 runs = 181 sweep + 9 block-level** | **`paper3/PAPER3_EXPLAIN.md` §4.2 官方构成表**（190 = 86+45+30+20+9）+ `paper3/scripts/outputs/experiments/`（块级配置计数） | 86+45+30+20 = **181** ✅；块级独立配置恰为 **9**（theory·violation·uniform × 3 seeds）✅ |
| 1b | 摘要描述的运行总数 190 | 同上 | 181 + 9 = **190** ✅ |
| 2 | Theory（主表 r=4）**−108 ± 27**（sample std, n=5） | `all_results.json` → `Theory` | mean **−108.0**、sd(样本) **26.7**、n=5、0 NaN | ✅ |
| 3 | Random **+491 ± 808**（n=13，2 次 NaN） | `all_results.json` → `Random` | mean **490.8**、sd(样本) **808.1**、n=13、2 NaN | ✅ |
| 4 | Violation_r16 **+1507.8 ± 155**（n=5） | `all_results.json` → `Violation_r16` | mean **1507.8**、sd(样本) **154.7**、n=5 | ✅ |
| 5 | Violation_r32 **5/5 NaN**（完全塌缩） | `all_results.json` → `Violation_r32` | 5 次全 NaN、有效 0 | ✅ |
| 6 | **封面信**："random allocation suffers a **30× larger standard deviation** (808 vs 27)" | 同 #2/#3 | 808.1 / 26.7 = **30.2×**，四舍五入正是 **(808 vs 27)** | ✅ |
| 7 | 主表 r=16 = **+1572 ± 67** | `E2_results.json` → `E2`（name `E2_r16_s*`） | mean **+1571.5**、n=3 | ✅（均值吻合；稿件 ±67 与重算 sd 82.6 的差异见 §四注） |
| 8 | 主表 r=4 = **−105 ± 21** | `E2_results.json` → `E2` | mean **−105.2**、sd(样本) 25.8、n=3 | ✅ 均值吻合 |
| 9 | **r_c ∈ [5,6]**：r=5 安全、r=6 起受损 | `E2_results.json` → `extra`（`E2_r5/r6/r7/r8_s*`） | r=5 **−21.0**（负/safe）→ r=6 **+62.3**（转正）→ r=7 +191.5 → r=8 +311.3 | ✅ **符号翻转精确落在 5 与 6 之间** |
| 10 | "in LLaVA **but not** Qwen-VL"（架构依赖） | `outputs/c1_qwen_asymmetry.json`（4 臂 × 4 seeds） | 各臂 ΔE 为 +168 / −2340 / … **无一致的符号翻转过零行为** | ✅ 支持"Qwen 侧无相变" |
| 11 | 相位统计的显著性检验 | `outputs/phase_stats_recompute.json` | 其 `summary` 自带：**7 项检验全部复现、not_reproduced = 0**；BH-FDR 7 项、存活 0.05 的 3 项 | ✅ |
| 12 | 引用完整性 / 环境配对 / 未引用 label | —— | `audit_check.py`：环境配对全 OK、公式 7/7、定理 2/2、**未引用 label = 无**；`audit_pdf.py`：**46 项抽查缺失 0** | ✅ |

> **注（#1 的溯源与一次误判）**：`paper3/PAPER3_EXPLAIN.md` §4.2 给出官方构成表
> **190 = 86 + 45 + 30 + 20 + 9**（LLaVA 扫描 86 / Qwen 扫描 45 / 反事实 30 / 样本量扫描 20 / Qwen 块级分配 9）。
> 前三项 + 样本量扫描 = **86+45+30+20 = 181** → 与稿件 "181 sweep runs" 逐字对应；末项 **9** = Qwen 块级配置
> （theory / violation / uniform × 3 seeds），脚本 `tools/_p3_verify_run_count.py` 从档案侧独立确认为 **9 个独立配置**
> （每个另存 `v2`/`blankimg_v3` 版本快照，故文件数为 27/64）。
>
> ⚠️ **我最初判它"未核实"是误判**：当时只搜了 `outputs/` 与 `paper3/scripts/outputs/experiments/`，
> 且误把 LLaVA 的 `all_results.json`（30 条记录）当成块级反事实的档案。**依据其实在项目自带说明文档里**——
> 教训：判定"缺依据"之前，先把项目文档读全。

---

## 三、核验方法（可复跑）

| 手段 | 命令 | 覆盖 |
|---|---|---|
| 反事实批独立重算 | `python tools/_p3_recompute_counterfactual.py` | ΔE 的 mean / sd(样本·总体) / NaN / 30× 比值 |
| EM 表单字段提取 | `python tools/_extract_em_fields.py` | 标题、摘要（197 词 ≤300）、关键词 |
| 投稿包审核 | `python tools/_audit_prl_package.py` | 18 项：源↔PDF 文本等价、声明顺序、边界 |
| 稿件自带审计 | `python paper3/paper_ieee/audit_check.py`、`audit_pdf.py` | 环境配对、label 引用、46 项数字抽查 |
| 相位聚合对照 | `python tools/audit_phase_aggregate.py`、`audit_key_numbers.py` | 各批次 rank vs ΔE 的交叉对照 |

**口径约定**：稿件声明 sample std，故一律按 **ddof=1** 对照；ΔE 由每次运行的 `E` 序列首末差得到
（`E` 是逐 epoch 列表，非标量——直接读 `dE` 字段会得到 `None`，这是初次尝试失败的原因）。

---

## 四、反事实节（experiments.tex:277–297）的**逐项**重算 —— 14/14 吻合

> 本轮我先怀疑这里有一处"把 15 次记录当成 15 次有效运行"的错误，**核查后证明是我的误判**：
> 稿件在 `experiments.tex:289` 明写 "**two of fifteen runs** produce NaN collapse (one at $r{=}32$, one at $r{=}64$)"，
> 即**已交代 15 次中 2 次 NaN**，统计量按 13 个有效值计算——**完全自洽，无缺陷**。
> （记录此误判过程，以免日后再"发现"同一个假问题。）

| 稿件断言（行号） | 重算值 | 判定 |
|---|---|---|
| 总运行 15 次；其中 2 次 NaN；位于 $r{=}32$ 与 $r{=}64$（:289–290） | 15 条记录、2 条 NaN、rank = **[32, 64]** | ✅ |
| $\sigma_{\text{Random}} = 808$（:288） | **808.1** | ✅ |
| $\sigma_{\text{Theory}} = 27$（:286） | **26.7** | ✅ |
| "30× larger"（:279） | **30.23×** | ✅ |
| CV(Random) $=1.65$（:288） | **1.65** | ✅ |
| CV(Theory) $=0.25$（:286） | **0.25** | ✅ |
| median(Random) $=-92$（:288） | **−92.0** | ✅ |
| mean(Random) $=+491$（:289） | **+490.8** | ✅ |
| 最差 Random $=+1659$（:296） | **+1659.0** | ✅ |
| "driven by runs exceeding $+1000$"（:289） | 5 条 > +1000 | ✅ |
| 五个 Theory 种子全部改善（:295） | 全部为负（max **−76.0**） | ✅ |
| Theory $-108 \pm 27$、Violation $r{=}16$ $+1508\pm155$、$r{=}32$ 全 NaN（:277–282） | **−108.0 ± 26.7**、**+1507.8 ± 154.7**、5/5 NaN | ✅ |

**注**："$+1508$" 是 $+1507.8$ 的四舍五入，全稿一致（`appendix.tex:132`、`experiments.tex:149/272/281/305` 同写法），非笔误。

---

## 五、另一处"看似矛盾"（已定性为协议差异，非错误）

工具 `tools/audit_phase_aggregate.py` 从 `outputs/phase_stats_recompute.json` 重算得到
**rank=16 → +950.7 ± 756.2**，而稿件主表写 **+1572 ± 67**。**两者不矛盾**，原因：

| 批次 | 档案标记 | 用途 | r=16 的值 |
|---|---|---|---|
| `sweep` 批 | `name = sweep_r*_s*` | **全 rank 扫描**（r=4…20 连续），用于"增长率/单调性"叙述 | **+950.7**（3 seeds） |
| `E2` 批 | `name = E2_r*_s*` | **主表的 reference protocol**（r=4/16/32/64） | **+1571.5** |
| `extra` 批 | `name = E2_r*_s*` | r=5/6/7/8 加密扫描，用于确定 $r_c$ | r=5 −21.0、r=6 +62.3 |

三批**协议与 rank 网格不同**，同一 rank 数值本就不同。稿件主表引用 `E2` 批，"增长率"叙述引用 `sweep` 批——**各自内部自洽**。
审核脚本打印的 `[paper +1572±67]` 是它自加的对照注释，提示"该聚合口径与主表不是同一批"。

### ~~仍需说明的一处口径细节~~ → ✅ 已查清（此前的怀疑不成立）

**主表 r=16 的 $\pm 67$** 一度让我以为"与重算不符"。**查清后：稿件表注 `experiments.tex:69-73` 明确写
"Mean $\pm$ **population std** over 3 seeds"** —— 按**总体 sd**（ddof=0）重算即得 **67.5 → 67**（精确吻合），
r=4 同理 **21.1 → 21**。我先前用样本 sd（82.6 / 25.8）去比，才产生"对不上"的错觉。

**sd 口径总表（供复核者使用，避免假警报）**：

| 位置 | 稿件声明的口径 | 重算（正确口径） | 若用错口径会得到 |
|---|---|---|---|
| 主表 `tab:phase`（3 seeds） | **population std**（表注已写） | 21.1 → **21**；67.5 → **67** | 样本 sd 25.8 / 82.6（→ 假"对不上"） |
| 反事实正文（5 / 13–15 runs） | **sample std**（正文已写） | 26.7 → **27**；808.1 → **808**；154.7 → **155** | 总体 sd 23.9 / 776.4 / 138.3（→ 假"对不上"） |
| `:87` 显著性检验 | **sample standard deviations**（正文已写） | — | — |
| `tab:sample` | 无 ±（只有均值） | — | — |

**→ 无需任何改动，也无需"补齐种子"**：均值与 ± 都与源档案一致，口径已由稿件显式声明。

---

## 六、核验结论：28/28 通过，无待核项

| 项 | 结论 | 依据 |
|---|---|---|
| **"9 block-level counterfactual runs"** | ✅ **确认** | `paper3/PAPER3_EXPLAIN.md` §4.2 官方构成表：**190 = 86 + 45 + 30 + 20 + 9**（LLaVA 扫描 86 / Qwen 扫描 45 / 反事实 30 / 样本量扫描 20 / **Qwen 块级分配 9 = theory·violation·uniform × 3 seeds**）。**86+45+30+20 = 181**，与稿件 "181 sweep runs" 逐字对应；复跑脚本 `tools/_p3_verify_run_count.py` 亦确认块级配置恰为 **9 个独立配置**（每个另存 3 个版本快照，故文件数 27/64） |
| **主表 ± 的口径** | ✅ **已正确标注** | 表注 `experiments.tex:69-73` 原文 "Mean $\pm$ **population std** over 3 seeds"。重算印证：r=4 → 总体 sd **21.1** → 稿面 **21**；r=16 → 总体 sd **67.5** → 稿面 **67**（若用样本 sd 会是 25.8 / 82.6，与稿面不符） |
| **反事实正文 ± 的口径** | ✅ **已正确标注** | `:277-278` 原文 "mean $\pm$ **sample std** over 5 seeds"、"**sample std** over 15 runs"；重算印证 26.7→27、808.1→808。`:87` 的显著性检验亦声明 "two-sided; **sample standard deviations**" |
| `tab:sample` 是否需口径说明 | ✅ 不需要 | 该表只列均值、**不含 ±** |

**两种口径并存但有据**：主表用总体 sd（与 `σ` 记法一致），反事实节用样本 sd（n 小、更保守）。
两者都在各自位置显式声明，**属规范写法，无需统一**。
附：反事实的关键比值在两种口径下都是 30×（样本 **30.23×**、总体 32.47×），结论对口径不敏感。

> ⚠️ 我**没有**改动稿件任何字句——三轮核查后确认**没有需要改的地方**。
> 若后续仍需改动，脚本 `tools/_p3_sd_convention_audit.py` 与 `tools/_p3_verify_run_count.py` 可复跑复核。
