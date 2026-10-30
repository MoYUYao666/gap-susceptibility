# Paper A — anticipated reviewer objections and prepared evidence (2026-10-19)

> Working document for the revision round. Every answer names the archive and script. The submitted package is frozen;
> this file is not part of the manuscript.

| # | Likely objection | Prepared answer | Evidence |
|---|---|---|---|
| 1 | "The position effect is an artefact of the LoRA/full-tower labelling confusion." | The convention is stated explicitly in Section 3 (adapters injected, backbone not frozen); the strict-freezing control isolates the vision side by construction; and true-LoRA reruns reproduce the ordering. The rank sweep shows the effect is flat in rank (Spearman $-0.46$ / $-0.18$), so it is not a capacity artefact. | `paperA_rank_position_dynamics.json`; `_p1331`; strict-freezing tables |
| 2 | "The ODE is curve fitting, not theory." | The ODE is derived from gradient flow with trajectory-averaged coefficients; $\beta$-constancy is a parameter-free prediction; the fit quality is reported per condition (LoRA mean $R^2=0.955$ text-only, 100% of runs above 0.9; adapter $0.73$/$0.61$ where the first-order account fails). | `paperA_ode_diagnostics.json`, `ode_ledger.json` |
| 3 | "Family differences could just be different fit quality." | The family separation is reported both in $\alpha$ (LoRA $-0.0245$ vs adapter $-0.0393$ vs full fine-tuning $-0.0413$) and in $R^2$; matched-position contrasts are given, so the reader can see it is not only a fit artefact. | `paperA_lora_vs_fullft.json` |
| 4 | "DG correlates with retrieval by construction." | The retrieval relation is measured across configurations, and the zero-shot dissociation is stated separately; the discussion separates predictive use from causal claims. | `outputs/analysis/dg_*` archives; Section 5 |
| 5 | "Single-seed noise." | Every configuration has three seeds; the $R^2$ and $\alpha$ tables report per-seed means; the position table reports five seeds per arm with per-arm values. | `position_table_verification.json` |
| 6 | "SigLIP contradicts CLIP, so the claim is architecture-dependent and weak." | That is the stated finding: the position effect is architecture- and pre-training-dependent (WIT vs LAION), and the paper reports it as a boundary rather than hiding it. | Section 5 strict-freezing tables |
| 7 | "Theory is post hoc." | Three predictions are tested out of sample: $\beta$ constancy, cross-architecture transfer of $\Gamma$, and the effective-rank saturation; failures are reported. | `validation.tex`, `ode_ledger.json` |
| 8 | "Adapters underperform LoRA, so the comparison is unfair." | The adapter runs are reported with their own fit diagnostics; the paper's claims are about the position effect and the dynamics, not about adapter superiority. | `paperA_ode_diagnostics.json` |
