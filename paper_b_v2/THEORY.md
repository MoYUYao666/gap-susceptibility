# Paper B v2 theory — selection resolution and the last-epoch baseline

Status: **G0 theory draft; no experiments, no cloud.** This document labels every standard result explicitly. No
TPAMI-level theorem is claimed.

## 1. Model

A PEFT run produces checkpoints `t=1,...,T` (here `T=3` in the frozen evidence). For checkpoint `t`:

- `r_t in R`: target readout (higher is better);
- `g_t in R^p`: label-free proxy/geometry vector;
- the last-epoch baseline is `T`.

A **label-free selector** is a map `h(g_1,...,g_T) -> {1,...,T}`. Its regret relative to last epoch is

\[
  R(h)=r_{h(g)}-r_T.
\]

`R(h)<0` means the selector improves on last epoch; `R(h)>0` means it is worse. The oracle gap is
`Delta_oracle = max_t r_t - r_T`; this is the maximum possible improvement.

## 2. Assumptions

- **A1 (finite trajectories).** `T` finite.
- **A2 (proxy-only selector).** `h` sees only `g_1...g_T`, not target readouts.
- **A3 (proxy error model).** In the alignment analysis, `|g_t-r_t| <= epsilon` for all `t`; this is an assumption
  about a one-dimensional proxy. For a multi-dimensional geometry score, the same statement applies after a
  pre-declared scalarization; the scalarization is part of the protocol.
- **A4 (monotone-readout condition).** `r_1 <= r_2 <= ... <= r_T`.
- **A5 (exchangeability).** When stated, the prior over the two trajectories is symmetric under swapping the
  checkpoint labels.

## 3. T1 — last-epoch dominance under monotone readout

**Proposition T1 (standard).** Under A4, for every label-free selector `h`,
\[
  R(h)=r_h-r_T \ge 0.
\]
Moreover `h=T` is optimal and no proxy can improve it.

**Proof.** By monotonicity, `r_t <= r_T` for every `t`; the selected checkpoint's readout is at most `r_T`. []

This is elementary; it makes the last-epoch baseline explicit but is not a new theorem. It explains why a negative
selection result is not surprising when adaptation improves the readout along the trajectory.

## 4. T2 — proxy-invariance lower bound on oracle regret

**Proposition T2 (standard permutation argument, applied to PEFT selection).** Let
`R_or(h) = max_t r_t - r_{h(g)}` be oracle regret. Consider `K` checkpoints whose readouts are a uniform random
permutation of `{0, Delta, ..., (K-1)Delta}`, with identical proxy observations `g`. Any deterministic label-free
selector is a fixed index; its expected oracle regret is at least `(K-1)Delta/2`. For `K=2` this is `Delta/2`.

**Proof.** The selected readout is uniform over the `K` values, with mean `(K-1)Delta/2`; the maximum is
`(K-1)Delta`; subtraction gives `(K-1)Delta/2`. []

This bound is about **oracle regret**, not regret relative to last epoch. Last epoch is always available, may be
the best fixed choice, and is exactly the baseline we measure empirically. The earlier two-world statement for
`R(h)=r_h-r_T` is not used: a selector can always choose `T`, so no positive last-regret lower bound follows.

This is a Le Cam/permutation argument. Its role here is to formalize why geometry proxies without target
alignment cannot certify a better checkpoint. It does not by itself prove that all empirical proxies fail.

**Corollary.** If a proxy is invariant to checkpoint identity/order within an equivalence class, no calibration
on that class can resolve the hidden readout ordering. A target-label channel is required.

## 5. T3 — alignment sufficiency

**Proposition T3 (standard approximation bound).** Assume A3. If the true best checkpoint `t*` satisfies
\[
  r_{t^*} - r_{t'} > 2\epsilon
  \quad\text{for every }t'\ne t^*,
\]
then selecting `argmax_t g_t` returns `t*`.

**Proof.** For every `t`, `|g_t-r_t|<=epsilon`; the best readout has proxy at least `r_{t*}-epsilon`, every other
has proxy at most `r_{t'}+epsilon < r_{t*}-epsilon`; hence the argmax is unique. []

This is a basic approximation/robustness bound. It is not new, but it gives the operational boundary: a proxy must
be accurate relative to the readout margin to certify a non-last checkpoint.

**Sign/orientation caveat.** T3 assumes the proxy is oriented so that larger means better. If the sign is unknown,
a fixed sign is an assumption. A sign-calibration step needs target labels. The G2 reanalysis finds strong signed
rank correlations with proxy-specific signs; calibration recovers the sign and it transfers across the frozen
split, but the correctly oriented proxy still loses to last epoch. The remaining gap is a utility-margin problem,
not a global sign instability.

## 6. T4 — candidate selection-resolution statement

Define the **selection resolution** at a trajectory as

\[
  \rho = \max_t |g_t-r_t|.
\]

The upper side is a corollary of T3: if `Delta_oracle > 2 rho` and the margin condition holds, the proxy recovers
the best checkpoint.

The lower side (`Delta_oracle <= rho` implies no proxy can certify) is **not proved here**. It is a heuristic
decision boundary, not a theorem. A sharp minimax statement is left open and is not claimed.

**Status:** T4 is a **conjecture/heuristic**, not a proposition. It must not be cited as a lower bound unless a
proof is supplied.


## 6b. T4b — certification necessity (standard)

**Proposition T4b (standard impossibility of label-free certification).** Fix two candidate checkpoints and the
last epoch. Suppose the proxy observation is identical in two worlds:
World A: `r_1 > r_T > r_2`; World B: `r_2 > r_T > r_1`.
Any deterministic label-free selector that chooses a non-last checkpoint on this observation is worse than last in
at least one world. Hence no label-free rule can certify a positive improvement over last from this observation
alone.

**Proof.** The selector's index is fixed because the proxy observation is identical. If it chooses 1, World B has
`r_1 < r_T`, so `R>0`; if it chooses 2, World A has `R>0`. []

This is a standard indistinguishability argument, not a new theorem. It formalizes why the last-epoch baseline
cannot be beaten by proxy evidence alone without an additional assumption or target labels.


## 6c. T5 — certified abstention (standard)

**Proposition T5 (standard; certified abstention).** Let `ĝ_t` be a calibrated scalar proxy with
`|ĝ_t-r_t| <= epsilon` for all `t`. Define the selector:
- if `ĝ_best - ĝ_T > 2 epsilon`, return `argmax ĝ`;
- otherwise return the last epoch `T`.

Then every non-last selection has `r_selected > r_T`; otherwise the selector returns last. The rule therefore
has a certified positive improvement whenever it does not abstain.

**Proof.** If `ĝ_best-ĝ_T>2ε`, then `r_best >= ĝ_best-ε > ĝ_T+ε >= r_T`; the argmax is best. []


## 6d. T6 — minimax fallback (standard)

**Proposition T6 (standard; last epoch is minimax optimal under proxy ambiguity).** Consider any set of readout
worlds that are consistent with the same proxy observations. The last-epoch rule has worst-case regret 0 relative
to itself; any label-free rule that can choose a non-last checkpoint has a world in which that choice is worse
than last, hence positive worst-case regret. Last epoch therefore minimizes worst-case regret over the ambiguity
set.

**Proof.** `R(last)=0` in every world. For any other rule, choose a world in which its selected checkpoint has
readout below `r_T`; such a world is consistent with the proxy observations by construction. The worst case is
therefore nonnegative, and last attains 0. []

## 7. Counterexamples

### C1 — non-monotone readout

`r=(0.70,0.90,0.60)`, `T=3`. Last epoch is not best; a proxy that sees only training progress may choose `t=3` or
`t=1`. T1 does not apply. This shows the monotone-readout assumption is essential.

### C2 — proxy correlated with training time but anti-aligned after site shift

Proxy favors later checkpoints in the source site, but target readout favors an earlier checkpoint in a shifted
site. No target labels on the shifted site means the proxy cannot know the reversal; T2 applies at the level of the
two site worlds.

### C3 — ties and readout noise

If two checkpoints have readout difference below the evaluation resolution, no selector can certify which is
better; this is the selection-resolution boundary from T4, not evidence that a proxy is informative.

## 8. What is new vs standard

| Result | Status |
|---|---|
| T1 monotone last-epoch dominance | elementary, standard |
| T2 permutation/proxy-invariance bound | standard Le Cam/permutation argument |
| T3 Lipschitz/approximation sufficiency | standard approximation bound |
| T4 selection-resolution boundary | corollary; not a new minimax theorem |
| **Last-epoch baseline as first-class object + selection-resolution measurement for PEFT** | the paper's framing/contribution, not a new theorem |

The honest claim is a **formal measurement/negative-result paper** for PR, not a TPAMI theory contribution.

## 9. G0/G1 checks

- G0: model, assumptions and counterexamples complete.
- G1: test whether T1/T3/T4 predictions hold on the frozen 144-run records; no new training.
- If the frozen data contradict the theory, revise the theory or kill the paper.
