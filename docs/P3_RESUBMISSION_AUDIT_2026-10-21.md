# P3 改投审计（2026-10-21）

> 新稿号：**`PRLETTERS-D-26-02671`**（Pattern Recognition Letters，**Submitted to Journal**，2026-10-21）。
> 前稿：`PRLETTERS-D-26-02378R1`（2026-10-21 拒稿）。
> 本文件回答：**R1 审稿意见与拒稿回信提出的问题，是否都已经在改投版里解决**。

## 一、提交事实

| 字段 | 值 |
|---|---|
| 新稿号 | `PRLETTERS-D-26-02671` |
| 标题 | Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry: Identifiability, Negative Results, and Protocol Dependence |
| 投稿日期 | 2026-10-21 |
| 状态 | **Submitted to Journal** |
| 投稿包 | `SUBMISSION/P3_PRL_resubmission/`（Manuscript 10 页 + Supplementary 8 页 + CoverLetter 2 页 + TitlePage 1 页 + Highlights 1 页 + AuthorshipConfirmation 1 页 + LaTeXSource.zip）|
| 数据 DOI | `10.5281/zenodo.23523263`（v2.2，正文/EM 字段/包内 Manuscript 一致）|
| 文件命名 | 上传文件名全部无下划线 |
| 审计脚本 | `tools/_p1494_p3_submission_audit.py` → `outputs/analysis/p3_submission_audit.json` |

## 二、R1 预期意见 → 改投版的处理 → 状态

| # | R1 预期意见 | 改投版处理 | 证据 | 状态 |
|---|---|---|---|---|
| 1 | 分配不比随机好，方法失败 | 把负结果作为正文结论；报告同 seed/rank 配对的 +11.5（CI [6.8,16.2]）；S17 明确列为"not supported" | 正文 §V + S17 `tab:claims` | ✅ 已处理 |
| 2 | 临界秩 r_c∈[5,6] 借用别的 family | 5 seeds/rank：r5 −23.0±22.3 vs r6 +65.5±38.5，精确置换 **p=0.008**；补充 S16 给出协议窗口；结论明确"属于协议" | S14、S16、conclusion | ✅ 已处理 |
| 3 | AdaLoRA 更好、比较不公平 | 正文如实引用 AdaLoRA 的 −1468.15/−757.30，并称其在指标上胜出；S17 把"AdaLoRA 更差"列为 not supported | 正文 §V + S17 | ✅ 已处理 |
| 4 | 迁移只在 CLIP 内部验证 | 目标为 LLaVA-1.5-7B 与 Qwen2-VL-7B；本地 Qwen2-VL-2B 仅作 boundary 观察；范围句写明 | 正文 §IV + 补充 | ✅ 已处理 |
| 5 | matched loss 下 uniform 更好 | 正文原样报告 +5968 vs +2842，不再声称胜出；S17 标记 | 正文 §V + S17 | ✅ 已处理 |
| 6 | 10 页压缩丢失细节 | 补充材料 8 页（S1–S17）+ 公开仓库完整版/逐 run 记录 | Supplementary、数据声明 | ✅ 已处理 |
| 7 | 这是工程不是贡献 | 贡献重述为"表征定理 + 负结果边界"；标题副标题加入 Identifiability / Negative Results / Protocol Dependence | 标题、摘要、§V | ✅ 已处理 |
| 8 | 为什么信本地 CLIP proxy | 不声称 proxy 结论；正文说明本地控制只作 boundary，不作 LLaVA 协议验证 | 正文 §V/S10 | ✅ 已处理 |

## 三、拒稿回信（AE 一句话）→ 改投版的处理

| AE 指出的类别 | 具体措施 | 证据 |
|---|---|---|
| **technical choice 的 soundness**：blank-image 协议 | 真实图像对照数字写入 conclusion（+83.0 vs −7.5；+66.5 vs −39.5，r=5/6），并明确"crossing 属于测量协议" | 正文 conclusion + S7 |
| **technical choice**：可加性假设 (R3′) | S17 明确写为**假设**并列为 untested；不再当作推导结果 | S17 `tab:claims` |
| **interpretation**：结果解释 | claim-status 表逐条区分 supported / not supported / boundary；负结果前置 | S17 |
| **统计可信度** | 5 seeds/rank + 精确置换 p=0.008（最小可达）；S14 逐 seed 表 | S14 |
| **可复现性** | 删除 "code upon request"，改为公开仓库 + 版本 DOI；S13 provenance 附录 | conclusion + S13 |

## 四、本地可验证的提交前检查（全部通过）

- 正文 10 页，0 错、0 overfull；补充 8 页，0 错；`audit_check`、`audit_pdf` 均 **0 hard / 0 warn**；
- 正文/EM 字段/包内 PDF 的 DOI 均为 `10.5281/zenodo.23523263`，旧 v1.0 DOI 已不出现；
- 标题副标题、真实图像数字、S14/S16/S17、provenance S13 均在 PDF 文本中；
- 上传文件名无下划线；Authorship Confirmation 日期 2026-10-21、姓名×2、None×2；
- A23 verify / Commentary final check / provenance gate / frozen hashes / staged 包检查均通过（见 `final_verification.json`）。

## 五、仍未解决 / 无法本地确认的（如实列出）

1. **审稿意见原文始终未取得**（只在 EM 平台）——上表是基于 R1 预判清单与 AE 那句话的映射；若审稿人另有具体技术点，需要原文才能逐条确认。
2. **可加性 (R3′) 未被实测**：S17 已如实标为 untested，没有做"违反可加性时的误差测量"。
3. **协议窗口只完成 n=12**：n=64 的 r=5 运行因单 run 超过 95 min 被中断；S16 只含 12 与默认 20 两个窗口。
4. **AdaLoRA 未重跑**：引用的是归档结果，不是本轮独立复跑。
5. **Qwen2-VL-7B 的 crossing 未复现**：只有 2B 本地 boundary 观察；这是论文已声明的范围限制。
6. **EM 侧上传文件**：本地包已核对；EM 上实际替换/上传的文件需你在提交页复核（尤其重传后的 `Manuscript.pdf` 是否含 v2.2 DOI）。

## 六、结论

**可以本地确认的部分已全部解决**：R1 的 8 条预判意见与 AE 指出的两类问题，在改投版里都有对应文字/证据/负结果声明，且门禁全过、DOI/命名/作者声明一致。
**不能确认的部分**是"审稿人真正的具体意见是否条条命中"——因为原文未取得；以及第 5 节列出的 3 个实验性缺口（R3′ 实测、n=64 窗口、AdaLoRA 重跑）。
若需要把这三项补上，属于**再下一轮加固**，不影响当前已投版本。

## 七、按 R1 真实审稿意见重审（2026-10-21 晚；更正）

**更正**：本文件第二节原按"预判清单"写；实际上 **R1 的完整审稿意见、我们的 44 KB 逐条回复、以及 10 页修订稿
（`CORRECTED_2026-10-15/`）都在归档里**——先前"审稿意见原文未取得"只适用于**拒稿通知**（它没有附新的审稿报告）。

来源文件（`SUBMISSION/_archive/P3_PRL_rejected_2026-10-21/`）：

| 文件 | 内容 |
|---|---|
| `reviews/PRLETTERS-D-26-02378-reviews.pdf` | 三位审稿人报告原件 |
| `reviews/PRL Revison.txt` | R1 决定信（Revise，2026-09-30，截止 2026-11-02）|
| `evidence/p3_reviews_structured.json` | 33 条意见结构化版（R1.1–R3.23）|
| `response/P3_RESPONSE_LETTER.md` | 44 KB 逐条回复（11 项主要改动，含 5 处反向修改/撤稿）|
| `CORRECTED_2026-10-15/` | R1 修订稿（10 页 + 6 页补充）|

**逐条状态**（33 条）：✅ **25 条已实质处理**；⚠️ **8 条部分处理/明确声明为限制**；无一条被忽略。

| 状态 | 意见 ID | 说明 / 在改投版中的位置 |
|---|---|---|
| ✅ | R1.1 R1.2 R1.3 R1.5 R2.1 R2.2 R2.4 R2.5 R3.1 R3.2 R3.3 R3.4 R3.6 R3.7 R3.8 R3.10 R3.11 R3.12 R3.13 R3.14 R3.15 R3.17 R3.19 R3.20 R3.21 | 见 `P3_RESPONSE_LETTER.md` 对应条；R1.5 的 R3′ 公理、R2.2 的逐块分配实验、R1.3 的下游检索反例、R3.12 的逐块 Γ 表、R3.17/R3.19 的统计降级均在正文/补充中可检索到 |
| ⚠️ | **R1.4** | 未补"更新的 VLM 家族"；改为真实图文对复跑 + Qwen 边界 + 范围声明 |
| ⚠️ | **R2.3 / R3.16** | 下游只补了 CLIP 检索 `R@1`；VQA/captioning 任务指标未做 |
| ⚠️ | **R3.5** | Hessian 项**未测量**，已在论文中明确声明该限制 |
| ⚠️ | **R3.9** | 只实现并对比了 AdaLoRA；HALoRA / IGU-LoRA / ShapLoRA / NTK 仅在文中讨论，未做同预算实验 |
| ⚠️ | **R3.18** | 做了受控软件环境/seed 对比，但 CUDA/PyTorch/硬件矩阵不完整 |
| ⚠️ | **R3.22** | 报告了多重比较校正；未做权重/激活/梯度级别的 NaN 诊断 |
| ⚠️ | **R3.23** | 用真实图文对回答了"分布差异"，但未换到 VQA/captioning 数据集族 |

**改投版相对 R1 修订稿的新增**（补强，不替代 R1 回复）：
- **S14**：五 seed 统计（r=5 −23.0±22.3 vs r=6 +65.5±38.5；精确置换 **p=0.008**），直接加强 R3.17/R3.19；
- **S16**：协议窗口测量（n=12 的 r=5 −39.5 vs 默认 n=20 −10.5），部分回应 R3.18；
- **S17**：claim-status 表（把 R1.5/R2.2/R2.3/R3.5/R3.9/R3.11 的"不支持/仅边界"逐条公开）；
- 数据 DOI 改为 v2.2、文件名规则、封面信披露前稿号。

**结论**：R1 的 33 条里，**25 条已实质处理、8 条为部分处理或声明限制**；这些内容都随 R1 修订稿进入了本次改投版。
**无法确认的是 R2 阶段审稿人为何仍判"not substantially addressed"**——拒稿信没有附新报告；最可能的争议点就是上表 8 条 ⚠️
（尤其 R1.4 的新模型族、R2.3/R3.16 的任务指标、R3.9 的更多基线）。

## 八、R1 缺口补齐结果（2026-10-21 晚，改投后完成）

原始结果：`outputs/analysis/p3_gapfill_summary.json`；说明文档 `docs/P3_GAPFILL_2026-10-21.md`。

| 缺口 | 补了什么 | 结果 | 状态 |
|---|---|---|---|
| **R3.5** Hessian | LLaVA-1.5-7B 4-bit + LoRA r=5/6，有限差分测 $g^\top H g$ | 在训练学习率 $\eta=5\times10^{-5}$ 下二阶项为**一阶项的 −3.5%（sd 0.3–0.4%）**；曲率由 vision 塔主导；探测步长 $10^{-3}$ 时比例升至约 −0.7（局部性） | ✅ 已实测（结论：一阶近似在操作点成立但二阶非零，须按局部表述）|
| **R3.9** 更多基线 | NTK 分配 + Γ 分配 + uniform 的**计算对比**（CLIP），并**训练** NTK/Γ 两个显式四块 arm（LLaVA，blank-image，20 样本，3 epochs）| NTK 排序 (8/5/2/1) vs Γ (5/5/4/2) 不同；训练结果：NTK arm ΔE +396.0、Γ arm ΔE +196.5（均未改善）| ✅ NTK/Γ arm 已训练；HALoRA/IGU/Shap 仍未实现 |
| **R3.18** 环境矩阵 | 五 seed 归档 + transformers 4.57 vs 5.16 对照 | r5：n=5，−23.0±22.3，范围 [−49.0,+8.0]；r6：+65.5±38.5，[+25.5,+115.0]；跨版本 ΔE 0.0 vs −39.5（轨迹形状一致）| ⚠️ 单机单卡，硬件矩阵不可扩 |
| **R3.22** NaN 诊断 | 已有 `p3_nan_diagnostics.json` / `p3_nan_probe.json`（156 日志扫描 + 初始化 GPU 探针） | E 先 NaN 而 loss 有限 → 能量泛函在病态几何上产生非有限值，不是优化器爆炸 | ✅ 已有归档，无需新跑 |
| **R2.3/R3.16** 下游任务 | 在 marine caption 数据上训 r=5/r=6 适配器（20 样本、3 epochs），对 4 个留出样本测 BLEU-4 / token F1 / CLIP 相似度 | 三个 arm 生成完全相同：BLEU-4=0、token F1=0.1787、CLIP=0.3233 → **零结果**（20 样本适配器不改变贪婪生成）| ⚠️ 仅小规模 sanity check；VQA 未做 |
| **R3.23** 数据集族 | 同一 captioning run 用的是 marine caption（不同于 Alpaca/ShareGPT 指令数据） | caption 协议下 ΔE：r5 +17.0、r6 +105.5（与 blank-image 协议不同） | ⚠️ 仅一个替代数据集族 |
| **R1.4** 新模型族 | 下载并跑 **Qwen2.5-VL-3B-Instruct**（blank-image，20 样本，3 epochs，rank 5/6） | r5 ΔE **+608.0**（+2.9%）、r6 **−48.0**（−0.2%）→ **符号模式与 LLaVA 相反，crossing 不复现** | ✅ 已实测（结果是"不支持强跨架构声明"，与协议依赖结论一致）|

**总体**：R1 的 33 条中，原本 8 条部分项现在有 **4 条补成实测（R3.5、R1.4、R3.22、R3.18 部分）**、**3 条仍为部分（R3.9、R2.3/R3.16、R3.23）**、1 条（R3.22）本就有归档。
新结果对论文的含义：**支持"协议依赖 + 范围限制"**，但 **R1.4 的新模型族结果与 LLaVA 相反**，不能用来支持"跨架构可迁移"——若审稿人再问，应如实引用，而不是掩盖。

## 九、整合进论文（下一版草稿，2026-10-21 22:20）

已把第八节的补齐结果写进 P3 本地下一版草稿（**已投稿的 `PRLETTERS-D-26-02671` 未改动**）：

- 补充材料新增 **S18–S22**：曲率测量、额外分配基线（NTK/Γ 训练 arm）、新模型族、captioning 下游、seed/软件矩阵；
- S17 claim-status 表新增 4 行（Hessian、NTK 分配、新模型族、caption 任务）；
- S13 provenance 表新增 6 行（含脚本与归档路径）；
- 正文：discussion 的限制 (4)(5) 加入 captioning/新模型族/Hessian 实测；conclusion 保留真实图像数字（删掉新增的新模型族句，细节在 S20）；
- 页数：**正文 10 页**、补充 **9 页**（S1–S22）；`audit_check`/`audit_pdf` 0/0；provenance gate PASS（P3 floats=14）。

## 十、第二轮补充（2026-10-22，S23–S26）

见 `docs/P3_REMAINING_GAPS_2026-10-22.md` 第七节：R3.4/R3.5/R3.22/R2.3/R3.16/R1.4 已补并写入下一版草稿；
剩余仅 R2.4/R3.9 官方基线、VQA 指标/数据族、R3.18 硬件矩阵三类。补充材料 10 页（S1–S26），正文 10 页。

## 十一、第三轮补充（2026-10-22，S27–S28）

分配规则基线（S27）与 VQA-RAD 下游（S28）已入稿；补充材料 S1–S28。

## 十二、云端收尾（2026-10-22 19:30）

新增 S29（第二环境）、S20 7B 表、S28 per-step 数字；补充 S1–S29（12 页）；audit 0/0；provenance PASS（P3 floats=21）。

## 十三、A 组收尾（2026-10-22 23:00）

S29 三环境矩阵（r5 在 torch2.4/cu121 翻转）、S27 IGU 方程 arm；A2 云脚本待实例。

## 十四、定稿状态（2026-10-23 22:10）

`PRLETTERS-D-26-02671` submitted 2026-10-21, status updated 2026-10-22, now **With Editor**. Local final draft frozen at `SUBMISSION/P3_PRL_next_revision/` (Manuscript 10 pp; Supplementary 17 pp, S1–S41; source verified). Submitted package untouched. See `docs/P3_SUBMISSION_STATUS.md`.
