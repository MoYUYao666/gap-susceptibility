# A1 — Reviewer-mandated experiments (E2 / E3 / E4)

Revision experiments for Pattern Recognition Letters submission **PRLETTERS-D-26-01941**
("The Modality Gap Is Not a Universal Health Metric: Order Preservation Governs Zero-Shot
Robustness"), addressing reviewer points **R2.2 (top-k ablation)**, **R2.3 (more zero-shot /
fine-grained benchmarks)** and **R1.6 (checkpoints fine-tuned on data other than Flickr30k)**.

Everything below was produced by the scripts listed in §5 in this session. **No number in this
document is hand-computed or extrapolated**: each one is read from an `outputs/a1_rr_*.json`
produced by a run recorded here, and every JSON carries a `meta` block with the script name, the
ImageNet shard signature (`shard_sig = d13718e47e9e41c2` for all runs), the class-list length, the
random seeds and the run time. Nothing under `paper_a1/` was modified, and no pre-existing result
JSON was overwritten.

Environment: CLIP ViT-B/32 (`openai/clip-vit-base-patch32`, `local_files_only`), PyTorch 2.9.1+cu130,
single RTX 4060 Laptop (8 GB), all GPU jobs run strictly serially. Data: `data/imagenet_hf/*.parquet`
(14 shards, 50 000 images, 1001 label names = 1000 real ImageNet-1K classes + a trailing
placeholder `none`), `flickr30k/`, `data/dtd`, `data/food-101`, `data/inat_wild`,
`data/rare-species`, `coco/`.

---

## 1. Shared protocol (kept byte-compatible with the archived A1 scripts)

| element | value |
|---|---|
| surgery | `x̃ = norm(x + λ‖g‖d̂)`, `λ ∈ {-2,-1,-0.5,0,0.25,0.5,1,2,4}` |
| gap direction `g` | `μ_T − μ_I` on Flickr30k rows 2000..3000 (A1 convention); `‖g‖ = 0.8154` |
| τ | mean Kendall τ_b over the **frozen** top-k class sets, frozen vs perturbed ranking (same estimator as `tools/clip_a1_probe2.py`; `tools/clip_a1_tau_trajectory.py` for checkpoints) |
| τ sample | fixed 5 000-image ImageNet sample, `RandomState(42)` |
| 26-condition grid | exactly the grid of `tools/clip_a1_baseline_metrics.py`, same `RandomState(7)` perturbation stream and same condition order |
| class lists | both conventions reported: `legacy1001` (published τ tables) and `clean1000` (placeholder dropped, `train_class_aligned.imagenet_class_names()`) |
| environment check | frozen `‖g‖ = 0.8147–0.8157`, frozen 5 k top-1 = **59.1 %** — identical to `outputs/a1_tau_trajectory.json` ("frozen": 0.815 / 59.1) |

τ is recomputed with a vectorised tie-aware Kendall τ_b that was **cross-checked against the
archived scipy loop** — agreement 1e-8 (`estimator_crosscheck_vs_archived_scipy` in
`outputs/a1_rr_e2_topk.json`). The cross-check mattered: a naive no-tie formula drifts by up to
0.004 because 1.4 % (k=3) to 65 % (k=100) of images have a tied pair in the float32 perturbed
score vector.

---

## 2. E2 — top-k ablation (R2.2)

**Question.** Is the τ–accuracy relation and the τ(λ) curve an artefact of k = 5, or is it stable
in k?

**What ran.** `tools/a1_rr_e2_topk.py` → **`outputs/a1_rr_e2_topk.json`** (119 s). For
k ∈ {1,3,5,10,20,50,100}: measured τ under the full surgery grid, measured τ under the 26-condition
grid, Spearman(τ, top-1) over that grid, the stability of the τ(λ) curve against k = 5, and the
exact bias-field predictor τ_pred(λ) generalised from 10 pairs (k = 5) to C(k,2) pairs.

### 2.1 Headline table (legacy1001; identical conclusion under clean1000, §2.3)

| k | τ(λ=0) | τ(0.5) | τ(1) | τ(2) | ρ(τ, top-1), 26 cond. | ρ(τ(λ) curve vs k=5) | exact-predictor MAE |
|---|---|---|---|---|---|---|---|
| 1 | *undefined* | *undefined* | *undefined* | *undefined* | — | — | — |
| 3 | 1.000 | 0.496 | 0.318 | 0.163 | 0.9248 | 1.000 | 0.0018 |
| **5** | 1.000 | **0.465** | **0.290** | **0.150** | **0.9125** | 1.000 | 0.0012 |
| 10 | 1.000 | 0.442 | 0.272 | 0.142 | 0.9262 | 1.000 | 0.0006 |
| 20 | 1.000 | 0.425 | 0.252 | 0.126 | 0.9344 | 1.000 | 0.0004 |
| 50 | 1.000 | 0.410 | 0.229 | 0.101 | 0.9357 | 1.000 | 0.0002 |
| 100 | 1.000 | 0.411 | 0.225 | 0.094 | 0.9303 | 1.000 | 0.0001 |

Supporting values (same JSON): mean |Δτ| vs k = 5 rises monotonically 0.017 (k=3) → 0.032 (k=100);
max |Δτ| = 0.065 (k=100); all Spearman p-values ≤ 8.5e-11; the T-family-only τ–top-1 Spearman is
0.8333 for every k ≥ 3.

### 2.2 Verdict (one line)

> **The headline claim survives:** for every k ∈ {3,…,100} the τ–top-1 coupling stays in
> **0.913–0.936** and the τ(λ) curve is *rank-identical* to the k = 5 curve (Spearman 1.000), so
> top-5 is not an artefact — with the explicit caveat that the **absolute** τ level drifts
> monotonically with k (0.496 → 0.411 at λ = 0.5 from k = 3 to k = 100), so τ values are only
> comparable at a fixed k, and k = 1 is degenerate.

### 2.3 Honesty notes for E2

* **k = 1 is undefined, not a value.** The archived `kendall_topk()` skips images whose frozen
  set has zero variance; with a single rank *every* image is skipped, so τ is reported as `null`
  and a clearly-labelled diagnostic (`top1_agreement_diagnostic`, arg-max preservation) is given
  instead. No τ was invented for k = 1.
* **Absolute scale is k-dependent.** τ is a *rank-overlap* statistic, so larger k retains more
  ranks and yields systematically lower τ under the same surgery (more pairs available to invert).
  The dependence is smooth and saturating (k = 50 and k = 100 differ by ≤ 0.002) but it is real:
  at λ = 0.5, k = 5 sits 0.031 below k = 3 and 0.054 above k = 100.
* **Placeholder class.** With the legacy 1001-name list the unreachable class `none` enters the
  frozen top-k for 0.14 % (k=5) of images and 33 % (k=100). The clean1000 convention gives
  τ(0.5) = 0.496/0.465/0.442/0.425/0.411/0.413 and ρ = 0.9248/0.9125/0.9262/0.9344/0.9323/0.9303
  — i.e. the conclusion does not depend on the placeholder.
* **Published k = 5 value not reproduced — and it turns out to be a k = 10 number.**
  The paper quotes ρ(τ, top-1) = 0.9262 (`outputs/a1_baseline_metrics.json`, 26 conditions,
  k = 5 in the text). My faithful re-run of that protocol at k = 5 gives **0.9125**. A dedicated
  provenance probe (`tools/a1_rr_e2_provenance.py` → `outputs/a1_rr_e2_provenance.json`) then swept
  every (k, grid) combination of my recomputation against the four stored correlations, and the
  stored τ value is reproduced **to machine precision by exactly one combination**:

  | recomputation | r | p | = stored p (1.1861084080501641e-11)? |
  |---|---|---|---|
  | k = 3, 26 conditions | 0.924786 | 1.4677e-11 | no |
  | **k = 5, 26 conditions** | **0.912479** | 8.4785e-11 | no |
  | **k = 10, 26 conditions** | **0.926154** | **1.1861084080501641e-11** | **yes (exact)** |
  | k = 20 | 0.934359 | 3.0126e-12 | no |
  | k = 50 | 0.935726 | 2.3568e-12 | no |
  | k = 100 | 0.930256 | 6.1035e-12 | no |

  The stored 0.9262 is therefore a **top-10** correlation, not top-5, even though
  `tools/clip_a1_baseline_metrics.py` as it stands computes `argsort(...)[:, :5]` (the variable is
  still named `topk5`). **Caveat, stated plainly:** two of the other stored metrics are *not*
  reproduced exactly by my recomputation (CG −0.0828 vs −0.0821, mean cosine 0.8619 vs 0.8715;
  CKA matches exactly, +0.755214 vs +0.755200), so the archived JSON was not produced by a script
  identical to mine except in k, and I cannot certify the cause. What is certain is that the
  manuscript's headline τ-correlation is not the top-5 number: at k = 5 it is 0.9125. **For the
  revision, either quote 0.9125 as the top-5 value or state explicitly that the headline
  correlation uses top-10 — the E2 ablation shows the claim itself is unaffected (0.913–0.936 for
  every k ∈ {3,…,100}).** This is precisely the ambiguity reviewer R2.2 asked to be removed.

* **Exact predictor.** τ_pred is the Lemma-1 inversion count over C(k,2) pairs; MAE against
  measurement is ≤ 0.0018 for every k and *improves* with k (0.0001 at k = 100). The residual is
  float32 tie mass, not model error.

---

## 3. E3 — additional zero-shot / fine-grained benchmarks (R2.3)

**What ran.** `tools/a1_rr_e3_benchmarks.py` → **`outputs/a1_rr_e3_benchmarks.json`** (565 s).
Frozen → gap-surgery → class-contraction protocol on four further benchmarks that are present on
disk, at the same λ grid, with the exact-predictor comparison.

**Two gap variants are reported** because these benchmarks have no captions:
`flickr30k` (primary) applies the *same* `g = μ_T − μ_I` estimated on Flickr30k rows 2000..3000 —
protocol-identical to the ImageNet experiment; `self` uses
`mean(class-name text embeddings) − mean(benchmark image embeddings)`, the class-name protocol of
`tools/clip_ocean_margins.py`. Both variants are in the JSON; the tables below use the primary one.

### 3.1 Benchmarks actually loaded — **4 of 4** (nothing dropped, nothing substituted)

| key | source | images used | classes | notes |
|---|---|---|---|---|
| `dtd` | torchvision DTD `root=data, split=test`, `download=False` | 1 880 | 47 | texture benchmark (fine-grained textures) |
| `food101` | torchvision Food-101 `root=data, split=test`, `download=False` | 25 250 | 101 | **fine-grained** |
| `inat_wild` | `data/inat_wild/` (iNaturalist research-grade wild photos) | 718 | 48 | fine-grained species, 15 imgs/class; 2 dirs skipped for < 8 images (`Acipenser_sturio` 2, `Acropora_acuminata` 0) — the `MIN_PER_CLASS=8` rule of `tools/clip_ocean_inat_wild.py` |
| `rare_species` | `data/rare-species/data/*.parquet` (BioCLIP / IUCN rare-species benchmark, 11 983 examples, 400 species) | 1 000 | 50 | top 50 species by image count, ≤ 20 images/class (30 available each); the full 400-class set was not used — see §3.4 |

No benchmark failed to load. The two `torchvision` datasets were verified to be already extracted
(`data/dtd/dtd/images`, `data/food-101/images` + `meta/`), so `download=False` succeeds offline.

### 3.2 Main result table (`flickr30k` gap variant, `‖g‖ = 0.8154`)

| benchmark | frozen top-1 | top-1 λ=0.5 | λ=1 | λ=2 | τ(0.5) | τ(1) | τ(2) | τ_pred − τ_meas (max) | class-contraction a=0.5 (top-1, τ) |
|---|---|---|---|---|---|---|---|---|---|
| DTD (47 cl.) | 43.14 | 40.90 | 31.91 | 16.70 | 0.5645 | 0.3530 | 0.1591 | < 5e-7 | **58.46**, 0.581 |
| Food-101 (101 cl.) | 82.06 | 75.80 | 60.46 | 30.04 | 0.6211 | 0.4404 | 0.2604 | < 5e-7 | **98.59**, 0.676 |
| iNat-wild (48 cl.) | 11.14 | 9.61 | 8.91 | 7.24 | 0.3660 | 0.1440 | −0.0033 | < 5e-7 | **14.76**, 0.625 |
| rare-species (50 cl.) | 16.40 | 8.30 | 5.70 | 3.10 | 0.3830 | 0.1598 | 0.0202 | < 5e-7 | **21.20**, 0.582 |

Full λ grid (including λ = −2, −1, −0.5, 0.25, 4) plus the `self`-gap variant is in the JSON; the
`self` variant is uniformly **more** destructive (τ(1) = 0.233 / 0.391 / 0.054 / 0.082 for
DTD / Food-101 / iNat / rare-species), i.e. the collapse signature is not an artefact of how the
gap direction is estimated.

### 3.3 Findings

1. **The surgery signature replicates on all four benchmarks.** Gap-direction translation collapses
   class order (τ → 0 or below) and takes top-1 with it, on tasks whose frozen accuracy differs by
   a factor of 7 (11.1 % → 82.1 %) and whose label spaces differ 2× (47 → 101 classes).
2. **τ is monotone in accuracy across the δ-grid on 4/4 benchmarks** (see JSON `surgery` blocks:
   τ and top-1 fall together for λ > 0 and recover together for λ < 0).
3. **The exact predictor is exact.** For the surgery family the per-image normalisation is a
   positive scalar, so the bias-field model predicts the perturbed *ordering* exactly;
   |τ_pred − τ_meas| < 5e-7 on every grid point of all four benchmarks (largest deviation anywhere:
   8e-6, on the Food-101 `self` variant, again float32 ties).
4. **Class contraction replicates and is large.** Contracting each image toward its own class
   centroid by a = 0.5 *improves* top-1 on 4/4 benchmarks (DTD +15.3 pts, Food-101 +16.5 pts,
   iNat +3.6 pts, rare-species +4.8 pts), always with τ far below 1 (0.58–0.68). This is the
   paper's claim (ii) — order-preserving/accuracy-improving re-ranking — reproduced outside
   ImageNet/Flickr30k.
5. **λ = +0.25 is already order-destroying but accuracy-neutral on some benchmarks** (iNat:
   τ 1.000 → 0.599 while top-1 stays 11.14 %), which is the τ-as-early-warning behaviour the paper
   recommends, visible on a fine-grained benchmark.

### 3.4 What could not be done / deviations

* **Nothing was dropped**, but three deliberate choices must be stated plainly:
  * `rare_species` is a **subset** (top 50 of 400 species, ≤ 20 images each, 1 000 images) taken
    from the local parquet mirrors; the full 400-class benchmark was not run. The selection rule is
    recorded in the JSON (`class_selection`).
  * the **gap direction for image-only benchmarks** cannot be estimated from captions; the primary
    variant reuses the Flickr30k estimate (documented above) and the class-name variant is reported
    alongside.
  * prompts are the single template `a photo of a {class}` (`TEMPLATE` in every script, matching
    the archived A1 scripts); no prompt ensembling was applied.
* **Benchmarks on disk but not used, with reasons:** `data/fathomnet8` has only 7 classes — a top-5
  set would span 71 % of the label space, which makes the τ metric meaningless;
  `data/marinelife16k`, `data/NKSID`, `data/second_sonar` are domain-specific sets whose class
  lists/protocols belong to other manuscripts (`tools/clip_ocean_*`, `clip_sonar_*`), not to this
  zero-shot protocol. They were not in the reviewer's candidate list and were not forced in.
* **No network access was needed** for E3 (all data local); `download=True` was never used.

---

## 4. E4 — checkpoints fine-tuned on data other than Flickr30k (R1.6)

**What ran.** `tools/a1_rr_e4_train.py` (`outputs/a1_rr_e4_coco.json`,
`outputs/a1_rr_e4_food101.json`, `outputs/a1_rr_e4_dtd.json`, `outputs/a1_rr_e4_flickr30k_ref.json`)
plus one shared-evaluator pass over the archived Flickr30k checkpoints
(`outputs/a1_rr_e4_eval_archived.json`, 1 046 s).

**Archived configuration, reproduced exactly.** LoRA on **both towers, rank 8, α = 16**, applied by
`src.lora.apply_lora_to_model` (targets `q_proj`, `v_proj`); trainable parameters selected **by
name** (`p.requires_grad and 'lora_' in p.name`), which is what makes it a strict LoRA test —
selecting by `requires_grad()` alone silently updates the un-wrapped MLP/LayerNorm/Embedding
weights (the incident documented in `tools/train_class_aligned.py`). AdamW lr 1e-4, wd 0.01, cosine
schedule, batch 64, 10 epochs, 2 000 train pairs = **320 steps**, CLIP symmetric contrastive loss.
Trainable LoRA parameters: **491 520** — which is exactly the size of the archived
`outputs/imagenet_zs/both_r8/best_checkpoint.pt` (1.91 MB × 4 B ≈ 491 520), confirming the
architecture matches. (Note: that run's `results.json` reports `n_trainable_params: 20969472`,
a different accounting rule; the weight file itself is a 491 520-parameter rank-8 q/v LoRA.)

### 4.1 Checkpoints and results (all measured by **one** evaluator, `legacy1001` convention)

| checkpoint | trained on | pairs (unique imgs) | τ₅ | top-1 5k | top-1 **50k** | CG (Flickr30k val) |
|---|---|---|---|---|---|---|
| `flickr30k_ref_r8_both` | **Flickr30k rows 0..1999** (control, my trainer) | 2 000 (400) | 0.6131 | 57.80 | 57.93 | 0.8374 |
| `coco_r8_both` | **COCO train2014 captions** | 2 000 (1 978) | 0.5754 | 58.14 | 58.05 | 0.7777 |
| `food101_r8_both` | **Food-101 train** (class-name captions) | 2 000 (2 000) | 0.5936 | 58.22 | 58.21 | 0.8205 |
| `dtd_r8_both` | **DTD train** (class-name captions) | 1 880 (1 880) | 0.5402 | 55.42 | 55.00 | 0.8315 |
| `flickr30k_text_only_r8` (archived `outputs/imagenet_zs`) | Flickr30k | 2 000 | 0.7595 | 58.50 | 58.68 | 0.7902 |
| `flickr30k_both_r8` (archived `outputs/imagenet_zs`) | Flickr30k | 2 000 | 0.6962 | 59.32 | **59.66** | 0.8479 |
| `flickr30k_retrain_both_ep10` (archived `outputs/a1_retrain/both`) | Flickr30k | 2 000 | 0.7497 | 58.58 | 58.63 | 0.8476 |
| *frozen reference* | — | — | 1.000 | 59.10 | 59.28 † | 0.8147 |

† frozen 50 k top-1 = 59.28 is taken from the pre-existing `outputs/a1_full_results.json`
(T, λ = 0), which uses the same 1001-class convention; the frozen 5 k value 59.10 was measured in
this session and matches `outputs/a1_tau_trajectory.json` exactly.

**Cross-checkpoint correlations** (`outputs/a1_rr_summary.json`), 7 checkpoints:
Spearman(τ₅, top-1 50k) = **0.786**, Pearson = **0.694**;
Spearman(CG, top-1 50k) = **0.286**, Pearson = **0.021**.
Restricted to the four runs of *this* trainer (one code path, only the data changes):
Spearman(τ₅, top-1 50k) = 0.400, **Pearson = 0.849**;
Spearman(CG, top-1 50k) = **−0.600**, Pearson = −0.376 — i.e. within a controlled data sweep the
gap moves in the *wrong* direction while τ moves with accuracy.

### 4.2 Verdict for R1.6

> **The criticised limitation is removed and the claim is supported, with a qualification.**
> Three checkpoints fine-tuned on data other than Flickr30k (COCO captions, Food-101, DTD) plus a
> same-code Flickr30k control now exist with the archived LoRA configuration; **no** LoRA
> fine-tuning on the new datasets collapses zero-shot accuracy (50 k top-1 spans 55.0–59.7 %
> against a frozen 59.28 %; the only clear loss is DTD, −4.3 pts), and
> τ tracks accuracy far better than the gap does (Spearman 0.79 vs 0.29 across all checkpoints;
> Pearson 0.85 vs −0.38 across the controlled sweep). **But** τ is not a tight *cross-checkpoint*
> predictor inside this narrow high-τ LoRA band (Spearman only 0.40 across the four controlled
> runs, where accuracy differences are ≤ 3 pts), and every real LoRA checkpoint sits **above** the
> synthetic τ→top-1 curve: at the measured τ₅ the synthetic surgery would predict 51.0–54.5 %,
> while the checkpoints achieve 55.4–58.2 % (excess +3.3 to +5.5 pts); the three archived Flickr30k
> checkpoints have τ (0.70–0.76) above the entire synthetic curve at fixed k = 5 (max 0.643 at
> λ = 0.25). That "above-the-curve" behaviour is the same signature as the class-contraction family
> (τ = 0.68 at 98.6 % on Food-101), i.e. accuracy-improving order changes, and it means the
> paper's Figure-2 statement that real checkpoints lie *on the same manifold* as the synthetic
> perturbations should be softened to "on or above".

### 4.3 Provenance validations performed

* The evaluator reproduces the published checkpoint values exactly:
  `outputs/a1_retrain/both/epoch10.pt` → **τ₅ = 0.7497, top-1 5k = 58.58**, identical to the
  epoch-10 row of `outputs/a1_tau_trajectory.json` (0.7497 / 58.58) and to the paper's τ = 0.750 /
  58.6; frozen 5 k top-1 = 59.10 ✓ (paper 59.1).
* All three archived checkpoints were re-evaluated *inside the same process* as the new ones, with
  shared frozen references, so the table above is internally consistent.
* `τ_by_k` is recorded for **every** checkpoint (JSON `image_only.legacy1001.tau_by_k`), and the
  checkpoint ranking is identical at every k — this is the E2 k-stability result applied to E4:

  | checkpoint | τ(k=3) | τ(k=5) | τ(k=10) | τ(k=20) |
  |---|---|---|---|---|
  | flickr30k_ref | 0.6289 | 0.6131 | 0.5881 | 0.5769 |
  | food101 | 0.6247 | 0.5936 | 0.5646 | 0.5471 |
  | coco | 0.6081 | 0.5754 | 0.5463 | 0.5345 |
  | dtd | 0.5684 | 0.5402 | 0.5071 | 0.4861 |
  | flickr30k_text_only_r8 (archived) | 0.7800 | 0.7595 | 0.7391 | 0.7302 |
  | flickr30k_retrain_both_ep10 (archived) | 0.7683 | 0.7497 | 0.7264 | 0.7189 |
  | flickr30k_both_r8 (archived) | 0.7209 | 0.6962 | 0.6739 | 0.6648 |

### 4.4 What could not be done / deviations

* **Archived COCO checkpoint rejected.** `outputs/theory/coco/coco_both_r8/seed42/best_checkpoint.pt`
  exists on disk but its own `results.json` shows 131 290 881 trainable parameters, 790 steps and a
  validation R@1 of 2.9 %, i.e. a different, apparently broken run. It was **not** used as evidence;
  COCO was retrained from scratch instead.
* **No full-fine-tuning seeds were re-run.** R1.6 concerns LoRA checkpoints on other data; the
  three full-FT seed values quoted in the manuscript (τ = −0.083 / 0.122 / 0.122) were left
  untouched and are not re-derived here.
* **Budget matching is by pairs/steps, not by dataset size.** Each new run uses 2 000 train pairs
  (the archived Flickr30k budget) so that only the *data* changes. This means COCO contributes
  ≈ 1 978 unique images (1 caption each) whereas Flickr30k contributes 400 unique images
  (5 captions each), and DTD contributes its entire 1 880-image train split. Unique-image counts
  and sampling rules are recorded per run in the JSONs. Training larger subsets was not attempted.
* **No second seed per dataset.** Each non-Flickr30k dataset was trained once (seed 42); a
  seed-to-seed spread for the new datasets is therefore unknown. This is the main weakness that
  remains in E4.
* **No network was used**; nothing had to be downloaded, so there is no download failure to report.

---

## 5. File inventory (all new; nothing pre-existing was modified)

| file | role |
|---|---|
| `tools/a1_rr_e2_topk.py` | E2 top-k ablation (τ for k ∈ {1…100}, 26-condition grid, exact predictor, estimator cross-check) |
| `tools/a1_rr_e3_benchmarks.py` | E3 four-benchmark frozen/surgery/contraction protocol |
| `tools/a1_rr_e4_train.py` | E4 LoRA trainer + shared evaluator (`--dataset`, `--eval-spec`) |
| `tools/a1_rr_summary.py` | derives every table in this document into one JSON |
| `tools/a1_rr_e2_provenance.py` | sweep of (k, grid) against the stored `a1_baseline_metrics.json` correlations |
| `outputs/a1_rr_e2_topk.json` | E2 results (119 s) |
| `outputs/a1_rr_e2_provenance.json` | provenance probe result (k = 10 reproduces the stored τ exactly) |
| `outputs/a1_rr_e3_benchmarks.json` | E3 results (565 s) |
| `outputs/a1_rr_e4_{coco,food101,dtd,flickr30k_ref}.json` | E4 training + evaluation results (985 / 813 / 819 / 692 s) |
| `outputs/a1_rr_e4_evalspec_archived.json` | input spec for the archived-checkpoint evaluation |
| `outputs/a1_rr_e4_eval_archived.json` | archived Flickr30k checkpoints, re-measured (1 046 s) |
| `outputs/a1_rr_summary.json` | all report tables + the 26- vs 27-condition Spearman probe |
| `outputs/a1_rr_ckpt/{coco,food101,dtd,flickr30k_ref}/epoch{1..10}.pt` | new LoRA checkpoints (1.9 MB each) |
| `logs_a1_rr_*.txt` | raw run logs (stdout + stderr) for every job |

---

## 6. Everything that failed or remains open (consolidated)

1. **The manuscript's headline τ-correlation is not a top-5 number.** The stored 0.9262 is
   reproduced exactly (machine precision) only by the k = 10 τ on the 26-condition grid; the k = 5
   value is 0.9125. The two other stored metrics are not exactly reproduced by any variant I tried,
   so the archived JSON's exact code state cannot be certified — this needs an author-side
   confirmation, and the revision must quote whichever k it actually uses. Verdicts are unaffected
   either way (all k ∈ {3,…,100} give 0.913–0.936).
2. **τ at k = 1 does not exist** (Kendall τ on one rank is undefined); reported as `null` with an
   arg-max-agreement diagnostic instead. Any τ(k) figure must therefore start at k ≥ 2.
3. **Absolute τ is k-dependent** (up to 0.085 between k = 3 and k = 100 at λ = 0.5) — τ numbers from
   different k must never be compared.
4. **E3 `rare_species` is a 50-class/1 000-image subset** of the 400-species benchmark, and the
   image-only benchmarks need a gap direction that is not caption-derived (both variants reported).
5. **E4 has one seed per non-Flickr30k dataset**, and the archived COCO checkpoint was rejected as
   non-comparable (131 M trainable params, 790 steps, val R@1 2.9 %).
6. **Every real LoRA checkpoint lies above the synthetic τ→top-1 curve** (+3.3 to +5.5 pts at
   matched τ), which qualifies the "real checkpoints lie on the same manifold" phrasing of the
   manuscript; the archived Flickr30k checkpoints have τ above the synthetic curve's range entirely.
