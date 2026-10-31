# Repository layout after the 2026-10-28 tidy-up

Rule applied: nothing is deleted; everything that is no longer part of an active pipeline moved under `弃用/` with a move
manifest (`弃用/_organization_manifest_2026-10-28.json`). Active gates must keep passing afterwards, so any directory that a
gate reads was left in place.

## Active (do not move)

| path | role |
|---|---|
| `paper_a1/`, `paper_a2/`, `paper3/paper_ieee/`, `paper合/`, `paper_review_prl/` | the five live manuscript trees |
| `paper_rsvlm_survey/` | the new remote-sensing VLM survey (draft + verified corpus + MDPI package) |
| `SUBMISSION/A23_JOE_next_revision/` | **current A23 upload package** (74-page manuscript, IEEE-style captions, print-legal figures) |
| `SUBMISSION/PaperA_MachineLearning*`, `SUBMISSION/A1_*`, `SUBMISSION/P3_*`, `SUBMISSION/Review_PRL/` | live submission packages |
| `SUBMISSION/A23_JOE/`, `SUBMISSION/_frozen_submitted/`, `SUBMISSION/_archive/`, `SUBMISSION/_venue_builds/` | frozen references and staged builds; **read by the verification gates** (`_p1454`, claim ledgers, `verify_a23_fix`) |
| `publish_clean/` | release mirror + source for `_claim_ledger_paperA.py` |
| `src/`, `experiments/`, `exp/`, `local_runs/`, `outputs/`, `models/`, `data/`, `external/`, `cloud_retrieved/` | code, experiments, assets and archives used for reproducibility |
| `tools/` (minus `obsolete/`), `docs/`, `HANDOFF.md`, `文件地图.md`, `AGENTS.md`, `CLAUDE.md` | working tooling and documentation |

## Moved to `弃用/` on 2026-10-28

| item | destination | why |
|---|---|---|
| `_fnpy/` | `弃用/01_临时脚本/` | third-party library clone, unused by any manuscript |
| `.git-rewrite/` | `弃用/01_临时脚本/` | git rewrite leftovers |
| `tmp_asar/` | `弃用/01_临时脚本/` | one-off DSH asar extraction |
| `tools/obsolete/` | `弃用/01_临时脚本/` | historical one-off scripts |
| `cloud_next/` | `弃用/07_旧云轮/` | old cloud-round orchestration (results already retrieved) |
| `paper_a2/submitted_rebuild/` | `弃用/09_临时/` | temporary rebuild of the submitted A23 source |
| `cloud_artifacts.tgz`, `round2_artifacts.tgz`, `round3.tgz` | `弃用/02_日志与转储/` | old cloud artefact bundles, unreferenced |
| `texput.log`, `supplementary.tex` (empty), `fig1_lambda.pdf` | `弃用/02_日志与转储/` | stray build by-products at the repository root |
| `AUTOMATION_HANDOVER.md` | `弃用/05_其他/` | superseded by `HANDOFF.md` |
| `SUBMISSION/A23_JOE_resubmission_2026-10-28/` (65-page alternative) | `弃用/09_临时/A23_JOE_baseline65_NOT_USED/` | the operator chose the current 74-page version |

## Left in place deliberately

- `backups/` (3.6 GB release archive) - backup, not deprecated.
- `data/`, `models/`, `local_runs/` (large asset directories) - reproducibility sources.
- `SUBMISSION/_venue_builds/`, `_archive/`, `_frozen_submitted/`, `A23_JOE/`, `publish_clean/` - named inline above; moving
  them breaks `_p1454_final_verify.py`, the claim ledgers or `verify_a23_fix.py`.

## Verification after the move

- `python -m tools.paper_audit selftest` -> PASS;
- `_claim_ledger.py` / `_claim_ledger_paperA.py` -> PASS;
- `_p1428_provenance_gate.py` -> PASS;
- `_p1454_final_verify.py --apply` -> **PASS WITH 15 WARNINGS**, six profiles READY, page counts match, git clean.

## `paper3/` after the 2026-10-28 tidy-up

| path | content |
|---|---|
| `paper3/paper_ieee/` | **active P3 manuscript** (10-page main, full version, supplement, audit scripts, `sections/`, `figures/`) - only the files the `p3_prl` audit profile needs remain |
| `paper3/scripts/` | analysis scripts that produced the P3 results (provenance) |
| `paper3/theory/` | four theory notes |
| `paper3/docs/` | P3 documentation moved out of the root: `PAPER3_EXPLAIN.md`, `REPRODUCE.md`, `FOR_ADVISOR.md`, `literature_review.md`, `TNNLS_unsubmit_notice.md`, the earlier decision letter (`1.md`) and the index note |
| `paper3/data/` | the prepared evaluation parquet files (VQA-RAD, instruction, caption, POPE) plus a README mapping each to its consumer |
| moved to `弃用/` | `paper3/paper/` and `paper3/paper_ICLR_backup/` (superseded manuscript versions), the temporary build folders (`_bak_archive`, `_build`, `_scratch`, `_superseded`, `_tmp`, `__pycache__`, `PRL_submission`), the old PRL-era cover letters/highlights/title pages, build by-products and two stray artefacts |

Kept in the manuscript folder because the audit profile reads them by name: `main.tex`, `main_10pp.tex`, `main_full.tex`,
their PDFs and logs, `main_body_full.tex`, `sections_full/`, `references.bib`, `audit_check.py`, `audit_pdf.py`.
