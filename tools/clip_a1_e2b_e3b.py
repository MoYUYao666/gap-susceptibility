"""A1 E2b + E3b:
E2b --- input-dependent low-rank perturbation field (per-image independent random subspace/vector) vs global low-rank (already run) → test P2v3
      (order preservation comes from the input dependence of the field, not from the low-rankness of the subspace).
E3b --- the full τ suite over real checkpoints: text_only_r8 / both_r8 / full_ft_s{42,123,999}
      top-1 and τ on the ImageNet 5000 sample (vs the frozen ranking).
Results are stored in outputs/a1_e2b_e3b.json.
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
OUT = 'outputs/a1_e2b_e3b.json'

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


@torch.no_grad()
def get_feats(m):
    text_in = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = m.text_model(**text_in)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    tf = F.normalize(m.text_projection(pooled), dim=-1)
    imgs = []
    for i in range(0, len(sub), 64):
        b = sub[i:i + 64]
        inp = processor(images=b['image'], return_tensors='pt').to('cuda')
        vout = m.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        imgs.append(F.normalize(m.visual_projection(vpooled), dim=-1))
    return torch.cat(imgs), tf


with torch.no_grad():
    base, tf = get_feats(model)
base_sims = base @ tf.T
base_np = base_sims.cpu().numpy()
topk5 = np.argsort(-base_np, axis=1)[:, :5]

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
gap_norm = (ft.mean(0) - fi.mean(0)).norm().item()


def evaluate(img2):
    sims = img2 @ tf.T
    top1 = (sims.argmax(1).cpu() == labels).float().mean().item() * 100
    s_np = sims.cpu().numpy()
    taus = []
    for i in range(N):
        r1v = base_np[i][topk5[i]]
        r2v = s_np[i][topk5[i]]
        if np.std(r1v) < 1e-12 or np.std(r2v) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1v, r2v)
        if np.isfinite(t):
            taus.append(t)
    return top1, float(np.mean(taus))


results = {'E2b_input_dependent': [], 'E3b_real_checkpoints': []}
D = base.shape[1]

# ---------- E2b: input-dependent low-rank field ----------
for k in [1, 16, 64]:
    Q = torch.tensor(rng.randn(N, D, D), dtype=torch.float32, device='cuda')  # per-image independent random basis
    # use a per-image random k-dimensional subspace: take the first k columns of Q_i and project
    with torch.no_grad():
        Qi = Q[:, :, :k]
        # per-image independent orthogonalization (simplified: use the non-orthogonalized columns directly + a normalized perturbation)
        v = torch.tensor(rng.randn(N, k), dtype=torch.float32, device='cuda')
        delta = (Qi @ v.unsqueeze(-1)).squeeze(-1)
        delta = delta / delta.norm(dim=-1, keepdim=True)
        img2 = F.normalize(base + gap_norm * delta, dim=-1)
    t1, tau = evaluate(img2)
    results['E2b_input_dependent'].append({'k': k, 'top1': round(t1, 2), 'tau_top5': round(tau, 4)})
    print('E2b input-dependent low-rank k=%d: top1=%.2f tau=%.4f' % (k, t1, tau), flush=True)

# ---------- E3b: real checkpoint τ ----------
def load_ckpt(ckpt, vision, text):
    m, lora_layers, _ = apply_lora_to_model(
        CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True),
        rank=8, alpha=16.0, apply_to_vision=vision, apply_to_text=text)
    sd = torch.load(ckpt, map_location='cpu', weights_only=False)['lora_state_dict']
    with torch.no_grad():
        for kk, w in sd.items():
            lora_layers[kk].lora_A.data.copy_(w['A'])
            lora_layers[kk].lora_B.data.copy_(w['B'])
    return m.cuda().eval()


def load_fullft(ckpt):
    m = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
    m.load_state_dict(torch.load(ckpt, map_location='cpu', weights_only=False))
    return m.cuda().eval()


checkpoints = {
    'text_only_r8': load_ckpt('outputs/imagenet_zs/text_only_r8/best_checkpoint.pt', False, True),
    'both_r8': load_ckpt('outputs/imagenet_zs/both_r8/best_checkpoint.pt', True, True),
    'full_ft_s42': load_fullft('outputs/imagenet_zs_rerun/full_ft/model_state_last.pt'),
    'full_ft_s123': load_fullft('outputs/imagenet_zs_rerun/full_ft_s123/model_state_last.pt'),
    'full_ft_s999': load_fullft('outputs/imagenet_zs_rerun/full_ft_s999/model_state_last.pt'),
}
for name, m in checkpoints.items():
    with torch.no_grad():
        img2, _ = get_feats(m)
    t1, tau = evaluate(img2)
    results['E3b_real_checkpoints'].append({'name': name, 'top1': round(t1, 2), 'tau_top5': round(tau, 4)})
    print('E3b %s: top1=%.2f tau=%.4f' % (name, t1, tau), flush=True)
    del m
    torch.cuda.empty_cache()

json.dump({'gap_norm': round(gap_norm, 4), 'results': results}, open(OUT, 'w', encoding='utf-8'), indent=2)
print('ALL DONE ->', OUT, flush=True)
