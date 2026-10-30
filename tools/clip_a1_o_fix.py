"""补测 O 族 λ=-0.25 实测点（2026-08-22）。

a1_full_results.json 的 O 族缺 λ=-0.25（原批未跑）；为让 figT4 九点完整，
按 clip_a1_full.py 同口径（seed 42 五万张抽样、RandomState(7) 的 r_hat、
Flickr30k 2000-3000 鸿沟、top-5 kendalltau）补测该点，追加到 outputs/a1_theory_verify.json。
"""
import os
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
import glob
import json
import sys
import pathlib

import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats
from transformers import CLIPModel, CLIPProcessor
from datasets import Dataset
from torch.utils.data import DataLoader

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from src.dataset import Flickr30kDataset, _collate_fn  # noqa: E402

TEMPLATE = 'a photo of a {}'
N = 5000
LAM = -0.25

parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
ds_in = Dataset.from_parquet(parq)
names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
texts = [TEMPLATE.format(c.replace('_', ' ')) for c in names]
rng = np.random.RandomState(42)
idx = rng.choice(len(ds_in), N, replace=False)
sub = ds_in.select(list(idx))

model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32',
                                  local_files_only=True).cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32',
                                          local_files_only=True)
with torch.no_grad():
    ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**ti)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    tf = F.normalize(model.text_projection(pooled), dim=-1)
    imgs = []
    for i in range(0, N, 64):
        b = sub[i:i + 64]
        inp = processor(images=b['image'], return_tensors='pt').to('cuda')
        vout = model.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        imgs.append(F.normalize(model.visual_projection(vpooled), dim=-1))
    base = torch.cat(imgs)
    base = base / base.norm(dim=-1, keepdim=True)

ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
val_ds = torch.utils.data.Subset(ds_f, range(2000, 3000))
loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0, collate_fn=_collate_fn)
fi, ft = [], []
with torch.no_grad():
    for batch in loader:
        out = model(pixel_values=batch['image'].cuda(),
                    input_ids=batch['input_ids'].cuda(),
                    attention_mask=batch['attention_mask'].cuda(), return_loss=False)
        fi.append(F.normalize(out.image_embeds, dim=-1))
        ft.append(F.normalize(out.text_embeds, dim=-1))
fi = torch.cat(fi)
ft = torch.cat(ft)
gap_vec = ft.mean(0) - fi.mean(0)
gap_norm = gap_vec.norm().item()
d_hat = gap_vec / gap_norm
rng2 = np.random.RandomState(7)
rv = torch.tensor(rng2.randn(512), dtype=torch.float32, device='cuda')
rv = rv - (rv @ d_hat) * d_hat
r_hat = rv / rv.norm()

S = (base @ tf.T).cpu().numpy()
with torch.no_grad():
    img2 = F.normalize(base + LAM * gap_norm * r_hat, dim=-1)
S2 = (img2 @ tf.T).cpu().numpy()
labels = np.array(sub['label'])
top1 = float((S2.argmax(1) == labels).mean() * 100)
topk5 = np.argsort(-S, axis=1)[:, :5]
taus = []
for i in range(N):
    k5 = topk5[i]
    r1, r2 = S[i][k5], S2[i][k5]
    if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
        continue
    t, _ = stats.kendalltau(r1, r2)
    if np.isfinite(t):
        taus.append(t)
tau = float(np.mean(taus))
print('O lambda=-0.25: top1=%.2f  tau=%.4f' % (top1, tau))

vp = 'outputs/a1_theory_verify.json'
d = json.load(open(vp, encoding='utf-8'))
d['measured_tau_orthogonal']['-0.25'] = tau
if 'measured_top1_orthogonal' not in d:
    fr = json.load(open('outputs/a1_full_results.json', encoding='utf-8'))
    d['measured_top1_orthogonal'] = {str(r['lambda']): r['top1'] for r in fr
                                     if r.get('kind') == 'O'}
d['measured_top1_orthogonal']['-0.25'] = top1
json.dump(d, open(vp, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('updated', vp)
