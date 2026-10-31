# Archive metadata correction, 2026-10-16

File: `outputs\llava_bf16_sites_cloud\llava_sites.json`

The twelve records came from a bfloat16 run; the summary carried a hard-coded '4-bit nf4' label written for the earlier development runs.

- `quantisation`: `4-bit nf4` -> `bfloat16 (no quantisation)`
- `caveat`: replaced with the bfloat16 wording
- `precision`: added, `bf16`
- `_label_correction`: added, keeping the original values

All 12 runs and every metric are unchanged.
