"""
Main entry — modality gap evolution experiments for LoRA fine-tuning of CLIP
============================================
"Figures first, then the paper" — all experiments run and 5 core figures are generated automatically

How to run:
    # single experiment
    python main.py --mode single --rank 8

    # RQ1: effect of LoRA rank
    python main.py --mode rq1

    # RQ2: LoRA injection position
    python main.py --mode rq2

    # RQ3: missing modality
    python main.py --mode rq3

    # Gap-Init baseline
    python main.py --mode gap_init

    # all experiments + automatic figures (the core pipeline)
    python main.py --mode all --auto_viz
"""

import os, sys
os.environ["HF_HUB_OFFLINE"] = "1"  # HF is blocked domestically, force offline mode
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
    """Fix the random seed"""
    torch.manual_seed(seed)
    torch.mps.manual_seed(seed)
    np.random.seed(seed)


def run_single_experiment(config: ExperimentConfig, data_dir: str = "./data"):
    """Run a single experiment"""
    print(f"\n{'='*70}")
    print(f"🔬 Experiment: {config.name}")
    print(f"   LoRA: r={config.lora.rank if config.lora else 'full'}, "
          f"α={config.lora.alpha if config.lora else 'N/A'}")
    print(f"   Vision={config.lora.apply_to_vision if config.lora else True}, "
          f"Text={config.lora.apply_to_text if config.lora else True}")
    print(f"{'='*70}")

    # Data loading
    train_loader, val_loader, test_loader = create_dataloaders(
        dataset_name=config.train.dataset,
        data_dir=data_dir,
        batch_size=config.train.batch_size,
        image_size=config.train.image_size,
        max_samples=config.train.max_samples,
    )

    # Training
    trainer = GapAwareTrainer(config)
    results = trainer.train(train_loader, val_loader)

    # Test-set evaluation
    print("\n📊 Test-set evaluation...")
    test_metrics = trainer._compute_retrieval_metrics(test_loader)
    results["test_metrics"] = test_metrics
    print(f"   R@1: {test_metrics.get('R@1', 0):.4f}")
    print(f"   R@5: {test_metrics.get('R@5', 0):.4f}")
    print(f"   R@10: {test_metrics.get('R@10', 0):.4f}")

    # Save results
    save_path = os.path.join(config.train.save_dir, config.name, "results.json")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results


def run_rq1_rank_impact(data_dir: str = "./data", max_samples=None, epochs=None):
    """RQ1: effect of LoRA rank on the Gap"""
    print("\n" + "="*70)
    print("🔬 RQ1: effect of LoRA rank on modality gap evolution")
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

    # Generate the comparison figure
    generate_report(results, save_dir="./outputs/rq1_comparison")

    return results


def run_rq2_lora_position(data_dir: str = "./data", max_samples=None, epochs=None):
    """RQ2: effect of LoRA injection position"""
    print("\n" + "="*70)
    print("🔬 RQ2: effect of LoRA injection position")
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
    """RQ3: Gap stability under missing modalities"""
    print("\n" + "="*70)
    print("🔬 RQ3: effect of missing modalities on the Gap")
    print("="*70)

    results = {}
    epoch_val = epochs if epochs else 20
    base_lora = LoRAConfig(rank=8, alpha=16.0,
                          apply_to_vision=True, apply_to_text=True)

    # Different missing ratios
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

        # Load data
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
    """Run baseline experiments: frozen vs full fine-tuning"""
    print("\n" + "="*70)
    print("🔬 Baseline experiments")
    print("="*70)

    results = {}
    epoch_val = epochs if epochs else 5

    # Frozen
    tc = TrainConfig(save_dir="./outputs/baseline_frozen", num_epochs=epoch_val,
                    max_samples=max_samples)
    config = ExperimentConfig(
        name="baseline_frozen",
        lora=LoRAConfig(rank=0, apply_to_vision=False, apply_to_text=False),
        train=tc,
    )
    results["frozen"] = run_single_experiment(config, data_dir)

    # Full fine-tuning
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
    Gap-Init experiment (ref: "When Is Rank-1 Enough?", arXiv:2602.01522)

    Core comparison: rank-1/2/4/8 + Gap-Init vs standard LoRA at the same rank
    Proposition tested: can Gap-Init let a low rank reach high-rank performance?
    """
    print("\n" + "="*70)
    print("🔬 Gap-Init experiment (arXiv:2602.01522)")
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

    # Null-LoRA comparison
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
    Full pipeline: all experiments → automatic figures → directly usable in the paper
    The core entry point for "figures first, then the paper"
    """
    print("\n" + "="*70)
    print("🎬 Full experiment pipeline: figures first → then the paper")
    print("="*70)

    all_results = {}

    # Step 1: baselines
    print("\n📌 Phase 1/5: baseline experiments")
    all_results["baselines"] = run_baselines(data_dir, max_samples, epochs)

    # Step 2: RQ1 — effect of rank
    print("\n📌 Phase 2/5: RQ1 — effect of LoRA rank on Gap evolution")
    all_results["rq1"] = run_rq1_rank_impact(data_dir, max_samples, epochs)

    # Step 3: RQ2 — injection position
    print("\n📌 Phase 3/5: RQ2 — effect of LoRA position")
    all_results["rq2"] = run_rq2_lora_position(data_dir, max_samples, epochs)

    # Step 4: RQ3 — missing modality
    print("\n📌 Phase 4/5: RQ3 — Gap stability under missing modalities")
    all_results["rq3"] = run_rq3_missing_modality(data_dir, max_samples, epochs)

    # Step 5: Gap-Init
    print("\n📌 Phase 5/5: Gap-Init baseline")
    all_results["gap_init"] = run_gap_init_baselines(data_dir, max_samples, epochs)

    # ---- Automatically generate all figures ----
    print("\n" + "="*70)
    print("📊 Automatic figures — generating paper figures")
    print("="*70)

    # Merge all gap histories for the comparison figure
    _merge_and_plot_all(all_results, save_dir="./outputs/figures")

    print("\n" + "="*70)
    print("🎉 Pipeline complete!")
    print(f"   Experiment data: ./outputs/")
    print(f"   Paper figures: ./outputs/figures/")
    print(f"   Next step: read the figures and write the paper → paper_outline.md")
    print("="*70)

    return all_results


def _merge_and_plot_all(all_results: dict, save_dir: str = "./outputs/figures"):
    """Merge all experiment results and generate comprehensive comparison figures"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    os.makedirs(save_dir, exist_ok=True)

    # Collect all gap histories
    gap_histories = {}
    for group_name, group_results in all_results.items():
        if isinstance(group_results, dict):
            for exp_name, result in group_results.items():
                if isinstance(result, dict):
                    # Try to load gap_history from the saved file
                    pass  # each experiment saves its own; here we load from files
                # Simplified handling: use gap data directly if result has it
                if "initial_gap" in result and "final_gap" in result and result["initial_gap"] is not None and result["final_gap"] is not None:
                    gap_histories[f"{group_name}/{exp_name}"] = [
                        {"epoch": 0, **result["initial_gap"]},
                        {"epoch": result.get("epoch", 20), **result["final_gap"]},
                    ]

    # Load detailed gap history from each experiment directory (directories sit directly under outputs/, not nested)
    for exp_dir in os.listdir("./outputs"):
        exp_path = os.path.join("./outputs", exp_dir)
        if not os.path.isdir(exp_path):
            continue
        gap_file = os.path.join(exp_path, "gap_history.json")
        if os.path.exists(gap_file):
            with open(gap_file) as f:
                import json
                raw = json.load(f)
                # Column-wise → row-wise conversion
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

    # RQ1: rank comparison figure
    rq1_histories = {k: v for k, v in gap_histories.items() if "rq1" in k}
    if rq1_histories:
        from src.visualize import plot_gap_evolution
        plot_gap_evolution(
            rq1_histories,
            save_path=os.path.join(save_dir, "fig_rq1_rank_comparison.png"),
            figsize=(14, 10),
        )

    # Gap-Init comparison figure: rank-1 + Gap-Init vs rank-8 Standard
    gap_init_histories = {k: v for k, v in gap_histories.items() if "gap_init" in k or "rq1_rank8" in k}
    if gap_init_histories:
        from src.visualize import plot_gap_evolution
        plot_gap_evolution(
            gap_init_histories,
            save_path=os.path.join(save_dir, "fig_gap_init_comparison.png"),
            figsize=(14, 10),
        )

    print(f"📊 Generated comparison figures for {len(gap_histories)} Gap curves")
    print(f"   Saved in: {save_dir}/")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Modality gap evolution experiments for LoRA fine-tuning of CLIP",
    )
    parser.add_argument(
        "--mode", type=str, default="single",
        choices=["single", "rq1", "rq2", "rq3", "baselines", "gap_init", "all"],
        help="experiment mode (all = full pipeline: experiments + automatic figures)",
    )
    parser.add_argument("--gap_init", action="store_true",
                       help="use Gap-Init initialization in single mode")
    parser.add_argument("--null_lora", action="store_true",
                       help="use the Null-LoRA constraint in single mode")
    parser.add_argument("--auto_viz", action="store_true",
                       help="automatically generate visualization figures after the experiments")
    parser.add_argument("--peft_method", type=str, default="lora",
                       choices=["lora", "adapter", "prefix", "full_ft", "frozen"],
                       help="PEFT method")
    parser.add_argument("--rank", type=int, default=8, help="LoRA rank")
    parser.add_argument("--alpha", type=float, default=16.0, help="LoRA alpha")
    parser.add_argument("--bottleneck_dim", type=int, default=16,
                       help="Adapter bottleneck dim")
    parser.add_argument("--prefix_length", type=int, default=16,
                       help="Prefix Tuning prefix length")
    parser.add_argument("--data_dir", type=str, default="./data", help="data directory")
    parser.add_argument("--dataset", type=str, default="flickr30k",
                       choices=["flickr30k", "coco"], help="dataset")
    parser.add_argument("--batch_size", type=int, default=64, help="Batch size")
    parser.add_argument("--epochs", type=int, default=20, help="number of training epochs")
    parser.add_argument("--max_samples", type=int, default=None, help="limit the number of samples")
    parser.add_argument("--device", type=str, default="auto",
                       choices=["auto", "cuda", "mps", "cpu"], help="device")
    parser.add_argument("--seed", type=int, default=42, help="random seed")

    args = parser.parse_args()

    # Device: auto-detect CUDA > MPS > CPU
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
        print(f"🖥️  Using device: CUDA (GPU: {torch.cuda.get_device_name(0)})")
    elif device == "mps":
        print(f"🖥️  Using device: Apple Silicon MPS")
    else:
        print(f"🖥️  Using device: CPU")

    set_seed(args.seed)

    # Base training configuration
    train_cfg = TrainConfig(
        device=device,
        dataset=args.dataset,
        batch_size=args.batch_size,
        num_epochs=args.epochs,
        max_samples=args.max_samples,
    )

    if args.mode == "single":
        # Single experiment — supports LoRA / Adapter / Prefix
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
            raise ValueError(f"unknown PEFT method: {args.peft_method}")

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
