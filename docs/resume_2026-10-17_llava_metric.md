# Resume note: LLaVA canonical-metric recomputation (2026-10-17)

## The task

Recompute DG*/CG for the twelve archived LLaVA runs under the canonical definition in `src/dg_star_tracker.py:compute` (the one `tools/_p47_qwen_train.py` says it matches), because the archived records used a different formula written into `tools/_p820_llava_sites.py`.

```
DG*  = mean_i || I_i - T_i ||^2      (paired, squared, after L2 normalisation)
CG   = || mean_i I_i - mean_i T_i ||
DG_e = sqrt(CG^2 + || sigma_I - sigma_T ||^2)
```

Embeddings as in `_p47`: last hidden state, mean-pooled over non-padding positions (text) and over image-token positions (vision). **No training is needed** -- the adapters are saved.

## First check before anything else

Run the **frozen** arm only. The archived frozen run moves 0.261161 -> 0.261937 under the old definition; if the canonical definition moves it comparably, the quantity cannot resolve anything on this model and the work stops with an honest report.

## Measured on the 2026-10-16 host (weste:43147, RTX 4080 SUPER, fresh instance)

| Source / route | Rate |
|---|---|
| pypi.tuna.tsinghua.edu.cn | 3.1-4.6 MB/s |
| download.pytorch.org | 0 B/s (stalled at 476 MB) |
| huggingface.co | unreachable |
| hf-mirror.com (host 3's method) | ~0.5 MB/s -- host 3 got 30-40 MB/s |
| ModelScope, single connection | ~1 MB/s (throttled) |
| **ModelScope, 32 range connections** | **13-18 MB/s** (reached 9.9 GB of 15 GB) |
| images.cocodataset.org, annotation archive | ~400 B/s single; multi-connection did not start |

## Reusable pieces (all local)

- `tools/_p1060_recompute_canonical.py` -- the recomputation, forward passes only
- `tools/_p1083_parallel_fetch.py` -- multi-connection downloader, resume-safe, proven
- `tools/_p1088_coco_fixture.py` -- fetch and trim the COCO fixture in the original id order
- `outputs/llava_bf16_sites_cloud/` -- the 7 adapters and 12 records -- the only input

## Suggested order tomorrow

1. probe the new host's sources (`tools/_p1063`, `tools/_p1065`);
2. weights: **mirror first** -- `HF_ENDPOINT=https://hf-mirror.com`, `HF_HOME=/root/autodl-tmp/hf`, then `snapshot_download('llava-hf/llava-1.5-7b-hf')` (host 3: 15 GB in 6-8 min). If it is slow on the new host, fall back to the multi-connection ModelScope fetcher (`tools/_p1083_parallel_fetch.py`, proven 13-18 MB/s). Measure first, as the rule requires -- the mirror gave 0.5 MB/s on the 2026-10-16 host and 30-40 MB/s on host 3;
3. COCO annotations plus the 500 held-out images, obtained with many connections;
4. `python tools/_p1060_recompute_canonical.py --arms frozen`;
5. only if frozen is stable, run the other three arms, then put the numbers through `tools/_claim_ledger.py` before touching Section F.

**Do not mix** the recomputed numbers with the archived twelve: they are different quantities, and each must name its own script and field.
