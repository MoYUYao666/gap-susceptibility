# P3 submission status — PRLETTERS-D-26-02671

| field | value |
|---|---|
| manuscript ID | `PRLETTERS-D-26-02671` |
| title | *Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry: Identifiability, Negative Results, and Protocol Dependence* |
| journal | Pattern Recognition Letters (Elsevier) |
| submitted | 2026-10-21 |
| status updated | 2026-10-22 |
| current status | **With Editor** |
| submitted package | `SUBMISSION/P3_PRL_resubmission/` (Manuscript 10 pp; Supplementary 8 pp, S1–S17) |
| finalized local draft | `SUBMISSION/P3_PRL_next_revision/` (Manuscript 10 pp; Supplementary 18 pp, S1–S43; the 2026-10-23 freeze was 17 pp) |
| frozen draft built | 2026-10-23; rebuilt 2026-10-24 |
| draft git commit | see `git log` at freeze time; checksums in the package `SHA256SUMS.txt` |

## How the finalized draft differs from the submitted version

- **Main text:** claims, theorem, figures and title unchanged; only the discussion's limitations wording was updated
  (four-stack environment matrix, newer-family and third-family controls, high-rank curvature).
- **Supplement:** 8 → 18 pages, S1–S43 (S42 per-layer coupling on Qwen2.5-VL-3B, S43 SmolVLM third-family control added in the purely-local round). New sections: S18 curvature extension, S19 allocation baselines, S20 newer
  family, S21 captioning, S22 seeds/software matrix, S23 reference-batch sensitivity, S24 non-finite diagnostics,
  S25 instruction following, S26 newer-family seeds, S27 allocation-rule baselines, S28 VQA (full-scale),
  S29 second environment, S30 additivity residual, S31 per-layer coupling and robust statistics, S32 signed coupling
  and non-CLIP sources, S33 ten-seed crossing, S34 rank/seed/stack curvature, S35 real-image sweep, S36 per-step
  instrumentation, S37 environment-variance decomposition, S38 allocation bootstrap, S39 official IGU allocation,
  S40 Dolly replication, S41 third checkpoint family.
- **Claim status table (S17):** rewritten to 25 rows (24 plus the SmolVLM-500M row) so that every row
  matches the current evidence.

## Submission-state note

The `P3_PRL_resubmission/` directory and `SUBMISSION/_frozen_submitted/` are the submitted artifacts and must remain
untouched. The `P3_PRL_next_revision/` directory is a locally frozen candidate; no submission action accompanies this
freeze because the manuscript is still with the Editor.

## Purely-local extra round (2026-10-24)

Fourth stack (torch 2.6/CUDA 12.4): r5 -35.5, r6 +42.0. Environment-variance update: sigma_env 31.1, sigma_seed 34.3, share 45% [21, 75]. Exact permutation r=3 vs r=8: p=1.08e-5. Qwen2.5-VL-3B per-layer: layer 0 holds 98.1% of the coupling. SmolVLM-500M (three seeds): r5 -70.8/-67.2/-85.2, r6 +25.1/+53.6/+17.5, i.e. the sign change replicates in a second family with small r=6 magnitude.

## Repository DOI versions (2026-10-25)

- `v2.5` (current repository release, 2026-10-25): **10.5281/zenodo.23632347** (concept DOI `10.5281/zenodo.23341082`).
- `v2.4` (superseded release, 2026-10-24): 10.5281/zenodo.23614290.
- `v2.2` (DOI cited by the submitted manuscript PRLETTERS-D-26-02671): 10.5281/zenodo.23523263; kept frozen.
- `v2.3` (superseded release, recorded 2026-10-24): 10.5281/zenodo.23609295; kept frozen.
- `v1.0-prl-revision` (historical): 10.5281/zenodo.23341223.

### Deliberate submitted-vs-live divergence (2026-10-25)

The **submitted** P3 package (`SUBMISSION/_frozen_submitted/P3_PRL_R1` and the earlier frozen archives)
keeps `10.5281/zenodo.23523263` (v2.2): a frozen package keeps the DOI it was submitted with.
The **live draft** (`paper3/paper_ieee/main.tex`, `sections/conclusion.tex`) now cites
**`10.5281/zenodo.23632347` (v2.5, 25 October 2026)**. The two therefore differ **on purpose** - it is
the live draft tracking the current archive, not an omission. Anyone comparing the shipped PDF with the
live sources must expect this difference; the gate that pins the live DOI
(`paper3/paper_ieee/audit_check.py`, `audit_pdf.py`) was updated to the new value, and the frozen
package hashes are unchanged. See `docs/retire_exceptions_and_doi_v25_2026-10-25.md` §4.

## EM query sent (2026-10-25)

| item | value |
|---|---|
| Manuscript | `PRLETTERS-D-26-02671` (Pattern Recognition Letters) |
| Channel | Editorial Manager, "Send E-mail" to the handling editor (no files uploaded) |
| Subject | correction of one sentence and additional supplementary analyses |
| Sent | **2026-10-25** (operator confirms sent with the final plain-text version, commit `8c497f9e`) |
| Awaiting | editor's answer to the explicit either/or: upload updated files now, or hold for the revision |

**What the message said** (full text: `docs/P3_EM_UPDATE_2026-10-25.md`):
1. A one-sentence **correction**: the submitted manuscript says three of the ten random allocations are below the
   Gamma-guided arm and that "the third is lower by 264"; the archive shows only two are below (2928, 1700 as printed)
   and the next is **264 above** (+1741.35 vs +1477.45). The paragraph's conclusion (indistinguishable within noise)
   is unchanged.
2. The supplement has been extended **8 -> 26 pages (S1-S17 -> S1-S51)**; every addition bounds rather than extends
   the claims (paired allocation analysis, family-wise r_c analysis, Gamma-ordering robustness, four-stack variance
   decomposition, the POPE second downstream task, and the official-implementation comparison).
3. The archive DOI advanced **v2.2 10.5281/zenodo.23523263 -> v2.5 10.5281/zenodo.23632347**; the v2.2 snapshot stays
   available, so the submitted version remains checkable.

**Follow-up branches**
- **If the editor says upload**: build `SUBMISSION/P3_PRL_EM_update_2026-10-25/` (Manuscript.pdf 10 pp +
  Supplementary.pdf 26 pp + ChangeList.pdf), undo nothing in the frozen package, re-run
  `paper3/paper_ieee/audit_check.py` and `audit_pdf.py` before uploading, and record the upload.
- **If the editor says hold for the revision**: merge the same material into
  `SUBMISSION/P3_PRL_next_revision/` and answer the change list point by point in the revision letter.
- Either way: paste the editor's reply verbatim into this document the moment it arrives.

### Supplement page count after the visual inspection (2026-10-25)

The supplement was compiled at **26 pages** when the EM message was sent; a visual inspection then found large whitespace
blocks on pages 13-26 caused by 47 tables using `[h]` placement. Relaxing the placement specifiers
(`table*[h]` -> `table*[!t]`, `table[h]` -> `table[!htbp]`) gave the same content in **22 pages**, mean page ink
8.4 % -> 9.9 %, with 0 errors / 0 undefined / 0 overfull / 0 float-too-large. Structure is unchanged:
**46 sections, 51 tables (S1-S51)**. Both P3 audits pass and the `p3_prl` profile is READY grade A
(pass 54 / fail 0 / warn 1, the warning being the named frozen-package I-02).

The EM message therefore quoted the pre-cleanup page count (26). If the editor asks for updated files, the change list
must say: same content, **22 pages after a float-placement cleanup**, and note that the letter quoted 26.

### Second layout pass (2026-10-25 13:35)

Two visual defects were fixed after the operator's review: (i) table captions sat flush against the table body because
**IEEEtran ignores `\abovecaptionskip` for tables** - an explicit `\vspace` macro (`\tabcaptiongap`, 3pt) is now
inserted before 38 table captions, giving a visible ~6pt gap without adding a page; (ii) the last two tables had
been converted to a single column but their long `\texttt` archive paths overflowed the text block - the cells now
carry breakable short keys and the **full archive paths moved into the captions**, so provenance is unchanged.
The supplement is **22 pages / 46 sections / 51 tables**, 0 errors, 0 overfull, 0 float-too-large, and no page has
more than 20 % bottom whitespace in either column. The value needles for tables S28/S29 and the POPE table were
rebuilt as per-value needles so a float move can no longer produce a false failure.
