# Additivity: what R3' buys, formally

Written for the revision. All numerical claims below are produced by `tools/_p1768_theory_checks.py`
(archive `outputs/analysis/paperA_theory_hardness_checks.json`, 4000 draws, seed 20261027).

## Setting

Energy `E: R^{d1} x R^{d2} -> R`, block gradients `g_k = dE/dx_k`, unit direction `u` with block components `u_k`, and
per-block susceptibility `Gamma_k = <g_k, u_k>`. The paper's requirements R1, R2, R4, R5 plus **R3' (additivity)**
single out `S = c * sum_k Gamma_k^2`; the question is how much R3' buys.

## Proposition 1 (the block-norm statistic is not a function of Gamma)

Let `N(x) = sum_k |g_k|^2`. If `N = c * sum_k Gamma_k^2` for all `x` and some constant `c > 0`, then `cos^2 phi_k` must be
the same for every block at every configuration. Proof: write `|g_k|^2 = Gamma_k^2 / cos^2 phi_k`
with `cos phi_k = <g_k, u_k> / |g_k|`; equality for all configurations forces `cos^2 phi_k` to be the same constant for
every `k` and every `x`. This fails for the two-block quadratic family `E = 1/2|x_1|^2 + 1/2|x_2|^2 + eps x_1^T x_2`
at generic configurations: the numerical check finds the two orderings disagree on **26%** of 4000 random draws, so no
monotone transform of `N` reproduces the ordering produced by `Gamma`. R3' therefore is not redundant: it is what makes
the ordering well defined.

## Proposition 2 (open-set additivity suffices, hence is the weakest useful form)

Let `S` and `s_k` be continuous on a nonempty open set `U`. If `S(x) = sum_k s_k(x_k)` for all `x` in `U`, then the same
identity holds for every `x`. Proof: the difference `S(x) - sum_k s_k(x_k)` is continuous and vanishes on `U`; a
continuous function that vanishes on a nonempty open set vanishes identically. Consequently R3' can be replaced by
additivity on any nonempty open set of configurations - strictly weaker than assuming it everywhere - with continuity.

## Proposition 3 (additivity on the closed subclass is not enough)

Additivity on the closed measure-zero subclass `D = {x : x_1^T x_2 = 0}` plus continuity does **not** restore uniqueness.
Counterexample: `S_lam = sum_k |g_k|^2 + lam (x_1^T x_2)^2` with `lam = 1.7` is continuous, and on `D` it equals the
separable statistic `sum_k |g_k|^2` exactly (the coupling term vanishes there), yet off `D` it differs from it (numerical
check: gap 0.00e+00 on `D`, 1.70 and 0.27 at the two off-`D` test points). Hence the natural weakening "assume additivity
only for block-orthogonal perturbations" is false as a route to uniqueness.

## Corollary

R3' cannot be weakened by restricting additivity to a measure-zero subclass, and it can be weakened to additivity on
nonempty open sets. Both statements are cheap to state and check, and together they convert "we assume additivity" into a
characterised boundary.
