"""
5-Seed 统计验证 — Flickr30k
============================
4 实验 × 5 seed = 20 runs
输出: outputs/flickr30k_seeds/{exp}/seed{seed}/results.json + 汇总
"""

import os, sys, json, time
import numpy as np
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from src.config import ExperimentConfig, LoRAConfig, TrainConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders

SEEDS = [42, 123, 456, 789, 1024]
DATA_DIR = "."

# 实验定义（baseline_frozen 无随机性，从已有结果取）
EXPERIMENTS = [
    ("rq1_rank4",  LoRAConfig(rank=4,  alpha=8,   apply_to_vision=True,  apply_to_text=True)),
    ("rq1_rank32", LoRAConfig(rank=32, alpha=64,  apply_to_vision=True,  apply_to_text=True)),
    ("rq2_text_only", LoRAConfig(rank=8, alpha=16, apply_to_vision=False, apply_to_text=True)),
    ("baseline_full_ft", None),  # full fine-tune
]

OUTPUT_DIR = "./outputs/flickr30k_seeds"


def set_seed(seed):
    torch.manual_seed(seed)
    np.random.seed(seed)


def run_one(name, lora_cfg, seed):
    set_seed(seed)

    config = ExperimentConfig(
        name=name,
        lora=lora_cfg,
        train=TrainConfig(
            dataset="flickr30k",
            batch_size=128,
            num_epochs=10,
            max_samples=5000,
            save_dir=f"{OUTPUT_DIR}/{name}/seed{seed}",
            gradient_accumulation_steps=4 if lora_cfg is None else 1,
        ),
    )

    train_loader, val_loader, _ = create_dataloaders(
        dataset_name="flickr30k",
        data_dir=DATA_DIR,
        batch_size=config.train.batch_size,
        max_samples=config.train.max_samples,
    )

    trainer = GapAwareTrainer(config)
    result = trainer.train(train_loader, val_loader)
    return result


def summarize(all_results):
    """计算 mean ± std 并输出汇总表"""
    print("\n" + "=" * 80)
    print("5-Seed 统计验证 — 汇总")
    print("=" * 80)

    summary = {}
    for exp_name in all_results:
        runs = all_results[exp_name]
        cg_deltas = []
        r1_values = []

        for seed, r in runs.items():
            cg_init = r.get("initial_gap", {}).get("centroid_gap", None)
            cg_final = r.get("final_gap", {}).get("centroid_gap", None) if r.get("final_gap") else None
            if cg_init is not None and cg_final is not None:
                cg_deltas.append(cg_final - cg_init)

            r1 = r.get("final_task_metrics", {}).get("R@1", None)
            if r1 is not None:
                r1_values.append(r1)

        summary[exp_name] = {
            "cg_delta_mean": np.mean(cg_deltas) if cg_deltas else None,
            "cg_delta_std": np.std(cg_deltas) if cg_deltas else None,
            "r1_mean": np.mean(r1_values) if r1_values else None,
            "r1_std": np.std(r1_values) if r1_values else None,
            "n_runs": len(runs),
        }

    print(f"\n{'Experiment':25s} {'CG Δ mean ± std':25s} {'R@1 mean ± std':25s}")
    print("-" * 75)
    for exp_name, s in summary.items():
        cg_str = f"{s['cg_delta_mean']:+.4f} ± {s['cg_delta_std']:.4f}" if s['cg_delta_mean'] is not None else "N/A"
        r1_str = f"{s['r1_mean']:.4f} ± {s['r1_std']:.4f}" if s['r1_mean'] is not None else "N/A"
        print(f"{exp_name:25s} {cg_str:25s} {r1_str:25s}")

    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(f"{OUTPUT_DIR}/summary.json", 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n📁 汇总: {OUTPUT_DIR}/summary.json")

    return summary


def main():
    total_start = time.time()
    all_results = {}

    total_runs = len(EXPERIMENTS) * len(SEEDS)
    run_idx = 0

    for exp_name, lora_cfg in EXPERIMENTS:
        all_results[exp_name] = {}
        for seed in SEEDS:
            run_idx += 1
            save_dir = f"{OUTPUT_DIR}/{exp_name}/seed{seed}"
            if os.path.exists(f"{save_dir}/results.json"):
                print(f"\n⏭ [{run_idx}/{total_runs}] {exp_name} seed={seed} — 已完成，跳过")
                with open(f"{save_dir}/results.json") as f:
                    all_results[exp_name][seed] = json.load(f)
                continue

            print(f"\n{'='*60}")
            print(f"[{run_idx}/{total_runs}] {exp_name} seed={seed}")
            print(f"{'='*60}")

            start = time.time()
            result = run_one(exp_name, lora_cfg, seed)
            elapsed = time.time() - start

            # 保存
            os.makedirs(save_dir, exist_ok=True)
            with open(f"{save_dir}/results.json", 'w') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            all_results[exp_name][seed] = result

            r1 = result.get("final_task_metrics", {}).get("R@1", "N/A")
            loss = result.get("final_train_loss", "N/A")
            print(f"   ✅ seed={seed}: R@1={r1}, loss={loss}, time={elapsed:.0f}s")

    total = time.time() - total_start
    print(f"\n🎉 5-Seed 验证完成！总耗时: {total/60:.0f} 分钟")

    summary = summarize(all_results)
    return all_results, summary


if __name__ == "__main__":
    main()
