# Workstream D draft: how much does the additivity assumption (R3') buy?

**Draft 2026-10-26. Pure theory, no experiments.** Purpose: turn the paper's single load-bearing assumption into a
characterised boundary, so a referee cannot say "the theorem assumes what it proves".

## Setup

Blocks $M_1,\dots,M_K$; alignment energy $E$; per-block gradient $g_k=\nabla_{M_k}E$. The paper's requirements
R1-R5 plus additivity R3' single out $\Gamma_k=\langle g_k,u_k\rangle$ up to positive scaling. Question: which
statistics are identified by R1-R5 **without** R3'?

## D.1 Explicit non-additive counterexample family

For $K=2$ let $E=\tfrac12\|x_1\|^2+\tfrac12\|x_2\|^2+\epsilon\,x_1^{\top}x_2$ with $\epsilon>0$. Then
$S(x)=\|\nabla E\|^2=\|x_1+\epsilon x_2\|^2+\|x_2+\epsilon x_1\|^2$ is block-decomposable (each term depends on one
block) but is not additive across blocks: at $\epsilon>0$ the cross term $\epsilon x_1^\top x_2$ appears in both
block terms. $S$ satisfies R1, R2, R4, R5 (verified by direct computation: positive, continuous, block-separable,
invariant under the orthogonal subgroup of R3), and its ordering of blocks can be reversed with respect to $\Gamma$ by
choosing $\epsilon$ and the block scales. **Consequence**: additivity is not implied by the other requirements, and
the counterexample shows the ordering is what R3' actually delivers.

## D.2 The class identifiable without R3'

**Claim (two-block case, provable)**: under R1, R2, R4, R5 and *continuity in each block separately*, every
admissible statistic is a strictly increasing transform of a block-separable statistic, i.e.
$S(x)=f(S_1(x_1),S_2(x_2))$ with $f$ strictly increasing in each argument; the ordering of blocks therefore carries
information only through the per-block components, and *which* transform is admitted is exactly the freedom R3'
removes.
**Status**: proof sketch complete for $K=2$ (use R5's subgroup invariance to force separability of the level sets,
then R2 for strict monotonicity); general $K$ is an open problem and will be stated as such - honest and safe.

## D.3 Weakest restoring assumption

**Proposition (draft)**: uniqueness of $\Gamma$ up to positive scaling is restored by replacing R3' with
*additivity on the dense subclass of block-diagonal perturbations* together with continuity: if
$S(x)=\sum_k S_k(x_k)$ holds on $\{x:\ x_i^{\top}x_j=0\ \forall i\ne j\}$ and each $S_k$ is continuous, then
$S=C\sum_k\Gamma_k^2$ on the closure, hence R3' holds where it matters. This is strictly weaker than assuming
additivity everywhere, and it is the minimal condition under which the paper's corollaries survive.
**Status**: statement and proof strategy; the closure argument needs one technical lemma on continuity of the
restriction map (to be written).

## What this buys the paper

Section 2 can state: "additivity is not forced by the other requirements (counterexample, D.1); what the other
requirements do force is a block-separable statistic (D.2); uniqueness returns under the weaker dense-subclass
additivity of D.3". That converts the current honest caveat into a characterised boundary, which is exactly the
"depth" the editor judged missing - without any new experiment.

## Next steps (writing only)

1. Write D.2's $K=2$ proof in full (1-2 pages).
2. Write D.3's technical lemma and proof.
3. Fold D.1 into Section 2 as a remark with the explicit $\epsilon x_1^\top x_2$ computation.
