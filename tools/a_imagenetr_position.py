# -*- coding: utf-8 -*-
"""Run the Paper A ImageNet-R new-dataset positional grid on the local RTX 4060.

Protocol: ImageNet-R parquet release (30,000 images, 200 classes), deterministic image-level split
(crc32 0-7 train / 8 val / 9 test), CLIP ViT-B/32 LoRA rank 8, strict freeze, batch 64,
5000 training samples, 10 epochs, three adaptation sites x three seeds.
"""
import argparse
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
LOG = os.path.join(REPO, "local_runs", "logs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", default="text_only,both")
    ap.add_argument("--seeds", default="42,123,456")
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--max-samples", type=int, default=5000)
    ap.add_argument("--batch-size", type=int, default=64)
    a = ap.parse_args()
    os.makedirs(LOG, exist_ok=True)
    for tag in [t for t in a.tags.split(",") if t]:
        for seed in [int(s) for s in a.seeds.split(",") if s]:
            logp = os.path.join(LOG, "a_imagenetr_%s_seed%d.log" % (tag, seed))
            cmd = [PY, os.path.join(REPO, "experiments", "strict_freeze_control.py"),
                   "--dataset", "imagenet_r", "--data-dir", "data",
                   "--out-dir", "outputs/a_imagenetr/r8", "--name", "ir_", "--rank", "8",
                   "--tags", tag, "--seeds", str(seed),
                   "--epochs", str(a.epochs), "--max-samples", str(a.max_samples),
                   "--batch-size", str(a.batch_size), "--skip-frozen"]
            t0 = time.time()
            with open(logp, "wb") as f:
                subprocess.run(cmd, cwd=REPO, stdout=f, stderr=subprocess.STDOUT)
            print("done %s seed%d %.1f min" % (tag, seed, (time.time() - t0) / 60.0), flush=True)
    print("IMAGENETR_QUEUE_DONE", flush=True)


if __name__ == "__main__":
    main()
