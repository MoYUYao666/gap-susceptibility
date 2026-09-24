"""
SigLIP both_r8 — fixed measurement.
Directly measures only LoRA-injected parameters.
"""
import os, sys, json, warnings
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch, torch.nn.functional as F
from src.lora import apply_lora_to_model
from src.dataset import create_dataloaders

warnings.filterwarnings("ignore")

MODEL_ID = "./models/siglip-base-patch16-224"
ETA, BATCH, STEPS = 1e-4, 64, 8000/64
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load SigLIP
from transformers import AutoModel
print(f"Loading {MODEL_ID}...")
model = AutoModel.from_pretrained(MODEL_ID, local_files_only=True).to(DEVICE)

# Inject LoRA on CPU, then move everything to device
model, lora_layers, trainable = apply_lora_to_model(
    model, rank=8, alpha=16,
    apply_to_vision=True, apply_to_text=True,
    target_modules=["q_proj", "v_proj"],
)
model = model.to(DEVICE)  # move LoRA params to GPU
print(f"LoRA layers: {len(lora_layers)}  Trainable: {trainable:,}")

# Data
_, val_loader, _ = create_dataloaders(
    dataset_name="flickr30k", data_dir=str(PROJECT_ROOT),
    batch_size=BATCH, max_samples=500, num_workers=0,
)

from transformers import AutoProcessor
processor = AutoProcessor.from_pretrained(MODEL_ID, local_files_only=True)

# Forward pass
model.train()
for batch in val_loader:
    images = batch["image"].to(DEVICE)[:32]
    texts = batch["caption"][:32]
    inputs = processor(text=texts, images=images, return_tensors="pt",
                      padding="max_length", truncation=True, max_length=64)
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    outputs = model(**inputs)
    ie = F.normalize(outputs.image_embeds, p=2, dim=-1)
    te = F.normalize(outputs.text_embeds, p=2, dim=-1)
    break

# ---- Manual Gamma measurement (fixed: only LoRA params) ----
model.zero_grad()
dg_star = ((ie - te) ** 2).sum(dim=-1).mean()
dg_star.backward(retain_graph=True)

grad_DG = {}
for name, param in model.named_parameters():
    if param.grad is not None:
        grad_DG[name] = param.grad.clone()

model.zero_grad()
logit_scale = model.logit_scale.exp() if hasattr(model, 'logit_scale') else torch.tensor(1.0, device=DEVICE).exp()
logits_per_image = logit_scale * ie @ te.T
logits_per_text = logits_per_image.T
B = ie.shape[0]
labels = torch.arange(B, device=DEVICE)
loss = (F.cross_entropy(logits_per_image, labels) + F.cross_entropy(logits_per_text, labels)) / 2.0
loss.backward()

grad_L = {}
for name, param in model.named_parameters():
    if param.grad is not None:
        grad_L[name] = param.grad.clone()

model.zero_grad()

# Filter: ONLY LoRA params (lora_A or lora_B in name)
lora_names = {n for n in grad_DG if "lora_A" in n or "lora_B" in n}

def accum(prefix):
    dot, ng, ndg, du = 0.0, 0.0, 0.0, 0.0
    for n in lora_names:
        if prefix not in n or n not in grad_L: continue
        gd = grad_DG[n].flatten(); gl = grad_L[n].flatten()
        dot += (gd * gl).sum().item()
        ng += (gl**2).sum().item()
        ndg += (gd**2).sum().item()
        du += (gd * gl).sum().item()
    ng = ng**0.5; ndg = ndg**0.5
    cos = du / max(ndg * ng, 1e-8)
    return dot / max(ng, 1e-8), ng, ndg, cos

gv, ngv, ndgv, cv = accum("vision")
gt, ngt, ndgt, ct = accum("text")
a_epoch = -ETA * (gv * ngv + gt * ngt) * STEPS

print(f"Gamma_v={gv:.4f}  Gamma_t={gt:.4f}")
print(f"|g_v|={ngv:.2f}  |g_t|={ngt:.2f}")
print(f"cos_v={cv:.4f}  cos_t={ct:.4f}")
print(f"alpha_pred (per-epoch) = {a_epoch:.4f}")
print(f"LoRA param count: {len(lora_names)} (vision in lora: {sum(1 for n in lora_names if 'vision' in n)})")
