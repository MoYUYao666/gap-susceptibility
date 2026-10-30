# Paper A power upgrade — plan and ready-to-run procedure

**Started 2026-10-26, after the operator said "变强吧，开始".**
Purpose: the only remaining weakness identified by our own reviews is **statistical power**, not novelty:

- allocation comparison: 6 seeds per arm, while the paper itself computes that separating a 3570 ΔE difference
  needs **11-28 seeds per arm** (`experiments.tex`, "resolution limit" paragraph);
- random-pool paired comparison: **n = 4** pairs, archived verdict `UNDERPOWERED_TO_DISTINGUISH`;
- several controls mix 3 / 5 / 10 seed families, which is what a referee attacks first.

## Target design

| arm | current | target | why |
|---|---|---|---|
| Γ-guided allocation vs uniform (capacity-matched) | 6 seeds | **16 seeds** | puts the paired CI inside the 11-28 range the text itself demands |
| random same-budget pool, seed-paired | 4 pairs | **12 pairs** | converts "underpowered" into a resolved comparison |
| strict-freezing position arms | 5 seeds | 10 seeds (only if time allows) | tightens Table 1 bootstrap intervals from ±0.004 |

Cost estimate: 4-bit 7B LoRA training, 10 epochs, 5000 samples -> about 35-50 min per arm on an A800.
16 + 16 allocation arms + 12 random-pool arms ≈ 44 arms ≈ **1.5 GPU-days serial**, roughly **14-18 h** at
parallelism 2-3 (VRAM measured first, per the cloud parallelism rule).

## Hard gates before any training (cloud rule, in this order)

1. `--plan` prints inputs, fairness checks, will-write file names; exit 0.
2. `--self-test` runs the assertion set; exit 0.
3. `--dry-run` prints every command and every number that will be written; exit 0.
4. **Naming-conflict check**: every arm writes `<arm>__seed<seed>.json`; the seed set must be disjoint from the
   six archived seeds (42, 123, 456, 789, 1011, 1213) so nothing overwrites an archive file.
5. One-arm smoke run on the cloud, artefacts inspected, then full batch.

## Execution (unattended, per the cloud rules)

```
# per batch (disjoint arms, one detached process each)
setsid nohup python run_alloc_arm.py --arm <arm> --seed <seed> > logs/<arm>_<seed>.log 2>&1 &
```
`logs/parallel_plan.txt` records the exact commands and the measured peak VRAM that justified the batch size.
After every batch: `ps aux` check, per-arm assertion, retrieve the JSONs, hash them, and only then shut down
(`sync && shutdown -h now`) with a port probe afterwards to confirm the instance is off.

## Acceptance criteria

- 16-seed allocation contrast: paired CI must exclude zero (or, if it does not, the paper reports the new power
  explicitly — a wider CI at 16 seeds is still an improvement, because it is *resolved* rather than underpowered).
- 12-pair random-pool contrast: the verdict in `p3_alloc_runs/*/analysis` moves off `UNDERPOWERED_TO_DISTINGUISH`
  one way or the other.
- Every new number registered in `docs/QUANTITY_REGISTRY.json` with its canonical value; `claim_ledger` entry added;
  the manuscript's "resolution limit" paragraph updated with the measured power.

## Blocker

The AutoDL instance used for the earlier rounds is **shut down** (port probe false). To run this I need the operator
to start an instance and give its host / port / password (or confirm an existing one). Nothing here can start a GPU
by itself, and no weights are downloaded locally by rule.
