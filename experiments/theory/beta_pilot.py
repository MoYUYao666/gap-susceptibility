"""
Phase 1 — Beta Pilot Experiment
================================
Measures beta (the alignment restoring force coefficient) on 3 pilot
configurations to verify it is approximately constant across PEFT
configurations.

If beta varies by >30% across configurations, the entire Gap
Susceptibility theoretical framework needs revision.

Output: outputs/theory/beta_pilot/beta_pilot_results.json

Usage:
    python experiments/theory/beta_pilot.py
"""

import os
import sys
import json
import time
import warnings
from pathlib import Path
from collections import defaultdict

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch
import torch.nn.functional as F
from scipy.optimize import curve_fit

from src.config import ExperimentConfig, LoRAConfig, TrainConfig, GapConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders
from src.gap_susceptibility import (
    compute_gap_susceptibility,
    compute_beta_theoretical,
    estimate_alpha_from_susceptibility,
)

warnings.filterwarnings("ignore")

# ============================================================
# Configuration
# ============================================================

SEEDS = [42, 123, 456]
DATA_DIR = str(PROJECT_ROOT)
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "theory" / "beta_pilot"
BATCH_SIZE = 128
NUM_EPOCHS = 10
MAX_SAMPLES = 10000  # limit for pilot (full dataset would be ~158K)
LEARNING_RATE = 1e-4

PILOT_CONFIGS = [
    {
        "name": "beta_pilot_text_r8",
        "peft_method": "lora",
        "rank": 8,
        "alpha": 16.0,
        "apply_to_vision": False,
        "apply_to_text": True,
    },
    {
        "name": "beta_pilot_both_r8",
        "peft_method": "lora",
        "rank": 8,
        "alpha": 16.0,
        "apply_to_vision": True,
        "apply_to_text": True,
    },
    {
        "name": "beta_pilot_full_ft",
        "peft_method": "full_ft",
    },
]


# ============================================================
# Exponential fitting
# ============================================================

def fit_exponential(epochs, dg_star_vals):
    """
    Fit DG*(t) = A + B * exp(-beta * t).

    Args:
        epochs: list of epoch numbers (should be >= 3 entries)
        dg_star_vals: list of DG* values

    Returns:
        (A, B, beta, r_squared) — all floats, or None tuples on failure.
        beta is guaranteed non-negative.
    """
    epochs = np.array(epochs, dtype=float)
    dg_star_vals = np.array(dg_star_vals, dtype=float)

    if len(epochs) < 3:
        print("  Warning: too few data points for exponential fit (need >=3)")
        return None, None, None, None

    def model(t, A, B, beta):
        return A + B * np.exp(-beta * t)

    A0 = float(dg_star_vals[-1])
    B0 = float(dg_star_vals[0] - A0)
    beta0 = 0.5

    try:
        popt, _ = curve_fit(
            model, epochs, dg_star_vals,
            p0=[A0, B0, beta0], maxfev=5000,
        )
        A, B, beta = popt
        predicted = model(epochs, A, B, beta)
        ss_res = np.sum((dg_star_vals - predicted) ** 2)
        ss_tot = np.sum((dg_star_vals - np.mean(dg_star_vals)) ** 2)
        r_squared = 1.0 - ss_res / max(ss_tot, 1e-8)
        return float(A), float(B), float(abs(beta)), float(r_squared)
    except Exception as e:
        print(f"  Warning: Exponential fit failed: {e}")
        return None, None, None, None


# ============================================================
# Seed helper
# ============================================================

def set_seed(seed):
    """Deterministic seeding across torch, numpy, and CUDA."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


# ============================================================
# Single config x seed runner
# ============================================================

def run_one_config(pilot_cfg, seed):
    """
    Train one (config, seed) pair for NUM_EPOCHS epochs, then compute:

      - DG*(t) trajectory (from trainer's internal tracker)
      - Fitted beta via exponential decay model
      - beta_theoretical via finite-difference of gradient-flow coupling
      - Gamma_v, Gamma_t via compute_gap_susceptibility on one val batch
      - alpha estimate from susceptibility
    """
    name = pilot_cfg["name"]
    peft_method = pilot_cfg["peft_method"]

    set_seed(seed)

    # ---- Build configs ----
    if peft_method == "lora":
        lora_cfg = LoRAConfig(
            rank=pilot_cfg["rank"],
            alpha=pilot_cfg["alpha"],
            apply_to_vision=pilot_cfg["apply_to_vision"],
            apply_to_text=pilot_cfg["apply_to_text"],
        )
    else:
        lora_cfg = None

    # full_ft at BS=128 on ViT-B/32 likely needs gradient accumulation
    grad_accum = 4 if peft_method == "full_ft" else 1

    train_cfg = TrainConfig(
        dataset="flickr30k",
        batch_size=BATCH_SIZE,
        num_epochs=NUM_EPOCHS,
        learning_rate=LEARNING_RATE,
        save_dir=str(OUTPUT_DIR / name / f"seed{seed}"),
        seed=seed,
        gradient_accumulation_steps=grad_accum,
    )

    # compute_every_n_epochs=1  ==>  DG* recorded at every epoch
    gap_cfg = GapConfig(compute_every_n_epochs=1)

    exp_cfg = ExperimentConfig(
        name=name,
        peft_method=peft_method,
        lora=lora_cfg if lora_cfg is not None else LoRAConfig(),
        gap=gap_cfg,
        train=train_cfg,
    )

    # ---- Data ----
    train_loader, val_loader, _ = create_dataloaders(
        dataset_name="flickr30k",
        data_dir=DATA_DIR,
        batch_size=BATCH_SIZE,
        max_samples=MAX_SAMPLES,
    )

    # ---- Train ----
    trainer = GapAwareTrainer(exp_cfg)
    trainer.setup_model()
    trainer.enable_dg_star_tracking()
    trainer.train(train_loader, val_loader)

    # ---- Extract DG* trajectory ----
    dg_star_vals = trainer.dg_star_tracker.get_dg_star_array()
    epochs_list = trainer.dg_star_tracker.get_epochs()

    print(f"\n  DG* trajectory ({len(dg_star_vals)} points): "
          f"{[f'{v:.4f}' for v in dg_star_vals]}")
    print(f"  Epochs recorded: {epochs_list}")

    # ---- Fit exponential:  DG*(t) = A + B * exp(-beta * t) ----
    A, B, beta_fitted, r_squared = fit_exponential(epochs_list, dg_star_vals)
    if beta_fitted is not None:
        print(f"  Exponential fit: A={A:.4f}, B={B:.4f}, "
              f"beta={beta_fitted:.4f}, R^2={r_squared:.4f}")
    else:
        print("  Exponential fit: FAILED")

    # ---- Compute Gamma_v, Gamma_t on one validation batch ----
    trainer.model.eval()
    gamma_results = None
    for batch in val_loader:
        images = batch["image"].to(trainer.device)[:64]
        texts = batch["caption"][:64]

        text_inputs = trainer.processor(
            text=texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=77,
        )
        input_ids = text_inputs["input_ids"].to(trainer.device)
        attention_mask = text_inputs["attention_mask"].to(trainer.device)

        outputs = trainer.model(
            pixel_values=images,
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        ie = F.normalize(outputs.image_embeds, p=2, dim=-1)
        te = F.normalize(outputs.text_embeds, p=2, dim=-1)
        gamma_results = compute_gap_susceptibility(trainer.model, ie, te)
        break  # single batch

    if gamma_results is not None:
        print(f"  Gamma_v={gamma_results['Gamma_v']:.6f}, "
              f"Gamma_t={gamma_results['Gamma_t']:.6f}, "
              f"cos_phi_v={gamma_results['cos_phi_v']:.4f}, "
              f"cos_phi_t={gamma_results['cos_phi_t']:.4f}")
    else:
        print("  Gamma: FAILED (no validation batches)")

    # ---- Compute beta_theoretical (finite-difference on f(DG*)) ----
    beta_theoretical = compute_beta_theoretical(
        trainer.model,
        val_loader,
        device=trainer.device,
        n_batches=5,
        learning_rate=LEARNING_RATE,
        eps_frac=0.01,
    )
    print(f"  beta_theoretical = {beta_theoretical:.6f}")

    # ---- Estimate alpha from susceptibility ----
    alpha_est = None
    if gamma_results is not None:
        alpha_est = estimate_alpha_from_susceptibility(
            gamma_v=gamma_results["Gamma_v"],
            gamma_t=gamma_results["Gamma_t"],
            norm_g_v=gamma_results["norm_g_v"],
            norm_g_t=gamma_results["norm_g_t"],
            learning_rate=LEARNING_RATE,
        )
        print(f"  alpha_estimated = {alpha_est:.6f}")

    # ---- Package results ----
    run_result = {
        "config": pilot_cfg,
        "seed": seed,
        "learning_rate": LEARNING_RATE,
        "dg_star_trajectory": {
            "epochs": epochs_list,
            "dg_star": dg_star_vals,
            "dg_empirical": trainer.dg_star_tracker.get_dg_empirical_array(),
            "cg": trainer.dg_star_tracker.get_cg_array(),
        },
        "exponential_fit": {
            "A": A,
            "B": B,
            "beta_fitted": beta_fitted,
            "r_squared": r_squared,
        },
        "beta_theoretical": beta_theoretical,
        "gamma": gamma_results,
        "alpha_estimated": alpha_est,
        "train_losses": trainer.train_losses,
        "val_losses": trainer.val_losses,
    }

    return run_result


# ============================================================
# Main
# ============================================================

def main():
    total_start = time.time()
    all_results = []

    total_runs = len(PILOT_CONFIGS) * len(SEEDS)
    run_idx = 0

    print("=" * 70)
    print("Phase 1 — Beta Pilot")
    print("Measuring beta across 3 PEFT configurations")
    print(f"Seeds:    {SEEDS}")
    print(f"Configs:  {[c['name'] for c in PILOT_CONFIGS]}")
    print(f"Output:   {OUTPUT_DIR}")
    print(f"Epochs:   {NUM_EPOCHS}")
    print(f"BS:       {BATCH_SIZE}")
    print("=" * 70)

    for pilot_cfg in PILOT_CONFIGS:
        name = pilot_cfg["name"]

        for seed in SEEDS:
            run_idx += 1

            # Skip completed runs
            result_path = (
                OUTPUT_DIR / name / f"seed{seed}" / "beta_results.json"
            )
            if result_path.exists():
                print(
                    f"\n[{run_idx}/{total_runs}] {name} seed={seed}"
                    f" -- already done, loading cached result"
                )
                with open(result_path, "r") as f:
                    run_result = json.load(f)
                all_results.append(run_result)
                continue

            print(f"\n{'='*60}")
            print(f"[{run_idx}/{total_runs}] {name}  seed={seed}")
            print(f"{'='*60}")

            start = time.time()
            run_result = run_one_config(pilot_cfg, seed)
            elapsed = time.time() - start

            # Save per-run results
            save_dir = OUTPUT_DIR / name / f"seed{seed}"
            os.makedirs(str(save_dir), exist_ok=True)
            with open(str(result_path), "w") as f:
                json.dump(run_result, f, indent=2, ensure_ascii=False)

            all_results.append(run_result)

            bf = run_result["exponential_fit"]["beta_fitted"]
            bt = run_result["beta_theoretical"]
            r2 = run_result["exponential_fit"]["r_squared"]

            bf_str = f"{bf:.4f}" if bf is not None else "N/A"
            bt_str = f"{bt:.6f}" if bt is not None else "N/A"
            r2_str = f"{r2:.4f}" if r2 is not None else "N/A"

            print(f"   beta_fitted     = {bf_str}")
            print(f"   beta_theoretical = {bt_str}")
            print(f"   R^2              = {r2_str}")
            print(f"   elapsed          = {elapsed:.0f} s")

    total = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"Phase 1 complete!  Total wall time: {total/60:.0f} min")
    print(f"{'='*60}")

    # ================================================================
    # Cross-config beta summary
    # ================================================================

    print("\n" + "=" * 70)
    print("BETA CONSTANCY CHECK -- Cross-Config Summary")
    print("=" * 70)
    header = (
        f"{'Config':30s} {'Seed':>5s} {'beta_fitted':>12s} "
        f"{'beta_theory':>16s} {'R^2':>8s}"
    )
    print(header)
    print("-" * 70)

    beta_fitted_all = []
    beta_theory_all = []
    by_config = defaultdict(
        lambda: {"beta_fitted": [], "beta_theoretical": [], "r2": []}
    )

    for r in all_results:
        cfg_name = r["config"]["name"]
        seed = r["seed"]
        bf_val = r["exponential_fit"]["beta_fitted"]
        bt_val = r["beta_theoretical"]
        r2_val = r["exponential_fit"]["r_squared"]

        bf_str = f"{bf_val:.4f}" if bf_val is not None else "N/A"
        bt_str = f"{bt_val:.6f}" if bt_val is not None else "N/A"
        r2_str = f"{r2_val:.4f}" if r2_val is not None else "N/A"

        print(f"{cfg_name:30s} {seed:>5d} {bf_str:>12s} {bt_str:>16s} {r2_str:>8s}")

        if bf_val is not None:
            beta_fitted_all.append(bf_val)
            by_config[cfg_name]["beta_fitted"].append(bf_val)
        if bt_val is not None:
            beta_theory_all.append(bt_val)
            by_config[cfg_name]["beta_theoretical"].append(bt_val)
        if r2_val is not None:
            by_config[cfg_name]["r2"].append(r2_val)

    print("-" * 70)

    # Per-config stats
    print(f"\n{'Config':30s} {'beta_fitted mean +/- std':>28s} {'CV':>8s}")
    print("-" * 70)
    config_means = []
    for cfg_name in [c["name"] for c in PILOT_CONFIGS]:
        vals = by_config[cfg_name]["beta_fitted"]
        if len(vals) >= 2:
            mean_v = np.mean(vals)
            std_v = np.std(vals)
            cv = std_v / max(mean_v, 1e-8) * 100
            print(f"{cfg_name:30s} {mean_v:.4f} +/- {std_v:.4f}         {cv:5.1f}%")
            config_means.append(mean_v)
        elif len(vals) == 1:
            print(f"{cfg_name:30s} {vals[0]:.4f} (single run)          N/A")
            config_means.append(vals[0])
        else:
            print(f"{cfg_name:30s} N/A")

    # Cross-config variation
    if len(config_means) >= 2:
        overall_mean = np.mean(config_means)
        max_dev = max(abs(m - overall_mean) for m in config_means)
        cv_cross = max_dev / max(overall_mean, 1e-8) * 100

        print(f"\n  Cross-config beta mean:  {overall_mean:.4f}")
        print(f"  Max deviation:           {max_dev:.4f}  ({cv_cross:.1f}%)")

        if cv_cross > 30:
            print(
                f"\n  *** WARNING: Cross-config beta variation "
                f"({cv_cross:.1f}%) exceeds 30% threshold! ***"
            )
            print(
                "  The Gap Susceptibility theoretical framework "
                "needs revision."
            )
        else:
            print(
                f"\n  *** PASS: Cross-config beta variation "
                f"({cv_cross:.1f}%) is within 30% threshold. ***"
            )
            print(
                "  beta is approximately constant across "
                "PEFT configurations."
            )
    elif len(config_means) == 1:
        print("\n  Only one config has valid beta -- cannot assess constancy.")
    else:
        print("\n  No valid beta values -- check training logs.")

    # ================================================================
    # Save full results
    # ================================================================

    os.makedirs(str(OUTPUT_DIR), exist_ok=True)

    beta_summary = {}
    for cfg_name, v in by_config.items():
        bf_vals = v["beta_fitted"]
        bt_vals = v["beta_theoretical"]
        beta_summary[cfg_name] = {
            "beta_fitted_mean": float(np.mean(bf_vals)) if bf_vals else None,
            "beta_fitted_std": float(np.std(bf_vals)) if len(bf_vals) >= 2 else 0.0,
            "beta_theoretical_mean": float(np.mean(bt_vals)) if bt_vals else None,
            "beta_theoretical_std": float(np.std(bt_vals)) if len(bt_vals) >= 2 else 0.0,
            "n_runs": len(bf_vals),
        }

    summary = {
        "phase": "Phase 1 — Beta Pilot",
        "description": (
            "Measures beta across 3 PEFT configurations to verify "
            "constancy. If CV > 30%, the theory framework needs revision."
        ),
        "pilot_configs": PILOT_CONFIGS,
        "seeds": SEEDS,
        "num_epochs": NUM_EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "beta_summary": beta_summary,
        "all_results": all_results,
    }

    summary_path = OUTPUT_DIR / "beta_pilot_results.json"
    with open(str(summary_path), "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nFull results saved: {summary_path}")

    return all_results, summary


if __name__ == "__main__":
    main()
