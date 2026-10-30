"""
Bulk theta_0 Gamma measurement for all V1 LoRA configs.
Re-measures Gamma BEFORE training to improve Theorem 2 correlation.
Lightweight — loads model, injects LoRA, one forward-backward pass.
No training.

Usage: python experiments/theory/theta0_bulk.py
"""
import os, sys, json, warnings
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch, torch.nn.functional as F
from src.config import LoRAConfig, TrainConfig, GapConfig, ExperimentConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders
from src.gap_susceptibility import compute_gap_susceptibility

warnings.filterwarnings("ignore")

ETA, BATCH, STEPS = 1e-4, 128, 8000/128
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "theory" / "theta0"
V1_DIR = PROJECT_ROOT / "outputs" / "theory" / "v1_trajectory"

RANKS = [1, 2, 4, 8, 16, 32, 64]
POSITIONS = [("text", False), ("both", True)]

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    total = len(RANKS) * len(POSITIONS)
    idx = 0

    print(f"Bulk theta_0 measurement: {total} configs")
    print(f"{'Config':22s} {'Gamma_v':>10s} {'Gamma_t':>10s} {'|g_v|':>10s} {'|g_t|':>10s} {'a_pred':>10s} {'a_fit':>10s}")
    print("-" * 90)

    for rank in RANKS:
        for pos_name, pos_val in POSITIONS:
            idx += 1
            name = f"v1_{pos_name}_only_r{rank}" if pos_name == "text" else f"v1_{pos_name}_r{rank}"

            # Load V1 alpha_fit for comparison
            a_fit = None
            for seed_dir in (V1_DIR / name).iterdir() if (V1_DIR / name).exists() else []:
                v1f = seed_dir / "v1_result.json"
                if v1f.exists():
                    a_fit = json.load(open(v1f)).get("alpha")
                    break

            # Measure Gamma at theta_0
            try:
                lora = LoRAConfig(rank=rank, alpha=rank*2,
                                 apply_to_vision=pos_val, apply_to_text=True)
                train = TrainConfig(dataset="flickr30k", batch_size=BATCH,
                                   num_epochs=1, seed=42,
                                   save_dir=str(OUTPUT_DIR / name))
                exp = ExperimentConfig(name=name, peft_method="lora", lora=lora,
                                      gap=GapConfig(compute_every_n_epochs=1), train=train)
                trainer = GapAwareTrainer(exp)
                trainer.setup_model()
                _, val_loader, _ = create_dataloaders(
                    dataset_name="flickr30k", data_dir=str(PROJECT_ROOT),
                    batch_size=BATCH, max_samples=2000, num_workers=0)

                trainer.model.train()
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
                a_pred = -ETA * (gv * ngv + gt * ngt) * STEPS

                a_fit_s = f"{a_fit:.4f}" if a_fit else "N/A"
                print(f"{name:22s} {gv:>10.4f} {gt:>10.4f} {ngv:>10.2f} {ngt:>10.2f} {a_pred:>10.4f} {a_fit_s:>10s}")

                results.append({"name": name, "rank": rank, "position": pos_val,
                               "gamma": gamma, "a_pred": a_pred, "a_fit": a_fit})

                del trainer  # free GPU memory

            except Exception as e:
                print(f"{name:22s} FAILED: {e}")

    # Save and compute correlation
    with open(OUTPUT_DIR / "theta0_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    # Correlation
    preds = [r["a_pred"] for r in results]
    fits = [r["a_fit"] for r in results if r["a_fit"] is not None]
    preds_for_fits = [r["a_pred"] for r in results if r["a_fit"] is not None]
    if len(preds_for_fits) >= 5:
        import numpy as np
        preds_arr = np.array(preds_for_fits)
        fits_arr = np.array(fits)
        r = np.corrcoef(preds_arr, fits_arr)[0, 1]
        print(f"\nCorrelation: r = {r:.4f}  (was 0.580 with post-training measurement)")
        if r > 0.7:
            print(">>> Significant improvement — theta_0 measurement resolves primary discrepancy")
        elif r > 0.6:
            print(">>> Moderate improvement")

    print(f"\nSaved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
