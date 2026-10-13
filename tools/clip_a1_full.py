"""A1 experiment 1: full Gap Surgery phase diagram (CLIP ViT-B/32) + OpenCLIP cross-model reproduction.
Perturbation families: T=shift along the gap direction (λ∈{-2,-1,-0.5,0,0.25,0.5,1,2,4}), O=random orthogonal shift (same λ),
C=contraction toward the image centroid (a∈{0.1,0.25,0.5}).
Metrics: CG, R@1, top-1, top-5, τ_top5, NCC (nearest-centroid classification, a linear-probe surrogate).
OpenCLIP (laion2B) reproduction: T family λ∈{0,0.5,1,2}.
Results are appended incrementally to outputs/a1_full_results.json (guards against loss on crash).
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
OUT = 'outputs/a1_full_results.json'

# ---------- shared data ----------
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
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


@torch.no_grad()
def extract(model, proc):
    text_in = proc(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**text_in)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    tf = F.normalize(model.text_projection(pooled), dim=-1)
    full = []
    for i in range(0, len(ds_in), 64):
        b = ds_in[i:i + 64]
        inp = proc(images=b['image'], return_tensors='pt').to('cuda')
        vout = model.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        full.append(F.normalize(model.visual_projection(vpooled), dim=-1))
    full = torch.cat(full)
    fi, ft = [], []
    for batch in loader:
        out = model(pixel_values=batch['image'].cuda(),
                    input_ids=batch['input_ids'].cuda(),
                    attention_mask=batch['attention_mask'].cuda())
        fi.append(F.normalize(out.image_embeds, dim=-1))
        ft.append(F.normalize(out.text_embeds, dim=-1))
    return tf, full, torch.cat(fi), torch.cat(ft)


def metrics(img_full, tf, fi, ft, base_sims_np, base_labels):
    # CG
    mu_i = fi.mean(0); mu_t = ft.mean(0)
    cg = (mu_i - mu_t).norm().item()
    # R@1
    sims = fi @ ft.T
    i2t = (sims.argmax(1) == torch.arange(len(fi), device='cuda')).float().mean().item()
    t2i = (sims.argmax(0) == torch.arange(len(fi), device='cuda')).float().mean().item()
    r1 = (i2t + t2i) / 2
    # top-1 / top-5 (all 50k)
    s_all = img_full @ tf.T
    pred = s_all.argmax(1).cpu()
    lab_all = torch.tensor(ds_in['label'])
    top1 = (pred == lab_all).float().mean().item() * 100
    top5 = (s_all.topk(5, dim=1).indices.cpu() == lab_all.unsqueeze(1)).any(1).float().mean().item() * 100
    # τ_top5 on 5000
    s_sub = img_full[tau_idx] @ tf.T
    taus = []
    topk = np.argsort(-base_sims_np, axis=1)[:, :5]
    s_sub_np = s_sub.cpu().numpy()
    for i in range(N_TAU):
        r1v = base_sims_np[i][topk[i]]
        r2v = s_sub_np[i][topk[i]]
        if np.std(r1v) < 1e-12 or np.std(r2v) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1v, r2v)
        if np.isfinite(t):
            taus.append(t)
    tau = float(np.mean(taus))
    # NCC (nearest-centroid classification)
    cls = torch.tensor(sorted(set(ds_in['label'])))
    cents = torch.stack([img_full[lab_all == c].mean(0) for c in cls])
    cents = F.normalize(cents, dim=-1)
    ncc = (img_full @ cents.T).argmax(1).cpu()
    lab_map = {int(c): i for i, c in enumerate(cls)}
    ncc_acc = (torch.tensor([lab_map[int(x)] for x in lab_all]) == ncc).float().mean().item() * 100
    return dict(CG=round(cg, 4), R1=round(r1, 4), top1=round(top1, 2), top5=round(top5, 2),
                tau_top5=round(tau, 4), ncc=round(ncc_acc, 2))


def run_model(model, proc, tag):
    print('== %s: extracting embeddings ==' % tag, flush=True)
    tf, full, fi, ft = extract(model, proc)
    mu_i = fi.mean(0); mu_t = ft.mean(0)
    gap_vec = mu_t - mu_i; gap_norm = gap_vec.norm().item(); d_hat = gap_vec / gap_norm
    rng2 = np.random.RandomState(7)
    r_hat = torch.tensor(rng2.randn(512), dtype=torch.float32, device='cuda')
    r_hat = r_hat - (r_hat @ d_hat) * d_hat  # orthogonal to the gap direction
    r_hat = r_hat / r_hat.norm()
    base_sims_np = (full[tau_idx] @ tf.T).cpu().numpy()
    print('%s frozen CG=%.4f' % (tag, gap_norm), flush=True)
    rows = []
    def run(label, lam, kind):
        with torch.no_grad():
            if kind == 'T':
                delta = lam * gap_norm * d_hat
                img_full2 = F.normalize(full + delta, dim=-1)
                fi2 = F.normalize(fi + delta, dim=-1)
            elif kind == 'O':
                delta = lam * gap_norm * r_hat
                img_full2 = F.normalize(full + delta, dim=-1)
                fi2 = F.normalize(fi + delta, dim=-1)
            else:  # C contraction
                a = lam
                img_full2 = F.normalize((1 - a) * full + a * mu_i, dim=-1)
                fi2 = F.normalize((1 - a) * fi + a * mu_i, dim=-1)
        m = metrics(img_full2, tf, fi2, ft, base_sims_np, sub_labels)
        m.update({'model': tag, 'kind': kind, 'lambda': lam})
        rows.append(m)
        print('  %s %s λ/a=%+.2f: CG=%.4f R1=%.4f top1=%.2f top5=%.2f tau=%.4f ncc=%.2f' %
              (tag, kind, lam, m['CG'], m['R1'], m['top1'], m['top5'], m['tau_top5'], m['ncc']), flush=True)
        json.dump(rows, open(OUT, 'w', encoding='utf-8'), indent=2)
    if tag == 'clip':
        grid = [-2.0, -1.0, -0.5, 0.0, 0.25, 0.5, 1.0, 2.0, 4.0]
        for lam in grid:
            run('T', lam, 'T')
            if lam != 0.0:
                run('O', lam, 'O')
        for a in [0.1, 0.25, 0.5]:
            run('C', a, 'C')
    else:
        for lam in [0.0, 0.5, 1.0, 2.0]:
            run('T', lam, 'T')
    del full, fi, ft, tf
    torch.cuda.empty_cache()
    return rows


# ---------- main flow ----------
all_rows = []
m1 = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True).cuda().eval()
all_rows += run_model(m1, processor, 'clip')
del m1; torch.cuda.empty_cache()

try:
    from transformers import CLIPModel as CLIPModel2
    m2 = CLIPModel2.from_pretrained('laion/CLIP-ViT-B-32-laion2B-s34B-b79K', local_files_only=True).cuda().eval()
    p2 = CLIPProcessor.from_pretrained('laion/CLIP-ViT-B-32-laion2B-s34B-b79K', local_files_only=True)
    all_rows += run_model(m2, p2, 'openclip_laion2b')
except Exception as e:
    print('OpenCLIP part failed: %s' % str(e)[:200], flush=True)

json.dump(all_rows, open(OUT, 'w', encoding='utf-8'), indent=2)
print('ALL DONE ->', OUT, flush=True)
