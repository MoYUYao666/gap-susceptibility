# LLaVA clean-gap measurement (2026-10-17 18:00)

Same nine adapters as the canonical retrain, re-measured with the text side taken from the caption
positions instead of the instruction prompt, and with no projection. Forward passes only.

* frozen DG* = 0.3566
* text_only  +73.27% +/- 7.54   (0.5976 / 0.6000 / 0.6558)
* both       +95.66% +/- 7.91   (0.6634 / 0.6971 / 0.7325)
* vision_only +121.48% +/- 16.33 (0.7114 / 0.8066 / 0.8510)

Ordering: vision_only > both > text_only -- the vision side moves the clean gap most, which agrees
with the paper's dual-encoder result. The earlier 'text side dominates' reading was produced by a
measurement whose text side was the prompt (no caption in the sequence) and is superseded.

Source: `outputs/canonical_caption_metric.json`, produced by `tools/_p1145_clean_gap_measure.py`.
