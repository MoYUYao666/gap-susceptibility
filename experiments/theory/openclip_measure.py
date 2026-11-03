"""
OpenCLIP Gamma measurement — BitFit style (unfreeze only bias terms).
Avoids LoRA injection issues with OpenCLIP internals.
"""
import os, sys, warnings
os.environ.pop("HF_HUB_OFFLINE", None)
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch, torch.nn.functional as F
import numpy as np
from src.gap_susceptibility import compute_gap_susceptibility
from src.dataset import create_dataloaders

warnings.filterwarnings("ignore")

ETA, BATCH, STEPS = 1e-4, 64, 8000/64
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

import open_clip

def load_and_config(apply_vision, apply_text):
    """Load OpenCLIP, unfreeze bias params only on specified modalities."""
    m, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    m = m.to(DEVICE)
    m.train()

    for n, p in m.named_parameters():
        is_bias = "bias" in n
        in_vision = n.startswith("visual.")
        in_text = not in_vision  # everything else is text transformer
        p.requires_grad = is_bias and (
            (apply_vision and in_vision) or (apply_text and in_text))

    n_train = sum(p.numel() for p in m.parameters() if p.requires_grad)
    n_vis = sum(p.numel() for n, p in m.named_parameters() if p.requires_grad and n.startswith("visual."))
    n_txt = sum(p.numel() for n, p in m.named_parameters() if p.requires_grad and not n.startswith("visual."))
    return m, n_train, n_vis, n_txt

tokenizer = open_clip.get_tokenizer("ViT-B-32")

# Data
_, val_loader, _ = create_dataloaders(
    dataset_name="flickr30k", data_dir=str(PROJECT_ROOT),
    batch_size=BATCH, max_samples=500, num_workers=0,
)

CONFIGS = [
    {"name": "openclip_both", "vis": True,  "txt": True},
]

print(f"{'Config':20s} {'Gamma_v':>10s} {'Gamma_t':>10s} {'|g_v|':>10s} {'|g_t|':>10s} {'a_pred':>10s} {'cos_v':>8s} {'cos_t':>8s}")
print("-" * 90)

for cfg in CONFIGS:
    m, n_train, n_vis, n_txt = load_and_config(cfg["vis"], cfg["txt"])
    print(f"\n{cfg['name']}: {n_train} trainable (vision={n_vis} text={n_txt})")

    for batch in val_loader:
        images = batch["image"].to(DEVICE)[:32]
        texts = batch["caption"][:32]
        tokens = tokenizer(texts).to(DEVICE)

        ie = m.encode_image(images, normalize=True)
        print(f"  ie.requires_grad={ie.requires_grad}  grad_fn={type(ie.grad_fn).__name__}")

        # Quick test: can we backward through ie?
        dg = (ie**2).sum()
        try:
            dg.backward(retain_graph=True)
            has_vis_grad = any(p.grad is not None and p.grad.abs().sum()>0
                              for n,p in m.named_parameters() if p.requires_grad)
            print(f"  vision grad test: {has_vis_grad}")
            m.zero_grad()
        except Exception as e:
            print(f"  grad test failed: {e}")
        break

    # Now do actual measurement
    for batch in val_loader:
        images = batch["image"].to(DEVICE)[:32]
        texts = batch["caption"][:32]
        tokens = tokenizer(texts).to(DEVICE)
        ie = m.encode_image(images, normalize=True)
        with torch.no_grad():
            te = m.encode_text(tokens, normalize=True)
        break

    try:
        gamma = compute_gap_susceptibility(m, ie, te)
        gv, gt = gamma["Gamma_v"], gamma["Gamma_t"]
        ngv, ngt = gamma["norm_g_v"], gamma["norm_g_t"]
        a_epoch = -ETA * (gv*ngv + gt*ngt) * STEPS
        cv, ct = gamma["cos_phi_v"], gamma["cos_phi_t"]
        print(f"{cfg['name']:20s} {gv:>10.4f} {gt:>10.4f} {ngv:>10.2f} {ngt:>10.2f} {a_epoch:>10.4f} {cv:>8.4f} {ct:>8.4f}")
    except Exception as e:
        print(f"  Failed: {e}")

    del m

print("\nCLIP baseline: text alpha=-0.048, both alpha=-0.042 (both negative)")
