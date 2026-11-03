# -*- coding: utf-8 -*-
r"""Run the matched 3,000-image subset comparison for the LLM-caption arm.

All arms use exactly the same images (corpora/rsicd/subset3000_<arm>.jsonl), the same adapter and the same schedule,
so the only difference is the text source. Two seeds.

Usage
  python run_llmarm_grid2.py --plan
  python run_llmarm_grid2.py --run
"""
import argparse
import io
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
RUNS = os.path.join(ROOT, "runs", "llmarm_1k_nwpu")
LOG = os.path.join(RUNS, "grid_log.txt")
ARMS = ["human", "templated", "metadata", "llmcaption"]
SEEDS = [0, 1]
SITE = "both"
EPOCHS = 2
BATCH = 32


def cells():
    for arm in ARMS:
        corpus = os.path.join(ROOT, "corpora", "nwpu_captions", "subset1000_%s.jsonl" % arm)
        for seed in SEEDS:
            yield "%s_%s_s%d" % (arm, "subset1000", seed), corpus, seed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.plan:
        cs = list(cells())
        print("matched 1,500-image NWPU subset | arms %s | seeds %s | cells %d" % (ARMS, SEEDS, len(cs)))
        for n, c, s in cs:
            print("   ", n, "corpus exists:", os.path.exists(c))
        return 0
    os.makedirs(RUNS, exist_ok=True)
    for name, corpus, seed in cells():
        out = os.path.join(RUNS, name)
        if os.path.exists(out + ".json"):
            print("skip", name)
            continue
        cmd = [PY, "-u", os.path.join(ROOT, "scripts", "train_lora_provenance.py"),
               "--corpus", corpus, "--images-root", os.path.join(ROOT, "data", "nwpu_captions"),
               "--model", os.path.join(ROOT, "models", "RemoteCLIP-ViT-B-32.pt"),
               "--site", SITE, "--seed", str(seed), "--epochs", str(EPOCHS), "--batch", str(BATCH),
               "--max-pairs", "0", "--workers", "8", "--out-prefix", out]
        print("start", name, flush=True)
        t0 = time.time()
        with io.open(os.path.join(RUNS, "log_%s.txt" % name), "wb") as f:
            rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT).returncode
        print("%s %s in %.1f min" % ("OK" if rc == 0 else "FAIL", name, (time.time() - t0) / 60), flush=True)
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
