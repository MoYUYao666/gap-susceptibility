# Robustness of the two headline statistics (local, 2026-10-27)

## (5) DG vs R@1: nothing is carried by one family

Archive `outputs/analysis/dg_r1_reproducible.json`, n = 204. Pooled r(DG, R@1) = **-0.714**, r(CG, R@1) = -0.594, partial
r(DG, R@1 | CG) = -0.581. Bootstrap 2000 resamples: DG [-0.788, -0.639], CG [-0.669, -0.517].

Leave-one-family-out (each row excludes all runs of that family):

| excluded family | n excluded | r(DG, R@1) | r(CG, R@1) |
|---|---|---|---|
| blip2 | 5 | -0.746 | -0.611 |
| coco | 7 | -0.686 | -0.605 |
| flickr30k | 29 | -0.675 | -0.534 |
| flickr30k_seeds | 20 | -0.699 | -0.571 |
| imagenet_zs | 3 | -0.715 | -0.594 |
| phase1 | 7 | -0.701 | -0.588 |
| route_c | 8 | -0.724 | -0.606 |
| route_d | 5 | -0.719 | -0.600 |
| route_e | 3 | -0.722 | -0.602 |
| siglip | 5 | -0.720 | -0.603 |
| theory | 110 | -0.815 | -0.669 |
| vitl | 2 | -0.706 | -0.585 |

The association survives every exclusion, which is what the manuscript needs: it is not an artefact of LLaVA, CLIP or any
single family.

## (6) How much of the pre-registered effect is structural

One-way ANOVA of DeltaCG across the three adaptation sites, per backbone, with five seeds per site:

| backbone | seeds/site | eta^2 (site) | F | p | max seed sd |
|---|---|---|---|---|---|
| CLIP B/32 | 5 | 0.965 | 167.3 | 1.7e-09 | 0.0078 |
| OpenCLIP B/32 | 5 | 0.872 | 40.9 | 4.4e-06 | 0.0057 |
| CLIP B/16 | 5 | 0.974 | 224.7 | 3.1e-10 | 0.0057 |

A high eta^2 means the between-site spread dominates the seed noise, i.e. the ordering is structural rather than sampling
noise. The seed standard deviations are reported next to it so the claim stays falsifiable.
