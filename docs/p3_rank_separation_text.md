# Paper 3 — rank-separation statistics: draft supplement text (S33 and S28)

**Status: DRAFT ONLY. No `.tex` file has been edited or is edited by this document.**
Every number below is produced by `tools/_p1595_p3_rank_separation.py` and carried in
`outputs/analysis/p3_rank_separation_extended.json`; the provenance table in section 7 gives the exact field path
for each one. Section 6 lists the open items that must be settled *before* any of this text is inserted.

Line numbers refer to `paper3/paper_ieee/supplementary/supplementary.tex` **as of 2026-10-24** (1682 lines).

---

## 1. What the extended analysis adds

| Question | Answer | Where |
|---|---|---|
| Which of the 15 rank pairs separate? | 14 of 15, before and after Holm–Bonferroni | `separation.pairs`, `separation.n_separating_holm_p05` |
| Which pair does not? | only the adjacent `r=7` vs `r=8` (`+40.0`, exact `p=0.0709`) | `conclusion.non_separating_pair_keys` |
| Is the quoted `r=5` vs `r=6` value `p≈1.1e-5` right? | yes — exactly `2/C(20,10) = 1.0825e-5`; it was asserted in the manuscript but had **no archive** until now | `separation.pairs` entry `rank_a=5, rank_b=6` → `p_exact` |
| Is the archived `r=3` vs `r=8` value reproduced? | yes, to machine precision (`1.082508822e-5`) | `separation.pairs` entry `rank_a=3, rank_b=8` → `p_exact` |
| Is the `r=5` effect equivalent to zero? | **no** — TOST `p=0.652` at the pre-declared margin of one seed sd (38.77); equivalence would need ±66.2 | `rank5_equivalence` |
| Does the VQA claim "both improve but do not order" hold? | on token F1 **yes** (TOST `p=0.0074` at ±0.05); on exact-match accuracy **no** — `r=5` is *higher* than `r=6` by `+0.0433` (95% CI `[+0.0033,+0.0833]`) | `vqa_equivalence.claim_verdict` |

The complete 15-pair matrix (difference, exact `p`, Holm `p`, 95% bootstrap CI of the difference, paired sign-flip
`p`) is in `separation.pairs`; the 6×6 matrix form is in `separation.matrix`.

---

## 2. Draft text for S33 — "Crossing position with ten seeds per rank" (`\label{app:crossing10}`)

### 2.1 Replacement caption (minimal edit; the table body itself is already correct)

Current caption is at lines 1422–1425. Replace it with:

```latex
\caption{Ten-seed crossing statistics. Every run at $r=3,4,5$ is negative and every run at $r=6,7,8$ is positive
(complete separation), so the crossing lies between $r=5$ and $r=6$. All fifteen rank pairs are tested, not only the
two quoted below: an exact two-sided permutation test over the $\binom{20}{10}=184756$ splits of the pooled runs
separates fourteen of the fifteen pairs at the $5\%$ level, and the same fourteen survive a Holm--Bonferroni
adjustment across the fifteen tests. The single unresolved pair is the adjacent $r=7$ vs $r=8$ comparison
(difference $+40.0$, $p=0.071$). The $r=5$ vs $r=6$ test attains the minimum attainable
$p=2/\binom{20}{10}=1.08\times10^{-5}$, and the extreme ranks $r=3$ vs $r=8$ give the same value.
Source: \texttt{tools/\_p1595\_p3\_rank\_separation.py} $\to$
\texttt{outputs/analysis/p3\_rank\_separation\_extended.json} (\texttt{separation.pairs},
\texttt{separation.n\_separating\_holm\_p05}); input archives
\texttt{paper3/scripts/outputs/experiments/cloud\_verify\_r*\_s*.json}, field \texttt{delta\_E}.}
```

### 2.2 Optional body paragraph (insert directly after `\end{table*}` on line 1427)

```latex
All fifteen rank pairs were tested, not only the two quoted above. Permuting the ten seed labels between the two rank
groups and enumerating every one of the $\binom{20}{10}=184756$ splits gives exact two-sided $p$-values: fourteen of
the fifteen pairs separate at the $5\%$ level and the same fourteen survive a Holm--Bonferroni adjustment across the
fifteen tests. The only pair that does not is the adjacent $r=7$ vs $r=8$ comparison (difference $+40.0$, exact
$p=0.071$, $95\%$ bootstrap CI of the difference $[-77.20,-0.25]$, which clears zero by $0.25$ energy units; we
report this pair as unresolved rather than ordered). Every other adjacent-rank difference is resolved: $r=3$ vs $r=4$
($-23.05$, $p=0.0100$), $r=4$ vs $r=5$ ($-53.95$, $p=0.00235$), $r=5$ vs $r=6$ ($-131.0$, $p=1.08\times10^{-5}$) and
$r=6$ vs $r=7$ ($-107.7$, $p=1.08\times10^{-5}$). Because the ten seed labels are the same in every rank, we also ran
the exact paired sign-flip permutation test over the $2^{10}=1024$ sign patterns of the ten paired differences: it
agrees on the completely ordered pairs (minimum attainable $p=2/1024=0.0020$, reached by twelve pairs including
$r=5$ vs $r=6$) and on the unresolved pair ($r=7$ vs $r=8$, $p=0.061$), but it is less sharp than the unpaired test
on the two smallest adjacent differences ($r=3$ vs $r=4$: $p=0.039$ versus $0.0100$; $r=4$ vs $r=5$: $0.014$ versus
$0.00235$), because the rank effect itself varies strongly from seed to seed.
```

### 2.3 Equivalence sentence for the near-zero rank (S33, or wherever the ten-seed `r=5` effect is called zero)

```latex
The ten-seed $r=5$ group is the smallest-magnitude negative rank but it is not statistically indistinguishable from
zero. A two-one-sided-tests equivalence test against zero with the margin pre-declared as one seed sd of that group
($\pm38.8$) gives TOST $p=0.652$; equivalence could be declared only at a margin of $\pm66.2$ ($1.71$ seed sd). The
$90\%$ interval of the group mean is $[-66.2,-21.2]$ and the $95\%$ interval is $[-71.4,-16.0]$, both wholly below
zero, so what the ten-seed data support is that $r=5$ still has a negative effect and that it is the last rank on the
negative side of the crossing, not that its effect is zero.
```

---

## 3. Draft text for S28 — "VQA-RAD downstream check" (`\label{app:vqa}`)

### 3.1 Replacement caption (current caption is at lines 1221–1224)

```latex
\caption{VQA-RAD downstream check at scale (real images, 300 held-out questions, paired by question across arms).
Both ranks improve over the base model on token F1 ($+0.0713$ at $r=5$ and $+0.0647$ at $r=6$; $95\%$ paired bootstrap
CIs $[+0.0204,+0.1235]$ and $[+0.0194,+0.1103]$). On exact-match accuracy the $r=5$ gain is resolved ($+0.0633$,
$95\%$ CI $[+0.0133,+0.1167]$) while the $r=6$ gain is not ($+0.0200$, $95\%$ CI $[-0.0233,+0.0633]$). The two ranks
do not order on token F1: the $r=5$ minus $r=6$ difference is $+0.0067$ and a two-one-sided-tests equivalence test
against zero is significant at the pre-declared margin of $0.05$ (TOST $p=0.0074$). On exact-match accuracy the same
difference is $+0.0433$ ($95\%$ CI $[+0.0033,+0.0833]$), a small reversal rather than an ordering in the
alignment-energy direction, and equivalence at the $0.05$ margin is not declared (TOST $p=0.35$; the smallest margin
at which it can be declared is $0.0767$). The task check is therefore a small downstream gain for both ranks, with any
accuracy ordering bounded above $7.7$ points. Source: \texttt{tools/\_p1595\_p3\_rank\_separation.py} $\to$
\texttt{outputs/analysis/p3\_rank\_separation\_extended.json} (\texttt{vqa\_equivalence.contrasts},
\texttt{vqa\_equivalence.claim\_verdict}); archives
\texttt{outputs/analysis/cloud\_vqa1793\_\{base,5,6\}.json}, fields \texttt{accuracy}, \texttt{token\_f1},
\texttt{hypotheses}, \texttt{refs}.}
```

### 3.2 Optional body sentence (goes with the paragraph at lines 1206–1208)

```latex
The margin of $0.05$ is pre-declared rather than fitted: a single arm on 300 questions carries a binomial standard
error of about $0.027$--$0.028$ in accuracy, so differences below roughly two of those standard errors are at the resolution
limit of this evaluation set. The three archives are paired by question (identical held-out questions in the same
order in all three), which is what allows the differences above to be bootstrapped jointly.
```

### 3.3 Optional honesty sentence on the yes/no sub-accuracy (only if a reviewer raises it)

```latex
The gain is not uniform across question types: on the 174 yes/no questions the base model reaches $0.5517$ and the two
adapters $0.5345$ ($r=5$) and $0.5402$ ($r=6$), so the overall accuracy gain comes from the open-ended questions.
```

---

## 4. Draft rows for the claim table, S17 (lines 870, 871, 879)

| line | current text | proposed text |
|---|---|---|
| 870 | `... five seeds, exact $p=0.008$; ten seeds $r=3$--$8$ completely separated, $p\approx1.1\times10^{-5}$ (S33)` | `... five seeds, exact $p=0.008$; ten seeds $r=3$--$8$ completely separated, 14 of 15 rank pairs exact at the $5\%$ level, minimum attainable $p=2/\binom{20}{10}=1.08\times10^{-5}$ (S33)` |
| 871 | `crossing position reproducible with ten seeds & supported & complete separation (S33)` | `crossing position reproducible with ten seeds & supported & complete sign separation at $r=5$/$r=6$; all adjacent pairs except $r=7$ vs $r=8$ resolve (S33)` |
| 879 | `energy predicts VQA accuracy & reported, no positive claim & 1434 training pairs, 300 held-out questions (S28)` | `energy predicts VQA accuracy & reported, no positive claim & 300 held-out questions; $r=5$/$r=6$ do not order on token F1 (TOST $p=0.0074$), accuracy reversed by $+0.0433$ (S28)` — **the training-pair count is an open item, see flag F6** |

---

## 5. Insertion points

| # | File | Line (2026-10-24) | Anchor / label | Action |
|---|---|---|---|---|
| 1 | `paper3/paper_ieee/supplementary/supplementary.tex` | 1403–1427 | `\section{Crossing position with ten seeds per rank}` / `\label{app:crossing10}` / `\label{tab:crossing10}` | replace the caption at 1422–1425 (§2.1); optionally insert the paragraph of §2.2 after `\end{table*}` on line 1427, i.e. immediately before `\section{Curvature at high rank}` on line 1428 |
| 2 | same | 1203–1226 | `\section{VQA-RAD downstream check}` / `\label{app:vqa}` / `\label{tab:vqa}` | replace the caption at 1221–1224 (§3.1); optionally extend the paragraph at 1206–1208 (§3.2) |
| 3 | same | 1250–1255 | caption of `\label{tab:envcloud}` (S29) | **do not** change on account of this analysis; that caption's "near zero" refers to the four cross-environment stacks (`outputs/analysis/p3_env_matrix3.json`), a different data set — see flag F5 |
| 4 | same | 543 | ShareGPT second-dataset check (S9), `$r=5$: $+2.7$, near zero` | not affected: `+2.7` is genuinely near zero on that dataset |
| 5 | same | 655 | S11 paragraph, five-seed crossing, `p=0.008` | not affected: five-seed result, archive `outputs/analysis/p3_seeds_combined.json` field `permutation.p_two_sided` = `0.0079365` (= 2/252) |
| 6 | same | 773–774 | caption of `\label{tab:seed5}` (S14), five-seed `p=0.008` | not affected; same five-seed archive |
| 7 | same | 870, 871, 879 | claim table `\label{tab:claims}` (S17) | apply the rows of §4 |
| 8 | `docs/PROVENANCE_MANIFEST_2026-10-20.md` | — | provenance manifest | add one entry for the S33 matrix and one for the S28 equivalence, pointing at `outputs/analysis/p3_rank_separation_extended.json` (see section 7) |

There is no need to touch the main text: `paper3/paper_ieee/sections/experiments.tex` does not carry the
`1.1\times10^{-5}` value (checked 2026-10-24).

---

## 6. Flags and open items (resolve before inserting)

* **F1 — the ten-seed `r=5` vs `r=6` value was unarchived.** The caption at line 1424 asserts
  `p=2/\binom{20}{10}\approx1.1\times10^{-5}`; before this analysis the only archived **ten-seed** permutation value
  was `r=3` vs `r=8` (`outputs/analysis/p3_perm_r3_r8.json`). The value is now computed exactly and is correct
  (`1.082508822e-5` = `2/184756`, `separation.pairs` entry `rank_a=5, rank_b=6` → `p_exact`). Recommendation: quote
  the exact value and cite the new JSON rather than leaving an approximation with no archive behind it.
* **F2 — "complete separation" needs its scope fixed.** The manuscript's phrase means the *sign split* (every run at
  `r≤5` negative, every run at `r≥6` positive). It does **not** mean that all adjacent ranks are ordered: `r=7` vs
  `r=8` is not resolved (`p=0.0709`, ten seeds per group). §2.1/§2.2 word it that way; do not re-tighten it.
* **F3 — one bootstrap/permutation disagreement.** For `r=7` vs `r=8` the percentile bootstrap CI of the difference
  `[-77.20,-0.25]` excludes zero by `0.25` units while the exact permutation test does not separate (`p=0.0709`). The
  script records this per pair (`bootstrap_agrees_with_permutation`, false for exactly that pair) and the exact test
  is the decision rule. If both intervals and `p`-values are printed in the supplement, say which one governs.
* **F4 — the `r=5` "near zero" reading.** The ten-seed blank-image `r=5` group is *not* equivalent to zero
  (TOST `p=0.652` at ±38.8; the smallest equivalent margin is ±66.2). Any sentence that calls the ten-seed `r=5`
  effect zero should carry the qualifier of §2.3.
* **F5 — two different `r=5` claims must not be conflated.** The sign instability of `r=5` in S29 comes from four
  software/hardware stacks (`outputs/analysis/p3_env_matrix3.json` holds three of them: `r=5` = `-10.5` (torch 2.9),
  `-33.5` (torch 2.12), `+41.0` (torch 2.4); the fourth, torch 2.6, is `-35.5` in
  `paper3/scripts/outputs/experiments/verify_r5_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_a10_torch26.json`) — a
  different data set from the ten-seed blank-image protocol, where all ten `r=5` runs are negative. Both statements
  can stand, but they must not be merged into one.
* **F6 — VQA training-pair count is unresolved.** The S28 prose (line 1206) says "1434 training pairs per epoch,
  three epochs, 4302 optimizer steps". The three archives carry `meta.train_samples = 1793`, which matches the file
  name (`cloud_vqa1793`) and the training parquet (`paper3/train-vqarad.parquet`, 1793 rows, read 2026-10-24). No
  archive field containing `1434` or `4302` was found. **Do not guess**: either locate the source of `1434` or
  correct the sentence to the archived value `1793` (`4302` would then have to be re-derived).
* **F7 — the accuracy reversal is currently understated.** The S28 caption says "no rank ordering consistent with the
  alignment-energy picture"; the archived data are stronger than that: `r=5` beats `r=6` by `+0.0433` accuracy with a
  95% CI excluding zero. §3.1 states the reversal and the `7.7`-point bound.
* **F8 — table body check (no action).** The S33 table values in the `.tex` were re-derived from the 60 archives and
  match exactly, including `r=3` sd `6.6` (computed `6.5752`), `r=8` sd `56.8` (computed `56.8385`), and every
  mean/min/max.
* **F9 — incidental, outside the S33/S28 scope.** The S29 caption (line 1254–1255) cites the fourth environment as
  `paper3/scripts/outputs/experiments/verify\_r5\_s42\_*\_a10\_torch26.json`, which covers only the `r=5` row; the
  `r=6` row of that stack (`+42.0`) lives in
  `paper3/scripts/outputs/experiments/verify\_r6\_s42\_lr5e-05\_nw\_float1\_adamw\_e3\_bcuniform\_a12\_torch26.json`.
  Both files were read on 2026-10-24 and carry the values printed in the S29 table. Flagged for the provenance pass,
  not fixed here.

---

## 7. Provenance table

Script for every row: **`tools/_p1595_p3_rank_separation.py`** (idempotent; 83 assertions, all passing).
JSON for every row: **`outputs/analysis/p3_rank_separation_extended.json`**.
Input archives for the rank rows: `paper3/scripts/outputs/experiments/cloud_verify_r<R>_s*.json`, field `delta_E`,
excluding file names containing `partial`, `imgs` or `_e1_` — the same primary (blank-image, text-only) arm used by
`tools/_p1543_robust_stats_10seed.py`, `tools/_p1560_update_c1_d3.py` and `tools/_p1565_quick_stats.py`.

| Quantity | Value | JSON field path |
|---|---|---|
| per-rank mean / sd / min / max, `n` = 10 each | see `ranks` | `ranks.<r>.mean`, `.sd`, `.min`, `.max`, `.n_negative`, `.n_positive`, `.values_by_seed`, `.source_files` |
| sign split (crossing location) | 10/10 negative at `r=3,4,5`; 10/10 positive at `r=6,7,8` | `ranks.<r>.n_negative`, `ranks.<r>.n_positive`, `conclusion.sign_split` |
| 15 exact permutation `p`-values | `1.0825e-5` … `0.0709` | `separation.pairs[i].p_exact`, `.n_splits`, `.n_abs_diff_ge_observed` |
| Holm-adjusted `p`, separations counted | 14 of 15 | `separation.pairs[i].p_holm`, `separation.n_separating_holm_p05` |
| mean differences and their 95% bootstrap CIs | 15 pairs + 6×6 matrix | `separation.pairs[i].diff_a_minus_b`, `.ci95_diff`; `separation.matrix.mean_diff_a_minus_b`, `.ci95_lo`, `.ci95_hi` |
| paired sign-flip `p` (2^10 patterns) | `0.0020` … `0.0605`; 12 pairs at the minimum `2/1024` | `separation.pairs[i].p_paired_signflip`, `separation.n_pairs_at_paired_minimum`, `separation.paired_minimum_p` |
| `r=5` TOST against zero | margin `38.77`, `p=0.652`, min margin `66.17` | `rank5_equivalence.margin`, `.tost_p`, `.min_equivalent_margin`, `.min_equivalent_margin_in_seed_sd`, `.ci90_t`, `.ci95_t`, `.bootstrap` |
| VQA arm accuracies / token F1 | `0.3300`/`0.3563`, `0.3933`/`0.4276`, `0.3500`/`0.4210` | `vqa_equivalence.arms.{base,5,6}.accuracy`, `.token_f1`, `.yes_no_accuracy`, `.n_yes_no` |
| VQA paired differences, CIs, TOST | three contrasts × two metrics | `vqa_equivalence.contrasts.<a>_minus_<b>.{accuracy,token_f1}.delta`, `.ci95`, `.ci90`, `.tost_p`, `.min_equivalent_margin`, `.equivalent_at_declared_margin` |
| VQA verdicts | both improve / do not order | `vqa_equivalence.claim_verdict.both_ranks_improve_over_base`, `.ranks_do_not_order` |

VQA input archives: `outputs/analysis/cloud_vqa1793_base.json`, `cloud_vqa1793_5.json`, `cloud_vqa1793_6.json`
(produced by `tools/_p1516_p3_vqa_downstream.py`; 300 held-out questions each; fields `accuracy`, `token_f1`,
`yes_no_accuracy`, `n_yes_no`, `hypotheses`, `refs`, `meta.train_samples`).

Cross-checks the script asserts on every run (all pass):

* `r=4..7` reproduce `outputs/analysis/p3_robust_stats_10seed.json` (`ranks.<r>.mean/sd/median/mad/min/max/n`) exactly;
* `r=3`/`r=8` means reproduce `outputs/analysis/p3_perm_r3_r8.json` (`mean3` = `-120.7`, `mean8` = `235.0`) and the
  `r=3` vs `r=8` exact `p` reproduces its `p` field to `1e-15`;
* the exhaustive vectorised enumeration is re-derived for `r=3` vs `r=8` and `r=5` vs `r=6` by a plain-Python
  reference implementation (`n_ge = 2` both times);
* recomputed VQA `accuracy`, `token_f1` and `yes_no_accuracy` match the archived fields to `1e-12`, and the reference
  answer lists are identical across the three arms (which is what makes the paired bootstrap legitimate);
* means/sds from `numpy` are re-derived with `statistics.mean`/`statistics.stdev`.

---

## 8. How to reproduce

```bash
python tools/_p1595_p3_rank_separation.py
```

Runtime is under a minute; the exhaustive enumeration is `15 x 184756` splits. The script writes
`outputs/analysis/p3_rank_separation_extended.json` and prints an `OK`/`FAIL` ledger (83 checks, 0 failures on
2026-10-24). It contains no wall-clock field, so re-running reproduces the file byte for byte
(SHA-256 `8796452148D827109A5D42979D24E4492382C85E89487DEC552B00E62EF2EDAA`, verified by two consecutive runs).
`python -c "import scipy"` is required (`scipy.stats.t` supplies the `t` quantiles); `numpy` and the standard library
cover everything else.

Operational note: `outputs/analysis/p3_rank_separation_extended.json` is ignored by the root `.gitignore` (line 31,
`outputs/`) exactly like its sibling archives — `p3_robust_stats_10seed.json`, `p3_seeds_combined.json` and
`cloud_vqa1793_*.json` are all untracked in the root repository (`git ls-files --error-unmatch` fails for each, checked
2026-10-24). Publishing the new JSON therefore needs the same explicit add/copy step those archives already get.