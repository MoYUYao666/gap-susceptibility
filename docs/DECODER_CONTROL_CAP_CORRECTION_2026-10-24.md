# Correction: the local decoder control never enforced its image-token budget

Date: 2026-10-24. Author: lead session. Status: **defect confirmed and documented; archives left untouched**.

## What was wrong

`tools/_p1595_qwen_objective_control.py` (the local Paper A objective-isolation control, run earlier the same day)
intended to cap the image-token budget at 64 tokens per image and advertised exactly that in its docstring and in
the `meta` block of the four archives it wrote. The way it tried to apply the cap -

```python
proc.image_processor.max_pixels = MAX_PIXELS          # transformers 4.x spelling
proc.image_processor.size = {"longest_edge": ...}     # added later
```

- is **silently discarded by transformers 5.x** (the installed version is 5.16.1): the processor keeps its
  default `size` (`longest_edge = 12845056`), so the runs proceeded at the processor default of roughly
  **1200-2500 image tokens per image** instead of 64/144.

## Evidence

Discovered while building the matched cloud ladder (`tools/_p1612_objective_control_multimodel.py`), whose smoke
tests measure the realised token count:

* the older script's archives report `meta.image_tokens = 64` while their frozen `DG* = 1.0703125` is
  **not reproducible by any flag combination** of the new script;
* with the cap applied the way transformers 5.x honours it (`image_processor.size.longest_edge`, a pixel budget
  of about `cap x patch_size^2`), the same model at cap 196 realises ~164 tokens per image and the frozen value
  lands where the ladder's 2B rungs report it (`0.644531`);
* the new script records `meta.image_token_budget_applied_via` and **aborts** when the realised count exceeds
  `0.6 x batch x cap`, so a silently ignored budget cannot recur unnoticed.

## Consequence for the record

* The four `outputs/analysis/qwen_objective_control_*.json` archives are **kept as they are** (they are the
  provenance of what was actually run) but their protocol block is misleading: they were run at the processor's
  default resolution, not at 64 tokens per image.
* Their results (-73.5 % contrastive, -14.2 % generative on Qwen2-VL-2B) remain valid **as measurements at that
  resolution**; they are the numbers quoted in the first version of Paper A's Section H.
* The superseding evidence is the matched ladder at a properly enforced budget:
  `outputs/analysis/decoder_attribution_*.json` (5 archives, `meta.protocol = "match"`, 320 pairs, 3 epochs,
  seed 42): Qwen2-VL-2B contrastive -88.79 % / generative -3.64 %; LLaVA-1.5-7B contrastive -65.07 % /
  generative +16.12 %; Qwen2.5-VL-7B generative -34.42 %.
* Paper A's Section H now describes the earlier control as run at the processor's default resolution and uses the
  ladder as the evidence; `meta.image_token_budget_applied_via` is the field that distinguishes the two.

## Reproduce

```bash
python tools/_p1612_objective_control_multimodel.py --model qwen2vl-2b --objective contrastive --dry-run
# prints the resolved budget mode; the smoke/apply runs assert the realised token count before training
```