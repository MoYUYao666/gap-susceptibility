# Release notes - v2.5

This release adds the cloud round of 24 October 2026 and the Paper 3 improvement round of 24-25
October 2026. Like every release in this repository it contains code, result archives and
provenance metadata only.

**Not yet tagged.** These files are on `main` and form the next version; no version DOI has been
minted, because a Zenodo version DOI is created by the `v2.5` tag.

## Included

- **Cloud-round tools** (`tools/`)
  - `_p1612_objective_control_multimodel.py` - matched decoder ladder: four model registries, two
    objectives, two protocols, tower isolation, a non-finite-step guard and an A/B frozen check;
  - `_p1613_p3_cloud_runner.py` - environment-stack seeds and the 451-question VQA evaluation, with
    paired bootstrap and TOST equivalence;
  - `_p1614_a23_multi_encoder_transfer.py` - multi-encoder threshold-transfer grid;
  - `_p1615_cloud_exec.py` - the SSH/SFTP helper used to drive the instance (password from the
    environment);
  - `cloud_next/` - the prepared, resumable cloud bundle: mirror-first setup, phase driver, per-phase
    entry points, expected-output manifest and the pre-shutdown gate.

- **Paper 3 improvement round** (`tools/`)
  - `_p1634_p3_allocation_paired.py` - standalone paired re-analysis of the Gamma-guided versus
    uniform allocation claim, including reproduction of the cross-paper addendum. Under the
    capacity-matched design the Gamma-guided allocation is **not** claimed to beat the uniform one,
    and the two are not equated either;
  - `_p1635_p3_rc_family.py` - the R_c crossing per backbone family, plus the AdaLoRA boundary. The
    families do not agree: a single R_c across families is not supported;
  - `_p1636_p3_gamma_robustness.py` - the Gamma applicability boundary re-derived from the archives
    only (no new training): rank sensitivity, batch sensitivity, a noise break-even and backbone
    coverage;
  - `_p1637_p3_reproduce_all.py` - a one-command reproduction ledger that maps every number the
    Paper 3 manuscript reports to an archived source and recomputes it;
  - `_p1638_p3_balanced_env_design.py` - audit and plan for a balanced environment design at common
    seeds, with a cost estimate and a power comparison;
  - `_p1639_p3_official_igu.py` - runs the **official** IGU-LoRA allocator under the block-level
    comparison protocol and quantifies the gap to our block-level reimplementation. **Written but
    not yet executed: it needs the cloud instance;**
  - `_p1640_p3_second_downstream.py` - a **second** downstream task, POPE (object hallucination),
    evaluated with the exact conventions of the VQA-RAD check so the two are comparable. **Written
    but not yet executed: it needs the cloud instance;**
  - `_p1629_record_submitted_check.py` - records which of the 2026-10-24 consistency findings also
    exist in the already-submitted Paper 3 package;
  - `_p1631_a23_next_revision.py` - builds the A23 next-revision directory from the current working
    draft, with a hash manifest and an optional standalone compile of the source zip.

- **Result archives** (`outputs/analysis/`)
  - the five `decoder_attribution_*` ladder runs, and the three `cloud_vqa_full451_*` arms plus their
    equivalence archive;
  - `p3_env_stack_seeds.json` - the four-stack environment decomposition. Adding the fourth stack
    raises the environment share of the variance from **45.20% to 49.59%**, with two duplicate
    `(stack, rank, seed)` cells resolved by keeping the archived row the frozen three-stack
    reference bucket holds;
  - `a23_multiencoder_transfer.json` - the widened transfer test: **21 units** (7 frozen encoders x 3
    corpora), every ordered pair asked whether a margin-mass threshold fitted on the source survives
    on the target;
  - `p3_allocation_paired_stats.json`, `p3_rc_family_boundary.json`, `p3_gamma_robustness.json`,
    `p3_balanced_design_plan.json` and `p3_reproduce_manifest.json` - the archives behind the
    improvement round above;
  - refreshed claim ledgers and the final verification record.

- **Verification**
  - all repository gates pass: frozen-archive hashes (12 checked, none bad), the provenance gate, the
    A1 ledger (216 pass / 0 fail), the six manuscript audit profiles (all `READY`, grade A, 0 fail,
    0 warn), the staged-package check, and the six expected page counts. Source:
    `outputs/analysis/final_verification.json`.

## Excluded (by repository policy)

- Model weights and datasets.
- Manuscripts, cover letters, title pages, highlights and `SUBMISSION/` material: this repository
  holds code and results only.
- Method notes kept under `docs/` in the working tree. The operator asked on 2026-10-14 to keep
  `docs/` out of the public repository, because it holds reviewer reports, response plans and venue
  decisions for manuscripts that are still under review. The notes for this round therefore stay
  local, as earlier rounds' notes did.
- The result archives that a `.gitignore` fix in the live repository retroactively tracked
  (2026-08-03 to 2026-10-24 19:01, i.e. from before this round). They are part of the live
  repository's history hygiene, not of this release; publishing them would widen the scope of this
  repository rather than describe the round.