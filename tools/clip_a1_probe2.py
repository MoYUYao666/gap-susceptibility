"""A1 probe 2: rank-preservation verification.
Measure (a) ImageNet class-level ranking Kendall τ vs λ=0 under global shifts at each λ; (b) τ of real both_r8 fine-tuning vs frozen.
Prediction: τ(global shift) collapses with λ; τ(both_r8) stays high → decoupling mechanism = rank preservation of the training perturbation.
"""
import os, sys, json
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn.functional as F
import numpy as np
from glob import glob
from datasets import Dataset
from transformers import CLIPModel, CLIPProcessor
from torch.utils.data import DataLoader
from src.dataset import Flickr30kDataset, _collate_fn
from src.lora import apply_lora_to_model
from scipy import stats

TEMPLATE = 'a photo of a {}'
LAMBDAS = [0.5, 1.0, 2.0]
N_SAMPLE = 5000  # 5000 sampled images are enough for τ

model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True).cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)

PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
ds_in = Dataset.from_parquet(PARQ)
names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
texts = [TEMPLATE.format(c.replace('_', ' ')) for c in names]

rng = np.random.RandomState(42)
idx = rng.choice(len(ds_in), N_SAMPLE, replace=False)
sub = ds_in.select(list(idx))


@torch.no_grad()
def img_feats(m):
    out_list = []
    for i in range(0, len(sub), 64):
        b = sub[i:i + 64]
        inp = processor(images=b['image'], return_tensors='pt').to('cuda')
        vout = m.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        out_list.append(F.normalize(m.visual_projection(vpooled), dim=-1))
    return torch.cat(out_list)


@torch.no_grad()
def text_feats(m):
    text_in = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = m.text_model(**text_in)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    return F.normalize(m.text_projection(pooled), dim=-1)


# gap direction (Flickr30k val)
ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
val_ds = torch.utils.data.Subset(ds_f, range(2000, 3000))
loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0, collate_fn=_collate_fn)
with torch.no_grad():
    f_img, f_txt = [], []
    for batch in loader:
        out = model(pixel_values=batch['image'].cuda(),
                    input_ids=batch['input_ids'].cuda(),
                    attention_mask=batch['attention_mask'].cuda())
        f_img.append(F.normalize(out.image_embeds, dim=-1))
        f_txt.append(F.normalize(out.text_embeds, dim=-1))
f_img = torch.cat(f_img); f_txt = torch.cat(f_txt)
mu_i = f_img.mean(0); mu_t = f_txt.mean(0)
gap_vec = mu_t - mu_i; gap_norm = gap_vec.norm().item(); d_hat = gap_vec / gap_norm

tf = text_feats(model)
base = img_feats(model)          # frozen, λ=0
base_sims = base @ tf.T
base_top1 = (base_sims.argmax(1).cpu() == torch.tensor(sub['label'])).float().mean().item() * 100
print('frozen top-1 (5k sample) = %.2f%%' % base_top1, flush=True)


def kendall_topk(rank_a, rank_b, k=5):
    """Mean Kendall τ of the class-level top-k set (per-image rank correlation over the top k classes, then averaged)."""
    taus = []
    topk = np.argsort(-rank_a, axis=1)[:, :k]
    for i in range(len(rank_a)):
        r1 = rank_a[i][topk[i]]; r2 = rank_b[i][topk[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    return float(np.mean(taus))


results = {}
for lam in LAMBDAS:
    shifted = F.normalize(base + lam * gap_norm * d_hat, dim=-1)
    sims = shifted @ tf.T
    top1 = (sims.argmax(1).cpu() == torch.tensor(sub['label'])).float().mean().item() * 100
    tau = kendall_topk(base_sims.cpu().numpy(), sims.cpu().numpy(), k=5)
    results['lambda_%+.1f' % lam] = {'top1': round(top1, 2), 'kendall_tau_top5': round(tau, 4)}
    print('λ=%+.1f  top-1=%.2f%%  τ_top5=%.4f' % (lam, top1, tau), flush=True)

# real both_r8 fine-tuning
m2, lora_layers, _ = apply_lora_to_model(
    CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True),
    rank=8, alpha=16.0, apply_to_vision=True, apply_to_text=True)
sd = torch.load('outputs/imagenet_zs/both_r8/best_checkpoint.pt', map_location='cpu', weights_only=False)['lora_state_dict']
with torch.no_grad():
    for k, w in sd.items():
        lora_layers[k].lora_A.data.copy_(w['A'])
        lora_layers[k].lora_B.data.copy_(w['B'])
m2 = m2.cuda().eval()
with torch.no_grad():
    ft_feats = img_feats(m2)
    ft_sims = ft_feats @ tf.T
    ft_top1 = (ft_sims.argmax(1).cpu() == torch.tensor(sub['label'])).float().mean().item() * 100
    ft_tau = kendall_topk(base_sims.cpu().numpy(), ft_sims.cpu().numpy(), k=5)
results['both_r8_ft'] = {'top1': round(ft_top1, 2), 'kendall_tau_top5': round(ft_tau, 4)}
print('both_r8 fine-tuned: top-1=%.2f%%  τ_top5=%.4f' % (ft_top1, ft_tau), flush=True)

json.dump({'frozen_top1_5k': round(base_top1, 2), 'gap_norm': round(gap_norm, 4),
           'results': results}, open('outputs/a1_probe2_tau.json', 'w', encoding='utf-8'), indent=2)
print('saved outputs/a1_probe2_tau.json', flush=True)
