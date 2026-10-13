"""A1 cross-model reproduction: T-family gap-shift surgery for OpenCLIP (laion2B) and SigLIP.
Model directory convention (log in to HF in a browser, download the whole repo folder, and drop it here):
  models/openclip/            <- all files from laion/CLIP-ViT-B-32-laion2B-s34B-b79K
  models/siglip-base-patch16-224/ <- all files from google/siglip-base-patch16-224
For every model present, run T with λ∈{0,0.5,1,2} × {CG, R@1, top-1, τ}; results go to outputs/a1_crossmodel_results.json.
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
from transformers import CLIPModel, CLIPProcessor, SiglipModel, SiglipProcessor
from torch.utils.data import DataLoader
from src.dataset import Flickr30kDataset, _collate_fn
from scipy import stats

TEMPLATE = 'a photo of a {}'
N_TAU = 5000
OUT = 'outputs/a1_crossmodel_results.json'

PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
ds_in = Dataset.from_parquet(PARQ)
names = [n.split(',')[0].strip() for n in ds_in.features['label'].names]
texts = [TEMPLATE.format(c.replace('_', ' ')) for c in names]
rng = np.random.RandomState(42)
tau_idx = rng.choice(len(ds_in), N_TAU, replace=False)
sub = ds_in.select(list(tau_idx))
sub_labels = torch.tensor(sub['label'])

ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
val_ds = torch.utils.data.Subset(ds_f, range(2000, 3000))
loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0, collate_fn=_collate_fn)

MODELS = [
    ('openclip', 'models/openclip', CLIPModel, CLIPProcessor),
    ('siglip', 'models/siglip-base-patch16-224', SiglipModel, SiglipProcessor),
]

all_rows = []
for tag, mdir, MCls, PCls in MODELS:
    if not os.path.isdir(mdir):
        print('skipping %s (directory %s does not exist)' % (tag, mdir), flush=True)
        continue
    print('== %s ==' % tag, flush=True)
    try:
        model = MCls.from_pretrained(mdir, local_files_only=True).cuda().eval()
        proc = PCls.from_pretrained(mdir, local_files_only=True)
    except Exception as e:
        print('  %s failed to load: %s' % (tag, str(e)[:200]), flush=True)
        continue

    @torch.no_grad()
    def feats(m, proc):
        if tag == 'siglip':
            # SigLIP eos_id == pad_id == 1, so the model's native convention must be replicated:
            # padding='max_length' + text_model.pooler_output (= last_token + head).
            text_in = proc(text=texts, return_tensors='pt', padding='max_length', max_length=64).to('cuda')
            tout = m.text_model(**text_in)
            tf = F.normalize(tout.pooler_output, dim=-1)
        else:
            text_in = proc(text=texts, return_tensors='pt', padding=True).to('cuda')
            tout = m.text_model(**text_in)
            pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
            tf = F.normalize(m.text_projection(pooled), dim=-1)
        full, fi, ft = [], [], []
        for i in range(0, len(ds_in), 64):
            b = ds_in[i:i + 64]
            inp = proc(images=b['image'], return_tensors='pt').to('cuda')
            vout = m.vision_model(**inp)
            vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            imf = m.visual_projection(vpooled) if hasattr(m, 'visual_projection') else vpooled
            full.append(F.normalize(imf, dim=-1))
        full = torch.cat(full)
        for batch in loader:
            inp = proc(images=batch['image'], return_tensors='pt').to('cuda')
            if tag == 'siglip':
                tin = proc(text=batch['caption'], return_tensors='pt', padding='max_length',
                           max_length=64, truncation=True).to('cuda')
                tfeat = m.text_model(**{k: v for k, v in tin.items() if k != 'pixel_values'}).pooler_output
                vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vfeat = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            else:
                tin = proc(text=batch['caption'], return_tensors='pt', padding=True,
                           truncation=True, max_length=64).to('cuda')
                tout = m.text_model(**{k: v for k, v in tin.items() if k != 'pixel_values'})
                tpool = tout[1] if isinstance(tout, tuple) else tout.pooler_output
                tfeat = m.text_projection(tpool) if hasattr(m, 'text_projection') else tpool
                vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vpool = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                vfeat = m.visual_projection(vpool) if hasattr(m, 'visual_projection') else vpool
            fi.append(F.normalize(vfeat, dim=-1))
            ft.append(F.normalize(tfeat, dim=-1))
        return tf, full, torch.cat(fi), torch.cat(ft)

    tf, full, fi, ft = feats(model, proc)
    mu_i, mu_t = fi.mean(0), ft.mean(0)
    gap_vec = mu_t - mu_i
    gap_norm = gap_vec.norm().item()
    d_hat = gap_vec / gap_norm
    base_np = (full[tau_idx] @ tf.T).cpu().numpy()
    print('  %s frozen CG=%.4f' % (tag, gap_norm), flush=True)

    def evaluate(img_full, fi2):
        cg = (fi2.mean(0) - mu_t).norm().item()
        sims = fi2 @ ft.T
        i2t = (sims.argmax(1) == torch.arange(len(fi2), device='cuda')).float().mean().item()
        t2i = (sims.argmax(0) == torch.arange(len(fi2), device='cuda')).float().mean().item()
        r1 = (i2t + t2i) / 2
        s_all = img_full @ tf.T
        pred = s_all.argmax(1).cpu()
        lab_all = torch.tensor(ds_in['label'])
        top1 = (pred == lab_all).float().mean().item() * 100
        s_np = (img_full[tau_idx] @ tf.T).cpu().numpy()
        topk5 = np.argsort(-base_np, axis=1)[:, :5]
        taus = []
        for i in range(N_TAU):
            r1v = base_np[i][topk5[i]]
            r2v = s_np[i][topk5[i]]
            if np.std(r1v) < 1e-12 or np.std(r2v) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1v, r2v)
            if np.isfinite(t):
                taus.append(t)
        tau = float(np.mean(taus))
        return dict(CG=round(cg, 4), R1=round(r1, 4), top1=round(top1, 2), tau_top5=round(tau, 4))

    for lam in [0.0, 0.5, 1.0, 2.0]:
        with torch.no_grad():
            delta = lam * gap_norm * d_hat
            img2 = F.normalize(full + delta, dim=-1)
            fi2 = F.normalize(fi + delta, dim=-1)
        m = evaluate(img2, fi2)
        m.update({'model': tag, 'lambda': lam})
        all_rows.append(m)
        print('  %s T λ=%+.1f: CG=%.4f R1=%.4f top1=%.2f tau=%.4f' %
              (tag, lam, m['CG'], m['R1'], m['top1'], m['tau_top5']), flush=True)
        json.dump(all_rows, open(OUT, 'w', encoding='utf-8'), indent=2)
    del model, full, fi, ft, tf
    torch.cuda.empty_cache()

print('ALL DONE ->', OUT, flush=True)
