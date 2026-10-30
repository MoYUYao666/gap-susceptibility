# P1 — Independent adversarial review: number provenance and figure/table fidelity

**Manuscript reviewed**: "Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models",
Hongrui Wan (sole author), *Pattern Recognition*, MS **PR-D-26-10149**.

**Artefact of record**: `paper/main_nn.pdf` — 37 pp., `Output written on main_nn.pdf (37 pages, 2611229 bytes)`,
creation stamp `2026-08-22 13:10:18` (`pdfinfo`), i.e. built *after* the last source edit
(`paper/sections/supplementary.tex` 13:00:45) and after the last figure rebuild (`paper/figures/*` ≤ 13:00:06).
`pdfimages -list` confirms every figure float embeds the PNG audited here (p.10 → 2036×1136 = `fig1.png`;
p.12 → 2890×1390/3143×1402 = `fig3.png`/`fig4.png`; p.14 → 2290×940 = `fig2.png`; p.16 → 1886×986 = `fig5.png`;
p.18 → 1586×1076/1736×1076 = `fig6.png`/`fig7.png`; p.32 → 4757×2683/2956×2360 = `fig8_weight_svd.png`/
`fig9_noise_sensitivity.png`; p.33 → 3860×1480/3561×1525/1586×1076 = `fig10_layered_ft.png`/`fig11_gsnr.png`/
`fig12_zeroshot_more.png`; p.34 → 1993×1128/3561×1480 = `fig13_vitl_layered.png`/`fig14_adapter_layered.png`).
A `pdftotext -layout` pass over the PDF reproduces every table cell and caption quoted below, so the
`.tex` line numbers cited are the lines that are actually in the submitted PDF.

**Scope of this round.** Number provenance and figure/table fidelity only. Read-only: **no file under
`paper/`, `outputs/`, `src/`, `tools/` or `.worktrees/` was created or modified**; this report is the only
file written. `docs/P1_eval_audit.md` (2026-08-16, training-convention mismatch) is treated as known; the
question of whether its prescribed disclosures landed is another agent's brief and is **not** re-audited
here. `docs/*.md`, `paper/REVIEW_DEFENSE.md`, `HANDOFF.md` are treated as claims, never as evidence.

**Verification rule applied.** Every number relied on below was recomputed from a named JSON key path or
read out of the archived figure/PDF artefact. Where a figure is a raster image, the plotted values were
recovered either from the companion SVG's path geometry (fig1) or by reading the PNG/webp directly.
Aggregation (mean, sd, ratio, percentage) was re-derived rather than accepted.

---

## 1. Findings, ordered by severity

### 1.1 Must fix before this manuscript can be defended

---

**[A1] — Figure 1 is drawn from the COCO runs while its caption, its surrounding text and the paper's headline narrative are Flickr30k; one panel superimposes two datasets built on different frozen baselines (1.053 vs 0.818).**

*Evidence chain (artefact → code → manuscript)*
- `paper/figures/fig1.svg` (same build as the shipped `fig1.png`, both 2026-07-17 18:50) contains exactly three
  7-point polylines whose first vertex sits at display `y = 112.3`, one 4-point polyline also starting at
  `y = 112.3`, and one 7-point polyline starting at `y = 188.2`. Solving the linear axis map from the
  extremes of the plotted data (`y = 43.2` ↔ COCO full-FT maximum 1.2665; `y = 203.0` ↔ Flickr seed-band
  minimum 0.7705) gives **1.0520** at `y = 112.3` and **0.8164** at `y = 188.2`.
- `outputs/coco/baseline_full_ft_coco/gap_history.json :: centroid_gap` = `[1.05306, 1.26339, 1.26653, 1.24705]`
  — four points, exactly the red "Full FT" curve. (Every Flickr `baseline_full_ft` run has 7 points.)
- `outputs/coco/rq2_both_coco/gap_history.json :: centroid_gap` = `[1.05306 … 1.00062]` (7 pts) = the salmon
  "Both" curve; `outputs/coco/rq2_text_only_coco/gap_history.json :: centroid_gap` = `[1.05306 … 1.01251]`
  (7 pts) = the blue "Text-only" curve.
- The flat "Text-only (mean)" band is the **Flickr** five-seed band:
  `outputs/flickr30k_seeds/rq2_text_only/seed{42,123,456,789,1024}/gap_history.json`, mean curve
  `0.8184 → 0.8128 → 0.8140 → 0.7922 → 0.7791 → 0.7736 → 0.7726`.
- **The defect is live, not stale**: re-running the committed selector
  (`paper/scripts/generate_figures.py:33-60`) against the current `outputs/` reproduces the archived figure
  exactly — `Full FT ← outputs/coco/baseline_full_ft_coco` (4 pts, 1.0531→1.2470),
  `Both ← outputs/coco/rq2_both_coco`, `Text-only ← outputs/coco/rq2_text_only_coco`. The guard
  (`"Text-only" not in sel`) plus `sorted()` ordering makes `outputs\coco\…` the first match; only fig5 was
  re-pointed away from the COCO batch on 2026-08-22 (`paper/scripts/generate_figures.py:164`, comment
  "原图误选 COCO rq2 批"), fig1 was not.
- Manuscript: `paper/sections/experiments.tex:11` — caption "Modality gap evolution during PEFT.
  Full fine-tuning explodes the gap; text-only and low-rank configurations preserve or reduce it."
  The float is introduced immediately before Table 1 (`experiments.tex:8-13`) as the paper's framing figure;
  `main_nn.pdf` p.10 embeds it.

*Why it matters.* Figure 1's own frozen reference (the flat band, ≈0.814–0.818) is a different dataset from
its three singleton curves (≈1.053). A reader therefore cannot reconcile Figure 1 with Table 2's Flickr
Text-only `CGΔ = −0.064` (`0.8184 → 0.7548`) or with the Discussion's "preserves CG at the frozen baseline
level (0.814)": in the figure, "Text-only" runs 1.05 → 1.01 while the "frozen-level" band sits 0.23 below it.
The same trap as the sibling manuscript's 52-vs-38 condition count: a figure extracted from a different
condition set than its title/caption claims.

*Fix.* Add explicit dataset filters (or one panel per dataset) and rebuild; the current script cannot be
re-run as-is because its `Full FT` branch still selects COCO while the other two branches now select Flickr.

---

**[A2] — The Adapter results in Table 1, Table 4, §RQ4 and the Discussion are computed from each run's *own* epoch-0 gap, not from the frozen baseline the tables declare; every Adapter configuration ends **above** the frozen gap, and on a common baseline the Adapter-vs-LoRA ordering reverses.**

*Evidence chain (artefact → code → manuscript)*
- `outputs/phase1/adapter_d{4,8,16,32,64}_text|d16_both|d16_vis/gap_history.json :: centroid_gap` first→last:
  `1.1464→1.0772`, `1.1215→1.0803`, `1.1014→1.0552`, `1.1254→0.9213`, `1.0987→0.8820`, `1.3585→1.3187`,
  `1.0824→0.9990`.
- Frozen baseline: `outputs/flickr30k/baseline_frozen/gap_history.json :: centroid_gap[0]` = **0.81850**;
  `outputs/layered_ft_results.json :: Frozen[0][1]` = **0.81372**.
- Recomputation, same rows, two conventions:

  | convention | Adapter mean CGΔ (n=7) | LoRA α-sweep mean CGΔ (n=5) |
  |---|---|---|
  | Δ vs each run's own epoch-0 (= published value) | **−0.100** | −0.042 |
  | Δ vs the frozen baseline 0.81372 | **+0.234** | **−0.042** |

  Per-run Adapter Δ vs frozen: `+0.264, +0.267, +0.242, +0.108, +0.068, +0.505, +0.185` — **all seven positive**.
- Code/artefact for the published mean: `outputs/cross_method/cross_method_report.json :: 5C_efficiency_comparison.adapter`
  = `{n_experiments: 7, cg_delta_mean: -0.1001, R1_mean: 0.173}`;
  `tools/audit/fix_paper1_round3.py:22-23` is the patch that wrote the `−0.100 / 0.173` row into Table 4.
- Manuscript: `paper/sections/supplementary.tex:17` — Table 1 caption "CG$\Delta_{\text{best}}$ = best gap
  change (**relative to frozen baseline** for each category)"; `experiments.tex:30` "Adapter & 7 & $-$0.217 & 0.574";
  `experiments.tex:138` "Adapter & $-$0.100 & 0.173 & $d$=64, text-only"; `experiments.tex:144` "…Adapter attains
  substantially larger gap reduction on average (mean CG$\Delta = -0.100$ vs.\ $-0.004$ for LoRA)…";
  `discussion.tex:28` "**For Adapter users**: Use text-only with large bottleneck dimension ($d=64$,
  CG$\Delta = -0.217$)."; `experiments.tex:126` "Adapter favors larger bottleneck dimension ($d=64$ achieves
  CG$\Delta = -0.217$), revealing different constraint mechanisms".
- The same convention break affects the Adapter-layered block: `outputs/adapter_layered_results.json ::
  "Adapter Text-only"` starts at **1.1092** and ends at **1.0644**; `:: "Adapter Text+Vis"` starts at
  **1.3608** and ends at **1.3168** — while `:: "Frozen"` = 0.8143. Table 1 (`supplementary.tex:41`) prints
  "Adapter layered FT & 2 & −0.045" under the same "relative to frozen baseline" caption; against frozen the
  two rows are **+0.250** and **+0.503**.

*Why it matters.* This is the paper's RQ4 headline ("the PEFT method choice also matters"), the source of the
ANOVA (`experiments.tex:144`) and of one of the Discussion's practical guidelines. It is a comparison of two
different zero points: LoRA Δ is measured from ≈frozen (LoRA B is zero-initialised, so Flickr LoRA runs start
at 0.818–0.819), Adapter Δ from a state that random adapter initialisation has already pushed to 1.08–1.36.
Reported as a "gap reduction", the largest Adapter "improvement" (−0.217) is in fact the run that comes
*closest to but still does not reach* the pre-trained gap (final 0.882 vs frozen 0.814).

*Fix.* Either (a) restate the Δ convention per block and delete the "relative to frozen baseline" clause —
then the Adapter column must not be read as gap reduction — or (b) recompute Adapter Δ against the frozen
baseline and rewrite §RQ4, Table 4, Table 1's Adapter row and `discussion.tex:28` accordingly. In either case
the sentence "Adapter attains substantially larger gap reduction on average" cannot stand.

---

**[A3] — The abstract's headline correlation (r = −0.827, partial r = −0.807) has no reproducible sample: `correlations.json` asserts n = 81, the only script that computes it selects 185 rows on the current archive, the metrics table has 89 rows, and the figure generator hard-codes the "n = 81" label over a 17-point scatter.**

*Evidence chain (artefact → code → manuscript)*
- `outputs/analysis/correlations.json :: "Distribution Gap (final)"` = `{pearson_r: -0.8274, p_value: 0.0, n: 81}`;
  `:: "Centroid Gap (final)"` = `{pearson_r: -0.6832, n: 81}`;
  `:: "Distribution Gap → R@1 (partial, controlling Centroid)"` = `{pearson_r: -0.8069}`;
  `:: "Distribution Gap Δ"` = `{pearson_r: -0.0415, p_value: 0.7127, n: 81}`.
- The only generator in the repository is `.worktrees/theory-paper/analyze_gaps.py:141-200` (writes
  `correlations.json` at line 284-286), filtering `R@1 is not None and "frozen" not in name and "full_ft" not in name`
  with no cap on n. Re-running that filter over the current `outputs/**/results.json` (248 files) yields
  **185** rows (`theory` 99, `flickr30k` 28, `flickr30k_seeds` 15, `route_c` 8, `phase1` 7, `coco` 6, `blip2` 5,
  `route_d` 5, `siglip` 5, `route_e` 3, `imagenet_zs` 2, `vitl` 2). No archived file lists the 81 rows.
- The companion metrics table is a third number: `outputs/analysis/all_metrics.csv` has **89** data rows
  (89 with a finite `dg_final` and `R@1`; 75 with `R@1 ≥ 0.01`).
- Code, figure side: `paper/scripts/generate_figures.py:62-91`. The `sk()` filter at line 65 yields **17**
  points from `outputs/master_results.json` (re-executed to confirm); line 71 computes `n = len(ra)` = 17, then
  lines 72-77 read the annotation from the archive and set the sample size by fiat —
  "标注值强制从 verified 档案读取（outputs/analysis/correlations.json）… 已发布 fig2.png/svg（2026-07-17，
  标注 r=-0.827/-0.683, n=81）是正确的——请勿重生成 fig2 … 标注 n 固定为 81" — and line 87 prints
  `ax.set_title(f"r = {rv:.3f}    n = 81")`. The shipped `paper/figures/fig2.png` (2026-07-17) carries the same
  label; `main_nn.pdf` p.14 embeds it.
- Manuscript: `paper/main_nn.tex:54-55` (abstract) "the Distribution Gap predicts retrieval performance at
  $r=-0.827$ (partial $r=-0.807$ controlling for Centroid Gap)"; `experiments.tex:149` "across 81 experiments";
  `experiments.tex:162` "Table 5: Pearson correlation between gap metrics and R@1 ($n=81$)";
  `methodology.tex:26,28`; `conclusion.tex:8`; `discussion.tex:36`.

*Why it matters.* The abstract's single strongest quantitative claim, and the journal-facing figure that
carries it (`fig2.png`), cannot be re-derived by a referee from the archived data. The repository's own
generator would print a 17-point scatter under the identical "n = 81" heading.

*Fix.* Archive the 81-row sample (or regenerate the correlations from a stated, reproducible filter and update
`n` and `r` everywhere), re-point fig2 at that sample, and delete the "do not regenerate" instruction.

---

**[A4] — Figure 5's legend and the caption call `e2_dges_alpha4` a "Both-LoRA" run; the artefact says text-only, and the caption's "two both-position runs" is therefore wrong.**

*Evidence chain (artefact → code → manuscript)*
- `outputs/route_e/e2_dges_alpha4/results.json :: experiment` = `"e2_dges_alpha4"`,
  `:: n_trainable_params` = **145170177** — byte-for-byte the same count as the text-only run
  `outputs/route_e/e3_dges_text_r8/results.json :: n_trainable_params` = **145170177**, while the both-position
  run `outputs/route_e/e1_dges_both_r8/results.json :: n_trainable_params` = **131290881**.
- Checkpoint sizes agree: `e1_dges_both_r8/best_checkpoint.pt` = 2,001,779 B vs
  `e2_dges_alpha4/best_checkpoint.pt` = 806,339 B vs `e3_dges_text_r8/best_checkpoint.pt` = 804,675 B.
- The experiment catalogue itself says text-only: `paper/sections/supplementary.tex:115` —
  "`e2\_dges\_text\_alpha4 & text, $\alpha$=4, DG-ES & text\_only & $+$0.198 & 0.638`"; and
  `discussion.tex:38` calls it a "low-$\alpha$ configuration".
- Code: `paper/scripts/generate_figures.py:166-170` —
  `("Both-LoRA (r=8, $\\alpha$=4)", ROOT / "outputs/route_e/e2_dges_alpha4", C["b"])`; the shipped
  `paper/figures/fig5.png` legend reads "**Both-LoRA (r=8, α=4)**".
- Manuscript: `experiments.tex:186` — "…so a first-rise stop criterion fires immediately for every
  configuration; yet **the two both-position runs later recover (R@1 = 0.66 and 0.64)**, illustrating the
  premature stopping discussed in the text." The two R@1 values are `e1` (0.663) and **`e2` (0.638, text-only)**.
  `visual_fragility.tex:30` repeats it: "Triggers on both/low-$\alpha$ (CG$\Delta$: $+$0.186/$+$0.198)".

*Why it matters.* DG-ES is the paper's only instantiation of the proposed monitoring method, and its
"triggered correctly on both-position configs but not on text-only" story is the argument that the monitoring
signal tracks visual-encoder perturbation. If run 2 is text-only, DG-ES fired on a text-only run as well —
the evidence for the predictor's specificity is one run, not two.

*Fix.* Relabel run 2 in the figure and caption ("Text-only LoRA (r=8, α=4)") and rewrite "the two both-position
runs later recover" as "the both-position and the low-α text-only runs later recover".

---

**[A5] — The effective-rank evidence contradicts the claim it is cited for, and three different definitions of "effective rank" appear across the figure, the code and the footnote.**

*Evidence chain (artefact → code → manuscript)*
- `outputs/effective_rank_tracking.json` (means over the 12 `vis_L*` / `txt_L*` keys):
  `:: Frozen[0]` = **12.447 (vision)** / 4.134 (text);
  `:: text-only[0]` = 12.407 / 4.134; `:: text-only[1]` = **8.124** / 3.371;
  `:: text-only[2]` = 7.494 / 2.929; `:: text-only[3]` = **7.832** / **3.217**.
  Under "text-only" the *vision* effective rank falls **37 %** in one epoch and the *text* rank falls 22 %.
- Code: `paper/scripts/noise_sensitivity.py:171-177` defines the rank as `exp(−Σ pᵢ log pᵢ)` over normalised
  singular values and `:181-227` computes it on **per-layer transformer hidden states**, mean-pooled over a
  single 16-image batch (`:210-215`), not on "image embeddings". `paper/scripts/weight_svd_analysis.py:155`
  uses a *different* metric (`int(np.sum(S/S[0] > 0.01))`, "number of singular values above 1 % of σ₁"), and
  the shipped `fig8_weight_svd.png` legends print `(eff=200)` for both Frozen and text-only.
- Manuscript: `introduction.tex:25` "…and **effective rank tracking confirms text-only preserves visual
  embedding geometry**"; `supplementary.tex:173` footnote c "Effective rank of **image embeddings**
  (**threshold 0.99 explained variance**); **text-only preserves rank**" — that 0.99-variance definition
  appears in no script in the repository; `supplementary.tex:270` Figure 9 caption "(B–C) Effective rank of
  vision and text embeddings under Frozen vs. text-only fine-tuning".

*Why it matters.* A text-only run does not adapt the vision transformer blocks, so a 37 % drop in their
activation rank is either (i) measurement noise across different minibatches — the metric is evaluated on one
16-image batch, with no fixed seed or fixed held-out set — or (ii) evidence that the vision tower *did* change,
which is exactly `docs/P1_eval_audit.md`'s known convention problem. Either way the archived numbers cannot
support "text-only preserves visual embedding geometry". As printed, the figure's lower-right panel shows the
opposite of what the text says. (Minor, same float: the two lower panels are both lettered "B" while the
caption says "(B–C)".)

*Fix.* Pick one definition, evaluate it on a fixed held-out batch, report the actual direction, and align
`introduction.tex:25` and footnote c with it — or drop the effective-rank claim from the causal-evidence list.

---

### 1.2 Should fix (a referee is likely to raise these)

---

**[B1] — The headline "116 experiments" is not reproducible from the paper's own tables: the catalogue's printed rows expand to 117, and the one block that makes the arithmetic close is the block that omits its frozen baseline.**

- `paper/sections/supplementary.tex:158` — section header "**XIII. Zero-Shot Generalization and SigLIP --- 7 experiments**",
  but the block lists **8** rows (`:160` DTD zero-shot, `:161` Food101 zero-shot, `:162` `siglip_frozen`,
  `:163-167` `siglip_lora_r4/r8/r16`, `siglip_text_only`, `siglip_both`).
- Counting every printed row of `tab:full_experiments`:
  `30+7+8+7+3+16+4(VII)+4(VIII)+5+4+2+3+8 = 101` rows, of which 4 are the 5-seed rows. Counting the seed block
  as the 20 runs the header claims (Table 10 lists 5 seeds × 4) gives `101 − 4 + 20 = **117**` runs, against
  `:169` "`\textbf{Total} & \textbf{116}`".
- The stated per-section counts do sum to 116 — but only because Table 9 counts SigLIP as 7 (= 5 configurations
  + DTD + Food101) while counting the frozen baseline for **every** other block: `supplementary.tex:36`
  `baseline_frozen`, `:71` `coco_frozen`, `:82` `blip_frozen`, `:92` `vitl_frozen`, `:127` `imagenet_zs_frozen`.
- Corroborating artefact: `outputs/master_results.json :: _meta.by_category.siglip` = **6**, and
  `_meta.total_experiments_with_results` = 100 with `_meta.complete` = 94.
- Manuscript: `main_nn.tex:39` (abstract), `introduction.tex:8`, `conclusion.tex:4`, `experiments.tex:6,49`,
  `supplementary.tex:12`, `visual_fragility.tex:37`, `discussion.tex:22`.

*Fix.* State the counting unit (training run vs configuration), count the frozen baseline consistently, and
change 116 → 117 (or drop `siglip_frozen` from the catalogue and say so).

---

**[B2] — Table 1's "Best CG$\Delta$" and "R@1" columns are taken from different runs in 5 of the 10 core categories (7 of the 15 blocks), so the printed pair never describes one configuration.**

| category (Table 1 line) | Best CGΔ | run holding it (R@1) | R@1 printed |
|---|---|---|---|
| Flickr30k (`experiments.tex:26`) | −0.081 | `alpha_64` (0.637) | 0.702 = `rq1_rank16` |
| 5-Seed (`:28`) | −0.046 | `rq2_text_only` (0.621) | 0.708 = `rq1_rank32` |
| Route C (`:32`) | +0.181 | `c3_gapinit_text_r1` (0.630) | 0.671 = `c3_gapinit_text_r4` |
| Route D (`:33`) | +0.079 | `d1_alpha64_text_r8` (0.389) | 0.657 = `d4_gapinit_text_alpha64` |
| Route E (`:34`) | +0.096 | `e3_dges_text_r8` (0.133) | 0.663 = `e1_dges_both_r8` |
| ViT-B layered (`:39`) | −0.009 | `vitb_layered_vis_L2` (0.680) | 0.713 = `vitb_layered_vis_L4` |
| SigLIP (`:47`) | +0.058 | `siglip_both` (0.454) | 0.479 = `siglip_lora_r4` |

*(Artefacts: `outputs/master_results.json :: experiments[<run>].{cg_delta,R1}` and
`paper/sections/supplementary.tex:99-167` for the per-run rows.)* In the four categories where the two columns
do coincide (Adapter, BLIP-1, COCO, ViT-L) the coincidence is accidental or the R@1 column is "—".
Caption (`experiments.tex:17`) explains `CGΔ_best` but not what the R@1 column means.

*Fix.* Rename the column "best R@1 in category" or print the co-occurring pair.

---

**[B3] — Table 4 reports group means with no n, and the archived group definitions are mislabelled and double-count runs.**

- `outputs/cross_method/cross_method_report.json :: 5C_efficiency_comparison` —
  `lora` = `{n_experiments: 56, cg_delta_mean: -0.0038, R1_mean: 0.6692}`;
  `full_ft` = `{n_experiments: **2**, cg_delta_mean: 0.1994}` with
  `sample_experiments: ["baseline_full_ft/baseline_full_ft", "flickr30k/baseline_full_ft"]` — **one** run
  listed under two directory roots.
- `:: 5D_composite_ranking` tags the five full-fine-tuning rows `baseline_full_ft/seed*`
  (`cg_delta` +0.179 … +0.199) as `"peft_method": "lora"`, and tags the five genuine LoRA runs
  `flickr30k/alpha_*` as `"peft_method": "adapter"`. It also contains **13 exact duplicate
  `(cg_delta, R@1)` pairs** covering 26 of its 63 rows (e.g. `flickr30k/rq2_text_only` ≡
  `rq2_text_only/rq2_text_only`, `gap_init_r4/gap_init_r4` ≡ `flickr30k/gap_init_r4`).
- Recomputing from `5D_composite_ranking`: rows actually tagged `lora` give mean **−0.0020** (n=58);
  excluding the five full-FT rows gives **−0.0202** (n=53). Neither is the published −0.004 with n=56.
- The same defective grouping is what the ANOVA ran on: `:: 5A_statistical_tests.anova_peft_methods` =
  `{f_statistic: 13.37, p_value: 0.0005, groups: {adapter: {n: 7, mean: -0.1001}, lora: {n: 56, mean: -0.003759}}}`;
  `:: welch_t_peft_vs_full_ft` = `{t_statistic: -22.96, p_value: 3.5e-31}`.
- Manuscript: `experiments.tex:133-144` — Table 4 and "Welch's $t$-test … yields $t = -22.96$,
  $p = 3.5 \times 10^{-31}$ … One-way ANOVA across PEFT methods … $F = 13.37$, $p = 5 \times 10^{-4}$".
  No n appears anywhere in the table or the sentence.
- Stale companion artefact: `outputs/cross_method/paper_tables.md` still lists "adapter … 5" and
  "CGΔ −0.0472", i.e. the *pre*-correction grouping, contradicting its own JSON.

*Fix.* State n and the row list per group, de-duplicate by experiment path, fix the `peft_method` tags (the
full-FT rows must not sit in the "LoRA" group), and re-run the two tests.

---

**[B4] — Figure 11's own panel titles contradict its caption, and one of them is a broken computation printed verbatim in the paper.**

- Artefact: `outputs/gsnr_results.json :: text_advantage_pct` = **−639.81**, `:: both_final_loss` = 0.5615,
  `:: text_final_loss` = 4.1540, `:: v_t_ratio` = 1.4531.
- Code: `paper/scripts/gsnr_analysis.py:172` —
  `ax2.set_title(f"B: Text-only matches Both\n(Vis grads contribute <{max(0, -text_advantage):.0f}% to loss reduction)")`
  → the shipped `paper/figures/fig11_gsnr.png` renders "**B: Text-only matches Both (Vis grads contribute
  <640% to loss reduction)**" above two curves that end at 4.15 and 0.56.
- Manuscript: `supplementary.tex:284` caption — "Visual gradients are 1.5$\times$ larger than text gradients in
  both-modality LoRA; text-only converges to a higher final loss (4.15 vs.\ 0.56) yet preserves alignment better."
  The caption is right, the figure panel is wrong, and the panel is what a referee sees.

*Fix.* Regenerate the panel with a correct annotation; the "Vis grads contribute <X%" sentence should be
deleted (the script's own docstring assumed Vis contributes <10 %, whereas the measurement is 640 % the other way).

---

**[B5] — Figure 8's caption numbers have no archived artefact.**

- `paper/scripts/weight_svd_analysis.py` writes **no JSON** — `main()` (`:295-391`) prints `σ₁` at `:382` and
  saves only PNGs; there is no `.json` output anywhere in the script.
- A content search for the caption's digits (`19.12`, `15.88`, `12.45`, `19.62`, `1.0275`, `0.6752`, `0.6606`)
  across `outputs/**/*.json` finds **no** matching artefact — `16.15` matches only unrelated sonar files
  (`outputs/sonar_protocol.json`, `outputs/sonar_spectrum.json`), and the only prose record is
  `HANDOFF.md:157`, a hand-written handoff note (explicitly not evidence).
- Manuscript: `supplementary.tex:259` — "(A) … ($\|\Delta W\|_{\text{txt}} = 0.66$); Full FT … (mean
  $\|\Delta W\|_F$: vision 1.03, text 0.68). (B) … ($\sigma_1 = 16.15$); Full FT inflates the spectrum
  ($\sigma_1 = 19.12$). (C) … ($\sigma_1$: 15.88 $\to$ 12.45 and 15.88 $\to$ 19.62). (D) Frozen image effective
  rank is preserved under text-only but degrades under Full FT."
- Also: panel (D) is a **text box**, not a plot; the code only lists effective ranks for `Frozen` and
  `text-only` (`:265-269`), so the caption's "(D) … degrades under Full FT" is supported only by the panel-B
  legend (`Full FT (eff=185)`), not by panel D.

*Fix.* Archive the ΔW norms and σ₁ values as JSON, or strip the digits from the caption and describe the
panels qualitatively; either remove "(D)" or make the panel actually show the Full-FT rank.

---

**[B6] — The "causal evidence" numbers are single-run, single-batch measurements whose n is never stated, and the noise curve is not monotone.**

- `outputs/noise_sensitivity.json` — `vision[5][2]` = 9.2199 and `text[5][2]` = 3.5461 (ratio **2.600**, matching
  the "2.6×" claim), but `vision[0][2]` = **1.4184** and `text[0][2]` = **0.7092** at σ = 0 (no noise injected),
  and the vision series `[1.4184, 2.8369, 0.7092, 0.0, 1.4184, 9.2199]` is non-monotone: the σ = 0.001 point
  (2.84 %) is *larger* than the σ = 0.1 text-side drop that defines the denominator of the published ratio.
- Code: `paper/scripts/noise_sensitivity.py:91-95,129` — R@1 is computed on `n_batches=20` × batch 64
  (≤ 1 280 pairs) of a `max_samples=2000` validation slice, with no repeats (`baseline_R1` = 0.705).
- `outputs/gsnr_results.json` is a single 3-epoch × 15-batch run (`gsnr_analysis.py:88,117`).
- Manuscript: `supplementary.tex:154, 284`; `introduction.tex:25`; `visual_fragility.tex:4`.
  Neither the figure captions nor §RQ7/prose state n, seeds, or the evaluation-set size.
- Related: `outputs/effective_rank_tracking.json` is likewise one 16-image batch per point (see A5).

*Fix.* State n (and the number of repeats) for each causal measurement, and present the σ = 0.1 comparison as
one point on a noisy curve rather than as "direct causal evidence".

---

**[B7] — "Collapses zero-shot accuracy to near-chance levels" is unquantified and describes only the mean of three seeds spanning 30×.**

- `outputs/imagenet1k_zs_50k_plain.json :: results_plain` = `{full_ft_s42: 0.13, full_ft_s123: 4.09,
  full_ft_s999: 3.54}` → mean 2.5867, range 0.13–4.09. ImageNet-1K chance = 0.1 %, so the mean is 26× chance
  and seed 123 is 41× chance.
- Manuscript: `main_nn.tex:45-46` "collapses zero-shot accuracy to near-chance levels (mean $2.6\%$ over 3
  retrained seeds, vs.\ $59.3\%$ frozen)"; `experiments.tex:215,229`; `supplementary.tex:173` footnote e does
  give the range.

*Fix.* Write "0.1 %–4.1 % (mean 2.6 %)" and reserve "near chance" for the seed-42 run.

---

**[B8] — The full-fine-tuning CGΔ range in the ImageNet footnote is printed one digit high.**

- `outputs/imagenet_zs_rerun/{full_ft,full_ft_s123,full_ft_s999}/centroid_gap.json :: cg_delta` =
  `0.6646, 0.2609, 0.2672` → mean 0.3976 (the table's `+0.40` ✓), range **0.26–0.66**.
- Manuscript: `supplementary.tex:173` footnote e prints "CG$\Delta$ range $+0.26$--$+0.67$".

*Fix.* `+0.26–+0.66`.

---

**[B9] — The ViT-L block's retrieval metric is visibly broken (frozen R@1 = 0.000 against the paper's own 0.586), yet its CG numbers are used as a headline cross-model result; the repair was to delete the R@1 panel, not to fix the measurement.**

- `outputs/master_results.json :: experiments` — `"vitl/vitl_frozen".R1` = `null`,
  `"vitl/vitl_rank4".R1` = 0.0025, `"vitl/vitl_text_only".R1` = 0.0050; the catalogue prints
  `supplementary.tex:92-94` as `0.000 / 0.003 / 0.005`. Compare `"flickr30k/baseline_frozen".R1` = 0.586 and
  `outputs/layered_ft_results.json :: Frozen[0][2]` = 0.6167 on the same dataset.
- Code: `paper/scripts/plot_fig13_cg_only.py:1-9` — docstring: "原 fig13 的 R@1 面板数据损坏（frozen R@1=0.000、
  全配置≈0.005–0.01，均约为机会水平；ViT-L 冻结模型在 Flickr30k 上不可能为 0）——且 ViT-L 权重不在本地
  （models/vit-large 不存在），无法复算 … 故删去 R@1 面板" — the broken panel was removed, the CG panel kept.
  The unreferenced `paper/figures/fig14_vitl_layered.png` still ships the damaged 2-panel version
  (frozen R@1 flat at 0.000).
- Manuscript: `experiments.tex:60` (RQ1: "On ViT-L, however, rank-4 fails dramatically (CG$\Delta = +0.128$),
  while text-only with rank-8 remains effective (CG$\Delta = -0.036$), suggesting that effective rank may scale
  with model capacity"), `experiments.tex:86`, `introduction.tex:15`,
  `visual_fragility.tex:29` ("Larger models exhibit stronger text-only effects (ViT-L) & $\checkmark$").

*Fix.* State that the ViT-L retrieval evaluation is unavailable/known-broken wherever the ViT-L CG evidence is
used, or repair and re-run the evaluation; the ✓ in `tab:predictions` currently rests on a run whose frozen
baseline scores zero.

---

**[B10] — The BLIP-1 CGΔ comparison is made between runs whose starting gaps differ by up to 0.55 against a frozen baseline of 1.31.**

- `outputs/blip2/{b1_blip2_frozen, b4_blip2_lora_text_only, b4_blip2_lora_both, b3_blip2_lora_r4,
  b3_blip2_lora_r8, b3_blip2_lora_r16}/gap_history.json :: centroid_gap[0]` =
  `1.3081, 1.7301, 1.7791, 1.3018, 1.2322, 1.7214` — a spread of **0.547**, larger than the difference the
  paper reports (`+0.047` vs `+0.152`, i.e. 0.105).
- Manuscript: `experiments.tex:211` — "Text-only remains superior to both (CG$\Delta$: $+0.047$ vs.\ $+0.152$).
  Rank-4 text-only achieves CG$\Delta = -0.476$ … BLIP results exhibit substantially higher variance across
  ranks (e.g., rank-8 reverses to CG$\Delta = +0.489$), likely due to the use of selective unfreezing rather
  than native LoRA injection"; `experiments.tex:78,86`; `discussion.tex:34`.
- The variance is attributed to "selective unfreezing" without noting that the epoch-0 gap of the LoRA runs
  already differs from frozen by up to **+0.47**, and that the four "text-only" rank variants start from four
  different points (1.30 / 1.72 / 1.73).

*Fix.* Report the epoch-0 gap alongside Δ (or Δ against the frozen baseline) for the BLIP-1 block, and tie the
"higher variance" explanation to the measured initialisation scatter.

---

### 1.3 Minor / hygiene

**[C1] — Stale duplicate generators and stale duplicate figures sit next to the live ones, and the archive itself carries two competing "paper values".**
`paper/generate_figures.py` (2026-08-13) is a near-identical copy of `paper/scripts/generate_figures.py`
(2026-08-22) but writes to `outputs/paper_figures/` instead of `paper/figures/`; its `fig6()` (`:189-203`)
draws the ImageNet bars at `accs=[60.72,59.06,56.14,7.38]` / `deltas=[0,-1.66,-4.58,-53.34]`, whereas the
live copy draws `accs=[59.28,58.66,59.67,2.6]` (`paper/scripts/generate_figures.py:199`, the values in
Table 7). The stale digits appear in no manuscript table and contradict `outputs/imagenet1k_zs_50k_plain.json`;
they survive inside the archive as `"paper_values"` blocks:
`outputs/imagenet1k_ckpt_check.json :: paper_values` = `{frozen 60.72, text_only 59.06, both 56.14}` and
`outputs/imagenet1k_zs_synset_single.json :: paper_values` = `{…, full_ft 7.38}`.
Four unreferenced figure files also coexist with the referenced ones: `fig12_gsnr.png`,
`fig13_zeroshot_more.png`, `fig14_vitl_layered.png`, `fig15_adapter_layered.png`
(`fig15_adapter_layered.png` is byte-identical to the referenced `fig14_adapter_layered.png`,
sha256 prefix `a09e89f630fb969d`). The unreferenced `fig13_zeroshot_more.png` plots Food101-Frozen **80.6 %**
and DTD-Both **42.5 %** (from the superseded `outputs/zeroshot_extra.json`) where the referenced
`fig12_zeroshot_more.png` plots **82.32 %** and **43.03 %** (`outputs/dtd_food101_zs_check.json :: results`).
*Fix:* delete the stale generator, override the `paper_values` blocks, and remove the unreferenced duplicates
before the figure files travel with the submission.

**[C2] — `outputs/cross_method/paper_tables.md` contradicts its own JSON.**
It lists `adapter … 5 … −0.0472`, the pre-correction grouping; `outputs/cross_method/cross_method_report.json ::
5C_efficiency_comparison.adapter` = `{n 7, −0.1001}`.

**[C3] — Four different "Frozen" R@1 baselines are quoted across the paper with no per-block protocol.**
`0.586` (Table 1 / catalogue, `outputs/master_results.json :: flickr30k/baseline_frozen.R1`),
`0.6167` (`outputs/layered_ft_results.json :: Frozen[0][2]` and `fig10`), `0.685`
(`outputs/adapter_layered_results.json :: Frozen[0][2]` and `fig14`), `0.705`
(`outputs/noise_sensitivity.json :: baseline_R1`). `methodology.tex:20` states only "Recall@K".

**[C4] — The 5-seed `±` convention is neither stated nor uniform.**
`supplementary.tex:5` says only "mean $\pm$ std across 5 independent runs". Against
`outputs/master_results.json :: seeds_summary`:
`rq1_rank4` −0.019815 ± 0.007043 → printed `−0.020 ± 0.007` = population sd (sample sd would be 0.0079 → 0.008);
`rq1_rank32` 0.002756 → `0.003` (ambiguous); `rq2_text_only` 0.002099 → `0.002` (ambiguous);
**`baseline_full_ft` 0.007473 → the population sd rounds to `0.007`, but the paper prints `± 0.008`**
(`supplementary.tex:123`), which is the *sample* sd (0.008355) of the same seeds. One of four cells therefore
uses the other convention. The convention should be declared (and, for 5 runs, sample sd is the defensible one).

**[C5] — Table 2 is captioned "Effect of LoRA position" but two of its four columns are not LoRA.**
`experiments.tex:70` vs the Adapter (`:78`) and BLIP-1 (`:77`) columns.

**[C6] — The abstract's "increases the Centroid Gap by 24 %" is the Flickr-only figure.**
Recomputed: Flickr full FT `0.81857 → 1.01795` = **24.36 %**; COCO `1.05306 → 1.24705` = **18.42 %**
(`introduction.tex:13` gives both; the abstract at `main_nn.tex:45` names neither).

---

## 2. Numbers spot-checked this round (JSON path = value)

✓ = the manuscript reproduces the artefact; ✗ = it does not. Every entry was recomputed in this round.

**Abstract / Introduction**
- `116 experiments` (`main_nn.tex:39`) ↔ rows of `supplementary.tex:28-167` + 5-seed expansion = **117** — ✗ (**B1**)
- `increases the Centroid Gap by 24 %` ↔ `outputs/flickr30k/baseline_full_ft/gap_history.json :: centroid_gap`
  `0.81857 → 1.01795` = 24.36 % ✓ ; `18 %` on COCO ↔ `outputs/coco/baseline_full_ft_coco` `1.05306 → 1.24705`
  = 18.42 % ✓ (**C6** for the abstract's missing scope)
- `mean 2.6 % over 3 retrained seeds, vs. 59.3 % frozen` ↔ `outputs/imagenet1k_zs_50k_plain.json :: results_plain`
  `{frozen 59.28, text_only_r8 58.66, both_r8 59.67, full_ft_s42 0.13, full_ft_s123 4.09, full_ft_s999 3.54}`
  → mean 2.5867 ✓ (**B7** on "near-chance")
- `limits zero-shot degradation to 0.6 percentage points` ↔ `59.28 − 58.66 = 0.62` ✓
- `$r=-0.827$ (partial $r=-0.807$)` ↔ `outputs/analysis/correlations.json` (−0.8274 / −0.8069, n asserted 81)
  ✓ on value, ✗ on reproducibility (**A3**)
- `Text+Vis-L1 … CG remains at 0.814 … R@1 reaches 0.700` ↔ `outputs/layered_ft_results.json ::
  "Text + Vis-L1"[0][1] 0.81340` and `[5][1] 0.81434`, `[5][2] 0.70000` ✓
- `pure text-only (R@1=0.427) and full both-modality (R@1=0.510)` ↔ `:: "Text-only"[5][2]` 0.42667,
  `:: "Both (all Vis)"[5][2]` 0.51000 ✓
- `DTD/Food101 … within ±0.8 pp` (`introduction.tex:27`) ↔ `outputs/dtd_food101_zs_check.json :: results`
  max |Δ| = 0.74 pp ✓; `fig12_zeroshot_more.png` shows 42.87/43.30/43.03 and 82.32/81.58/81.63 ✓
- `vision encoder noise degrades retrieval 2.6× more` ↔ `outputs/noise_sensitivity.json`
  9.2199 / 3.5461 = 2.600 ✓ (**B6** on n and monotonicity)
- `visual gradients are 1.5× larger` ↔ `outputs/gsnr_results.json :: v_t_ratio` 1.4531 ✓ (rounds to 1.5)
- `text-only converges to a higher final loss (4.15 vs 0.56)` ↔ `:: text_final_loss` 4.1540,
  `:: both_final_loss` 0.5615 ✓ (figure panel contradicts it — **B4**)
- `effective rank tracking confirms text-only preserves visual embedding geometry` (`introduction.tex:25`)
  ↔ `outputs/effective_rank_tracking.json :: text-only[0→3]` vision 12.41 → 7.83, text 4.13 → 3.22 — ✗ (**A5**)

**Table 1 / Table 2 (Centroid Gap)**
- Table 2 — all 15 cells ↔ `outputs/{flickr30k,coco,phase1,blip2,vitl}/…/gap_history.json :: centroid_gap`
  (last − first): all 15 reproduce to ±0.0005 ✓ — *but* the Adapter column's Δ is measured from 1.08–1.36, not
  from frozen 0.8137 — ✗ on the stated convention (**A2**)
- Table 1 `Best CGΔ` / `R@1` pairs ↔ per-run rows in `supplementary.tex:28-167` — 5 of the 10 core categories
  mismatch (7 of 15 blocks; the other three core blocks print "—" in the R@1 column) (**B2**)

**Table 3 (`tab:ablation`) / Table 6 (`tab:alpha_rank`)**
- α ∈ {4,16,64} → −0.017/−0.045/−0.081, R@1 0.611/0.614/0.637 ↔ `outputs/flickr30k/alpha_*/gap_history.json` ✓
  (`fig4.png` additionally plots α = 8, 32 at −0.023/−0.071, which the table omits — consistent, not an error)
- modules q/qv/qvko → −0.045/−0.048/−0.067 ↔ `outputs/flickr30k/modules_{q,qv,qvko}` ✓
- α=64 r=8/4/16 → +0.079/+0.183/+0.196 ↔ `outputs/route_d/d{1,2,5}_*/results.json` ✓

**Table 4 / Welch / ANOVA**
- LoRA −0.004 / 0.669 ↔ `outputs/cross_method/cross_method_report.json :: 5C_efficiency_comparison.lora`
  (mean −0.0038, R1 0.6692) ✓ on value, ✗ on group hygiene and n (**B3**)
- Adapter −0.100 / 0.173 ↔ `:: .adapter` (−0.1001, 0.173, n 7) ✓ on value, ✗ on convention (**A2**) and n (**B3**)
- Full FT +0.199 / 0.527 ↔ `:: .full_ft` (0.1994, 0.527, n_experiments **2** for one run) ✓ / ✗ (**B3**)
- `t = −22.96, p = 3.5e-31` ↔ `:: 5A_statistical_tests.welch_t_peft_vs_full_ft` ✓
- `F = 13.37, p = 5e-4` ↔ `:: 5A_statistical_tests.anova_peft_methods` ✓ (group composition defective — **B3**)

**Table 5 (correlation)**
- −0.827 / −0.683 / −0.807 / −0.042 / +0.012, p 0.713 / 0.915 ↔ `outputs/analysis/correlations.json` ✓ on value,
  ✗ on sample provenance (**A3**); `fig7.png` prints 0.827/0.683/0.807 ✓

**Table 7 / Figure 6 (ImageNet zero-shot)**
- Frozen 59.28 / Text-only 58.66 / Both 59.67 / Full FT 2.6 ↔ `outputs/imagenet1k_zs_50k_plain.json ::
  results_plain` ✓; Δ column −0.62/+0.39/−56.7 recomputes ✓; `fig6.png` prints 59.3/58.7/59.7/2.6 ✓
- Table 7 `CGΔ` full-FT +0.40 ↔ mean of `outputs/imagenet_zs_rerun/*/centroid_gap.json :: cg_delta`
  = 0.3976 ✓; footnote range `+0.26–+0.67` ✗ (**B8**)

**5-seed block (Table 10) / `tab:full_experiments` VII**
- `−0.020 ± 0.007, −0.002 ± 0.003, −0.046 ± 0.002, +0.191 ± 0.008` ↔ `outputs/master_results.json ::
  seeds_summary` means ✓; sds ✓ for three of four, ✗ for `baseline_full_ft` (**C4**)
- per-seed rows `−0.009 … +0.199` ↔ `outputs/flickr30k_seeds/*/seed*/gap_history.json` (last − first) ✓
  (e.g. `rq1_rank4/seed42` 0.81829 → 0.80963 = −0.00866 → −0.009 ✓)

**Catalogue blocks IX–XIII**
- ViT-B layered CGΔ `+0.237/+0.001/−0.009/−0.002/+0.209`, R@1 `0.427/0.700/0.680/0.713/0.510`
  ↔ `outputs/layered_ft_results.json` (each run's own epoch-0) ✓; `fig10.png` matches ✓
- ViT-L layered CGΔ `−0.058/+0.066/+0.065/+0.066` ↔ `outputs/vitl_layered_results.json` ✓; `fig13_vitl_layered.png`
  matches ✓; R@1 suppressed to "—" (broken — **B9**)
- Adapter layered CGΔ `−0.045/−0.044` ↔ `outputs/adapter_layered_results.json` own-epoch-0 ✓, frozen-relative
  ✗ (+0.250/+0.503 — **A2**); `fig14_adapter_layered.png` title "Text-only Also Preserves Alignment" shows both
  runs ending 0.25–0.50 above the plotted Frozen point
- Route C/D/E cells ↔ `outputs/route_c/*`, `outputs/route_d/*`, `outputs/route_e/*/results.json` ✓
- DTD/Food101 footnote values ↔ `outputs/dtd_food101_zs_check.json :: results` ✓

**Figures opened and read this round**: `fig1.png` (+`fig1.svg` geometry), `fig2.png`, `fig4.png`, `fig5.png`,
`fig6.png`, `fig7.png`, `fig8_weight_svd.png`, `fig9_noise_sensitivity.png`, `fig10_layered_ft.png`,
`fig11_gsnr.png`, `fig12_zeroshot_more.png`, `fig13_vitl_layered.png`, `fig14_adapter_layered.png`, plus the
unreferenced `fig13_zeroshot_more.png` and `fig14_vitl_layered.png`. `fig3.png` was checked against its
hard-coded data list (`paper/scripts/generate_figures.py:95-96`), which matches Table 2.

---

## 3. Verdict

**Not ready to defend as it stands — the blocking problems are in the figures, not in the arithmetic.**

On the arithmetic the manuscript is in good shape: every cell of Table 2 (**15/15**), Table 3, Table 6,
Table 7 and the catalogue's per-run CGΔ and R@1 values reproduces from a named JSON key path; the abstract's
`24 %`, `2.6 %`, `59.3 %`, `0.6 pp`, `2.6×`, `1.5×`, `4.15 vs 0.56` and the `−0.827/−0.683/−0.807` triple all
recompute to the printed digits; the correlation table's five `r`/`p` pairs match
`outputs/analysis/correlations.json`; the 5-seed means match `master_results.seeds_summary`; and the ImageNet
zero-shot row set is internally consistent. The PDF is the current build and embeds exactly the figures
audited here.

What blocks the manuscript is that **five of the figures and their surrounding claims do not describe the
conditions they are drawn from**, which is precisely the class of defect a referee finds by opening the float:

1. **Figure 1 plots the COCO runs** (`1.053 → 1.25` for "Full FT", 7-point COCO curves for "Both" and
   "Text-only") **under a Flickr30k caption, with a Flickr five-seed band as the "frozen" reference** — and
   the committed script still selects that mix today (**A1**).
2. The **Adapter** story — RQ4, Table 1, Table 4, the ANOVA, the practical guideline — reports Δ measured from
   a random-initialised state rather than the frozen baseline its own caption declares; on the declared
   baseline every Adapter configuration makes the gap *worse* than frozen and the Adapter-vs-LoRA ordering
   reverses (**A2**).
3. The **n = 81** sample behind the abstract's headline correlation is not reconstructible from anything in
   the repository, and the figure generator prints the same "n = 81" over a 17-point scatter it computes
   itself (**A3**).
4. **Figure 5's** blue run is labelled "Both-LoRA" in the legend and in the caption but is text-only in the
   artefact, which halves the evidence that DG-ES discriminates visual-encoder perturbation (**A4**).
5. The **effective-rank** panel shows the visual geometry degrading by 37 % under the run the text says
   preserves it, under one of three mutually inconsistent definitions of "effective rank" (**A5**).

**Minimum set of changes**: (1) rebuild Figure 1 with unambiguous dataset filters and re-check the caption;
(2) restate or recompute the Adapter Δ convention and rewrite §RQ4, Table 4, Table 1's Adapter row and
`discussion.tex:28`; (3) archive the n = 81 row list (or regenerate the correlations and fig2 from a stated
filter); (4) relabel Figure 5's second run and fix the sentence that depends on it; (5) fix or withdraw the
effective-rank claim and collapse the three definitions into one; (6) reconcile the 116/117 count and add n to
Table 4 and to the causal-evidence captions. Items 1–5 are visible in the abstract, in five figures and in the
two most-read tables; with 1–6 done the residual risk is ordinary copy-editing.

---

## 4. Files read / written

**Read**: `paper/main_nn.tex`, `paper/sections/{introduction,methodology,experiments,visual_fragility,discussion,conclusion,supplementary}.tex`,
`paper/generate_figures.py`, `paper/scripts/{generate_figures,noise_sensitivity,gsnr_analysis,weight_svd_analysis,
plot_fig13_cg_only}.py`, `tools/audit/fix_paper1_round3.py`, `.worktrees/theory-paper/analyze_gaps.py`,
`paper/figures/*.png|.svg` (14 floats read as images + `fig1.svg` path geometry), `paper/main_nn.pdf`
(`pdfinfo`, `pdfimages -list`, `pdftotext -layout`); JSON by key path: `outputs/master_results.json`,
`outputs/analysis/{correlations.json,all_metrics.csv}`, `outputs/cross_method/cross_method_report.json`,
`outputs/cross_method/paper_tables.md`, `outputs/imagenet1k_zs_50k_plain.json`,
`outputs/imagenet1k_zs_50k_synset.json`, `outputs/imagenet1k_zs_synset_single.json`,
`outputs/imagenet1k_ckpt_check.json`, `outputs/imagenet_zs_rerun/*/{centroid_gap,zero_shot_eval}.json`,
`outputs/dtd_food101_zs_check.json`, `outputs/zeroshot_extra.json`, `outputs/gsnr_results.json`,
`outputs/noise_sensitivity.json`, `outputs/effective_rank_tracking.json`, `outputs/layered_ft_results.json`,
`outputs/vitl_layered_results.json`, `outputs/adapter_layered_results.json`, and all 213
`outputs/**/gap_history.json` plus `outputs/{flickr30k,phase1,coco,blip2,vitl,siglip,route_e}/…/results.json`.

**Written**: `docs/P1_REVIEW_NUMBERS.md` (this file) — only.

**Not modified**: every file under `paper/`, `outputs/`, `src/`, `tools/` and `.worktrees/`. No LaTeX or figure
build was run; `main_nn.pdf` was read, not regenerated.
