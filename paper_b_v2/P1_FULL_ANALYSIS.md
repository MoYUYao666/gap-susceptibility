# Paper B v2 — full P1 analysis (cloud, 2026-11-16)

Status: **All CLIP-B/32 and SigLIP-B/16 P1 blocks complete (216/216).**
No submission. Cloud instance shut down after retrieval.

## Coverage

| Block | n complete | n expected |
|---|---:|---:|
| CLIP-B/32 rank 6 | 36 | 36 |
| CLIP-B/32 rank 12 | 36 | 36 |
| CLIP-B/32 rank 24 | 36 | 36 |
| CLIP-B/32 rank 48 | 36 | 36 |
| CLIP-B/32 split-2 rank 16 | 36 | 36 |
| SigLIP-B/16 rank 8 | 36 | 36 |
| **Total** | **216** | **216** |

All 216 runs have 3 epochs; the three previously incomplete SigLIP runs were completed locally with the same runner.

## CLIP-B/32 full rank blocks

Cluster bootstrap by `dataset × site` (9 clusters), test split.

| Block | last = oracle | mean gap | best proxy | proxy diff [95% cluster CI] |
|---|---:|---:|---|---:|
| rank 6 | 77.8% | 0.00346 | DG:lower | **−0.00157** [−0.00470, 0.00000] |
| rank 12 | 83.3% | 0.00284 | DG:lower | **−0.00146** [−0.00438, 0.00000] |
| rank 24 | 69.4% | 0.00484 | CG:lower | 0.00000 [0.00000, 0.00000] |
| rank 48 | 63.9% | 0.01085 | top1:lower | −0.00000 [−0.01068, 0.00931] |
| split-2 rank 16 | 75.0% | 0.00606 | DG:lower | +0.00060 [−0.00923, 0.01311] |

### What this changes

- The full rank blocks **confirm the last-epoch baseline is strong** across ranks 6–48: last-oracle
  63.9–83.3%, mean gap 0.00284–0.01085.
- At ranks 6 and 12, the best proxy (DG) has a **slightly negative mean difference** (proxy better on
  average), but the cluster CI includes zero. This is **not a certified win**.
- No geometry proxy is significantly better than last epoch in any of the five full blocks.
- The rank-64 boundary from B16 is not contradicted: rank 48 is already lower (63.9%) than ranks 6–24,
  and B16 rank 64 is 47.2%.

## SigLIP-B/16 rank 8 (36/36 complete)

| Quantity | Value |
|---|---:|
| last = oracle | 30/36 = 83.3% |
| mean gap | 0.00416 |
| best proxy | DG:lower |
| proxy diff [95% cluster CI] | **+0.00323** [−0.00256, +0.01026] |

Direction is consistent with CLIP: last epoch is strong and the best proxy is not certified. This is
The block is complete (36/36).

## Manuscript interpretation

- The P1 table strengthens **external/rank validity**, not the theory claim.
- The honest headline becomes: **last epoch is strong at ranks 6–48 in CLIP-B/32 and in the SigLIP
  rank-8 pilot; no fixed geometry proxy is certified better; B16 rank 64 is the boundary.**
- Do not claim "universal last-epoch dominance"; do not claim the P1 blocks are a full SigLIP matrix.

## Sources

- `cloud/p1_full.json`; `paper_b_v2/results/p1_full.json`
- `paper_b_v2/results/p1_siglip_valid.json`
- `cloud/p1_full_2026-11-16.tar.gz`
- scripts: `cloud/build_data_cache.py` (cloud-side), `paper_b_v2/analysis/p1_full.py`,
  `paper_b_v2/analysis/p1_siglip_valid.py`
