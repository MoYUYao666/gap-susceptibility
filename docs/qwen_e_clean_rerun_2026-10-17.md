# Qwen2-VL-2B clean re-run (2026-10-17 19:55)

Same training protocol as `tools/_p47_qwen_train.py` (400 samples, 3 epochs, batch 2, rank 8,
alpha 16, contrastive objective, 13 seeds per arm), with the measurement corrected: the text side
is the caption span rather than every non-padding position, and the two fixed random projections
are removed. Produced by `tools/_p1150_qwen_clean_sweep.py`; baseline by
`tools/_p1163_qwen_frozen_baseline.py`.

* frozen clean DG* = 0.777826 (CG 0.742107)
* both         ep3 0.0111, reduction 98.57% +/- 0.44, legacy 2.0192
* text_only    ep3 0.0253, reduction 96.74% +/- 0.29, legacy 2.0103
* vision_only  ep3 0.0824, reduction 89.41% +/- 1.01, legacy 2.0322

Ordering: both > text_only > vision_only in reduction, i.e. vision-only moves the clean gap
least; the legacy construction stays at ~2.0 for every arm, which is the two random projections
talking, not the gap.

Note the objective differs from the LLaVA run (contrastive here, caption cross-entropy there), so
the two tables are not compared in magnitude -- only in which side is least/most consequential.
