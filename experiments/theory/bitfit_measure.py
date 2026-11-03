"""
BitFit Gamma measurement — train only bias terms.
Third PEFT method (after LoRA hard constraint, Adapter soft bottleneck).
Tests whether Gamma framework holds for minimal-parameter PEFT.

Usage: python experiments/theory/bitfit_measure.py
"""
import os, sys, json, warnings
# CLIP model is already cached locally — keep offline
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch, torch.nn.functional as F
import numpy as np

from src.gap_susceptibility import compute_gap_susceptibility
from src.dataset import create_dataloaders

warnings.filterwarnings("ignore")

ETA, BATCH, STEPS = 1e-4, 128, 8000/128
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load CLIP
from transformers import CLIPModel, CLIPProcessor
MODEL_ID = "openai/clip-vit-base-patch32"
print(f"Loading {MODEL_ID}...")
model = CLIPModel.from_pretrained(MODEL_ID, local_files_only=True).to(DEVICE)
processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=True)
model.train()

# Freeze all, unfreeze only bias
for n, p in model.named_parameters():
    p.requires_grad = "bias" in n
print(f"  Trainable: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

# Data
_, val_loader, _ = create_dataloaders(
    dataset_name="flickr30k", data_dir=str(PROJECT_ROOT),
    batch_size=BATCH, max_samples=500, num_workers=0,
)

# Get embeddings — need full autograd path
for batch in val_loader:
    images = batch["image"].to(DEVICE)[:32]
    texts = batch["caption"][:32]
    ti = processor(text=texts, return_tensors="pt", padding=True, truncation=True, max_length=77)
    outputs = model(pixel_values=images, input_ids=ti["input_ids"].to(DEVICE),
                    attention_mask=ti.get("attention_mask",
                        torch.ones_like(ti["input_ids"])).to(DEVICE),
                    return_dict=True)
    ie = outputs.image_embeds
    te = outputs.text_embeds
    print(f"  ie.requires_grad={ie.requires_grad}  te.requires_grad={te.requires_grad}")
    print(f"  ie.grad_fn={ie.grad_fn}")
    print(f"  te.grad_fn={te.grad_fn}")
    ie = F.normalize(ie, p=2, dim=-1)
    te = F.normalize(te, p=2, dim=-1)
    break

gamma = compute_gap_susceptibility(model, ie, te)
gv, gt = gamma["Gamma_v"], gamma["Gamma_t"]
ngv, ngt = gamma["norm_g_v"], gamma["norm_g_t"]
a_epoch = -ETA * (gv*ngv + gt*ngt) * STEPS

print(f"BitFit (bias-only):")
print(f"  Gamma_v={gv:.4f}  Gamma_t={gt:.4f}")
print(f"  |g_v|={ngv:.2f}  |g_t|={ngt:.2f}")
print(f"  cos_v={gamma['cos_phi_v']:.4f}  cos_t={gamma['cos_phi_t']:.4f}")
print(f"  alpha_pred = {a_epoch:.4f}")
print(f"  Trainable: vision={sum(1 for n,p in model.named_parameters() if 'vision' in n and p.requires_grad)}, text={sum(1 for n,p in model.named_parameters() if 'text' in n and p.requires_grad)}")
