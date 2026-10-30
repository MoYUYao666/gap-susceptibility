# Cross-modal probe: audio-text susceptibility on real paired data

Inference only (no optimiser step). Archives:
`outputs/analysis/paperA_crossmodal_esc50.json` (real data, main) and
`outputs/analysis/paperA_crossmodal_gamma_clap_local.json` (synthetic tones, superseded).

## Real paired data: ESC-50 + LAION-CLAP

- Data: `ashraq/esc50`, 2000 five-second environmental recordings with human-annotated categories; **160 clips / 49
  classes** sampled evenly, audio resampled 44.1 -> 48 kHz. Read directly from the parquet shards.
- Backbone: `laion/clap-htsat-unfused` (audio-text), local copy.
- Memory-safe chunking: 24 clips per chunk; DG is size-weighted, tower gradient norms are root-mean-square over chunks
  (an approximation, stated rather than hidden).
- Bootstrap: **120 resamples over clips**.

| pairing | DG | grad audio | grad text | gamma audio | gamma text |
|---|---|---|---|---|---|
| **matched** captions | **0.00214** | 0.0069 | 0.0522 | 0.131 | **0.991** |
| shuffled captions (control) | 0.00370 | 0.0063 | 0.0152 | 0.382 | 0.924 |

Bootstrap 95% CI: DG [0.00206, 0.00220]; text-tower share [0.987, 0.993].

## Reading

1. The text tower carries the overwhelming share of the gap coupling on real audio-text pairs (0.991 against 0.131), the
   same qualitative direction the manuscript reports for image-text backbones.
2. The mismatch control behaves as the mechanism predicts: shuffling captions raises DG (0.00214 -> 0.00370) while the
   text-tower gradient collapses (0.0522 -> 0.0152) and the audio tower barely moves. The alignment error is registered on
   the text side.
3. It is not a PEFT-arm experiment: no adaptation sites, no seeds, no training, so it cannot be scored against the
   pre-registered predictions. It supports the direction of the cross-modal claim only.

## Status in the paper

Internal probe, not a manuscript result. One backbone, category-name captions and no adaptation arms cannot carry a
generality claim; the manuscript's evidence stays the image-text programme. This is the evidence to show (and extend)
if a reviewer asks about non-image-text pairs.
