# P3 — anticipated reviewer objections and prepared evidence (2026-10-19)

> Working document for the revision round (PRL R1 under review, deadline 2026-11-02). Archive: `outputs/analysis/p3_upgrade_analysis.json`.

| # | Likely objection | Prepared answer | Evidence |
|---|---|---|---|
| 1 | "The allocation is no better than random, so the method fails." | We report that as the result, and now quantify the direction: pairing guided and random arms at the same seed and rank ($n=4$ pairs), the guided arm ends $+11.5$ higher in alignment energy (95 % bootstrap CI $[+6.8,+16.2]$). The claim we defend is the zero-shot *purpose*, not a win. | `all_results.json` Theory/Random; `p3_upgrade_analysis.json` |
| 2 | "The critical rank $r_c\in[5,6]$ is borrowed from another family." | The E2 blank-image runs place the sign change between $r=5$ (mean final $3906 < 3927$ start) and $r=6$ (mean $3989 > 3927$). The paper already retracts sharpness and attributes the bracket to the protocol; the independent 3-epoch sweep gives a different boundary ($r\le14$ converge, majority divergence at $r=16$), which supports the protocol-dependence claim rather than contradicting the retraction — but the two run families must be labelled explicitly in the next version. | `E2_results.json` (E2 and sweep), memo |
| 3 | "AdaLoRA is better; the comparison is unfair." | Verified from the archived runs: AdaLoRA at lr $3\times10^{-4}$ gives $\Delta E=-1468.15$ and at $10^{-3}$ gives $-757.30$, against $+1478$ for our best rule. Both sides were swept over the same rates; the manuscript says so and calls the adaptive method the winner on this metric. | `_p458_adalora_lr0.0003.txt`, `_p458_adalora_lr0.001.txt` |
| 4 | "Cross-architecture transfer is only tested inside CLIP." | The transfer experiments use LLaVA-1.5-7B and Qwen2-VL-7B targets with CLIP ViT-B/32 as the source; the scope sentence says the evidence is at these scales, and the local reproducibility is LLaVA-only. | `sections/experiments.tex` |
| 5 | "Uniform beats the rule at matched loss." | We report exactly this: at $3\times10^{-4}$ the arms reach nearly the same loss and the rule is worse ($+5968$ vs $+2842$), so we no longer claim a win over uniform. | `sections/experiments.tex` |
| 6 | "The compression to 10 pages omits necessary detail." | The full version (`main_full.tex`, 13 pages) and the supplement are archived; R1 is a 10-page letter by design, and the omitted detail is in the public repository. | `paper3/paper_ieee/main_full.pdf` |
| 7 | "This is engineering, not a contribution." | The contribution is the Representation Theorem plus the negative controls that bound it; the conclusion states the purpose (allocation without search) explicitly. | Theorem III.1 and §V |
| 8 | "Why should I trust the local CLIP proxy?" | We do **not** add a local proxy claim: the rank-sensitivity control planned as P2-7 was deferred because a generic CLIP run cannot validate a LLaVA-protocol statement, and adding it would be scope creep. | memo |

## 2026-10-21：PRL 拒稿（决定记录）

- 稿号 `PRLETTERS-D-26-02378R1`；EIC Yonghuai Liu；AE 决定 reject。
- 理由原文：*remaining issues regarding the soundness of certain technical choice and interpretation of experimental results which haven't been substantially addressed in the current version.*
- 审稿意见正文在 EM 平台，**待操作者导出**；导出后逐条对照本文件已列 objection 更新状态。
- 本地升级稿（10+7 页）转为**改投基础**，不再走 PRL 修回流程。

## 2026-10-21 18:40：已提交

- 新稿号 **`PRLETTERS-D-26-02671`**，状态 **Submitted to Journal**。
- 改投审核报告：`docs/P3_RESUBMISSION_AUDIT_2026-10-21.md`（R1 8 条 + AE 两类问题逐条映射）。

## 2026-10-21 晚：R1 完整意见已启用（更正）

R1 的审稿报告、33 条结构化意见、44 KB 逐条回复与 10 页修订稿都在
`SUBMISSION/_archive/P3_PRL_rejected_2026-10-21/`（`reviews/`、`evidence/p3_reviews_structured.json`、`response/`、
`CORRECTED_2026-10-15/`）。按真实意见的重审结论见
`docs/P3_RESUBMISSION_AUDIT_2026-10-21.md` 第七节：25 条实质处理、8 条部分处理/声明限制。
