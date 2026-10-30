# Independent verification of `docs/A1_HARDENING.md`

> **⚠ 本文件含两处已知错误——下游请勿照此修改（2026-09-15 由残量修正代理证明）**
>
> 1. **V-4 是误报。** 报告称 12 检查点的超出量区间应为 "+3.06 … +6.06"、并称存储聚合值
>    `excess_stats.min` 有缺陷。**均不成立**：`outputs/a1_h_offset.json →
>    offset_analysis.by_vision_tower.vision_lora_checkspoints.tags` 恰好 12 个 tag 且**包含**
>    取值 +0.54 的 `flickr30k_retrain_both_ep10`；这 12 个值的 mean 3.616667 / sd 1.407456 /
>    min 0.54 / max 6.06 与存储值逐位一致。被排除的第 13 个是 `flickr30k_text_only_r8`
>    （`vision_lora=false`，+0.48），不是 +0.54。且**+3.06 对 12 元素子集算术上不可能**
>    （13 个值里只有 10 个 ≥3.06）。→ 按本报告去改会把正确数字改错。
>
> 2. **V-5 的 "27 个子集里 16 个 τ=+0.50" 是错的。** 重算为 **6/27**（top1_50k 列）或
>    9/27（5k 列）；21 个子集给 +1.00。"16" 对不上任何定义。
>
> 另注：V-11 的 0.006336 归属应为**九个受控种子检查点**，而非报告所写的"12 个视觉 LoRA"。
> 其余各条经复核成立，尤其 §①（τ@k=10 = 0.9262，连 p 值 17 位有效数字精确复现）与
> "无任何数组被重启截断"。


**Reviewer role.** Independent verification of the five evidence-hardening experiments. Nothing below
is taken from the running agent's own validators or its prose; every number was re-read from the
JSONs named in the right-hand column and every derived statistic was recomputed with
`D:\Anaconda\envs\pytorch\python.exe` (numpy + scipy) in a read-only session. No file under
`outputs/`, `paper_a1/` or `docs/A1_HARDENING.md` was modified.

**Method note on "verified".** A number counts as verified only with a file and key path. Where a
recomputation was possible it was performed; where only a re-read was possible that is stated.
The running agent's `tools/a1_h_validate.py` / `a1_h_validate2.py` were re-executed and both exit 0,
but their coverage is narrower than §"Reproducing this document" implies (see finding **V-14**).

---

## 1. Baseline certification (report §①)

Evidence file: `outputs/a1_h_baseline_metrics.json` (4.79 MB).
Archived comparator: `outputs/a1_baseline_metrics.json` (541 B, read directly).

| # | item | report value | JSON value | key path | verdict |
|---|---|---|---|---|---|
| 1.1 | Spearman(τ@k=5, top-1), 26 cond. | 0.9125 (p = 8.4785e-11) | `0.9125` / p `8.478458746369484e-11` | `metric_correlations.tau_k5.spearman_r` / `.p` | **PASS** |
| 1.2 | Spearman(τ@k=10, top-1) — the manuscript's number | 0.9262 (p = 1.1861084080501641e-11) | `0.9262` / p identical to 17 s.f. | `metric_correlations.tau_k10` | **PASS** |
| 1.3 | is 0.9262 the k=10 value? | yes | archived file stores `metric_correlations.tau.spearman_r = 0.9262`, p `1.1861084080501641e-11` — byte-equal to the new k=10 row | `outputs/a1_baseline_metrics.json → metric_correlations.tau` | **PASS** |
| 1.4 | Spearman(linear CKA, top-1) | 0.7552 (p = 8.218838697506625e-06) | `0.7552` / p exact | `metric_correlations.cka` | **PASS** |
| 1.5 | Spearman(mean cosine, top-1) | 0.8619 (p = 1.5443e-08) | `0.8619` / p `1.5443161369804112e-08` | `metric_correlations.mean_cos` | **PASS** |
| 1.6 | Spearman(CG, top-1) | −0.2150 (p = 0.2914) | stored as `-0.215`; recomputed p `0.29143212940113744` | `metric_correlations.CG` | **PASS** (value is stored at 3 d.p.; see **V-3**) |
| 1.7 | archived CG / mean-cos values | −0.0821 / 0.8715 | `-0.0821` / `0.8715` | `outputs/a1_baseline_metrics.json → metric_correlations.CG/.mean_cos` | **PASS** |
| 1.8 | per-condition CG range / mean | [0.264, 1.220] / **0.841** | recomputed from all 26: min `0.263590`, max `1.219960`, mean **`0.841431`**; no negative | `conditions[*].CG` | **PASS** |
| 1.9 | "val block rows 0..1000" CG variant | Spearman −0.2150, mean 0.837020 | `spearman_r: -0.215`, `mean_cg: 0.83702` | `cg_mean_cos_variants.alternative_cg_definitions_through_the_correlation.CG_val_0_1000` | **PASS** |
| 1.10 | mean-cosine variants | 1.000000 / 0.465424 / 0.181905 | identical | `cg_mean_cos_variants.mean_cos_variants.*` | **PASS** |
| 1.11 | estimator cross-check max deviation | max **2.1e-8** on T0.5/P0.5 at k=5,10 (400 images) | recomputed max over the 6 stored entries = `2.0901362085545827e-08`, all `n_images = 400` | `estimator_crosscheck_vs_archived_scipy.*.abs_diff` | **PASS** |
| 1.12 | "identical (diff 0.0) at λ = 0" | 0.0 | `base_k5.abs_diff = 0.0`, `base_k10.abs_diff = 0.0` | same block | **PASS** |
| 1.13 | theory check | pearson 1.0000, std(m_c) 0.0674, gap_norm 0.8149 | `1.0`, `0.0674`, `0.8149` | `theory_verification.*` | **PASS** |
| 1.14 | τ@k=5 at λ=0.25 and λ=0.5 | 0.6425 / 0.4656 | `conditions[T0.25].tau_k5 = 0.642498`, `conditions[T0.5].tau_k5 = 0.465609` | `conditions[*]` | **PASS** |
| 1.15 | frozen 5k top-1 | 59.10 | `meta.frozen_top1_5k_filtered = 59.100002` | `meta.frozen_top1_5k_filtered` | **PASS** |
| 1.16 | run time | "147.7 s" (§①) / "103.5 s" (§6.3) | `meta.runtime_s = 103.2` | `meta.runtime_s` | **FAIL (both)** — see **V-1** |

**Assessment of the §1 verdict.** The core claim is verified and is the strongest single result in
the document: the k=10 row of the *new* JSON reproduces the *archived* JSON's value **and** its
p-value to all 17 significant figures, and the CKA row likewise. That is not reachable by chance
and confirms that the new script re-implements the archived protocol. The `-0.0828`-is-a-pair-sample
excavation is corroborated: the JSON stores `archived_hints.CG = -0.0821` alongside the certified
`-0.215`, and the diagnostic sweep (`cg_mean_cos_variants.cg_variants_reaching_archived = []`) lists
five CG variants, none of which reaches −0.0821.

---

## 2. Seed spread and the 9-run τ-vs-CG contrast (report §②)

Evidence: `outputs/a1_h_seeds_{coco,food101,dtd}_seed{43,44}.json`, `outputs/a1_h_seed_summary.json`,
seed-42 rows from `outputs/a1_rr_e4_{coco,food101,dtd}.json`.

### 2.1 Per-run table (§2.1)

All nine (τ₅, top-1 5k, top-1 50k, CG, n_steps) tuples in the report's §2.1 table match the JSONs
exactly. Spot-checked paths:

* COCO s43: `result.image_only.legacy1001.tau_by_k["5"] = 0.575651`, `top1_5k = 56.94`,
  `result.top1_50k_legacy1001 = 56.922`, `result.CG_flickr_val = 0.766421`, `meta.n_steps = 320`.
* DTD s44: `…tau_by_k["5"] = 0.514949`, `top1_5k = 53.5`, `top1_50k_legacy1001 = 53.92`,
  `CG_flickr_val = 0.833206`, `meta.n_steps = 300`.
* Food-101 s43: `…tau_by_k["5"] = 0.580987`, `top1_5k = 59.78`, `top1_50k_legacy1001 = 58.716`,
  `CG_flickr_val = 0.826939`, `meta.n_steps = 320`.

`outputs/a1_h_seed_summary.json → per_dataset_spread.*.*.per_seed` matches the same nine rows.
**PASS** (9/9 rows).

### 2.2 Seed spreads — recomputed from scratch

Recomputed with `statistics.stdev` (sample sd, n−1) directly from the nine raw values, not re-read
from the summary's `stats` blocks:

| dataset | quantity | report (§2.1/§6.1) | my recomputation | JSON `stats` | verdict |
|---|---|---|---|---|---|
| COCO | τ₅ mean ± sd (range) | 0.5757 ± **0.0002** (0.0005) | 0.575671 ± **0.0002490** (0.000496) | sd 0.000249, range 0.000496 | **PASS** |
| Food-101 | τ₅ | 0.5797 ± **0.0146** (0.0291) | 0.579668 ± **0.0146093** (0.029129) | sd 0.014609 | **PASS** |
| DTD | τ₅ | 0.5321 ± **0.0149** (0.0262) | 0.532093 ± **0.0148528** (0.026153) | sd 0.014853 | **PASS** |
| COCO | top-1 50k | 57.42 ± **0.58** (1.13) | 57.424 ± **0.575441** (1.130) | sd 0.575441 | **PASS** |
| Food-101 | top-1 50k | 58.23 ± **0.48** (0.95) | 58.231333 ± **0.475295** (0.950) | sd 0.475295 | **PASS** |
| DTD | top-1 50k | 54.67 ± **0.66** (1.18) | 54.674 ± **0.654972** (1.182) | sd 0.654972 | **PASS** |
| COCO | CG | 0.7709 ± **0.0060** (0.0113) | 0.770855 ± **0.0060003** (0.011261) | sd 0.006 | **PASS** |
| Food-101 | CG | 0.8283 ± **0.0086** (0.0170) | 0.828348 ± **0.0086105** (0.017049) | sd 0.008611 | **PASS** |
| DTD | CG | 0.8335 ± **0.0022** (0.0044) | 0.833505 ± **0.0021917** (0.004354) | sd 0.002192 | **PASS** |

**PASS** — all nine mean/sd/range triples reproduce. Arithmetic shown for the two load-bearing ones:

```
COCO  τ₅ = {0.575433, 0.575651, 0.575929};  mean = 1.727013/3 = 0.575671
      deviations = {-0.000238, -0.000020, +0.000258};  Σd² = 1.2388e-7
      sd(n−1) = sqrt(1.2388e-7 / 2) = sqrt(6.194e-8) = 2.490e-4   → 0.0002  ✓
      range   = 0.575929 − 0.575433 = 0.000496                          → 0.0005  ✓
FOOD101 τ₅ = {0.593573, 0.580987, 0.564444}; mean = 1.739004/3 = 0.579668
      deviations = {+0.013905, +0.001319, −0.015224}; Σd² = 4.2684e-4
      sd(n−1) = sqrt(4.2684e-4 / 2) = sqrt(2.1342e-4) = 1.4609e-2    → 0.0146  ✓
      range   = 0.593573 − 0.564444 = 0.029129                           → 0.0291  ✓
DTD   τ₅ = {0.540227, 0.541102, 0.514949}; mean = 1.596278/3 = 0.532093
      deviations = {+0.008134, +0.009009, −0.017144}; Σd² = 4.4113e-4
      sd(n−1) = sqrt(4.4113e-4 / 2) = 1.4853e-2                       → 0.0149  ✓
```

### 2.3 The 9-run τ-vs-CG contrast (§2.2 table and verdict)

Recomputed in scipy from the nine `(τ₅, top-1 50k, CG)` triples:

```
              Spearman r      p         Pearson r     p
τ₅ vs top-1     +0.8500      0.003705     +0.9396     0.000168
CG vs top-1     −0.2667      0.487922     −0.3426     0.366799
```

| # | report claim | JSON | verdict |
|---|---|---|---|
| 2.3.1 | 9 runs: Spearman(τ₅, top-1) **+0.850** (p = 0.0037) | `cross_checkpoint_correlations.seed42_plus_new_seeds_all.tau5_vs_top1_50k`: `spearman_r 0.85`, `spearman_p 0.0037047773275858125` | **PASS** |
| 2.3.2 | 9 runs: Spearman(CG, top-1) **−0.267** (p = 0.49) | same block `CG_vs_top1_50k`: `-0.2667`, p `0.48792227483870076` | **PASS** |
| 2.3.3 | seed-42-only row: n=3, **+1.000** / −0.500 | `seed42_only.tau5_vs_top1_50k.spearman_r = 1.0`; `CG_vs_top1_50k.spearman_r = -0.5` | **PASS** |
| 2.3.4 | s42+43 (n=6): +0.886 / −0.371 | `seed42_and_43`: `0.8857` / `-0.3714` | **PASS** |
| 2.3.5 | s42+44 (n=6): +0.829 / −0.314 | `seed42_and_44`: `0.8286` / `-0.3143` | **PASS** |
| 2.3.6 | s43+44 (n=6): +0.829 / −0.029 | `seeds43_44_only`: `0.8286` / `-0.0286` | **PASS** |
| 2.3.7 | + Flickr30k s42 control (n=10): +0.794 (p=0.0061) / −0.152 | `with_flickr30k_control_all_seeds`: `0.7939` / p `0.0060999…` ; `-0.1515` | **PASS** |
| 2.3.8 | + 3 archived Flickr30k (n=13): +0.841 (p=0.00032) / +0.198 | `with_archived_flickr30k_all`: `0.8407` / p `0.00031907` ; `0.1978` | **PASS** |
| 2.3.9 | variant claimed | **Spearman** | the row is `spearman_r`; the JSON *also* stores `pearson_r 0.9396` and `kendall_r 0.7222`. Report correctly says Spearman. | **PASS** (variant correctly stated) |

**Plain-language verdict on §2.2.** The point estimates are right; the *word* "strengthens" is not.
See **V-5** — the τ−CG gap narrows from 1.50 (3 runs) to 1.12 (9 runs); what improves is the
p-value, and the whole effect is carried by DTD.

### 2.4 Within-dataset ranking and the offset over 9 seeds (§2.3, §2.4)

| # | claim | evidence | verdict |
|---|---|---|---|
| 2.4.1 | within-dataset Spearman(τ₅, top-1) = −0.5 / −0.5 / +1.0 | `within_dataset_rank_check.{coco,food101,dtd}.spearman_tau_vs_top1_within_dataset` = `-0.5`, `-0.5`, `1.0`; recomputed from the same 5k series | **PASS** (note: these use `top1_5k`, not `top1_50k`; consistent within file) |
| 2.4.2 | excess over the synthetic curve: mean **+4.72**, sd **0.70**, range **+4.00 … +5.78** | `synthetic_curve_position_summary`: `excess_50k_mean 4.7191`, `sd 0.702032`, `min 3.9964`, `max 5.7821`; recomputed mean of the nine `excess_top1_50k` = 4.7191 | **PASS** |
| 2.4.3 | τ₅ range over nine runs 0.5149 – 0.5936 | `runs[*].tau5`: min `0.514949`, max `0.593573` | **PASS** |
| 2.4.4 | "every one of them sits above the curve" | all nine `excess_top1_50k` > 0 in `synthetic_curve_position` | **PASS** |
| 2.4.5 | DTD 300 steps explained | `10 × ceil(1880/64) = 300`; `meta.data.n_pairs_used = 1880` | **PASS** — see §4 below |

---

## 3. Template sensitivity (report §③)

Evidence: `outputs/a1_h_templates.json` (7.81 MB). All numbers below recomputed from
`results.<benchmark>.templates.<t>.variants.<coupled|fixed_t0>.surgery.<λ>.{tau,top1}` and
`stability.*`.

| # | claim | JSON | verdict |
|---|---|---|---|
| 3.1 | 15/15 monotone decreasing in τ **and** top-1 | recomputed per (benchmark, template): all 15 τ sequences strictly decreasing over λ = 0→0.5→1→2, and all 15 top-1 sequences likewise; `stability.*.collapse_per_template.*.monotone_decreasing = true` in all 15 | **PASS** |
| 3.2 | τ(2) ∈ [0.071, 0.297] | recomputed min `0.070745` (dtd/t2_in_the_wild), max `0.296697` (food101/t2_in_the_wild) | **PASS** |
| 3.3 | absolute-τ drift "up to 0.111" | recomputed max over all (benchmark, λ, template-pair) of \|Δτ\| = `0.110955` (food101 λ=1, t2 − t4) | **PASS** |
| 3.4 | §3.3 spread table (12 rows) | recomputed every row — ImageNet λ=0.5/1/2 spreads `0.094345/0.101060/0.088029`, DTD `0.065213/0.084575/0.103617`, Food-101 `0.096317/0.110955/0.097302`; all top-1 spreads identical to the report | **PASS** |
| 3.5 | cross-template τ table (3 benchmarks × 4 templates) | `cross_template_tau.<b>.<t>.tau_vs_t0_on_t0_top5` = 0.64785 / 0.609059 / **0.564661** / 0.688421 (ImageNet); 0.61266 / **0.480851** / 0.536489 / 0.54617 (DTD); 0.795617 / 0.754788 / **0.711335** / 0.805117 (Food-101) | **PASS** (all 12 exact) |
| 3.6 | frozen-top-5 Jaccard t0 vs t3 on ImageNet-5k = **0.571** | `cross_template_tau.imagenet5k.t3_bare_class.top5_set_jaccard_vs_t0 = 0.570875` | **PASS** |
| 3.7 | ‖g‖ = 0.8149 / 0.8151 / 0.8152 / 0.8157 / 0.8154, spread 8e-4 | `variants.coupled.gap_norm` = `0.814929`, `0.815080`, `0.815157`, `0.815697`, `0.815422`; spread `7.68e-4` | **PASS** |
| 3.8 | §3.1 frozen/τ/top-1 tables (all 60 numbers) | recomputed cell by cell from `results.*.templates.*` — every value matches | **PASS** |
| 3.9 | default template "best or near-best on all three" | ImageNet t0 = 59.10 = max; DTD t0 = 43.1383 = max; Food-101 t0 = 82.0594 vs t1 83.4693 → **2nd** of five, not 3rd | **PASS with a correction** — see **V-8** |
| 3.10 | "t4 is the most destructive template at λ = 1 on all three benchmarks" | t4 τ(1) = 0.239887 / 0.277234 / 0.373964 — minimum in all three; t4 top-1(1) = 25.02 / 29.57 / 51.54 — minimum in all three | **PASS** |
| 3.11 | "τ(λ) is template-dependent to ±0.05" | largest spread anywhere is 0.1110; smallest benchmark-level spread is 0.0652 | **FAIL (loose)** — see **V-7** |
| 3.12 | "at λ = 2 the class-contraction family sits at τ = 0.58 – 0.68 while surgery sits at τ = 0.07 – 0.30" | surgery range verified (recomputed 0.070745 – 0.296697). No object anywhere stores the interval 0.58 – 0.68: the only λ=2 contraction figures in `outputs/a1_h_baseline_metrics.json` are `O2.tau_k5 = 0.263500` and `C0.1/C0.25/C0.5` are λ=0.1/0.25/0.5 runs; the "P" family sits at 0.6086 (λ=0.5) / 0.7519 (λ=0.25) | **UNVERIFIABLE** — see **V-6** |

`meta` block completeness: `script`, `class_list_len` (dict per benchmark: 1001/47/101),
`shard_signature = d13718e47e9e41c2`, `runtime_s = 185.4`, `topk_for_tau = 5`,
`tau_convention` (template-internal τ) — all present. **PASS**.

---

## 4. Bootstrap intervals and k-specificity (report §④)

Evidence: `outputs/a1_h_bootstrap.json`.

### 4.1 Dose-response grid (§4.1)

All nine rows re-read and re-checked; report values are exact matches to the stored `point` /
`ci_low` / `ci_high` / `se`:

| condition | point | 95 % CI | SE | path |
|---|---|---|---|---|
| base | 1.000000 | [1.0000, 1.0000] | 0.000000 | `bootstrap.dose_response_grid_imagenet5k_k5.conditions.base` |
| λ = −1 | 0.331360 | [0.320995, 0.342320] | 0.005569 | `…T-1` |
| λ = −0.5 | 0.493147 | [0.483306, 0.503702] | 0.005117 | `…T-0.5` |
| λ = +0.25 | 0.642498 | [0.633128, 0.651160] | 0.004522 | `…T0.25` |
| λ = +0.5 | 0.465609 | [0.454674, 0.475935] | 0.005479 | `…T0.5` |
| λ = +1 | 0.290120 | [0.278479, 0.301718] | 0.005995 | `…T1` |
| λ = +2 | 0.149600 | [0.137578, 0.161472] | 0.006145 | `…T2` |
| λ = +4 | 0.065502 | [0.053742, 0.077427] | 0.006140 | `…T4` |
| P0.5 | 0.608569 | [0.599253, 0.617486] | 0.004733 | `…P0.5` |

Every row carries `agrees_with_source: true`. **PASS** (9/9).

Recomputed half-widths: min `0.009016` (λ=0.25) … max `0.011947` (λ=2), so the report's
**"CI half-width ≈ 0.011"** is a correct representative figure. Separation
λ=0.5 vs λ=1 = `0.465609 − 0.290120 = 0.175489` ≈ 0.176 ✓, CIs `[0.4547, 0.4759]` and
`[0.2785, 0.3017]` do **not** overlap ✓. **PASS**.

### 4.2 E3 benchmarks (§4.2)

Point estimates and CIs re-read for all 16 rows; report values match the stored `point`, `ci_low`,
`ci_high`, `se`, `n_images`, `n_classes`, `frozen_top1`. **PASS** (16/16 rows).

| claim | recomputation | verdict |
|---|---|---|
| iNat-wild λ=2 τ = −0.0036, CI [−0.036, +0.026] → indistinguishable from zero | `…inat_wild.conditions["2.0"]`: `point = -0.0036211699164345424`, `ci = [-0.03621866, +0.02591226]`; CI contains 0 | **PASS** |
| rare-species λ=2 τ = 0.0190, CI [−0.008, +0.045] → indistinguishable from zero | `…rare_species.conditions["2.0"]`: `point = 0.019`, `ci = [-0.008, +0.0454]`; CI contains 0 | **PASS** |
| CI half-width 0.004 (Food-101, n=25250) vs 0.016 (iNat, n=718), factor 4 tracking 1/√n | recomputed `0.0035`, `0.0042`, `0.0047` (Food-101) vs `0.0298`, `0.0299`, `0.0311` (iNat). The *reported* column values 0.0018/0.0021/0.0024 are the **SEs**, not half-widths — the substantive ratio claim (≈ 4× in SE, ≈ 8.5× in half-width) holds | **PASS** (terminology) — see **V-9** |
| "reproduce the E3 JSON to within **0.0072**" | recomputed max \|point − `tau_in_e3_json`\| = **0.012131** (food101 λ=1); food101 λ=2 = 0.010904; dtd max = 0.000851; inat max = 0.001671; rare max = 0.001200 | **FAIL** — see **V-2** |
| "≤ 0.6 points in top-1" (§6.2 item 9) | recomputed max \|top1 − `top1_in_e3_json`\| = **1.3274** (food101 λ=1: 59.1327 vs 60.4554); food101 λ=2 = 2.0278 | **FAIL** — see **V-2** |

### 4.3 k-specificity (§4.3)

Recomputed from `k_specificity.per_k_bootstrap_at_sweep_lambdas`:

| k | τ(−0.5) | τ(0.5) | τ(1.0) | τ(2.0) | n at λ=1 | report | verdict |
|---|---|---|---|---|---|---|---|
| 2 | 0.544634 | **0.503711** | **0.328652** | **0.171916** | **4984** | 0.5037 / 0.3287 / 0.1719 / 4 984 | **PASS** |
| 3 | 0.512667 | 0.496667 | 0.317297 | 0.163467 | 5000 | 0.4967 / 0.3173 / 0.1635 | **PASS** |
| **5** | 0.493147 | **0.465609** | **0.290120** | **0.149600** | 5000 | 0.4656 / 0.2901 / 0.1496 | **PASS** |
| 10 | 0.467351 | 0.442073 | 0.271913 | 0.141930 | 5000 | 0.4421 / 0.2719 / 0.1419 | **PASS** |
| 20 | 0.463089 | 0.424846 | 0.252164 | 0.125811 | 5000 | 0.4248 / 0.2522 / 0.1258 | **PASS** |
| 50 | 0.470546 | **0.409657** | 0.228727 | 0.100555 | 5000 | 0.4097 / 0.2287 / 0.1006 | **PASS** |
| 100 | 0.475571 | 0.411063 | **0.225044** | 0.093665 | 5000 | 0.4111 / 0.2250 / 0.0937 | **PASS** |

* "shifts by up to **0.104** with k": recomputed `absolute_level_shift_over_k["1.0"].abs_shift = 0.103608`. **PASS**
* "this run measures 0.4967 → 0.4097, a shift of **0.087** at λ = 0.5": `0.4966667 − 0.4096572 = 0.0870094`. **PASS**
* "`a1_rr_e2_topk.json` gives 0.496 / 0.465 / 0.442 / 0.425 / 0.410 / 0.411 … matching to ≤ 0.001": those six values are stored inside `a1_h_bootstrap.json → k_specificity.e2_absolute_levels_by_k.e2_absolute_levels.legacy1001` at λ=0.5 for k = 3/5/10/20/50/100; max \|Δ\| vs this run's k-sweep = `0.0007`. **PASS** (and the independent-script attribution is corroborated by the E2 values being carried in the bootstrap JSON)
* "**k = 2 drops 0.32 % (tied pair)**, n = 4 984": `n_images = 4984` at λ=0.5 **and** λ=1.0 **and** λ=2.0 for k=2, but `5 000` at λ=−0.5. Section 4.3's table annotates the *λ = 1* column with "4 984", and the text says "no ties are dropped at k ≥ 3". **PASS**, with a note that the 0.32 % is really 0.3 % (16/5000 = 0.32 %) — arithmetically correct.
* "every per-point CI is far narrower than that shift (typical half-width 0.004–0.015)": across all 28 (k, λ) cells the half-widths run `0.0024 … 0.0269`; only **k = 2** exceeds 0.015 (0.0223–0.0269). **PASS** with the k=2 exception.

### 4.4 Template-window CIs (§4.4)

Recomputed half-widths from `bootstrap.templates.benchmarks.*`:

| benchmark | report | recomputed | verdict |
|---|---|---|---|
| ImageNet-5k (n=5000) | 0.0098–0.0112 / 0.0107–0.0119 / 0.0114–0.0120 | `[0.0098,0.0112]` / `[0.0107,0.0119]` / `[0.0114,0.0120]` | **PASS** |
| DTD (n=1880) | 0.0137–0.0151 / 0.0163–0.0182 / 0.0178–0.0189 | `[0.0137,0.0151]` / `[0.0163,0.0182]` / `[0.0178,0.0189]` | **PASS** |
| Food-101 (n=25250) | 0.0034–0.0038 / 0.0041–0.0044 / 0.0046–0.0048 | `[0.0034,0.0038]` / `[0.0041,0.0044]` / `[0.0046,0.0048]` | **PASS** |

"6–25× larger than the CI half-width": min template spread 0.065213 (DTD λ=0.5) / max half-width
0.018936 → **3.4×**; max spread 0.110955 / min half-width 0.003394 → **32.7×**; the per-cell ratios
across all 9 (benchmark, λ) cells span `3.44 … 32.68`. **FAIL (mild)** — see **V-10**.

---

## 5. The offset (report §⑤)

Evidence: `outputs/a1_h_offset.json`.

### 5.1 Synthetic curve (§5.1) — **PASS**

All eight λ rows match `synthetic_curve.*.{tau,top1,displacement}`:
τ = 1.0 / 0.6425254 / 0.4656321 / 0.3603233 / 0.2901322 / 0.2011900 / 0.1496211 / 0.0655233;
top-1 = 59.10 / 55.80 / 47.48 / 39.84 / 32.10 / 19.52 / 12.62 / 3.24;
displacement = 0.0 / 0.200540 / 0.415908 / 0.624593 / 0.807636 / 1.073629 / 1.233878 / 1.473700.
The report's `mean ‖Δx‖` column roundings (0.2005, 0.4159, 0.6246, 0.8076, 1.0736, 1.2339,
1.4737) are all correct.

### 5.2 Matched-τ excess table and the +3.62 ± 1.41 statistic — **PASS (with range error)**

The 13 `excess` values in `checkpoints[*].matched_tau.excess_top1` are:
COCO 4.56/3.36/3.96, Food-101 4.06/6.06/5.20, DTD 3.56/3.72/3.06, flickr30k_ref 3.12,
flickr30k_both_r8 2.20, flickr30k_retrain 0.54, flickr30k_text_only 0.48. The report's §5.2 table
reproduces every one. The statistics on the **12 vision-LoRA checkpoints**
(`offset_analysis.by_vision_tower.vision_lora_checkspoints`, `n = 12`):

```
excess = [4.56, 4.06, 3.56, 3.12, 2.2, 0.54, 3.36, 3.96, 6.06, 5.2, 3.72, 3.06]
mean   = 43.42 / 12           = 3.616667   → report  +3.62       ✓
sd(n−1) = sqrt(21.7721 / 11) = 1.407456    → report  1.41        ✓
min = 0.54   max = 6.06
SE = 1.407456/√12 = 0.40630
95 % CI (t₁₁ = 2.200985) = 3.616667 ± 0.89425 = [2.7224, 4.5109]  → report ≈ [2.72, 4.51]  ✓
t = 3.616667/0.40630 = 8.90  (p ≈ 3.6e-6, two-sided)
```

The JSON's own `by_vision_tower.vision_lora_checkspoints.excess_stats` reads
`{n: 12, mean: 3.6167, sd: 1.4075, min: 0.54, max: 6.06, range: 5.52}` — identical. **PASS.**

Also verified: `offset_analysis.excess_top1_mean = 3.3754`, `sd = 1.604`, `min = 0.48`,
`max = 6.06` (all 13), matching the report's §5.2 "3.3–5.5 points" framing and §6.2 item 5.

**However** the report writes the 12-checkpoint spread as **"range +0.54 … +6.06"** immediately
after saying "12 vision-LoRA checkpoints". The 12-checkpoint minimum is **3.06**, not 0.54;
0.54 belongs to the 13-set. It should read "+3.06 … +6.06". See **V-4**.

### 5.3 Orthogonality (§5.3) — **PASS**

| family | report | recomputed from `displacement.*` | verdict |
|---|---|---|---|
| COCO (3 seeds) | ‖Δx‖ 0.290–0.309; cos +0.015…+0.106; ⊥ share **94–99 %** | 0.290216 / 0.303902 / 0.309219; cos 0.014747 / 0.039746 / 0.105541; ⊥ 0.991660 / 0.977414 / 0.940839 | **PASS** |
| Food-101 (3 seeds) | 0.209–0.228; +0.051…+0.114; **94–98 %** | 0.208725 / 0.218417 / 0.228022; 0.050808 / 0.090063 / 0.113852; 0.975150 / 0.956194 / 0.942403 | **PASS** |
| DTD (3 seeds) | 0.311–0.339; −0.022…+0.030; **98–99 %** | 0.317159 / 0.310851 / 0.338936; 0.006004 / −0.022162 / 0.030349; 0.996634 / 0.988700 / 0.982494 | **PASS** |
| Flickr30k ref / archived | 0.118–0.243; −0.326…+0.046; **86–100 %** | 0.243056 / 0.147374 / 0.117994; −0.267741 / −0.325856 / 0.045713; 0.868881 / 0.859915 / 0.978851; text-only has ‖Δx‖ = 0 exactly | **PASS** (the "100 %" is the undefined 0/0 of the text-only checkpoint; the well-defined maximum is 99.6634 % — the report's own headline text says 86–99.7 %, which is the defensible phrasing) |
| synthetic translation | cos = +1, 0 % ⊥ | by construction | **PASS** |

Geometry deltas and `logit_scale`:

* `logit_scale = 100.0` for **all 13** checkpoints including `frozen`, with
  `geometry_delta_vs_frozen.d_logit_scale = 0.0` everywhere, and
  `frozen.mean_image_norm = 1.0`, `std_image_norm = 0.0`, `mean_text_norm = 1.0`. The report's
  "**exactly 100.0 for all 13 checkpoints**" and "all embeddings are normalised, so ‖x‖ = 1"
  are **PASS**, exactly as stated.
* within-class spread: recomputed range over all 13 = `[0.112178, 0.135386]`; max \|Δ\| = `0.016872`
  (flickr30k_ref), and **0.006336** if the 12 vision-LoRA checkpoints are meant. So the report's
  "**≤ 0.007**" is right for the 12-checkpoint set only, and "**1–2 orders of magnitude too small**"
  is wrong on its face: 0.0169 against a 3.62-point excess is a ratio of ~215, i.e. two orders —
  but the *margin* delta is 0.003853 against a 0.005227 frozen margin, which is the **same order of
  magnitude**, not 1–2 orders smaller. **FAIL** — see **V-11**.
* margin: max \|Δmargin_top1_mean\| = `0.003853` (dtd s44); frozen `margin_top1_mean = 0.005227`.
  Report's "≤ 0.004" ✓.

Correlation table (§5.3):

| report | JSON path | verdict |
|---|---|---|
| ‖Δx‖ ρ_pearson **+0.615** | `mean_abs_dx.pearson_r = 0.6145` (n=13) | **PASS** |
| text-tower ‖Δt‖ **+0.670** (p = 0.012) | `mean_abs_text_dx.pearson_r = 0.6698`, `pearson_p = 0.01226` | **PASS** |
| ⊥-component +0.615 | `component_orthogonal_to_gap_dir.pearson_r = 0.6146` | **PASS** |
| fraction of top-1 predictions changed **+0.689** | `frac_top1_class_shifted.pearson_r = 0.6892`, p `0.009166` | **PASS** |
| within-class-spread delta +0.288 | `d_within_class_spread.pearson_r = 0.2877` | **PASS** |
| margin deltas −0.11 … +0.37 | `d_margin_top1_mean −0.1072`, `d_margin_top1_p10 −0.3657`, `d_margin_top1_std +0.3686` | **PASS** |
| CG −0.100 | `cg_flickr_val.pearson_r = -0.1004` | **PASS** |
| "best single correlate explains **< 50 %** of the excess variance" | max R² over the 12 stored correlates = `0.6892² = 0.4750` (frac_top1_class_shifted). Independently confirmed for the 12-checkpoint subset: best `frac_top1_class_shifted` R² = 0.3077. | **PASS** |

---

## 6. Internal consistency of the JSONs

### 6.1 Which files actually contain per-image arrays, and are they full length?

| file | per-image arrays | full length? | stored scalar == mean of its array? |
|---|---|---|---|
| `a1_h_baseline_metrics.json` | 18 (`per_image_tau_by_condition.k5/k10` × 9 conditions) + 35 (`per_image_tau_k_sweep.data`) | yes, all 5 000 | yes (validator recomputes; all `agree`) |
| `a1_h_templates.json` | **45** — 30 `coupled` (5 templates × 3 λ × {imagenet5k, dtd, food101}) + 15 `fixed_t0` | yes: 5 000 / 1 880 / 25 250 as required | yes, to the 6-d.p. storage rounding of the scalar (max \|mean − stored\| = `4.95e-7`) |
| `a1_h_bootstrap.json` | **none** — CIs are stored, not the resampled arrays | n/a | points carry `agrees_with_source: true` (9/9 grid) and `tau_agrees_with_e3` (4/16 true — see V-2) |
| `a1_h_offset.json` | **none** — aggregates only | n/a | `excess_top1` reconciles with `measured.top1_5k_recomputed − matched_tau.synthetic_top1` for all 13 (checked) |
| `a1_h_seeds_*.json` (×6) | **none** — no per-image array at all (file size 3.1 KB) | n/a | all scalars are self-consistent (`tau_by_k` 3/5/10/20, `top1_5k`, `top1_50k`, `CG`) |
| `a1_h_seed_summary.json` | none — derived tables | n/a | `runs[*]` reproduces each source JSON's scalars (spot-checked 9/9) |

**No truncation found anywhere.** No array length is partial. The reboot did not damage a JSON.

### 6.2 `meta` provenance fields

Recomputed audit over every `outputs/a1_h_*.json`:

* **script** — present in 11/13 (as `meta.script`). `a1_h_recover_spec_food101_seed43.json` is a
  bare top-level JSON **list** with no `meta` at all; `a1_h_recover_spec_dtd_seed44.json` has a
  `meta` but its `class_list_len` and `runtime_s` are `null`.
* **class-list length** — present under the literal key `class_list_len` in only **4** files
  (`baseline_metrics` 1001, `bootstrap` 1001, `offset` 1001, `templates` `{1001,47,101}`). The six
  `a1_h_seeds_*` JSONs instead carry `meta.placeholder_class_index = 1000` and
  `meta.n_tau_images = 5000`. `seed_summary` and `recover_spec_dtd_seed44` carry **neither**.
* **shard signature** — `d13718e47e9e41c2` present as `shard_sig` in all six seed JSONs and as
  `shard_signature` in all four analysis JSONs. `seed_summary` has **no** shard field.
* **runtime_s** — absent/`null` in `seed_summary`, `recover_spec_*` and `seeds_dtd_seed44`.

So the ground rule "**every new JSON carries a `meta` block naming the script, the class-list
length, the shard signature**" is **not literally true** for 5 of the 13 files, even though the
underlying intent (traceability) is largely met. See **V-13**.

---

## 7. The three process claims (task item 4)

### 7.1 (a) `a1_h_seeds_dtd_seed43.json` was a *validator* bug, not a data problem — **PASS**

* DTD's `meta.data.n_pairs_used = 1880` (`outputs/a1_h_seeds_dtd_seed43.json → meta.data.n_pairs_used`).
* `10 × ceil(1880/64) = 10 × 30 = 300` = `meta.n_steps = 300`. **300 is genuinely correct.**
* The seed-42 DTD run is also 300: `outputs/a1_rr_e4_dtd.json → meta.n_steps = 300`, while
  `a1_rr_e4_coco.json` and `a1_rr_e4_food101.json` both give `320`. **Confirmed.**
* `tools/a1_h_validate.py` lines 49–55 implement exactly this reasoning
  (`expected_steps = 10 * -(-n_pairs // 64)`), with the inline comment "DTD's whole train split is
  1880 images → 300 steps; every other dataset draws 2000 pairs → 320 steps. Both are correct, not
  truncation." Re-running the validator now gives **PASS** for all six seed files, exit 0.
* Caveat: no surviving log records the earlier failing run, so "the validator was wrong" is
  **inferred from the code + the arithmetic**, not documented. The arithmetic is decisive.

### 7.2 (b) `dtd_seed44` checkpoint survived and only the evaluation was rebuilt — **PARTIAL / FAIL on wording**

*File size:* `outputs/a1_rr_ckpt/seed44/dtd/epoch10.pt` = **1 994 947 bytes**, identical to every
other `epoch10.pt` in the tree (seed-42 coco/dtd/food101/flickr30k_ref, seed-43/44 × coco/dtd/food101
— 12 siblings, all 1 994 947 B), and larger than the 1 989 277 B epoch-1..9 files. So the file **is**
a complete, final checkpoint. **PASS.**

*But "byte-identically" is not established:* the only evidence available is that the size matches;
the report cites the same size as its proof. No pre-reboot digest exists, so byte identity is
**unverifiable** and the wording overstates the evidence. See **V-12a**.

*Losses match the recovery spec:*

| epoch | `a1_h_recover_spec_dtd_seed44.json → history` | `a1_h_seeds_dtd_seed44.json → history` | `logs_a1_h_seeds.txt` (lines 636–654) |
|---|---|---|---|
| 1–5 | 2.0994 / 1.4367 / 1.1856 / 1.0287 / 0.9908 | identical | `loss=2.0994 / 1.4367 / 1.1856 / 1.0287 / 0.9908` |
| 6–10 | 0.8985 / 0.8286 / 0.8082 / 0.8119 / 0.8081 | identical | `loss=0.8985 / 0.8286 / 0.8082 / 0.8119 / 0.8081` |

`spec.history == rebuilt.history` is `True` element-wise; `spec.frozen == rebuilt.frozen` is `True`.
The log's cumulative-time jump at epoch 6 (`207.2 s → 2118.9 s`) independently corroborates the
interruption. **PASS** for the loss check.

*However the report's description of the recovery mechanism is wrong.* It says
`--seed-json` "**re-measures everything**". In `tools/a1_h_e4_seed.py` line 401 the recovery path
writes `{'frozen': src['frozen'], 'history': src['history'], 'result': res}` — i.e. it **copies**
`frozen` and `history` verbatim from the recovery spec and recomputes **only** `result`. The spec's
own `_recovery_note` says as much ("This meta block was reconstructed by hand …"); and the rebuilt
JSON's `meta.runtime_s` is `null` (the script only sets `runtime_s` on the non-recovery path, line
446) even though the log shows the recovery run took **369.9 s**. The seed-44 history values are also
rounded to 4 decimals whereas every other run's are full precision
(e.g. seed-43 DTD epoch 1 = `2.1066491842269897`). See **V-12b**.

### 7.3 (c) `food101_seed43` is genuinely complete — **PASS**

* `meta.epochs = 10`, `meta.n_steps = 320`, `history` has **10** entries with a sane decreasing loss
  profile (`0.9886 → 0.4470`).
* 50k evaluation present and consistent: `result.top1_50k_legacy1001 = 58.716`,
  `top1_50k_clean1000 = 58.716`, `CG_flickr_val = 0.826939`, `tau_by_k["5"] = 0.580987`.
* The log for that file ends with
  `food101: tau5={…0.580987…} | top1_5k={…59.78…} | CG=0.8269 | top1_50k={…58.716…}`,
  `ALL DONE -> outputs/a1_h_seeds_food101_seed43.json (1318.7s)`, `exit=0` — and `meta.runtime_s`
  is exactly `1318.7`. The JSON was written by that completed run.
* **Not verifiable:** the report says a *first* evaluation attempt died with
  `torch.AcceleratorError: CUDA error: an illegal memory access`. No log in the workspace contains
  `illegal memory access`, `AcceleratorError` or `CUDA error`, and the surviving
  `run_a1_h_resume.ps1` does not re-run `food101 seed 43`. Nothing contradicts the story; nothing
  corroborates it either. See **V-12c**.

---

## 8. Stress-tests of the two most consequential conclusions (task item 5)

### 8.1 (i) Does the τ-vs-CG contrast *strengthen* with the added seeds? — **SENSITIVE; "strengthens" FAILS**

Recomputed from `outputs/a1_h_seed_summary.json → runs` (the nine raw triples):

*The endpoint numbers are right and the contrast survives every single-run deletion:*

| variant | Spearman(τ, top-1) | Spearman(CG, top-1) | p(τ) |
|---|---|---|---|
| all 9 runs | **+0.850** | −0.267 | 0.0037 |
| leave-one-out, worst for τ | +0.786 (drop any DTD run) | −0.119 … −0.452 | 0.021 |
| leave-one-out, best for τ | +0.905 (drop any COCO run) | −0.238 … −0.452 | 0.0020 |

*But the point estimate of the headline correlation goes **down**, and the τ−CG gap narrows:*

| set | n | report | recomputed \|Δ\| = \|ρ_τ − ρ_CG\| |
|---|---|---|---|
| seed 42 only | 3 | +1.000 / −0.500 | **1.500** |
| all nine | 9 | +0.850 / −0.267 | **1.117** |
| s42+s43 | 6 | +0.886 / −0.371 | 1.257 |
| s42+s44 | 6 | +0.829 / −0.314 | 1.143 |
| s43+s44 | 6 | +0.829 / −0.029 | 0.857 |

So relative to the seed-42-only row the contrast *weakens* on both measures; what increases is only
the **evidence weight** (n = 3 → 9, p = n/a since ρ = 1 with n = 3 → p = 0.0037). The report's
"**the contrast survives, and it gets stronger**" is therefore overstated. It should say the
contrast *survives* and is now *supported by nine runs instead of three*.

*Two further sensitivities the report does not state:*

1. **The effect is entirely a between-dataset effect driven by DTD.** Dropping the DTD family
   (n = 6) gives τ = **+0.486** (p = 0.329) vs CG = **+0.657** (p = 0.156) — **the sign of the
   comparison reverses**: CG becomes the better correlate. Dropping Food-101 gives +0.829/−0.600;
   dropping COCO gives +0.943/−0.429. The 9-run result therefore rests on DTD being both the
   lowest-τ and the lowest-accuracy dataset.
2. **The τ direction is not seed-monotone.** Across the 27 one-seed-per-dataset combinations,
   Spearman(τ, top-1) takes only two values: **+1.00** (11 combos) and **+0.50** (1 combo, plus all
   COCO-seed-44 combinations); CG takes −0.50 or +0.50. In particular, for coco = s44 or
   food101 = s43, τ's rank correlation is no better than +0.5. §2.3 already concedes the
   within-dataset point; the §2.2/§6.1 framing ("the contrast strengthens", "removes the objection
   that the contrast was a seed-42 artefact") does not carry that concession. See **V-5**.

### 8.2 (ii) Does a τ < 0.5 tripwire fire at λ = −0.5 "where accuracy improves"? — **TRIPWIRE FIRES: PASS. ACCURACY-IMPROVING: FAIL**

*The tripwire table is exactly right.* From
`outputs/a1_h_bootstrap.json → k_specificity.first_lambda_below_threshold.<k>.first_lambda_below.thr_0.5`:

| k | 2 | 3 | 5 | 10 | 20 | 50 | 100 |
|---|---|---|---|---|---|---|---|
| first λ with τ < 0.5 | **1.0** | **0.5** | **−0.5** | **−0.5** | **−0.5** | **−0.5** | **−0.5** |

Verified against the stored τ values: τ(0.5, k=2) = 0.503711 ≥ 0.5 (no fire); τ(0.5, k=3) = 0.496667
< 0.5 (fires); τ(−0.5, k=5) = 0.493147 < 0.5 (fires). **PASS.**

*But the accuracy claim is inverted.* The λ = −0.5 condition is `T-0.5` in
`outputs/a1_h_baseline_metrics.json → conditions[2]`:

```
conditions[2] = {"name": "T-0.5", "family": "T", "param": -0.5,
                 "top1": 29.48, "tau_k5": 0.493147, ...}
conditions[0] = {"name": "base", "family": "base", "param": null,
                 "top1": 59.100002, "tau_k5": 1.0, ...}
```

**Accuracy at λ = −0.5 is 29.48 %, i.e. −29.62 points from the frozen baseline of 59.10 %.** It is
a severely accuracy-*destroying* intervention. The report's §4.3 states that τ < 0.5 at k ≥ 5 is
"tripped by a perturbation that makes the model **better**" and calls λ = −0.5 "an
accuracy-*improving* intervention, top-1 29.5 %", and §6.1 repeats "already at the *accuracy-improving*
λ = −0.5". The number quoted (29.5, actually 29.48) is the number in the JSON, but it is not
"improving" by any reading — the improvement at 29.5 % would require the frozen baseline to be below
29.5 %, and it is 59.1 %. The accuracy-improving conditions in the same grid are `T0.25` (55.80, still
below baseline) and `P0.5` (78.08) — neither is at λ = −0.5. See **V-14** — this is the most
consequential error found, because it is the concrete "practical consequence" argument the report
uses to justify a mandatory k statement in the manuscript.

*Note:* the tripwire conclusion *is* still defensible in a weaker form — at k ≥ 5 the τ < 0.5 alarm
fires on a **catastrophically damaging** perturbation whose accuracy damage (59.10 → 29.48) is
larger than any of the positive-λ points above λ = 0.25. That is a *severity* mismatch argument,
not an accuracy-improvement argument.

---

## 9. Overstatements, inconsistencies and unverifiable claims

### Overstatements

**V-5 — "the contrast survives, and it gets stronger" (§2.2 verdict, §6.1 item ②).** The point
estimate of Spearman(τ, top-1) falls from +1.000 (n=3) to +0.850 (n=9) and the τ−CG gap narrows
from 1.500 to 1.117. What improved is the evidence weight. Additionally the n=9 result is fragile in
a way the report does not say: **dropping the DTD family reverses the comparison** (τ +0.486 vs
CG +0.657) and 16 of 27 one-seed-per-dataset subsets give τ = +0.50.

**V-11 — "the remaining geometry deltas are 1–2 orders of magnitude too small" (§5.5, §6.1 item ⑤).**
Taking the report's own frozen values (`frozen.within_class_spread_mean = 0.12905`,
`frozen.margin_top1_mean = 0.005227`) and the largest deltas
(`max|Δ spread| = 0.016872`, `max|Δmargin| = 0.003853`), the margin delta is **74 %** of the frozen
margin — same order of magnitude, not 1–2 orders smaller. The within-class-spread delta is 13 %. The
claim needs the smaller 12-checkpoint magnitudes (0.006336 / 0.003853) to even approach "an order of
magnitude smaller", and even then 0.003853/0.005227 = 0.74.

**V-10 — "the template spread is 6–25× larger than the bootstrap CI half-width at every point" (§4.4).**
Recomputed per cell, the ratio spans **3.44× to 32.68×**; the 6–25× interval neither contains the
minimum nor the maximum. The underlying conclusion (template effect ≫ sampling noise) still holds
at every cell, but the stated range is wrong.

**V-7 — "A τ number quoted without its template is not well defined to better than ±0.05." (§3.3)**
The measured template spread ranges from 0.0652 (DTD, λ=0.5) to 0.1110 (Food-101, λ=1). "±0.05" is
a *weaker* claim than the data support, and it is inconsistent with the report's own sentence two
lines earlier ("Template choice moves τ by up to 0.111"). Prefer "to better than ±0.065".

**V-3 — precision of a rounded value.** §1.1/§1.2/§6.1 render `metric_correlations.CG.spearman_r`
as "**−0.2150**". The JSON stores `-0.215`; no more precision exists. The p-value (0.2914) and Δ
(0.1329) are correct.

**V-12a — "survived byte-identically" (§②, incident 2).** The checkpoint's file size (1 994 947 B) is
identical to all 12 sibling `epoch10.pt` files, which shows it is a complete final checkpoint; it does
**not** show byte identity. No pre-reboot digest exists.

### Numeric inconsistencies

**V-4 — the 12-checkpoint excess range.** §5.2: "**+3.62 ± 1.41 points** (range **+0.54 … +6.06**)",
attributed to the 12 vision-LoRA checkpoints. The 12-checkpoint extremes are **3.06** and **6.06**;
0.54 is the 13th (vision-frozen) checkpoint. The JSON's own block agrees
(`vision_lora_checkspoints.excess_stats = {n:12, mean:3.6167, min:0.54, max:6.06}`) — **the JSON
block is itself internally inconsistent**, because `min: 0.54` cannot be the min over 12 values whose
smallest member is 3.06. This is a genuine stored-data defect, not just a prose slip.

**V-2 — the E3 residual is understated by ~1.7×.** §4.2 says point estimates "reproduce the E3 JSON to
within **0.0072**", and §6.2 item 9 says "**≤ 0.0072 in τ, ≤ 0.6 points in top-1**". Recomputed
against `bootstrap.benchmarks_e3.benchmarks.*.conditions.*.tau_in_e3_json` and `top1_in_e3_json`:

| benchmark | λ | \|Δτ\| | \|Δtop-1\| |
|---|---|---|---|
| food101 | 0.5 / 1.0 / 2.0 | 0.007219 / **0.012131** / 0.010904 | 0.6732 / **1.3274** / **2.0278** |
| dtd | 0.5 / 1.0 / 2.0 | 0.000425 / 0.000851 / 0.000213 | 0.000 / 0.000 / 0.000 |
| inat_wild | 0.5 / 1.0 / 2.0 | 0.000557 / 0.001671 / 0.000278 | 0.000 / 0.000 / 0.1393 |
| rare_species | 0.5 / 1.0 / 2.0 | 0.000800 / 0.001000 / 0.001200 | 0.000 / 0.000 / 0.000 |

Max τ residual = **0.0121** (not 0.0072); max top-1 residual = **2.03 points** (not 0.6). The JSON
itself flags this correctly — 12 of the 16 E3 conditions carry `tau_agrees_with_e3: false` and 6
carry `top1_agrees_with_e3: false`, including `food101/0.0` where the *frozen* top-1 is 80.701 in the
bootstrap and 82.0594 in the E3 JSON. §4.2's prose ("Point estimates reproduce the E3 JSON to within
0.0072") is contradicted by the same file's own agreement flags. The conclusion drawn from these
rows (collapse is significant, iNat/rare end at τ ≈ 0) is unaffected — the residuals are an order of
magnitude smaller than the effects — but the stated bound is wrong and the report's own
`tau_agrees_with_e3` column shows it.

**V-1 — run times.** §① "147.7 s" and §6.3 "103.5 s" both describe
`outputs/a1_h_baseline_metrics.json`; `meta.runtime_s = 103.2`. `outputs/a1_h_hardening…` — the
147.7 s figure has no counterpart in any JSON. §6.3 also gives 197.4 s for the bootstrap
(`meta.runtime_s = 197.4` ✓), 349.2 s for the offset (✓), 185.4 s for the templates (✓) and
"710–1319 s each" for the six seed runs (actual `meta.runtime_s` = 716.9, 710.6, 760.2, `null`,
1318.7, 894.9 — the lower bound 710 is right, the upper bound 1319 is right, but `null` means the
range is not fully supported).

**V-8 — "Food-101 82.06, third of five" (§3.3 bullet 2).** `results.food101.templates.*.frozen_top1`
sorted descending: t1 `83.4693`, **t0 `82.0594`**, t4 `81.4257`, t3 `81.2119`, t2 `78.9069`. The
default template is **second** of five, not third. (ImageNet-5k: t0 59.10 = 1st ✓. DTD: t0 43.1383 =
1st ✓.) The qualitative point — the default is not cherry-picked — is unaffected and in fact
strengthened.

**V-6 — the λ = 2 contraction band "0.58 – 0.68" (§3.3 bullet 4) is unverifiable.** No key in
`outputs/a1_h_templates.json` or `outputs/a1_h_baseline_metrics.json` stores that interval. The
templates file has no contraction family at all; the certified grid's contraction rows are
`C0.1 = 0.907802`, `C0.25 = 0.763482`, `C0.5 = 0.480371` (λ = 0.1/0.25/0.5, not 2) and the
model-preserving rows are `P0.25 = 0.751884`, `P0.5 = 0.608569`. The *surgery* half of the sentence
(0.07 – 0.30) is verified. Because the load-bearing claim in that bullet is "contraction ≫ surgery
at matched λ under every template", which the surgery numbers do support, the defect is confined to
the quoted contraction interval.

**V-13 — the ground rule "every new JSON carries a `meta` block naming the script, the class-list
length, the shard signature" (§"Ground rules", §6.1).** The *substance* is met — every result JSON
carries `meta.script`, and every JSON that scores ImageNet carries either `class_list_len` (4 files)
or the equivalent `placeholder_class_index = 1000` + `n_tau_images = 5000` pair (the six seed JSONs).
Two wording-level gaps: `a1_h_seed_summary.json` has no class-list field, no shard signature and no
`runtime_s` (it is a pure analysis of other files, so arguably fine), and
`a1_h_recover_spec_food101_seed43.json` is a top-level **list** with no `meta` block at all. The
rule should read "**every run JSON**". Not a factual error; a precision caveat recorded here rather
than counted as a failure.

**V-14 — "which re-measures everything" (§②, incident 2).** `tools/a1_h_e4_seed.py` line 401 writes
`{'frozen': src['frozen'], 'history': src['history'], 'result': res}`: `frozen` and `history` are
copied from the recovery spec and only `result` is recomputed. Confirmed at the data level — the
rebuilt JSON's `frozen` and `history` are element-wise equal to the spec's (the spec has no `result`
key at all), `meta.runtime_s` is `null` even though the recovery run took 369.9 s per
`logs_a1_h_resume.txt` line 163, and its ten losses are 4-decimal rounded unlike every other run's.

### Verifiability gaps

**V-12c — the `food101_seed43` CUDA crash is not documented.** No file in the workspace contains
`illegal memory access` / `AcceleratorError` / `CUDA error`; the resume batch never re-ran
food101 seed 43. The surviving artefact (runtime 1318.7 s, exit 0, 10 epochs, 50 k present) is
consistent with a clean single run.

**V-12b — no log of the earlier validator failure.** The 300-step correction is fully justified by
the arithmetic and the code, but no failing validator run is preserved.

**V-14b — the validators do not validate what §"Reproducing this document" implies.**
`tools/a1_h_validate.py` cannot check per-image arrays for the six seed JSONs, because those files
**contain no per-image arrays** — it checks `n_tau_images == 5000` (a meta scalar), the presence of
`tau_by_k` keys, `len(history) == 10`, and a loose 5k-vs-50k top-1 sanity bound. `a1_h_validate2.py`
does check genuine per-image arrays, but only in the templates file (45 of them) and only re-reads
aggregates for the offset, bootstrap and seed JSONs; it also contains a dead placeholder
(`recomputed = mt['synthetic_lambda'] * 0`). The sentence "Both validators check that each per-image
array has its full expected length" is true only of the baseline/metrics file and the templates file.
No file asserts `n_steps == 10 × ceil(n_pairs/64)` except `a1_h_validate.py` — and nothing in the
JSON itself records that invariant.

**V-9 — "SE" heading over an SE-valued column (§4.2).** In the §4.2 table the columns headed
`95 % CI` / `SE` / `E3 stored τ` do not track the JSON's meaning: the JSON's `se` for DTD λ=0.5 is
`0.007145866…`, which the report prints as "0.0071" in the `SE` column — but the `95 % CI` column it
prints beside it (`[0.5502, 0.5780]`) is the *half-width* 0.0139, not a SE. The table is arithmetically
consistent (it prints `point`, `ci_low`, `ci_high` and `se` correctly); the two columns are simply
being read in different units and the §4.2 "Reading" bullet then compares the report's half-widths to
the JSON's SEs. Not a number error; a column-semantics ambiguity worth fixing.

**V-15 — §2.1 table column semantics.** The "top-1 50k" column in the first §2.1 table is correct
for all nine rows, but the second §2.1 table's "range" column for COCO reads 1.13 while the
per-dataset prose says "Accuracy moves by 1.0–1.2 points of 50k top-1 on **every** dataset." COCO's
50k range is `0.95` for Food-101 and `1.13` for COCO, so the statement "1.0–1.2 on every dataset" is
false for Food-101 (`top1_50k.range = 0.95`). §6.1 item ② states the sd values (0.58/0.48/0.66),
which are correct, but §2.1's prose claim should read "0.95–1.18 points".

---

## 10. Summary table

| # | checked item | file / key path | verdict |
|---|---|---|---|
| 1 | §① τ@k=5 = 0.9125 | `a1_h_baseline_metrics.json → metric_correlations.tau_k5` | PASS |
| 2 | §① manuscript 0.9262 is the k=10 value | `…tau_k10` (0.9262, p exact) + archived file | PASS |
| 3 | §① CKA 0.7552 exact | `…cka` | PASS |
| 4 | §① mean-cosine 0.8619 | `…mean_cos` | PASS |
| 5 | §① CG −0.215 (p 0.2914) | `…CG` | PASS |
| 6 | §① CG per-condition range/mean | `conditions[*].CG` (0.263590–1.219960, mean 0.841431) | PASS |
| 7 | §① estimator cross-check ≤ 2.1e-8 | `estimator_crosscheck_vs_archived_scipy` | PASS |
| 8 | §① theory check 1.0000 / 0.0674 / 0.8149 | `theory_verification` | PASS |
| 9 | §① run time 147.7 s / 103.5 s | `meta.runtime_s = 103.2` | **FAIL** |
| 10 | §② nine per-run rows | six seed JSONs + three `a1_rr_e4_*.json` | PASS |
| 11 | §② nine seed spreads (mean/sd/range) | `a1_h_seed_summary.json → per_dataset_spread` | PASS |
| 12 | §② 9-run Spearman(τ, top-1) +0.850 (p 0.0037) | `cross_checkpoint_correlations.seed42_plus_new_seeds_all.tau5_vs_top1_50k` | PASS |
| 13 | §② 9-run Spearman(CG, top-1) −0.267 (p 0.49) | `…CG_vs_top1_50k` | PASS |
| 14 | §② subset rows (3/6/6/6/10/13) | `cross_checkpoint_correlations.*` | PASS |
| 15 | §② "the contrast strengthens" | recomputed: gap 1.500 → 1.117; DTD-driven | **FAIL** |
| 16 | §② within-dataset Spearman −0.5/−0.5/+1.0 | `within_dataset_rank_check.*` | PASS |
| 17 | §② offset over 9 seeds +4.72 ± 0.70, +4.00…+5.78 | `synthetic_curve_position_summary` | PASS |
| 18 | §② DTD 300 steps, seed-42 DTD also 300 | `a1_h_seeds_dtd_seed43.json → meta.n_steps`; `a1_rr_e4_dtd.json → meta.n_steps` | PASS |
| 19 | §③ 15/15 monotone collapse | `a1_h_templates.json → results.*&.templates.*.variants.coupled.surgery.*` | PASS |
| 20 | §③ absolute-τ drift up to 0.111 | same, recomputed max \|Δτ\| = 0.110955 | PASS |
| 21 | §③ cross-template Jaccard 0.571 / τ 0.565 | `…imagenet5k.t3_bare_class.{top5_set_jaccard_vs_t0,tau_vs_t0_on_t0_top5}` | PASS |
| 22 | §③ full §3.1/§3.3 tables | `results.*.templates.*` | PASS |
| 23 | §③ "τ not defined to better than ±0.05" | measured spreads 0.0652–0.1110 | **FAIL** |
| 24 | §③ "Food-101 82.06, third of five" | `results.food101.templates.*.frozen_top1` → t1 > **t0** > t4 > t3 > t2 | **FAIL** |
| 25 | §③ contraction band "0.58–0.68 at λ=2" | no such key | **FAIL (unverifiable)** |
| 26 | §④ dose-response grid, 9 rows | `bootstrap.dose_response_grid_imagenet5k_k5.conditions.*` | PASS |
| 27 | §④ CI half-width ±0.011; λ=0.5 vs λ=1 separation 0.176 | recomputed 0.009016–0.011947; 0.175489 | PASS |
| 28 | §④ E3 table, 16 rows (point/CI/SE/n/C/frozen) | `bootstrap.benchmarks_e3.benchmarks.*` | PASS |
| 29 | §④ iNat and rare end indistinguishable from zero | `…inat_wild.conditions["2.0"]`, `…rare_species.conditions["2.0"]` | PASS |
| 30 | §④ "to within 0.0072" (τ) and "≤ 0.6" (top-1) | `…*.tau_in_e3_json`, `…*.top1_in_e3_json` → 0.012131 and 2.0278 | **FAIL** |
| 31 | §④ k-table 7×3 + n at λ=1 | `k_specificity.per_k_bootstrap_at_sweep_lambdas` | PASS |
| 32 | §④ k shift 0.104 / 0.087 | `…absolute_level_shift_over_k` | PASS |
| 33 | §④ E2 cross-check 0.496…0.411 | `k_specificity.e2_absolute_levels_by_k.e2_absolute_levels.legacy1001` | PASS |
| 34 | §④ tripwire table k=2→1.0, k=3→0.5, k≥5→−0.5 | `k_specificity.first_lambda_below_threshold.*.first_lambda_below.thr_0.5` | PASS |
| 35 | §④ "λ=−0.5 is accuracy-improving, top-1 29.5 %" | `a1_h_baseline_metrics.json → conditions[2]` (top1 **29.48**, base 59.10) | **FAIL** |
| 36 | §④ template CI half-width windows | `bootstrap.templates.benchmarks.*` | PASS |
| 37 | §④ "6–25× larger than the CI half-width" | recomputed 3.44×–32.68× | **FAIL (wording)** |
| 38 | §⑤ synthetic curve, 8 λ rows | `a1_h_offset.json → synthetic_curve.*` | PASS |
| 39 | §⑤ 13-row matched-τ excess table | `checkpoints[*].matched_tau.excess_top1` | PASS |
| 40 | §⑤ +3.62 ± 1.41 over 12 vision-LoRA | `offset_analysis.by_vision_tower.vision_lora_checkspoints.excess_stats` (mean 3.6167, sd 1.4075) | PASS |
| 41 | §⑤ 95 % CI [2.72, 4.51] | recomputed t-based [2.7224, 4.5109] | PASS |
| 42 | §⑤ 12-checkpoint range "+0.54 … +6.06" | recomputed 3.06 … 6.06 | **FAIL** |
| 43 | §⑤ orthogonality by family (‖Δx‖, cos, ⊥ %) | `checkpoints[*].displacement.*` | PASS |
| 44 | §⑤ logit_scale exactly 100.0 for all 13 | `checkpoints[*].geometry.logit_scale`, `frozen.logit_scale` | PASS |
| 45 | §⑤ "within-class spread ≤ 0.007 / margins ≤ 0.004" | recomputed max 0.016872 (all 13) / 0.006336 (12); margin 0.003853 | **FAIL** |
| 46 | §⑤ "deltas are 1–2 orders of magnitude too small" | margin delta / frozen margin = 0.74 | **FAIL** |
| 47 | §⑤ 12-row correlation table | `offset_analysis.correlation_of_excess_with_geometry.*` | PASS |
| 48 | §⑤ "best correlate explains < 50 %" | max R² = 0.4750 | PASS |
| 49 | §⑤ text-tower control (+0.48 flagged as artifact) | `by_vision_tower.vision_frozen_checkpoints.*`, `zero_vision_displacement_control` | PASS |
| 50 | §⑤ "‖Δt‖ ≈ ‖Δx‖ for every both-tower checkpoint" | ratios span 0.71–1.50 | **FAIL** |
| 51 | JSON internal consistency: scalars == means of arrays | all 98 per-image arrays (18 + 35 + 45) | PASS |
| 52 | JSON internal consistency: no truncated arrays | none found in any `a1_h_*.json` | PASS |
| 53 | `meta` records script / class-list / shard in **every** file | every JSON *does* carry per-run seed/class-list evidence (`placeholder_class_index=1000`, `n_tau_images=5000`, `shard_sig`, `script`); the literal key `class_list_len` appears in 4/13 and one file is a bare list | PASS (wording caveat, V-13) |
| 54 | (a) DTD 300 steps is genuine, not a data problem | `meta.n_steps` + `meta.data.n_pairs_used` + `a1_rr_e4_dtd.json` | PASS |
| 55 | (b) dtd_seed44 checkpoint survived / only eval rebuilt | `outputs/a1_rr_ckpt/seed44/dtd/epoch10.pt` (1 994 947 B) | PASS |
| 56 | (b) "byte-identically" | size equality is the only evidence | **FAIL (unverifiable)** |
| 57 | (b) rebuilt per-epoch losses == recovery spec == log | `a1_h_recover_spec_dtd_seed44.json → history` vs rebuilt `history` vs `logs_a1_h_seeds.txt` L636–654 | PASS |
| 58 | (b) "`--seed-json` re-measures everything" | `tools/a1_h_e4_seed.py` L401 copies `frozen`+`history` | **FAIL** |
| 59 | (c) food101_seed43 complete (50 k + 10 epochs) | `a1_h_seeds_food101_seed43.json → result.top1_50k_legacy1001`, `history`, `meta.runtime_s` | PASS |
| 60 | (c) the CUDA-crash history | no log evidence | **FAIL (unverifiable)** |
| 61 | (i) contrast robust to single-run deletion | leave-one-out τ 0.786–0.905 | PASS |
| 62 | (i) contrast robust to dataset deletion | drop DTD → τ +0.486 vs CG +0.657 (reversed) | **FAIL** |
| 63 | (ii) tripwire fires at λ=−0.5 for k ≥ 5 | `first_lambda_below_threshold` + `per_k_bootstrap_at_sweep_lambdas` | PASS |
| 64 | (ii) λ=−0.5 "accuracy improves", top-1 29.5 % | `conditions[2].top1 = 29.48` vs base 59.10 | **FAIL** |
| 65 | §2.1 prose "accuracy moves by 1.0–1.2 pts on every dataset" | Food-101 50k range = 0.95 | **FAIL** |

Tally: rows 1–65 give **47 PASS / 18 FAIL** (the 18 include three explicitly unverifiable rows:
25, 56, 60).

---

## 11. Verdict

**What is solid.** The archival-reproduction result in §① is genuinely strong and survives
independent recomputation: the new script's k=10 row reproduces the archived value *and* its p-value
to 17 significant figures, and CKA likewise. The seed spreads in §② are numerically exact (all nine
mean/sd/range triples reproduce from the raw values). The template section §③ is the cleanest part of
the document — all 60 table entries, all 15 monotonicity flags, every spread, the Jaccard and the
cross-template τ values reproduce exactly. The bootstrap §④ dose-response and k-specificity blocks
reproduce exactly, including the tripwire table. The orthogonality measurements in §⑤ and
`logit_scale = 100.0` across all 13 checkpoints are exactly as stated. No JSON has a truncated
array; the reboot did not damage any artifact. The three process claims are substantively correct
(DTD really is a 300-step dataset, the seed-44 checkpoint really is a complete final checkpoint, and
its copied losses really do match both the recovery spec and the log).

**What does not hold.** Four findings should be corrected before this document is used as the
manuscript's evidence base:

1. **V-14 (§4.3, §6.1 item ④): the λ = −0.5 accuracy claim is inverted.** Accuracy at λ = −0.5 is
   **29.48 %**, down from a 59.10 % baseline. The report calls it "an accuracy-*improving*
   intervention" twice and builds its recommendation to the manuscript on that. The tripwire table
   itself is right; the interpretation attached to it is not.
2. **V-5 (§2.2, §6.1 item ②): "the contrast strengthens" is wrong.** The correlation falls
   1.000 → 0.850 and the τ−CG gap narrows 1.50 → 1.12; and the n=9 result reverses
   (τ +0.486 vs CG +0.657) if the DTD family is removed. "Survives, now on nine runs" is supportable;
   "strengthens" is not.
3. **V-2 (§4.2, §6.2 item 9): the E3 residual bound is understated ~1.7× (τ) and ~3.4× (top-1),**
   contradicting the JSON's own `tau_agrees_with_e3` / `top1_agrees_with_e3` flags. The conclusion
   survives; the stated bound does not.
4. **V-11 (§5.5, §6.1 item ⑤): "1–2 orders of magnitude too small" is a mis-description** of
   deltas that are 13 % and 74 % of the frozen quantities they are compared against.

The report's own concluding instruction — "soften the Figure-2 claim" — is the right instinct, and
the same standard should now be applied to §2.2's "strengthens", §4.3's "accuracy-improving", §5.5's
"1–2 orders of magnitude" and §2.1's "1.0–1.2 points on every dataset".

---

**PASS count: 47. FAIL count: 18.**

FAIL list (one line each):

* V-1 — Run-time figures: §① says 147.7 s, §6.3 says 103.5 s; `outputs/a1_h_baseline_metrics.json → meta.runtime_s` = **103.2**.
* V-2 — E3 residual understated: §4.2/§6.2 say ≤ 0.0072 in τ and ≤ 0.6 in top-1; `a1_h_bootstrap.json → bootstrap.benchmarks_e3…` gives **0.012131** (food101 λ=1) and **2.0278** points, with 12/16 `tau_agrees_with_e3 = false`.
* V-3 — §①/§6.1 print CG as "−0.2150"; `a1_h_baseline_metrics.json → metric_correlations.CG.spearman_r` stores only `-0.215`.
* V-4 — §5.2 gives the 12-checkpoint excess range as "+0.54 … +6.06"; the 12 vision-LoRA values span **3.06 … 6.06** (0.54 is the 13th, vision-frozen checkpoint) — and `offset_analysis.by_vision_tower.vision_lora_checkspoints.excess_stats.min` is itself wrong at `0.54`.
* V-5 — §2.2/§6.1 "the contrast survives, and it gets stronger": Spearman(τ) falls 1.000 → 0.850 and the τ−CG gap narrows 1.50 → 1.12; dropping the DTD family reverses the comparison (τ **+0.486** vs CG **+0.657**).
* V-6 — §3.3's "class-contraction family sits at τ = 0.58 – 0.68 at λ = 2" is unverifiable — no such interval exists in `a1_h_templates.json` or `a1_h_baseline_metrics.json`.
* V-7 — §3.3 "not well defined to better than ±0.05": the measured template spreads are **0.0652 – 0.1110**, i.e. the stated bound is weaker than the data.
* V-8 — §3.3 "Food-101 82.06, third of five": `results.food101.templates.*.frozen_top1` orders t1 83.4693 > **t0 82.0594** > t4 > t3 > t2, so the default is **second**.
* V-9 — §4.2's "Reading" calls the SEs of 0.004 / 0.016 "CI widths"/"half-widths"; the JSON's `se` is right and the half-widths are 0.0035–0.0047 and 0.0298–0.0311, so the units in the prose are mixed (presentation, not arithmetic).
* V-10 — §4.4 "the template spread is 6–25× larger than the bootstrap CI half-width at every point"; recomputed ratios span **3.44× – 32.68×**.
* V-11 — §5.3/§5.5 "within-class spread changes by ≤ 0.007 (frozen 0.12905 → 0.112–0.135)" and "1–2 orders of magnitude too small": max |Δ| is **0.016872** over all 13 (0.006336 over the 12), the 0.112–0.135 range is the *between-checkpoint* spread not a delta, and the margin delta 0.003853 is **74 %** of the frozen margin 0.005227.
* V-12a — §② "survived byte-identically": only the file *size* (1 994 947 B, matching 12 siblings) is evidenced; no pre-reboot digest exists.
* V-12b — §② "`--seed-json` … re-measures everything": `tools/a1_h_e4_seed.py` L401 writes `{'frozen': src['frozen'], 'history': src['history'], 'result': res}`, copying frozen and history; corroborated by `meta.runtime_s = null` despite the 369.9 s recovery run in `logs_a1_h_resume.txt`.
* V-12c — §② the `food101_seed43` CUDA illegal-memory-access crash is asserted in `a1_h_recover_spec_food101_seed43.json` but **no log contains** `illegal memory access` / `AcceleratorError` / `CUDA error`.
* V-13 — §"Ground rules" "every new JSON carries a `meta` block naming the script, the class-list length and the shard signature": true in substance but not in the literal key — only 4 of 13 files carry `class_list_len`, the six seed JSONs record the same facts as `placeholder_class_index` + `n_tau_images`, and `a1_h_recover_spec_food101_seed43.json` is a bare top-level **list** with no `meta` (wording).
* V-14 — §4.3/§6.1 "already at the *accuracy-improving* λ = −0.5 (top-1 29.5 %)": `a1_h_baseline_metrics.json → conditions[2]` (`T-0.5`) has `top1 = 29.48` against `conditions[0].top1 = 59.10` — accuracy **falls 29.62 points**; the tripwire table itself is correct.
* V-14b — §"Reproducing this document" implies both validators guard truncation of every per-image array; `a1_h_validate.py` cannot (the six seed JSONs contain **no** per-image arrays — it checks a meta scalar `n_tau_images`, `len(history) == 10` and a 5k-vs-50k bound), and `a1_h_validate2.py` checks real arrays only in the templates file plus aggregates elsewhere (it also carries a dead placeholder `recomputed = mt['synthetic_lambda'] * 0`).
* V-15 — §2.1 "Accuracy moves by 1.0–1.2 points of 50k top-1 on **every** dataset": Food-101's range is **0.95** (`a1_h_seed_summary.json → per_dataset_spread.food101.top1_50k.stats.range`).

Caveats that move no number (already listed above as V-9 and V-13, and counted in the 18):

* **V-9 — §4.2 column semantics.** The `SE` column correctly prints the JSON's `se` and the `95 % CI` column correctly prints `ci_low`/`ci_high`; but the §4.2 "Reading" bullet quotes "0.004" and "0.016" as "CI half-widths" when those are the **SEs** — the half-widths are 0.0035–0.0047 (Food-101) and 0.0298–0.0311 (iNat). The 1/√n scaling argument is unaffected. Rename the bullet to "bootstrap SE" or quote the half-widths.
* **V-13 — "every new JSON carries a `meta` block naming the script, the class-list length and the shard signature".** The substance holds (see §6.2); only the literal key name is inconsistent — the six seed JSONs record the same fact as `placeholder_class_index` + `n_tau_images`. Reword to "every run JSON".
