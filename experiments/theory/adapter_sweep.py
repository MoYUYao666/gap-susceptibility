"""
Phase 6 — Adapter Scaling Experiment
======================================
Sweep Adapter bottleneck d in {4, 8, 16, 32, 64} x {text_only, both} x 3 seeds.
Records DG*(t) every epoch for ODE fitting.
Measures Gamma_v, Gamma_t post-training.
Resumable.

Output: outputs/theory/adapter/

Usage:
    python experiments/theory/adapter_sweep.py
"""
import os, sys, json, time, warnings
from pathlib import Path
from collections import defaultdict

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch, torch.nn.functional as F
from scipy.optimize import curve_fit

from src.config import ExperimentConfig, AdapterConfig, TrainConfig, GapConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders
from src.gap_susceptibility import compute_gap_susceptibility

warnings.filterwarnings("ignore")

SEEDS = [42, 123, 456, 789, 999]
DATA_DIR = str(PROJECT_ROOT)
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "theory" / "adapter"
BATCH_SIZE, NUM_EPOCHS, MAX_SAMPLES = 128, 10, 10000

DIMS = [4, 8, 16, 32, 64]
POSITIONS = ["text_only", "both"]


def make_configs():
    cfgs = []
    for d in DIMS:
        for pos in POSITIONS:
            cfgs.append({
                "name": f"adapter_{pos}_d{d}",
                "peft_method": "adapter",
                "dim": d,
                "apply_to_vision": (pos == "both"),
                "apply_to_text": True,
            })
    return cfgs


def fit_exp(epochs, dg_star_vals):
    t = np.array(epochs, float)
    y = np.array(dg_star_vals, float)
    def mdl(t, A, B, b): return A + B * np.exp(-abs(b) * t)
    try:
        p, _ = curve_fit(mdl, t, y, p0=[y[-1], y[0]-y[-1], 0.15], maxfev=5000)
        A, B, b = p; b = abs(b)
        pred = mdl(t, A, B, b)
        r2 = 1 - np.sum((y-pred)**2) / max(np.sum((y-np.mean(y))**2), 1e-8)
        return float(A), float(B), float(b), float(r2)
    except:
        return None, None, None, None


def run_one(cfg_dict, seed):
    name = cfg_dict["name"]
    adapter_cfg = AdapterConfig(
        bottleneck_dim=cfg_dict["dim"],
        apply_to_vision=cfg_dict["apply_to_vision"],
        apply_to_text=cfg_dict["apply_to_text"],
    )
    train_cfg = TrainConfig(
        dataset="flickr30k", batch_size=BATCH_SIZE,
        num_epochs=NUM_EPOCHS, seed=seed,
        save_dir=str(OUTPUT_DIR / name / f"seed{seed}"),
    )
    exp_cfg = ExperimentConfig(
        name=name, peft_method="adapter", adapter=adapter_cfg,
        gap=GapConfig(compute_every_n_epochs=1), train=train_cfg,
    )

    trainer = GapAwareTrainer(exp_cfg)
    trainer.setup_model()
    trainer.enable_dg_star_tracking()
    train_loader, val_loader, _ = create_dataloaders(
        dataset_name="flickr30k", data_dir=DATA_DIR,
        batch_size=BATCH_SIZE, max_samples=MAX_SAMPLES,
    )
    trainer.train(train_loader, val_loader)

    epochs = trainer.dg_star_tracker.get_epochs()
    dg_star = trainer.dg_star_tracker.get_dg_star_array()
    A, B, beta, r2 = fit_exp(epochs, dg_star)
    alpha = -B * beta if B and beta else None

    gamma = None
    try:
        trainer.model.eval()
        for batch in val_loader:
            images = batch["image"].to(trainer.device)[:64]
            texts = batch["caption"][:64]
            ti = trainer.processor(text=texts, return_tensors="pt",
                                   padding=True, truncation=True, max_length=77)
            outputs = trainer.model(pixel_values=images,
                                    input_ids=ti["input_ids"].to(trainer.device),
                                    attention_mask=ti.get("attention_mask",
                                        torch.ones_like(ti["input_ids"])).to(trainer.device))
            ie = F.normalize(outputs.image_embeds, p=2, dim=-1)
            te = F.normalize(outputs.text_embeds, p=2, dim=-1)
            gamma = compute_gap_susceptibility(trainer.model, ie, te)
            break
    except Exception as e:
        print(f"    Gamma warning: {e}")

    return {"name": name, "seed": seed, "dim": cfg_dict["dim"],
            "position": cfg_dict["apply_to_vision"],
            "alpha": alpha, "beta": beta, "r_squared": r2,
            "dg_star_inf": A, "gamma": gamma}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    configs = make_configs()
    total_runs = len(configs) * len(SEEDS)
    all_results, run_idx = [], 0

    print("=" * 70)
    print(f"Phase 6 — Adapter Scaling  |  {len(DIMS)} dims x {len(POSITIONS)} pos x {len(SEEDS)} seeds = {total_runs} runs")
    print("=" * 70)

    for cfg in configs:
        name = cfg["name"]
        for seed in SEEDS:
            run_idx += 1
            rp = OUTPUT_DIR / name / f"seed{seed}" / "adapter_result.json"
            if rp.exists():
                print(f"\n[{run_idx}/{total_runs}] {name} seed={seed} -- SKIP")
                all_results.append(json.load(open(rp)))
                continue

            print(f"\n{'='*60}\n[{run_idx}/{total_runs}] {name}  seed={seed}\n{'='*60}")
            t0 = time.time()
            result = run_one(cfg, seed)
            elapsed = time.time() - t0

            save_dir = OUTPUT_DIR / name / f"seed{seed}"
            save_dir.mkdir(parents=True, exist_ok=True)
            with open(str(rp), "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            all_results.append(result)

            bf = f"{result.get('beta',0):.4f}" if result.get("beta") else "N/A"
            r2 = f"{result.get('r_squared',0):.4f}" if result.get("r_squared") else "N/A"
            print(f"   beta={bf}  R^2={r2}  elapsed={elapsed:.0f}s")

    # Summary
    print(f"\n{'='*70}\nADAPTER SUMMARY\n{'='*70}")
    groups = defaultdict(list)
    for r in all_results:
        groups[(r["dim"], r["position"])].append(r)

    print(f"{'Config':22s} {'alpha':>10s} {'beta':>10s} {'R^2':>8s} {'DG*_inf':>10s} {'Gamma_v':>10s} {'Gamma_t':>10s}")
    print("-" * 85)
    for pos in [False, True]:
        for d in DIMS:
            runs = groups.get((d, pos), [])
            if not runs: continue
            a = np.mean([r["alpha"] for r in runs if r.get("alpha") is not None])
            b = np.mean([r["beta"] for r in runs if r.get("beta")])
            r2 = np.mean([r["r_squared"] for r in runs if r.get("r_squared")])
            dg = np.mean([r["dg_star_inf"] for r in runs if r.get("dg_star_inf")])
            g = [r.get("gamma") or {} for r in runs]
            gv = np.mean([x.get("Gamma_v", 0) for x in g])
            gt = np.mean([x.get("Gamma_t", 0) for x in g])
            label = f"adapter_{'text' if pos is False else 'both'}_d{d}"
            print(f"{label:22s} {a:>10.4f} {b:>10.4f} {r2:>8.4f} {dg:>10.4f} {gv:>10.4f} {gt:>10.4f}")

    agg = OUTPUT_DIR / "adapter_all_results.json"
    with open(agg, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nSaved: {agg}")


if __name__ == "__main__":
    main()
