"""Debug: find where OpenCLIP gradients break."""
import os, sys
os.environ.pop("HF_HUB_OFFLINE", None)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import torch, torch.nn.functional as F

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
import open_clip

m, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
m = m.to(DEVICE)
tok = open_clip.get_tokenizer("ViT-B-32")

# Unfreeze vision bias only
for n, p in m.named_parameters():
    p.requires_grad = ("bias" in n and n.startswith("visual."))

n_train = sum(p.numel() for p in m.parameters() if p.requires_grad)
print(f"Trainable: {n_train}")
m.train()

# Dummy input
img = torch.randn(2, 3, 224, 224, device=DEVICE)
txt = tok(["a photo of a cat"]).to(DEVICE)

# Step 1: encode_image
ie = m.encode_image(img, normalize=True)
print(f"Step 1: image_embeds.requires_grad={ie.requires_grad}  grad_fn={ie.grad_fn}")

# Step 2: encode_text
te = m.encode_text(txt, normalize=True)
print(f"Step 2: text_embeds.requires_grad={te.requires_grad}  grad_fn={te.grad_fn}")

# Step 3: compute DG* and backward
if ie.requires_grad and te.requires_grad:
    dg = ((ie - te) ** 2).sum(dim=-1).mean()
    print(f"Step 3: dg.requires_grad={dg.requires_grad}")
    dg.backward()
    has_vis_grad = any(p.grad is not None and p.grad.abs().sum() > 0
                       for n, p in m.named_parameters() if "visual" in n and p.requires_grad)
    print(f"Step 4: visual bias gradient non-zero: {has_vis_grad}")
else:
    print("FAIL: embeddings don't require grad")
    # Try manual forward
    print("\nTrying manual forward...")
    ie_raw = m.visual(img)
    print(f"  visual output type: {type(ie_raw)}")
    if isinstance(ie_raw, tuple):
        ie_raw = ie_raw[0]
    print(f"  visual grad_fn: {ie_raw.grad_fn}")
