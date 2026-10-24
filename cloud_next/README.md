# cloud_next - prepared bundle for the next cloud GPU round

Nothing in this directory runs automatically, and no cloud instance is required to prepare it. It is the
staged, resumable plan for the four remaining GPU jobs, together with the gate that must pass before the
instance is shut down.

| Phase | Job | Entry point | Why it matters |
|---|---|---|---|
| 1 | Decoder objective x scale ladder (decisive) | `run_all.sh phase1` | Turns Paper A Section H from "cannot attribute" into "the objective is separated; scale x family remains" |
| 2 | P3 environment-stack seeds | `p3_env_seeds.sh` | Gives the torch 2.6 stack more than one seed, so the sigma_env / sigma_seed decomposition in S37 is not single-seed |
| 3 | P3 VQA on the full 451-question test set | `p3_env_seeds.sh` (second job) | Separates the rank-5/rank-6 accuracy reversal from the 300-question sampling noise |
| 4 | A23 multi-encoder transfer | `a23_encoders.sh` | Widens the "no threshold transfers" claim from two adapted encoders to six |

## Read this first

- `docs/CLOUD_RUNBOOK_2026-10-24.md` - the operator runbook: preconditions, commands, acceptance criteria,
  retrieval and the mandatory shutdown order.
- `cloud_next/expected_outputs.json` - the single source of truth for what a completed round must produce.
- `cloud_next/verify_cloud_artifacts.py` - the gate: it checks every expected artifact, then prints the
  retrieval list. It exits non-zero if anything is missing or malformed, and the instance must NOT be shut
  down while it fails.

## Order of operations

```bash
bash cloud_next/env_setup.sh          # caches, mirror probe, model fetches, sanity checks
bash cloud_next/run_all.sh phase1     # decisive decoder experiment (longest)
bash cloud_next/run_all.sh phase2     # P3 env-stack seeds
bash cloud_next/run_all.sh phase3     # P3 VQA full test set
bash cloud_next/run_all.sh phase4     # A23 multi-encoder transfer
python cloud_next/verify_cloud_artifacts.py --apply
```

Every phase is resumable: a job whose output already exists and validates is skipped, so re-running a
phase after an interruption costs nothing.

## Retrieval

Artifacts stay on the instance only until they are pulled back and verified locally:

```bash
# from the laptop, with the port and password of the current instance
scp -P <PORT> -r root@<HOST>:/root/autodl-tmp/p3work/outputs/analysis/  outputs/analysis/
scp -P <PORT> -r root@<HOST>:/root/autodl-tmp/p3work/paper3/scripts/outputs/experiments/ paper3/scripts/outputs/experiments/
python cloud_next/verify_cloud_artifacts.py --apply   # re-run locally after the copy
```

Only after that gate passes locally may the instance be stopped (see the runbook for the exact shutdown
sequence required by this repository).