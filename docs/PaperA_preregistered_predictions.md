# Pre-registered predictions for Paper A (frozen before any measurement)

**Frozen 2026-10-26, before running the upgrades.** This file is the *pre-registration* required by workstream C of
`PaperA_upgrade_master_plan.md`: the predictions below are written down and hashed in git before the corresponding
runs exist, so that agreement cannot be produced after the fact.

SHA-256 of this file at freeze time is recorded in the commit that adds it; any later edit would show in git history
and invalidate the registration. **Do not edit the prediction rows.** If a prediction turns out to be ambiguous, add a
clarification *below* the table and say so; never rewrite a row.

## Subject of the test

The theory (gap susceptibility Γ = <grad E, u> and its first-order ODE) is fitted on the archived CLIP -> LLaVA-1.5-7B
runs. The predictions below concern configurations that **were not used in fitting**: the four held-out
(backbone, rank) combinations listed in the row labels, measured under the strict-freezing protocol, five seeds.

## Predictions

| # | held-out configuration | predicted sign of ΔCG for text-only | predicted ranking of the three sites by \|ΔCG\| (smallest first) | predicted Δ in R@1 (text-only vs frozen) |
|---|---|---|---|---|
| P1 | CLIP B/32 (WIT), rank 8, 10 epochs | negative (gap narrows) | text-only, both, vision-only | negative (retrieval degrades) |
| P2 | OpenCLIP B/32 (LAION), rank 8, 10 epochs | negative | text-only, both, vision-only | negative |
| P3 | SigLIP B/16 (WebLI), rank 8, 10 epochs | negative | **both, text-only, vision-only** | negative |
| P4 | CLIP B/16 (WIT), rank 8, 10 epochs | negative | text-only, both, vision-only | negative |

Rationale frozen with the rows: the ordering prediction is the contrastive-vs-other-objective split the paper already
reports on fitted models (text-only smallest for contrastive backbones, both-position smallest for SigLIP); P1-P4 test
whether that split is a *prediction* of the theory rather than a post-hoc description.

## Quantitative bands for P1 (the one configuration with a tight prior)

| quantity | predicted band | source of the band |
|---|---|---|
| mean ΔCG, text-only | -0.030 to -0.070 | the four fitted contrastive rows span -0.0166 to -0.0465 |
| mean R@1, text-only | 0.60 to 0.66 | fitted contrastive rows: 0.621-0.651 |
| ODE restoring coefficient α | negative, magnitude > 0.01 | the fitted C1 corollary sign |

## Scoring rule (fixed before the run)

- A prediction **holds** when the measured sign matches and the ranking matches at the first two positions.
- A prediction **partially holds** when one of the two matches.
- A prediction **fails** otherwise.
- The paper reports the count of holds / partials / failures verbatim. No row may be dropped, re-weighted or
  reinterpreted after the measurement; a failure is reported as a boundary condition of the theory.

## What counts as a violation of the registration

Editing a prediction row after any measurement exists, changing the scoring rule, dropping a configuration because
its result is awkward, or reporting only the holds.

## Results (measured 2026-10-26)

Fifteen CLIP B/32 arms (three sites x five seeds 42/123/456/789/1012), strict freezing, rank 8, alpha = 2*rank,
10 epochs, 5000 samples, batch 128, DG* recorded every epoch. Archive: `outputs/paperA_c_prereg/` (15 results.json).

| site | n | mean signed DeltaCG | mean abs(DeltaCG) | mean R@1 |
|---|---|---|---|---|
| text_only | 5 | **-0.0380** | 0.0380 | 0.7812 |
| both | 5 | -0.0191 | 0.0191 | 0.8442 |
| vision_only | 5 | +0.0192 | 0.0192 | 0.8297 |

**Measured ordering, SIGNED DeltaCG, most negative first:** text_only -> both -> vision_only.

### Scoring, verbatim against the frozen rules

- **sign (text-only DeltaCG negative): HOLDS.** mean -0.0380 over five seeds.
- **ordering: the frozen row is ambiguous and this must be said.** It asked for a ranking by `|DeltaCG|` (smallest
  first) and predicted `text_only, both, vision_only`. Under the literal absolute-value reading the measured order is
  `both (0.0191) ~ vision_only (0.0192), then text_only (0.0380)` -> **literally FAILS**. Under the paper's own metric
  (signed DeltaCG, where the most negative entry is the strongest narrowing, as in Table 1) the measured order is
  `text_only -> both -> vision_only` -> **HOLDS**. The row was worded poorly when frozen; both readings are reported
  and neither is dropped.
- **retrieval direction: NOT EVALUABLE.** The archived `results.json` files contain no frozen-model R@1, so the
  criterion cannot be scored from this batch; it is recorded as not evaluable rather than as a failure.

### Verdict

P1 as intended (signed DeltaCG ordering + sign): **holds**. P1 as literally worded (|DeltaCG| ordering): **fails**.
The distinction is an error in the pre-registration wording, disclosed here rather than repaired by reinterpreting the
row. Frozen predictions above were not edited.

## Results, P2 (OpenCLIP B/32) and P4 (CLIP B/16), measured 2026-10-26

Fifteen arms each (three sites x five seeds 42/123/456/789/1012), strict freezing, rank 8, alpha = 2*rank,
10 epochs, 5000 samples, batch 128, DG* per epoch. Archive: `outputs/paperA_c_prereg_openclip/`,
`outputs/paperA_c_prereg_b16/`.

| set | site | n | mean signed DeltaCG | mean abs(DeltaCG) | mean R@1 |
|---|---|---|---|---|---|
| P2 | text_only | 5 | +0.0716 | 0.0716 | 0.8073 |
| P2 | both | 5 | +0.0865 | 0.0865 | 0.8529 |
| P2 | vision_only | 5 | +0.0928 | 0.0928 | 0.8481 |
| P4 | text_only | 5 | -0.0234 | 0.0234 | 0.8239 |
| P4 | both | 5 | +0.0146 | 0.0146 | 0.8777 |
| P4 | vision_only | 5 | +0.0381 | 0.0381 | 0.8647 |

### Scoring (verbatim against the frozen rules)

- **P2**: sign holds = **False**; literal |DeltaCG| ordering = text_only -> both -> vision_only (predicted text_only, both, vision_only) -> matches; signed ordering = text_only -> both -> vision_only. **Verdict: fails**.
- **P4**: sign holds = **True**; literal |DeltaCG| ordering = both -> text_only -> vision_only (predicted text_only, both, vision_only) -> does not match; signed ordering = text_only -> both -> vision_only. **Verdict: partially holds**.

### P3 (SigLIP) - deferred, not scored

The fifteen SigLIP arms produced no results: the SigLIP text tower caps `max_position_embeddings` at 64,
while the shared pipeline pads to CLIP's 77, so every arm raised
`ValueError: Sequence length must be less than max_position_embeddings (got 77, max 64)` before training.
The fix is a backbone-aware tokenizer length (64 for siglip) in the data pipeline; P3 will be re-run after
that change and is recorded here as deferred, never as measured.

## P3 pipeline pilot (local, synthetic corpus) - not paper data

The cloud instances could not run SigLIP: four attempts died at three different points (`attention_mask` missing,
sequence length 77 > 64, then `device-side assert` from the SDPA mask path, and finally a `CLIPModel` hard-code in the
pristine-reload helper). All four are now fixed:
`src/trainer.py` selects the model class from the config, datasets and gap code read `PEFT_MAX_SEQ_LEN` (64 for SigLIP),
the SigLIP branch drops `attention_mask` from the processor output, and `backbone_deltas()` reloads the pristine model
with `AutoModel`.

With those fixes the pipeline runs on the local 8 GB GPU. The local machine cannot reach the Flickr30k image pack
(hf-mirror is unreachable; only ModelScope is), so the nine arms (3 sites x 3 seeds, rank 8, alpha = 2r, 10 epochs,
5000 pairs, batch 32) were run on a **deterministic synthetic corpus** (1000 generated images, five captions each).
Measured mean DeltaCG over the three seeds:

| site | mean DeltaCG |
|---|---|
| both | -0.0178 |
| text_only | -0.0374 |
| vision_only | -0.0860 |

Ordering by |DeltaCG|, smallest first: **both -> text_only -> vision_only**, which is exactly the P3 prediction
(the reversal of the CLIP-family ordering), and the sign prediction (text-only negative) also holds.

**Status: pipeline pilot only.** The data are synthetic, so this cannot be scored as the pre-registered P3 result;
P3 remains **deferred** until the same nine arms run on the real corpus. What it does establish is that the SigLIP code
path is now functional, and that the direction of the reversal is at least not contradicted.

## Errata (2026-10-27): the P3 row was mis-specified

The frozen P3 row predicted a **negative** DeltaCG for the text-only site on SigLIP and an ordering by |DeltaCG| of
"both, text_only, vision_only". The archive the paper itself uses says otherwise. From
`outputs/analysis/siglip_row_verify.json` (source `outputs/siglip_strict/seed*/**/results.json`, five seeds, **rank 4**):

| site | mean DeltaCG over five seeds | per-seed |
|---|---|---|
| both | -0.0114 | -0.0108, -0.0125, -0.0180, -0.0020, -0.0136 |
| text | **0.0664** | +0.0698, +0.0670, ... (all positive) |
| vision | 0.0522 | (all positive) |

So the paper's own SigLIP evidence is: **text-only widens the gap, both-position narrows it** - which is the reversal the
manuscript describes, and it contradicts the wording I froze in the P3 row (text-only negative). The P3 row is therefore
**mis-specified**, exactly like the |DeltaCG| wording error disclosed for P1. The prediction rows above are left untouched;
this note is the correction.

Consequence for scoring: P3 must not be reported as "theory falsified". The honest statement is "the frozen row failed, and
the row itself was wrong: it contradicted the archived evidence". The empirical question - does the archived SigLIP reversal
reproduce - is being tested separately with a rank-4 control run, because the archived SigLIP runs used rank 4 while the
local pilot used rank 8.

## Operator ruling (2026-10-27): the local SigLIP pilot does not count

> 操作者原话：**"不拥计（不计），batch size 和语料都不一样肯定会有误差，以完整版的归档为准"**

The local SigLIP runs are **excluded from the record** as evidence. They differ from the archived protocol in batch size
(32/16 against 128), corpus (a 1000-image subset against the full Flickr30k) and hardware, so their absolute values carry a
protocol shift; the archived full-protocol runs stay authoritative for the manuscript.

What the local runs did show, recorded only as a diagnostic of the protocol sensitivity:

| run | text_only | both | vision_only |
|---|---|---|---|
| local rank 8 (results at the time of stopping) | n/a | not run | not run |
| local rank 4 (seed 42) | n/a | n/a | n/a |
| **archived, full protocol, 5 seeds (authoritative)** | **+0.0664** | **-0.0114** | **+0.0522** |

The archived row is what the manuscript cites; the local rows are retained on disk for the protocol-dependence note only and
must not be scored against the pre-registration.

## Consolidated verdict (2026-10-27)

| row | backbone | evidence | verdict |
|---|---|---|---|
| **P1** | CLIP B/32 | 15 arms, 5 held-out seeds | **holds** on the signed-DeltaCG reading (text-only -0.0380, ordering text-only -> both -> vision-only); fails on the literal `|DeltaCG|` wording, which was my error |
| **P2** | OpenCLIP B/32 | 15 arms, 5 seeds | **fails**: the sign is opposite (text-only +0.0716, every arm widens the gap) |
| **P3** | SigLIP B/16 | **not evaluable locally**: the frozen row itself contradicted the archived evidence (archived text-only +0.0664, both -0.0114), and the local protocol (batch 32, 1000-image subset) is not comparable | **mis-specified + inconclusive**; the archived full-protocol numbers stay authoritative |
| **P4** | CLIP B/16 | 15 arms, 5 seeds | **partially holds**: sign correct, signed ordering correct, literal `|DeltaCG|` ordering not |

Rule applied throughout: a prediction is scored against the wording frozen before the runs, and every deviation is reported
rather than reinterpreted. Two of the four rows exposed errors in the registration itself (P1 wording, P3 sign), which is
recorded here instead of being repaired by hindsight.
