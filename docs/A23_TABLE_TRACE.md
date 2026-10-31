# A23 — Numerical trace of every table in `paper_a2/`

**Engagement**: read-only numerical-integrity audit of the merged manuscript in `paper_a2/`
(target journal *Ocean Engineering*), pre-submission.

**Rule applied**: a number counts as *verified* only when the specific result JSON that is the
experiment behind that table can be named, and preferably a named key path with the value.
Corpus-wide coincidence matching was explicitly rejected: the corpus contains **126,860 leaf
values across 316 JSON files** (`outputs/*.json` + `paper3/scripts/outputs/**/*.json`), so a
"found somewhere" search is meaningless. Every attribution below names the file and key path;
whenever a match was found only by brute-force value search it is reported as *coincidence* and
**not** counted as verified.

**Tables audited**: 24 (16 in `main.tex`, 8 in the five `ext_part*.tex` files). Note: the task
brief counted 22; the actual capture is 16 + 8 = 24 (`tab:dynamics`, `tab:matrix`, `tab:degmap`,
`tab:subspace`, `tab:perimage`, `tab:theory-stack`, `tab:qa-layers`, `tab:classlaw` in the
extension parts).

**Verification classes used below**

- **direct** — value read from a named JSON key path.
- **recomputed** — derived (ratio / mean / sd / difference); the arithmetic is shown, inputs are
  direct values from the named JSON.
- **NOT attributed** — no JSON source; or the cell as *labelled* does not correspond to any
  experiment in the corpus.
- **DISCREPANCY** — a paper value that contradicts the JSON.

**No file under `paper_a2/` was modified.** Temporary scripts are `tools/_tmp_a23_*.py`.

---

## 0. Corpus layout (the mapping key)

| experiment family | JSON file(s) |
|---|---|
| sonar balanced 650 img | `outputs/sonar_protocol.json` (`clip_frozen`, `sonar_ft`, `clip_flickrft`) |
| sonar full 2617 img | `outputs/sonar_protocol_full.json` (`clip_frozen`, `sonar_ft_full`, `clip_flickrft`) |
| sonar adaptation seeds | `outputs/sonar_peft.json` (seed 42), `outputs/sonar_peft_ms.json` (s1, s99) |
| sonar NCC/spectrum | `outputs/sonar_spectrum.json` |
| marine portrait / margins | `outputs/ocean_margins.json`, `ocean_nsweep.json`, `ocean_spectrum.json`, `ocean_gap_surgery.json`, `ocean_multiseed.json`, `ocean_sigma_other.json`, `text_fine_grid.json`, `ocean_flickr_dhat.json` |
| matched-scale 2×2 | `outputs/ocean_clip2x2.json`, `ocean_flickrft_sigma.json`, `ocean_marineft10_sigma.json` |
| marine PEFT | `outputs/ocean_peft.json`, `outputs/ocean_peft_ms.json` |
| top-1 bounds | `outputs/ocean_rank1_bound.json` |
| degradation (marine/sonar) | `outputs/ocean_degradation.json`, `outputs/degradation_matrix.json`, `outputs/direction_operator.json`, `outputs/direction_subspace.json`, `outputs/perimage_operator.json`, `outputs/mechanism_summary.json` |
| MarineLife-16K | `outputs/ocean_ml16k_retrieval.json`, `outputs/ml16k_qa_layers.json`, `outputs/ocean_replica.json`, `outputs/bioclip_lora_instruction.json`, `outputs/bioclip_joint_training.json` |
| domain matrix | `outputs/domain_matrix.json` |
| dynamics | `outputs/ocean_tautraj.json`, `dynamics_matrix.json`, `dynamics_seed.json`, `dynamics_fathomnet.json`, `vlm_instruction_dynamics.json`, `vlm_vision_instruction_dynamics.json` |
| replication instruments | `outputs/watertank_protocol.json`, `outputs/riku_protocol.json`, `outputs/uatd_protocol.json` |
| tripwire calibration | `outputs/threshold_calibration.json` |
| canonical ImageNet reference (companion study A1) | `outputs/a1_full_results.json`, `a1_text_surgery.json`, `a1_baseline_metrics.json`, `a1_margins.json`, `a1_theory_verify.json`, `a1_tau_holdout.json` |

---

## 1. `tab:sonar-exact` (main.tex:207–228) — Sonar exact-predictor verification

**Source**: `outputs/sonar_protocol_full.json` (*FULL 2,617* protocol) — confirmed by `meta.dataset =
"NKSID (Bohai Bay, Oculus M750d), FULL 2617"`, `meta.n_images = 2617`, and by `sigma_m = 0.0247`
matching the "full" rows of `tab:sonar-sigma`. Blocks: `clip_frozen`, `sonar_ft_full`,
`clip_flickrft`; each `rows[i]` carries `lambda`, `top1`, `tau_meas`, `tau_pred`, `CG`.

All 36 numeric cells verified **direct**:

| row | τ pred | τ meas | top-1 | CG |
|---|---|---|---|---|
| CLIP frozen λ=0.5 | `clip_frozen.rows[3].tau_pred` 0.1631 | `.tau_meas` 0.1631 | `.top1` 16.469→16.47 | `.CG` 0.5787→0.579 |
| CLIP frozen λ=1 | `rows[4].tau_pred` −0.0807 | −0.0807 | 5.235→5.24 | 0.0377→0.038 |
| CLIP frozen λ=2 | `rows[5].tau_pred` −0.2031 | −0.2031 | 5.197→5.20 | 0.4984→0.498 |
| SonarCLIP λ=0.5 | `sonar_ft_full.rows[3]` 0.8028 | 0.8028 | 99.962→99.96 | 0.5696→0.570 |
| SonarCLIP λ=1 | `rows[4]` 0.7202 | 0.7202 | 99.885→99.89 | 0.0970→0.097 |
| SonarCLIP λ=2 | `rows[5]` 0.5839 | 0.5839 | 89.836→89.84 | 0.4079→0.408 |
| CLIP+Flickr λ=0.5 | `clip_flickrft.rows[3]` 0.1444 | 0.1444 | 10.814→10.81 | 0.6261→0.626 |
| CLIP+Flickr λ=1 | `rows[4]` −0.0906 | −0.0906 | 5.502→5.50 | 0.0811→0.081 |
| CLIP+Flickr λ=2 | `rows[5]` −0.2267 | −0.2267 | 4.165→4.17 | 0.5225→0.523 |

Caption claim "the full grid λ∈{−1,−0.5,0,0.5,1,2} is exact in all 18 conditions" — verified
**direct**: for all 3 blocks × 6 λ, `tau_pred == tau_meas` to the stored 4 decimals (e.g.
`clip_frozen.rows[0]` 0.5217/0.5217 … `sonar_ft_full.rows[5]` 0.5839/0.5839). 18/18 ✓.

**Unattributed**: none. **Discrepancies**: none. → **37/37 verified (fully)**

---

## 2. `tab:sonar-sigma` (main.tex:235–251) — Sonar domain affinity

**Sources**: balanced rows → `outputs/sonar_protocol.json`; full rows → `outputs/sonar_protocol_full.json`.

| cell | paper | JSON path | value |
|---|---|---|---|
| CLIP frozen σm | 0.0239 | `sonar_protocol.clip_frozen.sigma_m` | 0.0239 |
| mean_m | 0.514 | `.mean_m` | 0.5139 |
| top1₀ | 16.15 | `.top1_0` | 16.154 |
| τ@λ=1 | −0.02 | `.rows[4].tau_meas` | −0.0225 |
| SonarCLIP(650) σm | 0.0063 | `sonar_protocol.sonar_ft.sigma_m` | 0.0063 |
| mean_m | 0.648 | `.mean_m` | 0.6483 |
| top1₀ | 96.77 | `.top1_0` | 96.769 |
| τ@λ=1 | 0.896 | `.rows[4].tau_meas` | 0.8957 |
| CLIP frozen(full) σm | 0.0247 | `sonar_protocol_full.clip_frozen.sigma_m` | 0.0247 |
| top1₀ | 14.94 | `.top1_0` | 14.941 |
| τ@λ=1 | −0.0807 | `.rows[4].tau_meas` | −0.0807 |
| SonarCLIP(full) σm | 0.0136 | `sonar_ft_full.sigma_m` | 0.0136 |
| top1₀ | 99.89 | `.top1_0` | 99.885 |
| τ@λ=1 | 0.7202 | `.rows[4].tau_meas` | 0.7202 |
| CLIP+Flickr σm | 0.0222 | `.sigma_m` | 0.0222 |
| top1₀ | 27.97 | `.top1_0` | 27.971 |
| τ@λ=1 | −0.0906 | `.rows[4].tau_meas` | −0.0906 |

**Recomputed** *flatten* column (frozen σm ÷ row σm, identical-domain inputs):
balanced SonarCLIP 0.0239/0.0063 = **3.794 → 3.8×** ✓; full SonarCLIP 0.0247/0.0136 =
**1.816 → 1.8×** ✓ (prose "1.82×" ✓); terrestrial 0.0247/0.0222 = **1.113 → 1.1×** ✓.
Prose "3.4× deeper than terrestrial (0.0239→0.0063 vs 0.0216)": 0.0239/0.0216 = 1.106
(balanced terrestrial `sonar_protocol.clip_flickrft.sigma_m = 0.0216`), 3.794/1.106 = **3.43 → 3.4×** ✓.

**Unattributed**: none (`mean_m` for the two full rows is printed "—" although the JSON holds
0.5107 and 0.6795). **Discrepancies**: none. → **25/25 verified (fully)**

---

## 3. `tab:sonar-peft` (main.tex:257–269) — Sonar adaptation, three seeds

**Sources**: `outputs/sonar_peft.json` (seed 42: `lora_both`, `fullft`) +
`outputs/sonar_peft_ms.json` (`lora_both__s1`, `lora_both__s99`, `fullft__s1`, `fullft__s99`).
The three seeds are {42, 1, 99}; the set is *proved* by the means (see below).

| cell | paper | recomputed | verdict |
|---|---|---|---|
| LoRA-both top-1 | 100.0±0.0 | 100.0 / 100.0 / 100.0 → mean 100.0, sd 0.0 | ✓ |
| LoRA-both R@1 | 1.000±0.0 | 1.0 / 1.0 / 1.0 | ✓ |
| LoRA-both τ@1 | 0.575±0.062 | 0.6606 / 0.5132 / 0.5514 → mean **0.5751**, sd(pop) **0.0625** | ✓ |
| FullFT top-1 | 72.8±36.2 | 96.769 / 99.846 / 21.846 → mean **72.820**, sd(pop) **36.066**, sd(sample) 44.172 | **DISCREPANCY** |
| FullFT τ@1 | 0.881±0.015 | 0.8957 / 0.8877 / 0.8594 → mean **0.8809**, sd(pop) **0.0156**, sd(sample) 0.0191 | **DISCREPANCY (last digit)** |

sd convention: every other `mean±sd` in this table reproduces with the **population** sd
(numpy `ddof=0`). Prose "0.8877/0.8957/0.8594 across seeds" ✓ (**direct**).

- **DISCREPANCY D9** — top-1 sd: paper **36.2**, JSON-derived **36.07** (`sonar_peft.json
  fullft.top1_0`, `sonar_peft_ms.json fullft__s1.top1_0`, `fullft__s99.top1_0`). 36.2 matches
  neither the population (36.07) nor the sample (44.17) convention.
- **DISCREPANCY D10** — τ sd: paper **0.015**, JSON-derived **0.0156 → 0.016** (pop) / 0.0191 (sample).
- **DISCREPANCY D11** — prose "one of three seeds stalls at **21.9%** top-1": the stored value is
  **21.846** (`sonar_peft_ms.json fullft__s99.top1_0`) → 21.8%. (+0.1 pp.)
- Note: the FullFT row's inputs come from the **balanced 650** protocol
  (`sonar_peft.json.fullft.source = "sonar_protocol.json"`, `top1_0 = 96.769`), while the caption
  quotes the full-protocol baseline 99.89 as the SonarCLIP reference — the row is a balanced-protocol
  result compared against a full-protocol baseline in the caption.

→ **7/10 verified; 3 discrepancies**

---

## 4. `tab:spectrum` (main.tex:302–320) — Marine task-sensitivity spectrum

**Source**: `outputs/ocean_spectrum.json` (`bioclip.rows[i]`, `oceanclip.rows[i]`, keys `lambda`,
`NCC`, `top1`, `R1`, `CG`). All 32 numeric cells **direct**:

- BioCLIP: λ=0 → `rows[0]` NCC 78.358→78.36, top1 21.704→21.70, R1 0.3399→0.340, CG 0.5241→0.524;
  λ=0.5 → `rows[1]` 78.109→78.11, 19.59, 0.3293→0.329, 0.269; λ=1 → `rows[2]` 76.43, 18.035→18.03,
  0.2842→0.284, 0.0194→0.019; λ=2 → `rows[3]` 68.097→68.10, 14.925→14.93, 0.2537→0.254, 0.4097→0.410.
- OceanCLIP: λ=0 → 66.418→66.42, 24.192→24.19, 0.2777→0.278, 1.0209→1.021; λ=0.5 → 65.361→65.36,
  24.44, 0.264, 0.5042→0.504; λ=1 → 62.065→62.06, 23.383→23.38, 0.199, 0.1359→0.136;
  λ=2 → 46.953→46.95, 19.652→19.65, 0.1729→0.173, 0.3905→0.391.

Same file mirrors these under `outputs/mechanism_summary.json → sources.spectrum_marine` (consistency
check ✓). Prose ranges (78.4→76.4, 66.4→62.1, 0.340→0.254, 0.278→0.173, CG rebound 0.41/0.39) ✓.

**Unattributed**: none. **Discrepancies**: none. → **40/40 (fully)**

---

## 5. `tab:portrait` (main.tex:329–345) — Marine model portrait + subset-seed robustness

**Sources**: `ocean_spectrum.json`, `ocean_margins.json`, `ocean_sigma_other.json`,
`ocean_gap_surgery.json`, `ocean_multiseed.json`, and (ImageNet reference row) the A1 files.

| model | cell → path |
|---|---|
| OceanCLIP | top-1 24.19 `ocean_spectrum.oceanclip.rows[0].top1` 24.192; CG 1.021 `.CG` 1.0209; σm 0.0078 `ocean_margins.oceanclip.sigma_m` 0.00783; mean_m 0.683 `.mean_m` 0.68264; τ@1 0.454 `.predicted_tau_exact["1.0"]` 0.45386; retention 96.7% **recomputed** `ocean_nsweep.oceanclip["67"].top1_1/top1_0` = 23.38308/24.19154 = 0.96658; Δτ +0.007 **recomputed** `ocean_gap_surgery` text-side λ=1 `tau` 0.4607 − image-side 0.4539 = 0.0068 |
| BioCLIP | top-1 21.70 (21.704); CG 0.524 (0.52409); σm 0.0535 (0.05348); mean_m 0.204 (0.20371); τ@1 0.463 (0.46331); retention 83.1% = 18.03483/21.70398 = 0.83095; Δτ +0.246 = `text_fine_grid[4].tau` 0.7093 − 0.4633 |
| SigLIP | top-1 15.24 `ocean_gap_surgery[39].top1` 15.236; CG 1.130 `ocean_sigma_other.siglip.gap_norm` 1.1297; σm 0.0299; mean_m 0.609 (0.6089); τ@1 0.046 `ocean_gap_surgery[42].tau` 0.0462; retention 46.1% = 7.027/15.236 = 0.4612; Δτ +0.083 = text 0.1294 − image 0.0462 |
| OpenCLIP | top-1 7.03 `ocean_gap_surgery[27].top1` 7.027; CG 0.849 `ocean_sigma_other.openclip_tf.gap_norm` 0.8489; σm 0.0739; mean_m 0.513; τ@1 0.036 `[30].tau` 0.0361; retention 37.2% = 2.612/7.027 = 0.3717; Δτ +0.076 = 0.1123 − 0.0361 |
| CLIP (ImageNet) | top-1 59.28 `a1_full_results[6].top1`; CG 0.815 `[6].CG` 0.8153 / `a1_baseline_metrics.theory_verification.gap_norm` 0.8154; σm 0.067 `a1_baseline_metrics.theory_verification.std_m_c` 0.0673; mean_m 0.372 `a1_margins.meta.mean_m` 0.37204; τ@1 0.289 `a1_full_results[11].tau_top5` 0.2887; retention 54.0% = `[11].top1` 32.01 / `[6].top1` 59.28 = 0.5400; Δτ +0.141 = `a1_text_surgery.results[2].text_side.tau` 0.4295 − `image_side.tau` 0.2885 |

Caption robustness (**recomputed** from `ocean_multiseed.json`): OceanCLIP τ@λ=1 seeds
(0.4544, 0.4539, 0.4410) → mean **0.44977→0.450**, sd(pop) **0.0062→0.006** ✓; BioCLIP
(0.4590, 0.4633, 0.4512) → mean **0.45783→0.458**, sd(pop) **0.0050→0.005** ✓.

**Unattributed**: none. **Discrepancies**: none. → **37/37 (fully)**

---

## 6. `tab:disc` (main.tex:347–366) — Matched-scale 2×2 discrimination

**Sources**: `outputs/ocean_margins.json`, `ocean_flickrft_sigma.json`,
`ocean_marineft10_sigma.json`, `ocean_clip2x2.json`. All 28 numeric cells **direct**:

| row | σm | mean_m | CG | marine top-1 |
|---|---|---|---|---|
| BioCLIP none | 0.0535 `ocean_margins.bioclip` | 0.204 | 0.524 | 21.70 |
| BioCLIP+Flickr | 0.0233 `ocean_flickrft_sigma.sigma_m` | 0.591 (0.5909) | 0.893 (0.8927) | 9.08 `top1_0` |
| BioCLIP+Marine | 0.0064 `ocean_marineft10_sigma.sigma_m` | 0.630 (0.6303) | 1.062 (1.0615) | 100.0 `top1_0` |
| CLIP none | 0.0333 `ocean_clip2x2.clip_frozen.sigma_m` | 0.588 (0.5869) | 0.978 (0.9778) | 6.78 (6.779) |
| CLIP+Flickr | 0.0203 `clip_flickrft.sigma_m` | 0.585 | 1.069 (1.0685) | 3.61 (3.607) |
| CLIP+Marine | 0.0092 `clip_marineft.sigma_m` | 0.622 (0.6223) | 1.060 (1.0603) | 63.62 (63.619) |
| OceanCLIP 50ep | 0.0078 | 0.683 | 1.021 | 24.19 |

Prose ratios **recomputed**: 0.0233/0.0064 = **3.64 → 3.6×** ✓; 0.0203/0.0092 = **2.21 → 2.2×** ✓;
0.0233/0.0078 = **2.99 → 3×** ✓. Class-set sweep "99.1%/98.1%/96.7% at N=20/40/67"
**recomputed** from `ocean_nsweep.oceanclip`: 46.25/46.6667 = 99.11%, 37.60417/38.33333 = 98.10%,
23.38308/24.19154 = 96.66% ✓. fauna-117 98.5% (`ocean_inat_wild` 28.646/28.993 = 98.80% for iNat;
`mechanism_summary.sources.class_set[3].retention1` = 0.98548 for fauna) ✓; iNat-48 98.8% ✓.

**Unattributed**: none. **Discrepancies**: none. → **28/28 (fully)**

---

## 7. `tab:peft` (main.tex:368–385) — Adaptation sweep, three seeds

**Source**: `outputs/ocean_peft_ms.json`, keys `<model>__<method>__s<seed>`, fields `flickr_R1`,
`marine_top1`. Frozen baselines `ocean_spectrum` 21.704 / 24.192. All means and 5 of 6 sds
**recomputed** with the population sd used elsewhere in the paper:

| row | R@1 mean±sd | marine top-1 mean±sd | retention |
|---|---|---|---|
| BioCLIP LoRA-text | 0.11387±0.00373 → **0.114±0.004** ✓ | 22.948±0.2033 → **22.95±0.20** ✓ | 22.948/21.704−1 = **+5.73%** (paper +5.8%) |
| BioCLIP FullFT | 0.33977±0.05424 ✓ | 8.3333±1.3175 ✓ | **−61.60%** ✓ |
| OceanCLIP LoRA-text | 0.34837±**0.00347** (paper 0.348±**0.004**) | 23.3623±0.1274 ✓ | **−3.43%** ✓ |
| OceanCLIP LoRA-both | 0.6200±0.00497 ✓ | 22.2223±0.3568 ✓ | **−8.14%** ✓ |
| OceanCLIP BitFit | 0.1781±0.00184 ✓ | 23.5073±0.0510 ✓ | **−2.83%** ✓ |
| OceanCLIP FullFT | 0.5870±0.01510 ✓ | 20.5223±0.7111 ✓ | **−15.17%** ✓ |

- Minor: OceanCLIP LoRA-text R@1 sd printed **0.004**, population sd **0.0035** (sample sd 0.0042);
  this is the only cell in the table that needs the sample convention.
- Minor: BioCLIP LoRA-text retention printed **+5.8%**; 22.948/21.704 = +5.73% (+5.75% if the
  rounded baseline 21.70 is used). Within last-digit rounding, flagged for completeness.
- The `+5.8%` / `−61.6%` / `−15.2%` etc. all use the unrounded baselines 21.704/24.192 ✓.

→ **28/30 strictly verified; 2 last-digit rounding notes; no material discrepancy**

---

## 8. `tab:rank1` (main.tex:399–419) — Top-1 loss bounds

**Source**: `outputs/ocean_rank1_bound.json`, keys `<model>.rows.<λ>.{exact, corr_gauss,
weak_bound, meas_keep_loss}`. All 32 numeric cells **direct**:

| row | exact(3a) | Gaussian(3c) | weak | measured |
|---|---|---|---|---|
| BioCLIP 0.5 | 0.2251 | 0.2788 | 1.8045→1.80 | 0.0974→0.097 |
| BioCLIP 1 | 0.3507 | 0.45→0.4500 | 2.6835→2.68 | 0.169 |
| BioCLIP 2 | 0.4745 | 0.6059 | 3.4465→3.45 | 0.3123→0.312 |
| OceanCLIP 0.5 | 0.1940 | 0.2349 | 1.7115→1.71 | −0.0103→−0.010 |
| OceanCLIP 1 | 0.3570 | 0.3732 | 2.7305→2.73 | 0.0334→0.033 |
| OceanCLIP 2 | 0.5560 | 0.5178 | 3.798→3.80 | 0.1877→0.188 |
| OpenCLIP 1 | 0.7351 | 0.7499 | 4.8195→4.82 | 0.6283→0.628 |
| SigLIP 1 | 0.7867 | 0.6969 | 4.769→4.77 | 0.5388→0.539 |

Independent cross-check: `ocean_margins.<model>.predicted_rank1_loss_exact` holds the same
`exact` values (BioCLIP 0.5/1/2 = 0.22512/0.35075/0.47450; OceanCLIP = 0.19403/0.35697/0.55597) ✓,
and the weak bound recomputes as 5(1−τ) from `ocean_margins.predicted_tau_exact`
(e.g. BioCLIP λ=1: 5(1−0.46331) = 2.6834) ✓.

- **DISCREPANCY D8** — caption "Bold: the **single** violation of the Gaussian bound (OceanCLIP,
  λ=2)". The table's own SigLIP λ=1 row is a **second** violation: exact **0.7867** > Gaussian
  **0.6969**. The prose makes it worse by asserting the false inequality "siglip **0.697 ≥ 0.787**
  holds by a smaller margin". (In the full stored grid there are further violations:
  `bioclip.rows["-1.0"]` 0.5106 vs 0.45; `openclip_tf.rows["2.0"]` 0.7929 vs 0.7756;
  `siglip.rows["2.0"]` 0.8818 vs 0.7498.)

→ **32/32 cells verified; caption/text claim is wrong**

---

## 9. `tab:dir-op` (main.tex:426–443) — Direction-resolved operator v1

**Source**: `outputs/direction_operator.json` (`marine_bioclip[0..2]`, `sonar_frozen[0..3]`);
columns `tau_meas`, `err_gap`, `err_mean`, `resid_frac_mean`. All 24 numeric cells **direct**:

| row | τ | err(gap) | err(mean-dir) | residual |
|---|---|---|---|---|
| Marine haze t=0.6 | 0.4803→0.480 | 0.4626→0.463 | 0.3167→0.317 | 0.9543→0.954 |
| Marine haze t=0.3 | 0.2881→0.288 | 0.6155→0.616 | 0.3623→0.362 | 0.9387→0.939 |
| Marine uw_cast | 0.399 | 0.5328→0.533 | 0.3254→0.325 | 0.9522→0.952 |
| Sonar speckle 20% | 0.5252→0.525 | 0.4178→0.418 | 0.2898→0.290 | 0.7028→0.703 |
| Sonar blur r=2 | 0.1843→0.184 | 0.7243→0.724 | 0.1769→0.177 | 0.8097→0.810 |
| Sonar shadow | 0.620 | 0.3622→0.362 | 0.1772→0.177 | 0.9031→0.903 |

Cross-checks: the marine rows are identical to `outputs/ocean_degradation.json`
(`bioclip.rows[1..3]`, `oceanclip.rows[1..3]` for the top-1 column, `haze_t0.60/haze_t0.30/uw_cast`);
the PCA caveat in the prose ("sonar blur 0.43 vs 0.18") = `sonar_frozen[2].err_pca` 0.432 and
`.err_mean` 0.1769 ✓; the residual ranking in the prose (speckle 0.70 < blur 0.81 < shadow 0.90 <
marine 0.94–0.95) ✓.

**Unattributed**: none. **Discrepancies**: none. → **24/24 (fully)**

---

## 10. `tab:ml16k` (main.tex:450–466) — Natural-text retrieval

**Source**: `outputs/ocean_ml16k_retrieval.json` (`<model>.q_ans|q_only|ans.{video_R1,
video_R5}`), `meta.n_frames = 3416`, `meta.n_queries = 3440`. All 15 numeric cells **direct**:

- OpenCLIP (general) q+a: `openclip_tf.q_ans.video_R1` 1.919 → **1.92%** ✓ (chance 1/427 =
  0.2342% → 0.23% ✓ **recomputed**); `video_R5` absent for this model → "—" ✓.
- BioCLIP q+a: `bioclip.q_ans` 0.872 → 0.87%, 3.198 → 3.20% ✓.
- OceanCLIP q+a: `oceanclip.q_ans` 0.262 → 0.26%, 1.599 → 1.60% ✓.
- OceanCLIP question only: `.q_only` 0.291 → 0.29%, 1.25 ✓.
- OceanCLIP answer only: `.ans` 0.291 → 0.29%, 1.541 → 1.54% ✓.

Prose multipliers **recomputed**: 1.919/0.2342 = 8.2× ("8× chance" ✓); 27.645 (replica) / 0.2342
= 118× ("120× chance" in `tab:replica` prose — see §11).

**Unattributed**: none. **Discrepancies**: none. → **15/15 (fully)**

---

## 11. `tab:watertank` (main.tex:483–514) — Three-instrument acoustic replication

**Sources**: `outputs/watertank_protocol.json`, `outputs/riku_protocol.json`,
`outputs/uatd_protocol.json` (each: `frozen`, `flickrft`, `domainft` with
`sigma_m`, `top1_0`, `rows[i].{lambda,top1,tau_meas,tau_pred}`, `rows[6]` = `"text1.0"`).

Direct cells all verified: σm 0.0287/0.0309/0.0067 (watertank), 0.0286/0.0265/0.0213 (riku),
0.0176/0.0175/0.0002 (uatd); top1₀ 17.33/13.352/99.432, 6.796/0.0/84.951, 15.438/9.812/4.438;
τ@λ=1 = `rows[4].tau_meas` −0.1074 / 0.3642 / 0.7943, −0.3252 / 0.0087 / 0.7893,
0.1171 / −0.1202 / **0.1532**; "all exact" for watertank-domainft and riku-domainft ✓ (all 6 λ
have `tau_pred == tau_meas`); negative values in prose (−0.1074, −0.3252, −0.1202) ✓.

**Recomputed** Δτ = τ_text(λ=1) − τ_image(λ=1) using `rows[6].tau_meas` − `rows[4].tau_meas`:

| row | computed | paper |
|---|---|---|
| watertank frozen | −0.079 − (−0.1074) = **+0.0284 → +0.028** | +0.028 ✓ |
| watertank flickrft | 0.3807 − 0.3642 = **+0.0165 → +0.017** | +0.017 ✓ |
| watertank domainft | 0.8091 − 0.7943 = **+0.0148 → +0.015** | +0.015 ✓ |
| riku frozen | −0.299 − (−0.3252) = **+0.0262 → +0.026** | +0.026 ✓ |
| riku flickrft | 0.0612 − 0.0087 = **+0.0525 → +0.053** | +0.053 ✓ |
| riku domainft | 0.7913 − 0.7893 = **+0.0020 → +0.002** | +0.002 ✓ |
| uatd frozen | 0.1706 − 0.1171 = **+0.0535 → +0.054** | +0.054 ✓ |
| uatd flickrft | 0.0685 − (−0.1202) = **+0.1887 → +0.189** | +0.189 ✓ |
| **uatd domainft** | 0.1126 − 0.1532 = **−0.0406 → −0.041** | **+0.009** ✗ |

**Recomputed** flatten: 0.0287/0.0067 = 4.284 → **4.3×** ✓ (prose 4.6× below terrestrial:
0.0309/0.0067 = 4.612 ✓); 0.0286/0.0213 = 1.343 → **1.34×** ✓; 0.0287/0.0309, 0.0286/0.0265,
0.0176/0.0175 all ≈ 1.0–1.08 → **1.1× / 1.1× / 1.0×** ✓.

- **DISCREPANCY D2** — UATD domainft Δτ: paper **+0.009**; JSON gives **−0.041**
  (`uatd_protocol.json domainft.rows[6].tau_meas` 0.1126 minus `domainft.rows[4].tau_meas` 0.1532).
  (+0.009 coincides with the τ_pred−τ_meas deviation at λ=0.5 of the same block: 0.8186 − 0.8095 =
  0.0091; and the prose separately reports "deviation 0.009–0.016", which *is* correct.)
- **DISCREPANCY D3** — "exact τ = **12/12†**" printed in the UATD domainft row. The JSON shows only
  **3 of 6** λ conditions exact for that row (`tau_pred == tau_meas` at λ = −1, −0.5, 0; deviations
  0.0091 / 0.0161 / 0.0061 at λ = 0.5 / 1 / 2). "12/12" matches the *frozen + flickrft* rows
  (6 + 6), as the caption footnote itself states — as printed it contradicts the row it sits on.

→ **40/42 verified; 2 discrepancies (1 wrong value, 1 mislabelled count)**

---

## 12. `tab:replica` (main.tex:550–573) — Text-type discrimination

**Sources**: `ocean_margins.json` + `ocean_ml16k_retrieval.json` (BioCLIP, OceanCLIP rows),
`ocean_replica.json` (`marine`, `retrieval`), `bioclip_lora_instruction.json`
(`marine`, `retrieval`). All 20 numeric cells verified:

| row | σm | top1₀ | τ@1 | Δτ | ML16K R@1 |
|---|---|---|---|---|---|
| BioCLIP | 0.0535 | 21.704 | 0.46331 | 0.7093−0.4633 = +0.2460 ✓ | `ocean_ml16k_retrieval.bioclip.q_ans.video_R1` 0.872 |
| OceanCLIP | 0.00783 | 24.192 | 0.45386 | 0.4607−0.4539 = +0.0068 ✓ | `.oceanclip.q_ans.video_R1` 0.262 |
| Replica | `ocean_replica.marine.sigma_m` 0.0167 | `.top1_0` 2.861 | `.rows[5].tau_meas` 0.2174 | `.tau_text1` 0.2781 − 0.2174 = +0.0607 ✓ | `ocean_replica.retrieval.q_ans.video_R1` 27.645 |
| Replica LoRA | `bioclip_lora_instruction.marine.sigma_m` 0.0598 | `.top1_0` 19.963 | `.tau_l1` 0.3435 | `.tau_text1` 0.5458 − 0.3435 = +0.2023 ✓ | `bioclip_lora_instruction.retrieval.q_ans.video_R1` 11.657 |

Prose cross-checks: "27.65%, 120× chance, 14× the general CLIP baseline" — **recomputed**
27.645/0.2342 = 118.0 (paper "120×", ~2% off, consistent with using chance = 0.23% and rounding);
27.645/1.919 = 14.4 → 14× ✓. "92% of the species zero-shot (19.96 vs 21.70)" — **recomputed**
19.963/21.704 = 91.98% ✓. "{13× base}" 11.657/0.872 = 13.4 ✓. Joint co-training negative
(83.52%, 9.58%, 13.05%, τ 0.3918, 0.5823) → `outputs/bioclip_joint_training.json marine.top1_0 =
83.52`, `.top1_heldout = 9.583`, `retrieval.q_ans.video_R1 = 13.052`, `.tau_l1 = 0.3918`,
`.tau_text1 = 0.5823` ✓ all **direct**.

**Unattributed**: none. **Discrepancies**: none (the "120×" is a rounding-level difference from
118×). → **20/20 (fully)**

---

## 13. `tab:monitor` (main.tex:657–676) — Training-time monitor worked example

**Source**: `outputs/ocean_tautraj.json` (`marine` = BioCLIP marine FT, `flickr` = BioCLIP
terrestrial FT; fields `epoch, loss, top1, tau, CG`). All 32 numeric cells **direct**:

| FT | ep | loss | top-1 | τ | JSON index |
|---|---|---|---|---|---|
| Marine | 1 | 2.4217→2.42 | 58.396→58.40 | 0.1765→0.177 | `marine[0]` |
| Marine | 3 | 0.753→0.75 | 86.256→86.26 | 0.1812→0.181 | `marine[2]` |
| Marine | 5 | 0.4389→0.44 | 97.761→97.76 | 0.1781→0.178 | `marine[4]` |
| Marine | 10 | 0.3075→0.31 | 100.0 | 0.1719→0.172 | `marine[9]` |
| Flickr | 1 | 3.6477→3.65 | 5.846→5.85 | 0.0693→0.069 | `flickr[0]` |
| Flickr | 3 | 0.5951→0.60 | 9.266→9.27 | 0.1474→0.147 | `flickr[2]` |
| Flickr | 5 | 0.0798→0.08 | 10.759→10.76 | 0.1566→0.157 | `flickr[4]` |
| Flickr | 10 | 0.008 | 9.701→9.70 | 0.1464→0.146 | `flickr[9]` |

Caption baselines (top-1 21.70, τ=1.0) = `ocean_spectrum.bioclip.rows[0]` ✓.

**Unattributed**: none. **Discrepancies**: none. → **34/34 (fully)**

---

## 14. `tab:degrad` (main.tex:690–707) — Degradation-surgery stress test

**Source**: `outputs/ocean_degradation.json` (`bioclip.rows`, `oceanclip.rows`; fields
`degrade, lam_eff, s_std, tau_meas, tau_pred, diff, top1`). Mirrored in
`mechanism_summary.sources.degradation_marine`. All 24 numeric cells **direct**:

- BioCLIP haze t=0.6: `rows[1]` lam_eff 0.0005→+0.001 ✓, τ 0.4803→0.480 ✓, τ_pred 0.9991→0.999 ✓,
  top1 19.341→19.34 ✓; haze t=0.3: `rows[2]` 0.0336→+0.034, 0.2881→0.288, 0.9668→0.967, 15.485→15.49 ✓;
  uw_cast: `rows[3]` −0.0247→−0.025, 0.399, 0.9718→0.972, 18.843→18.84 ✓.
- OceanCLIP: 0.6399→0.640 / 0.3637→0.364 / 0.5175→0.518; τ_pred 0.9983→0.998 / 0.9999→0.999 /
  0.9994→0.999; top1 23.756→23.76 / 19.9→19.90 / 22.948→22.95; lam_eff −0.0018→−0.002 / 0.0003→+0.000 /
  0.0012→+0.001 ✓.

Prose cross-checks **recomputed**: max |λ_eff| = 0.0336 ≤ 0.034 ✓; max `s_std` = 0.0758 ≤ 0.076 ✓;
`diff` column spans 0.3583–0.6787 → "failure of 0.36–0.68" ✓; "τ≈0.97–1.00" = τ_pred span
0.9668–0.9999 ✓; top-1 pairs (23.76/19.90/22.95 vs 19.34/15.49/18.84) ✓.

**Unattributed**: none. **Discrepancies**: none. → **24/24 (fully)**

---

## 15. `tab:eng` (main.tex:709–724) — Engineering procedure

Contains **no result-derived numeric cells**: every entry is a qualitative rule
(`τ≥0.8 safe`, `σm≲0.01 = marine-adapted`, `PEFT (BitFit/LoRA-both)`, `τ<0.5 precedes accuracy loss`,
`marine ≤ 1/2 of terrestrial`, `≥96% retention`). The two threshold numbers are consistent with
`tab:calib` (τ≥0.8 band) and `tab:disc` (σm values 0.0064–0.0092 vs 0.0203–0.0233, i.e. well below
1/2). → **n/a (0 numeric cells; thresholds consistent with §6 and §16)**

---

## 16. `tab:calib` (main.tex:726–743) — Tripwire calibration

**Source**: `outputs/threshold_calibration.json`, `cutoffs.ret_ge_0.96.<cut>.{sensitivity,
specificity, sens_lo, sens_hi, spec_lo, spec_hi}` and `cutoffs.ret_ge_0.83`. All 22 statistic cells
**direct**:

| tripwire | baseline | paper sens [CI] | JSON | paper spec [CI] | JSON |
|---|---|---|---|---|---|
| τ≥0.8 | ret≥96% | 0.229 [0.100, 0.375] | `ret_ge_0.96["0.8"]` ✓ | 0.988 [0.961, 1.0] | ✓ |
| τ≥0.8 | ret≥83% | 0.153 [0.067, 0.258] | `ret_ge_0.83["0.8"]` ✓ | 1.000 | ✓ |
| τ≥0.5 | ret≥96% | 0.543 [0.371, 0.707] | `ret_ge_0.96["0.5"]` ✓ | 0.735 [0.634, 0.827] | ✓ |
| τ≥0.5 | ret≥83% | 0.559 [0.434, 0.684] | `ret_ge_0.83["0.5"]` ✓ | 0.864 [0.774, 0.946] | ✓ |

Caption "118 matrix grid points, five domains, four model families": `n_points = 118` ✓ **direct**;
`cells` decompose into 6 domain labels (imagenet5k, dtd, food101, marine-67, sonar-balanced,
sonar-full) × 4 model families = 22 domain×model cells ✓ **recomputed**. Prose precision 0.889 =
`cutoffs.ret_ge_0.96["0.8"].precision` ✓.

- **NOT ATTRIBUTED D14** — "2{,}000-fold bootstrap over points": the JSON stores no
  bootstrap-replicate count (no key contains "boot"; the string "2000" does not occur in the file).
  The CI bounds themselves are stored and match.

→ **23/24 verified; 1 unattributed caption number**

---

## 17. `tab:theory-stack` (ext_partI_theory.tex:179–200)

**Sources**: `outputs/a1_tau_holdout.json`, `a1_text_surgery.json`, `a1_theory_verify.json`.

| cell | paper | JSON path | value |
|---|---|---|---|
| Thm 1 validation | "9/9 ≤0.002" | `a1_tau_holdout.theory_vs_measured_tau.predicted_tau_exact_vs_measured_tau_5k` | `n = 9`, `max_abs_diff = 0.0019` ✓ |
| Thm 4 validation | "0.43 vs 0.29" | `a1_text_surgery.results[2].text_side.tau` / `.image_side.tau` | 0.4295 / 0.2885 ✓ |
| Cor 1 validation | "σ̃=0.454σm" | `a1_theory_verify.orthogonal.ratio_sigmaO_over_sigmaM` | 0.45397→0.454 ✓ (σ̃ 0.03057→"0.0306" ✓) |

Surrounding prose also verified **direct**: ‖g‖=0.815 (`a1_text_surgery.gap_norm` 0.8152),
σm=0.067 (`a1_baseline_metrics.theory_verification.std_m_c` 0.0673); Cor 1 residual claims
**recomputed** from `a1_theory_verify.predicted_tau_orthogonal` vs `measured_tau_orthogonal`
(max |Δ| = 0.0749 → "within 0.075" ✓; max over |λ|≤1 = 0.0388 → "within 0.039" ✓); the
orthogonal-vs-gap comparison 0.408 (`predicted_tau_orthogonal["1"]` 0.40844) vs the canonical
gap-axis 0.290 (`a1_full_results[11].tau_top5` 0.2887) ✓; "Gaussian 0.180 vs exact 0.290"
(`a1_tau_holdout …predicted_tau_gauss_vs_measured_tau_5k.predicted["1"]` = 0.18) ✓;
"correlated-structure bound from 0.651 to 0.570 (against the exact 0.520)" —
`a1_margins.predicted_rank1_loss_corr["1"]` = 0.65086 ✓, `a1_theory_verify.predicted_rank1_loss_emp["1"]`
= 0.57009 ✓, `a1_margins.predicted_rank1_loss_exact["1"]` = **0.5214** (paper "0.520" — last-digit);
shrinkage micro-validation (`a1_theory_verify.class_contraction`: predicted top-1 70.32 / 78.58, τ
0.7598 / 0.615, measured identical; self-field mean 0.043545, std 0.028834) ✓.

→ **5/5 numeric claims verified (one 0.520 vs 0.5214 truncation); no material discrepancy**

---

## 18. `tab:matrix` (ext_partII_domains.tex:15–51) — Domain–model matrix

**Primary source for the new domains**: `outputs/domain_matrix.json`
(`<domain>.<model>.{sigma_m, top1_0, tau_text1, ncc_0, rows[]}`; `rows[4]` = λ=1 with
`tau_meas/tau_pred/top1/CG`), cross-verified against
`outputs/mechanism_summary.json → sources.domain_matrix`.

Verified **direct** — σm / τ@λ=1 / NCC for all new-domain rows:
imagenet5k CLIP 0.0730 / 0.2713→0.271 (ncc 47.12 not printed); OpenCLIP 0.0666 / 0.3689→0.369;
SigLIP 0.0434 / 0.3978→0.398; BioCLIP 0.0922 / 0.2529→0.253; dtd CLIP 0.0232 / 0.2463→0.246 / 68.6;
OpenCLIP 0.0286 / 0.4498→0.450 / 75.74→75.7; SigLIP 0.0164 / 0.4838→0.484 / 79.36→79.4;
BioCLIP 0.0731 / 0.2757→0.276 / 66.28→66.3; food101 CLIP 0.0345 / 0.3866→0.387 / 80.9;
OpenCLIP 0.0502 / 0.3986→0.399 / 81.96→82.0; SigLIP 0.0285 / 0.4323→0.432 / 89.36→89.4;
BioCLIP 0.0439 / 0.3754→0.375 / 57.84→57.8. **All 24 of those cells ✓.**

Marine rows ✓: σm 0.0535/0.0078/0.0739/0.0299 (`ocean_margins`, `ocean_sigma_other`), τ@1
0.463/0.454/0.036/0.046, retention 83.1%/96.7%/37.2%/46.1% (**recomputed**, see §5).

Sonar rows: σm 0.0239 / 0.0063 and τ@1 −0.02 / 0.896 ✓ (`sonar_protocol.json`); NCC 96.8 ✓
(`sonar_spectrum.sonar_ft.rows[0].NCC` 96.769).

Problems:

- **DISCREPANCY D4** — sonar-8 "CLIP frozen" **top-1 ret. 34%**: not attributable.
  The cell's own parenthetical "λ=1 top-1 **5.2/16.2**" mixes protocols: 5.235 is
  `sonar_protocol_full.json clip_frozen.rows[4].top1` (full 2,617) while 16.154 is
  `sonar_protocol.json clip_frozen.top1_0` (balanced 650) → 32.4%. The full-protocol retention is
  5.235/14.941 = **35.0%**; the balanced retention is 16.154/16.154 = **100%**. No JSON contains a
  34% retention for the frozen sonar model.
- **DISCREPANCY D5** — sonar-8 "SonarCLIP" **top-1 ret. 99.9%**: not attributable. Both protocols
  give exactly **100%** (96.769/96.769 and 99.885/99.885). The only nearby number, 99.885, is the
  full-protocol zero-shot *accuracy* (`sonar_protocol_full.sonar_ft_full.top1_0`) — and
  `tab:sonar-sigma` prints that same number as `top1₀ = 99.89`.
- **DISCREPANCY D6** — imagenet-1k "BioCLIP" **top-1 ret. 16.7%**: retention implied by the JSON is
  16.14/16.72 = **96.5%** (`domain_matrix.imagenet5k.bioclip.rows[4].top1` / `.top1_0`). 16.72 is the
  zero-shot *accuracy*, which ext_partV prints correctly as "top-1 16.72".
- **DISCREPANCY D7** — imagenet-1k "CLIP" row mixes two experiments: σm 0.0730 and τ@1 0.271 are
  `domain_matrix.imagenet5k.clip_tf` (5,000-image subset) but the printed retention **54.0%** comes
  from the companion A1 full-ImageNet run (`a1_full_results[11].top1` 32.01 / `[6].top1` 59.28 =
  54.0%). The retention implied by the row's own JSON is 33.22/59.26 = **56.1%**.
- Consistency issue — the **NCC column has two different λ conventions**: the marine rows print
  NCC@λ=1 (`ocean_spectrum.bioclip.rows[2].NCC` 76.43→76.4, `oceanclip.rows[2].NCC` 62.065→62.1)
  while all dtd/food101/imagenet rows print `ncc_0` (λ=0). The marine λ=0 values would be 78.4 / 66.4.

→ **≈62/66 numeric cells verified; 4 unattributed/mislabelled cells. Not fully verified.**

---

## 19. `tab:dynamics` (ext_partIII_dynamics.tex:20–43)

**Sources**: `outputs/dynamics_matrix.json` (`clip_sonar` = seed 42, `clip_flickr`),
`dynamics_seed.json` (`clip_sonar_s0/s1/s99`, `bio_marine_s0/s1`, `clip_sonar_50ep`),
`ocean_tautraj.json` (`marine` = BioCLIP marine seed 42), `dynamics_fathomnet.json`,
`vlm_instruction_dynamics.json`, `vlm_vision_instruction_dynamics.json`.

Verified **direct** (single-run rows): CLIP+FathomNet τ@1 0.0542→0.054, τ@10 0.1, σm@1 0.009,
σm@10 0.0097, top-1@10 100.0 (`traj[0]/[9]`); Qwen2-VL text-only τ@1 `traj[0].tau_l1` 0.926,
τ@10 `traj[9].tau_l1` 0.9436→0.944, σm@1 0.0839, σm@10 0.0755; Qwen2-VL vision τ@1 0.8823→0.882,
τ@10 0.8813→0.881, σm@1 0.1413, σm@10 0.0823. Prose ranges all ✓ (text-only 0.93–0.97 = 0.926–0.9682;
vision 0.86–0.92 = 0.8587–0.9201; cosine 0.372→0.234 / 0.372→0.189 = `mean_cos` 0.3716→0.2338/0.1886).

Means of the three-seed rows all verified **recomputed**:
BioCLIP+Marine τ@1 = (0.1867+0.1715+0.1765)/3 = **0.17823→0.178** ✓; τ@10 =
(0.1929+0.1867+0.1719)/3 = **0.18383→0.184** ✓; CLIP+Sonar τ@1 = (0.2757+0.36+0.6729)/3 =
**0.43620→0.436** ✓; τ@10 = (0.3083+0.1274+0.3972)/3 = **0.27763→0.278** ✓; σm@1 =
(0.0104+0.0003+0.0174)/3 = **0.00937→0.0094** ✓; σm@10 = (0.0063+0.0037+0.0051)/3 = **0.00503→0.0050** ✓;
top-1@10 = (96.769+98.923+99.846)/3 = **98.513→98.5** ✓. (The means uniquely determine the seed set
as {42, 0, 1}; seed 99 is stored but excluded.)

Problems:

- **DISCREPANCY D12** — four `±` cells do not reproduce under any single sd convention
  (population sd reproduces every other mean±sd in the paper):
  - CLIP+Sonar τ@1: paper **±0.200**; computed **0.171** (pop) / 0.209 (sample).
  - CLIP+Sonar τ@10: paper **±0.140**; computed **0.112** (pop) / 0.137 (sample).
  - CLIP+Sonar top-1@10: paper **±1.5**; computed **1.29** (pop) / 1.58 (sample).
  - BioCLIP+Marine τ@10: paper **±0.010**; computed **0.0088** (pop) / 0.0108 (sample).
  (Cells that *do* reproduce: BioCLIP+Marine τ@1 ±0.008 = sample 0.0077 ≈ 0.008;
  σm@1 ±0.009 = sample 0.0086; σm@10 ±0.001 ✓.)
- **DISCREPANCY (unattributed)** — BioCLIP+Marine **σm@10 = 0.0066**: only two seeds carry a σm
  trajectory in the whole corpus (`dynamics_seed.bio_marine_s0[9].sigma_m` = 0.0054;
  `bio_marine_s1[9].sigma_m` = 0.0081; the seed-42 trajectory `ocean_tautraj.marine` has no
  `sigma_m` field). Those two average **0.00675 → 0.0068**, not 0.0066. 0.0066 requires a third seed
  σm ≈ 0.0063 that exists in no JSON. (The σm@1 cell is consistent with the same 2 seeds:
  (0.0078+0.0106)/2 = **0.0092** ✓.)
- **DISCREPANCY D13** — the "CLIP+Sonar 50ep" row prints epoch-**50** values in the "@10" columns:
  τ@10 **0.155** and σm@10 **0.0046** are `dynamics_seed.clip_sonar_50ep[49].tau` 0.1548 and
  `[49].sigma_m` 0.0046; the JSON's epoch-10 values are τ **0.3166** (`[9].tau`) and σm **0.0062**
  (`[9].sigma_m`) — which is what the prose correctly reports ("σm 0.0062 at ep10 → 0.0046 at ep50;
  τ 0.317 at ep10 → 0.155 at ep50").

→ **≈32/38 cells verified; 4 sd cells + 1 mean cell + 2 mislabelled columns. Not fully verified.**

---

## 20. `tab:degmap` (ext_partIV_degradation.tex:14–46) — Degradation map

**Source**: `outputs/degradation_matrix.json` (`sonar_frozen`, `marine_bioclip`, `imagenet_clip`;
`rows[i].{degrade, lam_eff, tau_meas, top1, rel_top1_loss}`).

All printed **values** trace to that file (**direct**):
sonar speckle_p10 +0.0266→+0.027 / 0.5649→0.565 / 15.538→15.54 / 0.0381→0.04; p20 0.0261→+0.026 /
0.5252→0.525 / 11.385→11.38 / 0.2952→0.30; p40 0.0236→+0.024 / 0.4751→0.475 / 7.385→7.38 /
0.5429→0.54; blur_r1 0.0236→+0.024 / 0.2009→0.201 / 18.615→18.62; blur_r2 0.0386→+0.039 /
0.1843→0.184 / 21.538→21.54; blur_r4 0.0602→+0.060 / 0.2258→0.226 / 16.923→16.92;
shadow_strip −0.0025→−0.003 / 0.62 / 16.462→16.46 / 0.019→0.02.
marine rows 0.021/0.6498/20.149, 0.0747/0.4041/17.226, 0.0245/0.4898/19.403, 0.0347/0.481/18.905,
0.1108/0.3322/15.734. imagenet rows −0.0167/0.596/54.32, −0.0119/0.3798/36.12, −0.0078/0.6771/57.76,
−0.011/0.6294/55.24, −0.0062/0.5031/49.18. Prose "all |λ_eff| ≤ 0.11" ✓ (max 0.1108);
"sonar 0.565→0.475 / marine 0.481→0.332 / ImageNet 0.629→0.503" ✓.

- **DISCREPANCY D1 (label / semantics — the most serious finding of this audit)** — the marine and
  imagenet-5k rows printed as **"blur r=2"** and **"blur r=5"** are, in the JSON, the rows
  `degrade = "haze_t0.6"` and `degrade = "haze_t0.3"`:
  - `degradation_matrix.marine_bioclip.rows[0]` = `haze_t0.6` (lam_eff 0.021, τ 0.6498, top1 20.149)
    → paper "marine-67 blur r=2 τ 0.650 top-1 20.15".
  - `degradation_matrix.marine_bioclip.rows[1]` = `haze_t0.3` (0.0747, 0.4041, 17.226)
    → paper "marine-67 blur r=5 τ 0.404 top-1 17.23".
  - `degradation_matrix.imagenet_clip.rows[0/1]` = `haze_t0.6` / `haze_t0.3` → paper
    "imagenet-5k blur r=2 / r=5".
  No `blur_*` row exists for `marine_bioclip` or `imagenet_clip` in **any** file of the corpus
  (a full-text scan of all 316 JSONs finds `blur_r1/r2/r4` only in `sonar_frozen`, plus
  `direction_operator.sonar_frozen`, `direction_subspace.sonar_frozen`, `perimage_operator.sonar_frozen`,
  `sonar_degradation.json`, `watertank_protocol.json`). A "blur r=5" condition does not exist at all.
  Aggravating: the *same-named* haze conditions in the primary marine-degradation JSON carry
  **different** values — `ocean_degradation.bioclip.rows[1] haze_t0.60 τ = 0.4803`,
  `rows[2] haze_t0.30 τ = 0.2881` (mirrored in `mechanism_summary.sources.degradation_marine`), which
  are exactly the values `tab:degrad` and `tab:dir-op` report for haze. So the manuscript reports two
  mutually inconsistent numbers for the same named condition (haze t=0.6: τ = 0.480 in `tab:degrad`,
  τ = 0.650 in `tab:degmap`), and the second is relabelled "blur".
  The same mislabelling propagates to `tab:subspace` and `tab:perimage` (§21, §22) and to the prose
  "blur is the most destructive … marine 0.40 at r=5 vs 0.65 at r=2".

→ **73/73 values traceable; 4 rows (12 cells) carry a condition label that no JSON supports. Not fully verified.**

---

## 21. `tab:subspace` (ext_partIV_degradation.tex:70–92)

**Source**: `outputs/direction_subspace.json` (`marine_bioclip[i]`, `sonar_frozen[i]`; keys
`tau_meas`, `err_k1..err_k5`). All 48 numeric cells **direct**:

- marine[0] (haze_t0.6): τ 0.6498, err_k1 0.2572→0.257, k2 0.2369→0.237, k3 0.2188→0.219,
  k4 0.1958→0.196, k5 0.1866→0.187.
- marine[1] (haze_t0.3): 0.4041→0.404, 0.37, 0.3461→0.346, 0.3194→0.319, 0.2994→0.299, 0.2781→0.278.
- marine[2] (shadow_strip): 0.4898→0.490, 0.3718→0.372, 0.333, 0.3075→0.308, 0.2887→0.289, 0.2714→0.271.
- marine[3] (speckle_p20): 0.481, 0.3444→0.344, 0.316, 0.2866→0.287, 0.2687→0.269, 0.25.
- sonar[0..3]: 0.5252/0.4751/0.1843/0.62 with err_k1..k5 exactly as printed (incl. the
  k3→k4 regression 0.1345→0.1437 = **+0.0092 → "+0.009"** ✓).

- Same **D1** label problem on the two marine "blur r=2 / r=5" rows (they are `haze_t0.6`/`haze_t0.3`).
- Prose "the k=5 gain is ≤ 0.09 of error": mean gain over the 8 rows = 0.0899 ✓, but the per-row
  gain reaches **0.136** (sonar speckle 40%: 0.2843−0.148) and 0.130 (sonar speckle 20%), so four of
  eight rows exceed 0.09. Ambiguous phrasing; flagged.
- Prose "residual (0.12–0.28 at k=5)" ✓ (min 0.1191, max 0.2781).

→ **48/48 values verified; 2 rows mislabelled; 1 ambiguous prose claim**

---

## 22. `tab:perimage` (ext_partIV_degradation.tex:127–151)

**Source**: `outputs/perimage_operator.json` (`marine_bioclip[i]`, `sonar_frozen[i]`; keys
`name`, `tau_meas_tauB`, `tau_pred_perimage`, `err_same_def`). All 24 numeric cells **direct and ✓**:
τ = 0.6498 / 0.4041 / 0.4898 / 0.481 (marine) and 0.5252 / 0.4751 / 0.1843 / 0.62 (sonar);
`err_k=5 (shared subspace)` = the `err_k5` values of `direction_subspace.json` (0.187 / 0.278 /
0.271 / 0.250 / 0.160 / 0.148 / 0.139 / 0.119) ✓; `err per-image` = 0.0000 in all eight rows,
because `tau_pred_perimage == tau_meas_tauB` exactly in every row (`err_same_def = 0.0`), i.e.
"prediction equals measurement to four decimals" is verified, though it is exact **by construction**
(the predictor consumes the measured paired displacement).

- Same **D1** label problem on the two marine "blur r=2 / r=5" rows.

→ **24/24 values verified; 2 rows mislabelled**

---

## 23. `tab:qa-layers` (ext_partV_mechanisms.tex:17–37)

**Source**: `outputs/ml16k_qa_layers.json` (`meta.types`, `bioclip.<type>`, `oceanclip.<type>`;
fields `n`, `videoR1`, `videoR5`). All 24 R@1 cells + 8 `n` cells **direct**:

central_object n 426 / 1.408→1.41 / 0.235→0.23; central_object_appearance 426 / 1.408→1.41 / 0.235→0.23;
central_object_motion 290 / 1.379→1.38 / 0.345→0.34; object_detect 426 / 0.939→0.94 / 0.704→0.70;
camera_motion 426 / 0.939→0.94 / 0.0→0.00; caption 426 / 0.235→0.23 / 0.235→0.23;
environment 422 / 0.237→0.24 / 0.0→0.00; lighting 172 / 0.0→0.00 / 0.581→0.58. ✓

**Recomputed** gap multipliers: 1.408/0.235 = 5.99 → **×6** ✓ (×2 rows); 1.379/0.345 = 4.00 → **×4** ✓;
0.939/0.704 = 1.33 → **×1.3** ✓; 0.235/0.235 = 1.00 → **×1** ✓. Chance 1/427 = 0.234% → **0.23%** ✓.

**Unattributed**: none. **Discrepancies**: none. → **32/32 (fully)**

---

## 24. `tab:classlaw` (ext_partV_mechanisms.tex:65–84)

**Sources**: `outputs/ocean_margins.json` (marine-67), `outputs/domain_matrix.json`
(imagenet-1k/DTD/Food101), `outputs/sonar_protocol.json` (sonar-8). All 38 numeric cells **direct**:

BioCLIP marine-67 0.0535 / 0.46331→0.463 / 21.704→21.70 / 76.43→76.4;
BioCLIP imagenet-1k 0.0922 / 0.2529→0.253 / 16.72 / —;
BioCLIP dtd-47 0.0731 / 0.2757→0.276 / 6.18 / 66.28→66.3;
BioCLIP food101-101 0.0439 / 0.3754→0.375 / 4.20 / 57.84→57.8;
CLIP imagenet-1k 0.0730 / 0.2713→0.271 / 59.26 / —;
CLIP dtd-47 0.0232 / 0.2463→0.246 / 43.10 / 68.6;
CLIP food101-101 0.0345 / 0.3866→0.387 / 76.82 / 80.9;
CLIP sonar-8 0.0239 / −0.0225→−0.02 / 16.154→16.15 / —. ✓

Prose "class-set-size sweep N=20/40/67 retention 99.1/98.1/96.7%" ✓ (**recomputed**, §6);
"BioCLIP on ImageNet 0.0922, above its own marine value" ✓.

Note: the NCC column here is again λ=1 for the marine row (76.4) — same convention issue as §18, but
in this table the column is only populated for marine/dtd/food101, where DTD/Food101 use `ncc_0`.

→ **38/38 verified (fully)**

---

# Summary table

| # | Table label | Source JSON | verified / total | Discrepancies |
|---|---|---|---|---|
| 1 | `tab:sonar-exact` | `sonar_protocol_full.json` | 37 / 37 | — |
| 2 | `tab:sonar-sigma` | `sonar_protocol.json`, `sonar_protocol_full.json` | 25 / 25 | — |
| 3 | `tab:sonar-peft` | `sonar_peft.json`, `sonar_peft_ms.json` | 7 / 10 | **D9** sd 36.2 vs 36.07; **D10** sd 0.015 vs 0.0156; **D11** 21.9% vs 21.846 |
| 4 | `tab:spectrum` | `ocean_spectrum.json` | 40 / 40 | — |
| 5 | `tab:portrait` | `ocean_margins/sigma_other/gap_surgery/multiseed/spectrum/n_sweep` + `a1_*` | 37 / 37 | — |
| 6 | `tab:disc` | `ocean_clip2x2/flickrft_sigma/marineft10_sigma/margins/n_sweep` | 28 / 28 | — |
| 7 | `tab:peft` | `ocean_peft_ms.json` | 28 / 30 | last-digit: R@1 sd 0.004 vs 0.0035; retention +5.8% vs +5.73% |
| 8 | `tab:rank1` | `ocean_rank1_bound.json` (+`ocean_margins`) | 32 / 32 | **D8** caption "single violation" is false (SigLIP λ=1 also violates) |
| 9 | `tab:dir-op` | `direction_operator.json` (+`ocean_degradation`) | 24 / 24 | — |
| 10 | `tab:ml16k` | `ocean_ml16k_retrieval.json` | 15 / 15 | — |
| 11 | `tab:watertank` | `watertank_protocol/riku_protocol/uatd_protocol.json` | 40 / 42 | **D2** UATD Δτ +0.009 vs −0.041; **D3** "12/12†" vs 3/6 exact |
| 12 | `tab:replica` | `ocean_replica/bioclip_lora_instruction/ocean_margins/ocean_ml16k_retrieval` | 20 / 20 | — ("120×" vs 118×, rounding) |
| 13 | `tab:monitor` | `ocean_tautraj.json` | 34 / 34 | — |
| 14 | `tab:degrad` | `ocean_degradation.json` | 24 / 24 | — |
| 15 | `tab:eng` | (qualitative) | n/a | — |
| 16 | `tab:calib` | `threshold_calibration.json` | 23 / 24 | **D14** "2,000-fold bootstrap" has no JSON provenance |
| 17 | `tab:theory-stack` | `a1_tau_holdout/text_surgery/theory_verify` | 5 / 5 | 0.520 vs 0.5214 (truncation) |
| 18 | `tab:matrix` | `domain_matrix.json` + marine/sonar/A1 files | ~62 / 66 | **D4** sonar frozen ret 34%; **D5** SonarCLIP ret 99.9%; **D6** BioCLIP-ImageNet "ret" is accuracy; **D7** CLIP-ImageNet retention from a different run; NCC λ convention |
| 19 | `tab:dynamics` | `dynamics_matrix/dynamics_seed/ocean_tautraj/dynamics_fathomnet/vlm_*` | ~32 / 38 | **D12** 4 sd cells; σm@10 0.0066 unattributed; **D13** 50ep row "@10" = epoch 50 |
| 20 | `tab:degmap` | `degradation_matrix.json` | 73 / 73 values | **D1** marine+imagenet `blur r=2/r=5` rows are the JSON's `haze_t0.6/haze_t0.3` |
| 21 | `tab:subspace` | `direction_subspace.json` | 48 / 48 values | **D1** (2 rows); ambiguous "k=5 gain ≤0.09" |
| 22 | `tab:perimage` | `perimage_operator.json` (+`direction_subspace`) | 24 / 24 values | **D1** (2 rows) |
| 23 | `tab:qa-layers` | `ml16k_qa_layers.json` | 32 / 32 | — |
| 24 | `tab:classlaw` | `ocean_margins/domain_matrix/sonar_protocol` | 38 / 38 | — |

---

# Discrepancy register (ordered by severity)

### D1 — Condition labels contradict the JSON (3 tables: `tab:degmap`, `tab:subspace`, `tab:perimage`; plus prose)
- **Paper (exact values)**: `tab:degmap` "marine-67 / blur r=2 → λ_eff +0.021, τ 0.650, top-1 20.15";
  "marine-67 / blur r=5 → +0.075, 0.404, 17.23"; "imagenet-5k / blur r=2 → −0.017, 0.596, 54.32";
  "imagenet-5k / blur r=5 → −0.012, 0.380, 36.12". Same four conditions in `tab:subspace` (§21) and
  `tab:perimage` (§22); prose "marine 0.40 at r=5 vs 0.65 at r=2".
- **JSON**: `outputs/degradation_matrix.json :: marine_bioclip.rows[0].degrade = "haze_t0.6"`,
  `rows[1].degrade = "haze_t0.3"`, `imagenet_clip.rows[0/1]` likewise; and
  `outputs/direction_subspace.json :: marine_bioclip[0].degrade = "haze_t0.6"`,
  `[1].degrade = "haze_t0.3"`; `outputs/perimage_operator.json :: marine_bioclip[0].name = "haze_t0.6"`,
  `[1].name = "haze_t0.3"`. No `blur_*` condition exists for these two domains in any of the 316
  JSON files (blur exists only for `sonar_frozen` as `blur_r1/r2/r4`). The values quoted are the
  `haze_t0.6`/`haze_t0.3` values.
- **Aggravating contradiction**: the same-named haze conditions in
  `outputs/ocean_degradation.json :: bioclip.rows[1].tau_meas = 0.4803` and `rows[2].tau_meas = 0.2881`
  (mirrored at `mechanism_summary.sources.degradation_marine.bioclip.rows[1..2]`) are the values used
  in `tab:degrad`/`tab:dir-op` for haze — so paper_a2 reports τ = 0.480 and τ = 0.650 for the same
  named condition (haze t=0.6), the second under the label "blur r=2".

### D2 — `tab:watertank`, UATD domainft Δτ
- **Paper**: `+0.009`. **JSON**: `outputs/uatd_protocol.json :: domainft.rows[6].tau_meas = 0.1126`
  minus `:: domainft.rows[4].tau_meas = 0.1532` → **−0.0406 (−0.041)**. The other eight Δτ cells in
  the same table reproduce text−image exactly. (`+0.009` = the τ_pred−τ_meas deviation at λ=0.5 of the
  same failed run, 0.8186−0.8095 = 0.0091.)

### D3 — `tab:watertank`, "exact τ = 12/12†" on the UATD domainft row
- **Paper**: 12/12 conditions exact in that row.
  **JSON**: `uatd_protocol.json :: domainft.rows` is exact in **3 of 6** λ
  (λ = −1, −0.5, 0: pred = meas = 1.0); deviations 0.0091 (λ=0.5), 0.0161 (λ=1), 0.0061 (λ=2).
  "12/12" matches the frozen + flickrft rows (6+6), which the caption footnote does describe.

### D4 — `tab:matrix`, sonar-8 CLIP-frozen top-1 retention "34%"
- **Paper**: `34% (λ=1 top-1 5.2/16.2)`. **JSON**: no such retention exists. 5.235 =
  `sonar_protocol_full.json :: clip_frozen.rows[4].top1` (full protocol) but 16.154 =
  `sonar_protocol.json :: clip_frozen.top1_0` (balanced protocol); the mixed ratio is 32.4%.
  Full-protocol retention = 5.235/14.941 = **35.0%**; balanced retention = **100%**.

### D5 — `tab:matrix`, sonar-8 SonarCLIP top-1 retention "99.9%"
- **Paper**: `99.9%`. **JSON**: both protocols give exactly 100%
  (`sonar_protocol.json sonar_ft` 96.769/96.769; `sonar_protocol_full.json sonar_ft_full`
  99.885/99.885). The only 99.9-ish number is the full-protocol zero-shot **accuracy** 99.885
  (`sonar_ft_full.top1_0`) — an accuracy, not a retention, and one that `tab:sonar-sigma` already
  prints correctly as top1₀ = 99.89.

### D6 — `tab:matrix`, imagenet-1k BioCLIP "top-1 ret. 16.7%"
- **Paper**: retention 16.7%. **JSON**: retention = `domain_matrix.json :: imagenet5k.bioclip.rows[4].top1`
  16.14 ÷ `:: imagenet5k.bioclip.top1_0` 16.72 = **96.5%**. The printed 16.7 is the zero-shot
  accuracy (16.72), which ext_partV prints correctly as an accuracy.

### D7 — `tab:matrix`, imagenet-1k CLIP retention mixes two experiments
- **Paper**: σm 0.0730, τ@1 0.271, ret 54.0% in one row.
  **JSON**: σm/τ are `domain_matrix.json :: imagenet5k.clip_tf` (5,000-image subset), whose own
  retention is 33.22/59.26 = **56.1%**; the printed 54.0% is the companion A1 full-ImageNet result
  (`a1_full_results.json :: [11].top1` 32.01 ÷ `[6].top1` 59.28 = 0.5400).

### D8 — `tab:rank1` caption + prose
- **Paper**: "Bold: the **single** violation of the Gaussian bound (OceanCLIP, λ=2)"; prose
  "siglip **0.697 ≥ 0.787** holds by a smaller margin".
  **JSON/table**: `ocean_rank1_bound.json :: siglip.rows["1.0"].exact = 0.7867` vs
  `:: siglip.rows["1.0"].corr_gauss = 0.6969` → SigLIP λ=1 is a **second** violation and the stated
  inequality is false. (Full grid also violates at `bioclip.rows["-1.0"]` 0.5106/0.45,
  `openclip_tf.rows["2.0"]` 0.7929/0.7756, `siglip.rows["2.0"]` 0.8818/0.7498.)

### D9 / D10 / D11 — `tab:sonar-peft`
- **D9**: top-1 sd printed **36.2**; from `sonar_peft.json :: fullft.top1_0 = 96.769`,
  `sonar_peft_ms.json :: fullft__s1.top1_0 = 99.846`, `:: fullft__s99.top1_0 = 21.846` →
  mean 72.820 and sd **36.066** (population; all other sds in the paper use it) — 36.2 matches no convention.
- **D10**: τ sd printed **0.015**; from 0.8957 / 0.8877 / 0.8594 → sd **0.0156** (population) / 0.0191 (sample).
- **D11**: prose "one of three seeds stalls at **21.9%** top-1" vs stored **21.846** (→21.8%).

### D12 / D13 — `tab:dynamics`
- **D12**: sd cells that reproduce under neither the population nor the sample convention —
  CLIP+Sonar τ@1 **±0.200** (computed 0.171 / 0.209), CLIP+Sonar τ@10 **±0.140** (0.112 / 0.137),
  CLIP+Sonar top-1@10 **±1.5** (1.29 / 1.58), BioCLIP+Marine τ@10 **±0.010** (0.0088 / 0.0108);
  and BioCLIP+Marine **σm@10 = 0.0066** where the only two seed trajectories in the corpus
  (`dynamics_seed.json :: bio_marine_s0[9].sigma_m = 0.0054`, `:: bio_marine_s1[9].sigma_m = 0.0081`)
  average **0.0068** (a third seed σm ≈ 0.0063 exists in no JSON; the seed-42 trajectory
  `ocean_tautraj.json :: marine` has no σm field at all).
- **D13**: "CLIP+Sonar 50ep" row prints epoch-**50** values under the "@10" headers —
  τ@10 0.155 = `dynamics_seed.json :: clip_sonar_50ep[49].tau` 0.1548, σm@10 0.0046 =
  `:: clip_sonar_50ep[49].sigma_m`; the JSON's epoch-10 values are τ 0.3166 / σm 0.0062
  (`[9].tau`, `[9].sigma_m`), which the accompanying prose does report correctly.

### D14 — `tab:calib` caption
- **Paper**: "2{,}000-fold bootstrap over points".
  **JSON**: `threshold_calibration.json` stores `n_points = 118`, `cells`, `cutoffs.*.{sensitivity,
  specificity, precision, sens_lo, sens_hi, spec_lo, spec_hi}`. No bootstrap-replicate count exists
  anywhere in the file (no key contains "boot"; the string "2000" does not occur). The CI bounds
  themselves match the paper exactly.

### Rounding-level items (last printed digit; listed for completeness)
- `tab:peft`: OceanCLIP LoRA-text R@1 sd **0.004** vs population **0.0035**
  (`ocean_peft_ms.json oceanclip__lora_text__s{1,42,99}.flickr_R1` = 0.3471/0.3531/0.3449).
- `tab:peft`: BioCLIP LoRA-text retention **+5.8%** vs **+5.73%** (22.948/21.704) / +5.75% (vs 21.70).
- `tab:degmap`: 11.385→**11.38** and 7.385→**7.38** (round-half-even rather than half-up).
- `tab:theory-stack` prose: "against the exact **0.520**" vs `a1_margins.json ::
  predicted_rank1_loss_exact["1"] = 0.5214` (truncation).
- `tab:matrix`/§18 NCC column: marine rows print NCC@λ=1 (76.4 / 62.1) while every other domain
  prints `ncc_0` — two conventions in one column.
- `ext_partIV` prose "the k=5 gain is ≤0.09": mean gain across the 8 rows is 0.0899, but per-row
  gains reach 0.136 (`direction_subspace.json :: sonar_frozen[1]` 0.2843−0.148).
- `tab:replica` prose "120× chance" vs recomputed 118.0 (27.645 / 0.2342).

### Coincidence matches explicitly rejected
`0.815` (78 corpus hits), `0.0673` (280 hits), `0.141` (37 hits), `0.29`/`0.52`/`0.57` (tens of
hits, mostly `a1_margins.pair_samples.*`, i.e. per-pair floats) were each resolved to a *named
experiment key* before being counted; several matches were reached only because the search hit the
thousands-strong `pair_samples` arrays, and those hits were **not** used. Conversely, the values that
were *not* found anywhere (`34`, `99.9`) are reported as unattributed rather than accepted.

---

# Final answer

**(a) Tables fully verified (every number attributed to a named JSON key path, every derived value
recomputed, no contradiction): 15 of 24**

`tab:sonar-exact`, `tab:sonar-sigma`, `tab:spectrum`, `tab:portrait`, `tab:disc`, `tab:peft`*,
`tab:dir-op`, `tab:ml16k`, `tab:replica`, `tab:monitor`, `tab:degrad`, `tab:calib`†,
`tab:theory-stack`, `tab:qa-layers`, `tab:classlaw`.
(* `tab:peft`: two last-digit rounding items only. † `tab:calib`: all 22 statistics verified; the
caption's "2,000-fold" has no provenance — see D14, so strictly 14 fully + 1 with a caption caveat.)
`tab:eng` contains no result-derived numbers (qualitative procedure) and `tab:rank1` has every cell
verified but a false caption claim (D8) — so "15 verified / 1 verified-but-wrong-caption /
1 no-numbers / 7 with unattributed-or-contradictory cells" = 24.

**(b) Tables containing unattributed or non-reproducible numbers: 8**

`tab:matrix` (D4, D5, D6, D7), `tab:sonar-peft` (D9, D10, D11), `tab:watertank` (D2, D3),
`tab:dynamics` (D12, σm 0.0066, D13), `tab:calib` (D14), `tab:degmap` (D1),
`tab:subspace` (D1), `tab:perimage` (D1).

**(c) Every discrepancy found**

| id | paper value | JSON value | JSON path |
|---|---|---|---|
| D1 | `tab:degmap`/`subspace`/`perimage` marine "**blur r=2**" τ 0.650, λ_eff +0.021, top1 20.15 | τ **0.6498**, λ_eff 0.021, top1 20.149, degrade **"haze_t0.6"** | `outputs/degradation_matrix.json :: marine_bioclip.rows[0]` (also `direction_subspace.json :: marine_bioclip[0]`, `perimage_operator.json :: marine_bioclip[0]`) |
| D1 | marine "**blur r=5**" τ 0.404, +0.075, 17.23 | τ **0.4041**, 0.0747, 17.226, degrade **"haze_t0.3"** | `degradation_matrix.json :: marine_bioclip.rows[1]` |
| D1 | imagenet-5k "**blur r=2**" τ 0.596, −0.017, 54.32 | τ **0.596**, −0.0167, 54.32, degrade **"haze_t0.6"** | `degradation_matrix.json :: imagenet_clip.rows[0]` |
| D1 | imagenet-5k "**blur r=5**" τ 0.380, −0.012, 36.12 | τ **0.3798**, −0.0119, 36.12, degrade **"haze_t0.3"** | `degradation_matrix.json :: imagenet_clip.rows[1]` |
| D1b | `tab:degrad`/`tab:dir-op` haze t=0.6 τ **0.480** | τ **0.4803** (same condition name, different value from D1) | `outputs/ocean_degradation.json :: bioclip.rows[1].tau_meas` |
| D2 | `tab:watertank` UATD domainft Δτ **+0.009** | **−0.041** (0.1126 − 0.1532) | `outputs/uatd_protocol.json :: domainft.rows[6].tau_meas` − `:: domainft.rows[4].tau_meas` |
| D3 | `tab:watertank` UATD domainft "exact τ **12/12**" | **3/6** λ exact (deviations 0.0091, 0.0161, 0.0061) | `outputs/uatd_protocol.json :: domainft.rows[*].{tau_pred,tau_meas}` |
| D4 | `tab:matrix` sonar-8 CLIP frozen top-1 ret **34%** | **35.0%** (full) / **100%** (balanced); the cell's pair mixes protocols (32.4%) | `sonar_protocol_full.json :: clip_frozen.rows[4].top1` 5.235 ÷ `:: clip_frozen.top1_0` 14.941; `sonar_protocol.json :: clip_frozen.top1_0` 16.154 |
| D5 | `tab:matrix` sonar-8 SonarCLIP top-1 ret **99.9%** | **100%** (both protocols); 99.885 is the accuracy | `sonar_protocol.json :: sonar_ft.top1_0`/`.rows[4].top1` = 96.769; `sonar_protocol_full.json :: sonar_ft_full.top1_0` 99.885 |
| D6 | `tab:matrix` imagenet-1k BioCLIP top-1 ret **16.7%** | retention **96.5%**; 16.72 is the accuracy | `domain_matrix.json :: imagenet5k.bioclip.rows[4].top1` 16.14 ÷ `:: imagenet5k.bioclip.top1_0` 16.72 |
| D7 | `tab:matrix` imagenet-1k CLIP ret **54.0%** in a row whose σm/τ come from the 5k run | row's own JSON implies **56.1%**; 54.0% comes from the A1 50k run | `domain_matrix.json :: imagenet5k.clip_tf.rows[4].top1` 33.22 ÷ `:: .top1_0` 59.26 = 0.5606; `a1_full_results.json :: [11].top1` 32.01 ÷ `:: [6].top1` 59.28 = 0.5400 |
| D8 | `tab:rank1` caption "the **single** violation of the Gaussian bound"; prose "siglip 0.697≥0.787" | **two** violations in the printed table: SigLIP λ=1 exact **0.7867** > Gaussian **0.6969**; stated inequality is false | `ocean_rank1_bound.json :: siglip.rows["1.0"].exact` / `.corr_gauss` |
| D9 | `tab:sonar-peft` FullFT top-1 **72.8±36.2** | **72.820 ± 36.066** (pop) / 44.172 (sample) | `sonar_peft.json :: fullft.top1_0` 96.769; `sonar_peft_ms.json :: fullft__s1.top1_0` 99.846, `:: fullft__s99.top1_0` 21.846 |
| D10 | `tab:sonar-peft` FullFT τ **0.881±0.015** | **0.8809 ± 0.0156** (pop) / 0.0191 (sample) | `sonar_peft.json :: fullft.tau_l1` 0.8957; `sonar_peft_ms.json :: fullft__s1.tau_l1` 0.8877, `:: fullft__s99.tau_l1` 0.8594 |
| D11 | prose "stalls at **21.9%** top-1" | **21.846%** | `sonar_peft_ms.json :: fullft__s99.top1_0` |
| D12a | `tab:dynamics` CLIP+Sonar τ@1 **±0.200** | **0.171** (pop) / 0.209 (sample) | `dynamics_matrix.json :: clip_sonar[0].tau` 0.2757; `dynamics_seed.json :: clip_sonar_s0[0].tau` 0.36, `:: clip_sonar_s1[0].tau` 0.6729 |
| D12b | CLIP+Sonar τ@10 **±0.140** | **0.112** (pop) / 0.137 (sample) | `dynamics_matrix.json :: clip_sonar[9].tau` 0.3083; `dynamics_seed.json :: clip_sonar_s0[9].tau` 0.1274, `:: clip_sonar_s1[9].tau` 0.3972 |
| D12c | CLIP+Sonar top-1@10 **±1.5** | **1.29** (pop) / 1.58 (sample) | `dynamics_matrix.json :: clip_sonar[9].top1` 96.769; `dynamics_seed.json :: clip_sonar_s0[9].top1` 98.923, `:: clip_sonar_s1[9].top1` 99.846 |
| D12d | BioCLIP+Marine τ@10 **±0.010** | **0.0088** (pop) / 0.0108 (sample) | `dynamics_seed.json :: bio_marine_s0[9].tau` 0.1929, `:: bio_marine_s1[9].tau` 0.1867; `ocean_tautraj.json :: marine[9].tau` 0.1719 |
| D12e | BioCLIP+Marine **σm@10 = 0.0066** | only two seeds exist → **0.0068**; 0.0066 needs an unarchived seed σm ≈ 0.0063 | `dynamics_seed.json :: bio_marine_s0[9].sigma_m` 0.0054, `:: bio_marine_s1[9].sigma_m` 0.0081 |
| D13 | `tab:dynamics` "CLIP+Sonar 50ep" **τ@10 0.155 / σm@10 0.0046** | these are epoch **50** values; epoch 10 = **τ 0.3166 / σm 0.0062** | `dynamics_seed.json :: clip_sonar_50ep[49].tau` 0.1548 / `[49].sigma_m` 0.0046 vs `[9].tau` 0.3166 / `[9].sigma_m` 0.0062 |
| D14 | `tab:calib` caption "**2,000-fold** bootstrap" | no such field; only `n_points = 118` and the CI bounds | `threshold_calibration.json` (keys: `n_points`, `cells`, `cutoffs`) |

Primary output: `docs/A23_TABLE_TRACE.md`. Temporary audit scripts: `tools/_tmp_a23_jsonmap.py`,
`_tmp_a23_dump.py`, `_tmp_a23_rows*.py`, `_tmp_a23_index.py`, `_tmp_a23_recompute.py`,
`_tmp_a23_files.json`, `_tmp_a23_index.json`.
