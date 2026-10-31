# Paper A upgrade master plan (all five workstreams)

**Status**: prepared 2026-10-26 on the operator's instruction "整理方案，全部都要，然后开始升级，实验先都不跑，等我通知".
Nothing here has been executed. No training or inference run has been started; every workstream below is
"ready to start on the operator's signal".

## Why these five workstreams

The editor's desk rejection was about *perceived contribution* (originality, depth, contribution), and our own
reviews agree that the science is sound but the **ceiling** is set by three things other than volume:

| ceiling factor | current state | workstream that raises it |
|---|---|---|
| generality | image--text only | **B** (cross-modal transfer of the characterisation) |
| predictability | retrospective fit (R^2 0.949) | **C** (pre-registered out-of-sample predictions) |
| theoretical hardness | additivity (R3') assumed | **D** (can R3' be dropped? counterexample family / impossibility) |
| credibility | underpowered controls (6 seeds, n=4 pairs) | **A** (power upgrade) |
| competition | constant/linear baselines only | **E** (competing dynamical models) |

## A. Power upgrade (already planned in `PaperA_power_upgrade_plan.md`)

- 6 -> 16 seeds per allocation arm; 4 -> 12 seed-paired random-pool comparisons; strict-freezing arms 5 -> 10.
- Cost: about 1.5 GPU-days serial, 14-18 h at parallelism 2-3 (VRAM measured first).
- Gates: `--plan` / `--self-test` / `--dry-run`, disjoint new seeds, one-arm smoke, per-arm assertions.
- Feeds: the "resolution limit" paragraph, Table for the allocation contrast, the random-pool finding.

## B. Generality: does the characterisation transfer beyond image--text?

**Question**: is gap susceptibility a property of cross-modal contrastive training in general, or of CLIP-style
image--text training specifically?

**Design (inference only, no training)**: pick 2-3 non-image--text contrastive pairs that are publicly available and
small enough to measure on one GPU: audio--text (e.g. CLAP family), video--text (e.g. a small VideoCLIP/InternVideo
variant), and (if licensing permits) a scientific pair. For each: compute the alignment energy, the gradient
coupling per block, and the *predicted* ordering of the modality-side gradient contributions at three ranks.

**Deliverable**: a table "backbone pair | modality | predicted ordering | measured ordering | agreement", plus a
paragraph in the paper: "the characterisation is not image--text specific" (or an honest boundary if it fails).

**Cost**: 0.5-1 GPU-day, mostly forward passes and small gradient computations. **Risk**: low; a null result is
publishable as a boundary condition.

## C. Predictability: pre-register, then test

**Design**: before any run, freeze `docs/PaperA_preregistered_predictions.md` (written today, see that file) with
strictly specified point predictions for configurations NOT used in fitting: which adaptation site should preserve
the largest gap reduction, the sign of the retrieval change, and a numeric band for the ODE coefficient. Then run
only those configurations and report agreement.

**Deliverable**: a small table "prediction (frozen date) | measured | verdict", and a sentence in the abstract
("we pre-registered the predictions ... they hold for k of n configurations").

**Cost**: 0.5-1 GPU-day. **Risk**: a genuine test - it can fail, and a partial failure is still a result.

## D. Theoretical hardness: how much does R3' buy?

**Question**: the characterisation singles out Γ *given* additivity (R3'). Can R3' be weakened, and what fails
without it?

**Design (pure theory, no experiment)**:
1. Construct an explicit non-additive statistic that satisfies R1-R5 but is not monotone in Γ (candidate: a
   block-summed energy that is decomposable but not additive - the paper already notes ||grad E||^2 is one).
2. Characterise the *class* of statistics identifiable under R1-R5 without R3': conjecture "any statistics
   separable per block", prove it for the two-block case, state the general case as an open problem.
3. Derive the minimal extra assumption that restores uniqueness (weaker than additivity, e.g. continuity +
   additivity on a dense subclass) and prove the corollary.

**Deliverable**: a new theorem + one counterexample in Section 2, and an honest "what this does and does not
settle" paragraph. This is the highest-value but slowest workstream.
**Cost**: 1-2 weeks of theory writing, zero GPU.

## E. Competing dynamical models

**Question**: is the ODE actually better than simpler descriptions of gap evolution?

**Design**: fit four competing models to the same archived trajectories with the same protocol (per-run fit,
same free-parameter budget where possible): (i) the paper's ODE; (ii) exponential decay to a plateau with fitted
rate; (iii) linear-in-epoch model; (iv) a rank-only heuristic. Compare with leave-one-run-out cross-validated R^2
and AIC. Report where the ODE wins and where it does not.

**Deliverable**: one table + one paragraph; directly answers "is the theory load-bearing or decorative?".
**Cost**: hours, CPU only (trajectories are archived).

## Order of execution (on the operator's signal)

1. **C's pre-registration is already frozen today** (file written before any run - that is the whole point).
2. **E** first: pure CPU on archived data, gives an immediate answer about whether the theory carries weight.
3. **B** next: inference-only, raises generality.
4. **A** on the cloud instance when it exists (needs the operator to start it).
5. **C** runs after A/B/E settle, so the frozen predictions can be scored against fresh measurements.
6. **D** in parallel as writing work; no compute.

## Blockers and operator inputs

- Cloud instance for A (and the training parts of C): currently shut down; the operator must start it and provide
  host/port/password.
- Operator must confirm that measuring non-image--text backbones (B) is acceptable in terms of the paper's scope
  (it changes the title/abstract claims slightly).
- Nothing runs before the operator says go.

## Manuscript impact map

| workstream | sections touched |
|---|---|
| A | Section 5 (allocation), Table 1 footnote on power, the "resolution limit" paragraph |
| B | Section 2 (characterisation), Section 6 (boundary conditions) |
| C | Abstract, Section 5 first paragraph, new "Pre-registered predictions" subsection |
| D | Section 2 (theory), Section 6 (what is assumed) |
| E | Section 5 (validation), Table 16 area |
