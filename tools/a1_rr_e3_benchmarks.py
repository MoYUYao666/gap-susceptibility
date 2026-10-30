"""A1 revision E3 -- additional zero-shot benchmarks (answers R2.3).

Reviewer R2.3: only ImageNet-1K + Flickr30k were used; more zero-shot / fine-grained benchmarks
are required. This script re-runs the frozen / gap-surgery / class-contraction protocol of the
manuscript on further benchmarks that are actually present on disk:

  dtd            torchvision DTD test split (47 texture classes, fine-grained textures)
  food101        torchvision Food-101 test split (101 classes, fine-grained food)
  inat_wild      data/inat_wild  (iNaturalist research-grade wild photos, marine species)
  rare_species   data/rare-species (BioCLIP / IUCN "Rare Species" benchmark, parquet shards)

For each benchmark the script reports, at the paper's surgery grid
lambda in {-2,-1,-0.5,0,0.25,0.5,1,2,4}:
  - top-1 (%),
  - tau (mean Kendall coefficient of the class-relative similarity ranks over the FROZEN top-5
    class sets -- identical estimator to tools/clip_a1_probe2.py::kendall_topk),
  - the exact first-order predictor tau_pred from the class bias field
    (Lemma-1 inversion condition, tools/clip_a1_margins.py) and the prediction error,
  - the class-contraction family P (a in {0.1,0.25,0.5}) as in clip_a1_baseline_metrics.py.

Gap direction -- two variants are reported because these benchmarks have no captions:
  'flickr30k' (primary)  g = mu_T - mu_I estimated on Flickr30k rows 2000..3000 and applied to the
                         benchmark images -- protocol-identical to the ImageNet experiment.
  'self'                 g = mean(class-name text embeddings) - mean(benchmark image embeddings),
                         the class-name protocol used by tools/clip_ocean_margins.py.

Benchmarks that cannot be loaded are reported with loaded=false and the exact error; nothing is
silently substituted or dropped.

Output: outputs/a1_rr_e3_benchmarks.json
Run:    D:\\Anaconda\\envs\\pytorch\\python.exe tools/a1_rr_e3_benchmarks.py [--only dtd,food101]
"""
import os
import io
import sys
import json
import glob
import time
import argparse
import hashlib
import traceback

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from transformers import CLIPModel, CLIPProcessor
from torch.utils.data import DataLoader

from src.dataset import Flickr30kDataset, _collate_fn  # noqa: E402

TEMPLATE = 'a photo of a {}'
GRID = [-2.0, -1.0, -0.5, 0.0, 0.25, 0.5, 1.0, 2.0, 4.0]
A_CONTRACT = [0.1, 0.25, 0.5]
TOPK = 5
RARE_SPECIES_TOP_N = 50          # classes kept from the BioCLIP rare-species benchmark
RARE_SPECIES_MAX_PER_CLASS = 20
BATCH = 64
OUT = 'outputs/a1_rr_e3_benchmarks.json'


# --------------------------------------------------------------------------- metrics
def kendall_topk(base_np, cur_np, topk):
    """Identical estimator to tools/clip_a1_probe2.py::kendall_topk (mean over images)."""
    taus = []
    for i in range(len(base_np)):
        r1 = base_np[i][topk[i]]
        r2 = cur_np[i][topk[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    if not taus:
        return None, 0
    return float(np.mean(taus)), len(taus)


def predicted_tau_exact(base_np, idx5, m, gap_norm, lam):
    """Exact first-order predictor, generalised k=5 form of tools/clip_a1_margins.py."""
    inv = np.empty(len(base_np), dtype=np.int64)
    for i in range(len(base_np)):
        kk = idx5[i]
        s = base_np[i][kk]
        mk = m[kk]
        d = s[:, None] - s[None, :]
        b = mk[None, :] - mk[:, None]
        up = np.triu(np.ones((TOPK, TOPK)), k=1).astype(bool)
        inv[i] = int((lam * gap_norm * b[up] > d[up]).sum())
    return float(np.mean(1.0 - 2.0 * inv / (TOPK * (TOPK - 1) // 2)))


# --------------------------------------------------------------------------- data loaders
def open_src(src):
    """Image sources are a path (str / pathlib.Path, opened lazily) or a decoded PIL image."""
    if isinstance(src, Image.Image):
        return src.convert('RGB')
    return Image.open(src).convert('RGB')


def _tv_paths_labels(ds):
    """Paths + labels of a torchvision image dataset without decoding every image."""
    paths = None
    for attr in ('_image_files', 'imgs'):
        v = getattr(ds, attr, None)
        if v is not None and len(v) == len(ds):
            paths = [x[0] if isinstance(x, (tuple, list)) else x for x in v]
            break
    labels = None
    for attr in ('_labels', 'labels', 'targets'):
        v = getattr(ds, attr, None)
        if v is not None and len(v) == len(ds):
            labels = [int(x) for x in v]
            break
    if labels is None:                       # fallback: decode once to read the labels
        labels = [int(ds[i][1]) for i in range(len(ds))]
    return paths, labels


def load_dtd():
    import torchvision.datasets as tvds
    ds = tvds.DTD(root='data', split='test', download=False)
    names = list(ds.classes)
    paths, labels = _tv_paths_labels(ds)
    sources = paths if paths is not None else [ds[i][0] for i in range(len(ds))]
    return names, sources, np.array(labels), {'source': 'torchvision DTD(root="data", split="test")',
                                              'n_raw': len(ds), 'n_classes': len(names)}


def load_food101():
    import torchvision.datasets as tvds
    ds = tvds.Food101(root='data', split='test', download=False)
    names = list(ds.classes)
    paths, labels = _tv_paths_labels(ds)
    sources = paths if paths is not None else [ds[i][0] for i in range(len(ds))]
    return names, sources, np.array(labels), {'source': 'torchvision Food101(root="data", split="test")',
                                              'n_raw': len(ds), 'n_classes': len(names)}


def load_inat_wild():
    root = 'data/inat_wild'
    dirs = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    names, sources, labels = [], [], []
    per_class = {}
    for d in dirs:
        files = sorted(f for f in os.listdir(os.path.join(root, d)) if f.lower().endswith('.jpg'))
        if len(files) < 8:                     # same MIN_PER_CLASS as tools/clip_ocean_inat_wild.py
            per_class[d] = len(files)
            continue
        ci = len(names)
        names.append(d.replace('_', ' '))
        for f in files:
            sources.append(os.path.join(root, d, f))
            labels.append(ci)
        per_class[d] = len(files)
    return names, sources, np.array(labels), {
        'source': 'data/inat_wild (iNaturalist research-grade wild photos, CC, from '
                  'tools/clip_ocean_inat_wild.py)',
        'n_raw': len(sources), 'n_classes': len(names),
        'skipped_dirs_lt_8_images': {k: v for k, v in per_class.items() if v < 8}}


def load_rare_species():
    from datasets import load_dataset
    files = sorted(os.path.join('data/rare-species/data', f)
                   for f in os.listdir('data/rare-species/data'))
    ds = load_dataset('parquet', data_files=files, split='train')
    sci = ds['sciName']
    counts = {}
    for s in sci:
        counts[s] = counts.get(s, 0) + 1
    top = sorted(counts, key=lambda c: (-counts[c], c))[:RARE_SPECIES_TOP_N]
    top_set = set(top)
    keep_idx = {}
    for i, s in enumerate(sci):
        if s in top_set and len(keep_idx.get(s, [])) < RARE_SPECIES_MAX_PER_CLASS:
            keep_idx.setdefault(s, []).append(i)
    names, sources, labels = [], [], []
    for ci, s in enumerate(top):
        names.append(s)
        for i in keep_idx[s]:
            b = ds[i]['file_name']
            if isinstance(b, Image.Image):          # HF returns a decoded PIL image here
                im = b
            elif isinstance(b, dict):
                im = Image.open(b['path']) if b.get('path') else Image.open(io.BytesIO(b['bytes']))
            else:
                im = Image.open(b)
            sources.append(im.convert('RGB'))
            labels.append(ci)
    return names, sources, np.array(labels), {
        'source': 'data/rare-species parquet shards (BioCLIP / IUCN rare-species benchmark)',
        'n_raw': len(ds), 'n_classes_total': len(counts), 'n_classes': len(names),
        'class_selection': 'top %d species by image count (ties broken by name)' % RARE_SPECIES_TOP_N,
        'max_images_per_class': RARE_SPECIES_MAX_PER_CLASS, 'n_images': len(sources),
        'class_counts_selected': {s: counts[s] for s in top}}


LOADERS = {'dtd': load_dtd, 'food101': load_food101,
           'inat_wild': load_inat_wild, 'rare_species': load_rare_species}


# --------------------------------------------------------------------------- main
@torch.no_grad()
def embed_images(model, processor, sources):
    feats = []
    for i in range(0, len(sources), BATCH):
        pil = [open_src(s) for s in sources[i:i + BATCH]]
        inp = processor(images=pil, return_tensors='pt').to('cuda')
        vout = model.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        feats.append(F.normalize(model.visual_projection(vpooled), dim=-1))
    return torch.cat(feats)


@torch.no_grad()
def embed_texts(model, processor, texts):
    ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**ti)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    return F.normalize(model.text_projection(pooled), dim=-1)


def analyse(name, tf, base, labels, gap_vec, gap_label, model):
    """Full protocol for one benchmark and one gap-direction variant."""
    gap_norm = gap_vec.norm().item()
    d_hat = gap_vec / gap_norm
    m = (d_hat @ tf.T).cpu().numpy()
    base_np = (base @ tf.T).float().cpu().numpy()
    idx5 = np.argsort(-base_np, axis=1)[:, :TOPK]
    n = len(base_np)

    surgery, pred_err = {}, {}
    for lam in GRID:
        with torch.no_grad():
            shifted = F.normalize(base + lam * gap_norm * d_hat, dim=-1)
        Sl = (shifted @ tf.T).float().cpu().numpy()
        top1 = float((Sl.argmax(1) == labels).mean() * 100)
        if TOPK == 1:
            tau = None
        else:
            tau, _ = kendall_topk(base_np, Sl, idx5)
        tau_pred = predicted_tau_exact(base_np, idx5, m, gap_norm, lam)
        surgery[str(lam)] = {'top1': round(top1, 4), 'tau': None if tau is None else round(tau, 6),
                             'tau_pred_exact': None if tau_pred is None else round(tau_pred, 6)}
        if tau is not None:
            pred_err[str(lam)] = round(abs(tau_pred - tau), 6)

    # class-contraction family P (contract every image toward its own class centroid)
    cls_ids = sorted(set(labels.tolist()))
    cents = torch.stack([base[labels == c].mean(0) for c in cls_ids])
    cents = F.normalize(cents, dim=-1)
    lab_map = {int(c): i for i, c in enumerate(cls_ids)}
    c_own = cents[torch.tensor([lab_map[int(x)] for x in labels], device='cuda')]
    contraction = {}
    for a in A_CONTRACT:
        with torch.no_grad():
            x2 = F.normalize((1 - a) * base + a * c_own, dim=-1)
        S2 = (x2 @ tf.T).float().cpu().numpy()
        top1 = float((S2.argmax(1) == labels).mean() * 100)
        tau, _ = kendall_topk(base_np, S2, idx5)
        contraction[str(a)] = {'top1': round(top1, 4),
                               'tau': None if tau is None else round(tau, 6)}

    ok = [v for v in pred_err.values()]
    return {
        'gap_variant': gap_label, 'gap_norm': round(gap_norm, 6),
        'n_images': n, 'n_classes': int(tf.shape[0]),
        'sigma_m': float(np.std(m - m.mean())), 'mean_m': float(np.mean(m)),
        'top1_frozen': surgery['0.0']['top1'],
        'surgery': surgery,
        'exact_predictor_error': {'per_lambda': pred_err,
                                  'mae': round(float(np.mean(ok)), 6) if ok else None,
                                  'max_abs_err': round(float(np.max(ok)), 6) if ok else None},
        'class_contraction': contraction,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=None, help='comma-separated subset of benchmark keys')
    ap.add_argument('--out', default=OUT)
    args = ap.parse_args()
    keys = args.only.split(',') if args.only else list(LOADERS)

    t0 = time.time()
    parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
    h = hashlib.sha1()
    for p in parq:
        h.update(os.path.basename(p).encode())
        h.update(str(os.path.getsize(p)).encode())

    model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32',
                                      local_files_only=True).cuda().eval()
    processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32',
                                              local_files_only=True)

    # ---- primary gap direction: Flickr30k rows 2000..3000 (protocol-identical to ImageNet run)
    ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
    val_ds = torch.utils.data.Subset(ds_f, range(2000, 3000))
    loader = DataLoader(val_ds, batch_size=BATCH, shuffle=False, num_workers=0,
                        collate_fn=_collate_fn)
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
    flickr_gap_vec = ft.mean(0) - fi.mean(0)
    print('Flickr30k gap_norm = %.6f (paper reference 0.8154)'
          % flickr_gap_vec.norm().item(), flush=True)

    out = {
        'meta': {
            'script': 'tools/a1_rr_e3_benchmarks.py',
            'experiment': 'E3 additional zero-shot / fine-grained benchmarks (reviewer R2.3)',
            'model': 'openai/clip-vit-base-patch32 (frozen)',
            'template': TEMPLATE, 'surgery_grid': GRID, 'topk_for_tau': TOPK,
            'class_contraction_a': A_CONTRACT,
            'flickr30k_gap_norm': round(flickr_gap_vec.norm().item(), 6),
            'gap_variants': {
                'flickr30k': 'g = mu_T - mu_I from Flickr30k rows 2000..3000 (same as the '
                             'ImageNet experiment); applied to the benchmark image embeddings',
                'self': 'g = mean(class-name text embeddings) - mean(benchmark image embeddings); '
                        'class-name protocol of tools/clip_ocean_margins.py'},
            'shards': len(parq), 'shard_sig': h.hexdigest()[:16],
        },
        'benchmarks': {},
    }

    for key in keys:
        print('\n==================== %s ====================' % key, flush=True)
        entry = {'benchmark': key}
        try:
            names, sources, labels, meta = LOADERS[key]()
            entry['loaded'] = True
            entry['dataset'] = meta
            entry['class_list_len'] = len(names)
            entry['class_names_head'] = names[:10]
            print('  loaded: %d images, %d classes (%.1fs)'
                  % (len(sources), len(names), time.time() - t0), flush=True)
        except Exception as e:
            entry['loaded'] = False
            entry['error'] = '%s: %s' % (type(e).__name__, str(e)[:500])
            entry['traceback_tail'] = traceback.format_exc()[-800:]
            out['benchmarks'][key] = entry
            json.dump(out, open(args.out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
            print('  LOAD FAILED: %s' % entry['error'], flush=True)
            continue

        try:
            base = embed_images(model, processor, sources)
            tf = embed_texts(model, processor, [TEMPLATE.format(c.replace('_', ' ')) for c in names])
            entry['variants'] = {}
            entry['variants']['flickr30k'] = analyse(key, tf, base, labels, flickr_gap_vec,
                                                     'flickr30k', model)
            self_gap = tf.mean(0) - base.mean(0)
            entry['variants']['self'] = analyse(key, tf, base, labels, self_gap, 'self', model)
            v = entry['variants']['flickr30k']
            print('  [flickr30k gap] top1 frozen=%.2f | tau: %s | predMAE=%.4f'
                  % (v['top1_frozen'],
                     {a: v['surgery'][str(a)]['tau'] for a in [0.0, 0.5, 1.0, 2.0]},
                     v['exact_predictor_error']['mae']), flush=True)
            v2 = entry['variants']['self']
            print('  [self gap]      gap=%.4f top1 frozen=%.2f | tau: %s | predMAE=%.4f'
                  % (v2['gap_norm'], v2['top1_frozen'],
                     {a: v2['surgery'][str(a)]['tau'] for a in [0.0, 0.5, 1.0, 2.0]},
                     v2['exact_predictor_error']['mae']), flush=True)
            del base
            torch.cuda.empty_cache()
        except Exception as e:
            entry['loaded'] = True
            entry['analysis_error'] = '%s: %s' % (type(e).__name__, str(e)[:500])
            entry['traceback_tail'] = traceback.format_exc()[-800:]
            print('  ANALYSIS FAILED: %s' % entry['analysis_error'], flush=True)

        out['benchmarks'][key] = entry
        json.dump(out, open(args.out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('  [checkpoint] wrote %s' % args.out, flush=True)

    out['meta']['runtime_s'] = round(time.time() - t0, 1)
    json.dump(out, open(args.out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nALL DONE -> %s (%.1fs)' % (args.out, time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
