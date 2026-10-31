# Cloud runbook - 2026-10-24 round (prepared, partly executed)

Operator-facing runbook for the four prepared GPU jobs. Nothing here starts an instance by itself; every phase is
resumable, and the shutdown gate is in `cloud_next/verify_cloud_artifacts.py`.

## 1. What is in this round

| Phase | Job | Where it runs | Entry point | Status at the time of writing |
|---|---|---|---|---|
| 1 | Decoder objective x scale ladder (decisive) | cloud | `cloud_next/p1_driver.sh`, `tools/_p1612_objective_control_multimodel.py` | running |
| 2 | P3 torch-2.6 environment-stack seeds (r5/r6 x seeds 7,123,999) | **local** (the 2.6 stack is a local environment; the cloud has 2.12.1+cu130) | `tools/_p1613_p3_cloud_runner.py --job env-seeds --stack-suffix torch26` | running |
| 3 | P3 VQA on the full 451-question test set | cloud | `tools/_p1613_p3_cloud_runner.py --job vqa-full` (+ `--aggregate`) | done, archives retrieved |
| 4 | A23 multi-encoder threshold transfer | cloud (or laptop) | `cloud_next/a23_encoders.sh`, `tools/_p1614_a23_multi_encoder_transfer.py` | prepared, deferred |

Phase-specific detail lives in the notes each phase produced: `docs/decoder_attribution_cloud_notes.md`,
`docs/p3_cloud_round_notes.md`, `docs/p3_vqa451_round_notes.md`, `docs/a23_multiencoder_cloud_notes.md`.

## 2. Preconditions on a fresh instance

1. The operator starts the instance and provides the current SSH port (AutoDL changes it on every start).
2. `bash cloud_next/env_setup.sh` - probes the mirrors (12 s each, choose by measured throughput: hf-mirror is
   the first choice, ModelScope the fallback), pins `HF_HOME`/`MODELSCOPE_CACHE` to the data disk, fetches the
   models **on the server** (never upload weights from the laptop), and prints the corpora sanity list.
3. `bash cloud_next/_wire_models.sh` - exposes the pre-existing caches through the paths the scripts expect
   (ModelScope cache for Qwen2-VL-2B and LLaVA-1.5-7B, HF hub cache for Qwen2.5-VL-7B).
4. `set -x`-style checks are cheap; the helper `tools/_p1615_cloud_exec.py` runs remote commands from the laptop
   with the password taken from the `CLOUD_PW` environment variable (never written to a file).

## 3. Phase 1 - the matched decoder ladder

Protocol: `--protocol match` (320 pairs, 3 epochs, ~196 image tokens, LoRA r8/a16, both-position arm,
`data/marine_captions`). LLaVA-1.5-7B uses a fixed 336x336 CLIP crop, so its image-token cap cannot bind; that is
recorded in each JSON.

```bash
cd /root/autodl-tmp/p3work
setsid nohup bash cloud_next/p1_driver.sh > logs/p1_driver.log 2>&1 < /dev/null &
```

The driver runs, in order: `llava15-7b contrastive`, `llava15-7b generative`, `qwen2vl-2b contrastive`,
`qwen2vl-2b generative`, `qwen25vl-7b generative` (all seed 42, protocol match) and skips any output that
already exists. Set `EXTRA_SEEDS=1` to add seeds 7 and 123 for the LLaVA pair.

Known behaviour, learned the hard way in this round:

* the contrastive arm on a 4-bit LLaVA can overflow to NaN late in training; the script now skips a non-finite
  optimizer step, records `nonfinite_steps_skipped`, truncates to the last finite epoch and reports
  `final_epoch_truncated` instead of losing the run;
* the A/B check (both objectives of one model and seed must share the untrained forward pass) is evaluated
  **after** the result is written, so a mismatch is recorded in `meta.ab_check` and printed as `AB_MISMATCH`
  rather than destroying a finished run;
* `frozen_dg_star` is a property of the untrained model, so it should be identical across the two objectives.
  `meta.ab_check.frozen_rel_diff_percent` records the actual difference; treat anything above ~2 % as a caveat
  worth reporting, not as a result to hide.

## 4. Phase 3 - VQA on the full test set (already completed)

```bash
python tools/_p1613_p3_cloud_runner.py --job vqa-full            # 3 arms, one subprocess each
python tools/_p1613_p3_cloud_runner.py --job vqa-full --aggregate
```

The `r5_step`/`r6_step` adapters (1793 training pairs, 3 epochs, per-step) were already on the instance, so this
was inference only: three arms x 451 questions. The aggregate performs the paired-by-question bootstrap and TOST
equivalence tests. Archives: `outputs/analysis/cloud_vqa_full451_{base,5,6}.json`,
`outputs/analysis/p3_vqa_full_equivalence.json`.

## 5. Phase 2 - torch-2.6 stack seeds (local)

```powershell
& 'D:\Anaconda\envs\torch26\python.exe' tools\_p1613_p3_cloud_runner.py --job env-seeds --stack-suffix torch26
& 'D:\Anaconda\envs\torch26\python.exe' tools\_p1613_p3_cloud_runner.py --job env-seeds --aggregate --strict
```

The runner refuses to run a non-dry job when the installed torch does not match the expected stack, exactly so
that a local run cannot be mislabelled `_torch26`. Sanity anchor: `E(0) = 3917.0`, identical to the archived
seed-42 row. Aggregation writes `outputs/analysis/p3_env_stack_seeds.json` with an explicit per-stack registry -
the old loose glob in `tools/_p1570_env_variance_update.py` now also matches the torch26 files and no longer
reproduces the archived sigma values, which is why downstream text must point at the new archive.

## 6. Phase 4 - A23 multi-encoder transfer (deferred)

```bash
bash cloud_next/a23_encoders.sh          # fetch 7 repos, dry-run gate, encode 21 units, analyze, acceptance
python cloud_next/verify_cloud_artifacts.py --phase phase4 --apply
```

Needs the two corpora that are not on the instance (`data/fathomnet8` 2.1 GB, `data/NKSID` 49 MB) plus the
encoder weights (~7 GB). The local partial run (5 units, 260 ordered pairs) already reproduces every archived
certificate value exactly and finds **no** transfer survivor after the paired bootstrap; the cloud grid widens
that from 3 encoders to 7 and from 15 to 441 ordered pairs.

## 7. Closing sequence (mandatory order)

1. `python cloud_next/verify_cloud_artifacts.py --apply` **on the instance** - it must print `GATE: PASS`.
2. Retrieve: the globs in `cloud_next/expected_outputs.json` (`retrieval.globs`), e.g.
   `scp -P <PORT> -r root@<HOST>:/root/autodl-tmp/p3work/outputs/analysis outputs/analysis`.
3. Re-run the same verifier **on the laptop** against the retrieved files.
4. Only then stop the instance (`sync && shutdown -h now`), probe the port to confirm it is closed, and record
   the shutdown in `HANDOFF.md`.

Do not shut down while the gate fails, and never treat "the job printed something" as retrieval.