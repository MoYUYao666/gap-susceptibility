"""
SigLIP Gamma Measurement
=========================
Measure Gamma_v, Gamma_t for SigLIP ViT-B/16 at theta_0.
Verifies framework generalizes beyond InfoNCE (sigmoid loss).

Direct model loading — bypasses CLIP-specific trainer.

Usage: python experiments/theory/siglip_measure.py
"""
import os, sys, json, warnings
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch, torch.nn.functional as F
import numpy as np
from transformers import AutoModel, AutoProcessor

from src.lora import apply_lora_to_model
from src.gap_susceptibility import compute_gap_susceptibility
from src.dataset import create_dataloaders

warnings.filterwarnings("ignore")

MODEL_ID = "./models/siglip-base-patch16-224"
ETA = 1e-4
BATCH = 64
STEPS = 8000 / BATCH
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "theory" / "siglip"

CONFIGS = [
    {"name": "siglip_text_r8", "rank": 8, "alpha": 16, "vis": False, "txt": True},
    {"name": "siglip_both_r8", "rank": 8, "alpha": 16, "vis": True,  "txt": True},
    {"name": "siglip_frozen",  "rank": 0, "alpha": 0,  "vis": False, "txt": False},
]


def load_siglip():
    """Load SigLIP model + processor (offline)."""
    print(f"Loading {MODEL_ID}...")
    model = AutoModel.from_pretrained(MODEL_ID, local_files_only=True)
    processor = AutoProcessor.from_pretrained(MODEL_ID, local_files_only=True)
    print(f"  Parameters: {sum(p.numel() for p in model.parameters()):,}")
    return model, processor


def inject_lora(model, rank, alpha, apply_vis, apply_txt):
    """Inject LoRA into SigLIP vision/text encoders."""
    if rank == 0:
        for p in model.parameters():
            p.requires_grad = False
        return model, {}, 0

    from src.lora import apply_lora_to_model
    # SigLIP uses 'vision_model' and 'text_model' like CLIP
    model, layers, trainable = apply_lora_to_model(
        model, rank=rank, alpha=alpha,
        apply_to_vision=apply_vis, apply_to_text=apply_txt,
        target_modules=["q_proj", "v_proj"],
    )
    return model, layers, trainable


def get_embeddings(model, processor, loader, device):
    """Get image + text embeddings from one batch."""
    model.train()  # need grads for Gamma measurement
    for batch in loader:
        images = batch["image"].to(device)[:32]
        texts = batch["caption"][:32]

        # SigLIP processor
        inputs = processor(text=texts, images=images, return_tensors="pt",
                          padding="max_length", truncation=True, max_length=64)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        outputs = model(**inputs)

        # SigLIP outputs: image_embeds, text_embeds
        ie = F.normalize(outputs.image_embeds, p=2, dim=-1)
        te = F.normalize(outputs.text_embeds, p=2, dim=-1)
        return ie, te
    return None, None


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load model once
    base_model, processor = load_siglip()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    base_model = base_model.to(device)

    # Data loader (small)
    train_loader, val_loader, _ = create_dataloaders(
        dataset_name="flickr30k", data_dir=str(PROJECT_ROOT),
        batch_size=BATCH, max_samples=500, num_workers=0,
    )

    print(f"\n{'Config':20s} {'Gamma_v':>10s} {'Gamma_t':>10s} {'|g_v|':>10s} {'|g_t|':>10s} {'a_epoch':>10s} {'cos_v':>8s} {'cos_t':>8s}")
    print("-" * 90)

    results = []
    for cfg in CONFIGS:
        name = cfg["name"]

        # Fresh copy for each config (LoRA injection mutates model)
        model, _ = load_siglip()
        # Move to device BEFORE injecting LoRA so LoRA params are on GPU
        model = model.to(device)

        if cfg["rank"] > 0:
            model, _, _ = inject_lora(model, cfg["rank"], cfg["alpha"],
                                      cfg["vis"], cfg["txt"])
            # Re-move to device to ensure LoRA params on GPU
            model = model.to(device)

        # Get embeddings
        ie, te = get_embeddings(model, processor, val_loader, device)
        if ie is None:
            print(f"{name:20s}  FAILED")
            continue

        # Measure Gamma at theta_0
        gamma = compute_gap_susceptibility(model, ie, te)
        gv, gt = gamma["Gamma_v"], gamma["Gamma_t"]
        ngv, ngt = gamma["norm_g_v"], gamma["norm_g_t"]
        a_epoch = -ETA * (gv*ngv + gt*ngt) * STEPS
        cv, ct = gamma["cos_phi_v"], gamma["cos_phi_t"]

        print(f"{name:20s} {gv:>10.4f} {gt:>10.4f} {ngv:>10.2f} {ngt:>10.2f} {a_epoch:>10.4f} {cv:>8.4f} {ct:>8.4f}")

        results.append({"name": name, "gamma": gamma, "alpha_pred": a_epoch})
        with open(OUTPUT_DIR / f"{name}.json", "w") as f:
            json.dump(results[-1], f, indent=2, ensure_ascii=False, default=str)

        del model  # free memory

    # Summary
    print(f"\n{'='*60}")
    print("SigLIP vs CLIP comparison:")
    print(f"{'='*60}")
    clip_text_a = -0.048  # from V1
    clip_both_a = -0.042
    for r in results:
        if "text" in r["name"]:
            print(f"  {r['name']}: alpha_pred={r['alpha_pred']:.4f}  (CLIP: {clip_text_a})")
        elif "both" in r["name"]:
            print(f"  {r['name']}: alpha_pred={r['alpha_pred']:.4f}  (CLIP: {clip_both_a})")

    print(f"\nSaved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
