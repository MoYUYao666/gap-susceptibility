# P3 拒稿后的改投方案（2026-10-21）

> 结论先说：**可以再投 PRL**，但必须按"新投稿（new submission）"处理，且要有实质性的 soundness 加固；否则大概率 desk reject。
> 本地升级稿已完成加固，等你确认后再由你通过 EM 提交；我这里不执行投稿动作。

## 一、事实与判断

- 2026-10-21 PRL 拒稿（`PRLETTERS-D-26-02378R1`，EIC Yonghuai Liu）；AE 理由：technical choice 与 experimental
  interpretation 的 soundness 未充分解决；审稿正文在 EM 平台，**未取得**。
- 期刊对"拒稿后再投"没有公开禁令（Elsevier 常规做法是编辑决定）；但同一稿号/同一编辑再次收到近似版本，desk reject
  风险高。可做的降低风险措施：
  1. 以**新稿**提交（新题目、新摘要、新 cover letter），在 cover letter 中**主动披露**前稿号与被拒事实；
  2. 论证改动是**实质性**的（负结果前置、假设审计、统计加固、真实图像对照），而不是换措辞；
  3. 不与其他期刊并行投稿（P3 目前无在审版本）。
- 若 PRL 再次 desk reject，备选 SCI 期刊（按适配度）：**Neural Networks**（Q1，理论+实验匹配；注意 A1 曾在此 desk
  reject，风险中等）→ **Image and Vision Computing**（Q2，较快）→ **Knowledge-Based Systems**（Q1）→
  Pattern Recognition（P1 曾拒，重复风险高，不优先）。TMLR 不放（按你要求只要 SCI）。

## 二、已完成的 soundness 加固（相对被拒版本）

| # | 加固 | 位置 | 证据 |
|---|---|---|---|
| 1 | **负结果成为正文主内容**：claim-status 表逐条列"支持 / 不支持 / 仅边界" | 补充 **S17** `tab:claims` | 论文自身控制实验 |
| 2 | **临界点变为统计陈述**：5 seeds/rank（−23.0±22.3 vs +65.5±38.5），精确置换 **p=0.008**（最小可达） | 正文 conclusion/experiments + 补充 **S14** | `p3_rerun_seeds.json` 等 |
| 3 | **协议窗口测量**：r=5 在 n=12 测得 −39.5，与默认 n=20（−10.5）对比 ⇒ 符号边界稳定、幅度变化 | 补充 **S16** | `p3_protocol_shift.json` |
| 4 | **真实图像对照**（原有，现明确写入 conclusion 数字）：instruction +83.0 vs −7.5；caption +66.5 vs −39.5（r=5/6）| 正文 conclusion + 补充 S7 | `verify_r5/r6...imgs*.json` |
| 5 | **可用性声明修正**：删除"code upon request"，改为公开仓库 + 版本 DOI | conclusion | 与 Data statement 一致 |
| 6 | **标题/摘要重定向**：副标题 "Identifiability, Negative Results, and Protocol Dependence" | main.tex | — |
| 7 | **S11 与正文一致**：补充里旧的两 seed p=0.33 措辞改为五 seed p=0.008 | 补充 S11 | 自身一致性 |

## 三、投稿包状态

- 正文 **10 页**、补充 **8 页**（S1–S17；S13 provenance、S14 五 seed、S15 消融、S16 协议窗口、S17 claim status）；
- 新 cover letter：`paper3/paper_ieee/cover_letter_prl_resubmission.pdf`（2 页，含前稿号披露与 5 项改动）；
- 包：`SUBMISSION/P3_PRL_resubmission/`（已备好：10 页正文 + 8 页补充 + CoverLetter/TitlePage/Highlights/LaTeXSource）；
- 审计：`audit_check` / `audit_pdf` 0/0；页数/摘要词数（≤250）均过。

## 四、需要你确认/执行

1. **是否按 PRL 新投稿提交**（同意则我出最终包与提交清单；不同意则按上面备选 SCI 期刊改封面信）；
2. 若能从 EM 平台拿到审稿意见原文，发我，我把 S17 的"not supported"行逐条对齐评审判据；
3. 投稿时 cover letter 建议直接使用 `cover_letter_prl_resubmission.pdf`（已写明前稿号与改动）。

## 2026-10-21 18:40：已提交

- 新稿号 **`PRLETTERS-D-26-02671`**，状态 **Submitted to Journal**。
- 改投审核报告：`docs/P3_RESUBMISSION_AUDIT_2026-10-21.md`（R1 8 条 + AE 两类问题逐条映射）。
