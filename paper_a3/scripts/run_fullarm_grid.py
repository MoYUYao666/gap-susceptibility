# -*- coding: utf-8 -*-
r"""Run full-corpus arm comparisons (one text per image, no budget ceiling).

Usage
  python run_fullarm_grid.py --dataset rsicd --arms human,templated,metadata,llmcaption --seeds 0,1
"""
import argparse
import io
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
IMAGES = {"rsicd": "data/rsicd", "nwpu_captions": "data/nwpu_captions"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="rsicd")
    ap.add_argument("--arms", default="human,templated,metadata,llmcaption")
    ap.add_argument("--seeds", default="0,1")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    seeds = [int(s) for s in args.seeds.split(",")]
    runs = os.path.join(ROOT, "runs", "fullarm_%s%s" % (args.dataset, ("_" + args.tag) if args.tag else ""))
    os.makedirs(runs, exist_ok=True)
    for arm in arms:
        corpus = os.path.join(ROOT, "corpora", args.dataset, "full_%s.jsonl" % arm)
        if not os.path.exists(corpus):
            print("missing corpus", corpus)
            continue
        for seed in seeds:
            name = "%s_%s_s%d" % (args.dataset, arm, seed)
            out = os.path.join(runs, name)
            if os.path.exists(out + ".json"):
                print("skip", name)
                continue
            cmd = [PY, "-u", os.path.join(ROOT, "scripts", "train_lora_provenance.py"),
                   "--corpus", corpus, "--images-root", os.path.join(ROOT, IMAGES[args.dataset]),
                   "--model", os.path.join(ROOT, "models", "RemoteCLIP-ViT-B-32.pt"),
                   "--site", "both", "--seed", str(seed), "--epochs", "2", "--batch", "32",
                   "--max-pairs", "0", "--workers", "8", "--one-per-image", "--out-prefix", out]
            print("start", name, flush=True)
            t0 = time.time()
            with io.open(os.path.join(runs, "log_%s.txt" % name), "wb") as f:
                rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT).returncode
            print("%s %s in %.1f min" % ("OK" if rc == 0 else "FAIL", name, (time.time() - t0) / 60), flush=True)
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
