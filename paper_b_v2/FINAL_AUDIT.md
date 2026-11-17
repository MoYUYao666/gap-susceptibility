# Paper B v2 — final sanity audit

Status: **PASS with stated limitations.** No new experiments, no cloud, no submission.

## 1. Data completeness

| Block | Files | 3-epoch complete |
|---|---:|---:|
| B32 matrix | 144 | 144 |
| B16 rank 8 | 36 | 36 |
| B16 rank 16 | 36 | 36 |
| B16 rank 32 | 36 | 36 |
| B16 rank 64 | 36 | 36 |
| **Total** | **288** | **288** |

Checkpoint total: 288 x 3 = **864**. All result JSONs exist under
`paper_b_v2/results/`; each analysis script is present under `paper_b_v2/analysis/`.

## 2. Claim audit

| Claim | Evidence | Status |
|---|---|---|
| B32: last-oracle 100/144 (69.4%) | `reanalysis.json` | PASS |
| B32: all four proxy test CIs on worse side | `inference.json` | PASS |
| B32/B16: signs recoverable | `sign_transfer.json`; B16 rank analyses | PASS |
| B16 r8/r16/r32: last-oracle 83.3/75.0/69.4% | B16 validation JSONs | PASS |
| B16 r64: last-oracle 47.2%; best proxy mean better but CI includes 0 | `b16_r64_validation.json` | PASS |
| Rank-bounded conclusion | note Sec. 4.6 and interpretation | PASS |
| “Universal last-epoch dominance” | — | **not claimed** |
| New theorem / risk-controlled method | — | **not claimed** |

## 3. Build and figure/table audit

- `NOTE.pdf`: 12 pages, A4 (26 rendered references + cluster-baseline + full-P1 tables).
- Fonts: Times New Roman + STIX; no Type 3.
- 0 overfull boxes, 0 undefined references, 0 missing files.
- Tables: booktabs, caption 8 pt.
- Figures: vector PDFs, Times/STIX, CID TrueType.
- Visually inspected pages 1–6.

## 4. Residual risks

- Only one data split seed; calibration/test is by training seed.
- Three short epochs per run; last-epoch behavior may change with longer schedules.
- B16 blocks are 36 runs each; B32 is the primary matrix.
- No non-CLIP model family; no external public adapters.
- Theory is standard (T1–T3) plus a conjecture (T4), not a new theorem.

## 5. Venue assessment

| Option | Fit | Note |
|---|---|---|
| Pattern Recognition Letters | plausible after a PRL-format rewrite | short measurement/negative-result note; SCIE |
| Pattern Recognition (full) | weak as-is | 6 pages, single study family; would need expansion |
| arXiv / technical report | safe | no peer review; preserves priority |
| TPAMI | no | no TPAMI-level novelty; do not revive |

Recommendation: **do not submit yet.** Choose between a PRL-format rewrite and an arXiv technical
report; either way keep the rank-bounded conclusion.

## 6. Artifacts

- `paper_b_v2/NOTE.pdf`
- `paper_b_v2/NOTE.md`
- `paper_b_v2/manuscript/main.tex`
- `paper_b_v2/PROVENANCE.md`
- `paper_b_v2/results/*.json`
- `paper_b_v2/analysis/*.py`
