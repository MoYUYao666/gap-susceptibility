"""
Prospective Prediction — the definitive test of Theorem 2.
===========================================================
Before any training, measure Gamma at theta_0 for 6 configurations.
Predict DG*_inf ranking. Compare against actual V1 results.

This is the experiment the advisor wants: "predict which config is
best from epoch-0 Gamma alone."

Usage: python experiments/theory/prospective_prediction.py
"""

import os, sys, json, time, warnings
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch, torch.nn.functional as F

from src.config import ExperimentConfig, LoRAConfig, TrainConfig, GapConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders
from src.gap_susceptibility import compute_gap_susceptibility

warnings.filterwarnings("ignore")

ETA = 1e-4
BETA = 0.137   # from Phase 1 (PEFT pooled)
STEPS = 8000 / 128  # per epoch
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "theory" / "prospective"

# 6 configs to predict
CONFIGS = [
    {"name": "text_r4",  "rank": 4,  "alpha": 8,  "vis": False, "txt": True},
    {"name": "text_r8",  "rank": 8,  "alpha": 16, "vis": False, "txt": True},
    {"name": "text_r16", "rank": 16, "alpha": 32, "vis": False, "txt": True},
    {"name": "both_r4",  "rank": 4,  "alpha": 8,  "vis": True,  "txt": True},
    {"name": "both_r8",  "rank": 8,  "alpha": 16, "vis": True,  "txt": True},
    {"name": "both_r16", "rank": 16, "alpha": 32, "vis": True,  "txt": True},
]

# V1 actual results for comparison
V1_ACTUAL = {
    "text_r4":  {"DG*_inf": 1.267, "alpha": -0.043, "rank": 1},
    "text_r8":  {"DG*_inf": 1.257, "alpha": -0.048, "rank": 2},
    "text_r16": {"DG*_inf": 1.295, "alpha": -0.068, "rank": 4},
    "both_r4":  {"DG*_inf": 1.317, "alpha": -0.074, "rank": 6},
    "both_r8":  {"DG*_inf": 1.250, "alpha": -0.042, "rank": 0},
    "both_r16": {"DG*_inf": 1.278, "alpha": -0.047, "rank": 3},
}
# rank: 0=best (smallest DG*_inf within position)

# Also get frozen baseline DG_0 from V1 data
V1_DIR = PROJECT_ROOT / "outputs" / "theory" / "v1_trajectory"
frozen_file = V1_DIR / "v1_frozen" / "seed42" / "v1_result.json"
if frozen_file.exists():
    with open(frozen_file) as f:
        DG0 = json.load(f).get("dg_star_inf", 1.25)
else:
    DG0 = 1.25  # fallback


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("PROSPECTIVE PREDICTION — Theorem 2 definitive test")
    print(f"Configs: {len(CONFIGS)}  |  beta = {BETA}  |  DG0 = {DG0:.3f}")
    print("=" * 70)

    predictions = []

    for cfg in CONFIGS:
        name = cfg["name"]
        print(f"\n--- {name} ---")

        lora = LoRAConfig(rank=cfg["rank"], alpha=cfg["alpha"],
                          apply_to_vision=cfg["vis"], apply_to_text=cfg["txt"])
        train = TrainConfig(dataset="flickr30k", batch_size=128, num_epochs=1,
                            save_dir=str(OUTPUT_DIR / name), seed=42)
        exp = ExperimentConfig(name=name, peft_method="lora", lora=lora,
                               gap=GapConfig(compute_every_n_epochs=1), train=train)

        trainer = GapAwareTrainer(exp)
        trainer.setup_model()
        train_loader, val_loader, _ = create_dataloaders(
            dataset_name="flickr30k", data_dir=str(PROJECT_ROOT),
            batch_size=128, max_samples=2000, num_workers=0)

        # Measure Gamma at theta_0 — BEFORE any training
        trainer.model.eval()
        gamma = None
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

        gv, gt = gamma["Gamma_v"], gamma["Gamma_t"]
        ngv, ngt = gamma["norm_g_v"], gamma["norm_g_t"]
        a_step = -ETA * (gv * ngv + gt * ngt)
        a_epoch = a_step * STEPS
        dg_pred = DG0 - (ETA * STEPS / BETA) * (gv * ngv + gt * ngt)

        actual = V1_ACTUAL.get(name, {})
        print(f"  Gamma_v={gv:.4f}  Gamma_t={gt:.4f}  |g_v|={ngv:.2f}  |g_t|={ngt:.2f}")
        print(f"  alpha_pred={a_epoch:.4f}  DG*_inf_pred={dg_pred:.4f}")
        if actual:
            print(f"  alpha_actual={actual['alpha']:.4f}  DG*_inf_actual={actual['DG*_inf']:.4f}")

        predictions.append({
            "name": name, "gamma": gamma,
            "alpha_pred": a_epoch, "dg_pred": dg_pred,
            "alpha_actual": actual.get("alpha"),
            "dg_actual": actual.get("DG*_inf"),
        })

    # --- Ranking comparison ---
    print("\n" + "=" * 70)
    print("RANKING COMPARISON")
    print("=" * 70)

    # Within text-only
    text_preds = [p for p in predictions if "text" in p["name"]]
    both_preds = [p for p in predictions if "both" in p["name"]]

    for group_name, group in [("text-only", text_preds), ("both", both_preds)]:
        group.sort(key=lambda x: x["dg_pred"])
        print(f"\n{group_name} — predicted ranking (smaller DG* = better):")
        for i, p in enumerate(group):
            actual_rank = V1_ACTUAL.get(p["name"], {}).get("rank", "?")
            match = "✓" if actual_rank == i else f"(actual rank={actual_rank})"
            print(f"  {i+1}. {p['name']:12s}  DG*_pred={p['dg_pred']:.4f}  DG*_actual={p.get('dg_actual',0):.4f}  {match}")

    # --- Correlation ---
    all_pred = np.array([p["dg_pred"] for p in predictions])
    all_actual = np.array([p["dg_actual"] for p in predictions if p["dg_actual"] is not None])
    pred_for_actual = np.array([p["dg_pred"] for p in predictions if p["dg_actual"] is not None])

    if len(pred_for_actual) >= 4:
        r = np.corrcoef(pred_for_actual, all_actual)[0, 1]
        mae = np.mean(np.abs(pred_for_actual - all_actual))
        print(f"\nDG* correlation: r = {r:.4f}  MAE = {mae:.4f}")
        if r > 0.5:
            print(">>> PROSPECTIVE PREDICTION PASSES: Gamma at theta_0 predicts DG*_inf ranking")
        else:
            print(">>> PARTIAL: ranking partially predicted, see Discussion")

    # Save
    with open(OUTPUT_DIR / "prospective_results.json", "w") as f:
        json.dump(predictions, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nSaved: {OUTPUT_DIR / 'prospective_results.json'}")


if __name__ == "__main__":
    main()
