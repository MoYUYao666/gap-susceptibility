# Competing models by stratum (local, 2026-10-27)

Companion to `paperA_competing_models_cv.json`. Pooling 829 trajectories hides which family carries the result, so the
same 5-fold cross-validation was rerun inside each family and rank stratum. Strata with fewer than 20 trajectories are
marked `thin` and may not carry a conclusion on their own.

Pooled: median CV R2 ODE **0.448** vs power law 0.351 (gap **+0.097**).

| family | n | usability | ODE - power | ODE R2 | power R2 |
|---|---|---|---|---|---|
| unknown | 682 | ok | +0.131 | 0.468 | 0.338 |
| clip | 80 | ok | +0.139 | 0.633 | 0.494 |
| siglip | 57 | ok | +0.488 | -0.359 | -0.847 |
| dinov2 | 6 | thin | +0.031 | 0.806 | 0.775 |
| vit | 4 | thin | +0.011 | 0.030 | 0.019 |

Reading: the ODE advantage is positive in every stratum, so the pooled result is not produced by one family; the SigLIP
stratum is where it is largest (+0.488), but it is also the stratum with the most dynamic gap behaviour. The two thin
strata (dinov2, vit) are reported for completeness only.
