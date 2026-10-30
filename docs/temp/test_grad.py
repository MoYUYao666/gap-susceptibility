"""Debug: check both grad_DG and grad_L for OpenCLIP BitFit."""
import os; os.environ.pop("HF_HUB_OFFLINE",None); os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
import sys; sys.path.insert(0,".")

import torch, torch.nn.functional as F
from src.dataset import create_dataloaders

DEVICE="cuda" if torch.cuda.is_available() else "cpu"
import open_clip
m,_,_=open_clip.create_model_and_transforms("ViT-B-32",pretrained="laion2b_s34b_b79k")
m=m.to(DEVICE); m.train()
tok=open_clip.get_tokenizer("ViT-B-32")

# BitFit vision
for n,p in m.named_parameters():
    p.requires_grad=("bias" in n and n.startswith("visual."))
n_train=sum(p.numel() for p in m.parameters() if p.requires_grad)
print(f"Trainable: {n_train}")

_,vl,_=create_dataloaders(dataset_name="flickr30k",data_dir=".",batch_size=64,max_samples=500,num_workers=0)

for batch in vl:
    img=batch["image"].to(DEVICE)[:32]
    txt=batch["caption"][:32]
    tokens=tok(txt).to(DEVICE)
    ie=m.encode_image(img,normalize=True)
    with torch.no_grad():
        te=m.encode_text(tokens,normalize=True)
    break

# --- grad_DG ---
m.zero_grad()
dg=((ie-te)**2).sum(dim=-1).mean()
dg.backward(retain_graph=True)
vis_dg=sum(1 for n,p in m.named_parameters() if p.requires_grad and p.grad is not None and p.grad.abs().sum()>0)
print(f"grad_DG: {vis_dg} vision params non-zero")

# --- grad_L ---
m.zero_grad()
ls=m.logit_scale.exp()
logits=ls*ie @ te.T
B=ie.shape[0]
labels=torch.arange(B,device=DEVICE)
loss=(F.cross_entropy(logits,labels)+F.cross_entropy(logits.T,labels))/2
loss.backward()
vis_l=sum(1 for n,p in m.named_parameters() if p.requires_grad and p.grad is not None and p.grad.abs().sum()>0)
print(f"grad_L:   {vis_l} vision params non-zero")

# --- Manual Gamma ---
m.zero_grad()
dg.backward(retain_graph=True)
g_dg=torch.cat([p.grad.flatten() for n,p in m.named_parameters() if p.requires_grad and p.grad is not None and "visual" in n])
m.zero_grad()
loss.backward()
g_l=torch.cat([p.grad.flatten() for n,p in m.named_parameters() if p.requires_grad and p.grad is not None and "visual" in n])
dot=(g_dg*g_l).sum().item()
norm_g=g_l.norm().item()
gamma_v=dot/max(norm_g,1e-8)
print(f"Manual Gamma_v: {gamma_v:.6f}  dot={dot:.6f}  norm_g={norm_g:.4f}  norm_dg={g_dg.norm().item():.4f}")
