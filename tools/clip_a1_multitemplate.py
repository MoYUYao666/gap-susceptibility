"""A1 提升实验 3：多模板稳健性（3/7 模板）在关键 λ 点。
模板集：
3-tpl = ['a photo of a {}','a photo of the {}','a photo of a {} in a photo']
7-tpl = 3-tpl + ['a {} in a photo','a photo of one {}','an image of a {}','a close-up of a {}']
对 CLIP frozen 在 λ∈{0,0.5,1,2} 做 gap 方向平移，测 top-1 与 τ（各自模板集的 frozen 排序为基准）。
结果存 outputs/a1_multitemplate.json。
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

TPL_SETS = {
    '3tpl': ['a photo of a {}', 'a photo of the {}', 'a photo of a {} in a photo'],
    '7tpl': ['a photo of a {}', 'a photo of the {}', 'a photo of a {} in a photo',
             'a {} in a photo', 'a photo of one {}', 'an image of a {}', 'a close-up of a {}'],
}
N = 5000
OUT = 'outputs/a1_multitemplate.json'

model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True).cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
ds_in = Dataset.from_parquet(PARQ)
names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
rng = np.random.RandomState(42)
idx = rng.choice(len(ds_in), N, replace=False)
sub = ds_in.select(list(idx))
labels = torch.tensor(sub['label'])

ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
val_ds = torch.utils.data.Subset(ds_f, range(2000, 3000))
loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0, collate_fn=_collate_fn)

with torch.no_grad():
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


def text_feats(tpls):
    all_t = [t.format(c.replace('_', ' ')) for c in names for t in tpls]
    ti = processor(text=all_t, return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**ti)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    tf = F.normalize(model.text_projection(pooled), dim=-1)
    tf = tf.view(len(names), len(tpls), -1).mean(1)
    return F.normalize(tf, dim=-1)


results = {}
for tname, tpls in TPL_SETS.items():
    with torch.no_grad():
        tf = text_feats(tpls)
    base_sims = base @ tf.T
    base_np = base_sims.cpu().numpy()
    topk5 = np.argsort(-base_np, axis=1)[:, :5]
    rows = []
    for lam in [0.0, 0.5, 1.0, 2.0]:
        with torch.no_grad():
            img2 = F.normalize(base + lam * gap_norm * d_hat, dim=-1)
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
        rows.append({'lambda': lam, 'top1': round(top1, 2), 'tau': round(tau, 4)})
        print('%s λ=%+.1f: top1=%.2f tau=%.4f' % (tname, lam, top1, tau), flush=True)
    results[tname] = rows

json.dump({'gap_norm': round(gap_norm, 4), 'results': results},
          open(OUT, 'w', encoding='utf-8'), indent=2)
print('ALL DONE ->', OUT, flush=True)
