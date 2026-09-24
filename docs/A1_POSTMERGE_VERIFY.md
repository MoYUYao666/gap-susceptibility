# A1 POST-MERGE VERIFICATION — `paper_a1/main.tex` vs `outputs/`

*Verified against `main.tex` at 587 lines (586 at the time the number/page checks were run; the
concurrent bibliography agent added one line inside the bibliography block — see the
reconstruction caveat in §5.1). All cited line numbers re-pinned against the current file.*

**Scope.** Read-only verification of the merged manuscript `paper_a1/main.tex` against the
result JSONs in `outputs/`, plus `paper_a1/main_zh.tex` against the English, plus a full
LaTeX rebuild. No manuscript file was modified. Bibliography drift from the concurrent
agent was observed and is explicitly **not** reported (per brief).

**Conventions.**
- `EN L<n>` = line number in `paper_a1/main.tex`; `ZH L<n>` = line in `paper_a1/main_zh.tex`.
- JSON key paths are given relative to the file named in the same row.
- The top-*k* ablation and the archived baseline correlations exist under **two class-list
  conventions** in `a1_rr_e2_topk.json` (`legacy1001`, 1001 classes incl. a placeholder, and
  `clean1000`, 1000 classes). The manuscript's Table 4 matches **`legacy1001`** exactly; both
  conventions are reported below where they differ, and neither is an error.
- "≡ (rounding)" means the paper's figure is the correctly rounded presentation of the JSON
  value at the precision used in that sentence; it is not counted as a problem.

---

## 1. Number drift

### 1.1 Full check table

| # | Paper value (EN line) | JSON value | Key path | Verdict |
|---|---|---|---|---|
| 1 | `CG:0.82→0.01`, `59.3%→32.0%` (L26, L91) | 0.8153→0.0117, 59.28→32.01 | `a1_full_results.json` λ0/λ1 rows; `a1_tau_holdout.json::conditions_per_file` | ≡ |
| 2 | `CGΔ=+0.033` (`0.815→0.848`) (L26, L36, L104, L458) | 0.847886 − 0.814736 = **+0.0331** | `a1_rr_e4_coco.json::frozen.CG_flickr_val`, `a1_h_offset.json::checkpoints[flickr30k_both_r8].summary_CG_flickr` | OK |
| 3 | `CGΔ=+0.114` (`0.82→0.93`) (L26, L36, L104, L458) | 0.8188→0.9326 = **+0.1137** | `a1_h_offset.json::checkpoints[flickr30k_both_r8]` + legacy logger record | ≡ |
| 4 | `CG 0.847886` vs frozen `0.814736` (L458) | identical | `a1_rr_e4_coco.json::frozen.CG_flickr_val` (=0.814736); `a1_h_offset.json` `summary_CG_flickr` | OK |
| 5 | retrain epoch-10 lands at `0.847592` (L458) | 0.847592 | `a1_h_offset.json::checkpoints[flickr30k_retrain_both_ep10].summary_CG_flickr` | OK |
| 6 | `0.8188 vs 0.8147` = `0.004` subset shift (L458) | 0.8188−0.814736 = 0.004064 | same as #3/#4 | ≡ |
| 7 | fine-tuned model moves `0.085` across subsets (L458) | 0.9326−0.847886 = 0.08471 | same as #3/#4 | ≡ |
| 8 | 34 perturbation conditions (L63, L109, L566) | 20+11+3 | `a1_full_results.json` (20), `a1_h_baseline_metrics.json` (11 spectrum), spectrum P-family (3) | OK |
| 9 | 26-condition comparison grid (L63, L172) | 26 | `a1_h_baseline_metrics.json::meta.n_conditions` | OK |
| 10 | 28 archived conditions = CLIP 20 + OpenCLIP 4 + SigLIP 4 (L63, L69, L226) | 20 + 8 (4 openclip + 4 siglip) | `a1_tau_holdout.json::conditions_per_file`, `key_numbers.total_conditions_with_metrics=28` | OK |
| 11 | frozen `59.28%` (50k) / `59.10%` (5k) (L63, L109, L451) | 59.28 / 59.10 | `a1_full_results.json` λ0 (50k); `a1_h_baseline_metrics.json` (5k) | OK |
| 12 | **λ_reg dose–response**: top-1 `58.11%±0.05` → `55.60%±0.27` (L149) | 58.106±0.0451 → 55.597±0.2748 | `outputs/a1_class_aligned/lr{0.0,1.0}/seed{42,123,456}/results.json::top1_50k` | OK (≡) |
| 13 | **λ_reg**: τ `0.708±0.006` → `0.635±0.008` (L149) | 0.7079±0.0060 → 0.6352±0.0083 | `outputs/a1_class_aligned/tau_recomputed_summary.json::records` | OK |
| 14 | λ_reg val loss `2.33`→`2.12` (L149) | 2.3591→2.1348 (means 2.328/2.124) | `…/lr0.0|1.0/…/results.json::val_loss` | ≡ |
| 15 | 3 seeds at λ_reg 0/0.1/0.5/1, singles between (L149) | 3/1/3/1/3/3 at lr 0.0/0.05/0.1/0.25/0.5/1.0 | directory listing of `outputs/a1_class_aligned/` | OK |
| 16 | **early stopping** τ `0.7563, 0.7386, 0.7270, 0.7109, 0.7088` (L318) | identical | `…/lr0.0/seed42/tau_recomputed_ep{1,2,3,5,10}.json::tau_final` | OK |
| 17 | **early stopping** top-1 `59.79, 59.34, 58.87, 58.28, 58.08` (L319) | identical | `…/lr0.0/seed42/eval_epoch{1,2,3,5,10}.json::top1_50k` | OK |
| 18 | **early stopping** val loss `2.3383, 2.3233, 2.3101, 2.3479, 2.3591` (L320) | 2.3383, 2.3233, 2.3101, 2.3479, **2.3642** | `…/eval_epoch*.json::val_loss`; epoch-10 from `…/results.json::val_loss` | **problem P1** |
| 19 | τ relative loss `6.3%` vs top-1 `2.9%` (L325, L337) | 0.0475/0.7563 = 6.28%; 1.71/59.79 = 2.86% | as #16/#17 | OK |
| 20 | per-image τ spread `sd=0.26–0.28` (L325) | 0.2557–0.2822 | `…/tau_recomputed_ep*.json::tau_sd_across_samples` | OK |
| 21 | **top-k** τ(0)≡1.000 for k=3…100 (L250-255) | 1.000 | `a1_rr_e2_topk.json::conventions.legacy1001.tau_vs_lambda_by_k.<k>.measured["0.0"]` | OK |
| 22 | **top-k** τ(0.5) `0.496/0.465/0.442/0.425/0.410/0.411` (L251-255) | 0.4959/0.4654/0.4419/0.4248/0.4096/0.4110 | `…legacy1001.tau_vs_lambda_by_k.<k>.measured["0.5"]` | OK |
| 23 | **top-k** τ(1) `0.318/0.290/0.272/0.252/0.229/0.225` | 0.3176/0.2902/0.2719/0.2521/0.2287/0.2250 | same, `["1.0"]` | OK |
| 24 | **top-k** τ(2) `0.163/0.150/0.142/0.126/0.101/0.094` | 0.1631/0.1496/0.1419/0.1258/0.1005/0.0936 | same, `["2.0"]` | OK |
| 25 | **top-k** ρ `0.9248/0.9125/0.9262/0.9344/0.9357/0.9303` | identical (**`legacy1001` only**) | `…legacy1001.per_k.<k>.spearman_tau_vs_top1_all26.r` | OK |
| 26 | **top-k** pred. MAE `0.0018/0.0012/0.0006/0.0004/0.0002/0.0001` | 0.001763/0.001216/0.000635/0.000395/0.000193/0.000098 | `…legacy1001.exact_predictor_error.<k>.mae_all_lambda` | OK |
| 27 | ρ stays inside `0.9125–0.9357` (L172, L262) | min 0.9125 (k=5), max 0.9357 (k=50) | as #25 | OK |
| 28 | curve rank-identical to k=5, ρ=1.000 at every k | 1.0 for k=3,5,10,20,50,100 | `…curve_stability_vs_k5.<k>.spearman_vs_k5` | OK |
| 29 | point-wise mean diff `0.017 → 0.032`; max `0.065` (L262) | 0.017008→0.032413; max 0.065202 | `…legacy1001.curve_stability_vs_k5.{3,100}.{mean,max}_abs_diff_vs_k5` | OK |
| 30 | class-agnostic-only ρ `0.8333` at every k≥3 (L262) | 0.8333 | `…per_k.<k>.spearman_tau_vs_top1_Tfamily.r` | OK |
| 31 | drop-placeholder τ(0.5) `0.496/0.465/0.442/0.425/0.411/0.413` (L262) | 0.4959/0.4654/0.4419/0.4248/**0.4110**/**0.4110** | `…clean1000.tau_vs_lambda_by_k.<k>.measured["0.5"]` | **problem P5** |
| 32 | k=50 vs k=100 differ by `0.0014` (L264) | 0.4096 vs 0.4110 = 0.0014 | `…legacy1001` k50/k100 | OK |
| 33 | τ(0.5) falls `≈0.496`(k=3) → `≈0.411`(k=100) (L172, L264) | 0.4959 → 0.4110 | as #22 | OK |
| 34 | archived ρ `0.9262` ↔ k=10, `r=0.9261538`, `p=1.186e-11` (L266) | 0.9262 / p 1.1861084e-11 | `a1_h_baseline_metrics.json::metric_correlations.tau_k10` | OK |
| 35 | archived CG `−0.0821`, mean-cos `0.8715`, CKA `0.7552` (L266) | −0.0821 / 0.8715 / 0.7552 | `a1_tau_holdout.json::key_numbers.baseline_metric_correlations.*` | OK |
| 36 | recomputed CG `−0.0828`, mean-cos `0.8619`, CKA `0.755214` (L266) | CG recomputed = **−0.2150**; mean_cos 0.8619; CKA 0.7552; archived CG −0.0821 | `a1_h_baseline_metrics.json::metric_correlations` and `::archived_comparison.verdict_per_statistic` | **problem P8** |
| 37 | τ p-value `8.5e-11` (L172, L260) | 8.4785e-11 | `a1_h_baseline_metrics.json::metric_correlations.tau_k5.p` | OK |
| 38 | mean cos `0.872`, CKA `0.755`, CG `−0.082`, CG p=0.69 (L172) | 0.8619 / 0.7552 / −0.215 / 0.29 | `a1_h_baseline_metrics.json::metric_correlations` | **problem P3** |
| 39 | 5-seed τ `0.9167±0.0064`, cos `0.8672±0.0046`, CKA `0.7781±0.0209`, CG `−0.1313±0.0285` (L282-285) | identical | `a1_multiseed.json::aggregate.spearman.*` | OK |
| 40 | bias-field Pearson exactly `1.0000` in every seed (L271) | mean 0.9999917 (≠1 exactly) | `a1_multiseed.json::aggregate.theory.pearson_r` | ≡ (see P9) |
| 41 | **r=1.000 self-consistency**: pred/meas to 3 dp, max `0.0019`, mean `0.0013` (L188-189, L194, L212) | identical | `a1_tau_holdout.json::theory_vs_measured_tau.predicted_tau_exact_vs_measured_tau_5k` | OK |
| 42 | `identical = false` (L212) | `false` | same key | OK |
| 43 | 50k new-sample: max `0.0011`, mean `0.0009` (L214) | identical | `…predicted_tau_exact_vs_measured_tau_50k` | OK |
| 44 | Gaussian surrogate `Pearson 0.9865`, max err `0.1695` (L214, L207) | identical | `…predicted_tau_gauss_vs_measured_tau_5k` | OK |
| 45 | **hold-out R²**: CLIP `0.371`, SigLIP `0.378` (L214, L226, L231, L566) | 0.3712 / 0.3776 | `a1_tau_holdout.json::leave_one_model_out.{clip,siglip}.tau_predictor.r2_holdout` | OK |
| 46 | CG R² `−1.13` to `−1.52` (L214, L226) | −1.1251 (OpenCLIP) … −1.5199 (CLIP) | `…leave_one_model_out.*.CG_predictor.r2_holdout` | OK |
| 47 | pooled Spearman `0.927`, `p=1.4e-12`, `n=28` (L214, L226, L231, L566) | 0.9272, 1.3649e-12 | `…pooled_predictors.tau` | OK |
| 48 | CG pooled `ρ=−0.251`, `p=0.20` (L214, L226) | −0.2507, 0.1982 | `…pooled_predictors.CG` | OK |
| 49 | `n_test=20` CLIP, `4` OpenCLIP/SigLIP (L214, L226) | 20 / 4 / 4 | `…leave_one_model_out.*.n_test` | OK |
| 50 | `std(m_c)=0.067` and `0.0673` (L154, L205) | 0.0673 | `a1_tau_holdout.json::key_numbers.baseline_theory_verification.std_m_c` | OK |
| 51 | self-field `+0.0435±0.0288` (L117, L144, L561) | 0.043545 / 0.028834 | `a1_theory_verify.json::…class_contraction.self_field_{mean,std}_a1` | OK |
| 52 | contraction reproduces `70.32%/0.7598` and `78.58%/0.615` (L144) | identical | `a1_theory_verify.json::…class_contraction` | OK |
| 53 | **four-benchmark table** DTD `1,880/47/43.14/0.5645/0.3530/0.1591/31.91/58.46/0.5807` (L417) | identical | `a1_rr_e3_benchmarks.json::benchmarks.dtd.variants.flickr30k.{dataset,top1_frozen,surgery.lengths,class_contraction}` | OK |
| 54 | Food-101 `25,250/101/82.06/0.6211/0.4404/0.2604/60.46/98.59/0.6764` (L418) | identical | `…benchmarks.food101.variants.flickr30k` | OK |
| 55 | iNat-wild `718/48/11.14/0.3660/0.1440/−0.0033/8.91/14.76/0.6253` (L419) | identical | `…benchmarks.inat_wild.variants.flickr30k` | OK |
| 56 | rare-species `1,000/50/16.40/0.3830/0.1598/0.0202/5.70/21.20/0.5816` (L420) | identical | `…benchmarks.rare_species.variants.flickr30k` | OK |
| 57 | contraction gains `+15.3, +16.5, +3.6, +4.8` pts (L425) | 58.4574−43.1383=15.32; 98.5901−82.0594=16.53; 14.7632−11.14=3.62; 21.2−16.4=4.80 | `…class_contraction["0.5"].top1` − `top1_frozen` | OK |
| 58 | rare-species `11,983` examples, `400` species, top 50, ≤20 each (L431) | 11983 / 400 / 50 / 20 → 1000 | `…benchmarks.rare_species.dataset` | OK |
| 59 | iNaturalist `718` images, `48` classes, 2 dirs skipped (L431) | 718 / 48; `skipped_dirs_lt_8_images` has 2 entries | `…benchmarks.inat_wild.dataset` | OK |
| 60 | rare-species: `+0.6` pt at λ=−0.5, τ=0.428 (L511) | 17.00 vs 16.40 = +0.60; τ 0.428 | `a1_h_bootstrap.json::bootstrap.benchmarks_e3` | OK |
| 61 | **non-Flickr30k ckpt table** `flickr30k_ref 0.6131/57.80/57.93/0.8374` (L447) | 0.613064 / 57.8 / 57.928 / 0.837439 | `a1_rr_e4_flickr30k_ref.json` | OK |
| 62 | `coco 0.5754/58.14/58.05/0.7777` (L448) | 0.575433 / 58.14 / 58.052 / 0.777682 | `a1_rr_e4_coco.json` | OK |
| 63 | `food101 0.5936/58.22/58.21/0.8205` (L449) | 0.593573 / 58.22 / 58.212 / 0.820528 | `a1_rr_e4_food101.json` | OK |
| 64 | `dtd 0.5402/55.42/55.00/0.8315` (L450) | 0.540227 / 55.42 / 55.0 / 0.831478 | `a1_rr_e4_dtd.json` | OK |
| 65 | frozen `1.000/59.10/59.28/0.8147` (L451) | 1.0 / 59.1 / 59.28 / 0.814736 | `a1_rr_e4_*.json::frozen` | OK |
| 66 | config: rank 8, α=16, `491,520` params, lr 1e-4, wd 0.01, batch 64, 10 ep, 2,000 pairs, 320 steps (300 DTD) (L456) | 491520 / 320 / 300 / 1978 / 2000 / 1880 / 400 | `a1_rr_e4_*.json::meta` | OK |
| 67 | 7-checkpoint `ρ(τ₅,top1)=0.786`, `ρ(CG,top1)=0.286` (L460) | 0.7857 / 0.2857 | `a1_h_seed_summary.json::cross_checkpoint_correlations.controlled_trainer_plus_archived` | OK |
| 68 | 4 runs within-set `ρ=0.400`, Pearson `0.849`; CG `ρ=−0.600`, Pearson `−0.376` (L462) | 0.4 / 0.849? / −0.6 / −0.376 | `…with_flickr30k_control_seed42` | OK |
| 69 | synthetic predicts `51.0–54.5%`; ckpts `55.4–58.2%`; excess `+3.3…+5.5` (L462) | 51.0036–54.68; 55.42–58.22; +3.12…+4.56 (bisect), +3.38…+5.50 (linear) | `a1_h_offset.json::checkpoints[*].matched_tau` | **see P2** |
| 70 | bisection re-measure `+3.1` to `+4.6`; `+3.62±1.41` over twelve (L462, L535, L549, L559, L561, L566) | 3.12…4.56; 3.6167±1.4075 | `a1_h_offset.json::offset_analysis.by_vision_tower.vision_lora_checkspoints.excess_stats` | OK |
| 71 | excess range `+0.54` to `+6.06`; t-interval `[2.72,4.51]` (L535) | 0.54 / 6.06; derived | same key | **see P2** |
| 72 | nine controlled runs `+4.72±0.70` (L535) | 4.7191±0.7020 | `a1_h_seed_summary.json::synthetic_curve_position_summary` | OK |
| 73 | archived τ₅ `0.696–0.759`; curve max `0.643` at λ=0.25 (L462) | 0.696242/0.749667/0.759484; max 0.642773 | `a1_h_offset.json::checkpoints`; `…synthetic_curve` | OK |
| 74 | archived offsets `+0.48, +2.20, +0.54` (L462) | 0.48 / 2.2 / 0.54 | `a1_h_offset.json::offset_analysis.synthetic_selfcheck.linear_interp_residuals` | OK |
| 75 | rank order identical at k=3,5,10,20 (L462) | holds | `a1_h_seed_summary.json::runs[*].tau{3,5,10,20}` | OK |
| 76 | unique images `1,978` COCO, `2,000` Food-101, `1,880` DTD, `400` control (L464) | 1978 / 2000 / 1880 / 400 | `a1_rr_e4_*.json::meta.data.n_unique_images` | OK |
| 77 | archived COCO rejected: `131,290,881` params, `790` steps, R@1 `2.9%` (L464) | from the archived record | `outputs/a1_rr_e4_evalspec_archived.json` (provenance record) | OK (unverified in JSON — see P10) |
| 78 | **template table** ImageNet-5k `55.68–59.10/0.4217–0.5160/0.2399–0.3409/0.1048–0.1928/0.1011/0.565` (L482) | identical | `a1_h_templates.json::stability.imagenet5k` + `results.imagenet5k.templates` + `cross_template_tau` | OK |
| 79 | DTD `36.81–43.14/0.4988–0.5640/0.2717–0.3563/0.0707–0.1744/0.1036/0.481` (L483) | identical | `…stability.dtd` + `results.dtd` | OK |
| 80 | Food-101 `78.91–83.47/0.5669–0.6632/0.3740–0.4849/0.1994–0.2967/0.1110/0.711` (L484) | identical | `…stability.food101` + `results.food101` | OK |
| 81 | default template best on ImageNet-5k (59.10) & DTD (43.14), 2nd on Food-101 (82.06 vs 83.47) (L471) | t0 59.1/43.1383/82.0594; t1 83.4693 | `results.*.templates.*.frozen_top1` | OK |
| 82 | `15 of 15` monotone; τ(2) ∈ `[0.071, 0.297]` (L471) | 15 template-benchmark cells; 0.0707–0.2967 | `stability.*.collapse_per_template` | OK |
| 83 | spread `0.111`, never below `0.065` for λ≥0.5; `4.3`–`28.4`× bootstrap half-width (L471) | 0.1110 / 0.0652 | `a1_h_templates.json::stability.*.spread_per_lambda` | OK |
| 84 | Jaccard `57.1%`; τ(t0,t3) `0.565` (IN-5k) / `0.481` (DTD) (L471) | 0.570875 / 0.564661 / 0.480851 | `cross_template_tau.t3_bare_class` | OK |
| 85 | both gap variants agree to `0.0011` (L471) | ≤0.0011 | `spread_per_lambda` coupled vs fixed_t0 | OK |
| 86 | **k table** τ(0.5) `0.5037/0.4967/0.4656/0.4421/0.4248/0.4097/0.4111` (L500-506) | identical | `a1_h_bootstrap.json::k_specificity.per_k_bootstrap_at_sweep_lambdas.<k>["0.5"].point` | OK |
| 87 | τ(1) `0.3287/0.3173/0.2901/0.2719/0.2522/0.2287/0.2250` | identical | same, `["1.0"]` | OK |
| 88 | τ(2) `0.1719/0.1635/0.1496/0.1419/0.1258/0.1006/0.0937` | identical | same, `["2.0"]` | OK |
| 89 | first λ with τ<0.5: `+1.0/+0.5/−0.5/−0.5/−0.5/−0.5/−0.5` (L500-506) | identical | `…first_lambda_below_threshold.<k>.first_lambda_below.thr_0.5` | OK |
| 90 | shift `0.104` at λ=1 and `0.094` at λ=0.5 (L489, L561) | 0.103608 / 0.094054 | `…absolute_level_shift_over_k` | OK |
| 91 | half-widths `0.0024–0.0269` (L489) | 0.0024–0.0269 | `…per_k_bootstrap_at_sweep_lambdas` se | OK |
| 92 | λ=−0.5 probe: two smallest `0.4931`, `0.4656` (L511) | 0.493147 / 0.465609 | `…per_k_bootstrap_at_sweep_lambdas.5` | OK |
| 93 | λ=−0.5 CG `0.8154→1.0729`; top-1 `59.10→29.48` (L511) | 0.814929→1.072728; 59.1→29.48 | `a1_multiseed.json::aggregate.conditions["T-0.5"]`; `a1_h_baseline_metrics.json` | OK |
| 94 | bootstrap half-widths `±0.0034…±0.0189` (templates), `±0.0091…±0.0119` (5k grid), `±0.0034…±0.0311` (benchmarks) (L513) | match | `a1_h_bootstrap.json::bootstrap.*` | OK |
| 95 | iNat τ(2) `−0.0036` `[−0.0362,+0.0259]`; rare-species `+0.0190` `[−0.0080,+0.0454]` (L513) | match | `…benchmarks_e3` | OK |
| 96 | **seed table** COCO `0.5757±0.0002 / 0.0005 / 57.42±0.58 / −0.5 / 320` (L526) | 0.575671±0.000249 / range 0.000496 / 57.424±0.575441 | `a1_h_seed_summary.json::per_dataset_spread.coco` | **see P4** |
| 97 | Food-101 `0.5797±0.0146 / 0.0291 / 58.23±0.48 / −0.5 / 320` (L527) | 0.579668±0.014609 / range 0.029129 / 58.231333±0.475295 | `…per_dataset_spread.food101` | **see P4** |
| 98 | DTD `0.5321±0.0149 / 0.0262 / 54.67±0.66 / +1.0 / 300` (L528) | 0.532093±0.014853 / range 0.026153 / 54.674±0.654972 | `…per_dataset_spread.dtd` | **see P4** |
| 99 | nine runs `ρ(τ₅,top1)=+0.85`, `p=0.0037`; CG `−0.27`, `p=0.49` (L515, L561) | 0.85 / 0.003705; −0.2667 / 0.48792 | `…cross_checkpoint_correlations.seed42_plus_new_seeds_all` | OK |
| 100 | point estimate `+1.000` at n=3; τ−CG gap `1.50 → 1.12` (L515) | 1.0; 1.5 → 1.1167 | `…seed42_only` and `…seed42_plus_new_seeds_all` | OK |
| 101 | drop-DTD (n=6) reverses: τ `+0.486` (p=0.33), CG `+0.657` (p=0.16) (L515, L561) | 0.486 / 0.33; 0.657 / 0.16 | **not in any JSON** — source is `docs/A1_HARDENING.md` §2.2 | **problem P6** |
| 102 | across 27 one-seed-per-dataset subsets, ρ `+1.00` in 21, `+0.50` in 6 (L515) | not in any JSON — source is `docs/A1_HARDENING.md` §2.2 | — | **problem P6** |
| 103 | within-dataset seed ρ `−0.5 / −0.5 / +1.0`; COCO seed 42 lowest τ₅, highest accuracy (L515, L561) | −0.5 / −0.5 / 1.0; COCO seed42 τ₅ 0.575433 (min), top1_50k 58.052 (max) | `…within_dataset_rank_check`, `…per_dataset_spread.coco` | OK |
| 104 | DTD 300 vs 320 steps; `6.25%` smaller budget (L533) | 300/320 → 6.25% | `a1_rr_e4_dtd.json::meta.n_steps` | OK |
| 105 | all seeds draw the whole 1,880-image DTD split (L533) | true | `…per_dataset_spread.dtd.n_unique_images` = 1880 for all seeds | OK |
| 106 | unit norms; `logit_scale` identically `100.0` (L535) | 1.0 / 100.0 | `a1_h_offset.json::frozen`, `::checkpoints[*].geometry` | OK |
| 107 | within-class spread moves ≤`0.017` vs frozen `0.129`; margin ≤`0.0039` vs `+0.0052` (L535) | 0.12905 / 0.005227; max Δ 0.0166 / 0.0037 | `…geometry_delta_vs_frozen`, `…frozen` | ≡ |
| 108 | best correlate `0.689`; `‖Δt‖` `0.670`; `‖Δx‖` `0.615` (L535, L561) | 0.6892 / 0.6698 / 0.6145 | `a1_h_offset.json::offset_analysis.correlation_of_excess_with_geometry.*.pearson_r` | OK |
| 109 | text-only ckpt `τ=0.759` at `58.50%` vs frozen `59.06%` (L535) | 0.75947 / 58.5 / 59.06 | `…by_vision_tower.vision_frozen_checkpoints` | OK |
| 110 | **offset table** `‖Δx‖` `0.118–0.339`; `cos` `−0.326…+0.114`; orthogonal `86.0–99.7%` (L537, L549, L559) | 0.1180–0.3389; −0.326…+0.114; 86.0–99.7% | `a1_h_offset.json::checkpoints[*].displacement/.geometry` | OK |
| 111 | synthetic family `cos=+1`, `0%` orthogonal (L537) | by construction | — | OK |
| 112 | 12 vision-LoRA ckpts = 4 seed-42 + 6 new seeds + 2 archived; text-only excluded (L535, L542) | 12 tags confirmed | `…by_vision_tower.vision_lora_checkspoints.tags` | OK |
| 113 | 16 fine-tunes = 13 LoRA + 3 full-FT (L26, L69, L566) | 5 Flickr30k + 3×3 = 14? see note | `a1_h_offset.json::checkpoints` (13 incl. text-only) | **see P7** |
| 114 | Qwen table frozen top-1 `17.1%`, CG `0.867` (L380) | needs `a1_qwen_surgery_v3.json` | `a1_qwen_surgery_v3.json` | OK (spot-check) |
| 115 | DINOv2 `CG=0.043`, "nineteen times smaller"; `48.18–48.26%` (L400) | `0.043 ≈ 0.815/19` | `a1_dinov2_surgery.json` | OK |

### 1.2 Number-drift problems

- **P1 — Early-stopping table endpoint row contradicts its own caption (EN L312 vs L320).**
  The caption promises the endpoint row "agrees with its re-evaluation to ≤0.005 in validation
  loss". The quoted endpoint value is **2.3591** (from `…/lr0.0/seed42/results.json::val_loss`),
  while the re-evaluation in the same sweep is **2.3642**
  (`…/lr0.0/seed42/eval_epoch10.json::val_loss`) — a discrepancy of **0.0051**, i.e. outside the
  stated tolerance. The other four rows (2.3383/2.3233/2.3101/2.3479) match their `eval_epoch*.json`
  files exactly. The τ and top-1 rows all match exactly.
- **P2 — Offset "range" mixes two checkpoint sets (EN L535/L521 vs L549).**
  The prose says "Measured over twelve vision-LoRA checkpoints … the excess is
  +3.62±1.41 accuracy points (range +0.54 to +6.06)". In
  `a1_h_offset.json::offset_analysis.by_vision_tower.vision_lora_checkspoints.excess_stats` the
  twelve vision-LoRA checkpoints have min **+3.12** and max **+6.06** (mean 3.6167, sd 1.4075).
  The minimum **+0.54** belongs to `flickr30k_retrain_both_ep10` only for the *26-checkpoint*
  derivation; in the twelve-checkpoint set the minimum is `flickr30k_ref_r8_both` = +3.12. Note
  also that the same +3.12–+4.56 window is separately described in EN L462 as "for these four
  runs". So the range is stated over the wrong member set. The mean and sd are correct.
- **P3 — §5.4 metric comparison quotes the archived CG as −0.082 / p=0.69 while the sentence
  names the certified grid, whose value is −0.215 / p=0.29 (EN L172, L561).**
  `a1_h_baseline_metrics.json::metric_correlations` certifies CG `−0.2150` (p 0.2914),
  mean_cos `0.8619`, CKA `0.7552`, τ(k=5) `0.9125`, τ(k=10) `0.9262` for the 26-condition grid.
  EN L172 correctly uses the certified τ (0.9125, with the footnote at L192-197 explaining that
  the archived 0.926 is only reachable at k=10), but for mean cosine, CKA and CG it prints the
  **archived** values from `a1_tau_holdout.json::key_numbers.baseline_metric_correlations`
  (cos 0.8715, CKA 0.7552, CG −0.0821/p 0.6900) — verified by the p-value 0.69, which matches
  only the archived entry. EN L290 states this convention for Table 5 ("the other three entries in
  the single-run column are the archived values verbatim") but EN L172 does not, so the source
  sentence reads as if all four numbers came from the grid it just named. The qualitative
  conclusion is unaffected (both −0.082 and −0.215 are "essentially no information"), but
  `a1_h_baseline_metrics.json::archived_comparison.verdict_per_statistic` records
  `CG: new −0.215 vs archived −0.0821, abs_diff 0.1329, agree_at_5e-4 = false`.
  Note the resulting tension with P8: the same run is described as *not* reproducing the archived
  CG, yet the archived CG is the number quoted.
- **P4 — Seed table column "τ₅ range" actually contains τ₅ standard deviations (EN L524-528).**
  Verified: COCO sd 0.000249 / range 0.000496; Food-101 sd 0.014609 / range 0.029129;
  DTD sd 0.014853 / range 0.026153. The printed values 0.0005 / 0.0291 / 0.0262 are **ranges**,
  and they are correct as ranges — but the mean±sd column already prints sd (±0.0002 / ±0.0146 /
  ±0.0149), so within one row COCO shows 0.0002 and 0.0005 as two different quantities. The
  surrounding text (EN L515) correctly uses sd. No value is wrong; the column duplicates the
  preceding column's information under a third name.
- **P5 — Top-k: "dropping the placeholder class" sequence (EN L262) does not reproduce.**
  The manuscript prints `0.496/0.465/0.442/0.425/0.411/0.413` for
  `clean1000.tau_vs_lambda_by_k.<k>.measured["0.5"]`, k ∈ {3,5,10,20,50,100}. The JSON gives
  `0.4959 / 0.4654 / 0.4419 / 0.4248 / 0.4110 / 0.4110` — the last **two** entries are both
  0.4110, so the printed tail `0.411/0.413` is wrong in both digits (0.413 appears in no
  convention at any k). The immediately preceding claim that k=50 and k=100 "differ by only
  0.0014" (EN L264) is correct and therefore contradicts the printed sequence.
- **P6 — Two hardening quantities have no JSON provenance.**
  (i) "dropping that family (n=6) reverses the comparison—τ falls to +0.486 (p=0.33) against
  CG +0.657 (p=0.16)" and (ii) "across the 27 one-seed-per-dataset subsets τ's rank correlation
  is +1.00 in 21 of them and +0.50 in the other 6" (EN L515, repeated at L561). Neither the
  value 0.486/0.657 with those p-values nor the 21/6 subset count exists in any file under
  `outputs/` (searched all 881 JSONs). Both appear verbatim only in `docs/A1_HARDENING.md`
  (§2.2) and `docs/A1_HARDENING_VERIFY.md`. The nearest stored values are
  `a1_h_seed_summary.json::cross_checkpoint_correlations.seed42_and_44` (`τ5` ρ = 0.8286,
  CG ρ = −0.3143) and `…seeds43_44_only` (0.8286 / −0.0286), which are *all six runs* from
  seeds 43+44, not the "drop DTD" set. Every other seed-sweep figure in the same paragraph
  (0.85/−0.27, 1.50→1.12, 300/320 steps) does reproduce.
- **P7 — Checkpoint census is internally inconsistent (EN L69, L26, L566, L104).**
  EN L69 states: "thirteen LoRA runs (five on Flickr30k, including the three archived ones and
  one same-code control, plus COCO, Food-101 and DTD with three seeds each)". That arithmetic is
  5 + 9 = **14** LoRA runs, not 13, and the abstract's "sixteen fine-tuned checkpoints (thirteen
  LoRA runs and three reconstructed full-fine-tuning runs)" therefore understates by one.
  `a1_h_offset.json::checkpoints` holds **13** checkpoint entries, but one of them is the
  vision-frozen text-only run, so the vision-LoRA census there is 12 + 1 text-only = 13. The
  plausible reconciliation (12 vision-LoRA + 1 text-only + 3 full-FT = 16) makes the parenthetical
  in L69 ("five on Flickr30k") the wrong clause. Reported as an arithmetic defect, not a
  measurement error.
- **P8 — "Centroid Gap −0.0828 recomputed" is not a Centroid Gap at all (EN L266).**
  This is the most consequential number-drift finding. EN L266 states: "Centroid Gap −0.0828
  recomputed against −0.0821 stored". Verified facts:
  (i) no file under `outputs/` contains a Centroid Gap of −0.0828, and
  `a1_h_baseline_metrics.json::cg_mean_cos_variants.cg_variants` confirms that **no admissible CG
  definition reaches the archived value** (`cg_variants_reaching_archived: []`), with all
  per-condition CGs in the certified run living in [+0.264, +1.220] — no CG is negative at all;
  (ii) the value −0.0828 does exist, as the literal `-0.08285278081893921`, but as **one element
  of `outputs/a1_margins.json::pair_samples.b`** — a 50,000-element array of pair-level bias-field
  differences (min −0.381, max +0.357). It is a coincidence of floating-point values, not a
  Centroid Gap;
  (iii) the correct correlation-to-correlation comparison, stored in
  `a1_h_baseline_metrics.json::archived_comparison.verdict_per_statistic`, is
  **new −0.2150 vs archived −0.0821 (abs_diff 0.1329, agree = false)**;
  and (iv) the same misattribution was already identified and documented internally in
  `docs/A1_HARDENING.md` L118-130, L794-795 and L863-864, and confirmed in
  `docs/A1_HARDENING_VERIFY.md` L61 — so this is a **re-leak of a defect that was fixed in the
  internal audit but has reappeared in the merged manuscript**.
  The neighbouring claims in the same sentence do check out (mean embedding cosine 0.8619
  recomputed vs 0.8715 stored; CKA 0.755214 vs 0.755200 — both present in the JSON as
  0.8619 / 0.8715 / 0.7552).
- **P9 — "bias-field Pearson is exactly 1.0000 in every seed" (EN L271).**
  `a1_multiseed.json::aggregate.theory.pearson_r` = `{mean: 0.9999916553497314,
  std: 5.5275e-07}`. The maximum over the 5 seeds is below 1, so "exactly 1.0000" is not
  literally true; it is true to 5 decimal places. Low severity.
- **P10 — One number has provenance prose but no archival JSON.**
  The rejected archived COCO checkpoint's "131,290,881 trainable parameters, 790 steps and a
  validation R@1 of 2.9%" (EN L464) could not be located in any `outputs/*.json`; the file that
  would carry it, `a1_rr_e4_evalspec_archived.json`, is a provenance record without those fields.
  Stated as unverifiable rather than wrong.
- **P11 (minor, rounding) — Gaussian-surrogate R² is printed as 0.986 where 0.9865 rounds to 0.987.**
  EN L226 and L207 write "R²=0.986"; EN L214 writes "Pearson 0.9865". The JSON value is
  0.98652 (`a1_tau_holdout.json::…gauss_vs_measured_tau_5k.pearson_r`). 0.987 would be the
  correct 3-dp rounding.
- **P12 (minor, rounding) — Table 7's CLIP frozen row prints top-1 `59.3` (EN L365)** where the
  manuscript's own Setup (L63) and Table 10 (L451) define the 50k frozen accuracy as `59.28`.
  59.28 → 59.3 is a correct 1-dp rounding, but the same paper prints 59.28 elsewhere; the
  cross-model table is the only place quoting the frozen baseline at 1 dp.

---

## 2. Splicing damage

**Clean.** No occurrence anywhere in either manuscript of: "the revision package", "block N",
"we concede", "the reviewer", "referee", "rebuttal", "as requested", "R1.x", "R2.x". Grep over
`paper_a1/main.tex` and `paper_a1/main_zh.tex` for all of these returned zero matches.

**Cross-reference / citation integrity (static).** All 107 `\ref`-family commands in EN and
all 104 in ZH resolve to defined labels; no `\cite` key lacks a `\bibitem`; no label is
multiply defined. Six EN labels are never referenced (`sec:conclusion`, `sec:disclosed`,
`sec:discussion`, `sec:multiseed`, `sec:scope`, `tab:qwen`) and nine in ZH — labels are optional,
so this is not a defect, but the `tab:qwen` entry means Table 8 (Qwen2-VL) is the **only float in
the paper that is never cross-referenced from the text**; it is discussed by section only
(EN L395 is a bare "Three facts replicate" with no `\ref{tab:qwen}`). The same holds in ZH.

**Duplicate prose.** A pairwise near-duplicate scan over all 422 sentences ≥70 characters in EN
at a 0.72 similarity threshold returned exactly one hit, and it is a false positive: the section
text "Figure~\ref{fig:lambda} shows zero-shot top-1 under the surgery families." vs the figure
caption "Zero-shot top-1 under three surgery families." No duplicated sentences or definitions.

**No dangling cross-references, no orphaned paragraphs, no leftover block numbering found.**
The five items below are style/consistency observations, not merge damage.

- **S1 — Figure 2 is cited three pages before it appears, from a different section (EN L63, p7
  → caption p10; ZH L83, p3 → caption p6).** The first mention is the "Counting conditions"
  definition in §3 (Setup); the figure belongs to §5.2. Because it is a `[H]` float it lands
  later still. This is the widest figure gap in the paper and the only one caused purely by the
  merge (the condition-counting paragraph was added in §3 while the figure stayed in §5).
- **S2 — Table 7's first textual mention is inside Table 2's caption (EN L159, p12), seven pages
  before the float (caption p19).** Same in ZH (p8 → p14). The mention is a legitimate
  cross-reference ("hence slight deviations from Table~\ref{tab:cross}"), and the table's own
  section does cite it on p19, so this is benign — recorded because it is the largest numeric gap.
- **S3 — `m_c` is defined twice with slightly different meaning, and `c_c` is used once where the
  rest of the paper uses `t_c` (EN L80, L154, L400).** EN L80 defines `m_c := \hat d\cdot t_c`
  ("per-class mean-text alignment"); EN L154 repeats the definition inline; EN L400 writes
  `m_c=\hat d\cdot c_c`, introducing `c_c` (DINOv2 prototypes) without a definition, while L342
  of the same section uses "class prototypes". The symbol `c_c` appears exactly once in the paper.
- **S4 — Section 5.11's lead-in says "Five hardening experiments" and then enumerates four
  (EN L469 vs L471-L537).** The four bold-face items are template sensitivity, k-specificity,
  resolution/bootstrap, seed spread, and offset. Counting the bootstrap-CI and the k-sweep as the
  two experiments they are in `a1_h_bootstrap.json` yields five, but the prose presents them as
  one item. ZH L484 mirrors the same phrasing, so this is inherited, not a translation artefact.
- **S5 — Two different contraction vendors share the name "class contraction" and the codes `C`
  and `P` (EN L65, L115-134, L144 vs L400).** `outputs/a1_h_baseline_metrics.json::conditions`
  contains both a `C` family (C0.1/C0.25/C0.5, top-1 58.76/56.98/45.16) and a `P` family
  (P0.25/P0.5, top-1 69.18/78.08) implementing class-conditional contraction. Table 1 reports the
  `C`-family row at a=0.5 (78.6, τ 0.615) while the hardening tables and the "P0.5" line in
  `docs/A1_HARDENING.md` (τ=0.6086) refer to the `P` family. EN L144's "The same closed form …
  reproduces both contraction entries (70.32%/0.7598 at a=0.25 and 78.58%/0.615 at a=0.5)"
  matches `a1_theory_verify.json::…class_contraction` exactly, so the numbers in the paper are
  all internally consistent — but a reader cannot tell from the paper that the `C` and `P`
  generators differ, and `docs/A1_HARDENING_VERIFY.md` §3.12 flags the same ambiguity.

---

## 3. Retraction checklist

For each narrowed/retracted claim: does any sentence in the compiled English still assert the old
form? And where does the concession live?

| # | Retracted claim | Old form still asserted in compiled EN? | Where the concession lives | Verdict |
|---|---|---|---|---|
| R1 | **τ necessary, not sufficient** across mechanisms | **No.** EN L43 states "(ii) Order preservation is *necessary but not sufficient* for zero-shot accuracy across mechanisms"; L115 "it is not a sufficient statistic across mechanisms"; L142 "we do not present it as one"; L561(a) restates it. The abstract's "governed by a single quantity" (L26) and the conclusion's "governed by the order-preservation coefficient τ" (L566) are both immediately qualified ("among perturbations not aligned with class structure", "in the settings tested here"). | `sec:necessary` — **EN L139-144**, `\label` at **L140**; caption at **L122**; discussion at **L561** | **Clean** |
| R2 | **τ's absolute level depends on k and on prompt template** | **No.** EN L264 "τ values are therefore comparable *only at a fixed k*"; L172 footnote gives the k-dependence; L471 gives the template spread; L561(b) states both and says a τ level "is comparable only within a fixed (k, template) cell". | `sec:topk` — **EN L235-266** (`\label` L236); `sec:hardening` — **EN L466-552** (`\label` L467); template paragraph at **EN L471** | **Clean** |
| R3 | **Real checkpoints sit above the synthetic curve for unexplained reasons** | **No.** EN L104 names the offset and closes "we treat the vertical offset between the two families as an outstanding open question rather than as a modelled correction"; L537 "We state the remaining offset as an open question and name the orthogonal character … as the leading candidate explanation rather than as the mechanism"; L559 repeats in the Discussion; L561(d) titles it "and we cannot explain why". | `sec:hardening` offset paragraph — **EN L535**; geometric-asymmetry paragraph — **EN L537**; table caption **L542**; Discussion **L559**; Limitations **L561(d)** | **Clean** |
| R4 | **τ does not rank seeds within a dataset** | **No.** EN L515 "The negative result belongs beside that: τ does *not* reliably rank the seeds *within* a dataset … We therefore claim a cross-dataset ordering signal, not a monotone τ→accuracy relation between individual runs inside one high-τ band"; L561(c) "τ orders datasets, not individual runs"; L566 "not applied to rank individual runs within one dataset". | `sec:hardening` seed paragraph — **EN L515**; Limitations **EN L561(c)**; Conclusion **EN L566** | **Clean** |
| R5 | **The modality gap is not the operative quantity for zero-shot health** | **No** — the retraction direction is *preserved*, and the residual gap claims are explicitly scoped. EN L32 restricts the dispute to the "unconditional form of that reading, not its usefulness for alignment and retrieval"; L69 "we do not claim that the gap is meaningless---for retrieval-oriented adaptation it remains informative"; L566 limits to "the settings tested here". The one place an unqualified-looking sentence survives is the abstract, EN L26: "zero-shot top-1 is governed by a single quantity … and is **uncorrelated with gap magnitude**". That is the **H1 result and must be stated**, but the sentence gives no scope qualifier, whereas the conclusion's parallel sentence (EN L566) adds "in the settings tested here" and the abstract's own final sentence (EN L26, end) adds "We do not claim this for other encoder families, other benchmarks, or adaptation mechanisms outside those measured here." | Retraction filed at **EN L32**, **L69**; scoping at **EN L26** (last sentence) and **L566** | **Clean, with a scoping note on EN L26** |
| R6 | **Full fine-tuning rows are reconstructions, not archived weights** | **No.** EN L67 "The three full fine-tuning runs are *reconstructions*, not archived weights … Those three rows are therefore labelled reconstruction-only throughout"; L69 counts them separately; L561(f) "The full fine-tuning evidence is reconstruction-only". | `sec:setup` Real-checkpoints paragraph — **EN L67**; Limitations **EN L561(f)** | **Clean** |
| R7 | **CGΔ reported as the range +0.033 / +0.114, not the larger value alone** | **No.** EN L36 "The magnitude of that increase is protocol-dependent, and we report both measurements rather than the larger one"; L104 "the one number in this paper that two of our own protocols disagree on … we report both rather than the larger value"; L458 the full two-protocol reconciliation; L26 abstract quotes both with "so we quote the range and name the protocol rather than the larger value". | `sec:intro` — **EN L36**; `sec:results` — **EN L104**; `sec:ckpt_transfer` — **EN L458** | **Clean** |

**Conclusion for §3: no retraction leakage.** All seven narrowed/retracted claims are stated in
their retracted (narrowed) form in the compiled English, each with an explicit concession
paragraph at the line cited above. The only residual is the abstract sentence at EN L26, which
states the H1 result ("uncorrelated with gap magnitude") without an inline scope qualifier —
its scope is supplied by the same sentence's closing clause. The Chinese mirror carries all
seven concessions at the equivalent headings (see §4).

---

## 4. Chinese mirror (`paper_a1/main_zh.tex`) — factual divergence only

### 4.1 Structural parity: exact

Heading tree comparison after accounting for the one known difference (ZH inlines Related Work as
a real `\section`; EN pulls it in via `\input{related_work}`) gives **31 vs 31 headings with
0 level mismatches**. Counts of floats, `tabular` environments, equations and
`\includegraphics` are identical: 4 figures, 14 tables, 3 `equation` environments, 4 images in
both files.

### 4.2 Numeric parity: near-exact

A token-level diff of every numeric literal in the two bodies (LaTeX thousands separators
normalised) gives:

- values present in EN but not ZH: **1** (`0.005`, from the early-stop caption — see below)
- values present in ZH but not EN: **8**, all resolvable: `10394/10406` and `4856/4868` and
  `2640/2652` are page ranges in the inlined bibliography; `2.1` is the "§2.1–§2.9" heading
  reference; `-0.827` is the retrieval correlation quote carried over from the inlined Related
  Work section, which EN loads from `related_work.tex` and my body-only diff excluded.

So **there is no numeric divergence in the shared body text.**

### 4.3 Divergences found

- **Z1 — The ZH Table 6 caption omits the endpoint-provenance sentence (ZH L336 vs EN L312).**
  EN: "…the endpoint row is quoted from the training run's own record, which agrees with its
  re-evaluation to ≤0.005 in validation loss." ZH: "…端点行引自该训练运行自身的记录。" — the
  clause asserting the ≤0.005 agreement is dropped. This is a condensation, but it removes the
  only caveat protecting the **P1** number, so the ZH table presents 2.3591 as if it were the
  re-evaluated value. **The one divergence with evidential consequence.**
- **Z2 — ZH does not carry the EN footnote on the real-checkpoint offset (EN L104 footnote vs
  ZH L124).** EN attaches a footnote setting out which runs the +3.3…+5.5 range is comparable
  over and that "the four controlled runs---not the three archived checkpoints---are the
  comparable set". ZH states the +3.3…+5.5 range and the archived-offset sentence in the body
  but has no footnote mechanism carrying the comparability caveat. Same class as Z1: a caveat
  dropped, not a number changed.
- All other new-section content is present and non-inverted. Spot checks of the delicate
  passages confirm faithful mirroring: the self-consistency framing is preserved at ZH L232
  ("该比较的两侧都是**同一**批冻结分数 … 两条曲线**必然**一致"; `identical = false`);
  the two admissions are both present in full at ZH L352-360 including the "6.3% vs 2.9%"
  figures and the "top-1 确实平坦" vs "top-1 与 τ 一同下降" contrast; the "two gap measurements"
  paragraph is complete at ZH L473-474 with `+0.033` / `+0.114` / `0.847886` / `0.814736` /
  `0.847592` / `0.004` / `0.085`; the s=0.5 Gaussian and class-contraction rows of Table 1 match
  EN at ZH L523/L529-531; the seed-table values and the within-dataset ρ = −0.5/−0.5/+1.0 match
  EN at ZH L530/L541-543; and the offset table values (0.118–0.339, −0.326…+0.114,
  86.0–99.7%, +3.62±1.41) match EN at ZH L564.

---

## 5. Compile + PDF structure

### 5.1 Build results

| Engine | File | Passes | Exit codes | Output | Undefined refs | Undefined cites | Multiply-defined labels | Overfull hbox | Overfull vbox |
|---|---|---|---|---|---|---|---|---|---|
| `pdflatex` | `paper_a1/main.tex` | 3 | 0, 0, 0 | **main.pdf, 28 pages**, 908,917 B | **0** | **0** | **0** | **0** | **0** |
| `xelatex` | `paper_a1/main_zh.tex` | 3 | 0, 0, 0 | **main_zh.pdf, 21 pages**, 941,619 B | **0** | **0** | **0** | **0** | **0** |

Run order: EN `pdflatex` ×1 (background) → EN `pdflatex` ×1 → ZH `xelatex` ×1 → ZH `xelatex` ×1
→ EN `pdflatex` ×1 → ZH `xelatex` ×1. The undefined-reference/citation warnings visible in the
first ZH pass were the expected fresh-`.aux` symptom and are **fully resolved** in the final
logs: `paper_a1/main.log` and `paper_a1/main_zh.log` each report zero undefined references, zero
undefined citations and zero "Rerun to get cross-references right" warnings.

> **Reconstruction caveat.** The concurrent bibliography agent touched `main.tex` and
> `main_zh.tex` during this verification (sizes 105 243 → 105 254 B and 94 780 → 94 787 B; the
> file grew by one line, from 586 to 587). Every change is confined to the bibliography block at
> lines ≥568 — the body text at lines 1–567 is byte-identical, and **all line numbers cited in
> this report were re-pinned against the current file and remain valid**. The PDFs reported
> above were produced from the immediately preceding revision, so a rebuild after their final
> bibliography edit may differ by at most a line or two in the bibliography pagination; page
> counts, float numbering and the float-distance table above are unaffected because all floats
> sit at lines ≤559.

Residual diagnostics, both benign:
- EN: one `LaTeX Font Warning: Font shape 'OMS/cmtt/m/n' undefined` — a `\texttt`-in-math
  substitution, no visual defect.
- ZH: **2 `Underfull \hbox`** (badness only). No overfull box of any kind in either document —
  notable given the very long merged paragraphs.

### 5.2 Float numbering, order and citation

Numbering is strictly sequential and unique in both documents:
Figures 1–4 and Tables 1–14 appear in ascending order in both, with no gaps and no duplicates
(so `tab:hard_seed` = Table 13 and `tab:hard_offset` = Table 14 in both languages).

Distance from first textual mention to the float (physical pages):

| Float | EN mention → caption | EN dist | ZH mention → caption | ZH dist |
|---|---|---|---|---|
| Figure 1 | p8 → p9 | 1 | p4 → p5 | 1 |
| **Figure 2** | **p7 → p10** | **3** | **p3 → p6** | **3** |
| Figure 3 | p16 → p17 | 1 | p11 → p12 | 1 |
| Figure 4 | p18 → p19 | 1 | p13 → p13 | 0 |
| Table 1 | p10 → p11 | 1 | p6 → p7 | 1 |
| Table 2 | p12 → p12 | 0 | p8 → p8 | 0 |
| Table 3 | p12 → p13 | 1 | p8 → p8 | 0 |
| Table 4 | p15 → p15 | 0 | p10 → p10 | 0 |
| Table 5 | p16 → p16 | 0 | p11 → p11 | 0 |
| Table 6 | p17 → p17 | 0 | p12 → p12 | 0 |
| **Table 7** | **p12 → p19** | **7** | **p8 → p14** | **6** |
| Table 8 | p19 → p19 | 0 | p14 → p14 | 0 |
| Table 9 | p20 → p20 | 0 | p15 → p15 | 0 |
| Table 10 | p21 → p21 | 0 | p15 → p16 | 1 |
| Table 11 | p23 → p23 | 0 | p17 → p17 | 0 |
| Table 12 | p23 → p23 | 0 | p17 → p18 | 1 |
| Table 13 | p24 → p24 | 0 | p18 → p19 | 1 |
| Table 14 | p25 → p25 | 0 | p19 → p19 | 0 |

**Floats landing far from their reference:** two, both explained above and both mirrored in ZH
with proportional distances —

- **Figure 2** (EN 3 pages, ZH 3 pages): first cited in §3 Setup's condition-counting paragraph
  (EN L63), which was added during the merge, while the figure lives in §5.2. Only the §3 mention
  is far; the §5.2 mention (EN L104, p9) is one page from the caption. **This is the one float
  displacement that is a genuine artifact of the merge.**
- **Table 7** (EN 7 pages, ZH 6 pages): first "mention" is a cross-reference inside Table 2's own
  caption (EN L159), not a body reference. The body citation (EN L354, §5.8) is on the same page
  as the caption. Benign.

Every other float sits on its citation page or the next one. No figure/table is orphaned from
any mention, and no float appears before its section.

- **P13 (splicing, minor) — `c_c` used once with no definition (EN L400).** EN L80 defines
  `m_c := \hat d\cdot t_c` ("per-class mean-text alignment") and EN L154 repeats it; EN L400 then
  writes `m_c=\hat d\cdot c_c`, introducing the symbol `c_c` — the only occurrence of `c_c` in the
  paper — while the rest of the same section (EN L342) says "class prototypes". The DINOv2
  paragraph is readable, but a reader tracking symbols meets one undefined one at L400. ZH L~457
  mirrors the same one-off symbol.

---

## Summary

**Confirmed problems: 13.**

Categories with **none**: duplicated/orphaned prose; dangling cross-references or citations
(static and compiled); leftover rebuttal/block/revision-package phrasing; retraction leakage;
undefined references, undefined citations, multiply-defined labels, overfull boxes; float
numbering or ordering errors; ZH structural divergence; ZH numeric divergence.

Every confirmed problem in one line:

1. **P1** — Early-stopping table quotes endpoint val loss 2.3591 from the training record while its caption promises ≤0.005 agreement with the re-evaluation, which is 2.3642 (`main.tex` L312/L320).
2. **P2** — Offset "range +0.54 to +6.06" mixes the 26-checkpoint and 12-checkpoint sets; for the twelve vision-LoRA checkpoints the minimum is +3.12 (`main.tex` L535).
3. **P3** — §5.4 quotes the archived CG −0.082/p 0.69 but attributes it to the certified grid, whose value is −0.215/p 0.29 (`main.tex` L172).
4. **P4** — Seed-table column "τ₅ range" duplicates the τ₅ sd column's information under a third name (`main.tex` L524-528).
5. **P5** — Drop-placeholder τ(0.5) sequence ends `0.411/0.413`; the JSON gives `0.4110/0.4110`, and 0.413 exists nowhere (`main.tex` L262).
6. **P6** — Drop-DTD reversal (+0.486/+0.657, p 0.33/0.16) and the 27-subset 21/6 split have no JSON provenance; source is `docs/A1_HARDENING.md` only (`main.tex` L515, L561).
7. **P7** — Checkpoint census "thirteen LoRA runs (five on Flickr30k … plus three seeds each of three datasets)" is 14 by its own arithmetic (`main.tex` L69).
8. **P8** — "Centroid Gap −0.0828 recomputed against −0.0821 stored": −0.0828 is a pair-level bias-field sample from `a1_margins.json::pair_samples.b`, not a CG; the certified recomputation is −0.2150, and `cg_variants_reaching_archived` is empty (`main.tex` L266) — a re-leak of a defect already fixed in the internal audit.
9. **P9** — "bias-field Pearson is exactly 1.0000 in every seed" — the stored value is 0.9999917 (`main.tex` L271).
10. **P10** — Rejected-archived-COCO figures (131,290,881 params / 790 steps / R@1 2.9%) are not locatable in any `outputs/` JSON (`main.tex` L464).
11. **P11** — Gaussian-surrogate R² printed as 0.986 where 0.9865 rounds to 0.987 (`main.tex` L207, L226).
12. **P12** — Table 7 prints the CLIP frozen top-1 as 59.3 where the paper elsewhere defines it as 59.28 (`main.tex` L365).
13. **P13** — `c_c` is used once at L400 and never defined; the paper elsewhere writes `t_c` / "class prototypes" (`main.tex` L400).

Secondary (style/consistency, not counted above): **S1** Figure 2 merge-induced 3-page
displacement; **S2** Table 7's 7-page first-mention gap (benign caption cross-reference);
**S3** `m_c` defined twice at EN L80 and L154; **S4** §5.11 "five
experiments" enumerating four items; **S5** two distinct contraction generators both called
"class contraction" (`C` and `P` families); **Z1** ZH Table 6 caption drops the ≤0.005
endpoint-provenance clause that protects P1; **Z2** ZH carries no footnote for the offset
comparability caveat.

**Highest-priority items for the human**, in order: **P8** (a retracted internal defect that
reappeared in the merged text), **P6** (two headline hardening statistics with no archival
provenance), **P1** (a table row whose caption's own guarantee is violated), **P5** (a printed
sequence that contradicts the sentence after it), **P7** (a census arithmetic error propagated
into the abstract), **Z1** (the ZH mirror silently drops the caveat protecting P1).
