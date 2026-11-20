# Text-provenance retrieval results

Run `python -B -X utf8 replay.py` here to verify hashes, recover paired RSICD hits and contrasts, and recompute seed-group metrics. No downloads or writes.

The paired RSICD schedules use a shared held-out human reference pool. The archived site grid and additional configurations use source-specific pools and are descriptive. The corrected subset records use image-level holdout and replace the training-set evaluations. Same-corpus and cross-corpus transfer are marked separately. Unmatched historical schedules and budgets do not establish a crossover.

`protocols.json` documents the text sources, including the local LM Studio/Qwen archive, and exclusions. `producer/` contains corpus and model code; new runs require authorized image/caption inputs, compatible checkpoints, and the producer dependencies. The images, texts, checkpoints and query-level scores are not included.

**Security:** Use only trusted adapter `.pt` files with `producer/run_transfer_eval.py`. It loads them with `weights_only=False`, so an untrusted file can execute code.
