# P3 cloud round notes: environment-stack seeds (S29/S37) and full 451-question VQA (S28)

Preparation round, 2026-10-24. This document describes the *next cloud GPU round*: what it produces,
the exact commands, the expected filenames, the resources it needs, how a completed round is judged,
and what changes in the manuscript once the numbers exist. Nothing here requires a cloud instance to
prepare or to verify: every mode of the runner has a local, GPU-free path (`--dry-run`, `--self-test`).

| Item | Value |
|---|---|
| Runner | `tools/_p1613_p3_cloud_runner.py` |
| Instance entry point | `cloud_next/p3_env_seeds.sh` |
| Artifacts written by the round | six `verify_r{5,6}_s{7,123,999}_*_torch26.json`; `outputs/analysis/p3_env_stack_seeds.json`; `outputs/analysis/cloud_vqa_full451_{base,5,6}.json`; `outputs/analysis/p3_vqa_full_equivalence.json`; `outputs/analysis/p3_env_seeds_runlog.json`; logs under `cloud_next/logs/` |
| Why it is needed | S29/S37's fourth stack (torch 2.6.0+cu124) has a single seed, and S28's VQA equivalence rests on 300 of the 451 held-out questions |

## 1. What the two jobs do

**Job A, `--job env-seeds`.** Six training runs of `paper3/scripts/run_training.py`, one subprocess
per run: ranks 5 and 6 crossed with seeds 7, 123 and 999, on the torch 2.6.0+cu124 stack. Each run
is the archived seed-42 protocol, so the six new rows extend the existing torch26 row pair
(`verify_r5_s42_..._a10_torch26.json` = -35.5 and `verify_r6_s42_..._a12_torch26.json` = +42.0) to
four seeds per rank. Outputs are renamed to the archived convention with the stack suffix appended
(the training script itself cannot write `_torch26`).

**Job B, `--job vqa-full`.** Three inference arms (base model, rank 5, rank 6) evaluated on all 451
rows of `paper3/test-vqarad.parquet`, one subprocess per arm. The evaluation code is not rewritten:
model loading, prompt construction (`"Answer briefly. <question>"`), greedy decoding and the
`norm`/`token_f1` metric are imported from `tools/_p1516_p3_vqa_downstream.py`. The rank adapters are
the ones the archived 300-question round used.

## 2. Exact commands

On the instance (repository checkout at the path the bundle uses, caches on the data disk):

```bash
# both jobs, then both aggregations, all logged under cloud_next/logs/
P3_BASE=/root/autodl-tmp/p3work PY=python bash cloud_next/p3_env_seeds.sh

# one job at a time (this is how cloud_next/run_all.sh calls the script)
bash cloud_next/p3_env_seeds.sh --job env-seeds
bash cloud_next/p3_env_seeds.sh --job vqa-full

# rehearsal: prints every command, executes nothing, writes nothing
bash cloud_next/p3_env_seeds.sh --dry-run
```

Direct runner invocations (equivalent, and what `cloud_next/run_all.sh` phases 2 and 3 use):

```bash
python tools/_p1613_p3_cloud_runner.py --job env-seeds --dry-run
python tools/_p1613_p3_cloud_runner.py --job env-seeds
python tools/_p1613_p3_cloud_runner.py --job env-seeds --aggregate --strict

python tools/_p1613_p3_cloud_runner.py --job vqa-full --dry-run     # also accepts --apply
python tools/_p1613_p3_cloud_runner.py --job vqa-full
python tools/_p1613_p3_cloud_runner.py --job vqa-full --aggregate --strict
```

Local, GPU-free checks (used before this document was written, repeatable at any time):

```bash
python tools/_p1613_p3_cloud_runner.py --self-test        # 52 assertions, writes nothing
```

Useful flags: `--force` (re-run a valid output), `--limit N` (stage the round),
`--ranks`/`--seeds` (default `5,6` / `7,123,999`), `--stack-suffix` (default `torch26`),
`--expect-torch` (default `2.6`), `--data-path` (override the training parquet),
`--adapter-dir`, `--train-samples` (default 1793), `--n-boot` (default 20000).

### Preconditions the script enforces

* `paper3/scripts/run_training.py`, `tools/_p1516_p3_vqa_downstream.py`,
  `tools/_p1595_p3_rank_separation.py`, `paper3/test-vqarad.parquet`, `models/llava-hf`,
  `data/vqa_rad/images` must all exist; otherwise the script stops with a pointer to
  `cloud_next/env_setup.sh`. Weights and datasets are downloaded on the instance, never uploaded.
* Job A refuses to start when the installed torch is not 2.6.x, because that would mislabel rows as
  `_torch26` (override with `--allow-stack-mismatch` plus an honest `--stack-suffix`). Verified
  locally: on this workstation (torch 2.9.1+cu130) the job exits 2 before running anything.
* Job A refuses to start when `glob("paper3/train-*.parquet")[0]` is not
  `paper3/train-00000-of-00001-a09b74b3ef9c3b56.parquet`, because the archived rows do not record
  `--data-path` and a different first match would silently change the training set while leaving the
  filename unchanged. Pass `--data-path` explicitly to override.

## 3. The reconstructed training command for the torch26 rows

The archived invocation was not stored anywhere in the repository (`tools/` and `cloud_p3/` contain
no command that passes `--lora-alpha`, and the archived JSONs do not record `data_path`, `model_path`
or the argv). The command below is therefore reconstructed from the archived rows themselves and
validated field by field against both of them by `--self-test`; the reconstruction is the only
invocation that reproduces the archived filenames, since `_a10`/`_a12` appear in a
`run_training.py` filename tag **only** when `--lora-alpha` is passed explicitly (the uniform
default is already `rank * 2`, so the value is the same either way).

```bash
# rank 5, seed 42 (the archived row); the round runs the same command for seeds 7, 123, 999
python paper3/scripts/run_training.py \
  --rank 5 --seed 42 --epochs 3 --num-samples 20 \
  --lr 5e-5 --batch-size 1 --block-config uniform --opt adamw \
  --compute-dtype float16 --attn-targets qkvo --grad-mask none \
  --lora-alpha 10
# rank 6: --rank 6 --lora-alpha 12, everything else identical
```

Field-by-field evidence (all 17 fields reproduced for both ranks; self-test check
"every archived config field reproduced by the reconstruction"):

| Flag | Value | Evidence |
|---|---|---|
| `--rank` | 5 / 6 | filename `verify_r{5,6}_...`; payload `rank` |
| `--seed` | 42 in the archive, 7/123/999 in this round | filename; payload `seed` |
| `--epochs` | 3 | payload `epochs` = 3; tag `_e3` |
| `--num-samples` | 20 | payload `num_samples` = 20 (16 train / 4 eval) |
| `--lr` | 5e-5 | payload `lr` = 5e-05; tag `_lr5e-05` (`%g` of 5e-05) |
| `--batch-size` | 1 | payload `batch_size` = 1; no `_b*` in the tag |
| `--block-config` | uniform | payload `block_config` = "uniform"; tag `_bcuniform` |
| `--opt` | adamw | payload `opt` = "adamw"; tag `_adamw` |
| `--compute-dtype` | float16 | payload `compute_dtype` = "float16"; tag `_float1` |
| `--attn-targets` | qkvo | payload `attn_targets` = "qkvo" (also the default) |
| `--grad-mask` | none | payload `grad_mask` = "none" |
| `--lora-alpha` | **10 / 12 (2 x rank), passed explicitly** | the tag contains `_a10`/`_a12`, which `run_training.py` emits only when `args.lora_alpha is not None`; payload `lora_alpha` = 10.0 / 12.0 |
| `--warmup` absent | - | payload `warmup` = false; tag `_nw` |
| `--images-dir` absent | - | no `_imgs` in the tag; the protocol is the blank-image one |
| `--per-step` absent | - | not part of the tag; the archived payload has no per-step marker, and `epochs`/`num_samples` match the epoch-step protocol |
| `--proj-rank`, `--data-offset`, `--lang-only`, `--target-proj` absent | - | payload `proj_rank` = null, `data_offset` = 0, `lang_only` = false, `target_proj` = false |
| `--model-path` absent | - | default `models/llava-hf` (run_training.py line 125); not recorded in the archive |

**Field that could not be confirmed: `--data-path`.** The archived payloads do not contain it, and the
filename tag cannot distinguish the two candidates, because a non-caption `--data-path` leaves the tag
unchanged: both the default glob and
`--data-path paper3/train-00000-of-00001-a09b74b3ef9c3b56.parquet` produce exactly
`verify_r5_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_a10`. Every archived 20-sample command in
`cloud_p3/` omits `--data-path`, so the round keeps the default and verifies that the default glob's
first entry is the canonical Alpaca shard before each run. The other unrecorded fields
(`--model-path`, the exact interpreter, the GPU) do not affect the numbers as long as the model
directory is the same and the stack is the archived one.

The runner also validates the produced JSON against the archived `trainable` counts
(r5: vision 737280 / llm 5242880; r6: vision 884736 / llm 6291456), which catches a wrong rank,
alpha, target-module set or block configuration even if the filename looked right.

### Side files the training script rewrites

`run_training.py` always writes two files this round does not own: the untagged
`verify_r{rank}_s{seed}_lr5e-05_..._a{10,12}.json` and the per-epoch
`verify_r{rank}_s{seed}_b1_partial.json`. Both already exist for some of these seeds from the
torch 2.4/cu121 stack (seeds 123 and 999 for rank 5). The runner saves the pre-existing bytes before
each run and writes them back afterwards, so a completed round leaves the experiment directory
byte-identical apart from the six new `_torch26` files. The same protection is applied to the two
files that adapter training rewrites in job B
(`verify_r{rank}_s42_lr5e-05_nw_float1_adamw_imgs_e3_bcuniform.json` and the seed-42 partial).

## 4. Expected filenames

```
paper3/scripts/outputs/experiments/
  verify_r5_s7_lr5e-05_nw_float1_adamw_e3_bcuniform_a10_torch26.json
  verify_r5_s123_lr5e-05_nw_float1_adamw_e3_bcuniform_a10_torch26.json
  verify_r5_s999_lr5e-05_nw_float1_adamw_e3_bcuniform_a10_torch26.json
  verify_r6_s7_lr5e-05_nw_float1_adamw_e3_bcuniform_a12_torch26.json
  verify_r6_s123_lr5e-05_nw_float1_adamw_e3_bcuniform_a12_torch26.json
  verify_r6_s999_lr5e-05_nw_float1_adamw_e3_bcuniform_a12_torch26.json
outputs/analysis/
  p3_env_stack_seeds.json          # aggregation of job A (per-stack, per-rank, sigma_env)
  p3_env_seeds_runlog.json         # commands, stack, sha256 and wall time of each run
  cloud_vqa_full451_base.json      # 451 per-question records, base model
  cloud_vqa_full451_5.json         # 451 per-question records, rank 5 adapter
  cloud_vqa_full451_6.json         # 451 per-question records, rank 6 adapter
  p3_vqa_full_equivalence.json     # paired bootstrap CIs and TOST equivalence on the 451 set
cloud_next/logs/<job>.<timestamp>.log
```

The payload `name` field inside each new verify JSON deliberately stays without the stack suffix
(`verify_r5_s7_lr5e-05_nw_float1_adamw_e3_bcuniform_a10`), exactly as in the archived seed-42 rows:
`run_training.py` writes the payload, the runner adds the suffix to the filename.

## 5. Resources: expected runtime, memory, disk

Measured evidence for the 20-sample / 3-epoch / batch-1 protocol (job A), RTX 4060 Laptop, torch 2.9:

* `outputs/analysis/p3_rerun_{protocol,seeds,extra}.json` record `elapsed_min` for ten archived runs at
  ranks 5 and 6: 21.3, 21.4, 21.4, 21.5, 22.9, 23.0, 25.9, 26.6, 43.7, 65.8 minutes
  (median 23.0; the 43.7 and 65.8 outliers ran on a busy machine).
* The same protocol's console logs (`outputs/run_*.log`) report `Training time: 1265-1390 s`
  (21-23 min) and `Model loaded. VRAM: 4.1 GB`.

Budget: **~25 min per run on a laptop-class GPU, faster on a datacenter GPU; 6 runs = 2.5 h** for job A
(excluding the one-off model download).

Job B, measured on the cloud GPU that produced the 300-question archives (RTX 4080 SUPER, torch 2.12),
from the `elapsed_min` field of the archives themselves:

| Arm | Archived (300 questions) | Projection for 451 questions |
|---|---|---|
| base (no training) | 2.30 min | ~3.5 min |
| rank 5 (1793-pair `--per-step` training + eval) | 63.9 min | ~65 min |
| rank 6 (same) | 63.6 min | ~65 min |

Budget: **~2.3 h for job B**, dominated by the two adapter trainings; the adapters are cached in
`outputs/p3_vqa_adapters/r{5,6}_step`, so a re-run of the job skips the expensive part.

Round total: roughly **5 h** of GPU time (job A ~2.5 h + job B ~2.3 h) plus the model download.

Memory and disk:

* VRAM: 4-bit LLaVA-1.5-7B with batch 1 loaded in 4.1 GB (measured); 8 GB was sufficient locally.
  **Recommend at least 12 GB free, and prefer a 24 GB card** so that a larger batch or a longer
  generation budget cannot OOM. Job B holds one arm per process, so three arms never share memory.
* Disk: `models/llava-hf` 13.2 GB, `data/vqa_rad/images` 662 MB (2244 PNGs), the VQA parquets 0.2 MB,
  each adapter ~23-27 MB, and the round's JSONs are small. `HF_HOME` and `MODELSCOPE_CACHE` are
  exported to the 50 GB data disk by the entry point (never the 30 GB root disk).

## 6. Acceptance criteria

A round is accepted only when all of the following hold. `--aggregate --strict` returns 3 when its
own criteria are unmet, and `cloud_next/verify_cloud_artifacts.py --phase phase2/phase3` re-checks the
artifacts against `cloud_next/expected_outputs.json`.

1. **Six new verify JSONs with exactly the names in section 4**, each with a finite `delta_E`, an `E`
   array of four values, and the archived configuration fields (the runner validates every one of them
   and reports any field that does not match).
2. **The aggregation reports at least three seeds per rank on the torch26 stack** --
   `p3_env_stack_seeds.json` carries `ranks["5"].stacks.torch26_cu124.n` and the same for rank 6, both
   equal to 4 (seed 42 plus the three new seeds), and the trimmed acceptance key
   `torch26_at_least_three_seeds_per_rank` is `true`. The file also lists, explicitly, every
   `(stack, rank)` block that rests on one seed; before this round those are torch26 at r=5 and r=6
   and torch24_cu121 at r=6.
3. **The three VQA archives each contain 451 per-question records** (`questions`, and also `refs` and
   `hypotheses`, all length 451) **and their reference-answer lists are byte-identical across arms** --
   checked by comparing the JSON encoding of `refs` through `refs_sha256`, which is written into each
   archive and re-verified by the aggregation. The references must also equal the `output` column of
   `paper3/test-vqarad.parquet` in row order (checked by `refs_match_test_parquet_order`).
4. The archived three-stack S37 decomposition is reproduced exactly by the aggregation's frozen
   registry (sigma_env 31.1489, sigma_seed 34.2950, share 0.4520 from
   `outputs/analysis/p3_env_variance.json`) -- this is what makes a change in sigma_env attributable to
   the new seeds rather than to a change of inputs.
5. The first 300 records of each 451-question archive line up with the archived 300-question round:
   identical references, and the hypothesis-mismatch count is reported. Identical hypotheses are
   expected for the same adapters and greedy decoding; a mismatch is reported with the resulting
   accuracy/F1 deltas so that the comparison can be qualified instead of silently accepted.

## 7. What the aggregation archives contain

`outputs/analysis/p3_env_stack_seeds.json` (deterministic; no wall-clock field, so re-running on
unchanged inputs reproduces it byte for byte):

* `rows` -- one entry per archived run: stack, rank, seed, `delta_E`, `E0`, `source_file`,
  `source_field`;
* `ranks` -- per rank, per stack: `n`, `mean`, `sd`, `min`, `max`, `median`, `values_by_seed`,
  `seeds`, `single_seed`, `source_files`;
* `sigma_env`, `sigma_seed`, `env_variance_share` -- the r=5 four-stack random-effects decomposition
  (the same one-way ANOVA with the unequal-n correction `n0` as
  `tools/_p1570_env_variance_update.py`), plus `sigma_by_rank` with the three-stack reference design,
  the balanced common-seed design, the bootstrap CI of the share (10000 replicates), and the
  before-this-round values;
* `single_seed_rows` -- the explicit list required by the task;
* `acceptance` -- the booleans and counts of section 6.

`outputs/analysis/p3_vqa_full_equivalence.json` (also deterministic):

* `arms` with the same field names as the 300-question archives (`accuracy`, `token_f1`,
  `yes_no_accuracy`, `n_yes_no`) so the two sets of archives can be compared directly;
* `vqa_equivalence` -- archives, pairing rule, declared margins and the rule behind them, per-arm
  metrics, `contrasts` for base/r5, base/r6 and r5/r6 with paired percentile bootstrap CIs (`ci95`,
  `ci90`), TOST p-values at the declared margin, `min_equivalent_margin` per contrast, and a
  `claim_verdict` block;
* `rank5_equivalence` -- the rank-5 arm against the base model and against rank 6, both metrics;
* `smallest_equivalent_margin` -- the six per-contrast margins in one place;
* `comparison_to_300q_archive` -- the first-300 cross-check of section 6 item 5;
* `acceptance` and `refs_sha256`.

The contrast function is not a re-implementation: `tools/_p1595_p3_rank_separation.py`'s own
`vqa_contrast()` is imported and called with the same RNG seed and the same 20000 replicates that
produced the published 300-question numbers. The self-test runs the whole job-B aggregation on the
three real 300-question archives and confirms that all six contrast deltas equal the archived
`p3_rank_separation_extended.json` values exactly.

## 8. Downstream effect on the manuscript

Nothing below has been applied: the manuscript, the audits and the archives of the 300-question round
are untouched by this preparation round. This is the list of edits the numbers will trigger.

**S29, Table `tab:envcloud` (`paper3/paper_ieee/supplementary/supplementary.tex`, `\label{app:envcloud}`).**
The table's eight seed-42 rows stay exactly as printed (-35.5 and +42.0 for torch 2.6/cu124); the
runner's local checks and `paper3/paper_ieee/audit_pdf.py` both pin those two values and they do not
change. What changes is the caption claim about this stack, which currently reads "it is negative in
the two cu130 stacks and in the torch 2.6/cu124 stack" on the strength of one seed. After the round
the caption must carry the four-seed spread of the torch 2.6/cu124 stack, in the same form the
torch 2.4/cu121 stack already has ("gives +41.0 for seed 42 and -2.5, -2.0, +64.5 for three further
seeds"). Two outcomes, both mechanical:

* if all four r=5 values on this stack are negative, keep the "negative on this stack" wording but add
  the spread (mean, sd, min, max) so that a single seed no longer carries the claim;
* if at least one of the three new r=5 values is positive, replace the claim with the spread
  statement and note that the near-zero r=5 effect is not a cross-environment constant in this stack
  either.

The machine column also needs care: seed 42 was run on an RTX 4060 Laptop, the three new seeds on the
cloud GPU, so the stack's row group should say so (the per-run `gpu`/`torch`/`cuda` triples are in
`outputs/analysis/p3_env_seeds_runlog.json`).

**S37, Table `tab:envvar` (`\label{app:envvar}`) and the sigma values.** sigma_env becomes the
four-stack value in `p3_env_stack_seeds.json.sigma_env`, with sigma_seed and the environment share
beside it; the table gains the torch 2.6/cu124 row with its n and sd. Two warnings:

* The current archive `outputs/analysis/p3_env_variance.json` (sigma_env 31.1, sigma_seed 34.3,
  share 45%, CI [21, 75]) is **not reproducible today** and must be superseded, not merely extended:
  `tools/_p1570_env_variance_update.py` selects its "torch 2.4/cu121" bucket with the loose glob
  `verify_r5_s*_a10*.json`, which now also matches the `_a10_torch26.json` row and would match every
  future row of the same shape. Re-running that script today gives sigma_env 25.62 / sigma_seed 35.79 /
  share 0.339 instead of the archived 31.1489 / 34.2950 / 0.4520. The new runner does not use loose
  globs: it carries an explicit per-stack registry, and its self-test asserts that this registry
  reproduces the archived three-stack numbers exactly.
* The content gate `tools/_p1575_content_audit.py` reads `p3_env_variance.json` and requires
  "31.1"/"34.3"/"45"/"21" to appear in the S37 window of the supplementary. Once S37 reports the new
  numbers, that check must point at `p3_env_stack_seeds.json` (source change) instead of the stale
  archive.

**S28, `\label{app:vqa}`.** The body sentence "evaluated on 300 held-out questions", the margin rule
("a single arm on 300 questions carries a binomial standard error of about 0.027-0.028"), the table
rows (`n = 300`), and the caption's quoted deltas and TOST values all refer to the 300-question set.
After the round they must be rewritten for the full test set: 451 questions, `n = 451` in the table,
and a binomial standard error of 0.0221 at accuracy 0.33 (0.0230 at 0.3933) instead of 0.0272/0.0282.
The pre-declared margin stays at +/-0.05 -- it is pre-declared, not fitted, and the aggregation still
reports the smallest equivalent margin for every contrast. The numbers to quote (deltas, CIs, TOST
p-values, `min_equivalent_margin`, and whether the r=6 accuracy gain becomes resolved on the larger
set) must be read from `outputs/analysis/p3_vqa_full_equivalence.json`; the 300-question values in
`outputs/analysis/p3_rank_separation_extended.json` stay valid for that analysis and should not be
quoted for the 451-question claim.

`paper3/paper_ieee/audit_pdf.py` pins S28 needles to the printed PDF text -- `TOSTp=0.0074`,
`S28 accuracy reversal +0.0433`, `1793trainingpairs`, plus the two S29 archive filenames. Any rewrite
of S28's caption must update those needles in the same commit, and any S29 caption that cites new
archive filenames should extend the archive-filename list there. `docs/provenance_manifest.json`
currently points `tab:envcloud` at `p3_env_matrix3.json`, `tab:envvar` at the stale
`p3_env_variance.json`, and `tab:vqa` at `cloud_vqa1793_{base,5,6}.json` +
`p3_rank_separation_extended.json`; those `archive`/`archives` fields must be repointed at
`p3_env_stack_seeds.json`, `p3_vqa_full_equivalence.json` and the six new verify rows (the repo
requires a source line per table). `docs/P3_SUBMISSION_STATUS.md` and `docs/p3_rank_separation_text.md`
quote the 300-question numbers and the single-seed torch26 pair, and per the repository's stage-close
rule `HANDOFF.md` and `文件地图.md` need the round recorded with the archive paths.

## 9. Limits and open items

* **Hardware mixing inside the torch26 bucket.** The four runs of that stack are not on one machine
  (seed 42 on an RTX 4060 Laptop, three seeds on the cloud GPU). The decomposition treats the
  torch/CUDA stack as the environment factor; the new archive records the per-run hardware and S29's
  machine column must reflect it. If a strictly single-machine fourth environment is wanted, the
  round would have to re-run seed 42 on the instance as well (one extra command pair) -- that is a
  decision for the operator, and the runner supports it (`--seeds 42,7,123,999`).
* **Seeds are not fully crossed across stacks.** torch212 has ten seeds, torch29 five, torch24 four
  (rank 5) / one (rank 6), torch26 four. The aggregation therefore reports, next to the all-rows
  decomposition, a balanced common-seed design (the seeds present on every populated stack) so the
  effect of the unbalanced design can be seen; report both rather than choosing silently.
* **The VQA job reuses the archived adapters by construction.** The 300-question archives were
  produced with the per-step recipe and therefore with the `r5_step`/`r6_step` adapter directories:
  `cloud_p3/run_vqa_full.sh` deletes exactly those two directories before the run and passes
  `--per-step`, and the archives themselves record `meta.train_samples = 1793` and `meta.epochs = 3`.
  The plain `outputs/p3_vqa_adapters/r5` and `r6` directories that exist locally came from much
  shorter runs (16 samples/1 epoch and 40 samples/3 epochs, per the `meta` of
  `outputs/analysis/p3_vqa_downstream_{5,6}.json`) and are deliberately not used, otherwise the
  451-question numbers would move for a reason unrelated to the question count. If a `r{rank}_step`
  adapter is absent on the instance the runner trains it with the archived recipe and records
  `adapter_source: "trained_here"` plus the adapter's sha256; if it is present it records
  `pre_existing`. Either way the archive says which adapter produced it.
* **The torch26 wrapper rows are inference only.** Job A adds seeds to one stack; it does not add a
  fifth environment, and it cannot make S37's environment factor balanced (see the two items above).
* **Job A cannot be rehearsed beyond `--dry-run` locally** on this workstation, because the local
  torch is 2.9.1+cu130 and the runner refuses to write `_torch26` rows from a different stack. That
  refusal was verified (exit 2).

## 10. Local verification performed for this preparation round

All with `D:\Anaconda\envs\pytorch\python.exe` (torch 2.9.1+cu130), `PYTHONIOENCODING=utf-8`:

* `--self-test`: **52 checks, 0 failed**. Highlights: the reconstruction reproduces all 17 archived
  config fields for both ranks and predicts the archived filenames (including the untagged variant
  `verify_r5_s42.json`, which pins the `--lora-alpha` tag rule); the frozen three-stack registry
  reproduces sigma_env 31.1489 / sigma_seed 34.2950 / share 0.4520 exactly; the 300 archived VQA
  questions are the first 300 of the 451 in the same order with identical references across arms; the
  adapter-training by-product filenames match the archived files 2/2 for both ranks; the whole VQA
  aggregation runs end to end on the real 300-question archives and reproduces all six contrast deltas
  to 0.00e+00; both aggregation payloads serialise and carry the keys the cloud gate requires
  (`ranks`/`sigma_env`/`rows` and `vqa_equivalence`/`rank5_equivalence`).
* `--dry-run` for all four paths (job A, aggregation A, job B, aggregation B): every command printed,
  nothing executed, nothing written; the adapter-training command is shown verbatim by intercepting
  `subprocess` inside `tools/_p1516_p3_vqa_downstream.py` rather than by copying it.
* The non-dry job-A path aborts on this machine with `installed torch is 2.9.1+cu130, expected 2.6.x`
  and exit 2, before any run and before any write.
* `cloud_next/p3_env_seeds.sh`: `bash -n` and `bash --posix -n` both parse (exit 0); a full
  `--dry-run` rehearsal through Git Bash started all four steps as background jobs with per-step logs
  and collected exit 0 from each (the `setsid --wait` fallback path was exercised, since Git Bash has
  no `setsid`). The file is LF-only (0 CR bytes) so it is safe on Linux.
* `git status --porcelain -uall` shows no modified tracked file; the only new entries from this round
  are `tools/_p1613_p3_cloud_runner.py`, `cloud_next/p3_env_seeds.sh` and this document. None of the
  round's outputs exist locally (`p3_env_stack_seeds.json`, `p3_vqa_full_equivalence.json`,
  `cloud_vqa_full451_*.json`, `p3_env_seeds_runlog.json` and the six `_torch26` rows are all absent),
  so no archive was polluted by the rehearsal.

---

**Superseded (2026-10-24, later the same day):** the S28 section of this note was written before the 451-question run landed. See `docs/p3_vqa451_round_notes.md` for what was actually integrated into S28/S17, and `outputs/analysis/p3_vqa_full_equivalence.json` for the numbers.
