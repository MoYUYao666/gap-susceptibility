"""
主入口 — LoRA微调CLIP的模态差距演化实验
============================================
"先出图再写论文" — 所有实验跑完自动生成5张核心图表

运行方式:
    # 单次实验
    python main.py --mode single --rank 8

    # RQ1: LoRA rank 影响
    python main.py --mode rq1

    # RQ2: LoRA 作用位置
    python main.py --mode rq2

    # RQ3: 缺失模态
    python main.py --mode rq3

    # Gap-Init 基线
    python main.py --mode gap_init

    # 所有实验 + 自动出图（核心流水线）
    python main.py --mode all --auto_viz
"""

import os, sys
os.environ["HF_HUB_OFFLINE"] = "1"  # 国内HF被墙，强制离线模式
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import argparse
import torch
import numpy as np
from pathlib import Path

from src.config import (
    ExperimentConfig, LoRAConfig, GapConfig, MissingModalityConfig, TrainConfig,
    get_all_experiments,
)
from src.dataset import create_dataloaders
from src.missing_modality import MissingModalitySimulator
from src.trainer import GapAwareTrainer
from src.visualize import generate_report


def set_seed(seed: int = 42):
    """固定随机种子"""
    torch.manual_seed(seed)
    torch.mps.manual_seed(seed)
    np.random.seed(seed)


def run_single_experiment(config: ExperimentConfig, data_dir: str = "./data"):
    """运行单个实验"""
    print(f"\n{'='*70}")
    print(f"🔬 实验: {config.name}")
    print(f"   LoRA: r={config.lora.rank if config.lora else 'full'}, "
          f"α={config.lora.alpha if config.lora else 'N/A'}")
    print(f"   Vision={config.lora.apply_to_vision if config.lora else True}, "
          f"Text={config.lora.apply_to_text if config.lora else True}")
    print(f"{'='*70}")

    # 数据加载
    train_loader, val_loader, test_loader = create_dataloaders(
        dataset_name=config.train.dataset,
        data_dir=data_dir,
        batch_size=config.train.batch_size,
        image_size=config.train.image_size,
        max_samples=config.train.max_samples,
    )

    # 训练
    trainer = GapAwareTrainer(config)
    results = trainer.train(train_loader, val_loader)

    # 测试集评估
    print("\n📊 测试集评估...")
    test_metrics = trainer._compute_retrieval_metrics(test_loader)
    results["test_metrics"] = test_metrics
    print(f"   R@1: {test_metrics.get('R@1', 0):.4f}")
    print(f"   R@5: {test_metrics.get('R@5', 0):.4f}")
    print(f"   R@10: {test_metrics.get('R@10', 0):.4f}")

    # 保存结果
    save_path = os.path.join(config.train.save_dir, config.name, "results.json")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results


def run_rq1_rank_impact(data_dir: str = "./data", max_samples=None, epochs=None):
    """RQ1: LoRA rank 对Gap的影响"""
    print("\n" + "="*70)
    print("🔬 RQ1: LoRA Rank 对模态差距演化的影响")
    print("="*70)

    results = {}
    ranks = [4, 8, 16, 32, 64]
    epoch_val = epochs if epochs else 20

    for rank in ranks:
        tc = TrainConfig(save_dir=f"./outputs/rq1_rank{rank}", num_epochs=epoch_val,
                        max_samples=max_samples)
        config = ExperimentConfig(
            name=f"rq1_rank{rank}",
            lora=LoRAConfig(
                rank=rank, alpha=rank * 2,
                apply_to_vision=True, apply_to_text=True,
            ),
            train=tc,
        )
        results[f"rank{rank}"] = run_single_experiment(config, data_dir)

    # 生成对比图
    generate_report(results, save_dir="./outputs/rq1_comparison")

    return results


def run_rq2_lora_position(data_dir: str = "./data", max_samples=None, epochs=None):
    """RQ2: LoRA 作用位置的影响"""
    print("\n" + "="*70)
    print("🔬 RQ2: LoRA 作用位置影响")
    print("="*70)

    results = {}
    epoch_val = epochs if epochs else 20
    positions = [
        ("vision_only", True, False),
        ("text_only", False, True),
        ("both", True, True),
    ]

    for name, vis, txt in positions:
        tc = TrainConfig(save_dir=f"./outputs/rq2_{name}", num_epochs=epoch_val,
                        max_samples=max_samples)
        config = ExperimentConfig(
            name=f"rq2_{name}",
            lora=LoRAConfig(
                rank=8, alpha=16.0,
                apply_to_vision=vis, apply_to_text=txt,
            ),
            train=tc,
        )
        results[name] = run_single_experiment(config, data_dir)

    generate_report(results, save_dir="./outputs/rq2_comparison")

    return results


def run_rq3_missing_modality(data_dir: str = "./data", max_samples=None, epochs=None):
    """RQ3: 缺失模态下的Gap稳定性"""
    print("\n" + "="*70)
    print("🔬 RQ3: 缺失模态对Gap的影响")
    print("="*70)

    results = {}
    epoch_val = epochs if epochs else 20
    base_lora = LoRAConfig(rank=8, alpha=16.0,
                          apply_to_vision=True, apply_to_text=True)

    # 不同缺失比例
    missing_configs = [
        ("complete", MissingModalitySimulator(image_drop_ratio=0.0, text_mask_ratio=0.0)),
        ("img_drop_10", MissingModalitySimulator(image_drop_ratio=0.1)),
        ("img_drop_30", MissingModalitySimulator(image_drop_ratio=0.3)),
        ("img_drop_50", MissingModalitySimulator(image_drop_ratio=0.5)),
        ("txt_mask_10", MissingModalitySimulator(text_mask_ratio=0.1)),
        ("txt_mask_30", MissingModalitySimulator(text_mask_ratio=0.3)),
        ("txt_mask_50", MissingModalitySimulator(text_mask_ratio=0.5)),
    ]

    for name, missing_sim in missing_configs:
        tc = TrainConfig(save_dir=f"./outputs/rq3_{name}", num_epochs=epoch_val,
                        max_samples=max_samples)
        config = ExperimentConfig(
            name=f"rq3_{name}",
            lora=base_lora,
            train=tc,
        )
        trainer = GapAwareTrainer(config)

        # 加载数据
        train_loader, val_loader, test_loader = create_dataloaders(
            dataset_name=config.train.dataset,
            data_dir=data_dir,
            batch_size=config.train.batch_size,
            max_samples=config.train.max_samples,
        )

        result = trainer.train(train_loader, val_loader, missing_sim=missing_sim)
        results[name] = result

    generate_report(results, save_dir="./outputs/rq3_comparison")

    return results


def run_baselines(data_dir: str = "./data", max_samples=None, epochs=None):
    """运行基线实验：冻结 vs 全量微调"""
    print("\n" + "="*70)
    print("🔬 基线实验")
    print("="*70)

    results = {}
    epoch_val = epochs if epochs else 5

    # 冻结
    tc = TrainConfig(save_dir="./outputs/baseline_frozen", num_epochs=epoch_val,
                    max_samples=max_samples)
    config = ExperimentConfig(
        name="baseline_frozen",
        lora=LoRAConfig(rank=0, apply_to_vision=False, apply_to_text=False),
        train=tc,
    )
    results["frozen"] = run_single_experiment(config, data_dir)

    # 全量微调
    tc2 = TrainConfig(save_dir="./outputs/baseline_full_ft", num_epochs=epoch_val,
                     max_samples=max_samples, gradient_accumulation_steps=4)
    config = ExperimentConfig(
        name="baseline_full_ft",
        lora=None,
        train=tc2,
    )
    results["full_ft"] = run_single_experiment(config, data_dir)

    generate_report(results, save_dir="./outputs/baselines")

    return results


def run_gap_init_baselines(data_dir: str = "./data", max_samples=None, epochs=None):
    """
    Gap-Init 实验 (参考: "When Is Rank-1 Enough?", arXiv:2602.01522)

    核心对比: rank-1/2/4/8 + Gap-Init vs 相同rank的标准LoRA
    验证命题: Gap-Init 能否让低rank达到高rank的性能？
    """
    print("\n" + "="*70)
    print("🔬 Gap-Init 实验 (arXiv:2602.01522)")
    print("="*70)

    results = {}
    epoch_val = epochs if epochs else 20

    # Gap-Init: rank=1, 2, 4, 8
    for rank in [1, 2, 4, 8]:
        name = f"gap_init_r{rank}"
        tc = TrainConfig(save_dir=f"./outputs/{name}", num_epochs=epoch_val,
                        max_samples=max_samples)
        config = ExperimentConfig(
            name=name,
            lora=LoRAConfig(
                rank=rank, alpha=rank * 2,
                apply_to_vision=True, apply_to_text=True,
                use_gap_init=True,
            ),
            train=tc,
        )
        results[name] = run_single_experiment(config, data_dir)

    # Null-LoRA 对比
    tc2 = TrainConfig(save_dir="./outputs/null_lora_r8", num_epochs=epoch_val,
                     max_samples=max_samples)
    config = ExperimentConfig(
        name="null_lora_r8",
        lora=LoRAConfig(
            rank=8, alpha=16.0,
            apply_to_vision=True, apply_to_text=True,
            use_null_lora=True,
        ),
        train=tc2,
    )
    results["null_lora_r8"] = run_single_experiment(config, data_dir)

    generate_report(results, save_dir="./outputs/gap_init")

    return results


def run_all_and_viz(data_dir: str = "./data", max_samples=None, epochs=None):
    """
    完整流水线: 所有实验 → 自动出图 → 论文可直接用
    "先出图再写论文" 的核心入口
    """
    print("\n" + "="*70)
    print("🎬 完整实验流水线: 先出图 → 再写论文")
    print("="*70)

    all_results = {}

    # Step 1: 基线
    print("\n📌 Phase 1/5: 基线实验")
    all_results["baselines"] = run_baselines(data_dir, max_samples, epochs)

    # Step 2: RQ1 — Rank 影响
    print("\n📌 Phase 2/5: RQ1 — LoRA Rank 对 Gap 演化的影响")
    all_results["rq1"] = run_rq1_rank_impact(data_dir, max_samples, epochs)

    # Step 3: RQ2 — 作用位置
    print("\n📌 Phase 3/5: RQ2 — LoRA 位置影响")
    all_results["rq2"] = run_rq2_lora_position(data_dir, max_samples, epochs)

    # Step 4: RQ3 — 缺失模态
    print("\n📌 Phase 4/5: RQ3 — 缺失模态下的 Gap 稳定性")
    all_results["rq3"] = run_rq3_missing_modality(data_dir, max_samples, epochs)

    # Step 5: Gap-Init
    print("\n📌 Phase 5/5: Gap-Init 基线")
    all_results["gap_init"] = run_gap_init_baselines(data_dir, max_samples, epochs)

    # ---- 自动生成所有图表 ----
    print("\n" + "="*70)
    print("📊 自动出图 — 生成论文图表")
    print("="*70)

    # 合并所有 gap history 用于对比图
    _merge_and_plot_all(all_results, save_dir="./outputs/figures")

    print("\n" + "="*70)
    print("🎉 流水线完成！")
    print(f"   实验数据: ./outputs/")
    print(f"   论文图表: ./outputs/figures/")
    print(f"   下一步: 看图写论文 → paper_outline.md")
    print("="*70)

    return all_results


def _merge_and_plot_all(all_results: dict, save_dir: str = "./outputs/figures"):
    """合并所有实验结果，生成综合对比图表"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    os.makedirs(save_dir, exist_ok=True)

    # 收集所有 gap history
    gap_histories = {}
    for group_name, group_results in all_results.items():
        if isinstance(group_results, dict):
            for exp_name, result in group_results.items():
                if isinstance(result, dict):
                    # 尝试从保存的文件中加载 gap_history
                    pass  # 各实验自行保存，这里通过文件加载
                # 简化处理：如果result中有gap数据就直接用
                if "initial_gap" in result and "final_gap" in result and result["initial_gap"] is not None and result["final_gap"] is not None:
                    gap_histories[f"{group_name}/{exp_name}"] = [
                        {"epoch": 0, **result["initial_gap"]},
                        {"epoch": result.get("epoch", 20), **result["final_gap"]},
                    ]

    # 从各实验目录加载详细gap历史（目录直接在outputs/下，非嵌套）
    for exp_dir in os.listdir("./outputs"):
        exp_path = os.path.join("./outputs", exp_dir)
        if not os.path.isdir(exp_path):
            continue
        gap_file = os.path.join(exp_path, "gap_history.json")
        if os.path.exists(gap_file):
            with open(gap_file) as f:
                import json
                raw = json.load(f)
                # 列式 → 行式转换
                if isinstance(raw, dict) and "epoch" in raw and isinstance(raw["epoch"], list):
                    epochs = raw["epoch"]
                    history = [{k: raw[k][i] for k in raw if isinstance(raw[k], list) and len(raw[k]) == len(epochs)} for i in range(len(epochs))]
                else:
                    history = raw
                gap_histories[exp_dir] = history

    if gap_histories:
        from src.visualize import plot_gap_evolution
        plot_gap_evolution(
            gap_histories,
            save_path=os.path.join(save_dir, "fig1_gap_evolution.png"),
        )

    # RQ1: rank对比图
    rq1_histories = {k: v for k, v in gap_histories.items() if "rq1" in k}
    if rq1_histories:
        from src.visualize import plot_gap_evolution
        plot_gap_evolution(
            rq1_histories,
            save_path=os.path.join(save_dir, "fig_rq1_rank_comparison.png"),
            figsize=(14, 10),
        )

    # Gap-Init 对比图: rank-1 + Gap-Init vs rank-8 Standard
    gap_init_histories = {k: v for k, v in gap_histories.items() if "gap_init" in k or "rq1_rank8" in k}
    if gap_init_histories:
        from src.visualize import plot_gap_evolution
        plot_gap_evolution(
            gap_init_histories,
            save_path=os.path.join(save_dir, "fig_gap_init_comparison.png"),
            figsize=(14, 10),
        )

    print(f"📊 共生成 {len(gap_histories)} 条Gap曲线的对比图")
    print(f"   保存于: {save_dir}/")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="LoRA微调CLIP的模态差距演化实验",
    )
    parser.add_argument(
        "--mode", type=str, default="single",
        choices=["single", "rq1", "rq2", "rq3", "baselines", "gap_init", "all"],
        help="实验模式 (all = 完整流水线: 实验+自动出图)",
    )
    parser.add_argument("--gap_init", action="store_true",
                       help="在single模式下使用Gap-Init初始化")
    parser.add_argument("--null_lora", action="store_true",
                       help="在single模式下使用Null-LoRA约束")
    parser.add_argument("--auto_viz", action="store_true",
                       help="实验结束后自动生成可视化图表")
    parser.add_argument("--peft_method", type=str, default="lora",
                       choices=["lora", "adapter", "prefix", "full_ft", "frozen"],
                       help="PEFT 方法")
    parser.add_argument("--rank", type=int, default=8, help="LoRA rank")
    parser.add_argument("--alpha", type=float, default=16.0, help="LoRA alpha")
    parser.add_argument("--bottleneck_dim", type=int, default=16,
                       help="Adapter bottleneck dim")
    parser.add_argument("--prefix_length", type=int, default=16,
                       help="Prefix Tuning prefix length")
    parser.add_argument("--data_dir", type=str, default="./data", help="数据目录")
    parser.add_argument("--dataset", type=str, default="flickr30k",
                       choices=["flickr30k", "coco"], help="数据集")
    parser.add_argument("--batch_size", type=int, default=64, help="Batch size")
    parser.add_argument("--epochs", type=int, default=20, help="训练epoch数")
    parser.add_argument("--max_samples", type=int, default=None, help="限制样本数")
    parser.add_argument("--device", type=str, default="auto",
                       choices=["auto", "cuda", "mps", "cpu"], help="设备")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")

    args = parser.parse_args()

    # 设备：自动检测 CUDA > MPS > CPU
    if args.device == "auto":
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
    else:
        device = args.device

    if device == "cuda":
        print(f"🖥️  使用设备: CUDA (GPU: {torch.cuda.get_device_name(0)})")
    elif device == "mps":
        print(f"🖥️  使用设备: Apple Silicon MPS")
    else:
        print(f"🖥️  使用设备: CPU")

    set_seed(args.seed)

    # 基础训练配置
    train_cfg = TrainConfig(
        device=device,
        dataset=args.dataset,
        batch_size=args.batch_size,
        num_epochs=args.epochs,
        max_samples=args.max_samples,
    )

    if args.mode == "single":
        # 单次实验 — 支持 LoRA / Adapter / Prefix
        from src.config import AdapterConfig, PrefixConfig

        if args.peft_method == "lora":
            name_suffix = f"lora_r{args.rank}"
            lora_extra = {}
            if args.gap_init:
                name_suffix += "_gapinit"
                lora_extra["use_gap_init"] = True
            if args.null_lora:
                name_suffix += "_null"
                lora_extra["use_null_lora"] = True

            config = ExperimentConfig(
                name=f"single_{name_suffix}",
                peft_method="lora",
                lora=LoRAConfig(rank=args.rank, alpha=args.alpha, **lora_extra),
                train=train_cfg,
            )
        elif args.peft_method == "adapter":
            config = ExperimentConfig(
                name=f"single_adapter_d{args.bottleneck_dim}",
                peft_method="adapter",
                adapter=AdapterConfig(bottleneck_dim=args.bottleneck_dim),
                train=train_cfg,
            )
        elif args.peft_method == "prefix":
            config = ExperimentConfig(
                name=f"single_prefix_l{args.prefix_length}",
                peft_method="prefix",
                prefix=PrefixConfig(prefix_length=args.prefix_length),
                train=train_cfg,
            )
        elif args.peft_method == "full_ft":
            config = ExperimentConfig(
                name="single_full_ft",
                peft_method="full_ft",
                train=train_cfg,
            )
        elif args.peft_method == "frozen":
            config = ExperimentConfig(
                name="single_frozen",
                peft_method="frozen",
                lora=LoRAConfig(rank=0),
                train=train_cfg,
            )
        else:
            raise ValueError(f"未知 PEFT 方法: {args.peft_method}")

        result = run_single_experiment(config, args.data_dir)

        if args.auto_viz and result:
            from src.visualize import plot_gap_evolution
            gap_hist = {}
            if result.get("gap_history"):
                gap_hist["single"] = result["gap_history"]
                plot_gap_evolution(
                    gap_hist,
                    save_path=os.path.join(train_cfg.save_dir, "fig_gap_evolution.png"),
                )

    elif args.mode == "rq1":
        run_rq1_rank_impact(args.data_dir, max_samples=args.max_samples, epochs=args.epochs)

    elif args.mode == "rq2":
        run_rq2_lora_position(args.data_dir, max_samples=args.max_samples, epochs=args.epochs)

    elif args.mode == "rq3":
        run_rq3_missing_modality(args.data_dir, max_samples=args.max_samples, epochs=args.epochs)

    elif args.mode == "baselines":
        run_baselines(args.data_dir, max_samples=args.max_samples, epochs=args.epochs)

    elif args.mode == "gap_init":
        run_gap_init_baselines(args.data_dir, max_samples=args.max_samples, epochs=args.epochs)

    elif args.mode == "all":
        run_all_and_viz(args.data_dir, max_samples=args.max_samples, epochs=args.epochs)


if __name__ == "__main__":
    main()
