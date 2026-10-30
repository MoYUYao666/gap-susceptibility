"""Quick test: OpenCLIP BitFit Gamma with raw values."""
import os, sys
os.environ.pop("HF_HUB_OFFLINE", None)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.path.insert(0, ".")

import torch, torch.nn.functional as F
from src.gap_susceptibility import compute_gap_susceptibility
from src.dataset import create_dataloaders

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
import open_clip
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
m = m.to(DEVICE)
m.train()
tok = open_clip.get_tokenizer("ViT-B-32")

# BitFit vision only
for n, p in m.named_parameters():
    p.requires_grad = ("bias" in n and n.startswith("visual."))
print(f"Trainable: {sum(p.numel() for p in m.parameters() if p.requires_grad)}")

# Data
_, val_loader, _ = create_dataloaders(
    dataset_name="flickr30k", data_dir=".",
    batch_size=64, max_samples=500, num_workers=0)

# Get embeddings
for batch in val_loader:
    images = batch["image"].to(DEVICE)[:32]
    texts = batch["caption"][:32]
    tokens = tok(texts).to(DEVICE)
    ie = m.encode_image(images, normalize=True)
    with torch.no_grad():
        te = m.encode_text(tokens, normalize=True)
    print(f"ie.requires_grad={ie.requires_grad}  te.requires_grad={te.requires_grad}")
    break

# Manual DG* backward test
dg = ((ie - te)**2).sum(dim=-1).mean()
print(f"dg.requires_grad={dg.requires_grad}  grad_fn={dg.grad_fn}")
dg.backward(retain_graph=True)
vis_grad_count = sum(1 for n,p in m.named_parameters() if p.requires_grad and p.grad is not None and p.grad.abs().sum()>0)
print(f"Vision params with non-zero grad: {vis_grad_count}")
m.zero_grad()

# Try full Gamma
try:
    gamma = compute_gap_susceptibility(m, ie, te)
    for k, v in gamma.items():
        print(f"  {k}: {v}")
except Exception as e:
    print(f"Gamma failed: {e}")
    import traceback; traceback.print_exc()
