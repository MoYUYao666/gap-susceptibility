# Bootstrap confidence intervals for the A1 monitoring claim and the Paper A strict-freeze arms

**Status: DRAFT TEXT ONLY.** No manuscript `.tex` file was edited and no existing archive was modified.
Everything below is a proposal, with the numbers it quotes recomputed from the archives named in each row.

| item | value |
|---|---|
| script | `tools/_p1595_bootstrap_ci_round.py` |
| result archives | `outputs/analysis/a1_monitoring_bootstrap.json`, `outputs/analysis/paperA_strict_bootstrap.json` |
| method | percentile bootstrap, 20,000 resamples, fixed RNG seed (20261024), per-comparison deterministic streams |
| resampling unit | A1: run (dataset x backbone x seed). Paper A: seed within an archive. Arm differences: paired by seed |
| dispersion reported | sd with **both** `ddof=1` (sample) and `ddof=0` (population); the convention each printed spread matches is recorded under `sd_convention` |
| Monte-Carlo error | max shift of a CI endpoint when the stream is re-seeded: A1 ≤ 0.016 points, Paper A ≤ 0.015 percentage points (≪ CI half-widths) |
| idempotency | re-running `--apply` reproduces both JSON files byte-for-byte (verified by SHA-256) |
| exit status | 0 when every asserted manuscript digit reproduces; 1 otherwise. Three items are deliberately failing and are listed in §5 |

Reproduce with:

```
python tools/_p1595_bootstrap_ci_round.py            # dry run: recompute, assert, print every check
python tools/_p1595_bootstrap_ci_round.py --apply    # also write the two JSON archives
python tools/_p1595_bootstrap_ci_round.py --ignore-unarchived   # treat "no archive field" as informational
```

---

## 1. TASK A — A1 (`paper_a1/`, Pattern Analysis and Applications)

### 1.1 The claim under audit

`paper_a1/main.tex`, `\section{Introduction}` (`sec:intro`), lines 85–90:

> "across 16 runs with held-out splits of 353--1212 images the minimum-mass rule lands $0.58$ points from the
> oracle on average ($0.37$ binomial standard errors), against $3.55$ for the first epoch; training to the end
> reaches $0.52$"

and the same digits again in `\subsection{A label-free monitoring protocol}` (`sec:protocol`), lines 1297–1302,
with Table `tab:monitor_regret` (lines 1320–1338) giving the point means.

The parenthetical `0.37` is the **mean over runs of the per-run binomial standard error** of the held-out
accuracy at the epoch each rule selected (`a1_monitor_split_diagnosis.json::summary.large.mean_regret_minM_in_SE`
= 0.373874; recomputed here from `oracle_top1`, the quantisation step and `n_eval`). It bounds *within-run*
sampling error at the chosen epoch. It is **not** an uncertainty on the reported mean over runs, and it cannot
be: the 16 runs are not 16 draws of one binomial. A run-level bootstrap answers the question the sentence
actually raises — how much of `0.58` vs `0.52` vs `3.55` is run-to-run variation.

### 1.2 Provenance chain (all fields recomputed from the per-epoch records, then asserted)

| level | file | field |
|---|---|---|
| raw per-epoch | `outputs/analysis/a1_monitor_interior_v2.json` (12 runs) | `runs[<key>][epoch].{top1, mass_0.01, CG}` |
| raw per-epoch | `outputs/analysis/a1_monitor_interior_extra.json` (8 runs) | `runs[<key>][epoch].{top1, mass_0.01, CG}` |
| derived per-run | `outputs/analysis/a1_monitor_diagnosis.json` | `per_run.<key>.{oracle_top1, quant_step, regret_first, regret_epoch_last_epoch, regret_first_epoch}` |
| derived per-run | `outputs/analysis/a1_monitor_combined.json` | `per_run.<key>.{oracle, minCG, seqM}` |
| stratified summary | `outputs/analysis/a1_monitor_split_diagnosis.json` | `summary.{large,small}.{n_runs, n_eval_range, mean_regret_*, mean_regret_minM_in_SE}` |
| generators | `tools/_p1402_a1_monitor_diagnosis.py`, `tools/_p1404_a1_split_size.py`, `tools/_p1398_a1_combined.py`, `tools/_p1408_a1_table.py` | — |

Rule definitions (identical to the archived generators):
`minimum margin mass` = regret at `argmin` over epochs of `mass_0.01` (earliest minimum);
`first epoch` = regret at epoch 0; `training to the end` = regret at the last epoch (epoch 10);
`minimum centroid gap` = regret at `argmin` over epochs of `CG`; `sequential minimum mass` = stop at the first
epoch whose `mass_0.01` exceeds its running minimum by more than 0.01, else at the last epoch.

The 16 "large" runs are the DTD and Food-101 runs (held-out 353–1212 images); the 4 "small" runs are
fathomnet8 and inat_wild (60–144).

### 1.3 Results — run-level percentile bootstrap, 95 %

Large split, **n = 16 runs** (dispersion = sd across runs, `ddof=1`):

| rule | mean (points) | sd (ddof=1) | 95 % CI | CI half-width |
|---|---|---|---|---|
| minimum margin mass | 0.5823 | 0.6843 | **[0.284, 0.934]** | 0.325 |
| training to the end | 0.5177 | 0.5566 | **[0.265, 0.792]** | 0.264 |
| first epoch | 3.5454 | 2.4031 | **[2.422, 4.709]** | 1.144 |
| minimum centroid gap | 1.4501 | 1.0939 | [0.974, 2.009] | 0.517 |
| sequential minimum mass | 0.6405 | 0.6471 | [0.361, 0.969] | 0.304 |

Paired bootstrap (same run index resampled for both rules, so the run pairing is kept):

| contrast | mean difference | 95 % CI | CI excludes 0 |
|---|---|---|---|
| minimum mass − training to the end | +0.065 | [−0.342, +0.504] | no |
| minimum mass − first epoch | −2.963 | [−4.107, −1.859] | yes |
| training to the end − first epoch | −3.028 | [−4.208, −1.857] | yes |

Small split, n = 4 runs, for completeness (the manuscript already calls this regime noise-dominated):
minimum mass 6.18 [4.51, 8.75]; last epoch 4.51 [3.75, 5.28]; first epoch 22.05 [9.27, 32.50];
minimum mass − last epoch +1.67 [0.00, +5.00] (does not exclude 0); minimum mass − first epoch −15.87
[−27.08, −0.73].

Caveat to state alongside the numbers: with 16 runs (and 4 in the small group) a percentile bootstrap interval is
coarse and mildly anti-conservative; it bounds how much of the reported mean can be attributed to run-to-run
variation and should not be read as a hypothesis test. The paired intervals are the sharper of the two because
they remove the between-run level differences.

### 1.4 Draft sentences

**Insertion point A1-1** — `paper_a1/main.tex`, `\section{Introduction}` (`sec:intro`), appended to the
paragraph ending "…last epoch $4.51$, first epoch $22.05$." (current lines 85–90):

> "Bootstrapping over those 16 runs (20{,}000 resamples) puts a $95\%$ interval on each mean: the minimum-mass
> rule lands $0.58$ [$0.28$, $0.93$] points from the oracle, the first epoch $3.55$ [$2.42$, $4.71$], and
> training to the end $0.52$ [$0.26$, $0.79$], with run-to-run standard deviations of $0.68$, $2.40$ and
> $0.56$ points. The paired difference between the minimum-mass rule and training to the end is $+0.06$
> [$-0.34$, $+0.50$] points, so the two are indistinguishable on these runs, whereas both beat the first epoch
> by about three points ($-2.96$ [$-4.11$, $-1.86$] and $-3.03$ [$-4.21$, $-1.86$]). The $0.37$ above is the
> mean of the per-run binomial standard error of the held-out accuracy at the selected epoch, and bounds
> within-run sampling error only; the intervals here bound the uncertainty of the mean across runs."

**Insertion point A1-2** — `paper_a1/main.tex`, `\subsection{A label-free monitoring protocol}`
(`sec:protocol`), in the paragraph at lines 1297–1302 (after "…not a universal stopping rule, and it buys
early stopping rather than an accuracy gain."), replacing the bare "($1.08$ binomial SE)" phrasing by:

> "On the 16 large-split runs a run-level bootstrap ($20{,}000$ resamples) gives $95\%$ intervals of
> [$0.28$, $0.93$] points for the minimum-mass rule, [$0.26$, $0.79$] for training to the end and
> [$2.42$, $4.71$] for the first epoch; the mass rule and training to the end are indistinguishable
> ($+0.06$ [$-0.34$, $+0.50$]), while both separate from the first epoch. On the four small splits ($60$--$144$
> images) the same intervals are $[4.51$, $8.75]$, $[3.75$, $5.28]$ and $[9.27$, $32.50]$ points, i.e.\ the
> ordering there is not resolved by four runs."

**Insertion point A1-3** — Table `tab:monitor_regret` (caption, lines 1320–1326), add a final sentence:

> "Intervals in the text are run-level percentile bootstrap intervals over the runs of each column
> ($n=16$ and $n=4$; $20{,}000$ resamples; `outputs/analysis/a1_monitoring_bootstrap.json`)."

### 1.5 Recommended archive/appendix fix (digit issue, see §5.1)

Table `tab:monitor_regret` has ten cells. The provenance appendix
(`paper_a1/main.tex`, `Appendix~\ref{app:provenance}`, line 1718) cites
`tools/_p1408_a1_table.py` + `a1_monitor_split_diagnosis.json`, and that archive carries only six of them
(`minM`, `last`, `first`). The `minimum centroid gap` (`1.45` / `3.65`) and `sequential minimum mass`
(`0.64` / `16.53`) cells reproduce exactly from `outputs/analysis/a1_monitor_combined.json::per_run`
(`tools/_p1398_a1_combined.py`). Draft replacement for that appendix row:

> `\raggedright tab:monitor\_regret & \raggedright\path{tools/_p1408_a1_table.py}, \path{_p1398_a1_combined.py} & \raggedright\path{a1_monitor_split_diagnosis.json, a1_monitor_combined.json} & \texttt{verified} \\`

---

## 2. TASK B — Paper A (`paper合/`, Neurocomputing), strict-freeze arms

### 2.1 Scope, and a provenance warning about the brief's examples

The strict-freeze arm comparisons of Paper A are the three tables below. **The examples quoted in the task
brief — `+1478 +/- 1563` and `+5048 +/- 1900`, "matched-loss arms", "random-allocation control" — are not
Paper A digits**: they are Paper 3's Γ-guided vs uniform allocation arms
(`paper3/paper_ieee/sections/experiments.tex`, "Counterfactual validation"). They are nevertheless
recomputed and bootstrapped in §4 of this file, under an explicit addendum in
`outputs/analysis/paperA_strict_bootstrap.json::cross_paper_addendum_p3_allocation`, so that the digits the
brief named travel with their real provenance.

### 2.2 Tables covered, archives, and printed-digit verification

`\Delta\mathrm{CG}` is always recomputed as `final_gap.centroid_gap − initial_gap.centroid_gap` from the same
per-seed JSON; `R@1` from `final_task_metrics.R@1`.

| table (paper A) | section label | row | archive | per-arm n | printed ΔCG reproduced |
|---|---|---|---|---|---|
| `tab:position_strict` | `sec:empirical` (`paper合/sections/empirical.tex`) | CLIP B/32 (WIT), r8 | `outputs/strict_freeze/{text_only,both,vision_only}/seed*/results.json` | 5 | yes (3/3) |
| | | OpenCLIP B/32 (LAION), r4 | `outputs/strict_freeze_oclip/r4/...` (ΔCG) + `outputs/strict_freeze_openclip/...` (R@1) | 5 | yes (3/3) |
| | | CLIP B/32 (WIT), rank-matched r4 | `outputs/strict_freeze_b32_r4/...` | 5 | yes (3/3) |
| | | CLIP B/16 (WIT), rank-matched r4 | `outputs/strict_freeze_b16/r4/...` | 5 | yes (3/3) |
| | | SigLIP B/16 (WebLI), r8 | `outputs/siglip_strict/seed*/{s4_siglip_lora_text_only, s4_siglip_lora_both, s6_siglip_lora_vision_only}/results.json` | 5 | yes (3/3) |
| | | BioCLIP B/16, r4 | `outputs/strict_freeze_bioclip/results_partial.json::records` | 3 | yes (3/3) |
| `tab:vlm` | `sec:vlm` (`paper合/sections/supplement.tex`) | Qwen2-VL-2B strict freeze, reductions | `outputs/vlm_clean_summary.json::per_arm.*.per_seed` vs `frozen.dg_star` | 13 | yes (means, sds, ranges) |
| `tab:llava` | `sec:llava` (`paper合/sections/supplement.tex`) | LLaVA-1.5-7B strict freeze, changes | `outputs/canonical_caption_metric.json::runs.*_s*.clean.dg_star` vs `runs.frozen` | 3 | yes (means, sds, ranges) |

All 18 ΔCG cells of `tab:position_strict` reproduce to the printed four decimals; the OpenCLIP ΔCG cells come
from the rank-4 archive while its `R@1` cells come from the rank-8 archive, exactly as supplement Section
`sec:r1provenance` states. The `R@1` cells that the manuscript already declares non-reproducing remain so
(recorded as informational checks): B/32$^\dagger$ text-only 0.621 vs 0.6222, B/16$^\dagger$ text-only 0.651
vs 0.6502, B/32$^\dagger$ both 0.679 vs 0.6796.

### 2.3 Dispersion convention — what each printed spread is

| table | printed spread | convention that matches | the other convention |
|---|---|---|---|
| `tab:vlm` (13 seeds) | 0.44 / 0.29 / 1.01 | **population sd, `ddof=0`** (0.4393 / 0.2911 / 1.0141) | `ddof=1`: 0.4573 / 0.3030 / 1.0555 |
| `tab:llava` (3 seeds) | 7.54 / 16.33 / 7.91 | **population sd, `ddof=0`** (7.5363 / 16.3311 / 7.9141) | `ddof=1`: 9.2301 / 20.0014 / 9.6928 |
| `tab:position_strict` (5 seeds) | no spread printed; caption claims "seed-to-seed standard deviation of 0.0006--0.006" | `ddof=1`: 15 non-BioCLIP arm sds span 0.00056–0.00596, i.e. 0.0006–0.006 at the printed precision | BioCLIP arms are 0.0022 / 0.0104 / 0.0149 — **outside the printed range** |
| P3 allocation arms (6 seeds / 30 runs) | `± 1563`, `± 1900`, `± 4771` | **sample sd, `ddof=1`** (`st.stdev`) | `ddof=0` would be 1427.1 / 1734.4 / … |

Consequence worth a footnote: for the three-seed LLaVA table the printed spread is ~18 % smaller than the
sample sd (e.g. vision-only 16.33 vs 20.00), and the same table's sentence "separate in mean by a margin of
about two pooled standard deviations" is computed on the smaller number.

### 2.4 Results — seed-level percentile bootstrap, 95 %

`tab:position_strict` — arm means with CI, and paired arm differences (same seeds inside one archive):

| row | text-only ΔCG [95 % CI] | both ΔCG [95 % CI] | vision-only ΔCG [95 % CI] | text − vision [95 % CI] | text − both [95 % CI] |
|---|---|---|---|---|---|
| CLIP B/32 (WIT) r8 | −0.0465 [−0.0489, −0.0441] | −0.0258 [−0.0283, −0.0232] | +0.0106 [+0.0072, +0.0140] | −0.0571 [−0.0628, −0.0520] | −0.0207 [−0.0248, −0.0179] |
| OpenCLIP B/32 r4 | +0.0802 [+0.0798, +0.0806] | +0.0864 [+0.0834, +0.0902] | +0.0996 [+0.0973, +0.1014] | −0.0195 [−0.0214, −0.0174] | −0.0062 [−0.0099, −0.0029] |
| CLIP B/32 r4 | −0.0304 [−0.0338, −0.0282] | −0.0204 [−0.0229, −0.0187] | +0.0166 [+0.0122, +0.0209] | −0.0470 [−0.0537, −0.0409] | −0.0100 [−0.0113, −0.0087] |
| CLIP B/16 r4 | −0.0166 [−0.0179, −0.0152] | +0.0124 [+0.0104, +0.0141] | +0.0376 [+0.0335, +0.0416] | −0.0541 [−0.0592, −0.0496] | −0.0289 [−0.0317, −0.0265] |
| SigLIP B/16 r8 | +0.0664 [+0.0611, +0.0703] | −0.0114 [−0.0154, −0.0062] | +0.0522 [+0.0509, +0.0535] | **+0.0142 [+0.0081, +0.0181]** | +0.0778 [+0.0753, +0.0803] |
| BioCLIP B/16 r4 (n=3) | −0.3671 [−0.3786, −0.3584] | −0.4515 [−0.4625, −0.4346] | −0.2927 [−0.2952, −0.2914] | −0.0744 [−0.0834, −0.0669] | +0.0844 [+0.0560, +0.1041] |

Every non-SigLIP arm difference excludes zero with the seed pairing kept; the SigLIP `text − vision` difference
is **positive**, i.e. the reversal the paper reports is resolved too (+0.0142 [+0.0081, +0.0181], five seeds).

`tab:vlm` (13 seeds, reduction %): both-position 98.57 [98.33, 98.81]; text-only 96.74 [96.57, 96.88];
vision-only 89.41 [88.82, 89.93]. Paired: text − both −1.82 [−2.09, −1.54]; text − vision +7.34 [+6.80, +7.93];
both − vision +9.16 [+8.69, +9.68]. With the seed pairing kept the three arms separate on all 13 seeds, which
matches the manuscript's disjoint-range statement.

`tab:llava` (3 seeds, change %): text-only 73.27 [67.61, 83.92]; both 95.66 [86.04, 105.43];
vision-only 121.48 [99.53, 138.68]. Paired: text − both −22.39 [−37.15, −11.59];
text − vision −48.21 [−70.40, −31.92]; **both − vision −25.81 [−33.25, −13.48] — this interval excludes zero**,
whereas the manuscript reports the two vision-side arms as unresolved ("overlap in range and separate in mean by
a margin of about two pooled standard deviations"). Because the paired bootstrap removes the between-seed
variance, three seed pairs are enough to order them; the manuscript's more cautious phrasing rests on the
unpaired range comparison and is the conservative statement. Either phrasing can be defended, but not both in
the same paragraph.

### 2.5 Draft sentences / footnote changes

**Insertion point PA-1** — `paper合/sections/empirical.tex`, caption of `tab:position_strict`
(`sec:empirical`, current lines 55–70), appended before `\label{tab:position_strict}`:

> "Each arm is a seed-level percentile bootstrap with the seed pairing kept ($20{,}000$ resamples; five seeds,
> three for BioCLIP): the $95\%$ interval on an arm mean is $\pm0.001$--$0.005$ on $\Delta$CG, and the arm
> differences that carry the argument exclude zero narrowly but consistently — text-only minus vision-only is
> $-0.057$ [$-0.063$, $-0.052$] on CLIP B/32 at rank $8$, $-0.019$ [$-0.021$, $-0.017$] on OpenCLIP,
> $-0.047$ [$-0.054$, $-0.041$] and $-0.054$ [$-0.059$, $-0.050$] on the two rank-matched rows, and
> $+0.014$ [$+0.008$, $+0.018$] on SigLIP, where the ordering reverses. The seed-to-seed standard deviation is
> $0.0006$--$0.006$ on the dual-encoder rows and $0.002$--$0.015$ on BioCLIP, whose three seeds carry the
> widest spread in the table."

**Insertion point PA-2** — `paper合/sections/supplement.tex`, caption of `tab:vlm` (`sec:vlm`, lines 266–272),
one sentence appended:

> "Spreads are population standard deviations over the thirteen seeds (sample standard deviations would be
> $0.46$, $0.30$ and $1.06$); a seed-level percentile bootstrap ($20{,}000$ resamples, seed pairing kept) puts
> the arms at $98.57$ [$98.33$, $98.81$] for both-position, $96.74$ [$96.57$, $96.88]$ for text-only and
> $89.41$ [$88.82$, $89.93]$ for vision-only, and every paired arm difference excludes zero."

**Insertion point PA-3** — `paper合/sections/supplement.tex`, caption of `tab:llava` (`sec:llava`, lines
347–353), one sentence appended:

> "With three seeds per arm the printed spreads are population standard deviations ($7.54$, $16.33$, $7.91$;
> the sample values are $9.23$, $20.00$, $9.69$) and the percentile bootstrap intervals are
> $[67.61$, $83.92]$, $[99.53$, $138.68]$ and $[86.04$, $105.43]$; keeping the seed pairing, the
> both-position and vision-only arms separate at $-25.8$ [$-33.2$, $-13.5]$ points, while the unpaired
> range comparison in the text does not separate them."

**Insertion point PA-4** — `paper合/sections/empirical.tex`, `\subsection{Experimental Design}`
(`sec:empirical`, line 15) currently reads "Statistical validation uses 5-seed experiments with Welch's
$t$-test and ANOVA." Draft:

> "Statistical validation uses 5-seed experiments with Welch's $t$-test and ANOVA, complemented where the
> comparison is seed-paired by a seed-level percentile bootstrap (`outputs/analysis/paperA_strict_bootstrap.json`,
> generated by `tools/_p1595_bootstrap_ci_round.py`)."

**Insertion point PA-5** — `paper合/sections/supplement.tex`, Section F
(`\section*{F. Provenance of the $R@1$ column of Table~\ref{tab:position_strict}}`, `sec:r1provenance`, line
302), one sentence added to the opening paragraph:

> "The $\Delta$CG column is additionally certified column-wise: all eighteen cells reproduce from the per-seed
> JSON and are stable under a seed-level bootstrap, whose intervals are reported in the caption of
> Table~\ref{tab:position_strict}."

### 2.6 Suggested provenance-manifest entries (draft, not applied)

| label | generating script | result archive (field path) |
|---|---|---|
| `tab:position_strict` (ΔCG, 18 cells) | `tools/_p1595_bootstrap_ci_round.py` (verification) | `outputs/strict_freeze*/…/results.json::final_gap.centroid_gap − initial_gap.centroid_gap` |
| `tab:vlm` | `tools/_p1595_bootstrap_ci_round.py` (verification) | `outputs/vlm_clean_summary.json::per_arm.<arm>.per_seed` |
| `tab:llava` | `tools/_p1595_bootstrap_ci_round.py` (verification) | `outputs/canonical_caption_metric.json::runs.<arm>_s<seed>.clean.dg_star` |
| `tab:monitor_regret` | `tools/_p1408_a1_table.py`, `tools/_p1398_a1_combined.py` | `outputs/analysis/a1_monitor_split_diagnosis.json::summary`, `outputs/analysis/a1_monitor_combined.json::per_run` |

---

## 3. TASK A + B — one-line summary of what changed statistically

| claim | before | after |
|---|---|---|
| A1 monitoring mean regret | point means + a binomial SE that describes within-run accuracy noise | run-level 95 % intervals on each rule and on the paired differences, with n and the run-to-run sd stated |
| Paper A `tab:position_strict` | five-seed means, no uncertainty except a caption sd range | seed-level 95 % intervals per arm and per paired arm difference; the sd range corrected for BioCLIP |
| Paper A `tab:vlm`, `tab:llava` | mean ± population sd | same spreads, labelled as population sd, plus seed-level 95 % intervals and paired differences |
| P3 allocation arms (brief's examples) | mean ± sample sd, unpaired Welch test | same, plus paired bootstrap over the shared seeds and a bootstrap percentile for the random-allocation control |

---

## 4. Cross-paper addendum — the `+1478` / `+5048` figures (Paper 3, not Paper A)

Archive: `outputs/analysis/p3_alloc_results.json` (printed digits) over
`outputs/analysis/p3_alloc_runs/*/summary.json` (raw runs), generator `tools/_p440_aggregate.py`.
Manuscript: `paper3/paper_ieee/sections/experiments.tex`, "Counterfactual validation" (current lines 226–259).

| comparison | arms | n (paired seeds) | mean ± sd (ddof=1) | 95 % percentile CI | paired bootstrap |
|---|---|---|---|---|---|
| capacity-matched, lr 5e-5 | Γ-guided (`exp_beta_paper_0.137`) | 6 (42,123,456,789,1011,1213) | +1477.45 ± 1563.34 | [+273, +2564] | Γ-guided − uniform = **−3570** [−5524, −1850]; no resample reaches 0 |
| | uniform | 6 | +5047.55 ± 1899.90 | [+3775, +6500] | (archived Welch p = 0.00554, df = 9.64 — reproduces) |
| matched training loss, lr 3e-4 | Γ-guided | 2 (42,123) | +5967.75 ± 4775.1* | [2591, 9344] | Γ-guided − uniform = **+3125.7** [+369, +5883] |
| | uniform | 2 | +2842.07 ± 876.2* | [2223, 3462] | losses 0.5872 vs 0.5826 reproduce |
| lr 1e-3 (sweep) | Γ-guided / uniform | 2 each | +2867.4 ± 873.2 / +4935.8 ± 9083.7 | [2250, 3485] / [−1487, +11359] | the ordering returns, with the uniform arm spanning sign as the manuscript states |
| random allocation (control) | Γ-guided vs 10 random plans / 30 runs | 10 plans | Γ-guided +1477.45 sits at the **46.7th percentile** of the 30-run pool (printed "47th"; archived 46.667) | pool mean +3347.4 [+1790, +5113] over runs, [+1605, +5153] over plans | — |
| reversed rule (lr 5e-5) | `inverse_beta_paper_0.137` | 6 | +2470.21 ± 4111.22 | not bootstrapped here | archived p = 0.21 |

\* two-seed spread, reported for completeness only; the interval is the full range of two values.

Draft sentence for Paper 3 (if the brief's intent was to strengthen these arms):

> "Read as a paired comparison over the six shared seeds, the capacity-matched arms separate more sharply than
> the unpaired test alone suggests: the Γ-guided arm ends $3570$ alignment-energy units below uniform
> ($95\%$ percentile bootstrap [$-5524$, $-1850$]; no resample of the paired differences reaches zero), against
> Welch $p = 0.0055$ unpaired. At the matched training loss of $3\times10^{-4}$ the pairing instead reverses the
> sign, $+3126$ [$+369$, $+5883$] in favour of uniform, and the Γ-guided mean sits at the $47$th percentile of
> the random-allocation pool ($3347$ [$1790$, $5113]$ over thirty runs)."

---

## 5. Findings: digits that did NOT reproduce, and other defects

Severity key: **A** = must fix before submission; **B** = should fix (wording/consistency); **C** = cosmetic.

### 5.1 A1 — provenance appendix names an archive that covers only 6 of the table's 10 cells (**severity A**)

Cited: `tools/_p1408_a1_table.py` + `a1_monitor_split_diagnosis.json` (`paper_a1/main.tex` line 1718,
status `verified`). That archive has no `minCG`/`seqM` rule field. The four affected cells
(`minimum centroid gap` 1.45 / 3.65; `sequential minimum mass` 0.64 / 16.53) reproduce exactly from
`outputs/analysis/a1_monitor_combined.json::per_run` — so the numbers are sound and archived; only the citation
is incomplete. Fix = one appendix row (§1.5).

### 5.2 Paper A — `tab:position_strict` caption sd range excludes the BioCLIP row (**severity B**)

Caption: "a seed-to-seed standard deviation of $0.0006$--$0.006$ depending on the backbone".
Recomputed per-arm sample sds: 15 dual-encoder arms span 0.00056–0.00596 (0.0006–0.006 at printed precision);
BioCLIP's three arms are **0.0022 / 0.0104 / 0.0149**. The claim is right for the dual-encoder rows and wrong
if read as covering the table. Fix = the wording in insertion point PA-1.

### 5.3 Paper A — two decoder tables print the population sd (**severity B**)

`tab:vlm` (13 seeds) and `tab:llava` (3 seeds) print `ddof=0` sd (7.54 / 16.33 / 7.91 on LLaVA), while the
same paper's other spreads and the whole P3 line use the sample sd (`ddof=1`: 9.23 / 20.00 / 9.69). The numbers
are archived as printed (`vlm_clean_summary.json::per_arm.*.reduction_sd`), so this is a convention statement,
not an arithmetic error. Fix = label the convention in each caption (PA-2, PA-3).

### 5.4 Paper A — `tab:llava` "unresolved" phrasing versus the paired bootstrap (**severity B**)

The text reports both-position vs vision-only as unresolved (range overlap, "about two pooled standard
deviations"); the paired bootstrap over the same three seed pairs gives −25.81 [−33.25, −13.48], excluding zero.
Both statements are defensible; the draft in PA-3 keeps the unpaired caveat and adds the paired one.

### 5.5 Paper 3 — `+1478` is not the correct rounding of the archived mean (**severity C**)

`per_plan.exp_beta_paper_0.137.delta_E.mean = 1477.4502`; the manuscript prints `+1478` (and `+5048` for
5047.5485, which is correct). The value at the printed precision is `+1477`. Fix = print `+1477`, or quote one
more digit.

### 5.6 Paper 3 — the "47th percentile" is the archived 46.667th (**severity C, no change needed**)

The manuscript's "47th percentile" is the correct rounding of the archived
`p3_alloc_random_pool.json::gamma_mean_percentile_in_random_pool = 46.6667`, which `tools/_p458_random_pool_test.py`
(lines 204–207) defines as the fraction of the **30 individual random runs** below the Γ-guided mean. Recorded
here only because the same quantity computed over the ten *plan means* instead is the 20th percentile; the
archived definition is the 30-run one, and that is the one this script reproduces (46.667).

### 5.7 Items that reproduced exactly (no action)

A1: all ten `tab:monitor_regret` cells; the Introduction digits 16 / 353–1212 / 0.58 / 0.37 / 3.55 / 0.52;
the small-split digits 4 / 60–144 / 6.18 / 1.08 / 4.51 / 22.05 — every one recomputed from the raw per-epoch
records and asserted against the derived archives.
Paper A: all 18 ΔCG cells of `tab:position_strict` at four decimals; the `tab:vlm` means, sds, seed ranges and
the disjoint-range statement; the `tab:llava` means, sds and the text/both disjoint-range statement.
Paper 3 (addendum): `+1478 ± 1563`, `+5048 ± 1900`, the six-seed counts, `+5968` vs `+2842`, the matched
losses 0.5872 / 0.5826, the random pool `+3347 ± 4771`, the ten plans, the reversed rule `+2470 ± 4111`,
the 1e-3 sweep (`+2867 ± 873` vs `+4936 ± 9084`, spanning −1487 to +11359), and Welch `p = 0.0055`.