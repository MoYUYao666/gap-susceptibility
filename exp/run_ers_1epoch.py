"""ERS 1-epoch 重跑 — 恢复 Paper 3 fig3（真实数据版）

背景：原 fig3 数据 [-50, -113.5, -113.5, -226] 是硬编码的，无法溯源。
本脚本跑 4 ranks × 3 seeds 的 1-epoch 实验，输出 norm_g_v 和 |ΔE|。

产出：ers_1epoch_results.json
  {"r4": {"dE": [...], "norm_g_v": [...]}, "r16": {...}, "r32": {...}, "r64": {...}}
"""
import os, sys, json, torch, gc, subprocess, argparse
import numpy as np

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 复用 Paper 3 训练脚本（run_training.py --epochs 1）
TRAIN_SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'run_training.py')

RANKS = [4, 16, 32, 64]
SEEDS = [42, 123, 999]

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--model-path', type=str, default='/root/autodl-tmp/llava-hf',
                    help='本地 LLaVA 模型目录')
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
            # 运行并收集输出（run_training.py 打印 E(t) 和 gamma）
            proc = subprocess.run(cmd, capture_output=True, text=True)
            output = proc.stdout

            # 解析 E(t): 行格式 "  E(1) = 1234.5 (n=4) ↓"
            import re
            evals = [float(m) for m in re.findall(r"E\(\d+\) = ([-\d.]+)", output)]
            if evals and len(evals) >= 2 and evals[-1] == evals[-1]:
                dEs.append(evals[-1] - evals[0])
            else:
                dEs.append(float('nan'))

            # 保存原始输出（含完整日志，便于人工核查）
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
