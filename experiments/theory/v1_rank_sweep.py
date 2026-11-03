"""
Phase 2 — V1 DG* Trajectory + V2 Gap Susceptibility
=====================================================
Rank sweep r in {1,2,4,8,16,32,64} x {text_only, both} x 3 seeds.
Records DG*(t) every epoch for ODE fitting (V1).
Measures Gamma_v, Gamma_t at epoch 1 (V2).
Resumable: skips runs with existing results.json and dg_star_history.json.

Output: outputs/theory/v1_trajectory/

Usage:
    python experiments/theory/v1_rank_sweep.py
"""

import os, sys, json, time, warnings
from pathlib import Path
from collections import defaultdict

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
from src.gap_susceptibility import compute_gap_susceptibility

warnings.filterwarnings("ignore")

# ============================================================
# Configuration
# ============================================================
SEEDS = [42, 123, 456, 789, 999]
DATA_DIR = str(PROJECT_ROOT)
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "theory" / "v1_trajectory"
BATCH_SIZE = 128
NUM_EPOCHS = 10
MAX_SAMPLES = 10000
LEARNING_RATE = 1e-4

RANKS = [1, 2, 4, 8, 16, 32, 64]
POSITIONS = ["text_only", "both"]


def make_configs():
    """Generate all (rank, position) combinations + baselines."""
    configs = []
    for rank in RANKS:
        for pos in POSITIONS:
            configs.append({
                "name": f"v1_{pos}_r{rank}",
                "peft_method": "lora",
                "rank": rank,
                "alpha": rank * 2,
                "apply_to_vision": (pos == "both"),
                "apply_to_text": True,
            })
    # Baselines
    configs.append({"name": "v1_frozen", "peft_method": "frozen"})
    configs.append({"name": "v1_full_ft", "peft_method": "full_ft"})
    # Extra seed for r=16 verification (seed noise check)
    configs.append({"name": "v1_text_only_r16", "peft_method": "lora",
                    "rank": 16, "alpha": 32,
                    "apply_to_vision": False, "apply_to_text": True,
                    "_extra_seed": True})
    return configs


# ============================================================
# Exponential fitting
# ============================================================
def fit_exponential(epochs, dg_star_vals):
    """Fit DG*(t) = A + B*exp(-beta*t). Returns (A, B, beta, r_squared)."""
    epochs = np.array(epochs, dtype=float)
    dg_star_vals = np.array(dg_star_vals, dtype=float)

    def model(t, A, B, beta):
        return A + B * np.exp(-abs(beta) * t)

    A0 = dg_star_vals[-1]
    B0 = dg_star_vals[0] - A0
    beta0 = 0.15

    try:
        popt, _ = curve_fit(model, epochs, dg_star_vals,
                            p0=[A0, B0, beta0], maxfev=5000)
        A, B, beta = popt
        beta = abs(beta)
        predicted = model(epochs, A, B, beta)
        ss_res = np.sum((dg_star_vals - predicted) ** 2)
        ss_tot = np.sum((dg_star_vals - np.mean(dg_star_vals)) ** 2)
        r2 = 1 - ss_res / max(ss_tot, 1e-8)
        return float(A), float(B), float(beta), float(r2)
    except Exception as e:
        print(f"    Warning: fit failed: {e}")
        return None, None, None, None


# ============================================================
# Single run
# ============================================================
def run_one(cfg_dict, seed):
    name = cfg_dict["name"]
    peft_method = cfg_dict["peft_method"]

    lora_cfg = None
    if peft_method == "lora":
        lora_cfg = LoRAConfig(
            rank=cfg_dict["rank"], alpha=cfg_dict["alpha"],
            apply_to_vision=cfg_dict["apply_to_vision"],
            apply_to_text=cfg_dict["apply_to_text"],
        )

    train_cfg = TrainConfig(
        dataset="flickr30k", batch_size=BATCH_SIZE,
        num_epochs=NUM_EPOCHS, seed=seed,
        save_dir=str(OUTPUT_DIR / name / f"seed{seed}"),
    )

    exp_cfg = ExperimentConfig(
        name=name, peft_method=peft_method, lora=lora_cfg,
        gap=GapConfig(compute_every_n_epochs=1),
        train=train_cfg,
    )

    trainer = GapAwareTrainer(exp_cfg)
    trainer.setup_model()
    trainer.enable_dg_star_tracking()

    train_loader, val_loader, _ = create_dataloaders(
        dataset_name="flickr30k", data_dir=DATA_DIR,
        batch_size=BATCH_SIZE, max_samples=MAX_SAMPLES,
    )

    results = trainer.train(train_loader, val_loader)

    # ---- V1: Exponential fit from DG* trajectory ----
    epochs = trainer.dg_star_tracker.get_epochs()
    dg_star = trainer.dg_star_tracker.get_dg_star_array()
    if len(dg_star) == 0:
        # Frozen or no training: use gap_tracker's initial measurement as constant
        if trainer.gap_tracker.history:
            dg_val = trainer.gap_tracker.history[0].distribution_gap
            A, B, beta, r2 = dg_val, 0.0, 0.0, 1.0
        else:
            A, B, beta, r2 = None, None, None, None
    else:
        A, B, beta, r2 = fit_exponential(epochs, dg_star)
    alpha = -B * beta if (B is not None and beta is not None) else None
    dg_inf = A
    dg_0 = A + B if (A is not None and B is not None) else None

    # ---- V2: Gamma measurement at epoch 1 (or after training) ----
    gamma_result = None
    try:
        trainer.model.eval()
        for batch in val_loader:
            images = batch["image"].to(trainer.device)[:64]
            texts = batch["caption"][:64]
            ti = trainer.processor(text=texts, return_tensors="pt",
                                   padding=True, truncation=True, max_length=77)
            outputs = trainer.model(
                pixel_values=images,
                input_ids=ti["input_ids"].to(trainer.device),
                attention_mask=ti.get("attention_mask", torch.ones_like(ti["input_ids"])).to(trainer.device),
            )
            ie = F.normalize(outputs.image_embeds, p=2, dim=-1)
            te = F.normalize(outputs.text_embeds, p=2, dim=-1)
            gamma_result = compute_gap_susceptibility(trainer.model, ie, te)
            break
    except Exception as e:
        print(f"    Warning: Gamma measurement failed: {e}")

    return {
        "name": name, "seed": seed,
        "rank": cfg_dict.get("rank"), "position": cfg_dict.get("apply_to_vision"),
        "peft_method": peft_method,
        "alpha": alpha, "beta": beta, "r_squared": r2,
        "dg_star_0": dg_0, "dg_star_inf": dg_inf,
        "dg_star_trajectory": dg_star,
        "epochs": epochs,
        "gamma": gamma_result,
        "final_r1": ((results or {}).get("final_task_metrics") or {}).get("R@1"),
    }


# ============================================================
# Main
# ============================================================
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    configs = make_configs()
    # Count: regular configs x 3 seeds + extra seed config x 1 seed
    total_runs = sum(1 if c.get("_extra_seed") else len(SEEDS) for c in configs)
    all_results = []
    run_idx = 0

    print("=" * 70)
    print("Phase 2 — V1 DG* Trajectory + V2 Gap Susceptibility")
    print(f"Ranks:    {RANKS}")
    print(f"Positions: {POSITIONS}")
    print(f"Seeds:    {SEEDS}")
    print(f"Total:    {total_runs} runs")
    print(f"Output:   {OUTPUT_DIR}")
    print("=" * 70)

    total_start = time.time()

    for cfg in configs:
        name = cfg["name"]
        seeds_to_run = [789] if cfg.get("_extra_seed") else SEEDS
        for seed in seeds_to_run:
            run_idx += 1

            # Check if already done
            result_path = OUTPUT_DIR / name / f"seed{seed}" / "v1_result.json"
            if result_path.exists():
                print(f"\n[{run_idx}/{total_runs}] {name} seed={seed} -- SKIP (cached)")
                with open(result_path) as f:
                    all_results.append(json.load(f))
                continue

            print(f"\n{'='*60}")
            print(f"[{run_idx}/{total_runs}] {name}  seed={seed}")
            print(f"{'='*60}")

            t0 = time.time()
            result = run_one(cfg, seed)
            elapsed = time.time() - t0

            # Save
            save_dir = OUTPUT_DIR / name / f"seed{seed}"
            save_dir.mkdir(parents=True, exist_ok=True)
            with open(str(result_path), "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)

            all_results.append(result)

            bf = result.get("beta")
            r2 = result.get("r_squared")
            g = result.get("gamma") or {}
            bf_s = f"{bf:.4f}" if bf else "N/A"
            r2_s = f"{r2:.4f}" if r2 else "N/A"
            gv_s = f"{g.get('Gamma_v',0):.4f}" if g else "N/A"
            gt_s = f"{g.get('Gamma_t',0):.4f}" if g else "N/A"

            print(f"   beta={bf_s}  R^2={r2_s}  "
                  f"Gamma_v={gv_s}  Gamma_t={gt_s}  "
                  f"elapsed={elapsed:.0f}s")

    total_elapsed = time.time() - total_start
    print(f"\n{'='*70}")
    print(f"Phase 2 complete!  Total wall time: {total_elapsed/60:.0f} min")
    print(f"{'='*70}")

    # ---- Summary ----
    print("\n" + "=" * 70)
    print("V1 SUMMARY — ODE Fit by Rank and Position")
    print("=" * 70)
    print(f"{'Config':25s} {'alpha':>10s} {'beta':>10s} {'R^2':>8s} {'DG*_inf':>10s}")
    print("-" * 65)
    for r in all_results:
        name = r.get("name", "?")
        a = f"{r.get('alpha',0):.4f}" if r.get("alpha") else "N/A"
        b = f"{r.get('beta',0):.4f}" if r.get("beta") else "N/A"
        r2 = f"{r.get('r_squared',0):.4f}" if r.get("r_squared") else "N/A"
        di = f"{r.get('dg_star_inf',0):.4f}" if r.get("dg_star_inf") else "N/A"
        print(f"{name:25s} {a:>10s} {b:>10s} {r2:>8s} {di:>10s}")

    # ---- V2 Summary: Gamma_v/Gamma_t by rank ----
    print("\n" + "=" * 70)
    print("V2 SUMMARY — Gap Susceptibility by Rank and Position")
    print("=" * 70)
    print(f"{'Config':25s} {'Gamma_v':>10s} {'Gamma_t':>10s} {'G_v/G_t':>8s} "
          f"{'|g_v|':>10s} {'|g_t|':>10s} {'R@1':>8s}")
    print("-" * 85)
    for r in all_results:
        name = r.get("name", "?")
        g = r.get("gamma") or {}
        gv = f"{g.get('Gamma_v',0):.4f}" if g else "N/A"
        gt = f"{g.get('Gamma_t',0):.4f}" if g else "N/A"
        ratio = g.get("Gamma_v", 0) / max(g.get("Gamma_t", 0), 1e-8)
        ratio_s = f"{ratio:.3f}" if g else "N/A"
        ngv = f"{g.get('norm_g_v',0):.2f}" if g else "N/A"
        ngt = f"{g.get('norm_g_t',0):.2f}" if g else "N/A"
        r1 = f"{r.get('final_r1',0):.3f}" if r.get("final_r1") else "N/A"
        print(f"{name:25s} {gv:>10s} {gt:>10s} {ratio_s:>8s} "
              f"{ngv:>10s} {ngt:>10s} {r1:>8s}")

    # Save aggregate
    agg_path = OUTPUT_DIR / "v1_all_results.json"
    with open(agg_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nFull results: {agg_path}")

    # ================================================================
    # V3+V4+V5 Analysis (runs automatically after experiments complete)
    # ================================================================
    run_analysis(all_results)


# ============================================================
# V3+V4+V5 Analysis
# ============================================================
def run_analysis(all_results):
    valid = [r for r in all_results
             if r.get("beta") is not None and r.get("r_squared", 0) > 0.5]

    groups = defaultdict(list)
    for r in valid:
        key = (r.get("rank"), r.get("position"))
        groups[key].append(r)

    # ---- V3: ||g_v|| scaling ----
    print("\n" + "=" * 70)
    print("V3 — ||g_v|| SCALING EXPONENT")
    print("=" * 70)

    both_pts, text_pts = [], []
    for (rank, pos), runs in sorted(groups.items(), key=lambda x: (x[0][0] or 0, x[0][1] or False)):
        if pos is None or rank is None: continue
        gvs = [r["gamma"]["norm_g_v"] for r in runs
               if r.get("gamma") and r["gamma"].get("norm_g_v", 0) > 0]
        if not gvs: continue
        if pos is True: both_pts.append((rank, np.mean(gvs)))
        elif pos is False: text_pts.append((rank, np.mean(gvs)))

    if len(both_pts) >= 3:
        rb = np.log([p[0] for p in both_pts])
        gb = np.log([p[1] for p in both_pts])
        k, _ = np.polyfit(rb, gb, 1)
        pred = k * rb + _
        r2 = 1 - np.sum((gb - pred)**2) / max(np.sum((gb - np.mean(gb))**2), 1e-8)
        print(f"Both:    ||g_v|| propto r^{k:.3f}  (R^2={r2:.3f}, theory ~0.5)")

    if len(text_pts) >= 3:
        rt = np.log([p[0] for p in text_pts])
        gt = np.log([p[1] for p in text_pts])
        kt, _ = np.polyfit(rt, gt, 1)
        print(f"Text:    slope = {kt:.3f}  (expected ~0, g_v=0)")
        print(f"  {'PASS: text-only alpha independent of rank' if abs(kt) < 0.15 else 'WARNING: rank dependence in text-only'}")

    # ---- V4: Trajectory prediction ----
    print("\n" + "=" * 70)
    print("V4 — TRAJECTORY PREDICTION (epoch 1-2 -> 3-10)")
    print("=" * 70)

    errors = []
    for r in valid:
        traj, eps = r.get("dg_star_trajectory"), r.get("epochs")
        if not traj or not eps or len(traj) < 5: continue
        traj, eps = np.array(traj), np.array(eps, dtype=float)

        def mdl(t, A, B, beta):
            return A + B * np.exp(-abs(beta) * t)

        try:
            p, _ = curve_fit(mdl, eps[:2], traj[:2],
                            p0=[traj[1]*0.9, traj[0]-traj[1]*0.9, 0.15], maxfev=2000)
            pred = mdl(eps[2:], p[0], p[1], abs(p[2]))
            mae = np.mean(np.abs(pred - traj[2:])) / max(np.ptp(traj), 1e-8)
            errors.append(mae)
        except: continue

    if errors:
        print(f"Configs: {len(errors)}  NormMAE: {np.mean(errors):.3f}+/-{np.std(errors):.3f}")
        print(f"  {'PASS: trajectory predictable' if np.mean(errors) < 0.15 else 'Partial: >15% error'}")

    # ---- V5: Falsification ----
    print("\n" + "=" * 70)
    print("V5 — FALSIFICATION: text-only alpha(r)")
    print("=" * 70)

    ta = []
    for (rank, pos), runs in sorted(groups.items(), key=lambda x: (x[0][0] or 0, x[0][1] or False)):
        if pos is False and rank is not None:
            alphas = [r["alpha"] for r in runs if r.get("alpha") is not None]
            if alphas: ta.append((rank, np.mean(alphas)))
    if len(ta) >= 3:
        ra = np.array([a[0] for a in ta])
        aa = np.array([a[1] for a in ta])
        ks, _ = np.polyfit(np.log(ra), aa, 1)
        cv = np.std(aa) / (abs(np.mean(aa)) + 1e-8)
        print(f"log(alpha) vs log(r) slope: {ks:.3f}  CV: {cv:.1%}")
        for rk, av in ta: print(f"  r={rk}: alpha = {av:.4f}")
        if abs(ks) < 0.15 and cv < 0.3:
            print(">>> THEORY SURVIVES: text-only alpha independent of rank")
        else:
            print(">>> FALSIFIED: text-only alpha shows rank dependence")
            print("    (This would mean g_v!=0 has residual effect even in text-only)")

    # ---- Paper-ready table ----
    print("\n" + "=" * 70)
    print("PAPER TABLE: mean values by (rank, position)")
    print("=" * 70)
    print(f"{'r':>5s} {'a_txt':>10s} {'a_both':>10s} "
          f"{'b_txt':>10s} {'b_both':>10s} {'DG*_txt':>10s} {'DG*_both':>10s} {'R2_txt':>8s} {'R2_both':>8s}")
    print("-" * 80)

    for rank in sorted(set(r[0] for r in groups if r[0] is not None)):
        tr = groups.get((rank, False), [])
        br = groups.get((rank, True), [])
        def m(k, rs):
            vs = [r[k] for r in rs if r.get(k) is not None]
            return np.mean(vs) if vs else None
        def s(v): return f"{v:.4f}" if v is not None else "N/A"
        print(f"{rank:>5d} {s(m('alpha',tr)):>10s} {s(m('alpha',br)):>10s} "
              f"{s(m('beta',tr)):>10s} {s(m('beta',br)):>10s} "
              f"{s(m('dg_star_inf',tr)):>10s} {s(m('dg_star_inf',br)):>10s} "
              f"{s(m('r_squared',tr)):>8s} {s(m('r_squared',br)):>8s}")

    # ---- β constancy check across ranks ----
    print("\n" + "=" * 70)
    print("A1 RE-CHECK: beta constancy across ranks (PEFT only)")
    print("=" * 70)
    peft_betas = [r["beta"] for r in valid
                  if r.get("beta") and r.get("peft_method") == "lora"]
    if len(peft_betas) >= 5:
        arr = np.array(peft_betas)
        print(f"PEFT beta: {arr.mean():.4f} +/- {arr.std():.4f}  CV={arr.std()/arr.mean():.1%}  n={len(arr)}")
        print(f"  {'A1 PASS' if arr.std()/arr.mean() < 0.3 else 'A1 WEAKENED'}")


if __name__ == "__main__":
    main()
