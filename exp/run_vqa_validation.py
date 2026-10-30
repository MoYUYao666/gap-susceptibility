"""第二数据集相变验证 — 解耦 dataset vs architecture

目的：Paper 3 的相变只在 Alpaca 上验证过。审稿人要求第二个指令微调数据集。
用 LLaVA-Instruct-158K（真实图片，与 blank images 对比）验证 r_c 是否稳定。

注意：本实验用真实图片（不同于主实验的 blank images），
用于检验相变是架构现象还是数据集 artifact。

产出：vqa_phase_results.json
  {"r4": {"dE": [..3 seeds..]}, "r5": {...}, ..., "r20": {...}, "r24": "NaN"}

数据集选择（任选其一）：
1. LLaVA-Instruct-158K（LLaVA 官方微调集，真实图片+指令）
2. OK-VQA（需要下载，~9GB）
3. ShareGPT（纯文本指令，无图片——保持 blank images 设计）

推荐：LLaVA-Instruct-158K，最接近原始设置且图片真实。
"""
import os, sys, json, torch, gc, subprocess, argparse
import numpy as np

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

TRAIN_SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'run_training.py')

# 与原 sweep 相同：15 ranks × 3 seeds
RANKS = [4,5,6,7,8,10,12,14,16,20,24,28,32,48,64]
SEEDS = [42, 123, 999]

import argparse
ap = argparse.ArgumentParser()
ap.add_argument('--model-path', type=str, default='/root/autodl-tmp/llava-hf',
                help='本地 LLaVA 模型目录')
ap.add_argument('--output', type=str, default='vqa_phase_results.json')
vqa_args = ap.parse_args()
DATA_PATH = os.environ.get("VQA_DATA_PATH", None)  # 例：./llava_instruct/train.parquet

def main():
    if DATA_PATH is None:
        print("ERROR: 请设置 VQA_DATA_PATH 指向第二个数据集的 parquet")
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
    # 相变点检测
    for rank in sorted(results.keys(), key=lambda x: int(x[1:])):
        m = results[rank]["mean"]
        print(f"  r={rank[1:]}: ΔE={m}")

if __name__ == '__main__':
    main()
