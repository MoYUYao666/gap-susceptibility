# P3 supplement text: applicability boundary of the Gamma-driven allocation

English-only artifact. Every number below is asserted against
`outputs/analysis/p3_gamma_robustness.json` by
`tools/_p1636_p3_gamma_robustness.py` (153 hard assertions, all passing; the archive is
rerun-stable, `meta.self_sha256 = de69adcfba29e4fa…` is recomputed only over the hashed part,
which excludes `generated_utc`; `--dry-run` writes nothing and leaves the file byte-identical).

---

## 1. Insertion point

| Item | Value |
|---|---|
| Target file | `paper3/paper_ieee/supplementary/supplementary.tex` |
| New section label | `app:gammarobust` |
| New table label | `tab:gammarobust` |
| Insert **after** | line **1736** (`\end{table*}`, closing `tab:smolvlm`) |
| Insert **before** | line **1738** (`\bibliographystyle{IEEEtran}`) |
| Line range to insert | **1737–1737** — insert the block at line 1737, which is the currently blank line between `\end{table*}` and the bibliography |
| Resulting section number | `S44` — the file contains **43** `\section` commands, the last being `app:smolvlm` at line 1716, so the new section renders as `S44` (numbering comes from `\renewcommand{\thesection}{S\arabic{section}}` at line 22) |
| Related existing section | `app:crossing10`, lines **1430–1487**, whose table `tab:crossing10` (label at line 1462) reports the statistics this section builds on |
| Document class facts | `\renewcommand{\thesection}{S\arabic{section}}` (line 22), `\renewcommand{\thetable}{S\arabic{table}}` (line 24); `booktabs` is loaded (line 5), so `\toprule/\midrule/\bottomrule` are available |

Anchors that must not move: `\end{table*}` at line 1736, `\bibliographystyle{IEEEtran}` at
line 1738, `\bibliography{references}` at line 1739, `\end{document}` at line 1741. The file has
1741 newline-separated lines and ends at line 1741.

---

## 2. LaTeX-ready draft: one paragraph plus one compact table

```latex
\section{Limits of the applicability boundary}
\label{app:gammarobust}

The allocation rule is a statement about the ordering of the four block couplings, so its
applicability is bounded by how well that ordering is resolved. Three independent limits are
measured here, all from archives already reported and without new training. \emph{Rank.} With ten
seeds per rank the sign of the effect is the same for every archived seed at every rank: all ten
runs are negative at $r=3,4,5$ and all ten positive at $r=6,7,8$, so the crossing between $r=5$
and $r=6$ is exact and has no counterexample in the sweep. Within one side of the crossing the
ordering is weaker: twelve of the fifteen rank pairs are ordered in the same direction for every
seed, and the three that are not are the adjacent pairs $r=3$ vs $r=4$, $r=4$ vs $r=5$ and
$r=7$ vs $r=8$. The ordering is also defined only against the alignment energy. On the same
300-question VQA-RAD evaluation the two ranks adjacent to the crossing give token F1 that is
statistically equivalent ($r=5$ minus $r=6$ equals $+0.0067$, TOST equivalent at the pre-declared
$\pm0.05$ margin), and exact-match accuracy reverses ($+0.0433$, $95\%$ CI $[+0.0033,+0.0833]$),
so no ordering of the two ranks is supported by that metric. \emph{Batch.} The crossing does not
survive a change of training batch. The archives contain three batch families; at the four ranks
shared by two of them, three of the four ranks disagree in sign, and the direction of the rank
trend reverses between the families (Spearman $\rho=+1.00$ for the \texttt{extra} family against
$\rho=-1.00$ for the \texttt{sweep} family over the same ranks), with the largest disagreement
$+383.0$ energy units at $r=8$. The batch-size comparison is much narrower: changing
\texttt{batch\_size} from $1$ to $2$ keeps the side of the crossing in all four archived cells
(two ranks, seed $42$, local and cloud) but moves the effect toward zero by $23.0$ to $34.0$ units.
\emph{Measurement noise.} Under a uniform relative perturbation of every block coupling, the
ordering of the coupling magnitudes can already change at a relative drift of $\rho=0.160$
($16.0\%$ per block, driven by the pair \texttt{llm\_shallow} vs \texttt{llm\_mid}), and all six
block pairs hold their order only up to $\rho=0.087$. Against that tolerance the repeated-estimate
dispersion that is actually archived for the same backbone is $4.227$ relative sd on the
\texttt{llm\_deep} block across three seeds --- $26.4$ times the ordering break-even --- and none
of the three archived seeds reproduces the point ordering of the blocks. The allocation objective
itself is far more robust than the ordering: the archived plan keeps its advantage over the
uniform rank plan on $\sum_k \mathrm{rank}_k\,|\Gamma_k|$ until $\rho=3.33$. Table~\ref{tab:gammarobust}
collects the break-even perturbations. What this rules out is any claim that the ordering of the
blocks is reproducible at the precision the allocation rule assumes; what it does not settle is
whether the plan would still help after a perturbation of that size, because no archived arm was
trained with a deliberately perturbed coupling.

\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrl@{}}
\toprule
quantity & $\rho$ & meaning & archive field \\
\midrule
ordering of $|\Gamma_k|$ can change        & $0.160$ & one adjacent pair may swap      & \texttt{rho\_order\_flip} \\
all six block pairs keep their order       & $0.087$ & every pairwise gap survives     & \texttt{rho\_split\_all\_pairs} \\
advantage on the allocation objective lost & $3.33$  & plan no longer beats uniform    & \texttt{rho\_advantage\_lost\_on\_linear\_objective} \\
\addlinespace
observed dispersion, \texttt{llm\_deep}    & $4.227$ & relative sd over three seeds    & \texttt{noise\_to\_tolerance\_ratios.worst\_observed\_relative\_sd} \\
same, in units of the ordering break-even  & $26.4$  & $\rho_{\mathrm{obs}}/\rho_{\mathrm{order}}$ & \texttt{...worst\_observed\_relative\_sd\_over\_rho\_order} \\
\bottomrule
\end{tabular}
\caption{Break-even perturbations of the block coupling $\Gamma$ under a uniform relative drift
$\Gamma_k\to\Gamma_k(1+\rho)$ on every block, computed in closed form from
\texttt{outputs/analysis/p3\_alloc\_plans.json} (\texttt{gamma\_abs}, \texttt{beta\_grid.beta\_paper\_0.137}).
The ordering of $|\Gamma_k|$ is the quantity the allocation acts on; it is the first thing to fail,
at the smallest $\rho$ in the table. The archived plan is
\texttt{plans.exp\_beta\_paper\_0.137} and the uniform plan is \texttt{plans.uniform}. The
$\rho$ values are relative drift, so they compare directly with the relative seed-to-seed sd of
repeated $\Gamma$ estimates in the last two rows, taken from
\texttt{outputs/analysis/p3\_alloc\_gamma\_qwen2vl2b.json} (\texttt{gamma\_across\_seeds}). Only
$0$ of $3$ archived seeds reproduce the point ordering. Source:
\texttt{tools/\_p1636\_p3\_gamma\_robustness.py} $\to$
\texttt{outputs/analysis/p3\_gamma\_robustness.json} (\texttt{noise\_break\_even.*}); input
archives \texttt{outputs/analysis/p3\_alloc\_plans.json},
\texttt{outputs/analysis/p3\_alloc\_gamma\_qwen2vl2b.json},
\texttt{outputs/analysis/p3\_alloc\_results.json}.}
\label{tab:gammarobust}
\end{table*}
```

---

## 3. Field path for every number in the paragraph and the table

Path prefix for all rows: `outputs/analysis/p3_gamma_robustness.json`.

| Number | Value | Field path |
|---|---|---|
| ten seeds per rank, $r=3$–$r=8$ | 10 | `rank_sensitivity.primary_n_seeds_per_rank` |
| mean at $r=3$ | $-120.7$ | `rank_sensitivity.per_rank.3.mean` |
| sd at $r=3$ | $6.58$ | `rank_sensitivity.per_rank.3.sd` |
| mean at $r=5$ | $-43.7$ | `rank_sensitivity.per_rank.5.mean` |
| sd at $r=5$ | $38.77$ | `rank_sensitivity.per_rank.5.sd` |
| mean at $r=6$ | $+87.3$ | `rank_sensitivity.per_rank.6.mean` |
| fully negative ranks | $[3,4,5]$ | `rank_sensitivity.sign_split.fully_negative_ranks` |
| fully positive ranks | $[6,7,8]$ | `rank_sensitivity.sign_split.fully_positive_ranks` |
| crossing | $[5,6]$ | `rank_sensitivity.sign_split.crossing_between` |
| ordered pairs / total | 12 / 15 | `rank_sensitivity.n_pairs_sign_separated`, `rank_sensitivity.n_pairs` |
| unordered pairs | `r3-r4`, `r4-r5`, `r7-r8` | `rank_sensitivity.non_sign_separated_pairs` |
| VQA-RAD questions | 300 | `rank_sensitivity.vqa_rad_300q.n_questions` |
| token F1, $r=5$ minus $r=6$ | $+0.0067$ | `rank_sensitivity.vqa_rad_300q.contrast_r5_minus_r6.token_f1` |
| token F1 equivalence at margin | `true` | `rank_sensitivity.vqa_rad_300q.contrast_r5_minus_r6.token_f1_equivalent_at_margin` |
| accuracy, $r=5$ minus $r=6$ | $+0.0433$ | `rank_sensitivity.vqa_rad_300q.contrast_r5_minus_r6.accuracy` |
| accuracy 95% CI | $[+0.0033,+0.0833]$ | `rank_sensitivity.vqa_rad_300q.contrast_r5_minus_r6.accuracy_ci95` |
| batch families | `E2` (12 runs), `extra` (15), `sweep` (45) | `batch_sensitivity.batch_families.*.n_runs` |
| total batch-family runs | 72 | `batch_sensitivity.support_counts.n_batch_families_total_runs` |
| shared ranks | 4 | `batch_sensitivity.support_counts.n_ranks_shared_by_two_families` |
| sign-disagreeing shared ranks | 3 | `batch_sensitivity.support_counts.n_shared_ranks_sign_disagreeing` |
| $\rho$ for `extra` over shared ranks | $+1.00$ | `batch_sensitivity.ordering_reversal_within_families.extra_spearman` |
| $\rho$ for `sweep` over shared ranks | $-1.00$ | `batch_sensitivity.ordering_reversal_within_families.sweep_spearman` |
| largest disagreement at $r=8$ | $+383.0$ | `batch_sensitivity.shared_rank_comparison.8.difference` |
| batch-size cells keeping the crossing side | 4 of 4 | `batch_sensitivity.conclusions.n_batchsize_cells_preserving_side_at_bs2` (and `…_at_bs1`), `…n_batchsize_cells` |
| batch-size shift range | $-34.0$ to $-23.0$ | `batch_sensitivity.batchsize_paired_by_rank.5.mean_difference`, `…6.mean_difference` |
| ordering break-even | $\rho=0.160$ | `noise_break_even.rho_order_flip` |
| binding pair | `llm_shallow>llm_mid` | `noise_break_even.rho_order_flip_binding_pair` |
| all-pairs break-even | $\rho=0.087$ | `noise_break_even.rho_split_all_pairs` |
| advantage break-even | $\rho=3.33$ | `noise_break_even.rho_advantage_lost_on_linear_objective` |
| observed relative sd | $4.227$ | `noise_break_even.noise_to_tolerance_ratios.worst_observed_relative_sd` |
| observed sd over break-even | $26.4$ | `noise_break_even.noise_to_tolerance_ratios.worst_observed_relative_sd_over_rho_order` |
| seeds reproducing the ordering | 0 of 3 | `noise_break_even.n_seeds_preserving_point_order`, `noise_break_even.n_seeds_available` |
| $\Gamma$ block ordering, LLaVA, five rank levels | Kendall $W=1.0$ | `rank_sensitivity.gamma_block_ordering_vs_rank.llava.kendall_W` |
| $\Gamma$ block ordering, Qwen2-VL-2B, three seeds | 3 distinct orderings | `rank_sensitivity.gamma_block_ordering_vs_rank.qwen_seeds.n_distinct_orderings` |
| Qwen2-VL-2B rank sweep, Spearman | $+0.964$ | `rank_sensitivity.downstream_qwen_rank_sweep.spearman_rank_vs_dE` |
| families with $\Gamma$ / with both | 4 / 2 | `backbone_coverage.n_families_with_gamma`, `backbone_coverage.n_families_with_both` |
| LLaVA has no own $\Gamma$ archive | `false` | `backbone_coverage.families.llava_1_5_7b.gamma_archived` |
| Qwen2-VL-2B $\Gamma$ batch size | 4 | `backbone_coverage.families.qwen2_vl_2b.gamma_batch_size` |
| archive self-hash | `de69adcfba29e4fa…` | `meta.self_sha256` |

Two values quoted in the paragraph are copied from the allocation archive rather than recomputed,
because the perturbation logic only scales them:

| Number | Value | Field path |
|---|---|---|
| `plans.exp_beta_paper_0.137` plan | `{vision 4, llm_shallow 2, llm_mid 2, llm_deep 9}` | `noise_break_even.reference.point_allocation` (source: `outputs/analysis/p3_alloc_plans.json :: plans.exp_beta_paper_0.137.ranks`) |
| objective ratio $\Gamma$ plan / uniform plan | $0.601$ | `noise_break_even.objective_values.gamma_over_uniform` |

---

## 4. Caveats that must survive into the supplement

1. **Which configurations are missing.**
   - $\Gamma$ is never measured on LLaVA-1.5-7B itself. The allocation for that paper arm is
     derived from CLIP ViT-B/32 by design (`backbone_coverage.families.llava_1_5_7b.gamma_archived
     = false`), so the noise claim in the paragraph is transported from CLIP and Qwen2-VL-2B and
     must be phrased that way.
   - $\Gamma$ is re-estimated at a second batch size on CLIP only, and only as four reference
     batch sizes ($2,4,8,16$) with three draws each. On the backbone that actually owns the
     allocation, Qwen2-VL-2B, `gamma_batch_size` is fixed at 4 with no second value
     (`backbone_coverage.families.qwen2_vl_2b.gamma_batch_size = 4`).
   - SigLIP and BLIP have $\Gamma$ and an archived induced allocation but **no** paired downstream
     effect, so no "this allocation helps" claim is available for them
     (`backbone_coverage.families.siglip.downstream_effect_archive = null`, same for `blip`).
   - LLaVA has a downstream task metric at only two ranks ($r=5$, $r=6$, 300 VQA-RAD questions),
     not across the sweep.
2. **How many seeds per cell.**
   - LLaVA primary rank sweep: **10 seeds** per rank at $r=3$–$r=8$. This is the only cell with a
     seed-paired statement of full strength.
   - Qwen2-VL-2B rank sweep: **3 seeds** per rank; its Spearman $+0.964$ over seven ranks passes
     through ranks with $n=1$ in the wide sweep, so it must be read as a trend, not as a tested
     ordering.
   - CLIP rank-sweep contrast $r=5$ vs $r=6$ at `n_train` 1024: **3 seeds** paired; elsewhere
     single runs.
   - Batch families (`E2`, `extra`, `sweep`): **3 seeds** per rank.
   - Batch-size comparison: **1 seed** (seed 42) at **2 ranks** in **2 environments** — four
     cells. Stated in the paragraph; must not be upgraded to a general claim.
   - Qwen2-VL-2B $\Gamma$ repeated estimates: **3 seeds** only; that is the entire basis of the
     "26.4× the break-even" and "0 of 3 seeds" statements.
   - Curvature probes: **3 batches** per probe, 8 probes over ranks 5–64, and 3 probes at $r=24$
     with different seed labels in the file names only (`meta` records no seed field).
3. **What the break-even does and does not cover.**
   - The break-even is defined on the ordering of $|\Gamma_k|$, on the all-pairs version of the
     same quantity, and on the allocation objective $\sum_k \mathrm{rank}_k|\Gamma_k|$. It is
     **not** a break-even for the archived plan itself: the softmin weights
     $e^{-\beta|\Gamma_k|}$ are reproduced exactly at every archived $\beta$
     (`noise_break_even.softmin_weight_check_summary.n_softmin_weights_reproduced` equals
     `n_plans_checked`), but the nearest archived plan to the target rank $B w_k$ reproduces
     **none** of the archived plans
     (`…n_archived_plans_reproduced_by_nearest_target_rank = 0`), so the map from weights to plan
     is not documented in the archives. At $\beta=0.137$ the weights are one-hot to below
     $10^{-260}$ (`noise_break_even.weights_are_one_hot_at_beta_paper = true`), which is why no
     drift makes the four target ranks equal
     (`noise_break_even.rho_uniform_target_ranks = null`).
   - The advantage break-even assumes the perturbation is a **uniform relative scaling of every
     block**. A perturbation that degrades only one block has a different break-even and is not
     computed here.
   - No archived arm was trained with a deliberately perturbed $\Gamma$, so the second half of the
     question — whether the plan still helps after the ordering is lost — is bounded on the
     objective only, not measured downstream.
4. **What must not be claimed.**
   - Do not claim the ordering is reproducible; the archived dispersion exceeds its break-even by
     $26.4\times$ and $0$ of $3$ seeds reproduce it.
   - Do not claim the crossing is batch-invariant; three of four shared ranks disagree in sign
     across batch families.
   - Do not quote the rank-sweep ordering as holding for the downstream task metric; at the two
     ranks where VQA-RAD exists, token F1 is equivalent and accuracy reverses.
5. **Governance note (outside the write scope of this task).**
   Table `tab:gammarobust` is new and reports our own results, so under
   `docs/PROVENANCE_MANIFEST_2026-10-20.md` it needs a manifest row
   (`tab:gammarobust` → `tools/_p1636_p3_gamma_robustness.py` →
   `outputs/analysis/p3_gamma_robustness.json`) plus the `Source:` line already included in the
   caption, and `python tools/_p1428_provenance_gate.py` must pass before the table enters the
   submission package. That manifest is **not** in this task's write scope and was not modified.