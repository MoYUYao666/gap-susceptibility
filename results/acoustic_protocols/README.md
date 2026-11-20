# Sonar and marine benchmark results

Run `python -B -X utf8 replay.py` here to verify hashes and recompute the benchmark, zero-shot, seed, and operating-point summaries. No downloads or writes.

NKSID within-domain adaptation reuses training images. Water Tank, riku-1825 and UATD use their archived benchmark splits; these are not fresh independent field validations. The reprocessed Water Tank protocol is separate. Riku shares the ten Water Tank labels and adds mine. Order predictions are reported at archived precision; text-shift cancellation is conditional, and fixed-list order does not certify the all-class winner. Calibration is exploratory.

`protocols.json` identifies evaluation scope. `records/` includes archive-level metrics, not embeddings, images or weights. To produce new zero-shot records, see `producer/` for the Python entry points; externally obtain authorized NKSID images and compatible model checkpoints. Run the producer with `--help` for local input and output paths. Inference needs PyTorch, Pillow and OpenCLIP or Transformers; InternVL also needs torchvision and trusted model-side code. Replay needs none of these.
