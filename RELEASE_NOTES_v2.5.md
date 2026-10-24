# Release notes - v2.5 (unreleased)

## v2.5 (unreleased) - cloud round of 24 October 2026

Not yet tagged; these files are on `main` and would form the next version.

- `tools/_p1612_objective_control_multimodel.py` - matched decoder ladder (four model registries, two objectives,
  two protocols, tower isolation, non-finite-step guard, A/B frozen check).
- `tools/_p1613_p3_cloud_runner.py` - environment-stack seeds and 451-question VQA evaluation with paired
  bootstrap and TOST equivalence.
- `tools/_p1614_a23_multi_encoder_transfer.py` - multi-encoder threshold-transfer grid (7 encoders x 3 corpora).
- `tools/_p1615_cloud_exec.py` - the SSH/SFTP helper used to drive the instance (password from the environment).
- `cloud_next/` - the prepared, resumable cloud bundle: mirror-first setup, phase driver, per-phase entry points,
  expected-output manifest and the pre-shutdown gate.
- Result archives: the five `decoder_attribution_*` ladder runs, the three `cloud_vqa_full451_*` arms plus their
  equivalence archive, and the multi-encoder transfer archive.
- Notes: the cloud runbook, the three preparation notes, and the correction note for the earlier local control's
  image-token budget.
