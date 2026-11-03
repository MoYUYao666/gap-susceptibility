"""
Measure Gamma at epoch 1 from saved V1 checkpoints.
Best checkpoint = epoch with lowest val loss (likely epoch 8-10).
We rewind to epoch 1 by taking 1 DG* step and measuring Gamma.

Simpler approach: load model, inject LoRA, train exactly 1 epoch, measure Gamma.
"""
import os, sys, json, warnings
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

ETA, BATCH, STEPS = 1e-4, 128, 8000/128
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "theory" / "epoch1"

RANKS = [1, 2, 4, 8, 16, 32, 64]
POSITIONS = [("text_only", False), ("both", True)]

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    total = len(RANKS) * len(POSITIONS)
    idx = 0

    print(f"Epoch-1 Gamma measurement: {total} configs")
    print(f"{'Config':25s} {'Gamma_v':>10s} {'Gamma_t':>10s} {'|g_v|':>10s} {'|g_t|':>10s} {'a_pred':>10s} {'a_fit':>10s}")
    print("-" * 100)

    # V1 reference alphas
    v1_dir = PROJECT_ROOT / "outputs" / "theory" / "v1_trajectory"

    for rank in RANKS:
        for pos_name, pos_val in POSITIONS:
            idx += 1
            name = f"v1_{pos_name}_r{rank}"

            # Skip if already done
            result_path = OUTPUT_DIR / name / "results.json"
            if result_path.exists():
                print(f"\n[{idx}/{total}] {name} -- SKIP (cached)")
                continue

            print(f"\n[{idx}/{total}] {name}")

            # Get V1 alpha_fit for comparison
            a_fit = None
            v1_path = v1_dir / name
            if v1_path.exists():
                for sd in v1_path.iterdir():
                    f = sd / "v1_result.json"
                    if f.exists():
                        a_fit = json.load(open(f)).get("alpha")
                        break

            try:
                # Setup and train for 1 epoch
                lora = LoRAConfig(rank=rank, alpha=rank*2,
                                 apply_to_vision=pos_val, apply_to_text=True)
                train = TrainConfig(dataset="flickr30k", batch_size=BATCH,
                                   num_epochs=1, seed=42,
                                   save_dir=str(OUTPUT_DIR / name))
                exp = ExperimentConfig(name=name, peft_method="lora", lora=lora,
                                      gap=GapConfig(compute_every_n_epochs=1), train=train)

                trainer = GapAwareTrainer(exp)
                trainer.setup_model()
                train_loader, val_loader, _ = create_dataloaders(
                    dataset_name="flickr30k", data_dir=str(PROJECT_ROOT),
                    batch_size=BATCH, max_samples=10000, num_workers=0,
                )

                # Train exactly 1 epoch
                trainer.train(train_loader, val_loader)

                # Now measure Gamma at epoch 1
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

                a_fit_s = f"{a_fit:.4f}" if a_fit is not None else "N/A"
                print(f"{name:25s} {gv:>10.4f} {gt:>10.4f} {ngv:>10.2f} {ngt:>10.2f} {a_pred:>10.4f} {a_fit_s:>10s}")

                r = {"name": name, "rank": rank, "position": pos_val,
                     "gamma": gamma, "a_pred": a_pred, "a_fit": a_fit}
                results.append(r)
                # Save per-config immediately
                per_cfg_file = OUTPUT_DIR / name / "epoch1_result.json"
                per_cfg_file.parent.mkdir(parents=True, exist_ok=True)
                with open(per_cfg_file, "w") as f:
                    json.dump(r, f, indent=2, ensure_ascii=False, default=str)

                del trainer

            except Exception as e:
                print(f"  FAILED: {e}")

    # Reload any cached configs from previous runs
    for cfg_file in sorted(OUTPUT_DIR.glob("*/epoch1_result.json")):
        d = json.load(open(cfg_file))
        if d["name"] not in [r["name"] for r in results]:
            results.append(d)

    # Save and correlation
    with open(OUTPUT_DIR / "epoch1_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    preds = [r["a_pred"] for r in results]
    fits = [r["a_fit"] for r in results if r["a_fit"] is not None]
    preds_for = [r["a_pred"] for r in results if r["a_fit"] is not None]
    if len(preds_for) >= 5:
        pa = np.array(preds_for)
        fa = np.array(fits)
        r = np.corrcoef(pa, fa)[0, 1]
        print(f"\n{'='*60}")
        print(f"Epoch-1 correlation: r = {r:.4f}")
        print(f"  Post-training r = 0.580")
        print(f"  theta_0 r        = -0.271")
        if r > 0.65:
            print(f">>> Improvement over post-training!")
        elif r > 0.55:
            print(f">>> Comparable to post-training")
        else:
            print(f">>> No improvement")

    print(f"\nSaved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
