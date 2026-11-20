# Geometry and readout checks

Run `python -B -X utf8 replay.py` (Python 3.12+ with NumPy and SciPy). It verifies file hashes and reconstructs the main result summaries without changing the bundle.

- Frozen: 30 encoder–dataset cells. Caption t2i ranks image candidates by column; exact ties use optimistic rank. Grouped predictions leave out one encoder or dataset at a time. Spearman signs are not held-out R² signs.
- Controlled: 90 class runs and 270 nested checkpoints. The rank-16 comparison holds rank, not trainable parameter count, fixed. Bootstrap intervals are archived, not independently resampled by the default replay.
- Robustness: 46 runs, including 8 corrected caption-adapter runs with 24 checkpoints. External: 8 corrected caption cells and 12 retained class cells. Adapter-specific held-out effects exclude each adapter's training dataset; the pooled no-DTD check excludes all DTD cells.
- Norm-matched control: 60 targeted conditions and 3,840 seeded placebo conditions. Empirical direction distributions are descriptive, not confidence intervals or evidence of conservative coverage. The pooled class/caption group mixes relevance units. Mixed-modal retrieval is diagnostic only.
- Older caption results, duplicate smoke results and invalid aggregates are excluded. The archival consistency block is aggregate-only. The spectral inputs are derived cell statistics, not model-level reproductions.

Model-level evaluation requires separately obtained dataset inputs and model/adapter weights. The feature-level primitives in `code/` are separate from the offline score replay; no images, captions, weights or feature caches are included.
