"""A1 enhancement experiment 1: text-side symmetric surgery.
Apply a symmetric translation to the text embeddings (toward the image cluster), and compare with the image-side translation.
Prediction: the text-side translation is the reverse analogue of the image-side translation and likewise breaks classification (validates the class bias-field theory).
Results stored in outputs/a1_text_surgery.json.
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
N_TAU = 5000
OUT = 'outputs/a1_text_surgery.json'

model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True).cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
ds_in = Dataset.from_parquet(PARQ)
names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
texts = [TEMPLATE.format(c.replace('_', ' ')) for c in names]
rng = np.random.RandomState(42)
idx = rng.choice(len(ds_in), N_TAU, replace=False)
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
                    attention_mask=batch['attention_mask'].cuda())
        fi.append(F.normalize(out.image_embeds, dim=-1))
        ft.append(F.normalize(out.text_embeds, dim=-1))
fi = torch.cat(fi); ft = torch.cat(ft)
mu_i, mu_t = fi.mean(0), ft.mean(0)
gap_vec = mu_t - mu_i
gap_norm = gap_vec.norm().item()
d_hat = gap_vec / gap_norm

base_sims = base @ tf.T
base_np = base_sims.cpu().numpy()
topk5 = np.argsort(-base_np, axis=1)[:, :5]


def evaluate(img2, tf2, fi2, ft2):
    cg = (fi2.mean(0) - ft2.mean(0)).norm().item()
    s = img2 @ tf2.T
    top1 = (s.argmax(1).cpu() == labels).float().mean().item() * 100
    s_np = s.cpu().numpy()
    taus = []
    for i in range(N_TAU):
        r1v = base_np[i][topk5[i]]
        r2v = s_np[i][topk5[i]]
        if np.std(r1v) < 1e-12 or np.std(r2v) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1v, r2v)
        if np.isfinite(t):
            taus.append(t)
    return cg, top1, float(np.mean(taus))


results = []
for lam in [0.0, 0.5, 1.0, 2.0]:
    with torch.no_grad():
        # image-side translation (baseline, for comparison)
        delta_i = lam * gap_norm * d_hat
        img_i = F.normalize(base + delta_i, dim=-1)
        fi_i = F.normalize(fi + delta_i, dim=-1)
        cg_i, t1_i, tau_i = evaluate(img_i, tf, fi_i, ft)
        # text-side symmetric translation (move the text toward the image direction)
        delta_t = -lam * gap_norm * d_hat
        tf_t = F.normalize(tf + delta_t, dim=-1)
        ft_t = F.normalize(ft + delta_t, dim=-1)
        cg_t, t1_t, tau_t = evaluate(base, tf_t, fi, ft_t)
    results.append({'lambda': lam,
                    'image_side': {'CG': round(cg_i, 4), 'top1': round(t1_i, 2), 'tau': round(tau_i, 4)},
                    'text_side': {'CG': round(cg_t, 4), 'top1': round(t1_t, 2), 'tau': round(tau_t, 4)}})
    print('λ=%+.1f | image side: CG=%.3f top1=%.2f tau=%.3f | text side: CG=%.3f top1=%.2f tau=%.3f' %
          (lam, cg_i, t1_i, tau_i, cg_t, t1_t, tau_t), flush=True)

json.dump({'gap_norm': round(gap_norm, 4), 'results': results},
          open(OUT, 'w', encoding='utf-8'), indent=2)
print('ALL DONE ->', OUT, flush=True)
