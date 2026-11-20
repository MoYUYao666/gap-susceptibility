# Rank allocation and retrieval checks

Run `python -B -X utf8 replay.py` (Python 3.12+ with NumPy and SciPy). It checks hashes and recomputes recalls, paired comparisons, historical scores and the rank-stability pilot on the included numerical records.

- VizWiz and TextCaps are separate public image-to-text retrieval cases, with seven arms and three seeds per target. Within a target, seeds share the held-out query set and each arm uses the same gallery. The finite cases are not independently blinded and do not validate PACT as a utility predictor.
- PACT summarizes agreement among allocated ranks across reference-batch conditions. A wholly tied comparison is undefined, not zero. For a symmetric randomized allocation, an expectation before drawing and a worst case for the realized allocation are different quantities. A continuous equal-cost argument does not certify integer or unequal-cost allocations.
- Historical downstream results are separate. POPE uses yes/no scoring. MarineLife classification is withdrawn: 24 of 100 rows had no choice options, and there is no reduced-denominator substitute. The former adjusted multiplicity results are excluded; retained intervals are pointwise. VQA-RAD replays paired intervals and the declared-margin check. The archive has no combined run count across heterogeneous blocks.
- Historical text is replaced by numeric scoring contributions. Aggregate-only fields (such as CLIP similarity and some legacy text metrics) retain their exact archived values but cannot be reconstructed from public item scores.

The model scripts in `code/model/` are implementation references, not a standalone training or scoring chain. The VizWiz chain also needs `FitSmoke.json`, `ProjectedSource.json`, `VizWizImageIndex.json`, and private plans and staging inputs. None are included. Model-level reproduction requires the original corpora, matching preprocessing and split inputs, and model and adapter weights. Offline replay needs none of these.
