# Paper 3 allocation supplement text — Gamma-guided vs uniform, paired

**Status: draft, not inserted.** This file holds LaTeX-ready sentences and the exact insertion point.
Nothing in `paper3/` was modified by this round.

**Artifacts**

| Item | Path |
|---|---|
| Analysis script (idempotent, asserts every printed number) | `tools/_p1634_p3_allocation_paired.py` |
| Result archive (all field paths below resolve here) | `outputs/analysis/p3_allocation_paired_stats.json` |
| Addendum reproduced (earlier round, key `cross_paper_addendum_p3_allocation`) | `outputs/analysis/paperA_strict_bootstrap.json` |
| Archive SHA256 of the result file (canonical serialization, excluding `meta.result_sha256`) | `meta.result_sha256` = `e5a802c3d8e1446741e38941bd2c07b5a2919a20bbaec087a95fc40c24e07d72` |
| Reproduce | `python tools\_p1634_p3_allocation_paired.py` (exit 0 = all 49 addendum checks and 41 print-to-JSON assertions pass) |

All numbers below are read from `outputs/analysis/p3_allocation_paired_stats.json` and were re-derived from
the raw archives (`outputs/analysis/p3_alloc_runs/*/summary.json` and the per-run
`outputs/analysis/p3_alloc_runs/main/<plan>__seed<seed>.json`), not copied from the addendum.

---

## 1. Exact insertion point

**Primary (recommended): a new section in the supplement.**

* File: `paper3/paper_ieee/supplementary/supplementary.tex`
* Anchor: the end of `\section{Additional allocation baselines}` (`\label{app:baselines}`), which currently
  runs lines **926–968**; the section closes with the `table*` block for `\label{tab:ntkarm}`, whose last line
  is **968** (`\end{table*}`), and line **969** is blank, line **970** is
  `\section{Newer model family}`.
* Insert **between line 969 and line 970**, i.e. immediately before `\section{Newer model family}`.
  The new section label `app:allocation-paired` does not collide with any existing label
  (`app:baselines` and `app:newer` are the neighbours).
* Line range that carries the new text after insertion: **970–1032** (63 lines: `\section` + `\label`, four
  paragraphs, one `table*` block). The `\section{Newer model family}` heading and everything after it shift
  down by 63 lines.

**Alternative:** inside the main-text paragraph `paper3/paper_ieee/sections/experiments.tex` lines **231–259**
(the capacity-matched paragraph). If the claim is to be tightened in the main text rather than the supplement,
the two sentences marked *(main text option)* in section 2 below go between line **235** (`compared). That
comparison does not`) and line **236** (`survive being repeated at other learning rates, and we report the failure
rather than`). That paragraph carries the +1477 +5048 + Welch digits quoted in the supplement.

**Do not** edit `paper3/paper_ieee/sections_full/experiments.tex`: it is the superseded long version and still
contains the uncorrected `+1478` at line 331. The live file
`paper3/paper_ieee/sections/experiments.tex` already reads `+1477` (line 233).

---

## 2. LaTeX-ready text

```latex
\section{Paired re-analysis of the capacity-matched allocation comparison}
\label{app:allocation-paired}

The capacity-matched comparison of Section~IV-E is reported in the main text as an unpaired Welch test over
six seed pairs. Because both arms were run at the same six seeds
($42$, $123$, $456$, $789$, $1011$, $1213$), the seed pairing can be retained. Doing so sharpens the
contrast rather than weakening it: the seed-paired difference
$\Gamma$-guided minus uniform is $-3570$ (95\,\% percentile bootstrap over $20{,}000$ resamples of the six
paired differences, CI $[-5524,\,-1850]$), all six per-seed differences are negative, and no bootstrap resample
reaches zero. The unpaired Welch statistic on the same runs is $t=-3.55$, $\mathrm{df}=9.64$, $p=0.0055$, which
is the digit quoted in the main text; the two statements differ only in whether the between-seed variance is
removed, and neither supports an advantage for the $\Gamma$-guided allocation.

We also test equivalence rather than only difference. At a margin of one sample standard deviation of the
uniform arm ($1900$, a data-derived calibration rather than a pre-registered bound), the paired TOST does not
pass ($p=0.916$ for the binding one-sided test); TOST would not pass until the margin reached $6232$. The two
arms are therefore not equivalent: they are separated, in the direction opposite to the claim. The same test
on the matched-loss contrast gives $p=0.633$, so the reversal of sign there is not an equivalence result
either. Table~\ref{tab:alloc-paired} collects the contrasts; every number is recomputed by
\texttt{tools/\_p1634\_p3\_allocation\_paired.py} and archived in
\texttt{outputs/analysis/p3\_allocation\_paired\_stats.json}.

The two controls behave differently and both are reported. Matching the two arms on training loss as well as
on parameter budget reverses the sign: at $3\times10^{-4}$ the $\Gamma$-guided arm reaches $+5968$ against
$+2842$ for uniform, a seed-paired difference of $+3126$ (95\,\% CI $[+369,\,+5883]$, $n=2$ seeds per arm).
With two seeds this interval describes the seed spread and cannot carry a superiority claim, so we read the
reversal as a warning about the low-rate result rather than as evidence for the rule. Against the random
same-budget pool the comparison is unresolved in both pairings: pairing the ten-plan mean at the three shared
seeds gives $+1106$ (95\,\% CI $[-2494,\,+3884]$, $n=3$ seed-paired units), while pairing each plan against
the single $\Gamma$-guided plan gives $-1870$ (95\,\% CI $[-3654,\,-123]$). Two of the ten plans have a lower
mean than the $\Gamma$-guided arm, and both are lower by more than that arm's own seed-to-seed spread
($-2928$ and $-1700$); the next plan is $+264$ \emph{above} it, so it is not a third lower plan. The archived
verdict for this control is \textsc{underpowered-to-distinguish}: within-allocation seed range ($14331$)
exceeds the between-plan mean difference ($1870$), so neither pairing may be quoted as a win. Reversing the
rule (largest rank on the least coupled block) does not differ from uniform once the sample is doubled
($+2470 \pm 4111$, seed-paired difference against uniform $-2577$, 95\,\% CI $[-5418,\,+1255]$), and the
$10^{-3}$ learning-rate sweep is unresolved for the opposite reason: there the uniform arm's own spread
($\pm 9084$) exceeds the between-arm gap.

\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrrr@{}}
\toprule
contrast & seeds / pairs & mean difference & 95\,\% CI & TOST $p$ \\
\midrule
capacity-matched: guided $-$ uniform & 6 & $-3570$ & $[-5524,\,-1850]$ & $0.916$ \\
matched training loss: guided $-$ uniform & 2 & $+3126$ & $[+369,\,+5883]$ & $0.633$ \\
random pool: guided $-$ ten-plan mean & 3 & $+1106$ & $[-2494,\,+3884]$ & $0.357$ \\
reversed rule $-$ uniform & 6 & $-2577$ & $[-5418,\,+1255]$ & $0.628$ \\
$10^{-3}$ sweep: guided $-$ uniform & 2 & $-2068$ & $[-7874,\,+3737]$ & $0.509$ \\
\bottomrule
\end{tabular}
\caption{Paired contrasts for the allocation comparison (``guided'' is the $\Gamma$-guided
allocation). The TOST column is the two one-sided paired
$t$-test at $\alpha=0.05$ against a margin of $1900$ (one sample standard deviation of the uniform arm at the
capacity-matched setting); no contrast is equivalent at that margin, and the smallest margin at which TOST
would pass is reported per contrast in the archive. Means and intervals are percentile bootstrap
($20{,}000$ resamples) over the paired units. Archive:
\texttt{outputs/analysis/p3\_allocation\_paired\_stats.json}. Source:
\texttt{tools/\_p1634\_p3\_allocation\_paired.py}.}
\label{tab:alloc-paired}
\end{table*}
```

*(main text option)* — if a two-sentence tightening is wanted in
`paper3/paper_ieee/sections/experiments.tex` at lines 235–236 instead of a supplement section:

```latex
Pairing the two arms at the same six seeds strengthens rather than weakens this reading: the seed-paired
difference is $-3570$ (95\,\% bootstrap CI $[-5524,\,-1850]$), all six pairs are negative, and the arms are
not equivalent at a margin of one uniform sample standard deviation ($1900$; paired TOST $p=0.916$, the
smallest equivalent margin is $6232$). The supplement gives the paired form of every contrast
(Section~\ref{app:allocation-paired}).
```

---

## 3. Field paths for every number (one row per number)

All paths are relative to `outputs/analysis/p3_allocation_paired_stats.json` unless the "raw source" column
says otherwise. "Raw source" names the archive and field the value was re-derived from.

### 3.1 Capacity-matched arms (6 seeds: 42, 123, 456, 789, 1011, 1213)

| Printed number | JSON field path | Raw source (archive + field) |
|---|---|---|
| $\Gamma$-guided $+1477$ | `arms.exp_beta_paper_0.137.mean` = 1477.4501953125 | `outputs/analysis/p3_alloc_runs/main/summary.json::runs[plan=exp_beta_paper_0.137].delta_E`; also `outputs/analysis/p3_alloc_results.json::per_plan.exp_beta_paper_0.137.delta_E.mean` |
| $\Gamma$-guided $\pm 1563$ | `arms.exp_beta_paper_0.137.sd_ddof1_sample` = 1563.3373668985585 | `outputs/analysis/p3_alloc_results.json::per_plan.exp_beta_paper_0.137.delta_E.sd` (sample sd, ddof=1) |
| $\Gamma$-guided population sd $1427$ | `arms.exp_beta_paper_0.137.sd_ddof0_population` = 1427.1252347351176 | recomputed from `.../main/summary.json::runs[...].delta_E` |
| uniform $+5048$ | `arms.uniform.mean` = 5047.548502604167 | `outputs/analysis/p3_alloc_results.json::per_plan.uniform.delta_E.mean` |
| uniform $\pm 1900$ | `arms.uniform.sd_ddof1_sample` = 1899.897185980862 | `outputs/analysis/p3_alloc_results.json::per_plan.uniform.delta_E.sd` |
| uniform population sd $1734$ | `arms.uniform.sd_ddof0_population` = 1734.3609095038435 | recomputed from `.../main/summary.json::runs[...].delta_E` |
| per-seed values both arms | `arms.<plan>.values` / `arms.<plan>.seeds` | `.../main/summary.json::runs[plan=...].delta_E`, `::runs[...].seed` |
| arm training loss $\Gamma$-guided $1.3762$ | `arms.exp_beta_paper_0.137.loss_last_mean` = 1.3761667972236562 | `.../main/summary.json::runs[plan=exp_beta_paper_0.137].loss_last` |
| arm training loss uniform $1.3734$ | `arms.uniform.loss_last_mean` = 1.3733809256227687 | `.../main/summary.json::runs[plan=uniform].loss_last` |

### 3.2 Paired capacity-matched difference ($\Gamma$-guided minus uniform)

| Printed number | JSON field path | Raw source |
|---|---|---|
| mean $-3570$ | `paired.capacity_matched_by_seed.mean_difference` = −3570.0983072916665 | `.../main/summary.json::runs[plan=exp_beta_paper_0.137].delta_E` minus `::runs[plan=uniform].delta_E`, paired on the six shared seed labels |
| CI $[-5524,-1850]$ | `paired.capacity_matched_by_seed.ci95_percentile[0]` = −5524.157552083333, `[1]` = −1850.3134765625 | percentile bootstrap, 20000 resamples, paired units |
| all six pairs negative | `paired.capacity_matched_by_seed.n_pairs_negative` = 6, `pair_signs` = six `"negative"` | per-seed pairs in `paired.capacity_matched_by_seed.pairs` |
| no resample reaches zero | `paired.capacity_matched_by_seed.bootstrap_share_difference_le_zero` = 1.0 | same bootstrap |
| sd of the differences $2536$ | `paired.capacity_matched_by_seed.sd_of_differences_ddof1` = 2536.3620906915976 | recomputed |
| se of the mean difference $1035$ | `paired.capacity_matched_by_seed.se_of_mean_difference_ddof1` = 1035.4654875221943 | recomputed |
| Welch $t=-3.55$, df $9.64$, $p=0.0055$ | `controls.capacity_matched.welch_unpaired.welch_t` = −3.5542482207418193, `.df` = 9.642524000879323, `.p_two_sided` = 0.005537165222964369 | `outputs/analysis/p3_alloc_results.json::comparisons.exp_beta_paper_0.137.vs_uniform.Welch_t/df/p_two_sided` (archived; recomputed here and asserted equal, see `controls.capacity_matched.welch_unpaired.archived.matches_recomputation`) |
| budget is matched | `controls.capacity_matched.welch_unpaired.budget_note` | `outputs/analysis/p3_alloc_results.json::budget_params` = 7237632, `::same_budget_assert_passed` = true |

### 3.3 Equivalence (TOST) at the margin of one uniform sample sd

| Printed number | JSON field path | Raw source |
|---|---|---|
| margin $1900$ | `equivalence.capacity_matched_tost.margin` = 1899.897185980862 | derived: `arms.uniform.sd_ddof1_sample` |
| TOST $p=0.916$ | `equivalence.capacity_matched_tost.p_tost` = 0.9161678137131604 | two one-sided paired $t$-tests against $\pm 1900$, df = 5, on `arms.*.values` |
| smallest equivalent margin $6232$ | `equivalence.capacity_matched_tost.smallest_equivalent_margin` = 6231.847080944521 | max abs endpoint of `equivalence.capacity_matched_tost.ci95_paired_t` = [−6231.847080944521, −908.3495336388128] |
| equivalence rejected | `equivalence.capacity_matched_tost.equivalent_at_margin` = false, `equivalence_ci_within_margin` = false | same |
| margin is data-derived, not pre-registered | `equivalence.margin_policy.*` | `equivalence.margin_policy.derivation`, `.status`, `.why_this_margin` |
| matched-loss TOST $p=0.633$ | `equivalence.matched_loss_tost.p_tost` = 0.6331704591112892 | `.../exp_lr0.0003/summary.json` vs `.../uniform_lr0.0003/summary.json`, same margin |

### 3.4 Matched-loss control (lr $3\times10^{-4}$, 2 seeds: 42, 123)

| Printed number | JSON field path | Raw source |
|---|---|---|
| $\Gamma$-guided $+5968$ | `controls.matched_loss.arms.exp_beta_paper_0.137.mean` = 5967.751953125 | `outputs/analysis/p3_alloc_runs/exp_lr0.0003/summary.json::runs[plan=exp_beta_paper_0.137].delta_E` |
| $\Gamma$-guided $\pm 4775$ | `controls.matched_loss.arms.exp_beta_paper_0.137.sd_ddof1_sample` = 4775.103141896211 | same archive, recomputed |
| uniform $+2842$ | `controls.matched_loss.arms.uniform.mean` = 2842.068359375 | `outputs/analysis/p3_alloc_runs/uniform_lr0.0003/summary.json::runs[plan=uniform].delta_E` |
| uniform $\pm 876$ | `controls.matched_loss.arms.uniform.sd_ddof1_sample` = 876.1771174225967 | same archive, recomputed |
| paired difference $+3126$ | `controls.matched_loss.paired_by_seed.mean_difference` = 3125.68359375 | the two archives above, paired on seeds 42, 123 |
| CI $[+369,+5883]$ | `controls.matched_loss.paired_by_seed.ci95_percentile` = [368.7265625, 5882.640625] | percentile bootstrap, 2 paired units |
| both pairs positive | `controls.matched_loss.paired_by_seed.n_pairs_positive` = 2 | `controls.matched_loss.paired_by_seed.pairs` |
| $n=2$ seeds per arm | `controls.matched_loss.paired_by_seed.n_pairs` = 2, `.power_note` | `.../exp_lr0.0003/summary.json::seeds` = [42, 123] |
| losses coincide | `controls.matched_loss.loss_gap.gamma_minus_uniform` = 0.004612971678398026 | `loss_last` of the two archives; compare `controls.capacity_matched.loss_gap.gamma_minus_uniform` = 0.0027858716008875017 |
| $10^{-3}$ sweep $\pm 9084$ | `controls.learning_rate_sweep_1e-3.arms.uniform@lr0.001.sd_ddof1_sample` = 9083.67324995355, `.mean` = 4935.84765625, `.min` = −1487.279296875, `.max` = 11358.974609375 | `outputs/analysis/p3_alloc_runs/uniform_lr0.001/summary.json::runs[plan=uniform].delta_E` (2 seeds) |
| $10^{-3}$ sweep $\Gamma$-guided $+2867\pm 873$ | `controls.learning_rate_sweep_1e-3.arms.exp_beta_paper_0.137@lr0.001.mean` = 2867.408203125, `.sd_ddof1_sample` = 873.1774378742818 | `outputs/analysis/p3_alloc_runs/exp_lr0.001/summary.json::runs[plan=exp_beta_paper_0.137].delta_E` |

### 3.5 Random-allocation pool (10 plans x 3 seeds = 30 runs)

| Printed number | JSON field path | Raw source |
|---|---|---|
| pool mean $+3347$ | `controls.random_pool.pool_mean_over_runs.mean` = 3347.43046875 | `outputs/analysis/p3_alloc_random_pool.json::random_pool.mean` |
| pool sd $\pm 4771$ | `controls.random_pool.pool_mean_over_runs.sd_ddof1_sample` = 4771.180234255462 | `outputs/analysis/p3_alloc_random_pool.json::random_pool.sd` (over the 30 runs, ddof=1) |
| ten plans, thirty runs | `controls.random_pool.n_plans` = 10, `.n_runs` = 30, `.plans`, `.plan_seeds` | `outputs/analysis/p3_alloc_random_pool.json::random_plans_used`; per-run files `outputs/analysis/p3_alloc_runs/main/<plan>__seed<seed>.json` |
| plan means and their spread | `controls.random_pool.pool_mean_over_plans.mean` = 3347.43046875, `.sd_ddof1_sample` = 3010.0895615033232, `.min` = −1450.310546875, `.max` = 9125.866536458334 | `outputs/analysis/p3_alloc_random_pool.json::random_pool.per_plan[*].mean`, each asserted equal to the per-run files |
| plan 2 mean $+9126$, plan 3 mean $-1450$ | `controls.random_pool.pool_mean_over_plans.values` (order = `.plan_labels` = random_01, 02, 03, 05, 06, 07, 08, 09, 10, 11) | same |
| two plans below the $\Gamma$-guided mean | `controls.random_pool.plan_deviations_from_gamma_mean.plans_lower_than_gamma_mean` = 2, `.plans_beyond_one_gamma_sd_lower` = 2 | computed from `::random_pool.per_plan[*].mean` vs `::gamma.mean`, each per-plan deviation stored under `.per_plan` |
| the two deviations $-2928$, $-1700$ | `controls.random_pool.plan_deviations_from_gamma_mean.per_plan[0].difference_from_gamma_mean` = −2927.7607421875 (plan `random_03`), `.per_plan[1]` = −1699.6416015625 (plan `random_05`) | same |
| the next plan is $+264$ **above**, not below | `controls.random_pool.plan_deviations_from_gamma_mean.per_plan[2].difference_from_gamma_mean` = +263.8974609375 (plan `random_11`), `manuscript_cross_check.reconciles` = false | computed; see the discrepancy note in section 5 |
| percentile $47$ | `controls.random_pool.gamma_percentile_recomputed` = 46.666666666666664 | `outputs/analysis/p3_alloc_random_pool.json::random_pool.values` vs `::gamma.mean`; archived as `::gamma_mean_percentile_in_random_pool` = 46.666666666666664 |
| paired by seed $+1106$ | `paired.random_pool_by_seed.mean_difference` = 1106.465625 | per-run files at seeds 42, 123, 456 (all ten plans share them) vs `arms.exp_beta_paper_0.137` |
| paired by seed CI $[-2494,+3884]$ | `paired.random_pool_by_seed.ci95_percentile` = [−2493.7841796875, 3883.6976562500004] | percentile bootstrap, 3 paired units |
| paired by plan $-1870$ | `paired.random_pool_by_plan.mean_difference` = −1869.9802734375 | `outputs/analysis/p3_alloc_random_pool.json::random_pool.per_plan[*].mean` vs `::gamma.mean` |
| paired by plan CI $[-3654,-123]$ | `paired.random_pool_by_plan.ci95_percentile` = [−3653.5913427734376, −122.77513671875204] | percentile bootstrap, 10 units |
| underpowered | `controls.random_pool.archived_verdict` = "UNDERPOWERED_TO_DISTINGUISH", `.archived_power_diagnosis.max_within_plan_range` = 14331.41796875, `.between_plan_mean_diff` = 1869.9802734374998, `.ratio` = 7.663940722970946 | `outputs/analysis/p3_alloc_random_pool.json::verdict` and `::power_diagnosis` |
| four draws excluded | `controls.random_pool.excluded_plans` | `outputs/analysis/p3_alloc_random_pool.json::random_plans_excluded_as_duplicate_of_corner` |

### 3.6 Reversed rule (inverse-beta plan, 6 seeds) and other receipts

| Printed number | JSON field path | Raw source |
|---|---|---|
| reversed rule $+2470\pm 4111$ | `controls.reversed_rule.arms.inverse_beta_paper_0.137.mean` = 2470.2080078125, `.sd_ddof1_sample` = 4111.2182242525605 | `outputs/analysis/p3_alloc_results.json::per_plan.inverse_beta_paper_0.137.delta_E.mean/.sd`; recomputed from `.../main/summary.json::runs[plan=inverse_beta_paper_0.137].delta_E` |
| reversed rule vs uniform $-2577$ | `controls.reversed_rule.paired_by_seed_vs_uniform.mean_difference` = −2577.3404947916665 | the same archive, paired on the six seeds |
| reversed rule CI $[-5418,+1255]$ | `controls.reversed_rule.paired_by_seed_vs_uniform.ci95_percentile` | percentile bootstrap, 6 pairs |
| reversed rule TOST $p=0.628$ | `equivalence.reversed_rule_tost.p_tost` = 0.628307 | same margin 1900 |
| corner arm $+2344\pm 2426$ | `arms.corner.mean` = 2343.8977864583335, `arms.corner.sd_ddof1_sample` = 2426.091625165446 | `.../main/summary.json::runs[plan=corner].delta_E` |
| earlier LLaVA rank-level groups | `controls.earlier_llava_counterfactual_groups.groups.{Theory,Random,Violation_r16,Violation_r32}` | `paper3/scripts/outputs/experiments/all_results.json::<group>[*].E` (last minus first epoch); group-level only, **no seed/plan pairing with the allocation arms** |
| earlier group $\sigma$ ratio $30\times$ | `controls.earlier_llava_counterfactual_groups.groups.Theory.sd_ddof1_finite` = 26.73013280924732, `.Random.sd_ddof1_finite` = 808.0758921264124 | same archive; Random has 15 runs of which 2 are non-finite (`.Random.n_nonfinite` = 2) |
| every contrast in one place | `equivalence.all_contrasts_summary` (5 rows: contrast, n_pairs, mean difference, bootstrap CI, TOST $p$, smallest equivalent margin, source) | the paths above |
| rounding artefacts | `rounding_artefacts.*` | see section 4 |
| addendum reproduction | `addendum_reproduction.checks` (49 entries, `all_reproduced` = true) | each entry names its own `source` |

---

## 4. Caveats that must survive into the manuscript

1. **Seed count per arm is six, not more.** `arms.*.n` = 6 for every capacity-matched arm
   (seeds 42, 123, 456, 789, 1011, 1213; `arms.*.seeds`). The percentile CI covers those six seeds only.
   The universe of feasible same-budget allocations behind the pool is small
   (`outputs/analysis/p3_alloc_plans.json::n_exact_budget_allocations`), so "six seeds" is a seed count,
   not a sample of allocations.
2. **Matched-loss has two seeds per arm.** `controls.matched_loss.paired_by_seed.n_pairs` = 2,
   power note in `.power_note`. The $+3126$ CI is the spread of two numbers. It may be described as a sign
   reversal, never as a demonstrated advantage.
3. **The equivalence margin is data-derived, not pre-registered.** It is one sample sd of the uniform arm
   (`equivalence.margin_policy.pre_declared_margin` = 1899.897). Any equivalence sentence must carry that
   provenance, and the smallest equivalent margin (6232) must be given, otherwise "not equivalent" overstates
   what was tested.
4. **The random pool is underpowered by its own archived rule.** `controls.random_pool.archived_verdict` =
   UNDERPOWERED_TO_DISTINGUISH; within-plan seed range 14331 vs between-plan mean difference 1870. Neither
   the seed-paired ($+1106$) nor the plan-paired ($-1870$) form may be quoted as a win. The archived variance
   criterion also forbids a "lower variance" claim (`archived_variance_claim_allowed` = false).
5. **Only two plans are lower than the $\Gamma$-guided arm, and the "264" is a sign error.**
   `controls.random_pool.plan_deviations_from_gamma_mean.plans_lower_than_gamma_mean` = 2 and
   `manuscript_cross_check.reconciles` = false; see section 5 item 2. The live main text
   (`paper3/paper_ieee/sections/experiments.tex` lines 249–253) currently reads "Three of the ten
   allocations have a lower mean … the third is lower by 264", which this round does not reproduce.
6. **The $10^{-3}$ sweep is unresolved, not confirmatory.** `controls.learning_rate_sweep_1e-3` has two seeds
   per arm and the uniform arm's sd (9084) exceeds the between-arm gap; the ordering "returns" only in the
   mean.
7. **$+1478$ is a rounding artefact.** `rounding_artefacts.printed_plus_1478_vs_archive`: archive mean
   1477.4501953125 → correctly rounded $+1477$; `artefact` = true. The live main text already reads +1477
   (`paper3/paper_ieee/sections/experiments.tex` line 233); the superseded
   `paper3/paper_ieee/sections_full/experiments.tex` line 331 still reads +1478 and must not be reused for
   the submission.
8. **Digits that are *not* artefacts** (checked so they are not "corrected" by mistake):
   `rounding_artefacts.welch_p_printed_0_0055.artefact` = false (0.0055371652 → 0.0055 at four decimals,
   safe; at five decimals it would be 0.00554) and
   `rounding_artefacts.gamma_percentile_printed_47.artefact` = false (46.6667 → 47th percentile).
   The only genuine artefact in this family is +1478.
9. **The earlier rank-level LLaVA groups cannot be paired with the allocation arms.**
   `controls.earlier_llava_counterfactual_groups.groups.*.note`: `paper3/scripts/outputs/experiments/`
   carries no seed/plan linkage to `p3_alloc_runs`, and the random group there varies rank and capacity
   together. Use those groups only at group level.
10. **The pool's per-plan seeds are recovered from per-run files, not from the pooled archive.**
   `controls.random_pool.plan_seeds` shows seeds 42/123/456 for all ten plans; they are read from
   `outputs/analysis/p3_alloc_runs/main/<plan>__seed<seed>.json` and asserted to reconcile with
   `outputs/analysis/p3_alloc_random_pool.json::random_pool.per_plan[*].mean` and `::random_pool.values`.
   The derived archives alone do not record those seeds.

---

## 5. Things that could not be sourced this round (do not quote as ours)

1. **The main-text pairing claim `+11.5` with 95 % CI `[+6.8, +16.2]` ($n=4$ pairs)**, at
   `paper3/paper_ieee/sections/experiments.tex` lines 256–259, is **not** in any archive this round loaded.
   The nearest fields are `outputs/analysis/p3_upgrade_analysis.json::theory_vs_random.mean_diff_end_E` =
   11.5 and `::theory_vs_random.ci95` = [..., 16.25], i.e. a different analysis file that was outside the
   commissioned archive list. That claim is therefore not reproduced, not contradicted, and not repeated in
   the draft above. If it is to stay in the manuscript it needs its own provenance round.
2. **The main text's third low random plan ("lower by 264") does not reconcile — it is the opposite sign.**
   `controls.random_pool.plan_deviations_from_gamma_mean`: only **two** plans have a mean below the
   $\Gamma$-guided mean of 1477.45 (`plans_lower_than_gamma_mean` = 2), namely `random_03` (−1450.31, i.e.
   −2927.76 relative) and `random_05` (−222.19, i.e. −1699.64 relative); both reproduce the manuscript's
   $-2928$ and $-1700$. The next-lowest plan is `random_11` with mean 1741.35, which is **+263.90 above** the
   $\Gamma$-guided mean, not below it by 264 — same magnitude, opposite sign
   (`manuscript_cross_check.reconciles` = false, `.recomputed_third_lowest` = 263.9). The two "beyond one
   arm sd" values do reproduce; the count of lower plans and the sign of the third do not. This is flagged for
   a separate round and is **not** resolved here.
3. **A pre-registered equivalence margin** does not exist anywhere in the archives; the margin used here is
   derived on the spot and is labelled as such.
4. **A per-seed archive for the random pool beyond the three shared seeds** does not exist (only 42/123/456),
   so a six-seed plan-paired comparison with the $\Gamma$-guided arm is not possible.