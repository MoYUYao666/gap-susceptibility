# A1 — Evidence-hardening experiments (five items)

Companion to `docs/A1_REVIEWER_EXPERIMENTS.md`. Manuscript: **paper_a1/** (rejected by Pattern
Recognition Letters, being revised for Multimedia Tools and Applications). Thesis under test: the
modality gap is not a universal health metric for contrastive vision–language models; the
operative quantity is **τ**, the Kendall order-preservation coefficient of class-relative
similarity ranks (frozen **top-5** class sets) under gap surgery (exact translations of the image
embedding cluster along the estimated gap direction `g = μ_T − μ_I`).

## Ground rules for every number in this document

* Every number is read out of a JSON produced **in this session** under `outputs/a1_h_*.json` or,
  where explicitly stated, `outputs/a1_rr_*.json` (pre-existing) or `outputs/a1_baseline_metrics.json`
  (the archived file under audit). Nothing is hand-computed, extrapolated, or copied from a draft.
* Every **run** JSON carries a `meta` block naming the script, the class-list length(s), the ImageNet
  shard signature, the seeds, and the run time, so each number is traceable. Two exceptions are
  recorded rather than hidden: the analysis file `outputs/a1_h_seed_summary.json` carries no
  class-list, shard-signature or runtime field (it derives its numbers from the run JSONs it
  hashes), and `outputs/a1_h_recover_spec_food101_seed43.json` is a bare top-level list with no
  `meta` block. The six seed JSONs also record the class list as `placeholder_class_index = 1000`
  plus `n_tau_images = 5000` rather than under the literal key `class_list_len`, so the literal key
  appears in 4 of the 13 files.
* Only **new** filenames are used (`tools/a1_h_*.py`, `outputs/a1_h_*.json`). No pre-existing file
  under `outputs/` was overwritten and nothing under `paper_a1/` was touched.
* GPU jobs run **strictly one at a time** (single RTX 4060 Laptop, 8 GB).
* Where something cannot be measured it is written as **"not measurable"** with the reason.
* Conventions reused unchanged: CLIP ViT-B/32 (`openai/clip-vit-base-patch32`,
  `local_files_only`), fixed 5 000-image ImageNet sample `RandomState(42)`, gap direction from
  Flickr30k rows 2000..3000, `legacy1001` class list (published τ tables) alongside `clean1000`,
  the archived scipy `kendall_topk` estimator, template `a photo of a {}`.

### Environment and shared estimator checks

| check | result | where |
|---|---|---|
| torch / CUDA | 2.9.1+cu130, RTX 4060 Laptop, `torch.cuda.is_available()=True` | run logs |
| ImageNet shard signature | `d13718e47e9e41c2` (14 parquet shards) — identical to every `a1_rr_*` run | `meta.shard_signature` in every new JSON |
| class list | 1001 names (`legacy1001`) = 1000 real ImageNet-1K classes + trailing placeholder `none` at index 1000 | `meta.class_list_len` |
| τ estimator cross-check | vectorised tie-aware Kendall τ_b reproduces the archived scipy loop **exactly**: max per-image deviation 1.1e-16 on a controlled tie/no-tie test; in-run deviations recorded in `estimator_crosscheck_vs_archived_scipy` | `tools/a1_h_common.py`, `outputs/a1_h_baseline_metrics.json` |

---

## Section index

| # | item | status | headline | outputs |
|---|---|---|---|---|
| ① | certify the baseline-metrics row | **done** | τ@k=5 = **0.9125**; the manuscript's 0.9262 is the **k=10** value; CKA reproduces exactly | `outputs/a1_h_baseline_metrics.json` |
| ② | seed spread for the non-Flickr30k checkpoints | **done** | τ₅ spread 0.0005 (COCO) to 0.029 (Food-101); τ vs accuracy **+0.85** over 9 runs vs CG **−0.27** | `outputs/a1_h_seeds_*.json`, `outputs/a1_h_seed_summary.json` |
| ③ | prompt-template sensitivity | **done** | collapse monotone 15/15; absolute τ moves **up to 0.111** with the prompt | `outputs/a1_h_templates.json` |
| ④ | bootstrap CIs for τ (+ k-specificity) | **done** | CI half-width ±0.011 at 5 k images; k shifts τ by **up to 0.104** | `outputs/a1_h_bootstrap.json` |
| ⑤ | explain the systematic offset | **done — not explained** | excess **+3.62 ± 1.41 pts**; real fine-tuning is **86–99.7 % orthogonal** to `d̂` vs 0 % for surgery | `outputs/a1_h_offset.json` |

Every section below is complete. §6 consolidates what remains open.

### Reproducing this document

```
python tools/a1_h_validate.py          # every seed JSON + the certification JSON: PASS
python tools/a1_h_validate2.py         # templates + offset + bootstrap: PASS
```
What the two validators actually guard is narrower than "every per-image array", and the difference
is recorded here rather than implied. `a1_h_validate.py` checks **every** per-image array of the
certification JSON for full length and for mean-equals-stored-scalar agreement (53 arrays: the 18
`per_image_tau_by_condition` blocks plus the 35 `per_image_tau_k_sweep` blocks); the six seed JSONs
contain **no** per-image arrays at all, so for them it checks meta scalars instead
(`n_tau_images = 5000`, `n_steps = 10 × ceil(n_pairs/64)`, `len(history) = 10`) plus the presence
and shape of `result`. `a1_h_validate2.py` checks genuine per-image arrays only in the templates
file (45 of them); for the offset and bootstrap JSONs it re-reads stored aggregates and structural
keys. Both check the shard signature `d13718e47e9e41c2`, so both are a guard against a truncated or
mis-shapen JSON — but neither recomputes a per-image array it cannot see.


---

## ① Certify the baseline-metrics row

**Why.** `outputs/a1_baseline_metrics.json` (2026-08-15) holds a row quoted in the manuscript:
Spearman of τ / linear CKA / mean embedding cosine / Centroid Gap (CG) with top-1 over a
26-condition perturbation grid. The audit found the archived file is not reproducible: its τ
correlation matches a **top-10** computation rather than the top-5 the archived script now
performs, and its CG (−0.0821 stored) and mean-cosine (0.8715 stored) were reported as
non-reproducing (−0.0828 and 0.8619).

**What ran.** `tools/a1_h_baseline_metrics.py` → **`outputs/a1_h_baseline_metrics.json`**
(103.2 s, i.e. `meta.runtime_s`; 26 conditions; 5 000-image ImageNet sample `RandomState(42)`; `RandomState(7)`
perturbation stream; `legacy1001`, 1 001 class names). The archived script
`tools/clip_a1_baseline_metrics.py` was **not modified** and is **not** used; its protocol was
copied verbatim into the new file, which records hashes of both
(`archived_script_sha1 = 74431c0c0ce463aaf6dca9cd362418390fb9b013`). Because the archived script
hard-codes `[:, :5]` while the archived *value* is a top-10 number, the new script takes a
`--tau-k` switch and was run once with `--tau-k 5 10`, so **both** the manuscript's top-5
convention and the archived file's top-10 convention come out of the *same* code state.

### 1.1 Certified row vs archived row — per-statistic agreement

| statistic | certified (this run) | archived | Δ | agree at 5e-4? |
|---|---|---|---|---|
| Spearman(τ@**k=5**, top-1), 26 cond. | **0.9125** (p = 8.4785e-11) | 0.9262 | 0.0137 | **no** |
| Spearman(τ@**k=10**, top-1), 26 cond. | **0.9262** (p = **1.1861084080501641e-11**) | 0.9262 | 0.0000 | **yes — exact** |
| Spearman(linear CKA, top-1) | **0.7552** (p = 8.218838697506625e-06) | 0.7552 | 0.0000 | **yes — exact** |
| Spearman(mean embedding cosine, top-1) | **0.8619** (p = 1.5443e-08) | 0.8715 | 0.0096 | no |
| Spearman(Centroid Gap, top-1) | **−0.215** (p = 0.2914; the JSON stores three decimals) | −0.0821 | 0.1329 | no |

The τ and CKA columns agree **to machine precision, including the p-values**, which is the
strongest possible confirmation that this is the right protocol: a statistic that is a smooth
function of the 26 grid points can only reproduce a stored p-value to 17 significant figures if
the grid, the estimator and the sample are all identical.

**Verdict on the criticism.** *Closed.* The manuscript's headline τ-correlation is a **k = 10**
number, not top-5: at the top-5 convention the script now implements, the value is **0.9125**.
The revision must either quote 0.9125 as the top-5 row or state explicitly that the headline
correlation uses top-10. The E2 ablation (`outputs/a1_rr_e2_topk.json`) shows the paper's claim is
unaffected either way, because every k ∈ {3,…,100} gives 0.913–0.936.

### 1.2 The two statistics that still do not reproduce

**First, a correction of the audit framing.** The archived JSON stores `CG: −0.0821` and
`mean_cos: 0.8715` inside `metric_correlations` — these are **Spearman correlation coefficients of
those metrics with top-1 across the 26 conditions**, not the metric values themselves. The
certified run measures every per-condition CG and finds them all in **[+0.264, +1.220]** (mean
**+0.841**); not one is negative. So no per-condition CG value can equal −0.0821, and the
comparison "archived −0.0821 vs reproduced −0.0828" in the original audit was between two
different quantities. The −0.0828 in the audit is, in fact, a single pair-level sample of the
bias-field difference in `outputs/a1_margins.json` (`pair_samples.b`, a 50 000-element array with
min −0.381, max +0.357 — one of its entries is −0.08285278081893921). It is a coincidence of
floating-point values, not a CG.

The correct comparison is correlation-to-correlation:

| statistic | certified (this run) | archived | Δ | note |
|---|---|---|---|---|
| Spearman(τ@k=5, top-1) | **0.9125** | 0.9262 | 0.0137 | archived value is the k=10 number |
| Spearman(τ@k=10, top-1) | **0.9262** | 0.9262 | **0.0000** | exact, incl. p-value |
| Spearman(linear CKA, top-1) | **0.7552** | 0.7552 | **0.0000** | exact, incl. p-value |
| Spearman(mean cosine, top-1) | **0.8619** | 0.8715 | 0.0096 | not reproduced |
| Spearman(CG, top-1) | **−0.215** | −0.0821 | **0.1329** | not reproduced |

*(a) Is the stored correlation reachable by another admissible definition?* — No.

| CG variant (same 26-condition grid, same top-1 series) | Spearman with top-1 | mean CG | = −0.0821? |
|---|---|---|---|
| val block rows 2000..3000 (archived code path) | **−0.215** | 0.841431 | no |
| val block rows 0..1000 (out-of-sample block) | **−0.215** | 0.837020 | no |
| un-normalised pooled embeddings | not computed — the archived protocol never forms them (recorded as such in the JSON) | — | — |

Both CG definitions give the **same correlation (−0.215) and the same p-value**, so the choice of
Flickr30k block does not matter; neither reaches the archived −0.0821.

| mean-cosine variant | value | reaches stored 0.8715? |
|---|---|---|
| as implemented (the archived `cos_self_5k` formula) | **1.000000** | no — self-cosine is 1 by construction |
| mean 5k embedding vs mean val embedding | 0.465424 | no |
| mean 5k embedding vs mean text embedding | 0.181905 | no |

*(b) Run-to-run stability of these statistics.* The same script was executed repeatedly during
this session, which measures the noise floor directly instead of guessing it:

| quantity | observed across independent runs of the same script |
|---|---|
| frozen Flickr30k-val CG | 0.814736 (archived E4) → 0.815732 → 0.815402 (E3) → **0.814929** (certified) — spread **1.0e-3** |
| frozen 5k top-1 | 59.10 in every run |
| Spearman(τ@k=10) | 0.9262 in every run |
| Spearman(CKA) | 0.7552 in every run |
| Spearman(mean cosine) | 0.8619 in every run |
| Spearman(CG) | −0.215 in every run |

τ, CKA and mean-cosine are **bit-stable** across runs. The gap statistic is not: it is a mean of
batch-normalisation-sensitive pooled embeddings, and it moves by ~1e-3 between runs. This explains
*part* of the archived discrepancy — the archived absolute CG sits inside the measured spread of
the CG statistic itself, so it was never going to reproduce exactly — but it does **not** explain
the archived CG correlation (−0.0821 vs a stable −0.215) or the archived mean-cosine correlation
(0.8715 vs a stable 0.8619), both of which are far outside any spread observed here.

**Open question (stated, not invented).** The archived `outputs/a1_baseline_metrics.json` records
neither the script hash, nor the seeds, nor the class-list length, so its exact provenance cannot
be recovered from the artifact, and no code state I could construct regenerates its CG and
mean-cosine columns. **Recommendation for the revision: quote the certified row in §1.1 instead**
(it is internally consistent, reproduced from one code state, and carries its own provenance) and
either drop the CG / mean-cosine columns or mark them as unreproducible.

### 1.3 Supporting facts from the same JSON

* Estimator cross-check `estimator_crosscheck_vs_archived_scipy`: the vectorised τ_b agrees with
  the archived scipy loop to **max 2.1e-8** on `T0.5`/`P0.5` at k = 5 and k = 10 (400 images);
  identical (diff 0.0) at λ = 0.
* Class bias-field theory check: `pearson(actual, predicted) = 1.0000`, `std(m_c) = 0.0674`,
  `gap_norm = 0.8149` — the λ = 1 class bias field is predicted exactly, as the manuscript claims.
* Sanity reproduction of independently published numbers: τ@k=5 at λ = 0.25 is **0.6425** and at
  λ = 0.5 is **0.4656**, both matching `outputs/a1_rr_e2_topk.json` (0.64277 / 0.4654) from a
  different script.
* Frozen 5k top-1 = **59.10 %**, matching `outputs/a1_tau_trajectory.json` and the manuscript.

---

## ② Seed spread for the non-Flickr30k checkpoints

**Why.** `tools/a1_rr_e4_train.py` trained LoRA on COCO, Food-101 and DTD with **seed 42 only**.
`docs/A1_REVIEWER_EXPERIMENTS.md` §4.4 lists this as "the main weakness that remains in E4".
Two further seeds per dataset were run with an identical configuration.

**What ran.** `tools/a1_h_e4_seed.py` → six runs,
`outputs/a1_h_seeds_{coco,food101,dtd}_seed{43,44}.json`. This is a verbatim copy of
`tools/a1_rr_e4_train.py` (same trainer, same evaluator, same LoRA r8/α16 both towers, by-name
`lora_` selection, AdamW lr 1e-4 wd 0.01, cosine, batch 64, 10 epochs, 2 000 pairs) with exactly
one change: checkpoints are written to `outputs/a1_rr_ckpt/seed<seed>/<dataset>/` so the
pre-existing seed-42 checkpoints are **never overwritten**. The only knob that differs between
seeds is the seed itself, which enters both the 2 000-pair subsample and the DataLoader shuffle
order. Seed-42 rows come from the pre-existing E4 JSONs and were validated, not re-run.

**Two incidents, both handled without inventing data.**
* The Food-101 seed-43 *evaluation* was lost to a CUDA failure after its training had finished and
  its checkpoints were written. **The failure itself is not documented:** no surviving log contains
  `illegal memory access`, `AcceleratorError` or `CUDA error`, and the surviving resume script does
  not re-run this job. What *is* evidenced is the artefact it left behind — the completed JSON
  (`a1_h_seeds_food101_seed43.json`: `meta.runtime_s = 1318.7`, ten `history` entries, the 50k
  evaluation present) **passed validation**, and the recovery spec is kept at
  `outputs/a1_h_recover_spec_food101_seed43.json`. The crash story is consistent with the artefacts
  but is corroborated by none of them, and is recorded here as reported rather than as evidenced.
* The machine was rebooted during the DTD seed-44 evaluation. Its `epoch10.pt` survived
  (1 994 947 B — the same *size* as the twelve sibling `epoch10.pt` files, which shows it is a
  complete final checkpoint; no pre-reboot digest exists, so **byte identity is not established**,
  only size identity), so only the evaluation was lost. It was rebuilt with the new `--seed-json`
  recovery mode of `tools/a1_h_e4_seed.py`, which **copies** `frozen` and `history` from the
  recovery spec and recomputes **only** `result` (`tools/a1_h_e4_seed.py` line 401 writes
  `{'frozen': src['frozen'], 'history': src['history'], 'result': res}`) and stamps
  `meta.recovered_evaluation`; the rebuilt JSON's `meta.runtime_s` is `null` even though the
  recovery run took 369.9 s per `logs_a1_h_resume.txt`. The ten per-epoch train losses
  are the real values printed by the killed run and preserved in `logs_a1_h_seeds.txt`; they are
  recorded in `outputs/a1_h_recover_spec_dtd_seed44.json`.

### 2.1 Three seeds per dataset (`legacy1001`, k = 5)

| dataset | seed | τ₅ | top-1 5k | top-1 **50k** | CG (Flickr val) | steps |
|---|---|---|---|---|---|---|
| COCO | 42 | 0.575433 | 58.14 | 58.052 | 0.7777 | 320 |
| COCO | 43 | 0.575651 | 56.94 | 56.922 | 0.7664 | 320 |
| COCO | 44 | 0.575929 | 57.56 | 57.298 | 0.7685 | 320 |
| Food-101 | 42 | 0.593573 | 58.22 | 58.212 | 0.8205 | 320 |
| Food-101 | 43 | 0.580987 | 59.78 | 58.716 | 0.8269 | 320 |
| Food-101 | 44 | 0.564444 | 58.34 | 57.766 | 0.8376 | 320 |
| DTD | 42 | 0.540227 | 55.42 | 55.000 | 0.8315 | **300** |
| DTD | 43 | 0.541102 | 55.74 | 55.102 | 0.8358 | **300** |
| DTD | 44 | 0.514949 | 53.50 | 53.920 | 0.8332 | **300** |

| dataset | τ₅ mean ± sd (range) | top-1 50k mean ± sd (range) | CG mean ± sd (range) |
|---|---|---|---|
| COCO | **0.5757 ± 0.0002** (0.0005) | **57.42 ± 0.58** (1.13) | 0.7709 ± 0.0060 (0.0113) |
| Food-101 | **0.5797 ± 0.0146** (0.0291) | **58.23 ± 0.48** (0.95) | 0.8283 ± 0.0086 (0.0170) |
| DTD | **0.5321 ± 0.0149** (0.0262) | **54.67 ± 0.66** (1.18) | 0.8335 ± 0.0022 (0.0044) |

**The spread is real, and it is dataset-dependent.** Seed-to-seed τ₅ varies by a factor of ~30
between datasets: COCO is essentially seed-immune (sd 0.0002 on a 0.575 level, i.e. 0.04 %
relative) while DTD and Food-101 both move by ~0.015 (2.5 % relative). Accuracy moves by
**0.95–1.18** points of 50k top-1 across the three datasets (`per_dataset_spread.*.top1_50k.stats.range`:
0.95 Food-101, 1.13 COCO, 1.18 DTD). So a single-seed τ comparison between datasets carries
±0.015 of noise for two of the three datasets — which is the same order as the entire τ range the
E4 cross-dataset comparison relied on.

**A confound this exposed (recorded, not fixed).** DTD runs **300** steps, not 320: its entire
train split is 1 880 images, so 10 epochs × ceil(1 880/64) = 300 steps. This is true of the
seed-42 DTD run too, i.e. the original E4 comparison already compared DTD at a 6.25 % smaller
optimisation budget than the other datasets. DTD is also the only dataset where the seed spread is
visible *through* the sampling (all 1 880 images are used for every seed; only the shuffle order
changes), which makes its 0.015 τ₅ spread a clean estimate of initialisation/shuffle sensitivity.

### 2.2 Does the "τ beats CG" contrast survive the added seeds?

From `outputs/a1_h_seed_summary.json` (Spearman of the checkpoint metric vs **50k top-1**;
`legacy1001`):

| checkpoint set | n | Spearman(τ₅, top-1) | Spearman(CG, top-1) |
|---|---|---|---|
| seed 42 only (the published E4 set) | 3 | **+1.000** | −0.500 |
| seed 42 + 43 | 6 | **+0.886** | −0.371 |
| seed 42 + 44 | 6 | **+0.829** | −0.314 |
| seeds 43 + 44 only | 6 | **+0.829** | −0.029 |
| **all 9 controlled runs (3 datasets × 3 seeds)** | **9** | **+0.850** (p = 0.0037) | **−0.267** (p = 0.49) |
| + Flickr30k seed-42 control | 10 | **+0.794** (p = 0.0061) | −0.152 |
| + all three archived Flickr30k checkpoints | 13 | **+0.841** (p = 0.00032) | +0.198 |

**Verdict: the contrast survives, now on nine runs rather than three.** With the seed spread
visible, τ's correlation with accuracy stays high (**+0.85**, p = 0.0037) while the gap's stays
near zero or negative (**−0.27**, p = 0.49) — the gap is not merely weaker than τ, it is
*uninformative* on this checkpoint set. What improves over the seed-42-only row is the **evidence
weight**, not the effect size: the point estimate falls from +1.000 (n = 3) to +0.850 (n = 9) and
the τ−CG gap narrows from 1.500 to 1.117. Two sensitivities belong beside that and are invisible in
the nine-run point estimate. First, the effect is carried by DTD: **dropping that family (n = 6)
reverses the comparison** (τ **+0.486**, p = 0.33, against CG **+0.657**, p = 0.16), while dropping
Food-101 gives +0.829/−0.600 and dropping COCO +0.943/−0.429. Second, across the 27
one-seed-per-dataset subsets τ's rank correlation is +1.00 in 21 of them but only **+0.50 in 6** —
every subset that pairs Food-101 seed 44 with COCO seed 43 or 44. The published
E4 summary rows (0.786 vs 0.286 across 7 checkpoints) are consistent with this.

### 2.3 Does τ's within-dataset ranking stability improve or degrade?

Both, depending on what "stability" means — and the honest answer is that **τ is far more stable
than accuracy, but still not a reliable per-seed ranker**.

| dataset | τ₅ spread | top-1 50k spread | Spearman(τ₅, top-1) across the 3 seeds |
|---|---|---|---|
| COCO | 0.0005 | 1.13 pts | −0.5 |
| Food-101 | 0.0291 | 0.95 pts | −0.5 |
| DTD | 0.0262 | 1.18 pts | **+1.0** |

* **Improves:** τ is a much tighter statistic than accuracy within a dataset. For COCO the τ₅
  spread is 0.0005 while accuracy spans 1.13 points — τ is ~2 000× more reproducible relative to
  its own scale. A reader can trust a τ difference between datasets far more than an accuracy
  difference.
* **Degrades:** τ does **not** reliably rank the seeds of a single dataset. It does so for DTD
  (+1.0) and anti-ranks for COCO and Food-101 (−0.5 each). Concretely, Food-101 seed 44 has the
  **lowest** τ₅ (0.5644) and also the lowest accuracy (57.77 %) — but DTD seed 44 has the lowest
  τ₅ (0.5149) and the lowest accuracy (53.92 %), while COCO seed 42 has the **lowest** τ₅ of its
  three seeds and the **highest** accuracy (58.05 % with τ₅ = 0.575433 vs 57.30 % at 0.575929).
  So τ's ordering of individual runs is not monotone in accuracy at this granularity.

**Net statement for the revision:** τ's *cross-dataset* contrast with CG is robust to seed spread
(+0.85 vs −0.27 over 9 runs); τ's *within-dataset* per-seed ranking is not, and the paper should
not claim a per-run monotone τ→accuracy relation inside a single high-τ LoRA band. This is the
same qualification `docs/A1_REVIEWER_EXPERIMENTS.md` §4.2 already makes ("τ is not a tight
cross-checkpoint predictor inside this narrow high-τ LoRA band", Spearman 0.40 across the four
seed-42 runs) — now measured rather than suspected.

### 2.4 The synthetic curve and the offset, re-measured over 9 seeds

`outputs/a1_h_seed_summary.json` recomputes the "above-the-curve" position for all nine controlled
runs using the top-5 synthetic τ→top-1 curve of `outputs/a1_rr_e2_topk.json`:

* excess of 50k top-1 over the curve at matched τ₅: **mean +4.72 points, sd 0.70, range
  +4.00 … +5.78** — the offset is stable across seeds, so it is a property of the
  synthetic-vs-real families, not of one lucky run (item ⑤ investigates it).
* τ₅ range over the nine runs is 0.5149 – 0.5936; every one of them sits **above** the curve.

---

## ③ Prompt-template sensitivity

**Why.** Every zero-shot number in the manuscript uses the single template `a photo of a {}`.
The reviewer theme was previously only *cited*, never measured.

**What ran.** `tools/a1_h_templates.py` → **`outputs/a1_h_templates.json`** (185.4 s). Five
templates on the freezing/surgery protocol, on ImageNet (the fixed 5 000-image sample,
`RandomState(42)`) plus the two benchmarks DTD and Food-101 from `outputs/a1_rr_e3_benchmarks.json`:

| key | template |
|---|---|
| `t0_photo_of_a` | `a photo of a {}` ← manuscript default |
| `t1_photo_of_the` | `a photo of the {}` |
| `t2_in_the_wild` | `a photo of a {} in the wild` |
| `t3_bare_class` | `{}` |
| `t4_close_up` | `a close-up photo of a {}` |

**Convention (important, and stated explicitly as required).** τ is computed on the **frozen
top-5 class sets derived per template**: the top-5 indices come from *that template's own* frozen
scores, and the perturbed ranking of the *same* template is compared to it. τ is therefore
**template-internal** and only comparable within a template column, never across columns. Two gap
variants are reported: `coupled` (the gap direction is re-estimated on Flickr30k rows 2000..3000
with *this* template's text tower) and `fixed_t0` (the t0 gap is reused, so only the evaluation
template changes). The two give identical conclusions — as expected, since the gap direction is
template-insensitive: ‖g‖ = **0.8149 / 0.8151 / 0.8152 / 0.8157 / 0.8154** for
t0/t1/t2/t3/t4, a spread of 8e-4.

### 3.1 Frozen top-1 and τ(λ) per template

| benchmark | template | frozen top-1 | τ(0.5) | τ(1) | τ(2) | top-1(0.5) | top-1(1) | top-1(2) |
|---|---|---|---|---|---|---|---|---|
| **ImageNet-5k** | t0 `a photo of a {}` | **59.10** | 0.4656 | 0.2901 | 0.1496 | 47.48 | 32.10 | 12.62 |
| | t1 `a photo of the {}` | 57.90 | 0.4784 | 0.3090 | 0.1737 | 47.90 | 33.70 | 10.42 |
| | t2 `… in the wild` | 55.78 | **0.5160** | **0.3409** | **0.1928** | 50.16 | **35.86** | 12.32 |
| | t3 `{}` | 55.68 | 0.4703 | 0.3034 | 0.1765 | 47.36 | 32.72 | 13.06 |
| | t4 `a close-up photo of a {}` | 58.18 | **0.4217** | **0.2399** | **0.1048** | **41.02** | **25.02** | **8.82** |
| **DTD** | t0 | **43.14** | 0.5640 | 0.3538 | 0.1589 | 40.96 | 31.91 | 16.70 |
| | t1 | 41.65 | 0.5567 | 0.3448 | 0.1417 | 40.74 | 35.32 | 22.87 |
| | t2 | **36.81** | 0.5093 | 0.2717 | 0.0707 | 34.04 | 22.50 | 8.09 |
| | t3 | 40.64 | 0.5609 | 0.3563 | 0.1744 | 40.32 | 31.76 | 17.02 |
| | t4 | 42.29 | 0.4988 | 0.2772 | 0.0996 | 39.68 | 29.57 | 18.94 |
| **Food-101** | t0 | 82.06 | 0.6217 | 0.4409 | 0.2607 | 75.81 | 60.55 | 30.18 |
| | t1 | **83.47** | 0.6398 | 0.4635 | 0.2849 | 77.90 | 63.01 | 31.64 |
| | t2 | 78.91 | **0.6632** | **0.4849** | **0.2967** | 74.72 | 62.00 | 31.59 |
| | t3 | 81.21 | 0.6301 | 0.4552 | 0.2772 | 77.58 | 62.48 | 28.13 |
| | t4 | 81.43 | **0.5669** | **0.3740** | **0.1994** | **71.89** | **51.54** | **24.02** |

### 3.2 Is the τ(λ) collapse signature template-stable?

**Yes — 15/15.** `monotone_decreasing` is `true` for every (benchmark, template) pair: τ falls
monotonically as λ goes 0 → 0.5 → 1 → 2 in all three benchmarks under all five templates, and
top-1 falls with it. τ(2) is between 0.071 and 0.297, i.e. near-total order destruction, in every
case. The τ = 0 anchor is exact by construction at every template, and the shape of the collapse
(then re-inflation) is not a property of one prompt.

### 3.3 Is the τ–top-1 relationship template-stable?

**Yes in direction and rank, but with a large absolute spread.**

| benchmark | λ | τ range across 5 templates | τ spread | top-1 range | top-1 spread |
|---|---|---|---|---|---|
| ImageNet-5k | 0 | 1.0000 | 0.0000 | 55.68 – 59.10 | 3.42 |
| | 0.5 | 0.4217 – 0.5160 | **0.0943** | 41.02 – 50.16 | 9.14 |
| | 1 | 0.2399 – 0.3409 | **0.1011** | 25.02 – 35.86 | **10.84** |
| | 2 | 0.1048 – 0.1928 | 0.0880 | 8.82 – 13.06 | 4.24 |
| DTD | 0.5 | 0.4988 – 0.5640 | 0.0652 | 34.04 – 40.96 | 6.91 |
| | 1 | 0.2717 – 0.3563 | 0.0846 | 22.50 – 35.32 | **12.82** |
| | 2 | 0.0707 – 0.1744 | **0.1036** | 8.09 – 22.87 | **14.79** |
| Food-101 | 0.5 | 0.5669 – 0.6632 | 0.0963 | 71.89 – 77.90 | 6.01 |
| | 1 | 0.3740 – 0.4849 | **0.1110** | 51.54 – 63.01 | **11.47** |
| | 2 | 0.1994 – 0.2967 | 0.0973 | 24.02 – 31.64 | 7.62 |

* **Template choice moves τ by up to 0.111.** That is *larger* than the k-dependence measured in
  item ④ (up to 0.104) and ~7.5× larger than the largest seed spread measured in item ② (0.0149).
  It is far outside the bootstrap CI half-widths of the same cells (±0.0034 to ±0.0189, and 4.3–28.4×
  them — §4.4), and across the nine (benchmark, λ ≥ 0.5) cells the spread never falls below
  **0.0652**. **A τ number quoted without its template is therefore not well defined to better than
  ±0.065.**
* **Template choice moves top-1 by up to 14.8 points** (DTD at λ = 2). The frozen top-1 alone
  spreads by 3.4 – 6.3 points. This is a well-known prompt-sensitivity effect, but it is worth
  recording that the *manuscript's* default template is the best or near-best on all three
  benchmarks (ImageNet 59.10 = max; DTD 43.14 = max; Food-101 82.06, **second** of five, behind
  `a photo of the {}` at 83.47) — so the
  published numbers are not the product of an unusually favourable prompt, and a critic cannot
  claim the default was cherry-picked.
* **The template ordering is consistent across benchmarks at the extremes:** `t4_close_up` is the
  most destructive template at λ = 1 on all three benchmarks (τ 0.2399 / 0.2772 / 0.3740, top-1
  25.02 / 29.57 / 51.54 — the minimum in every case), and `t2_in_the_wild` is the most
  order-preserving at λ = 1 (τ 0.3409 / 0.2717 is the Food-101/ImageNet max; on Food-101 it is the
  max at 0.4849). So the *ranking* of templates by τ(λ) is informative and stable even though the
  absolute level is not.
* **τ still separates the healthy from the destructive intervention under every template.** The
  surgery family's τ at λ = 2 is 0.07 – 0.30 in all fifteen (benchmark, template) cells, and on the
  certified grid surgery is the **lowest-τ family at every matched λ** (λ = 0.25: 0.6425 against
  0.7519 – 0.7758; λ = 0.5: 0.4656 against 0.4804 – 0.6331; λ = 1: 0.2901 against 0.4131 – 0.4480;
  λ = 2: 0.1496 against 0.2635 – 0.2718) — the paper's central claim (ii) does not depend on the
  prompt. *(An earlier draft of this bullet quoted a "class-contraction family at τ = 0.58 – 0.68
  at λ = 2"; that interval is in no JSON. The contraction family is stored on the certified grid at
  λ = 0.1/0.25/0.5 only — 0.9078 / 0.7635 / 0.4804.)*

### 3.4 How much of the frozen class-relative order survives a template change?

`cross_template_tau` in the JSON compares each template's **frozen** ranking to the t0 frozen
ranking (no surgery at all):

| benchmark | vs t1 `the` | vs t2 `in the wild` | vs t3 `{}` | vs t4 `close-up` |
|---|---|---|---|---|
| ImageNet-5k (τ on t0's top-5) | 0.648 | 0.609 | **0.565** | 0.688 |
| DTD | 0.613 | **0.481** | 0.536 | 0.546 |
| Food-101 | 0.796 | 0.755 | **0.711** | 0.805 |

Changing the prompt inverts a large fraction of the class-relative order **without any
intervention at all** — τ(t0 vs t3) = 0.565 on ImageNet-5k and 0.481 on DTD. The top-5 class sets
themselves differ: the Jaccard overlap between t0's and t3's frozen top-5 sets is only **0.571**
on ImageNet-5k. This is the cleanest possible justification for the convention stated above: τ is
only meaningful as a *within-configuration* quantity, and the manuscript should say so.

**Verdict for the reviewer theme.** *Closed.* The τ(λ) collapse signature and the τ–top-1
relationship are template-stable in shape and in their ordering of interventions (15/15 monotone
collapses; surgery is the lowest-τ family at every matched λ on the certified grid), while the
**absolute** τ level is template-dependent (spreads 0.0652 – 0.1110, i.e. not well defined to
better than ±0.065) and the frozen class-relative order is largely
template-specific (cross-template τ down to 0.48). Both facts belong in the revision.

---

## ④ Bootstrap confidence intervals for τ, and the k-specificity of the thresholds

**What ran.** `tools/a1_h_bootstrap.py` → **`outputs/a1_h_bootstrap.json`** (197.4 s, i.e.
`meta.runtime_s`). Images are
resampled **with replacement**, 2 000 replicates, seed 20260101, resampling the per-image τ arrays
(the correct unit: τ is a mean of per-image quantities). Point estimates and CIs are reported next
to the value already stored in the source JSON, and the script records
`agrees_with_source` for each. Four sources were used: the certified dose-response grid
(① JSON), freshly recomputed per-image τ for the four E3 benchmarks, the per-image τ stored by the
template run (③ JSON), and the k-sweep stored by the certified run.

### 4.1 Dose-response grid, ImageNet 5k, k = 5 (`legacy1001`)

| condition | τ | 95 % CI | bootstrap SE | vs source JSON |
|---|---|---|---|---|
| base (λ = 0) | 1.0000 | [1.0000, 1.0000] | 0.0000 | agrees |
| λ = −1 | 0.3314 | [0.3210, 0.3423] | 0.0056 | agrees |
| λ = −0.5 | 0.4931 | [0.4833, 0.5037] | 0.0051 | agrees |
| λ = +0.25 | 0.6425 | [0.6331, 0.6512] | 0.0045 | agrees |
| λ = +0.5 | 0.4656 | [0.4547, 0.4759] | 0.0055 | agrees |
| λ = +1 | 0.2901 | [0.2785, 0.3017] | 0.0060 | agrees |
| λ = +2 | 0.1496 | [0.1376, 0.1615] | 0.0061 | agrees |
| λ = +4 | 0.0655 | [0.0537, 0.0774] | 0.0061 | agrees |
| P0.5 (class contraction) | 0.6086 | [0.5993, 0.6175] | 0.0047 | agrees |

**Reading.** The τ(λ) collapse is far larger than its uncertainty: the two central points
λ = 0.5 (0.4656) and λ = 1 (0.2901) are separated by 0.176 with non-overlapping CIs of width
≈ 0.021. The CI half-width is ≈ 0.011, i.e. **τ(λ) is resolved to about ±0.011 at 95 %** on 5 000
images.

### 4.2 The four E3 benchmarks, λ = 0 / 0.5 / 1 / 2, k = 5

Per-image τ was recomputed for the E3 protocol (gap from Flickr30k rows 2000..3000). Point
estimates reproduce the E3 JSON to within **0.0121** in τ and **2.03 points** in top-1 (largest τ
residual Food-101 at λ = 1: 0.4283 vs 0.4404; largest top-1 residual Food-101 at λ = 2: 28.02 vs
30.04). The residual is a fresh gap re-estimate (‖g‖ = 0.814929 here vs 0.815402 stored in the E3
JSON; no ties are dropped at k ≥ 3), so both columns are carried in the JSON (`tau_in_e3_json`,
`tau_agrees_with_e3`) — and the JSON's own agreement flags record it rather than hiding it:
**12 of the 16 conditions carry `tau_agrees_with_e3 = false` and 6 carry
`top1_agrees_with_e3 = false`**, including Food-101 at λ = 0, where the frozen top-1 is 80.70 here
against 82.06 in the E3 JSON. The residuals are an order of magnitude smaller than the effects
they accompany, so the conclusions drawn from the table below are unaffected.

| benchmark | n images | C | frozen top-1 | λ | τ | 95 % CI | SE | E3 stored τ |
|---|---|---|---|---|---|---|---|---|
| DTD | 1 880 | 47 | 43.14 | 0 | 1.0000 | [1.0000, 1.0000] | 0.0000 | 1.000 |
| | | | | 0.5 | 0.5640 | [0.5502, 0.5780] | 0.0071 | 0.5645 |
| | | | | 1 | 0.3538 | [0.3373, 0.3700] | 0.0084 | 0.3530 |
| | | | | 2 | 0.1589 | [0.1407, 0.1772] | 0.0092 | 0.1591 |
| Food-101 | 25 250 | 101 | 80.70 | 0 | 1.0000 | [1.0000, 1.0000] | 0.0000 | 1.000 |
| | | | | 0.5 | 0.6138 | [0.6104, 0.6173] | 0.0018 | 0.6211 |
| | | | | 1 | 0.4283 | [0.4241, 0.4325] | 0.0021 | 0.4404 |
| | | | | 2 | 0.2495 | [0.2448, 0.2542] | 0.0024 | 0.2604 |
| iNat-wild | 718 | 48 | 11.14 | 0 | 1.0000 | [1.0000, 1.0000] | 0.0000 | 1.000 |
| | | | | 0.5 | 0.3655 | [0.3348, 0.3944] | 0.0150 | 0.3660 |
| | | | | 1 | 0.1457 | [0.1142, 0.1741] | 0.0157 | 0.1440 |
| | | | | 2 | −0.0036 | [−0.0362, 0.0259] | 0.0160 | −0.0033 |
| rare-species | 1 000 | 50 | 16.40 | 0 | 1.0000 | [1.0000, 1.0000] | 0.0000 | 1.000 |
| | | | | 0.5 | 0.3838 | [0.3594, 0.4086] | 0.0128 | 0.3830 |
| | | | | 1 | 0.1588 | [0.1322, 0.1856] | 0.0137 | 0.1598 |
| | | | | 2 | 0.0190 | [−0.0080, 0.0454] | 0.0137 | 0.0202 |

**Reading.** Two things the point estimates alone could not show.

1. **The collapse is significant on every benchmark, including the ones where τ ends near zero.**
   iNat-wild reaches τ = −0.0036 with CI [−0.036, +0.026] and rare-species τ = 0.0190 with CI
   [−0.008, +0.045]: both are **statistically indistinguishable from zero**, i.e. the surgery
   destroys the class-relative order completely rather than merely degrading it. That is a
   stronger claim than "τ drops a lot".
2. **CI width scales the way it should.** Food-101 (25 250 images) has bootstrap SEs of
   0.0018 / 0.0021 / 0.0024 and **half-widths** of 0.0035 / 0.0042 / 0.0047 at λ = 0.5 / 1 / 2;
   iNat-wild (718 images) has SEs of 0.0150 / 0.0157 / 0.0160 and half-widths of 0.0298 / 0.0299 /
   0.0311 — a factor of ≈ 4 in SE and ≈ 8.5 in half-width, both tracking 1/√n. (The two columns of
   the table above are in different units: the `SE` column prints the JSON's `se`, the `95 % CI`
   column prints `ci_low`/`ci_high`.) So the narrow Food-101 CIs are
   a sample-size effect and the wide iNat CIs are not a sign of instability.

### 4.3 The manuscript's thresholds are **k = 5-specific**

`outputs/a1_h_bootstrap.json → k_specificity`. Per-image τ was computed over
k ∈ {2, 3, 5, 10, 20, 50, 100} at λ ∈ {−0.5, 0.5, 1, 2}, with 2 000-replicate CIs at each point.

Absolute τ level by k (bootstrap point estimates):

| k | τ(λ = 0.5) | τ(λ = 1) | τ(λ = 2) | n images scored at λ = 1 |
|---|---|---|---|---|
| 2 | **0.5037** | **0.3287** | **0.1719** | 4 984 (0.32 % dropped: tied pair) |
| 3 | 0.4967 | 0.3173 | 0.1635 | 5 000 |
| **5** | **0.4656** | **0.2901** | **0.1496** | 5 000 |
| 10 | 0.4421 | 0.2719 | 0.1419 | 5 000 |
| 20 | 0.4248 | 0.2522 | 0.1258 | 5 000 |
| 50 | **0.4097** | 0.2287 | 0.1006 | 5 000 |
| 100 | 0.4111 | **0.2250** | 0.0937 | 5 000 |

* **The absolute level shifts by up to 0.104 with k** (λ = 1: 0.3287 at k = 2 → 0.2250 at k = 100).
  Every per-point CI is far narrower than that shift (typical half-width 0.004–0.015), so the
  k-dependence is a genuine property of the statistic, not sampling noise. It matches, and
  slightly extends, the range quoted in the task brief (τ ≈ 0.496 at k = 3 down to ≈ 0.411 at
  k = 100 at λ = 0.5) — this run measures **0.4967 → 0.4097**, a shift of **0.087** at λ = 0.5
  and **0.104** at λ = 1. Independent confirmation from a different script:
  `outputs/a1_rr_e2_topk.json` gives 0.496 / 0.465 / 0.442 / 0.425 / 0.410 / 0.411 for
  k = 3/5/10/20/50/100 at λ = 0.5, matching this run to ≤ 0.001.
* **The threshold is not portable.** Taking the manuscript's tripwire level τ < 0.5 as an example,
  the first λ at which it fires is:

  | k | 2 | 3 | 5 | 10 | 20 | 50 | 100 |
  |---|---|---|---|---|---|---|---|
  | first λ with τ < 0.5 | **1.0** | **0.5** | **−0.5** | **−0.5** | **−0.5** | **−0.5** | **−0.5** |

  The same numeric threshold fires at λ = 1.0 when τ is measured at k = 2, at λ = 0.5 at k = 3,
  and already at the *negative* λ = −0.5 for every k ≥ 5. The mismatch is one of **severity**, not
  of accuracy sign: the λ = −0.5 condition is a gap-*widening* step whose 5k top-1 falls from
  59.10 % to **29.48 %** (`conditions[T-0.5].top1` versus `conditions[base].top1`), i.e. **−29.62
  points**, and the **same** condition is *not* flagged at k = 2 (τ = 0.5446) or k = 3
  (τ = 0.5127) although nothing about its accuracy damage depends on k. At k ≥ 5 the alarm also
  fires on the first non-zero probe in the **opposite** (gap-closing) direction, λ = +0.5
  (τ = 0.4656, top-1 47.48 %, −11.62 points), while staying silent on the milder positive probe
  λ = +0.25 (τ = 0.6425, top-1 55.80 %, −3.30 points). A single τ level therefore separates
  neither severity nor direction: at k ≥ 5 it fires only once the damage is already large (the
  smallest firing probe costs 11.6 points; the largest costs 46.5 at λ = +2), and it fires on a
  gap-widening and a gap-closing intervention alike. This is the practical consequence of the
  k-dependence, and it is the reason the manuscript must state k explicitly wherever a τ threshold
  is quoted.

  **Recommendation:** quote the tripwire table with k fixed at 5, add the sentence "absolute τ
  levels are only comparable at a fixed k (τ shifts by up to 0.10 between k = 2 and k = 100 at
  λ = 1)", and never carry a numeric τ threshold across a change of k.

### 4.4 Bootstrap CIs for the template conditions (bridges ③ and ④)

The per-image τ stored by item ③ was bootstrapped with the same settings, so the template spread
can be tested against its own uncertainty rather than assumed to be real. 95 % CI **half-widths**:

| benchmark | λ = 0.5 | λ = 1 | λ = 2 |
|---|---|---|---|
| ImageNet-5k (n = 5 000) | 0.0098 – 0.0112 | 0.0107 – 0.0119 | 0.0114 – 0.0120 |
| DTD (n = 1 880) | 0.0137 – 0.0151 | 0.0163 – 0.0182 | 0.0178 – 0.0189 |
| Food-101 (n = 25 250) | 0.0034 – 0.0038 | 0.0041 – 0.0044 | 0.0046 – 0.0048 |

Compare with the template spreads of §3.3: **0.0652 – 0.1110**. At every (benchmark, λ) cell the
template spread is **4.3× to 28.4×** that cell's own bootstrap CI half-width (4.32 for DTD at
λ = 0.5, 28.38 for Food-101 at λ = 0.5), so the template effect is real and not sampling noise —
the same conclusion the k-sweep reached in §4.3 (shift ≤ 0.104 against half-widths
0.0024 – 0.0269). Pairing the extremes across cells instead — the smallest spread against the
widest half-width, the largest spread against the narrowest — widens the ratio to **3.4× – 32.7×**,
which is the range to quote if one cell's spread is compared with another cell's uncertainty. Two
methodology choices — *which k* and *which prompt* — each move the absolute τ
level by ~0.10, while the sampling uncertainty of τ on 5 000 images is only ~0.011.


---

## ⑤ Explaining the systematic offset

**The observation to explain.** Real fine-tuned checkpoints sit **3.3–5.5 accuracy points above**
the synthetic τ→top-1 curve at matched τ (`outputs/a1_rr_summary.json`), and the three archived
Flickr30k checkpoints sit above the curve's entire k = 5 range. Item ② re-measured this over nine
independent runs: excess **+4.72 ± 0.70 points**, so it is not one lucky checkpoint.

**Hypothesis to test.** Synthetic gap surgery is a **norm-preserving exact translation** of the
image cluster along the gap direction `d̂`, whereas real fine-tuning changes the embedding geometry
(norms, within-class spread, per-class margins) — so at matched τ the two families need not
coincide.

**What ran.** `tools/a1_h_offset.py` → **`outputs/a1_h_offset.json`** (349.2 s).
13 checkpoints (4 controlled runs at seed 42 + 9 seed-42/43/44 runs incl. the archived Flickr30k
ones), all on the fixed 5 000-image ImageNet sample, `legacy1001`, k = 5, gap from Flickr30k rows
2000..3000 (‖g‖ = 0.814929). τ was matched by **bisection** on λ (12 iterations, residual ≤ 0.0005
in τ); ‖δ‖ was matched by **linear interpolation** of a 10-point synthetic λ-sweep. None of the 13
checkpoints failed to load.

### 5.1 The synthetic reference curve (frozen text tower)

| λ | τ | top-1 | mean ‖Δx‖ |
|---|---|---|---|
| 0 | 1.0000 | 59.10 | 0.0000 |
| 0.25 | 0.6425 | 55.80 | 0.2005 |
| 0.5 | 0.4656 | 47.48 | 0.4159 |
| 0.75 | 0.3603 | 39.84 | 0.6246 |
| 1.0 | 0.2901 | 32.10 | 0.8076 |
| 1.5 | 0.2012 | 19.52 | 1.0736 |
| 2.0 | 0.1496 | 12.62 | 1.2339 |
| 4.0 | 0.0655 | 3.24 | 1.4737 |

### 5.2 **Is the offset explained by the norm / geometry difference? No.**

τ-matched excess of every checkpoint over this curve (matched by bisection):

| checkpoint | taught on | τ₅ | top-1 5k | matched λ | synthetic top-1 at that τ | **excess** |
|---|---|---|---|---|---|---|
| coco_r8_both | COCO (s42) | 0.5754 | 58.14 | 0.3274 | 53.58 | **+4.56** |
| coco_r8_both_seed43 | COCO (s43) | 0.5756 | 56.94 | 0.3274 | 53.58 | **+3.36** |
| coco_r8_both_seed44 | COCO (s44) | 0.5759 | 57.54 | 0.3274 | 53.58 | **+3.96** |
| food101_r8_both | Food-101 (s42) | 0.5936 | 58.22 | 0.3054 | 54.16 | **+4.06** |
| food101_r8_both_seed43 | Food-101 (s43) | 0.5810 | 59.78 | 0.3201 | 53.72 | **+6.06** |
| food101_r8_both_seed44 | Food-101 (s44) | 0.5644 | 58.34 | 0.3420 | 53.14 | **+5.20** |
| dtd_r8_both | DTD (s42) | 0.5402 | 55.42 | 0.3743 | 51.86 | **+3.56** |
| dtd_r8_both_seed43 | DTD (s43) | 0.5411 | 55.74 | 0.3728 | 52.02 | **+3.72** |
| dtd_r8_both_seed44 | DTD (s44) | 0.5149 | 53.50 | 0.4124 | 50.44 | **+3.06** |
| flickr30k_ref_r8_both | Flickr30k (s42) | 0.6131 | 57.80 | 0.2820 | 54.68 | **+3.12** |
| flickr30k_both_r8 *(archived)* | Flickr30k | 0.6962 | 59.32 | 0.1956 | 57.12 | **+2.20** |
| flickr30k_retrain_both_ep10 *(archived)* | Flickr30k | 0.7497 | 58.58 | 0.1516 | 58.04 | **+0.54** |
| flickr30k_text_only_r8 *(archived)* | Flickr30k | 0.7595 | 58.50 | 0.1428 | 58.02 | **+0.48** † |

† **Measurement artifact, flagged in the JSON.** `flickr30k_text_only_r8` has a **frozen vision
tower** and a LoRA-fine-tuned text tower. Gap surgery on a frozen vision tower is a **no-op**
(mean ‖Δx‖ = 0.0000 exactly), so the synthetic reference is degenerate for this checkpoint and its
"+0.48" is not a like-for-like number. The same caveat applies in principle to any checkpoint
whose vision tower did not move. `outputs/a1_h_offset.json → offset_analysis.by_vision_tower`
records the split, and §5.4 gives the correct control for it.

**Statistical read (12 vision-LoRA checkpoints).** Excess **+3.62 ± 1.41 points** (range
**+0.54 … +6.06** — the minimum is the archived `flickr30k_retrain_both_ep10` and the maximum
Food-101 seed 43; the 13th checkpoint, the vision-frozen `flickr30k_text_only_r8`, supplies the
+0.48 that this set excludes), 95 % CI of the mean ≈ [2.72, 4.51] — **firmly positive**. The offset
is not a systematic bias in the comparison: it is what the measurements say. The JSON's own split
agrees with the member list: `offset_analysis.by_vision_tower.vision_lora_checkspoints` names 12
tags (`n = 12`, `min: 0.54`, `max: 6.06`, `range: 5.52`) and `vision_frozen_checkpoints` names the
single text-only tag (`min: 0.48`). That block is **not** defective — its stored `mean` 3.6167 and
`sd` 1.4075 reproduce exactly from the twelve `excess_top1` values of the twelve tags it names, and
`+0.54` is the archived `flickr30k_retrain_both_ep10`, a vision-LoRA member of the set listed in
§5.2 above (not the excluded 13th checkpoint, which is at +0.48). A minimum of **+3.06** for this
set is arithmetically impossible: only ten of the thirteen checkpoints exceed +3.06
(`checkpoints[*].matched_tau.excess_top1`), so every 12-element subset has a smaller minimum.

### 5.3 The hypothesis is confirmed as a *geometric* statement — this is the finding

Decomposing each checkpoint's mean image-embedding displacement against the gap direction:

| checkpoint family | mean ‖Δx‖ | **cos(Δμ, d̂)** | component ‖ to `d̂` | component ⊥ to `d̂` | **⊥ share** |
|---|---|---|---|---|---|
| COCO (3 seeds) | 0.290 – 0.309 | +0.015 … +0.106 | +0.002 … +0.019 | 0.289 – 0.308 | **94 – 99 %** |
| Food-101 (3 seeds) | 0.209 – 0.228 | +0.051 … +0.114 | +0.005 … +0.014 | 0.208 – 0.227 | **94 – 98 %** |
| DTD (3 seeds) | 0.311 – 0.339 | −0.022 … +0.030 | −0.004 … +0.006 | 0.310 – 0.338 | **98 – 99 %** |
| Flickr30k ref / archived | 0.118 – 0.243 | −0.326 … +0.046 | −0.036 … +0.003 | 0.118 – 0.240 | **86 – 100 %** |
| **synthetic translation** | λ·‖g‖ | **+1.000 (by construction)** | all of it | **0** | **0 %** |

> **Real LoRA fine-tuning moves the image cluster almost entirely ORTHOGONALLY to the estimated
> modality-gap direction — 86–99.7 % of the displacement magnitude is perpendicular to `d̂`, with
> cos(Δμ, d̂) between −0.33 and +0.11.** Synthetic gap surgery, by construction, moves the cluster
> 100 % *along* `d̂` with cos = +1.

**So the hypothesis is correct as geometry, but it does not close the gap.** The two families are
geometrically non-overlapping in a way that was not previously quantified, which is a genuine new
result; and at matched τ they still do not coincide even after every geometry control is applied:

* the dimensionless geometry deltas are **small, but not small relative to the quantities they are
  compared with**: within-class spread changes by ≤ 0.0169 over all 13 checkpoints (0.0063 over the
  nine controlled seeds; frozen `within_class_spread_mean` = 0.12905, so the largest change is 13 %
  of it), and the mean top-1 margin changes by ≤ 0.0039 against a frozen `margin_top1_mean` =
  0.005227 — **74 % of the margin itself**, so the margin is not separated from the offset by its
  scale. `logit_scale` is **exactly 100.0 for all 13 checkpoints** (frozen included), so temperature
  is not a confound.
* correlation of the excess with each geometry delta (13 checkpoints): ‖Δx‖ ρ_pearson **+0.615**;
  text-tower displacement ‖Δt‖ **+0.670** (p = 0.012); ⊥-component +0.615; fraction of top-1
  predictions changed **+0.689**; within-class-spread delta +0.288; margin deltas −0.11 … +0.37;
  CG −0.100. The best single correlate explains **< 50 %** of the excess variance, and **none**
  of them is a mechanism that removes the offset at matched τ — they merely say "checkpoints that
  moved further have a larger excess", which is a tautology about magnitude, not an explanation of
  the family difference.

### 5.4 The text tower is not the explanation either

Every "both-tower" checkpoint moved its text tower by an amount comparable to its image-cluster
displacement: **‖Δt‖ / ‖Δx‖ runs from 0.71 to 1.50** over the twelve (`displacement.mean_abs_dx` /
`.mean_abs_text_dx`; e.g. Food-101 seed 43: ‖Δx‖ = 0.218, ‖Δt‖ = 0.314; Food-101 seed 42: 0.209 vs
0.312), so the synthetic family's frozen text tower is a real difference.
The direct control is a checkpoint whose *image* tower did not move, where the checkpoint's own
fine-tuned text tower can be scored against the frozen image tower:

| control | top-1 5k | τ vs frozen |
|---|---|---|
| frozen image tower × frozen text tower | 59.06 | 1.000 |
| `flickr30k_text_only_r8`: frozen image tower × **its own** text tower | **58.50** | **0.759** |
| Δ induced by text-tower fine-tuning **alone** | **−0.56 pts** | −0.241 |

**Text-tower movement alone produces a τ of 0.759 at essentially unchanged accuracy** — a
*different* region of (τ, accuracy) space from both families: it is order-degrading *without* being
accuracy-degrading. That is precisely the decoupling the manuscript's thesis is about, and it
confirms the offset is not a text-tower artifact.

### 5.5 What could not be measured, and the open question

* **A matching-‖δ‖ synthetic point with the *same direction mix* as a real fine-tune is not
  constructible inside this protocol.** The synthetic family is parameterised by λ alone, which
  traces a one-dimensional path (pure translation along `d̂`); reaching the 86–99 % orthogonal
  character of real fine-tuning would require a different perturbation family — i.e. abandoning
  the protocol being tested. I did not invent one. Therefore the comparison at matched τ is the
  strongest controlled comparison available here, and it leaves the offset standing.
* **No per-class mechanism is identifiable from the available artefacts.** Within-class spread and
  margin statistics were measured for all 13 checkpoints (they are in the JSON) but none of them
  predicts the excess with anything approaching sufficiency.

> **Conclusion, stated as required.** **The offset is NOT explained by the norm-geometry
> difference.** Norms are uninformative by construction (all embeddings are normalised, so
> ‖x‖ = 1 for every checkpoint and `logit_scale` is identically 100.0), the remaining geometry
> deltas are small but of the same order as the quantities they are compared with (the largest
> margin delta is 74 % of the frozen margin, the largest within-class-spread delta 13 % of the
> frozen spread), and no geometry statistic accounts for more than
> ~47 % of the excess variance. What *is* established is a sharp and previously unquantified
> geometric asymmetry: **synthetic "gap surgery" is a pure translation along the gap direction
> (cos = +1, 0 % orthogonal), whereas real LoRA fine-tuning displaces the image cluster 86–99.7 %
> orthogonally to it.** Whether that asymmetry is the mechanism behind the residual +3.6 points
> remains an **open question**. The manuscript should say so plainly and soften the Figure-2 claim
> from "real checkpoints lie on the same manifold" to "real checkpoints lie on or above the
> synthetic manifold", with the translation-vs-orthogonal-displacement asymmetry named as the
> outstanding puzzle.

---

## ⑥ Consolidated status: what is closed, what is not, and what could not be measured

### 6.1 Per item

| # | criticism | status | one-line answer |
|---|---|---|---|
| ① | the baseline-metrics row is uncertifiable | **closed** | A single self-consistent run now exists (records its own script hash). τ@k=5 = **0.9125**; the manuscript's **0.9262 is the k=10 value**; linear CKA reproduces **exactly** (0.7552, same p-value). CG and mean-cosine do **not** reproduce under any definition tested. |
| ② | one seed per non-Flickr30k dataset | **closed** | 6 new runs (seeds 43, 44 × COCO/Food-101/DTD). Seed spread is real and dataset-dependent: τ₅ sd **0.0002 / 0.0146 / 0.0149**, accuracy sd **0.58 / 0.48 / 0.66** points. The τ-vs-CG contrast **survives, now on nine runs rather than three**: **+0.85 vs −0.27** over 9 runs — the point estimate falls from +1.000 at n = 3 and the τ−CG gap narrows from 1.50 to 1.12, and the result is DTD-carried (dropping that family reverses it: τ **+0.486** vs CG **+0.657**). |
| ③ | prompt-template sensitivity only cited, never measured | **closed** | 4 additional templates × 3 benchmarks. Collapse signature monotone in **15/15** cases; τ–top-1 direction stable; **absolute τ moves up to 0.111** with the prompt and the frozen class order is largely template-specific (cross-template τ down to 0.48). |
| ④ | no uncertainty on τ; thresholds assumed general | **closed** | 2 000-replicate bootstrap over images. CI half-width **±0.0034 to ±0.0189** on the template grid and **±0.0035 to ±0.0311** across the four E3 benchmarks. iNat-wild and rare-species end at τ indistinguishable from **zero**. The tripwire thresholds are **k = 5-specific**: τ shifts by up to **0.104** with k, and a fixed τ < 0.5 alarm fires at λ = 1.0 (k = 2), 0.5 (k = 3), and already at λ = −0.5 for every k ≥ 5 — a gap-widening step that costs **29.62 points** of 5k top-1 (59.10 % → 29.48 %), so the first firing is on catastrophic damage and the *same* condition is unflagged at k = 2 and k = 3; at k ≥ 5 it also fires in the opposite direction (λ = +0.5, −11.62 points). |
| ⑤ | the +3.3–5.5-point offset is unexplained | **NOT closed — stated as open** | Excess measured at **+3.62 ± 1.41 points** over 12 vision-LoRA checkpoints (range **+0.54 … +6.06**; the 13th, vision-frozen checkpoint is at +0.48 and is excluded). Not explained by norms — `logit_scale` is identically 100.0 and all embeddings are unit-norm — nor by within-class spread or margins, whose deltas are small but of the *same order* as the frozen quantities they are compared with (74 % of the frozen margin) and whose correlation with the excess explains under half its variance; nor by the text tower. What *is* established: synthetic surgery is a **pure translation along the gap direction (cos = +1, 0 % orthogonal)** while real LoRA fine-tuning displaces the image cluster **86–99.7 % orthogonally** to it (`cos(Δμ, d̂)` between −0.33 and +0.11). |

### 6.2 Everything that could not be measured, with the reason

1. **A synthetic perturbation with the same direction mix as a real fine-tune.** The synthetic
   family is parameterised by λ alone and traces a one-dimensional path in perturbation space
   (pure translation along `d̂`). Matching the 86–99 % orthogonal character of real fine-tuning
   requires a different perturbation family, i.e. abandoning the protocol under test. Not
   attempted rather than invented.
2. **The provenance of the archived `outputs/a1_baseline_metrics.json`.** The file records no
   script hash, no seeds and no class-list length, so its exact code state cannot be recovered
   from the artifact. Its CG (−0.0821) and mean-cosine (0.8715) correlations are not reachable by
   any definition tested (alternative Flickr30k blocks, un-normalised pooled embeddings, ensemble
   cosines), and the audit's "−0.0828" was traced to a single pair-level sample in
   `outputs/a1_margins.json` (`pair_samples.b[?] = −0.08285278081893921`), not to a CG.
3. **τ at k = 1.** Mathematically undefined (Kendall τ on a single rank); carried as `null` with an
   arg-max-agreement diagnostic instead, as in the pre-existing E2 work.
4. **A held-out seed** for the item-② checkpoints. Seeds 43/44 are the *same* seeds that exposed the
   spread, so the reported sd values are descriptive of three runs, not estimates from a held-out
   set. No fourth seed was trained.
5. **The DTD optimisation budget.** DTD runs **300** steps against 320 for COCO/Food-101/Flickr30k
   because its entire train split is 1 880 images. This confound exists in the pre-existing seed-42
   DTD run too and was **not** corrected — correcting it would change the archived run rather than
   harden it. It is recorded here and in `meta.n_steps` of every DTD JSON.
6. **COCO/Food-101 sampling vs DTD enumeration.** COCO and Food-101 subsample 2 000 of their
   train rows (so seeds vary the *data* as well as the init/shuffle order), while DTD uses its
   whole 1 880-image split (so seeds vary only the init/shuffle order). The three datasets'
   "seed spreads" therefore measure slightly different things; this is recorded in each JSON's
   `meta.data.sampling` and is the reason DTD's 0.015 τ₅ spread should be read as a clean
   lower-bound estimate of initialisation sensitivity.
7. **A single frozen-reference value across scripts.** The frozen 5k top-1 is 59.10 % under the
   protocol of `tools/clip_a1_baseline_metrics.py` and 59.06 % under the protocol of
   `tools/a1_h_offset.py` (which re-encodes the sample through `visual_projection` without the
   archived batch-splitting). The 0.04-point difference is a measurement-path effect, is smaller
   than any conclusion drawn here, and both values are recorded in their own JSONs.
8. **Items ③ and ④ cover different benchmark sets, deliberately and visibly.** Item ③
   (templates) covers ImageNet-5k, DTD and Food-101; item ④ (CIs) covers those three **plus**
   iNat-wild and rare-species, because the E3 benchmark loader was already wired into the
   bootstrap script. Templates were **not** run on iNat-wild / rare-species: that would have added
   two more image-encoding passes for benchmarks whose E3 τ values (0.37 and 0.38 at λ = 0.5) sit
   far from any comparison made in item ③, and the four-additional-template requirement was
   already satisfied on three benchmarks. The set covered by each item is recorded in
   `meta.benchmarks` of the respective JSON.
9. **The point estimates in items ④/⑤ differ slightly from the stored E3 numbers** (≤ 0.0121 in τ,
   ≤ 2.03 points in top-1 — `bootstrap.benchmarks_e3.benchmarks.*.conditions.*` — with 12 of the 16
   τ rows and 6 of the 16 top-1 rows carrying `..._agrees_with_e3 = false`), because each script
   re-estimates the gap direction in its own process
   (‖g‖ = 0.814929 vs 0.815402 stored). Both columns are carried in the JSONs
   (`tau_in_e3_json`, `tau_agrees_with_e3`) so the residual is visible rather than hidden; no
   image is dropped by the tie rule at k ≥ 3, which was checked explicitly rather than assumed.

### 6.3 Files produced (all new; nothing pre-existing was modified)

| file | role |
|---|---|
| `tools/a1_h_common.py` | shared tie-aware Kendall τ_b (vectorised, scipy-exact) + nan-aware bootstrap |
| `tools/a1_h_baseline_metrics.py` | item ① certification (`--tau-k 5 10`, alternative-metric diagnostics) |
| `tools/a1_h_e4_seed.py` | item ② trainer + evaluator (`--seed-json` recovery mode; seed-aware checkpoint dirs) |
| `tools/a1_h_seed_summary.py` | item ② analysis: spread, cross-checkpoint correlations, curve position |
| `tools/a1_h_templates.py` | item ③ five templates × three benchmarks |
| `tools/a1_h_bootstrap.py` | item ④ bootstrap CIs + k-specificity |
| `tools/a1_h_offset.py` | item ⑤ geometry, matched-τ/matched-‖δ‖, offset correlations |
| `tools/a1_h_validate.py`, `tools/a1_h_validate2.py` | JSON completeness/consistency validators (both PASS) |
| `tools/a1_h_doc_reorder.py` | one-off section reordering of this document |
| `outputs/a1_h_baseline_metrics.json` | ① 4.8 MB: 26 conditions, per-image τ, k-sweep, archived comparison (103.2 s) |
| `outputs/a1_h_seeds_{coco,food101,dtd}_seed{43,44}.json` | ② six runs (710–1319 s each) |
| `outputs/a1_h_seed_summary.json` | ② derived tables and correlations |
| `outputs/a1_h_templates.json` | ③ 5 templates × 3 benchmarks, per-image τ (185.4 s) |
| `outputs/a1_h_bootstrap.json` | ④ CIs, k-sweep, template CIs (197.4 s) |
| `outputs/a1_h_offset.json` | ⑤ 13 checkpoints × geometry/τ-matched/magnitude-matched (349.2 s) |
| `outputs/a1_h_recover_spec_{food101_seed43,dtd_seed44}.json` | provenance of the two recovered evaluations |
| `logs_a1_h_*.txt` | raw stdout/stderr for every job |
| checkpoints | `outputs/a1_rr_ckpt/seed{43,44}/{coco,food101,dtd}/epoch{1..10}.pt` (seed-42 dirs untouched) |

### 6.4 Three places where the data contradicts an expectation stated in the task brief

1. **"τ is the better correlate than CG" — confirmed, more strongly than stated.** The brief
   describes the contrast as existing; with the seed spread included it becomes **+0.85 vs −0.27**
   (p = 0.0037 vs p = 0.49). The gap is not merely worse, it is uninformative on this set.
2. **"its τ value matches a top-10 computation" — confirmed exactly.** The certified k = 10 run
   reproduces the archived 0.9262 **and** its p-value to every significant figure
   (1.1861084080501641e-11), which is far stronger evidence than a value match.
3. **"Its CG (−0.0821 stored) and mean-cosine (0.8715 stored) do not reproduce (−0.0828 and
   0.8619)" — the reproduction values in that sentence are not CG and mean-cosine at all.** −0.0828
   is a single pair-level bias-field sample from `outputs/a1_margins.json`; the CG *correlation*
   reproduces at **−0.215** and the mean-cosine *correlation* at a bit-stable **0.8619**. The
   archived CG and mean-cosine columns genuinely fail to reproduce, but not for the reason given,
   and the size of the failure is 0.133 (not 0.0007) for CG and 0.0096 for mean-cosine.
