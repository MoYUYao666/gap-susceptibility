"""Verification: is the pilot's full_ft β=0.643 a gradient accumulation artifact.

Same script, same training setup (batch=32 to fit 8GB), only gradient_accumulation_steps changed:
  accum=1 (effective batch 32)  vs  accum=4 (effective batch 128)
If β at accum=4 is markedly larger than at accum=1 (~0.6 vs ~0.16), then the pilot difference is conclusively driven by effective batch.

Usage (local conda activate pytorch):
    python experiments/theory/verify_accum.py
"""
import os, sys, json, time
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch
from scipy.optimize import curve_fit

from src.config import ExperimentConfig, LoRAConfig, TrainConfig, GapConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders

warnings_filter = True

BATCH_SIZE = 32      # fits 8GB VRAM (pilot/v1 used 128 on the cloud; local run only needs the relative difference)
NUM_EPOCHS = 10
MAX_SAMPLES = 10000
LEARNING_RATE = 1e-4
SEED = 42
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "theory" / "verify_accum"


def fit_exponential(epochs, dg_star_vals):
    epochs = np.array(epochs, dtype=float)
    dg_star_vals = np.array(dg_star_vals, dtype=float)
    if len(epochs) < 3:
        return None, None, None, None

    def model(t, A, B, beta):
        return A + B * np.exp(-beta * t)

    A0 = float(dg_star_vals[-1])
    B0 = float(dg_star_vals[0] - A0)
    try:
        popt, _ = curve_fit(model, epochs, dg_star_vals, p0=[A0, B0, 0.5], maxfev=5000)
        A, B, beta = popt
        predicted = model(epochs, A, B, beta)
        ss_res = np.sum((dg_star_vals - predicted) ** 2)
        ss_tot = np.sum((dg_star_vals - np.mean(dg_star_vals)) ** 2)
        r2 = 1.0 - ss_res / max(ss_tot, 1e-8)
        return float(A), float(B), float(abs(beta)), float(r2)
    except Exception as e:
        print("fit failed:", e)
        return None, None, None, None


def run_full_ft(accum, seed=SEED):
    name = f"full_ft_accum{accum}_bs{BATCH_SIZE}"
    train_cfg = TrainConfig(
        dataset="flickr30k", batch_size=BATCH_SIZE, num_epochs=NUM_EPOCHS,
        learning_rate=LEARNING_RATE, seed=seed,
        save_dir=str(OUTPUT_DIR / name / f"seed{seed}"),
        gradient_accumulation_steps=accum,
    )
    exp_cfg = ExperimentConfig(
        name=name, peft_method="full_ft", lora=LoRAConfig(),
        gap=GapConfig(compute_every_n_epochs=1), train=train_cfg,
    )
    train_loader, val_loader, _ = create_dataloaders(
        dataset_name="flickr30k", data_dir=str(PROJECT_ROOT),
        batch_size=BATCH_SIZE, max_samples=MAX_SAMPLES,
    )
    trainer = GapAwareTrainer(exp_cfg)
    trainer.setup_model()
    trainer.enable_dg_star_tracking()
    t0 = time.time()
    trainer.train(train_loader, val_loader)
    epochs = trainer.dg_star_tracker.get_epochs()
    dg_star = trainer.dg_star_tracker.get_dg_star_array()
    A, B, beta, r2 = fit_exponential(epochs, dg_star)
    alpha = -B * beta if (B is not None and beta is not None) else None
    print(f"[accum={accum}] beta={beta:.4f} alpha={alpha:.4f} R2={r2:.4f} "
          f"({time.time()-t0:.0f}s)  dg_star_tail={dg_star[-1]:.4f}")
    return {"accum": accum, "beta": beta, "alpha": alpha, "r2": r2,
            "epochs": list(epochs), "dg_star": list(dg_star)}


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 60)
    print("Verification: effect of gradient accumulation on full_ft β (batch=32, seed=42)")
    print("=" * 60)
    results = {}
    for acc in [1, 4]:
        results[f"accum{acc}"] = run_full_ft(acc)
    out_path = OUTPUT_DIR / "verify_accum_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {out_path}")
    print(f"Conclusion: accum=1 β={results['accum1']['beta']:.4f} vs "
          f"accum=4 β={results['accum4']['beta']:.4f}")
    if results['accum4']['beta'] and results['accum1']['beta']:
        ratio = results['accum4']['beta'] / results['accum1']['beta']
        print(f"Ratio: {ratio:.1f}x  (>2x → effective batch conclusively drives β; ~1x → accum is not the main cause)")
