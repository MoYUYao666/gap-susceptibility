# A23 — Verification re-audit of `paper_a2/` after the numerical corrections

**Engagement**: read-only verification re-audit of the manuscript in `paper_a2/` (target journal
*Ocean Engineering*) after the round of corrections that followed `docs/A23_TABLE_TRACE.md`
(discrepancy register D1–D14). Scope is bounded: the five corrections named in the task brief plus a
scan for inconsistencies introduced by those edits.

**Rule applied**: a number is *verified* only when the specific JSON file **and key path** are named
and the value read from it; derived quantities (ratios, means, standard deviations) are recomputed
here and the arithmetic is shown. No corpus-wide "the value appears somewhere" matching was used.

**Files touched**: none of the manuscript or result files was modified. This report
(`docs/A23_REAUDIT.md`) is the only file written.

**Corpus read**: `outputs/degradation_matrix.json`, `direction_subspace.json`,
`perimage_operator.json`, `ocean_degradation.json`, `uatd_protocol.json`, `watertank_protocol.json`,
`riku_protocol.json`, `sonar_protocol.json`, `sonar_protocol_full.json`, `domain_matrix.json`,
`ocean_spectrum.json`, `sonar_spectrum.json`, `ocean_rank1_bound.json`, `dynamics_matrix.json`,
`dynamics_seed.json`, `ocean_tautraj.json`, `a1_full_results.json`, `threshold_calibration.json`,
`sonar_peft.json`, `sonar_peft_ms.json`, plus a token scan of every `outputs/**/*.json`.

---

## 1. Required correction checks — PASS/FAIL

### 1a. `tab:degmap` / `tab:subspace` / `tab:perimage` — haze relabelling

| # | Check | Paper value | JSON evidence (file :: key path = value) | Verdict |
|---|---|---|---|---|
| A1 | `tab:degmap` marine rows relabelled | `marine-67 haze t=0.6` / `haze t=0.3` | `degradation_matrix.json :: marine_bioclip.rows[0].degrade = "haze_t0.6"`; `:: marine_bioclip.rows[1].degrade = "haze_t0.3"` | **PASS** |
| A2 | `tab:degmap` ImageNet rows relabelled | `imagenet-5k haze t=0.6` / `haze t=0.3` | `degradation_matrix.json :: imagenet_clip.rows[0].degrade = "haze_t0.6"`; `:: rows[1].degrade = "haze_t0.3"` | **PASS** |
| A3 | `tab:subspace` rows relabelled | `marine haze t=0.6` / `haze t=0.3` | `direction_subspace.json :: marine_bioclip[0].degrade = "haze_t0.6"`; `:: [1].degrade = "haze_t0.3"` | **PASS** |
| A4 | `tab:perimage` rows relabelled | `marine haze t=0.6` / `haze t=0.3` | `perimage_operator.json :: marine_bioclip[0].name = "haze_t0.6"`; `:: [1].name = "haze_t0.3"` | **PASS** |
| A5 | No marine/ImageNet row in **any** of the three tables is labelled blur | — (no blur rows in the optical blocks of `ext_partIV_degradation.tex`) | Only 8 of 316 JSONs contain the token `blur`, and every occurrence is under a sonar path: `degradation_matrix.json :: sonar_frozen.rows[3..5].degrade = blur_r1/blur_r2/blur_r4`; `direction_subspace.json :: sonar_frozen[2]`; `perimage_operator.json :: sonar_frozen[2]`; `mechanism_summary.json :: sources.degradation_sonar.rows[2]`; `sonar_degradation.json :: rows[2]`; `watertank_protocol.json :: deg_*[1]` | **PASS** |
| A6 | `tab:degmap` caption consistent with the relabelled rows (incl. the two-haze-instantiation note) | `λ_eff 0.021`, `τ 0.650` (map) vs `λ_eff 0.0005`, `τ 0.480` (real-degradation protocol) | `degradation_matrix.json :: marine_bioclip.rows[0].{lam_eff 0.021, tau_meas 0.6498}`; `ocean_degradation.json :: bioclip.rows[1].{degrade "haze_t0.60", lam_eff 0.0005, tau_meas 0.4803}` | **PASS** |
| A7 | "Three laws" paragraph consistent with the relabelled rows | law (ii): "in the optical domains the most destructive condition is thick haze (τ 0.40 marine … at t=0.3)" | `degradation_matrix.json :: marine_bioclip.rows[4]` (`speckle_p40`) `tau_meas 0.3322`, `top1 15.734`, `rel_top1_loss 0.2751` — more destructive than `rows[1]` (`haze_t0.3`) `0.4041 / 17.226 / 0.2063` | **FAIL** |

### 1b. `tab:watertank` (main.tex)

| # | Check | Paper value | JSON evidence (file :: key path = value) | Verdict |
|---|---|---|---|---|
| A8 | UATD domainft Δτ | `−0.041` | `uatd_protocol.json :: domainft.rows[6].tau_meas 0.1126` − `:: domainft.rows[4].tau_meas 0.1532` = **−0.0406 → −0.041** | **PASS** |
| A9 | UATD domainft exact τ | `3/6†` | `uatd_protocol.json :: domainft.rows[0..2].tau_pred == tau_meas` at λ = −1, −0.5, 0 (all 1.0); deviations at λ = 0.5/1/2: 0.8186−0.8095 = 0.0091, 0.1532−0.1371 = 0.0161, −0.9248−(−0.9187) = 0.0061 → **3 of 6** | **PASS** |
| A10 | No other Δτ cell in that table changed (all nine recomputed as `rows[6].tau_meas − rows[4].tau_meas`) | `+0.028 / +0.017 / +0.015`; `+0.026 / +0.053 / +0.002`; `+0.054 / +0.189 / −0.041` | `watertank_protocol.json`: frozen −0.079−(−0.1074) = 0.0284→**0.028**; flickrft 0.3807−0.3642 = 0.0165→**0.017**; domainft 0.8091−0.7943 = 0.0148→**0.015**. `riku_protocol.json`: −0.299−(−0.3252) = 0.0262→**0.026**; 0.0612−0.0087 = 0.0525→**0.053**; 0.7913−0.7893 = 0.0020→**0.002**. `uatd_protocol.json`: 0.1706−0.1171 = 0.0535→**0.054**; 0.0685−(−0.1202) = 0.1887→**0.189**. Only the UATD-domainft cell changed | **PASS** |

### 1c. `tab:matrix` (ext_partII_domains.tex)

| # | Check | Paper value | JSON evidence (file :: key path = value) | Verdict |
|---|---|---|---|---|
| A11 | sonar-8 CLIP frozen top-1 retention | `35%` (`λ=1` top-1 `5.2/14.9`) | `sonar_protocol_full.json :: clip_frozen.rows[4].top1 5.235` ÷ `:: clip_frozen.top1_0 14.941` = 0.35038 → **35%**; parenthetical now same-protocol (full 2,617) | **PASS** |
| A12 | sonar-8 SonarCLIP top-1 retention | `100%` | `sonar_protocol.json :: sonar_ft.rows[4].top1 96.769` ÷ `:: sonar_ft.top1_0 96.769` = 1.0000 → **100%** | **PASS** |
| A13 | imagenet-1k CLIP top-1 retention | `56.1%` | `domain_matrix.json :: imagenet5k.clip_tf.rows[4].top1 33.22` ÷ `:: imagenet5k.clip_tf.top1_0 59.26` = 0.56058 → **56.1%** | **PASS** |
| A14 | imagenet-1k BioCLIP top-1 retention | `96.5%` | `domain_matrix.json :: imagenet5k.bioclip.rows[4].top1 16.14` ÷ `:: imagenet5k.bioclip.top1_0 16.72` = 0.96531 → **96.5%** | **PASS** |
| A15 | NCC column now uses λ=0 values | marine-67 BioCLIP `78.4`, OceanCLIP `66.4`; sonar SonarCLIP `96.8` | `ocean_spectrum.json :: bioclip.rows[0].NCC 78.358` (λ=0), `:: oceanclip.rows[0].NCC 66.418` (λ=0); `sonar_spectrum.json :: sonar_ft.rows[0].NCC 96.769`; `domain_matrix.json :: dtd.*.ncc_0` 68.6/75.74/79.36/66.28 and `:: food101.*.ncc_0` 80.9/81.96/89.36/57.84 | **PASS** |
| A16 | Caption states the NCC convention | "NCC: nearest-class-centroid accuracy (centroids frozen) at λ=0" | as A15 — all quoted NCC values are the λ=0 rows / `ncc_0` keys (the former λ=1 values 76.43 / 62.065 are gone) | **PASS** |

### 1d. `tab:rank1` (main.tex) and `tab:dynamics` (ext_partIII_dynamics.tex)

| # | Check | Paper value | JSON evidence (file :: key path = value) | Verdict |
|---|---|---|---|---|
| A17 | `tab:rank1` caption no longer claims a single violation | caption: "Bold: **violations** of the Gaussian bound (OceanCLIP, λ=2; SigLIP, λ=1)"; prose: "seven of the 32 grid cells" | `ocean_rank1_bound.json` enumerates 4 families × 8 λ = **32** cells; `exact > corr_gauss` holds exactly **7** times: `bioclip.rows["-1.0"] 0.5106/0.45`, `bioclip.rows["-0.5"] 0.3128/0.2788`, `bioclip.rows["-0.25"] 0.158/0.15`, `oceanclip.rows["2.0"] 0.556/0.5178`, `openclip_tf.rows["2.0"] 0.7929/0.7756`, `siglip.rows["1.0"] 0.7867/0.6969`, `siglip.rows["2.0"] 0.8818/0.7498` | **PASS** |
| A18 | `tab:rank1` listed cells match that count exactly | prose list: OceanCLIP λ=2 (0.556/0.518); SigLIP λ=1,2 (0.787/0.882 vs 0.697/0.750); OpenCLIP λ=2 (0.793/0.776); BioCLIP λ=−1,−0.5,−0.25 (0.511/0.313/0.158 vs 0.450/0.279/0.150) | same seven key paths as A17 — family, λ, exact and Gaussian values all agree to the printed digits (7 = 1+2+1+3) | **PASS** |
| A19 | `tab:dynamics` "CLIP+Sonar 50ep" row shows its **own** epoch-1/epoch-10 values | `0.276 / 0.317 / 0.0104 / 0.0062 / 67.8` | `dynamics_seed.json :: clip_sonar_50ep[0].{tau 0.2757, sigma_m 0.0104}`; `:: clip_sonar_50ep[9].{tau 0.3166, sigma_m 0.0062, top1 67.846}` (epoch-50 values `[49].{tau 0.1548, sigma_m 0.0046}` are **not** in the table) | **PASS** |
| A20 | Running text reports the epoch-50 values | "σm 0.0062 at ep10 → 0.0046 at ep50"; "τ 0.317 at ep10 → 0.155 at ep50"; top-1 reaches 100% | `dynamics_seed.json :: clip_sonar_50ep[49].{sigma_m 0.0046, tau 0.1548, top1 100.0}` | **PASS** |
| A21 | Every `±` cell equals the **sample** sd (n−1) over the caption's seed sets | BioCLIP+Marine `0.178±0.008`, `0.184±0.011`, `0.0092±0.002`, `0.0068±0.002`, `99.9±0.1`; CLIP+Sonar `0.436±0.209`, `0.278±0.138`, `0.0094±0.009`, `0.0050±0.001`, `98.5±1.6` | 9 of 10 cells match (arithmetic in §3); **CLIP+Sonar τ@10** `dynamics_matrix.json :: clip_sonar[9].tau 0.3083`, `dynamics_seed.json :: clip_sonar_s0[9].tau 0.1274`, `:: clip_sonar_s1[9].tau 0.3972` → sd(n−1) = **0.137489 → 0.137**, not `0.138` | **FAIL** |

**Subtotal — required checks: 21 rows, 19 PASS / 2 FAIL.**

---

## 2. Additional inconsistencies found by the open-ended scan

These are *not* among the five mandated corrections; they are residual or newly visible issues in the
edited passages.

| # | Finding | Paper value | JSON value (key path) | Severity (all FAIL) |
|---|---|---|---|---|
| B1 | `tab:rank1` prose: weak bound "valid in all 32 conditions but … (values **1.1–5.5** …)" | `1.1–5.5` (and "only meaningful where τ̄ ≳ 0.8") | 28 finite cells of `ocean_rank1_bound.json :: *.rows[*].weak_bound` span **0.801 – 5.471**; the two cells with τ̄ ≥ 0.8 are exactly the two *smallest*: `oceanclip.rows["-0.25"].weak_bound 0.801`, `:: oceanclip.rows["0.25"].weak_bound 0.962` | medium |
| B2 | `tab:matrix` sonar-8 "CLIP frozen" row still mixes protocols while its caption claims "identical protocol" | σm `0.0239`, τ@λ=1 `−0.02` (balanced 650) **with** retention `35%` (full 2,617) | `sonar_protocol.json :: clip_frozen.{sigma_m 0.0239, rows[4].tau_meas −0.0225}` vs `sonar_protocol_full.json :: clip_frozen.{sigma_m 0.0247, rows[4].tau_meas −0.0807, rows[4].top1 5.235, top1_0 14.941}`; the companion SonarCLIP row is balanced (`sonar_protocol.json :: sonar_ft`) | medium |
| B3 | `tab:calib` caption still claims a bootstrap replicate count (register D14 — the one discrepancy not corrected) | "2{,}000-fold bootstrap over points" | `threshold_calibration.json` top-level keys are exactly `n_points` (118), `cells`, `cutoffs`; the strings `boot` and `2000` do not occur anywhere in the file | medium |
| B4 | Cross-table sd convention is now split | `tab:dynamics` uses sample sd (n−1) per its caption; `tab:sonar-peft` uses the population sd without saying so | FullFT top-1 (96.769, 99.846, 21.846): pop sd = **36.0662 → 36.1** (paper `72.8±36.1`), sample sd = 44.1719. τ (0.8957, 0.8877, 0.8594): pop = **0.015572 → 0.016** (paper `0.881±0.016`), sample = 0.019073. Keys: `sonar_peft.json :: fullft.{top1_0, tau_l1}`, `sonar_peft_ms.json :: fullft__s1.*, :: fullft__s99.*` | low (each table is internally consistent) |
| B5 | `tab:dynamics` §(i): "sonar-matched spread over **0.13–0.67**" at epoch 1 | `0.13–0.67` | Over the six direction–seed pairs the caption names, epoch-1 τ spans **0.1715–0.6729 → 0.17–0.67** (`dynamics_seed.json :: bio_marine_s0[0].tau 0.1867`, `:: bio_marine_s1[0].tau 0.1715`, `ocean_tautraj.json :: marine[0].tau 0.1765`, `dynamics_matrix.json :: clip_sonar[0].tau 0.2757`, `dynamics_seed.json :: clip_sonar_s0[0].tau 0.36`, `:: clip_sonar_s1[0].tau 0.6729`). The value 0.13 comes only from the **excluded** collapsed fourth seed: `dynamics_seed.json :: clip_sonar_s99[0].tau 0.132` | low |
| B6 | `tab:dynamics` caption: "the σm columns aggregate **the two seeds** for which σm was archived" | generic claim covering both ±-rows | True for BioCLIP+Marine (`ocean_tautraj.json :: marine[*]` has no `sigma_m` key; only `dynamics_seed.json :: bio_marine_s0[9].sigma_m 0.0054`, `:: bio_marine_s1[9].sigma_m 0.0081` exist → mean 0.00675 ≈ 0.0068, sd(n−1) 0.001909 ≈ 0.002). False for CLIP+Sonar, whose σm cells use **three** archived seeds (`dynamics_matrix.json :: clip_sonar[9].sigma_m 0.0063`, `dynamics_seed.json :: clip_sonar_s0[9].sigma_m 0.0037`, `:: clip_sonar_s1[9].sigma_m 0.0051` → mean 0.00503 ≈ 0.0050, sd(n−1) 0.001301 ≈ 0.001) | low |

**Subtotal — additional findings: 6, all FAIL-grade (severities above).**

---

## 3. Recomputations shown (item 5)

Caption seed sets: BioCLIP+Marine = {`bio_marine_s0`, `bio_marine_s1`, `ocean_tautraj.json::marine`};
CLIP+Sonar = {`dynamics_matrix.json::clip_sonar` (s42), `clip_sonar_s0`, `clip_sonar_s1`};
`clip_sonar_s99` deliberately excluded.

| cell | values used | mean (paper) | sd(n−1) (paper) | verdict |
|---|---|---|---|---|
| BioCLIP+Marine τ@1 | 0.1867, 0.1715, 0.1765 | 0.178233 → **0.178** | 0.007747 → **0.008** | OK |
| BioCLIP+Marine τ@10 | 0.1929, 0.1867, 0.1719 | 0.183833 → **0.184** | 0.010790 → **0.011** | OK |
| BioCLIP+Marine σm@1 | 0.0078, 0.0106 | 0.009200 → **0.0092** | 0.001980 → **0.002** | OK |
| BioCLIP+Marine σm@10 | 0.0054, 0.0081 | 0.006750 → **0.0068** | 0.001909 → **0.002** | OK (also closes D12e: the mean is the two-seed 0.0068, not 0.0066) |
| BioCLIP+Marine top-1@10 | 100.0, 99.813, 100.0 | 99.937667 → **99.9** | 0.107965 → **0.1** | OK |
| CLIP+Sonar τ@1 | 0.2757, 0.36, 0.6729 | 0.436200 → **0.436** | 0.209277 → **0.209** | OK (closes D12a) |
| CLIP+Sonar τ@10 | 0.3083, 0.1274, 0.3972 | 0.277633 → **0.278** | Σ(x−x̄)² = 0.0378067; /2 = 0.0189033; √ = **0.137489 → 0.137** | **paper prints 0.138 — last-digit mismatch** (0.138 needs sd ≥ 0.1375; pop sd here is 0.112260) |
| CLIP+Sonar σm@1 | 0.0104, 0.0003, 0.0174 | 0.009367 → **0.0094** | 0.008597 → **0.009** | OK |
| CLIP+Sonar σm@10 | 0.0063, 0.0037, 0.0051 | 0.005033 → **0.0050** | 0.001301 → **0.001** | OK |
| CLIP+Sonar top-1@10 | 96.769, 98.923, 99.846 | 98.512667 → **98.5** | 1.579007 → **1.6** | OK (closes D12c) |

D12b (τ@10 ±0.140) is also closed by the same recomputation: sd(n−1) = 0.137 (pop 0.112).

---

## 4. Observations — checked but *not* discrepancies

1. `tab:degmap` prints `---` in the rel. loss column for all ten marine/ImageNet rows although
   `degradation_matrix.json` stores the values (e.g. `:: marine_bioclip.rows[4].rel_top1_loss 0.2751`,
   `:: imagenet_clip.rows[1].rel_top1_loss 0.3905`). Omission, not a wrong number — but it hides the
   very datum that contradicts law (ii) (finding A7 above).
2. `tab:degmap` caption "every condition has |λ_eff| ≤ 0.11" vs the printed cell `0.111`
   (`degradation_matrix.json :: marine_bioclip.rows[4].lam_eff 0.1108`): true for the unrounded value.
3. `tab:degmap` caption wording "the two optical rows per domain are the two haze levels" is stale
   after the relabel (each optical domain now has five rows, two of them haze).
4. `tab:watertank` prints "---" for the UATD-domainft flattening although the definition in the
   caption would give 0.0176 / 0.0002 = 88× (`uatd_protocol.json :: frozen.sigma_m 0.0176`,
   `:: domainft.sigma_m 0.0002`); defensible for a collapsed run, but the caption's convention
   (`---` only for frozen rows) is not stated.
5. The same model/dataset pair now appears with two different retentions: `tab:matrix`
   "imagenet-1k (5k) CLIP" 56.1% (`domain_matrix.json :: imagenet5k.clip_tf.rows[4].top1 33.22` ÷
   `:: top1_0 59.26`) and `tab:portrait` "CLIP (ImageNet)" 54.0%
   (`a1_full_results.json :: [11].top1 32.01` ÷ `:: [6].top1 59.28`), with matching but likewise
   different σm (0.0730 vs 0.067) and τ@1 (0.271 vs 0.289). Both are JSON-consistent within their
   own protocol; a reviewer will need the "(5k)" marker to be unmistakable.
6. `ext_partV` procedure item 5 "Δτ: 0.246 → 0.007 marine, 0.058 → 0.006 sonar" is traceable to the
   **full** sonar protocol (`sonar_protocol_full.json :: clip_frozen.rows[6].tau_meas −0.0228`
   − `rows[4].tau_meas −0.0807` = +0.0579; `:: sonar_ft_full` 0.7261 − 0.7202 = +0.0059). The
   balanced protocol gives +0.0523 / +0.0031; no table prints these, so nothing contradicts — but the
   protocol is not named.
7. Chinese mirrors (`main_zh.tex`, `zh_ext_partII/III/IV`) carry the identical corrected numbers,
   including both FAILs (A7's "most destructive = thick haze" claim is mirrored in
   `zh_ext_partIV_degradation.tex`; `±0.138` is mirrored in `zh_ext_partIII_dynamics.tex`) and the
   B1 weak-bound range `1.1–5.5` in `main_zh.tex`. D14's "2,000-fold" also survives in the mirror.

---

## 5. Totals

| group | checks | PASS | FAIL |
|---|---|---|---|
| §1 required correction checks (A1–A21) | 21 | 19 | 2 |
| §2 additional residual inconsistencies (B1–B6) | 6 | 0 | 6 |
| **total** | **27** | **19** | **8** |

**Every FAIL, one line each**

1. **A7** — `tab:degmap` law (ii) calls thick haze the most destructive optical condition (`τ 0.40`
   marine) while the table's own marine `speckle 40%` row is more destructive on every recorded
   metric (`degradation_matrix.json :: marine_bioclip.rows[4]`: τ 0.3322, top-1 15.734, rel. loss
   0.2751 vs `rows[1]` haze t=0.3: 0.4041 / 17.226 / 0.2063).
2. **A21** — `tab:dynamics` CLIP+Sonar τ@10 prints `±0.138`; the sample sd (n−1) of 0.3083 / 0.1274 /
   0.3972 is 0.137489 → **0.137**.
3. **B1** — `tab:rank1` prose gives the weak bound as "values 1.1–5.5" over the 32-cell grid; the
   finite `weak_bound` values span **0.801–5.471** (`ocean_rank1_bound.json ::
   oceanclip.rows["-0.25"] 0.801`, `:: siglip.rows["2.0"] 5.471`).
4. **B2** — `tab:matrix` sonar-8 CLIP frozen row mixes the balanced-650 cells (σm 0.0239, τ −0.02)
   with the full-2,617 retention (35%) although the caption says "identical protocol".
5. **B3** — `tab:calib` caption still claims a "2,000-fold bootstrap" that
   `threshold_calibration.json` does not contain (keys: `n_points` 118, `cells`, `cutoffs`) — the
   uncorrected register item D14.
6. **B4** — the paper's `±` convention is now split: `tab:dynamics` sample sd (n−1) vs
   `tab:sonar-peft` population sd (`72.8±36.1` = pop 36.0662; `0.881±0.016` = pop 0.015572; sample
   would be 44.17 / 0.0191), undeclared in the latter.
7. **B5** — `tab:dynamics` §(i) "sonar-matched spread over 0.13–0.67" at epoch 1 is 0.17–0.67 over
   the six direction–seed pairs the caption names; 0.13 is `dynamics_seed.json ::
   clip_sonar_s99[0].tau 0.132`, the deliberately excluded collapsed seed.
8. **B6** — `tab:dynamics` caption "the σm columns aggregate the two seeds for which σm was archived"
   holds only for BioCLIP+Marine; the CLIP+Sonar σm cells average three archived seeds
   (`clip_sonar[9].sigma_m 0.0063`, `clip_sonar_s0[9] 0.0037`, `clip_sonar_s1[9] 0.0051`).
