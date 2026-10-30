# LLaVA canonical retrain and Qwen trial (2026-10-17)

## What ran

A twelve-run sweep of LLaVA-1.5-7B in bfloat16 with the corrected measurement: the last hidden state is captured
with an `lm_head` forward pre-hook, the vision side is the mean pool over image-token positions, the text side is
the mean pool over **non-image** positions, and the metric is the canonical trio from `src/dg_star_tracker.py`
(`DG* = mean ||I_i - T_i||^2`, paired and squared, after L2 normalisation).

* 1500 training pairs / 500 held-out pairs, 3 epochs, batch 2, rank 8, lr 1e-4, 3 seeds, 4 arms;
* `steps_total` 2250 per run; the twelve records were verified by `tools/_p1138_verify_and_pull.py`:
  12 records, canonical fields present on all of them, `n_eval == 500`, frozen seeds identical, adapters
  non-empty, `ARM_FAILURES.txt` absent;
* 22 files pulled back (1700.1 MB), zero size mismatches.

## Results (canonical definition)

| Arm | DG* before | DG* after | rel change mean | rel sd | CG | DG_emp |
|---|---|---|---|---|---|---|
| frozen | 0.8146 | 0.8199 | +0.650% | 0.000 | 0.8778 | 0.8868 |
| text_only | 0.8146 | 1.1052 | +35.678% | 6.053 | 0.9916 | 1.0201 |
| vision_only | 0.8146 | 0.8735 | +7.237% | 9.166 | 0.8979 | 0.9050 |
| both | 0.8146 | 1.0863 | +33.350% | 1.666 | 0.9683 | 1.0083 |

Per-seed canonical relative changes: frozen +0.650/+0.650/+0.650; text_only +40.765/+39.097/+27.173;
vision_only -1.508/+19.896/+3.322; both +31.011/+34.279/+34.761.

Signal-to-noise against the frozen floor (+0.650%): text_only 5.79, vision_only 0.72, both 19.63.

Reading: the canonical gap on LLaVA is driven almost entirely by **text-side** adaptation. Text-only and
both-position are far above the frozen floor and are indistinguishable from each other (35.7% against 33.4% with
sd 6.1 and 1.7); vision-only alone is not distinguishable from frozen (its delta is smaller than its own seed sd).

## Relation to the paper's existing decoder-VLM result

The supplement's Section E reports Qwen2-VL-2B under the same canonical definition:

| Arm | Qwen2-VL-2B (supplement E) | LLaVA-1.5-7B (this run) |
|---|---|---|
| Both | +87.9 +/- 5.4% | +33.4 +/- 1.7% |
| Text-only | +66.5 +/- 8.3% | +35.7 +/- 6.1% |
| Vision-only | +18.0 +/- 8.8% | +7.2 +/- 9.2% |

The **ordering agrees** across both decoder models (both ~ text-only >> vision-only), so the "text-side drives the
canonical gap" pattern is not unique to one model. The **sign does not**: for Qwen2-VL-2B the change is a
reduction, for LLaVA-1.5-7B it is an increase. Whether the sign tracks scale (2B against 7B), training data or
preprocessing is not resolved by these two points.

## Qwen2.5-VL-7B feasibility trial

Run once to answer whether the model fits, not to produce results:

* **fits**: bf16 7B in 32.8 GB with `exit=0` and no OOM, once the probe model is released (`tools/_p1143`);
  the 2026-10-16 conclusion that it did not fit was caused by holding two bf16 copies (16.6 GB x 2 = 33.2 GB),
  which also explains why reducing batch and max-length did not move the failure point;
* **1.59 s/step** (LLaVA measured 0.95 s/step on the same host), 362 visual tokens per sample;
* the canonical metric computes: DG* 1.2879 -> 1.2424 (-3.531%), CG 1.0586, DG_emp 1.1150 on 8 held-out pairs;
* the checkpoint holds **392 real LoRA tensors** (242.7 MB), so the 2026-10-16 empty-checkpoint defect is gone;
* tower isolation holds: `text_only trainable 20,185,088, by tower {'text': 20185088}`.

Estimated cost of a full twelve-run Qwen sweep at the measured rate: 1.59 s/step x 2250 = 59.6 min per run plus
evaluation and loading, about **68 min per run, roughly 13.6 GPU-hours**; reducing frozen to one seed (its sd is
0 on LLaVA because it trains nothing) brings it to about 11.3 GPU-hours. Not launched -- awaiting the operator's
value judgement.

## Not done deliberately

Paper A's supplement Section F still describes the archived 2026-10-16 legacy-metric result as a scoped null
result with text-only bit-identical to frozen. That text is now contradicted by the canonical numbers above and
will be rewritten, but only after the operator decides what story the section should tell.
