"""
MSCOCO cross-dataset validation — 3 key configs, 3 seeds each = 9 runs.
Proves ODE framework is not Flickr30k-specific.
Resumable.

Usage: python experiments/theory/coco_validation.py
"""
import os, sys, json, time, warnings
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch, torch.nn.functional as F
from scipy.optimize import curve_fit

from src.config import ExperimentConfig, LoRAConfig, TrainConfig, GapConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders
from src.gap_susceptibility import compute_gap_susceptibility

warnings.filterwarnings("ignore")

SEEDS = [42, 123, 456]
BATCH, EPOCHS, MAX_SAMPLES = 128, 10, 10000
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "theory" / "coco"

CONFIGS = [
    {"name": "coco_text_r8", "rank": 8, "alpha": 16, "vis": False},
    {"name": "coco_both_r8", "rank": 8, "alpha": 16, "vis": True},
    {"name": "coco_full_ft",  "rank": 0, "alpha": 0,  "vis": True, "full": True},
]

def fit_exp(epochs, dg_vals):
    t, y = np.array(epochs, float), np.array(dg_vals, float)
    def m(t, A, B, b): return A + B * np.exp(-abs(b)*t)
    try:
        p, _ = curve_fit(m, t, y, p0=[y[-1], y[0]-y[-1], 0.15], maxfev=5000)
        A, B, b = p; b = abs(b)
        pred = m(t, A, B, b)
        r2 = 1 - np.sum((y-pred)**2)/max(np.sum((y-np.mean(y))**2), 1e-8)
        return float(A), float(B), float(b), float(r2)
    except: return None, None, None, None

def run_one(cfg, seed):
    peft = "full_ft" if cfg.get("full") else "lora"
    lora = None if cfg.get("full") else LoRAConfig(
        rank=cfg["rank"], alpha=cfg["alpha"],
        apply_to_vision=cfg["vis"], apply_to_text=True)

    train = TrainConfig(dataset="coco", batch_size=BATCH, num_epochs=EPOCHS,
                        seed=seed, save_dir=str(OUTPUT_DIR / cfg["name"] / f"seed{seed}"))
    exp = ExperimentConfig(name=cfg["name"], peft_method=peft, lora=lora,
                           gap=GapConfig(compute_every_n_epochs=1), train=train)

    trainer = GapAwareTrainer(exp)
    trainer.setup_model()
    trainer.enable_dg_star_tracking()
    train_loader, val_loader, _ = create_dataloaders(
        dataset_name="coco", data_dir=str(PROJECT_ROOT),
        batch_size=BATCH, max_samples=MAX_SAMPLES, pre_tokenize=False,
    )
    trainer.train(train_loader, val_loader)

    epochs = trainer.dg_star_tracker.get_epochs()
    dg_star = trainer.dg_star_tracker.get_dg_star_array()
    A, B, beta, r2 = fit_exp(epochs, dg_star)
    alpha = -B * beta if B and beta else None

    return {"name": cfg["name"], "seed": seed, "alpha": alpha, "beta": beta,
            "r_squared": r2, "dg_star_inf": A}

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total = len(CONFIGS) * len(SEEDS)
    all_results, idx = [], 0

    print(f"MSCOCO validation: {total} runs")
    for cfg in CONFIGS:
        for seed in SEEDS:
            idx += 1
            rp = OUTPUT_DIR / cfg["name"] / f"seed{seed}" / "coco_result.json"
            if rp.exists():
                print(f"[{idx}/{total}] {cfg['name']} s{seed} SKIP")
                all_results.append(json.load(open(rp)))
                continue

            print(f"[{idx}/{total}] {cfg['name']} s{seed}")
            result = run_one(cfg, seed)
            rp.parent.mkdir(parents=True, exist_ok=True)
            with open(str(rp), "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            all_results.append(result)

            b = f"{result.get('beta',0):.4f}" if result.get("beta") else "N/A"
            r2 = f"{result.get('r_squared',0):.4f}" if result.get("r_squared") else "N/A"
            print(f"  beta={b}  R^2={r2}")

    # Summary
    print(f"\n{'='*60}\nMSCOCO vs Flickr30k\n{'='*60}")
    flickr_beta = {"coco_text_r8": 0.14, "coco_both_r8": 0.14, "coco_full_ft": 0.64}
    for cfg in CONFIGS:
        runs = [r for r in all_results if r["name"] == cfg["name"]]
        a = np.mean([r["alpha"] for r in runs if r.get("alpha") is not None])
        b = np.mean([r["beta"] for r in runs if r.get("beta")])
        r2 = np.mean([r["r_squared"] for r in runs if r.get("r_squared")])
        fb = flickr_beta.get(cfg["name"], 0)
        print(f"  {cfg['name']}: a={a:.4f}  b_COCO={b:.4f}  b_Flickr={fb:.4f}  R^2={r2:.4f}")

    print(f"\nSaved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
