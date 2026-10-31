# Local upgrade batch, 2026-10-27 (CPU only, no cloud)

Five work items were requested and all five are done locally. Nothing in this batch touched the frozen v1.0 package;
the revision is a separate directory built from the same sources plus the additions below.

## A1 Theory hardness (resolved)
`tools/_p1768_theory_checks.py` -> `outputs/analysis/paperA_theory_hardness_checks.json`,
write-up `docs/PaperA_theory_hardness_checks.md`.

- the projection-based ordering and the block-norm ordering disagree on **25.6%** of 4000 generic two-block
  configurations, so R3' is load-bearing;
- the tempting weakening is **refuted**: `sum_k n_k + 1.7 (x1.x2)^2` is additive on `{x1.x2 = 0}` (gap 0.0) but differs
  off it (1.70 and 0.27), so additivity on a closed measure-zero subclass plus continuity does not restore uniqueness;
- the true weakening is open-set additivity plus continuity (a continuous function vanishing on an open set vanishes
  identically); the numerical check finds the coupling deviation at **0 of 2000** points inside a ball.

## A2 Competition, out of sample
`tools/_p1767b_cv_compare.py` -> `outputs/analysis/paperA_competing_models_cv.json`.
Five-fold CV over epochs on **813** trajectories (>=5 epochs), median held-out numbers:

| model | median CV R2 | median CV MAE | wins (lowest CV MAE) | mean AIC |
|---|---|---|---|---|
| constant | -0.321 | 0.0294 | 182 | -59.2 |
| linear | 0.144 | 0.0188 | 288 | -66.1 |
| power law | 0.353 | 0.0178 | 42 | -70.1 |
| **ODE** | **0.464** | **0.0153** | **301** | **-74.1** |

Paired power-law-minus-ODE held-out MAE: **+0.00324** (t=20.8, p=3.2e-77, n=813) -> the ODE advantage survives out of sample.

## A3 Pre-registration statistics
`outputs/analysis/paperA_prereg_stats.json`: per-backbone means with 95% CI over five seeds, paired text-only vs
vision-only contrasts and Cohen's d. CLIP B/32: text-only -0.0380 +- 0.0024, vision-only +0.0192 +- 0.0041, contrast -0.0572
(t=-31.3, d=-14.0). CLIP B/16 reproduces the sign (-0.0234). OpenCLIP B/32: text-only +0.0716 +- 0.0071, i.e. the gap widens on
every arm; the arm ordering still separates text-only from vision-only (-0.0213, t=-8.3, p=0.0011).

## A4 Figures
`tools/_p1769_upgrade_a4_figures.py` -> `paper合/figures/fig_prereg_cross_backbone.pdf` and
`fig_competing_models_cv.pdf`; both verified with `pdffonts`: TimesNewRomanPSMT + STIXGeneral, CID TrueType, no Type 3.

## A5 Revision package
Built with `ML_PKG_DIR=SUBMISSION/PaperA_MachineLearning_revision` (the builder now accepts that override and reads
cover sources from the canonical directory). Result: **57 pages** (v1.0 was 55), 0 errors, 0 undefined, 0 overfull,
flat zip round-trip identical, upload names underscore-free, 25 hashes consistent. New material in the PDF is verified
present: the five-fold CV paragraph, the resolved R3' section, the pre-registered CI/effect-size paragraph, and both
figure captions.

## What is still not done
- P3 (SigLIP) arms: still deferred; the local 8 GB GPU could only run them at reduced batch size and the earlier
  device-side assert has not been re-tested after the mask fix;
- (1) cross-modal CLAP measurement: script ready, not run.
