# Release v2.0 — analysis addendum for the five-manuscript round

Status: **released** — https://github.com/MoYUYao666/gap-susceptibility/releases/tag/v2.0 . The Zenodo version DOI for this release is minted asynchronously and is recorded in HANDOFF.md when it appears. This file is written before the release so that the tag can be created once, after all
local work is finished (see the checklist at the end). The tag for the previous snapshot, `v1.0-prl-revision`, is frozen and
must not be moved.

## What this release adds

### P3 (Pattern Recognition Letters submission `PRLETTERS-D-26-02378R1`)

- Current-protocol re-run of the rank family on the present `run_training.py` defaults (seed 42): `ΔE = -10.5` at
  `r=5`, `+115.0` at `r=6`, and `+214.5, +262.0, +298.0, +1235.0` at `r=7, 8, 10, 16`. A second seed at `r=5/6` gives
  `+8.0/+25.5`, so the `r=5` interval spans zero while `r=6` is positive in both seeds; the crossing is bracketed
  between 5 and 6 with a noisy lower edge, exactly as the main text describes. An exact permutation test on the r=5 vs
  r=6 difference gives p = 0.33 (the smallest attainable with 2+2 seeds is 0.17); it is reported as a power note, not as
  a significance claim.
- A local CLIP rank-sensitivity control and a local Qwen2-VL-2B check, both reported as boundary/limitation evidence.
- Archives: `outputs/analysis/p3_rerun_protocol.json`, `p3_rerun_extra.json`, `p3_rerun_analysis.json`,
  `p3_rank_local_control.json`, `p3_qwen2b_crossing.json`; scripts `tools/_p1358_*.py`, `_p1365_*.py`, `_p1371_*.py`.

### A1 (Pattern Analysis and Applications, under review)

- Interior-optimum monitoring validation v2 (two backbones, three seeds, ten epochs): minimum-margin-mass selection has
  mean regret 0.41 (0.19 with the sequential rule at δ=0.01), against 3.54 for the first epoch and 0.60 for the last.
- Early-stopping baselines (third held-out domain, 60 checkpoints): margin-mass rule 0.18 mean regret against 2.80
  max-softmax, 3.15 max-logit, 3.96 entropy, 4.18 log-sum-exp energy.
- Per-epoch checkpoint hook (`outputs/a1_monitor_ckpt/`) so the monitoring history can be recomputed without retraining.
- Archives: `a1_monitor_interior_v2.json`, `a1_monitor_interior_v2_rules.json`, `a1_stopping_baselines.json`,
  `a1_stopping_baselines_rules.json`, `a1_monitor_ckpt.json`.

### A23 (IEEE Journal of Oceanic Engineering `26-0663`)

- Adapted-encoder margin certificate (BioCLIP/OceanCLIP): the margin mass is only weakly correlated with accuracy and its
  threshold does not transfer, while order preservation τ tracks accuracy at r ≈ +0.85/+0.81; the paper keeps the
  within-domain order diagnostic.
- Threshold transfer extended to twelve archived domain arms (cross-domain balanced accuracy stays at chance).
- Second acoustic corpus (UATD-derived detection crops, eleven classes) under the same gap-surgery protocol. It is
  class-wise out of distribution for both marine encoders (top-1 7.3-13.6% against a 9.1% chance level), so no ordering
  relation can be estimated there; it is reported as the boundary of the diagnostic's domain, not as a replication.
- Archives: `a23_certificate_adapted.json`, `a23_threshold_transfer.json`, `a23_threshold_transfer_extended.json`,
  `a23_tau_control.json`, `a23_uatd_domain.json`.

### Commentary (Pattern Recognition Letters `PRLETTERS-D-26-02402`)

- Three 2026 citations and an explicit scope sentence (why the gap matters vs which reported number is comparable).
- A compact six-instance table and a "what reporting would change" paragraph, both inside the seven-page limit.

## Citation guidance

- The submitted papers cite the **version DOI of the frozen v1.0 snapshot** (`10.5281/zenodo.23341223`). That record is
  unchanged and remains the reference for the submitted manuscripts.
- After the v2.0 release, Zenodo will mint a **new version DOI** under the same concept DOI. v2.0 should be cited only where
  the added analyses are used, and always as a specific version DOI (not the concept DOI).

## Release checklist (to execute only after everything is finished)

1. all tests/audits green; working tree committed;
2. `publish_clean` up to date with the live staging list, boundary check: 0 manuscript files, 0 files > 100 MB;
3. final `git -C publish_clean push ssh-origin main`;
4. create **one** new tag `v2.0` on the published commit and a GitHub release pointing at it; never move the tag afterwards;
5. verify the Zenodo record and record the new version DOI in `HANDOFF.md` and `文件地图.md`;
6. do not touch `v1.0-prl-revision`.
