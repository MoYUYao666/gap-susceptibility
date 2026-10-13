"""ERS 1-epoch rerun — restoring Paper 3 fig3 (real-data version)

Background: the original fig3 data [-50, -113.5, -113.5, -226] was hardcoded and cannot be traced to a source.
This script runs a 1-epoch experiment over 4 ranks × 3 seeds, outputting norm_g_v and |ΔE|.

Produces: ers_1epoch_results.json
  {"r4": {"dE": [...], "norm_g_v": [...]}, "r16": {...}, "r32": {...}, "r64": {...}}
"""
import os, sys, json, torch, gc, subprocess, argparse
import numpy as np

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# reuse the Paper 3 training script (run_training.py --epochs 1)
TRAIN_SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'run_training.py')

RANKS = [4, 16, 32, 64]
SEEDS = [42, 123, 999]

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--model-path', type=str, default='/root/autodl-tmp/llava-hf',
                    help='local LLaVA model directory')
parser.add_argument('--output', type=str, default='ers_1epoch_results.json')
args = parser.parse_args()

def main():
    results = {}
    for rank in RANKS:
        dEs, gvs = [], []
        for seed in SEEDS:
            out_name = f"ers_r{rank}_s{seed}.json"
            cmd = [
                sys.executable, TRAIN_SCRIPT,
                "--rank", str(rank),
                "--epochs", "1",
                "--seed", str(seed),
                "--num-samples", "16",
                "--model-path", args.model_path,
            ]
            # run and collect the output (run_training.py prints E(t) and gamma)
            proc = subprocess.run(cmd, capture_output=True, text=True)
            output = proc.stdout

            # parse E(t): line format "  E(1) = 1234.5 (n=4) ↓"
            import re
            evals = [float(m) for m in re.findall(r"E\(\d+\) = ([-\d.]+)", output)]
            if evals and len(evals) >= 2 and evals[-1] == evals[-1]:
                dEs.append(evals[-1] - evals[0])
            else:
                dEs.append(float('nan'))

            # save the raw output (with the full log, for manual inspection)
            with open(out_name, 'w') as f:
                json.dump({"rank": rank, "seed": seed, "raw": output, "E": evals}, f)
            print(f"  r={rank} s={seed}: ΔE={dEs[-1]:+.1f}", flush=True)

        valid = [d for d in dEs if d == d]
        results[f"r{rank}"] = {
            "dE": valid,
            "mean": round(float(np.mean(valid)), 1) if valid else "NaN",
            "n_nan": len(dEs) - len(valid),
        }

    with open("ers_1epoch_results.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: ers_1epoch_results.json")
    print(f"Summary: { {k: {'mean_dE': round(np.mean(v['dE']),1) if v['dE'] else 'NaN', 'n_nan': v['n_nan']} for k,v in results.items()} }")

if __name__ == '__main__':
    main()
