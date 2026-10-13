"""A1 improvement experiment 4: τ vs baseline metrics + theoretical verification (class bias field).
A) Metric comparison: for all perturbation conditions (T/O/C/G/L/ID/P families, isomorphic to the experiments already run) compute
   top-1, τ, linear CKA, mean embedding cosine, CG, then the Spearman correlation of each metric with top-1.
B) Theoretical verification: under the λ=1 translation, the Pearson correlation between the per-class actual score shift and the predicted λ||g||·m_c;
   the relation between std(m_c) and τ degradation.
Results are stored in outputs/a1_baseline_metrics.json.
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
OUT = 'outputs/a1_baseline_metrics.json'

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

ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
val_ds = torch.utils.data.Subset(ds_f, range(2000, 3000))
loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0, collate_fn=_collate_fn)

with torch.no_grad():
    ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**ti)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    tf = F.normalize(model.text_projection(pooled), dim=-1)
    imgs = []
    for i in range(0, len(sub), 64):
        b = sub[i:i + 64]
        inp = processor(images=b['image'], return_tensors='pt').to('cuda')
        vout = model.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        imgs.append(F.normalize(model.visual_projection(vpooled), dim=-1))
    base = torch.cat(imgs)
    fi, ft = [], []
    for batch in loader:
        out = model(pixel_values=batch['image'].cuda(),
                    input_ids=batch['input_ids'].cuda(),
                    attention_mask=batch['attention_mask'].cuda(), return_loss=False)
        fi.append(F.normalize(out.image_embeds, dim=-1))
        ft.append(F.normalize(out.text_embeds, dim=-1))
fi = torch.cat(fi); ft = torch.cat(ft)
gap_vec = ft.mean(0) - fi.mean(0)
gap_norm = gap_vec.norm().item()
d_hat = gap_vec / gap_norm

base_sims = base @ tf.T
base_np = base_sims.cpu().numpy()
topk5 = np.argsort(-base_np, axis=1)[:, :5]
cls_ids = torch.tensor(sorted(set(ds_in['label'])))
cents = torch.stack([base[labels == c].mean(0) for c in cls_ids])
cents = F.normalize(cents, dim=-1)
lab_map = {int(c): i for i, c in enumerate(cls_ids)}


def linear_cka(X, Y):
    XX = X @ X.T; YY = Y @ Y.T; XY = X @ Y.T
    denom = (torch.trace(XX @ XX).item() * torch.trace(YY @ YY).item()) ** 0.5
    return (torch.trace(XY @ XY).item() / denom) if denom > 0 else 0.0


def evaluate(img2, fi2):
    S = img2 @ tf.T
    top1 = (S.argmax(1).cpu() == labels).float().mean().item() * 100
    s_np = S.cpu().numpy()
    taus = []
    for i in range(N):
        r1v = base_np[i][topk5[i]]
        r2v = s_np[i][topk5[i]]
        if np.std(r1v) < 1e-12 or np.std(r2v) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1v, r2v)
        if np.isfinite(t):
            taus.append(t)
    tau = float(np.mean(taus))
    cg = (fi2.mean(0) - ft.mean(0)).norm().item()
    cka = linear_cka(base, img2)
    mean_cos = (base * img2).sum(1).mean().item()
    return dict(top1=top1, tau=tau, CG=cg, cka=cka, mean_cos=mean_cos)


conds = []
rng2 = np.random.RandomState(7)
D = base.shape[1]
Q, _ = torch.linalg.qr(torch.tensor(rng2.randn(D, D), dtype=torch.float32, device='cuda'))


def push(name, img2, fi2):
    conds.append({'name': name, **evaluate(img2, fi2)})
    print('%s: top1=%.2f tau=%.3f CG=%.3f cka=%.3f cos=%.3f' %
          (name, conds[-1]['top1'], conds[-1]['tau'], conds[-1]['CG'], conds[-1]['cka'], conds[-1]['mean_cos']), flush=True)


with torch.no_grad():
    push('base', base, fi)
    r_hat = torch.tensor(rng2.randn(D), dtype=torch.float32, device='cuda')
    r_hat = r_hat - (r_hat @ d_hat) * d_hat
    r_hat = r_hat / r_hat.norm()
    for lam in [-1, -0.5, 0.25, 0.5, 1, 2, 4]:
        push('T%.2g' % lam, F.normalize(base + lam * gap_norm * d_hat, dim=-1),
             F.normalize(fi + lam * gap_norm * d_hat, dim=-1))
        if lam > 0:
            push('O%.2g' % lam, F.normalize(base + lam * gap_norm * r_hat, dim=-1),
                 F.normalize(fi + lam * gap_norm * r_hat, dim=-1))
    for a in [0.1, 0.25, 0.5]:
        push('C%.2g' % a, F.normalize((1 - a) * base + a * fi.mean(0), dim=-1),
             F.normalize((1 - a) * fi + a * fi.mean(0), dim=-1))
    for sig in [0.25, 0.5, 1, 2]:
        noise = torch.tensor(rng2.randn(N, D), dtype=torch.float32, device='cuda')
        noise = noise / noise.norm(dim=-1, keepdim=True)
        push('G%.2g' % sig, F.normalize(base + sig * gap_norm * noise, dim=-1), fi)
    for k in [1, 4, 16, 64]:
        Pk = Q[:, :k] @ Q[:, :k].T
        v = torch.tensor(rng2.randn(D), dtype=torch.float32, device='cuda')
        v = Pk @ v; v = v / v.norm()
        push('L%d' % k, F.normalize(base + gap_norm * v, dim=-1), fi)
    for a in [0.25, 0.5]:
        c_own = cents[torch.tensor([lab_map[int(x)] for x in labels], device='cuda')]
        push('P%.2g' % a, F.normalize((1 - a) * base + a * c_own, dim=-1), fi)

# Spearman of each metric vs top-1
top1s = [c['top1'] for c in conds]
corrs = {}
for metric in ['tau', 'CG', 'cka', 'mean_cos']:
    vals = [c[metric] for c in conds]
    r, p = stats.spearmanr(top1s, vals)
    corrs[metric] = {'spearman_r': round(float(r), 4), 'p': float(p)}

# theoretical verification: λ=1 class bias field
with torch.no_grad():
    shifted = F.normalize(base + gap_norm * d_hat, dim=-1)
S1 = shifted @ tf.T
m_c = (d_hat @ tf.T).cpu().numpy()          # predicted bias coefficient
actual = (S1 - base_sims).mean(0).cpu().numpy()  # actual per-class score shift
pred = gap_norm * m_c
r_bias, p_bias = stats.pearsonr(actual, pred)
theory = {'pearson_actual_vs_predicted': round(float(r_bias), 4), 'p': float(p_bias),
          'std_m_c': round(float(np.std(m_c)), 4), 'gap_norm': round(gap_norm, 4)}
print('class bias field verification: pearson(actual, predicted)=%.4f  std(m_c)=%.4f' % (r_bias, np.std(m_c)), flush=True)

json.dump({'metric_correlations': corrs, 'theory_verification': theory,
           'n_conditions': len(conds)},
          open(OUT, 'w', encoding='utf-8'), indent=2)
print('ALL DONE ->', OUT, flush=True)
