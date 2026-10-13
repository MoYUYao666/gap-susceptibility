"""A1 enhancement experiment 2b: per-epoch τ/zero-shot trajectory + fig4.
Evaluate a1_retrain/{text_only,both}/epoch{N}.pt one by one (5000 sampled):
top-1, τ (vs frozen), CG (Flickr30k val). Results saved to outputs/a1_tau_trajectory.json,
figure saved to paper_a1/figures/fig4_trajectory.png.
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
N = 5000
OUT = 'outputs/a1_tau_trajectory.json'

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


def build(vision, text):
    m, lora_layers, _ = apply_lora_to_model(
        CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True),
        rank=8, alpha=16.0, apply_to_vision=vision, apply_to_text=text)
    return m, lora_layers


@torch.no_grad()
def evaluate(m):
    m = m.cuda().eval()
    ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = m.text_model(**ti)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    tf = F.normalize(m.text_projection(pooled), dim=-1)
    imgs = []
    for i in range(0, len(sub), 64):
        b = sub[i:i + 64]
        inp = processor(images=b['image'], return_tensors='pt').to('cuda')
        vout = m.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        imgs.append(F.normalize(m.visual_projection(vpooled), dim=-1))
    base = torch.cat(imgs)
    fi, ft = [], []
    for batch in loader:
        out = m(pixel_values=batch['image'].cuda(),
                input_ids=batch['input_ids'].cuda(),
                attention_mask=batch['attention_mask'].cuda(), return_loss=False)
        fi.append(F.normalize(out.image_embeds, dim=-1))
        ft.append(F.normalize(out.text_embeds, dim=-1))
    fi = torch.cat(fi); ft = torch.cat(ft)
    cg = (fi.mean(0) - ft.mean(0)).norm().item()
    S = base @ tf.T
    top1 = (S.argmax(1).cpu() == labels).float().mean().item() * 100
    return base, tf, S, top1, cg


# frozen baseline
mf, _ = build(False, False)
base_f, tf_f, S_f, _, cg_f = evaluate(mf)
base_np = S_f.cpu().numpy()
topk5 = np.argsort(-base_np, axis=1)[:, :5]
print('frozen: top1=%.2f CG=%.3f' % (S_f.argmax(1).cpu().eq(labels).float().mean().item() * 100, cg_f), flush=True)
del mf; torch.cuda.empty_cache()


def tau_of(S_np):
    taus = []
    for i in range(N):
        r1v = base_np[i][topk5[i]]
        r2v = S_np[i][topk5[i]]
        if np.std(r1v) < 1e-12 or np.std(r2v) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1v, r2v)
        if np.isfinite(t):
            taus.append(t)
    return float(np.mean(taus))


results = {'frozen': {'top1': round(S_f.argmax(1).cpu().eq(labels).float().mean().item() * 100, 2),
                      'CG': round(cg_f, 4), 'tau': 1.0}}
for mode, vis in [('text_only', False), ('both', True)]:
    results[mode] = []
    for epoch in range(1, 11):
        ckpt = 'outputs/a1_retrain/%s/epoch%d.pt' % (mode, epoch)
        m, lora_layers = build(vis, True)
        sd = torch.load(ckpt, map_location='cpu', weights_only=False)['lora_state_dict']
        with torch.no_grad():
            for k, w in sd.items():
                lora_layers[k].lora_A.data.copy_(w['A'])
                lora_layers[k].lora_B.data.copy_(w['B'])
        _, _, S, top1, cg = evaluate(m)
        tau = tau_of(S.cpu().numpy())
        results[mode].append({'epoch': epoch, 'top1': round(top1, 2), 'CG': round(cg, 4), 'tau': round(tau, 4)})
        print('%s ep%d: top1=%.2f CG=%.3f tau=%.3f' % (mode, epoch, top1, cg, tau), flush=True)
        del m; torch.cuda.empty_cache()

json.dump(results, open(OUT, 'w', encoding='utf-8'), indent=2)
print('ALL DONE ->', OUT, flush=True)
