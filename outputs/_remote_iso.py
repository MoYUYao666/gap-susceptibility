
import os, sys, json, torch
W = "/root/autodl-tmp/work"
os.chdir(W); sys.path.insert(0, W)

print("=== versions ===")
import transformers, torch as T
print("  torch", T.__version__, "| transformers", transformers.__version__)

from src.config import ExperimentConfig, LoRAConfig, TrainConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders

torch.manual_seed(42)
cfg = ExperimentConfig(
    name="isolate_b32_both_s42",
    lora=LoRAConfig(rank=4, alpha=8, apply_to_vision=True, apply_to_text=True),
    train=TrainConfig(dataset="flickr30k", batch_size=128, num_epochs=10,
                      max_samples=5000, clip_model="models/clip-vit-base-patch32",
                      save_dir="outputs/_isolate"),
)
tr = GapAwareTrainer(cfg)
tr.device = "cuda" if torch.cuda.is_available() else "cpu"
tr.setup_model()

print("\n=== LoRA init check (strict-freeze premise: B should be 0) ===")
nzB = nzA = 0
totB = totA = 0
for n, p in tr.model.named_parameters():
    if "lora_B" in n:
        totB += 1
        if p.abs().max().item() > 0:
            nzB += 1
    if "lora_A" in n:
        totA += 1
        if p.abs().max().item() > 0:
            nzA += 1
print(f"  lora_B nonzero tensors: {nzB}/{totB} (expected 0)")
print(f"  lora_A nonzero tensors: {nzA}/{totA} (expected all)")

n_tr = sum(p.numel() for p in tr.model.parameters() if p.requires_grad)
print(f"  n_trainable = {n_tr}")

# freezing check
vis_nz = 0
for n, p in tr.model.named_parameters():
    if "vision_model" in n and p.requires_grad:
        vis_nz += 1
print(f"  tensors with requires_grad in the vision tower: {vis_nz}")

loader, val_loader, _ = create_dataloaders(
    dataset_name="flickr30k", data_dir=".", batch_size=128, max_samples=5000)
print(f"  train batches = {len(loader)} | val = {len(val_loader)}")

params = [p for p in tr.model.parameters() if p.requires_grad]
opt = torch.optim.AdamW(params, lr=1e-4, weight_decay=0.01)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=len(loader) * 10)

print("\n=== train 10 epochs (print loss for the first 3 steps) ===")
losses = []
for ep in range(1, 11):
    tr.model.train()
    for i, b in enumerate(loader):
        imgs = b["image"].to(tr.device)
        ii = b["input_ids"].to(tr.device)
        am = b["attention_mask"].to(tr.device)
        out = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
        import torch.nn.functional as F
        I = F.normalize(out.image_embeds, p=2, dim=-1)
        Tt = F.normalize(out.text_embeds, p=2, dim=-1)
        logits = I @ Tt.T
        lab = torch.arange(I.shape[0], device=tr.device)
        loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
        loss.backward()
        opt.step(); sched.step(); opt.zero_grad()
        if ep == 1 and i < 3:
            print(f"    ep1 step{i}: loss={loss.item():.4f}")
        losses.append(loss.item())

# first/last gap
def gap():
    tr.model.eval()
    with torch.no_grad():
        II, TT = [], []
        for b in val_loader:
            out = tr.model(pixel_values=b["image"].to(tr.device),
                           input_ids=b["input_ids"].to(tr.device),
                           attention_mask=b["attention_mask"].to(tr.device))
            II.append(out.image_embeds); TT.append(out.text_embeds)
        I = torch.cat(II); Tt = torch.cat(TT)
        I = F.normalize(I, p=2, dim=-1); Tt = F.normalize(Tt, p=2, dim=-1)
        return float((I.mean(0) - Tt.mean(0)).norm()), float(((I - Tt) ** 2).sum(-1).mean())

cg1, dg1 = gap()
print(f"\n=== after training ===\n  CG(final)={cg1:.4f} | DG*(final)={dg1:.4f}")
print(f"  loss first/last = {losses[0]:.4f} / {losses[-1]:.4f}")
print("  (local both seed42: CGΔ=−0.0186, i.e. final should be smaller than initial)")
