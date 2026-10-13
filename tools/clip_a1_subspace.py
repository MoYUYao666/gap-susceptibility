"""A1 experiment 2: perturbation subspace spectrum (5000-image sample).
Perturbation families:
- G: isotropic Gaussian noise σ∈{0.25,0.5,1,2} (σ×gap_norm magnitude)
- L: low-rank structured perturbation k∈{1,4,16,64} (unit vector inside a random k-dimensional subspace × gap_norm)
- P: order-preserving positive control---contraction toward the class's own centroid a∈{0.25,0.5} (stronger within-class alignment, expected to preserve τ and raise top-1)
- T: global translation λ=+1 (reused from the full experiment as a baseline)
Metrics: top-1, top-5, τ_top5 (vs the frozen ranking). Results are stored in outputs/a1_subspace_results.json.
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
from scipy import stats

TEMPLATE = 'a photo of a {}'
N = 5000
OUT = 'outputs/a1_subspace_results.json'

model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True).cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
ds_in = Dataset.from_parquet(PARQ)
names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
texts = [TEMPLATE.format(c.replace('_', ' ')) for c in names]

rng = np.random.RandomState(42)
idx = rng.choice(len(ds_in), N, replace=False)
sub = ds_in.select(list(idx))
labels = torch.tensor(sub['label'])

with torch.no_grad():
    text_in = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**text_in)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    tf = F.normalize(model.text_projection(pooled), dim=-1)
    imgs = []
    for i in range(0, len(sub), 64):
        b = sub[i:i + 64]
        inp = processor(images=b['image'], return_tensors='pt').to('cuda')
        vout = model.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        imgs.append(F.normalize(model.visual_projection(vpooled), dim=-1))
    base = torch.cat(imgs)  # (N, D)
print('frozen embedding extraction done: %d x %d' % base.shape, flush=True)

# gap direction
ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
val_ds = torch.utils.data.Subset(ds_f, range(2000, 3000))
loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0, collate_fn=_collate_fn)
with torch.no_grad():
    fi, ft = [], []
    for batch in loader:
        out = model(pixel_values=batch['image'].cuda(),
                    input_ids=batch['input_ids'].cuda(),
                    attention_mask=batch['attention_mask'].cuda())
        fi.append(F.normalize(out.image_embeds, dim=-1))
        ft.append(F.normalize(out.text_embeds, dim=-1))
fi = torch.cat(fi); ft = torch.cat(ft)
gap_vec = ft.mean(0) - fi.mean(0)
gap_norm = gap_vec.norm().item()
d_hat = gap_vec / gap_norm
print('gap_norm = %.4f' % gap_norm, flush=True)

base_sims = base @ tf.T
base_sims_np = base_sims.cpu().numpy()
topk5 = np.argsort(-base_sims_np, axis=1)[:, :5]

# class centroids (for the positive control)
cls_ids = torch.tensor(sorted(set(ds_in['label'])))
cents = torch.stack([base[labels == c].mean(0) for c in cls_ids])
cents = F.normalize(cents, dim=-1)
lab_map = {int(c): i for i, c in enumerate(cls_ids)}


def evaluate(img2):
    sims = img2 @ tf.T
    pred = sims.argmax(1).cpu()
    top1 = (pred == labels).float().mean().item() * 100
    top5 = (sims.topk(5, dim=1).indices.cpu() == labels.unsqueeze(1)).any(1).float().mean().item() * 100
    s_np = sims.cpu().numpy()
    taus = []
    for i in range(N):
        r1v = base_sims_np[i][topk5[i]]
        r2v = s_np[i][topk5[i]]
        if np.std(r1v) < 1e-12 or np.std(r2v) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1v, r2v)
        if np.isfinite(t):
            taus.append(t)
    tau = float(np.mean(taus))
    return top1, top5, tau


rows = []
rng2 = np.random.RandomState(7)
D = base.shape[1]

# global translation baseline λ=+1
with torch.no_grad():
    img2 = F.normalize(base + gap_norm * d_hat, dim=-1)
t1, t5, tau = evaluate(img2)
rows.append({'family': 'translation', 'param': 1.0, 'top1': round(t1, 2), 'top5': round(t5, 2), 'tau_top5': round(tau, 4)})
print('T λ=1: top1=%.2f top5=%.2f tau=%.4f' % (t1, t5, tau), flush=True)

# Gaussian noise
for sig in [0.25, 0.5, 1.0, 2.0]:
    noise = torch.tensor(rng2.randn(N, D), dtype=torch.float32, device='cuda')
    noise = noise / noise.norm(dim=-1, keepdim=True)
    with torch.no_grad():
        img2 = F.normalize(base + sig * gap_norm * noise, dim=-1)
    t1, t5, tau = evaluate(img2)
    rows.append({'family': 'gaussian', 'param': sig, 'top1': round(t1, 2), 'top5': round(t5, 2), 'tau_top5': round(tau, 4)})
    print('G σ=%.2f: top1=%.2f top5=%.2f tau=%.4f' % (sig, t1, t5, tau), flush=True)

# low-rank structured perturbation
Q, _ = torch.linalg.qr(torch.tensor(rng2.randn(D, D), dtype=torch.float32, device='cuda'))
for k in [1, 4, 16, 64]:
    Pk = Q[:, :k] @ Q[:, :k].T  # rank-k projection
    v = torch.tensor(rng2.randn(D), dtype=torch.float32, device='cuda')
    v = Pk @ v
    v = v / v.norm()
    with torch.no_grad():
        img2 = F.normalize(base + gap_norm * v, dim=-1)
    t1, t5, tau = evaluate(img2)
    rows.append({'family': 'lowrank', 'param': k, 'top1': round(t1, 2), 'top5': round(t5, 2), 'tau_top5': round(tau, 4)})
    print('L k=%d: top1=%.2f top5=%.2f tau=%.4f' % (k, t1, t5, tau), flush=True)

# order-preserving positive control: contraction toward the class's own centroid
for a in [0.25, 0.5]:
    with torch.no_grad():
        c_own = cents[torch.tensor([lab_map[int(x)] for x in labels], device='cuda')]
        img2 = F.normalize((1 - a) * base + a * c_own, dim=-1)
    t1, t5, tau = evaluate(img2)
    rows.append({'family': 'class_contraction', 'param': a, 'top1': round(t1, 2), 'top5': round(t5, 2), 'tau_top5': round(tau, 4)})
    print('P a=%.2f: top1=%.2f top5=%.2f tau=%.4f' % (a, t1, t5, tau), flush=True)

json.dump({'gap_norm': round(gap_norm, 4), 'results': rows}, open(OUT, 'w', encoding='utf-8'), indent=2)
print('ALL DONE ->', OUT, flush=True)
