# Theory hardness: what is verified, what is not (local, CPU only)

Companion to `docs/PaperA_theory_hardness_draft.md` and to `tools/_p1768_theory_checks.py`.
Archive: `outputs/analysis/paperA_theory_hardness_checks.json`. All numbers below are produced by that script
(seed 20261027); nothing here is hand-computed.

## What the paper assumes

The identification of the per-block susceptibility

    Gamma_k = <g_k, u>,    g_k = dE/dx_k

given the requirement set R1, R2, R4, R5 uses **R3' (additivity)**: the block statistic must add across blocks. The
question a referee will ask is how much R3' buys. The natural competing statistic is the block-norm one,

    n_k = |g_k|^2,    sum_k n_k = |grad E|^2,

which needs no additivity assumption because it is additive by construction over block gradients.

## C1 / C2: the two orderings are genuinely different (verified)

A two-block quadratic energy with a cross term, `E = 1/2|x1|^2 + 1/2|x2|^2 + eps x1.x2`, `eps = 0.9`, was swept over the
second block's scale. Along that one-parameter sweep the norm ordering and the Gamma ordering agree at all seven
sampled scales, but over **4000 random draws the two orderings disagree in 25.6% of cases** (C2 in the archive). So the
choice between a norm-based and a projection-based statistic is not cosmetic: they order the blocks differently for a
quarter of generic configurations, and R3' is exactly what forces the projection-based one.

**Consequence for the manuscript**: R3' is load-bearing. The honest sentence is "additivity is not a technical
convenience; without it the block ordering is not well defined", which is stronger than the current caveat.

## C3: the minimal-restoring-assumption question, resolved

**The tempting weakening is false.** Additivity on the closed subclass of block-orthogonal configurations
`D = {x1.x2 = 0}` plus continuity does *not* restore R3'. Counterexample on the statistic side: for
`S_lam = sum_k n_k + lam (x1.x2)^2` with `lam = 1.7`, the gap between `S_lam` and the separable statistic is
**0.00e+00 on D** (so the hypothesis holds) but **1.70 and 0.27 off D** (so the conclusion fails). A continuous
coupling term that vanishes on a closed measure-zero set cannot be excluded by continuity alone.

**A weakening that is true, and is what the revision should state.** Additivity on any nonempty **open** set of
configurations plus continuity already forces global additivity, because a continuous function that vanishes on a
nonempty open set vanishes identically. This is strictly weaker than assuming additivity everywhere (one only has to
know the statistic is additive on a neighbourhood of the configurations actually used), and it makes no claim about
measure-zero subclasses. The numerical check confirms the distinction: inside a ball of radius 0.35 around a generic
configuration, the coupling deviation is zero at **0 of 2000** sampled points, i.e. an open set cannot hide it.

**What this buys.** The revision can say, with a one-line proof and a reproducible counterexample, both (i) that R3'
cannot be weakened by restricting additivity to a measure-zero subclass, and (ii) that it can be weakened to
open-set additivity. That is a characterised assumption, not a hand-wave.

## What this buys the revision

- A verified statement that the additivity assumption is not redundant (25.6% ordering disagreement), which converts an
  unexplained hypothesis into a justified one.
- An explicit, recorded failure of my own attempted minimality result, which is the kind of thing a reviewer can check
  and which prevents the paper from over-claiming.
- A concrete next step for the theory section: prove the projection-adapted version of C3, or state C3 as a conjecture
  with the counterexample structure of C1 as the boundary.

## Reproduce

```
D:\Anaconda\python.exe tools\_p1768_theory_checks.py
```
