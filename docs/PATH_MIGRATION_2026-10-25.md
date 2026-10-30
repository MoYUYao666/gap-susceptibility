# Path migration after the retirement (2026-10-25)

The operator asked to (a) audit only the latest drafts from now on and (b) move everything deprecated into the
alternatives folder, renaming that folder to `弃用` ("deprecated"). This file is the authoritative mapping, so a
reader who meets an older path knows where the material went.

**Rule added the same day** (see `AGENTS.md` / `CLAUDE.md`, section 审核范围规则): audits, gates and reproduction
ledgers cover only the five live manuscript trees (`paper_a1/`, `paper_a2/`, `paper3/paper_ieee/`, `paper合/`,
`paper_review_prl/`); **`弃用/` never enters an audit**; frozen `SUBMISSION/` packages are checked for hash
integrity only.

## Rename

| before | after |
|---|---|
| `备选/` | **`弃用/`** |

## Moves into `弃用/`

| before | after | files |
|---|---|---|
| `paper2/` | `弃用/06_归档稿件/paper2/` | 73 |
| `_bibbackup_20260918/` | `弃用/08_历史归档/_bibbackup_20260918/` | 4 |
| `cloud_round2/` | `弃用/07_旧云轮/cloud_round2/` | 51 |
| `cloud_round3/` | `弃用/07_旧云轮/cloud_round3/` | 149 |
| `cloud_p3/` | `弃用/07_旧云轮/cloud_p3/` | 40 |
| `cloud_pack/` | `弃用/07_旧云轮/cloud_pack/` | 59 |
| `期刊指南/` | `弃用/05_其他/期刊指南/` | 13 |

`弃用/` totals **613 files / 168.6 MB**.

## Second pass (2026-10-25, later the same day): the three exceptions were moved

The first pass kept three directories at the repository root because a guard reported gate references to
them. That guard matched **naive substrings**, so its `_archive/` hits were all `SUBMISSION/_archive/...`
(a different, frozen path) - a **false positive**. A **root-anchored** re-check over 15,111 text files
found **zero** root-level references to any of the three inside the 53-script gate chain
(`tools/paper_audit/**`, `_p1428`, `_p1637`, `_p1454`, `audit_check.py`, `audit_pdf.py`,
`verify_a23_fix.py`, `_p1181`, `_final_check_prl`, `_claim_ledger*`). They were therefore moved:

| directory | files | new location | reference handling |
|---|---|---|---|
| `_archive/` | 251 | `弃用/08_历史归档/_archive/` | **none needed**: the 46 `_archive/` occurrences in `tools/paper_audit/profiles.py` and the five `tools/paper_audit/freeze/*.json` manifests are all `SUBMISSION/_archive/...` (frozen, untouched) => the 133 frozen hashes are unaffected |
| `paper/` | 111 | `弃用/06_归档稿件/paper/` | live prose in `paper3/README_是哪篇.md` updated; the prose in the **frozen** `SUBMISSION/_archive/PaperA_Neurocomputing_2026-10-12_60pp/README.md` and `SUBMISSION/_archive/_old/P1_PatternRecognition/README.md` was **left untouched** (freeze rule) and stands as a historical record of where the directory was |
| `paper_review/` | 30 | `弃用/06_归档稿件/paper_review/` | 5 live references updated: `paper_review_prl/MANUSCRIPT.md:3,4`, `DRAFT_OUTLINE.md:16`, `FIXES_2026-10-18.md:96,111`; plus `docs/commentary_compression_and_table.md` |

Every move was verified by comparing a `{relative path: (size, sha256)}` inventory before and after: all
three inventories were **identical**, and no source directory remained. Executed by
`tools/_p1661_retire_three_dirs.py` (idempotent, with the same assertions).

`弃用/` now holds **1,005 files** (613 from the first pass + 392 from this one).

## ~~Deliberately NOT moved~~ (first pass, superseded by the section above)

| directory | why it stays |
|---|---|
| `_archive/` | referenced by `tools/paper_audit/profiles.py` and the freeze manifests `a1_nn.json` / `a1_paa.json`; moving it would break the **133-hash** freeze verification |
| `paper/` | referenced by `SUBMISSION/_archive/*/README.md` (archived package records); it also owns the Paper 1 submission id `PR-D-26-10149` |
| `paper_review/` | referenced by the LIVE Commentary documents in `paper_review_prl/` (`MANUSCRIPT.md`, `DRAFT_OUTLINE.md`, `FIXES_2026-10-18.md`) |

## Consequences for older documents and scripts

* Documents written before 2026-10-25 may still name a moved path as it was at the time. They are **historical
  records and were not rewritten**; this table is the pointer.
* The historical one-off scripts under `tools/_p*.py` that mention a moved path are kept as-is by the standing rule
  ("existing revision scripts are records, not maintenance targets"). Re-running one of them would need a path
  update first - that is expected, not a defect.
* `paper_a1/FIXES_2026-10-18.md` lives in a LIVE manuscript tree, so its `期刊指南/` reference was updated to the
  new path in the same pass.
