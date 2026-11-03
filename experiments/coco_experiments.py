"""
COCO 交叉验证实验 — 直接调用项目模块，不依赖 CLI
===================================================
在 COCO 上复现 Flickr30k 的核心发现，验证跨数据集泛化。

实验配置（7个）：
  - RQ1: rank=4, 8, 16  (3个)
  - RQ2: text_only, both, vision_only (3个)
  - Baseline: full_ft (1个)

用法:
    python coco_experiments.py --data_dir ./data --max_samples 20000 --epochs 10
"""

import os, sys, json, time, argparse
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from src.config import ExperimentConfig, LoRAConfig, TrainConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders
from src.visualize import generate_report

# ============================================================
# 实验定义
# ============================================================

COCO_EXPERIMENTS = [
    # (name, LoRAConfig 或 None=full_ft)
    # RQ1+RQ2 + baselines — 8 experiments, 10 epochs
    ("rq1_rank4_coco",  LoRAConfig(rank=4,  alpha=8,   apply_to_vision=True,  apply_to_text=True)),
    ("rq1_rank8_coco",  LoRAConfig(rank=8,  alpha=16,  apply_to_vision=True,  apply_to_text=True)),
    ("rq1_rank16_coco", LoRAConfig(rank=16, alpha=32,  apply_to_vision=True,  apply_to_text=True)),
    ("rq2_text_only_coco", LoRAConfig(rank=8, alpha=16, apply_to_vision=False, apply_to_text=True)),
    ("rq2_both_coco",      LoRAConfig(rank=8, alpha=16, apply_to_vision=True,  apply_to_text=True)),
    ("rq2_vision_only_coco", LoRAConfig(rank=8, alpha=16, apply_to_vision=True, apply_to_text=False)),
    ("baseline_frozen_coco", LoRAConfig(rank=0, apply_to_vision=False, apply_to_text=False)),
    ("baseline_full_ft_coco", None),  # None = full fine-tune
]


def run_one(args, name, lora_cfg):
    """运行单个实验"""
    print(f"\n{'='*60}")
    print(f"🔬 COCO: {name}")
    print(f"{'='*60}")

    config = ExperimentConfig(
        name=name,
        lora=lora_cfg,
        train=TrainConfig(
            dataset="coco",
            device="cuda" if torch.cuda.is_available() else "cpu",
            batch_size=args.batch_size,
            num_epochs=args.epochs if lora_cfg is not None else min(args.epochs, 5),
            max_samples=args.max_samples,
            save_dir=f"{args.outputs_dir}/{name}",
            gradient_accumulation_steps=4 if lora_cfg is None else 1,
        ),
    )

    train_loader, val_loader, test_loader = create_dataloaders(
        dataset_name="coco",
        data_dir=args.data_dir,
        batch_size=config.train.batch_size,
        max_samples=config.train.max_samples,
    )

    trainer = GapAwareTrainer(config)
    result = trainer.train(train_loader, val_loader)

    test_metrics = trainer._compute_retrieval_metrics(test_loader)
    result["test_metrics"] = test_metrics

    # 保存
    save_path = f"{args.outputs_dir}/{name}/results.json"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default=".",
                       help="数据根目录（包含 coco/ 子目录）")
    parser.add_argument("--outputs_dir", type=str, default="./outputs")
    parser.add_argument("--batch_size", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--max_samples", type=int, default=20000)
    parser.add_argument("--skip_full_ft", action="store_true",
                       help="跳过全量微调（省时间）")
    args = parser.parse_args()

    # 检查 COCO
    coco_dir = f"{args.data_dir}/coco"
    if not os.path.exists(f"{coco_dir}/train2014"):
        print(f"❌ COCO 数据集未找到: {coco_dir}/train2014/")
        print("   请下载: http://images.cocodataset.org/zips/train2014.zip")
        print("   并解压到上面的路径")
        return

    total_start = time.time()
    results = {}

    for name, lora_cfg in COCO_EXPERIMENTS:
        if args.skip_full_ft and "full_ft" in name:
            print(f"⏭ 跳过 {name}")
            continue

        start = time.time()
        result = run_one(args, name, lora_cfg)
        results[name] = result
        elapsed = time.time() - start
        r1 = result.get("test_metrics", {}).get("R@1", "N/A")
        print(f"   ✅ {name}: R@1={r1}, time={elapsed:.0f}s")

    total = time.time() - total_start
    print(f"\n🎉 COCO实验完成！总耗时: {total/60:.0f} 分钟")

    # 生成报告
    from analyze_gaps import scan_experiments, extract_metrics
    all_data = scan_experiments(args.outputs_dir)
    rows = extract_metrics(all_data)

    # 保存 COCO 指标
    coco_rows = [r for r in rows if "_coco" in r.get("name", "")]
    if coco_rows:
        save_dir = f"{args.outputs_dir}/coco_analysis"
        os.makedirs(save_dir, exist_ok=True)
        with open(f"{save_dir}/coco_metrics.csv", 'w') as f:
            if coco_rows:
                headers = list(coco_rows[0].keys())
                f.write(",".join(headers) + "\n")
                for r in coco_rows:
                    f.write(",".join(str(r.get(h, "")) for h in headers) + "\n")
        print(f"📁 COCO 指标: {save_dir}/coco_metrics.csv")

    # 对比 Flickr30k vs COCO
    flickr_rows = [r for r in rows if "_coco" not in r.get("name", "")
                   and r.get("R@1") is not None]
    coco_rows = [r for r in rows if "_coco" in r.get("name", "")
                 and r.get("R@1") is not None]

    print("\n" + "=" * 60)
    print("📊 Flickr30k vs COCO 核心发现验证")
    print("=" * 60)

    checks = []

    # Check 1: rank越低gap缩小越多？
    for label, data in [("Flickr30k", flickr_rows), ("COCO", coco_rows)]:
        rank_data = [(r.get("lora_rank"), r["cg_delta"]) for r in data
                     if r.get("lora_rank") and r["lora_rank"] > 0]
        if len(rank_data) >= 3:
            rank_data.sort()
            low_rank_delta = rank_data[0][1]
            high_rank_delta = rank_data[-1][1]
            ok = low_rank_delta < high_rank_delta
            checks.append(f"  Rank越低Gap越小 [{label}]: {'✅' if ok else '❌'} "
                         f"(r={rank_data[0][0]}:{low_rank_delta:+.3f} vs "
                         f"r={rank_data[-1][0]}:{high_rank_delta:+.3f})")

    # Check 2: text_only 优于 both
    for label, data in [("Flickr30k", flickr_rows), ("COCO", coco_rows)]:
        to = [r for r in data if "text_only" in r.get("name", "")]
        both = [r for r in data if "_both" in r.get("name", "")]
        if to and both:
            ok = to[0]["cg_delta"] < both[0]["cg_delta"]
            checks.append(f"  text_only > both [{label}]: {'✅' if ok else '❌'} "
                         f"(text:{to[0]['cg_delta']:+.3f} vs both:{both[0]['cg_delta']:+.3f})")

    # Check 3: full_ft 破坏对齐
    for label, data in [("Flickr30k", flickr_rows), ("COCO", coco_rows)]:
        ft = [r for r in data if "full_ft" in r.get("name", "")]
        if ft:
            ok = ft[0]["cg_delta"] > 0
            checks.append(f"  full_ft扩大Gap [{label}]: {'✅' if ok else '❌'} "
                         f"(Δ={ft[0]['cg_delta']:+.3f})")

    for c in checks:
        print(c)

    # 保存验证报告
    with open(f"{args.outputs_dir}/cross_validation.json", 'w') as f:
        json.dump({
            "checks": checks,
            "all_passed": all("✅" in c for c in checks),
            "flickr30k_experiments": len(flickr_rows),
            "coco_experiments": len(coco_rows),
        }, f, indent=2, ensure_ascii=False)

    print(f"\n📁 交叉验证报告: {args.outputs_dir}/cross_validation.json")


if __name__ == "__main__":
    main()
