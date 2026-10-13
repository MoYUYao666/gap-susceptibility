"""Second-dataset phase-transition validation — decoupling dataset vs architecture

Goal: the phase transition in Paper 3 was only validated on Alpaca. Reviewers asked for a second instruction-tuning dataset.
Use LLaVA-Instruct-158K (real images, compared against blank images) to check whether r_c is stable.

Note: this experiment uses real images (unlike the blank images of the main experiment),
to test whether the phase transition is an architectural phenomenon or a dataset artifact.

Output: vqa_phase_results.json
  {"r4": {"dE": [..3 seeds..]}, "r5": {...}, ..., "r20": {...}, "r24": "NaN"}

Dataset options (choose one):
1. LLaVA-Instruct-158K (the official LLaVA fine-tuning set, real images + instructions)
2. OK-VQA (needs download, ~9GB)
3. ShareGPT (text-only instructions, no images — keeps the blank images design)

Recommended: LLaVA-Instruct-158K, closest to the original setting and with real images.
"""
import os, sys, json, torch, gc, subprocess, argparse
import numpy as np

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

TRAIN_SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'run_training.py')

# same as the original sweep: 15 ranks × 3 seeds
RANKS = [4,5,6,7,8,10,12,14,16,20,24,28,32,48,64]
SEEDS = [42, 123, 999]

import argparse
ap = argparse.ArgumentParser()
ap.add_argument('--model-path', type=str, default='/root/autodl-tmp/llava-hf',
                help='local LLaVA model directory')
ap.add_argument('--output', type=str, default='vqa_phase_results.json')
vqa_args = ap.parse_args()
DATA_PATH = os.environ.get("VQA_DATA_PATH", None)  # e.g. ./llava_instruct/train.parquet

def main():
    if DATA_PATH is None:
        print("ERROR: please set VQA_DATA_PATH to the parquet of the second dataset")
        print("  export VQA_DATA_PATH=/path/to/your_dataset.parquet")
        sys.exit(1)
    results = {}
    for rank in RANKS:
        dEs = []
        for seed in SEEDS:
            cmd = [
                sys.executable, TRAIN_SCRIPT,
                "--rank", str(rank),
                "--epochs", "3",
                "--seed", str(seed),
                "--num-samples", "16",
                "--data-path", DATA_PATH,
                "--model-path", vqa_args.model_path,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            import re
            evals = [float(m) for m in re.findall(r"E\(\d+\) = ([-\d.]+)", proc.stdout)]
            if evals and len(evals) >= 2 and evals[-1] == evals[-1]:
                dEs.append(evals[-1] - evals[0])
            else:
                dEs.append(float('nan'))
            print(f"  r={rank} s={seed}: ΔE={dEs[-1]:+.0f}", flush=True)

        valid = [d for d in dEs if d == d]
        results[f"r{rank}"] = {
            "dE": valid,
            "mean": round(np.mean(valid),1) if valid else "NaN",
            "std": round(np.std(valid),1) if len(valid)>1 else 0,
            "n_nan": len(dEs) - len(valid),
        }

    with open("vqa_phase_results.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: vqa_phase_results.json")
    # phase-transition point detection
    for rank in sorted(results.keys(), key=lambda x: int(x[1:])):
        m = results[rank]["mean"]
        print(f"  r={rank[1:]}: ΔE={m}")

if __name__ == '__main__':
    main()
