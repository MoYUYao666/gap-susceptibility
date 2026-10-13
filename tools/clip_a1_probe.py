"""A1 kickoff probe (minimal version): separation effect of a controlled gap shift on task sensitivity.
λ grid × three metrics (ImageNet top-1, Flickr30k R@1, CG).
Prediction: CG grows linearly; R@1 degrades monotonically; top-1 stays flat (until misordering).
"""
import os, sys, json
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn.functional as F
from glob import glob
from datasets import Dataset
from transformers import CLIPModel, CLIPProcessor
from torch.utils.data import DataLoader
from src.dataset import Flickr30kDataset, _collate_fn

TEMPLATE = 'a photo of a {}'
LAMBDAS = [-1.0, 0.0, 0.5, 1.0, 2.0]

# ---------- 1. Model and data ----------
model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True).cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)

# ImageNet 50k
PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
ds_in = Dataset.from_parquet(PARQ)
names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
texts = [TEMPLATE.format(c.replace('_', ' ')) for c in names]
with torch.no_grad():
    text_in = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**text_in)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    in_text_feats = F.normalize(model.text_projection(pooled), dim=-1)  # (1000, D)

    in_img_feats = []
    for i in range(0, len(ds_in), 64):
        b = ds_in[i:i + 64]
        inp = processor(images=b['image'], return_tensors='pt').to('cuda')
        vout = model.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        in_img_feats.append(F.normalize(model.visual_projection(vpooled), dim=-1))
    in_img_feats = torch.cat(in_img_feats)  # (50000, D)
    in_labels = torch.tensor(ds_in['label'])
print('ImageNet: %d imgs, %d classes' % (in_img_feats.shape[0], in_text_feats.shape[0]), flush=True)

# Flickr30k val subset (consistent with the existing evaluation: captions 2000:3000)
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
print('Flickr30k val: %d pairs' % f_img.shape[0], flush=True)

# ---------- 2. Gap direction ----------
mu_i = f_img.mean(0); mu_t = f_txt.mean(0)
gap_vec = mu_t - mu_i
gap_norm = gap_vec.norm().item()
d_hat = gap_vec / gap_norm
print('frozen CG = %.4f' % gap_norm, flush=True)

# ---------- 3. Surgery evaluation ----------
def shift(feats, lam):
    delta = lam * gap_norm * d_hat
    return F.normalize(feats + delta, dim=-1)

results = []
for lam in LAMBDAS:
    with torch.no_grad():
        # CG
        si = shift(f_img, lam)
        cg = (si.mean(0) - mu_t).norm().item()
        # Flickr30k R@1
        sims = si @ f_txt.T
        i2t = (sims.argmax(1) == torch.arange(len(si), device='cuda')).float().mean().item()
        t2i = (sims.argmax(0) == torch.arange(len(si), device='cuda')).float().mean().item()
        r1 = (i2t + t2i) / 2
        # ImageNet top-1
        si_in = shift(in_img_feats, lam)
        sims_in = si_in @ in_text_feats.T
        pred = sims_in.argmax(1).cpu()
        top1 = (pred == in_labels).float().mean().item() * 100
    results.append({'lambda': lam, 'CG': round(cg, 4), 'R1': round(r1, 4),
                    'top1_imagenet': round(top1, 2)})
    print('λ=%+.1f  CG=%.4f  R@1=%.4f  ImageNet top-1=%.2f%%' % (lam, cg, r1, top1), flush=True)

json.dump({'gap_norm_frozen': round(gap_norm, 4), 'results': results},
          open('outputs/a1_probe.json', 'w', encoding='utf-8'), indent=2)
print('saved outputs/a1_probe.json', flush=True)
